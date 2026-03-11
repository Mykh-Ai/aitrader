"""Swing detection module skeleton.

Phase 0 contains signatures only (no swing logic yet).
"""

from __future__ import annotations

import pandas as pd


def annotate_swings(df: pd.DataFrame) -> pd.DataFrame:
    """Annotate dataframe with swing-related placeholders.

    TODO(phase1): implement H1/H4 fractal swing confirmation with explicit
    delayed confirmation to avoid lookahead bias.
    """
    return df.copy()
