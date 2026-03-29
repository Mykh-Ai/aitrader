"""H2 impulse feature-only detector (Patch 1 additive layer)."""

from __future__ import annotations

import numpy as np
import pandas as pd

IMPULSE_WINDOW_BARS = 20
PRE_COMPRESSION_SHORT_WINDOW_BARS = 6
IMPULSE_RANGE_RATIO_THRESHOLD = 1.8
IMPULSE_CONFIRMATION_THRESHOLD = 1.8
PRE_COMPRESSION_THRESHOLD = 0.75
IMPULSE_COOLDOWN_BARS = 12

IMPULSE_FEATURE_COLUMNS = [
    "ImpulseDetected_v1",
    "ImpulseDirection_v1",
    "ImpulseRangeRatio_20_v1",
    "ImpulseVolumeRatio_v1",
    "ImpulseDeltaRatio_v1",
    "ImpulseOIRatio_v1",
    "ImpulseLiqConfirmed_v1",
    "PreCompression_6v20_v1",
    "PreCompressionTag_v1",
    "ImpulseAnchorHigh_v1",
    "ImpulseAnchorLow_v1",
    "ImpulseAnchorMid_v1",
    "ImpulseAnchorVWAP_v1",
]


_REQUIRED_INPUT_COLUMNS = {
    "BarRange",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "CtxLiqSpike_v1",
    "Close",
    "Open",
    "CloseLocation",
    "High",
    "Low",
    "VWAP",
}


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = _REQUIRED_INPUT_COLUMNS - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for H2 impulse detection: "
            f"{sorted(missing)}"
        )


def _empty_like(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ImpulseDetected_v1"] = pd.Series(dtype=bool)
    out["ImpulseDirection_v1"] = pd.Series(dtype=object)
    out["ImpulseRangeRatio_20_v1"] = pd.Series(dtype=float)
    out["ImpulseVolumeRatio_v1"] = pd.Series(dtype=float)
    out["ImpulseDeltaRatio_v1"] = pd.Series(dtype=float)
    out["ImpulseOIRatio_v1"] = pd.Series(dtype=float)
    out["ImpulseLiqConfirmed_v1"] = pd.Series(dtype=bool)
    out["PreCompression_6v20_v1"] = pd.Series(dtype=float)
    out["PreCompressionTag_v1"] = pd.Series(dtype=bool)
    out["ImpulseAnchorHigh_v1"] = pd.Series(dtype=float)
    out["ImpulseAnchorLow_v1"] = pd.Series(dtype=float)
    out["ImpulseAnchorMid_v1"] = pd.Series(dtype=float)
    out["ImpulseAnchorVWAP_v1"] = pd.Series(dtype=float)
    return out


def detect_impulses(df: pd.DataFrame) -> pd.DataFrame:
    """Attach additive H2 impulse features without changing H1 semantics.

    Detector is strictly feature-only and uses current/past data only.
    """
    _validate_required_columns(df)

    if df.empty:
        return _empty_like(df)

    out = df.copy()

    bar_range = pd.to_numeric(out["BarRange"], errors="coerce")
    median_20 = bar_range.rolling(window=IMPULSE_WINDOW_BARS, min_periods=1).median()
    median_6 = bar_range.rolling(window=PRE_COMPRESSION_SHORT_WINDOW_BARS, min_periods=1).median()

    out["ImpulseRangeRatio_20_v1"] = np.divide(
        bar_range,
        median_20,
        out=np.zeros(len(out), dtype=float),
        where=median_20.abs() > 1e-12,
    )

    out["ImpulseVolumeRatio_v1"] = pd.to_numeric(out["RelVolume_20"], errors="coerce")
    out["ImpulseDeltaRatio_v1"] = pd.to_numeric(out["DeltaAbsRatio_20"], errors="coerce")
    out["ImpulseOIRatio_v1"] = pd.to_numeric(out["OIChangeAbsRatio_20"], errors="coerce")
    out["ImpulseLiqConfirmed_v1"] = out["CtxLiqSpike_v1"].fillna(False).astype(bool)

    out["PreCompression_6v20_v1"] = np.divide(
        median_6,
        median_20,
        out=np.zeros(len(out), dtype=float),
        where=median_20.abs() > 1e-12,
    )
    out["PreCompressionTag_v1"] = out["PreCompression_6v20_v1"] <= PRE_COMPRESSION_THRESHOLD

    range_ok = out["ImpulseRangeRatio_20_v1"] >= IMPULSE_RANGE_RATIO_THRESHOLD

    confirmation_votes = (
        (out["RelVolume_20"] >= IMPULSE_CONFIRMATION_THRESHOLD).astype(int)
        + (out["DeltaAbsRatio_20"] >= IMPULSE_CONFIRMATION_THRESHOLD).astype(int)
        + (out["OIChangeAbsRatio_20"] >= IMPULSE_CONFIRMATION_THRESHOLD).astype(int)
        + out["CtxLiqSpike_v1"].fillna(False).astype(int)
    )
    confirmation_ok = confirmation_votes >= 2

    bull = (out["Close"] > out["Open"]) & (out["CloseLocation"] >= 0.65)
    bear = (out["Close"] < out["Open"]) & (out["CloseLocation"] <= 0.35)

    raw_up = range_ok & confirmation_ok & bull
    raw_down = range_ok & confirmation_ok & bear

    impulse_detected = pd.Series(False, index=out.index, dtype=bool)
    impulse_direction = pd.Series(pd.NA, index=out.index, dtype=object)

    cooldown_up_until = -1
    cooldown_down_until = -1

    for i in range(len(out)):
        if bool(raw_up.iat[i]):
            if i > cooldown_up_until:
                impulse_detected.iat[i] = True
                impulse_direction.iat[i] = "IMPULSE_UP"
                cooldown_up_until = i + IMPULSE_COOLDOWN_BARS
            continue

        if bool(raw_down.iat[i]) and i > cooldown_down_until:
            impulse_detected.iat[i] = True
            impulse_direction.iat[i] = "IMPULSE_DOWN"
            cooldown_down_until = i + IMPULSE_COOLDOWN_BARS

    out["ImpulseDetected_v1"] = impulse_detected
    out["ImpulseDirection_v1"] = impulse_direction

    anchor_detected = out["ImpulseDetected_v1"].fillna(False).astype(bool)
    out["ImpulseAnchorHigh_v1"] = pd.to_numeric(out["High"], errors="coerce").where(anchor_detected, pd.NA)
    out["ImpulseAnchorLow_v1"] = pd.to_numeric(out["Low"], errors="coerce").where(anchor_detected, pd.NA)
    out["ImpulseAnchorMid_v1"] = (
        (pd.to_numeric(out["High"], errors="coerce") + pd.to_numeric(out["Low"], errors="coerce")) / 2.0
    ).where(anchor_detected, pd.NA)
    out["ImpulseAnchorVWAP_v1"] = pd.to_numeric(out["VWAP"], errors="coerce").where(anchor_detected, pd.NA)

    return out
