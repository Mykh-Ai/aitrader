from __future__ import annotations

import numpy as np
import pandas as pd

from research.own_signal_run.feed import closed_bars, usable_observations


def features(feed: pd.DataFrame) -> pd.DataFrame:
    bars = closed_bars(usable_observations(feed), 60)
    bars = bars.loc[bars.completed].copy().reset_index(drop=True)
    previous = bars.close.shift()
    tr = pd.concat([bars.high - bars.low, (bars.high - previous).abs(), (bars.low - previous).abs()], axis=1).max(axis=1)
    bars["atr"] = tr.rolling(24, min_periods=24).mean()
    bars["delta"] = (bars.buy - bars.sell) / bars.volume.replace(0, np.nan)
    bars["volume_ratio"] = bars.volume / bars.volume.shift().rolling(24, min_periods=24).median()
    bars["delta24"] = (bars.buy - bars.sell).rolling(24).sum() / bars.volume.rolling(24).sum()
    bars["change24"] = bars.close / bars.close.shift(24) - 1
    bars["ema24"] = bars.close.ewm(span=24, adjust=False).mean()
    bars["ema72"] = bars.close.ewm(span=72, adjust=False).mean()
    bars["ema168"] = bars.close.ewm(span=168, adjust=False).mean()
    bars["context_usable"] = bars.usable.rolling(24, min_periods=24).sum().eq(24)
    for lookback in [6, 12, 24, 48, 96]:
        bars[f"upper{lookback}"] = bars.high.shift().rolling(lookback, min_periods=lookback).max()
        bars[f"lower{lookback}"] = bars.low.shift().rolling(lookback, min_periods=lookback).min()
    # Strictly confirmed H1 two-sided swings; values become usable two hours later.
    high_center = bars.high.shift(2)
    low_center = bars.low.shift(2)
    confirmed = bars.usable.rolling(5, min_periods=5).sum().eq(5)
    high_valid = confirmed.copy()
    low_valid = confirmed.copy()
    for offset in [0, 1, 3, 4]:
        high_valid &= high_center.gt(bars.high.shift(offset))
        low_valid &= low_center.lt(bars.low.shift(offset))
    bars["confirmed_swing_high"] = high_center.where(high_valid).ffill()
    bars["confirmed_swing_low"] = low_center.where(low_valid).ffill()
    return bars


def signals(bars: pd.DataFrame, family: str, lookback: int, flow: float, volume: float, trend: str) -> np.ndarray:
    upper, lower = bars[f"upper{lookback}"], bars[f"lower{lookback}"]
    if family == "ACCEPTED_BREAK":
        # The reference is frozen before the first of two acceptance closes.
        upper_fixed, lower_fixed = upper.shift(1), lower.shift(1)
        long = bars.close.gt(upper_fixed) & bars.close.shift().gt(upper_fixed)
        short = bars.close.lt(lower_fixed) & bars.close.shift().lt(lower_fixed)
        long &= ~long.shift(fill_value=False)
        short &= ~short.shift(fill_value=False)
    elif family == "BREAKOUT":
        long, short = bars.close.gt(upper), bars.close.lt(lower)
    elif family == "TREND_RETEST":
        long = bars.low.le(bars.ema24) & bars.close.gt(bars.ema24) & bars.close.gt(bars.open)
        short = bars.high.ge(bars.ema24) & bars.close.lt(bars.ema24) & bars.close.lt(bars.open)
    elif family == "SWEEP_RECLAIM":
        # One completed penetration, followed by the next completed close-back.
        long = bars.low.shift().lt(lower.shift()) & bars.close.gt(lower.shift()) & bars.close.gt(bars.open)
        short = bars.high.shift().gt(upper.shift()) & bars.close.lt(upper.shift()) & bars.close.lt(bars.open)
    else:
        raise ValueError(family)
    if trend == "EMA":
        long &= bars.ema24.gt(bars.ema72) & bars.close.gt(bars.ema168)
        short &= bars.ema24.lt(bars.ema72) & bars.close.lt(bars.ema168)
    elif trend == "PRESSURE":
        long &= bars.change24.gt(0) & bars.delta24.gt(0)
        short &= bars.change24.lt(0) & bars.delta24.lt(0)
    elif trend != "NONE":
        raise ValueError(trend)
    long &= bars.delta.ge(flow)
    short &= bars.delta.le(-flow)
    quality = bars.context_usable & bars.usable & bars.volume_ratio.ge(volume)
    quality &= bars.usable.shift().rolling(lookback, min_periods=lookback).sum().eq(lookback)
    quality &= bars.timestamp.ge(pd.Timestamp("2026-03-18T14:00:00Z"))
    quality &= ~bars.timestamp.between(pd.Timestamp("2026-04-23T17:05:00Z"), pd.Timestamp("2026-05-10T00:00:00Z"), inclusive="left")
    for start, end in [("2026-06-22", "2026-06-29"), ("2026-08-25", "2026-09-01"), ("2026-10-01", "2026-10-13")]:
        quality &= ~bars.timestamp.between(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"), inclusive="left")
    return np.where(quality & long & ~short, 1, np.where(quality & short & ~long, -1, 0))
