"""Sweep detection against already confirmed structural swing levels (Phase 1C)."""

from __future__ import annotations

import pandas as pd

SWEEP_FEATURE_COLUMNS = [
    "Sweep_H1_Up",
    "Sweep_H1_Down",
    "Sweep_H1_Direction",
    "Sweep_H1_ReferenceLevel",
    "Sweep_H1_ReferenceTs",
    "Sweep_H4_Up",
    "Sweep_H4_Down",
    "Sweep_H4_Direction",
    "Sweep_H4_ReferenceLevel",
    "Sweep_H4_ReferenceTs",
]


def _annotate_tf_sweeps(out: pd.DataFrame, tf_label: str) -> pd.DataFrame:
    high_price_col = f"SwingHigh_{tf_label}_Price"
    high_ts_col = f"SwingHigh_{tf_label}_ConfirmedAt"
    low_price_col = f"SwingLow_{tf_label}_Price"
    low_ts_col = f"SwingLow_{tf_label}_ConfirmedAt"

    up_col = f"Sweep_{tf_label}_Up"
    down_col = f"Sweep_{tf_label}_Down"
    direction_col = f"Sweep_{tf_label}_Direction"
    ref_level_col = f"Sweep_{tf_label}_ReferenceLevel"
    ref_ts_col = f"Sweep_{tf_label}_ReferenceTs"

    high_level = pd.to_numeric(out[high_price_col], errors="coerce")
    low_level = pd.to_numeric(out[low_price_col], errors="coerce")

    up = high_level.notna() & (out["High"] > high_level)
    down = low_level.notna() & (out["Low"] < low_level)

    out[up_col] = up.astype(bool)
    out[down_col] = down.astype(bool)

    direction = pd.Series(pd.NA, index=out.index, dtype="object")
    direction.loc[up & ~down] = "up"
    direction.loc[down & ~up] = "down"
    direction.loc[up & down] = "both"
    out[direction_col] = direction

    ref_level = pd.Series(pd.NA, index=out.index, dtype="Float64")
    ref_level.loc[up & ~down] = high_level.loc[up & ~down]
    ref_level.loc[down & ~up] = low_level.loc[down & ~up]
    out[ref_level_col] = ref_level

    ref_ts = pd.Series(pd.NaT, index=out.index, dtype="object")
    ref_ts.loc[up & ~down] = out.loc[up & ~down, high_ts_col]
    ref_ts.loc[down & ~up] = out.loc[down & ~up, low_ts_col]
    out[ref_ts_col] = pd.to_datetime(ref_ts, utc=True)

    return out


def detect_sweeps(df: pd.DataFrame) -> pd.DataFrame:
    """Annotate strict sweeps against latest confirmed structural swings.

    Sweep definitions (strict, anti-lookahead-safe):
    - Upward sweep: ``High > latest confirmed swing high price``.
    - Downward sweep: ``Low < latest confirmed swing low price``.

    The function only references swing levels already materialized on each row via
    delayed-confirmation columns from :func:`analyzer.swings.annotate_swings`.
    """
    out = df.copy()
    for tf_label in ("H1", "H4"):
        out = _annotate_tf_sweeps(out, tf_label)
    return out
