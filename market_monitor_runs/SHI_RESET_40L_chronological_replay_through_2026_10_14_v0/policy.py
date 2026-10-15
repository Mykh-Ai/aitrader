"""40L cutoff adapter; frozen 40H thresholds/exits, October admission enabled."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.strategy_search.replay import ReplayData


def signals(bars, family, lookback, flow, volume, trend):
    # Verbatim 40D signal formulas; only the October date exclusion is removed.
    upper, lower = bars[f"upper{lookback}"], bars[f"lower{lookback}"]
    if family == "ACCEPTED_BREAK":
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
    for start, end in [("2026-06-22", "2026-06-29"), ("2026-08-25", "2026-09-01")]:
        quality &= ~bars.timestamp.between(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"), inclusive="left")
    return np.where(quality & long & ~short, 1, np.where(quality & short & ~long, -1, 0))


def hybrid_signals(bars, long, short):
    fields = ["family", "lookback", "flow", "volume", "trend"]
    longs = signals(bars, *[long[k] for k in fields])
    shorts = signals(bars, *[short[k] for k in fields])
    longs[((bars.close - bars.ema24).abs() / bars.atr > long["maturity"])
          | ((bars.high - bars.low) / bars.atr > long["impulse"])] = 0
    return np.where((longs > 0) & (shorts >= 0), 1,
                    np.where((shorts < 0) & (longs <= 0), -1, 0))


class TailAwareReplayData(ReplayData):
    """Precise replay may enter after the last closed H1 using observed minutes.

    The legacy entry helper unnecessarily requires another completed H1 even
    though precise trade_path ignores its first-hour range/quality aggregates.
    Only that final-index case is adapted; no future candle is manufactured.
    """

    def entry(self, i):
        if i + 1 < len(self.times):
            return super().entry(i)
        if i in self.entries:
            return self.entries[i]
        planned = self.available[i] + 2 * self.minute
        p = int(np.searchsorted(self.minute_ts, planned))
        if p >= len(self.minute_ts) or self.minute_ts[p] - planned > self.minute or not self.raw[p]:
            self.entries[i] = None
            return None
        # These aggregates are deliberately entry-minute-only and unused by
        # precise replay. This adapter must not be used for coarse H1 replay.
        item = (p, self.minute_ts[p] - self.minute, self.mo[p], self.mh[p], self.ml[p], bool(self.raw[p]))
        self.entries[i] = item
        return item


def classify_tail(trades, cutoff):
    result = trades.copy()
    result["status_at_cutoff"] = "CLOSED"
    incomplete = result.censored
    tail = incomplete & result.exit_reason.isin(["OPEN", "CENSORED_TAIL"]) & result.expiry_at.gt(cutoff)
    result.loc[incomplete, "status_at_cutoff"] = "CENSORED_DATA"
    result.loc[tail, "status_at_cutoff"] = "OPEN_AT_CUTOFF"
    assert result.loc[tail, ["exit_price", "net_usd", "exit_at"]].isna().all().all()
    return result


def open_marks(open_trades, spot, cutoff):
    records = []
    for r in open_trades.itertuples():
        observed = spot.loc[spot.DataQuality.eq("RAW") & spot.Timestamp.le(cutoff) & spot.Timestamp.gt(r.entry_at)]
        assert len(observed)
        last = observed.iloc[-1]
        assert cutoff - last.Timestamp <= pd.Timedelta(minutes=1)
        quantity = 3000 / r.entry_price
        gross = r.direction * (last.ClosePrice - r.entry_price) * quantity
        slip = (last.ClosePrice + r.entry_price) * quantity * .0002
        records.append({"signal_index": r.signal_index, "mark_at": last.Timestamp,
                        "mark_price_usdc": last.ClosePrice, "unrealized_gross_usdc": gross,
                        "hypothetical_net_if_closed_at_mark_usdc": gross - 5 - slip,
                        "included_in_realized_net": False})
    return pd.DataFrame(records, columns=["signal_index", "mark_at", "mark_price_usdc", "unrealized_gross_usdc",
                                        "hypothetical_net_if_closed_at_mark_usdc", "included_in_realized_net"])
