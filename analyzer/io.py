"""I/O helpers for analyzer outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_output_dir(output_dir: str | Path) -> Path:
    """Ensure output directory exists and return resolved ``Path``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_dataframe(df: pd.DataFrame, path: str | Path) -> Path:
    """Save dataframe to CSV and return output path."""
    path = Path(path)
    df.to_csv(path, index=False, encoding="utf-8")
    return path
