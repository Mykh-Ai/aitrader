"""Input loader for analyzer raw 1-minute feed."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import SchemaValidationError, missing_required_columns


def load_raw_csv(path: str | Path) -> pd.DataFrame:
    """Load and minimally validate raw aggregator CSV.

    Phase 0 behavior:
    - parse ``Timestamp`` as UTC datetime
    - verify required columns exist
    - sort ascending by ``Timestamp``
    - preserve ``IsSynthetic`` column without transformation
    """
    path = Path(path)
    df = pd.read_csv(path)

    missing = missing_required_columns(df.columns.tolist())
    if missing:
        joined = ", ".join(missing)
        raise SchemaValidationError(f"Missing required raw columns: {joined}")

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="raise")
    df = df.sort_values("Timestamp", ascending=True, kind="mergesort").reset_index(drop=True)
    return df
