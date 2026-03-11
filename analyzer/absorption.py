"""Absorption/context feature layer (Phase 1F)."""

from __future__ import annotations

import numpy as np
import pandas as pd

CONTEXT_WINDOW = 20
RATIO_EPSILON = 1e-12


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Safe elementwise ratio with zero-denominator handling."""
    num = numerator.astype(float)
    den = denominator.astype(float)
    out = pd.Series(np.zeros(len(num), dtype=float), index=num.index)
    valid = den.abs() > RATIO_EPSILON
    out.loc[valid] = num.loc[valid] / den.loc[valid]
    return out


def detect_absorption(df: pd.DataFrame) -> pd.DataFrame:
    """Attach deterministic context features for absorption research.

    Formulas (window = ``CONTEXT_WINDOW``):
    - ``RelVolume_20`` = ``Volume`` / rolling_mean(``Volume``)
    - ``DeltaAbsRatio_20`` = abs(``Delta``) / rolling_mean(abs(``Delta``))
    - ``OIChangeAbsRatio_20`` = abs(``OI_Change``) / rolling_mean(abs(``OI_Change``))
    - ``LiqTotalRatio_20`` = ``LiqTotal`` / rolling_mean(``LiqTotal``)

    Rolling baselines use ``min_periods=1`` and include only current/past bars
    (no future leakage). ``AbsorptionScore_v1`` is an additive context-stress
    helper, not a trading signal.
    """
    out = df.copy()

    vol_baseline = out["Volume"].rolling(window=CONTEXT_WINDOW, min_periods=1).mean()
    delta_abs = out["Delta"].abs()
    delta_baseline = delta_abs.rolling(window=CONTEXT_WINDOW, min_periods=1).mean()

    oi_change_abs = out["OI_Change"].fillna(0.0).abs()
    oi_baseline = oi_change_abs.rolling(window=CONTEXT_WINDOW, min_periods=1).mean()

    liq_baseline = out["LiqTotal"].rolling(window=CONTEXT_WINDOW, min_periods=1).mean()

    out["RelVolume_20"] = _safe_ratio(out["Volume"], vol_baseline)
    out["DeltaAbsRatio_20"] = _safe_ratio(delta_abs, delta_baseline)
    out["OIChangeAbsRatio_20"] = _safe_ratio(oi_change_abs, oi_baseline)
    out["LiqTotalRatio_20"] = _safe_ratio(out["LiqTotal"], liq_baseline)

    out["CtxRelVolumeSpike_v1"] = out["RelVolume_20"] >= 1.5
    out["CtxDeltaSpike_v1"] = out["DeltaAbsRatio_20"] >= 1.5
    out["CtxOISpike_v1"] = out["OIChangeAbsRatio_20"] >= 1.5
    out["CtxLiqSpike_v1"] = out["LiqTotalRatio_20"] >= 1.5
    out["CtxWickReclaim_v1"] = (
        out[["UpperWickToRange", "LowerWickToRange"]].max(axis=1) >= 0.4
    ) & (out["BodyToRange"] <= 0.35)

    out["AbsorptionScore_v1"] = (
        out[
            [
                "CtxRelVolumeSpike_v1",
                "CtxDeltaSpike_v1",
                "CtxOISpike_v1",
                "CtxLiqSpike_v1",
                "CtxWickReclaim_v1",
            ]
        ]
        .astype(int)
        .sum(axis=1)
    )

    return out
