"""Base metric computations for Analyzer.

Phase 0: function signatures and pipeline wiring only.
"""

from __future__ import annotations

import pandas as pd


def add_base_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return frame with base metrics.

    TODO(phase1): implement locked formulas from Spec v1.0 section 1 using
    anti-lookahead-safe rolling operations.
    """
    return df.copy()
