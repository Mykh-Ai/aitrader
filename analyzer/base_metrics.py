"""Base metric computations for Analyzer."""

from __future__ import annotations

import numpy as np
import pandas as pd


RANGE_EPSILON = 1e-12


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Safe elementwise ratio with zero-denominator handling as 0.0."""
    num = numerator.astype(float)
    den = denominator.astype(float)
    out = pd.Series(np.zeros(len(num), dtype=float), index=num.index)
    valid = den.abs() > RANGE_EPSILON
    out.loc[valid] = num.loc[valid] / den.loc[valid]
    return out


def add_base_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return frame with base metrics from Spec v1.0 Phase 1A formulas."""
    out = df.copy()

    out["Delta"] = out["BuyQty"] - out["SellQty"]
    out["CVD"] = out["Delta"].cumsum()
    out["DeltaPct"] = _safe_ratio(out["Delta"], out["Volume"])

    out["BarRange"] = out["High"] - out["Low"]
    out["BodySize"] = (out["Close"] - out["Open"]).abs()

    candle_max = out[["Open", "Close"]].max(axis=1)
    candle_min = out[["Open", "Close"]].min(axis=1)

    out["UpperWick"] = out["High"] - candle_max
    out["LowerWick"] = candle_min - out["Low"]

    out["CloseLocation"] = _safe_ratio(out["Close"] - out["Low"], out["BarRange"])
    out["BodyToRange"] = _safe_ratio(out["BodySize"], out["BarRange"])
    out["UpperWickToRange"] = _safe_ratio(out["UpperWick"], out["BarRange"])
    out["LowerWickToRange"] = _safe_ratio(out["LowerWick"], out["BarRange"])

    out["OI_Change"] = out["OpenInterest"].diff()
    out["LiqTotal"] = out["LiqBuyQty"] + out["LiqSellQty"]

    return out
