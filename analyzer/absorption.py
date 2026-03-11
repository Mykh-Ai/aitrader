"""Absorption detection skeleton module."""

from __future__ import annotations

import pandas as pd


def detect_absorption(df: pd.DataFrame) -> pd.DataFrame:
    """Attach absorption placeholders.

    TODO(phase1): implement rule-based absorption flags from bar structure,
    delta response, and context fields.
    """
    return df.copy()
