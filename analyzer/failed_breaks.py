"""Failed-break detection skeleton module."""

from __future__ import annotations

import pandas as pd


def detect_failed_breaks(df: pd.DataFrame, confirmation_bars: int = 3) -> pd.DataFrame:
    """Attach failed-break placeholders.

    TODO(phase1): implement break/failed/accepted lifecycle with strict
    non-retroactive resolution over ``confirmation_bars``.
    """
    return df.copy()
