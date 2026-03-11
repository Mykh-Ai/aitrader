"""Sweep detection skeleton module."""

from __future__ import annotations

import pandas as pd


def detect_sweeps(df: pd.DataFrame) -> pd.DataFrame:
    """Attach sweep placeholders.

    TODO(phase1): implement first-cross sweep detection against ACTIVE/TESTED
    swings using symbol tick size constraints.
    """
    return df.copy()
