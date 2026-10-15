"""Hard research phase boundaries; no optimization or automatic next candidate."""
from pathlib import Path
import hashlib
import json

import pandas as pd

WARMUP_START = pd.Timestamp("2025-02-01T00:00:00Z")
OOS_START = pd.Timestamp("2025-03-01T00:00:00Z")
OOS_END = pd.Timestamp("2026-03-09T23:59:00Z")


def scored_entries(entry_at):
    stamps = pd.to_datetime(entry_at, utc=True)
    return (stamps >= OOS_START) & (stamps <= OOS_END)


def rolling_window(frame, decision, hours):
    return frame.loc[frame.Timestamp.gt(decision - pd.Timedelta(hours=hours)) & frame.Timestamp.le(decision)]


def verify_hashes(root, hashes):
    for name, expected in hashes.items():
        actual = hashlib.sha256((Path(root) / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"FROZEN_STRATEGY_OR_SOURCE_CHANGED: {name}")


def decisions_equal(left, right):
    fields = ["timestamp", "raw_direction", "final_direction", "blocker_reasons"]
    a = left[fields].set_index("timestamp")
    b = right[fields].set_index("timestamp")
    indexes = a.index.union(b.index)
    return a.reindex(indexes).eq(b.reindex(indexes)).all(axis=1)


def authorize_first_oos_attempt(folder, manifest):
    folder = Path(folder)
    if manifest["strategy_count"] != 1 or manifest["optimization_allowed"] or manifest["variant_search_allowed"]:
        raise ValueError("NO_OPTIMIZATION_OR_VARIANTS_ALLOWED")
    acceptance = folder / "parity_acceptance.json"
    if not acceptance.exists() or json.loads(acceptance.read_text()).get("status") != "ACCEPTED_100_PERCENT_DECISION_PARITY":
        raise ValueError("SOURCE_PARITY_NOT_ACCEPTED_NO_OOS_ACCESS")
    with (folder / "first_oos_attempt.json").open("x", encoding="utf-8") as stream:
        json.dump({"strategy_count": 1, "variant_search": False, "optimization": False, "attempt": 1}, stream)


def oos_verdict(completed, net, profit_factor, net_without_best_two, causal, frozen, parity):
    if not causal or not frozen or not parity:
        raise ValueError("INVALID_REPLAY_NOT_FINANCIAL_EVIDENCE")
    if completed < 12:
        return "OOS_INSUFFICIENT_SAMPLE"
    if net > 0 and profit_factor >= 1.25 and net_without_best_two > 0:
        return "OOS_SUPPORTS_CONTINUED_VALIDATION"
    return "OOS_REJECTS_CURRENT_CANDIDATE"
