"""Deterministic intraday context metadata helpers."""

from __future__ import annotations

import pandas as pd

CONTEXT_MODEL_VERSION = "CONTEXT_MODEL_V1_SESSION_UTC"

_EU_OPEN_MINUTES = 8 * 60
_US_OPEN_MINUTES = 13 * 60 + 30
_US_SESSION_END_MINUTES = 21 * 60


def _session_label(minutes_of_day: int) -> str:
    if _EU_OPEN_MINUTES <= minutes_of_day < _US_OPEN_MINUTES:
        return "EU"
    if _US_OPEN_MINUTES <= minutes_of_day < _US_SESSION_END_MINUTES:
        return "US"
    return "ASIA"


def add_context_metadata(df: pd.DataFrame, *, timestamp_col: str = "Timestamp") -> pd.DataFrame:
    """Add deterministic context metadata columns from UTC timestamp values."""
    if timestamp_col not in df.columns:
        raise KeyError(f"Missing required timestamp column for context metadata: {timestamp_col}")

    out = df.copy()
    ts = pd.to_datetime(out[timestamp_col], utc=True)

    minutes_of_day = ts.dt.hour * 60 + ts.dt.minute
    out["session"] = minutes_of_day.map(_session_label)
    out["minutes_from_eu_open"] = (minutes_of_day - _EU_OPEN_MINUTES).astype(int)
    out["minutes_from_us_open"] = (minutes_of_day - _US_OPEN_MINUTES).astype(int)
    out["ContextModelVersion"] = CONTEXT_MODEL_VERSION
    return out

