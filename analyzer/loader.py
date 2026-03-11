"""Input loader for analyzer raw 1-minute feed."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import (
    NUMERIC_RAW_COLUMNS,
    SchemaValidationError,
    missing_required_columns,
    non_numeric_required_columns,
)


_IS_SYNTHETIC_NORMALIZATION = {
    0: 0,
    1: 1,
    0.0: 0,
    1.0: 1,
    False: 0,
    True: 1,
    "0": 0,
    "1": 1,
    "false": 0,
    "true": 1,
    "False": 0,
    "True": 1,
}


def _coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce required numeric columns, failing loudly on invalid/missing values."""
    out = df.copy()
    missing_numeric = non_numeric_required_columns(out.columns.tolist())
    if missing_numeric:
        joined = ", ".join(missing_numeric)
        raise SchemaValidationError(f"Missing numeric raw columns: {joined}")

    for col in NUMERIC_RAW_COLUMNS:
        coerced = pd.to_numeric(out[col], errors="coerce")
        bad_mask = coerced.isna()
        if bad_mask.any():
            bad_values = out.loc[bad_mask, col].astype(str).unique().tolist()
            sample = ", ".join(bad_values[:3])
            raise SchemaValidationError(
                f"Invalid numeric raw values in column '{col}': {sample}"
            )
        out[col] = coerced
    return out


def _normalize_is_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize strict bool-like IsSynthetic values to {0,1}, otherwise fail."""
    out = df.copy()
    normalized = out["IsSynthetic"].map(_IS_SYNTHETIC_NORMALIZATION)
    invalid_mask = normalized.isna()
    if invalid_mask.any():
        bad_values = out.loc[invalid_mask, "IsSynthetic"].astype(str).unique().tolist()
        sample = ", ".join(bad_values[:3])
        raise SchemaValidationError(
            f"Invalid IsSynthetic values (allowed: 0 or 1): {sample}"
        )
    out["IsSynthetic"] = normalized.astype(int)
    return out


def load_raw_csv(path: str | Path) -> pd.DataFrame:
    """Load and minimally validate raw aggregator CSV.

    Phase 1A behavior:
    - parse ``Timestamp`` as UTC datetime
    - verify required columns exist
    - validate required numeric columns are numeric-coercible and non-empty
    - normalize and validate ``IsSynthetic`` to strict {0,1}
    - sort ascending by ``Timestamp``
    - fail on duplicate ``Timestamp`` rows
    - preserve gaps (no synthetic backfill/fill)
    """
    path = Path(path)
    df = pd.read_csv(path)

    missing = missing_required_columns(df.columns.tolist())
    if missing:
        joined = ", ".join(missing)
        raise SchemaValidationError(f"Missing required raw columns: {joined}")

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="raise")
    df = _coerce_numeric_columns(df)
    df = _normalize_is_synthetic(df)

    df = df.sort_values("Timestamp", ascending=True, kind="mergesort").reset_index(drop=True)

    duplicate_mask = df["Timestamp"].duplicated(keep=False)
    if duplicate_mask.any():
        dupes = df.loc[duplicate_mask, "Timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").unique()
        joined = ", ".join(dupes[:5])
        raise SchemaValidationError(f"Duplicate Timestamp values found: {joined}")

    return df
