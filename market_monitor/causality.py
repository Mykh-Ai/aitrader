"""Shared evidence clocks for canonical historical consumers.

An old daily snapshot without an explicit availability clock is available only
at the end of its source day. Filtering a later snapshot cannot reconstruct
its earlier lifecycle; callers must supply the earlier frozen snapshot.
"""
from __future__ import annotations

import pandas as pd

AVAILABILITY_COLUMNS = (
    "snapshot_available_at_utc", "selection_cutoff_utc", "latest_consumed_evidence_at_utc",
    "zone_available_at_utc", "LevelAvailableAtUTC", "ConfirmingBarCloseUTC", "created_at", "first_seen_at", "last_updated_at", "last_seen_at",
    "geometry_available_at_utc",
    "lifecycle_processed_at_utc",
    "event_timestamp", "source_event_timestamp", "observation_start_timestamp", "observation_end_timestamp",
    "group_start_timestamp", "group_end_timestamp", "start_timestamp", "end_timestamp",
    "level_timestamp", "source_start", "source_end", "htf_origin_timestamp",
    "first_return_inside_at", "first_close_inside_at", "first_close_beyond_at",
    "invalidated_at", "retired_at", "left_point_timestamp", "head_point_timestamp", "right_point_timestamp",
    "setup_formed_at", "entry_candidate_ts", "decision_at_utc",
    "consumed_at", "last_touch_at", "last_cross_at", "last_clean_reaction_at", "first_sweep_at",
    "drift_away_confirmed_at", "accepted_above_at", "accepted_below_at", "htf_confirmation_timestamp",
)


def utc(value):
    value = pd.Timestamp(value)
    if pd.isna(value):
        raise ValueError("missing causal cutoff")
    return value.tz_localize("UTC") if value.tzinfo is None else value.tz_convert("UTC")


def evidence_times(frame: pd.DataFrame, *, legacy_day_end=True) -> pd.Series:
    clocks = []
    for name in AVAILABILITY_COLUMNS:
        if name in frame:
            raw = frame[name].replace("", pd.NA)
            parsed = pd.to_datetime(raw, utc=True, errors="coerce", format="mixed")
            if (raw.notna() & parsed.isna()).any():
                raise ValueError(f"invalid evidence timestamp: {name}")
            clocks.append(parsed)
    explicit = pd.Series(False, index=frame.index)
    for name in ("snapshot_available_at_utc", "selection_cutoff_utc", "latest_consumed_evidence_at_utc"):
        if name in frame:
            explicit |= frame[name].notna() & frame[name].astype(str).ne("")
    day_name = "_source_day" if "_source_day" in frame else "source_day" if "source_day" in frame else None
    if day_name and legacy_day_end:
        day_clock = (pd.to_datetime(frame[day_name], utc=True, errors="raise").dt.normalize()
                     + pd.Timedelta(hours=23, minutes=59))
        clocks.append(day_clock.where(~explicit))
    if not clocks:
        return pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
    return pd.concat(clocks, axis=1).max(axis=1)


def asof_rows(frame: pd.DataFrame, cutoff, *, require_clock=False) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    available = evidence_times(frame)
    mask = available.le(utc(cutoff))
    if not require_clock:
        mask |= available.isna()  # in-memory legacy fixtures; file callers stamp source_day
    return frame.loc[mask].copy()


def latest_zone_snapshot(frame: pd.DataFrame, cutoff) -> pd.DataFrame:
    out = asof_rows(frame, cutoff)
    if out.empty or "zone_id" not in out:
        return out
    out["_availability"] = evidence_times(out)
    return (out.sort_values("_availability", kind="mergesort")
            .drop_duplicates("zone_id", keep="last").drop(columns="_availability"))
