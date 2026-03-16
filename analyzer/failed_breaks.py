"""Failed-break detection built on top of materialized sweep facts (Phase 1D)."""

from __future__ import annotations

import pandas as pd

FAILED_BREAK_FEATURE_COLUMNS = [
    "FailedBreak_H1_Up",
    "FailedBreak_H1_Down",
    "FailedBreak_H1_Direction",
    "FailedBreak_H1_ReferenceLevel",
    "FailedBreak_H1_ReferenceSweepTs",
    "FailedBreak_H1_ConfirmedTs",
    "FailedBreak_H4_Up",
    "FailedBreak_H4_Down",
    "FailedBreak_H4_Direction",
    "FailedBreak_H4_ReferenceLevel",
    "FailedBreak_H4_ReferenceSweepTs",
    "FailedBreak_H4_ConfirmedTs",
]

MAX_STATE_GAP_MINUTES = 3


def _init_failed_break_columns(out: pd.DataFrame, tf_label: str) -> None:
    out[f"FailedBreak_{tf_label}_Up"] = False
    out[f"FailedBreak_{tf_label}_Down"] = False
    out[f"FailedBreak_{tf_label}_Direction"] = pd.Series(pd.NA, index=out.index, dtype="object")
    out[f"FailedBreak_{tf_label}_ReferenceLevel"] = pd.Series(
        pd.NA, index=out.index, dtype="Float64"
    )
    out[f"FailedBreak_{tf_label}_ReferenceSweepTs"] = pd.Series(pd.NaT, index=out.index, dtype="object")
    out[f"FailedBreak_{tf_label}_ConfirmedTs"] = pd.Series(pd.NaT, index=out.index, dtype="object")


def _annotate_tf_failed_breaks(out: pd.DataFrame, tf_label: str, confirmation_bars: int) -> None:
    sweep_dir_col = f"Sweep_{tf_label}_Direction"
    sweep_level_col = f"Sweep_{tf_label}_ReferenceLevel"
    sweep_ts_col = f"Sweep_{tf_label}_ReferenceTs"

    up_col = f"FailedBreak_{tf_label}_Up"
    down_col = f"FailedBreak_{tf_label}_Down"
    direction_col = f"FailedBreak_{tf_label}_Direction"
    ref_level_col = f"FailedBreak_{tf_label}_ReferenceLevel"
    ref_sweep_ts_col = f"FailedBreak_{tf_label}_ReferenceSweepTs"
    confirmed_ts_col = f"FailedBreak_{tf_label}_ConfirmedTs"

    pending_direction: str | None = None
    pending_level: float | None = None
    pending_sweep_ts = pd.NaT
    pending_bar_pos: int | None = None
    previous_ts = pd.NaT

    close = pd.to_numeric(out["Close"], errors="coerce")
    sweep_level = pd.to_numeric(out[sweep_level_col], errors="coerce")
    ts = pd.to_datetime(out["Timestamp"], utc=True)

    synthetic_mask = pd.Series(False, index=out.index)
    if "IsSynthetic" in out.columns:
        synthetic_mask = pd.to_numeric(out["IsSynthetic"], errors="coerce").fillna(0).astype(int) == 1

    for bar_pos, idx in enumerate(out.index):
        current_ts = ts.loc[idx]
        if pd.notna(previous_ts) and pd.notna(current_ts):
            gap_minutes = (current_ts - previous_ts).total_seconds() / 60.0
            if gap_minutes > MAX_STATE_GAP_MINUTES:
                pending_direction = None
                pending_level = None
                pending_sweep_ts = pd.NaT
                pending_bar_pos = None

        if (
            pending_direction is not None
            and pending_bar_pos is not None
            and (bar_pos - pending_bar_pos) > confirmation_bars
        ):
            pending_direction = None
            pending_level = None
            pending_sweep_ts = pd.NaT
            pending_bar_pos = None

        # Confirmation always evaluates only previously pending state.
        if (
            not synthetic_mask.loc[idx]
            and pending_direction == "up"
            and pd.notna(close.loc[idx])
            and pending_level is not None
        ):
            if close.loc[idx] < pending_level:
                out.at[idx, up_col] = True
                out.at[idx, direction_col] = "up"
                out.at[idx, ref_level_col] = pending_level
                out.at[idx, ref_sweep_ts_col] = pending_sweep_ts
                out.at[idx, confirmed_ts_col] = out.at[idx, "Timestamp"]
                pending_direction = None
                pending_level = None
                pending_sweep_ts = pd.NaT
                pending_bar_pos = None
        elif (
            not synthetic_mask.loc[idx]
            and pending_direction == "down"
            and pd.notna(close.loc[idx])
            and pending_level is not None
        ):
            if close.loc[idx] > pending_level:
                out.at[idx, down_col] = True
                out.at[idx, direction_col] = "down"
                out.at[idx, ref_level_col] = pending_level
                out.at[idx, ref_sweep_ts_col] = pending_sweep_ts
                out.at[idx, confirmed_ts_col] = out.at[idx, "Timestamp"]
                pending_direction = None
                pending_level = None
                pending_sweep_ts = pd.NaT
                pending_bar_pos = None

        # Current bar sweeps become pending only for subsequent bars.
        current_dir = out.at[idx, sweep_dir_col]
        current_level = sweep_level.loc[idx]
        if (
            not synthetic_mask.loc[idx]
            and isinstance(current_dir, str)
            and current_dir in {"up", "down"}
            and pd.notna(current_level)
        ):
            pending_direction = current_dir
            pending_level = float(current_level)
            pending_sweep_ts = out.at[idx, "Timestamp"]
            pending_bar_pos = bar_pos

        previous_ts = current_ts

    out[ref_sweep_ts_col] = pd.to_datetime(out[ref_sweep_ts_col], utc=True)
    out[confirmed_ts_col] = pd.to_datetime(out[confirmed_ts_col], utc=True)


def detect_failed_breaks(df: pd.DataFrame, confirmation_bars: int = 5) -> pd.DataFrame:
    """Annotate failed-break confirmations on top of materialized sweep facts.

    Conservative confirmation model:
    - sweep bars create pending break candidates
    - confirmation requires a later bar close reclaiming through the swept level
      * upward sweep fails when a later bar closes below the swept level
      * downward sweep fails when a later bar closes above the swept level
    - no retroactive marking on the sweep bar itself

    ``confirmation_bars`` sets how many bars after a sweep remain eligible for
    failed-break confirmation. It is a model/lifecycle parameter for pending
    failed-break validity, not a claim that later confirmations are inherently
    poor-quality market structure.
    """
    if confirmation_bars < 1:
        raise ValueError("confirmation_bars must be >= 1")

    out = df.copy()

    required = {"Timestamp", "Close"}
    missing_base = required - set(out.columns)
    if missing_base:
        raise KeyError(f"Missing required columns for failed-break detection: {sorted(missing_base)}")

    for tf_label in ("H1", "H4"):
        _init_failed_break_columns(out, tf_label)
        required_tf = {
            f"Sweep_{tf_label}_Direction",
            f"Sweep_{tf_label}_ReferenceLevel",
            f"Sweep_{tf_label}_ReferenceTs",
        }
        if required_tf.issubset(out.columns):
            _annotate_tf_failed_breaks(out, tf_label, confirmation_bars)

    return out
