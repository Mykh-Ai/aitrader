"""Event table helpers for analyzer."""

from __future__ import annotations

import pandas as pd

from .schema import EVENT_COLUMNS


def build_events(df: pd.DataFrame) -> pd.DataFrame:
    """Build event table from annotated features.

    Phase 0 returns an empty event table with locked schema columns.
    """
    _ = df
    return pd.DataFrame(columns=EVENT_COLUMNS)
