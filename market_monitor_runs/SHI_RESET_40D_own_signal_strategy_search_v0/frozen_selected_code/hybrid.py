"""Frozen research candidate: directional setup families, one global book."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import signals
from .replay import ExitRules, ReplayData, trade_path


def hybrid_signals(bars: pd.DataFrame, long: dict, short: dict) -> np.ndarray:
    fields = ["family", "lookback", "flow", "volume", "trend"]
    long_signals = signals(bars, *[long[k] for k in fields])
    short_signals = signals(bars, *[short[k] for k in fields])
    long_signals[((bars.close - bars.ema24).abs() / bars.atr > long["maturity"])
                 | ((bars.high - bars.low) / bars.atr > long["impulse"])] = 0
    # Conflicting families cannot be selected by the subsequent outcome.
    return np.where((long_signals > 0) & (short_signals >= 0), 1,
                    np.where((short_signals < 0) & (long_signals <= 0), -1, 0))


def replay_hybrid(data: ReplayData, direction: np.ndarray, long: dict, short: dict) -> pd.DataFrame:
    rows, busy = [], -1
    for i in np.flatnonzero(direction):
        if data.available[i] + data.minute <= busy:
            continue
        config = long if direction[i] > 0 else short
        trade = trade_path(data, int(i), int(direction[i]), ExitRules(**config["exit"]), precise=True, gap_policy="CENSOR")
        if trade is None:
            continue
        trade["family"] = config["family"]
        rows.append(trade)
        end = trade["expiry_at"] if trade["censored"] else trade["exit_at"]
        busy = end.value + 3 * data.minute
    return pd.DataFrame(rows)
