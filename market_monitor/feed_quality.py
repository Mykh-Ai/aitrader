from __future__ import annotations

import json
from collections.abc import Iterable

import pandas as pd


DEFAULT_WINDOWS_MINUTES = (5, 15, 30, 60, 240, 1440)

WINDOW_QUALITY_COLUMNS = [
    "cutoff_timestamp",
    "window_minutes",
    "window_start",
    "window_end",
    "expected_rows",
    "rows_used",
    "missing_timestamps",
    "duplicate_rows",
    "data_quality_counts",
    "completion_status",
]


def causal_slice(feed: pd.DataFrame, cutoff) -> pd.DataFrame:
    cutoff_ts = _utc_minute(cutoff)
    return feed.loc[feed["Timestamp"] <= cutoff_ts].copy()


def build_window_quality(
    feed: pd.DataFrame,
    cutoff,
    *,
    windows: Iterable[int] = DEFAULT_WINDOWS_MINUTES,
) -> pd.DataFrame:
    cutoff_ts = _utc_minute(cutoff)
    causal = causal_slice(feed, cutoff_ts)
    rows: list[dict[str, object]] = []
    for minutes_value in windows:
        minutes = int(minutes_value)
        if minutes < 1:
            raise ValueError("window minutes must be positive")
        start = cutoff_ts - pd.Timedelta(minutes=minutes - 1)
        expected = pd.date_range(start=start, end=cutoff_ts, freq="min", tz="UTC")
        window = causal.loc[
            (causal["Timestamp"] >= start) & (causal["Timestamp"] <= cutoff_ts)
        ].copy()
        timestamp_counts = window["Timestamp"].value_counts()
        if "IsSynthetic" in window:
            window.loc[pd.to_numeric(window.IsSynthetic, errors="raise").ne(0), "DataQuality"] = "SYNTHETIC"
        usable = ~window.DataQuality.isin(["SYNTHETIC", "INVALID"])
        unique_timestamps = pd.DatetimeIndex(window.loc[usable, "Timestamp"].unique()).sort_values()
        missing = expected.difference(unique_timestamps)
        duplicate_rows = int((timestamp_counts - 1).clip(lower=0).sum())
        quality_counts = {
            str(key): int(value)
            for key, value in window["DataQuality"].astype(str).value_counts().sort_index().items()
        }
        rows.append(
            {
                "cutoff_timestamp": _format_ts(cutoff_ts),
                "window_minutes": minutes,
                "window_start": _format_ts(start),
                "window_end": _format_ts(cutoff_ts),
                "expected_rows": minutes,
                "rows_used": int(len(unique_timestamps)),
                "missing_timestamps": "|".join(_format_ts(value) for value in missing),
                "duplicate_rows": duplicate_rows,
                "data_quality_counts": json.dumps(quality_counts, sort_keys=True, separators=(",", ":")),
                "completion_status": _completion_status(
                    rows_used=len(unique_timestamps),
                    expected_rows=minutes,
                    missing_count=len(missing),
                    duplicate_rows=duplicate_rows,
                    quality_counts=quality_counts,
                ),
            }
        )
    return pd.DataFrame(rows, columns=WINDOW_QUALITY_COLUMNS)


def _completion_status(
    *,
    rows_used: int,
    expected_rows: int,
    missing_count: int,
    duplicate_rows: int,
    quality_counts: dict[str, int],
) -> str:
    if rows_used == 0:
        return "EMPTY"
    if rows_used != expected_rows or missing_count or duplicate_rows:
        return "PARTIAL"
    qualities = set(quality_counts)
    if qualities == {"RAW"}:
        return "COMPLETE_RAW"
    if qualities <= {"RAW", "RECOVERED_DEGRADED"} and "RECOVERED_DEGRADED" in qualities:
        return "COMPLETE_RECOVERED_DEGRADED"
    return "COMPLETE_DEGRADED"


def _utc_minute(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
    return timestamp.floor("min")


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")
