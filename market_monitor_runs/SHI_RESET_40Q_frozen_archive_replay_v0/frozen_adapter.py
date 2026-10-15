"""Date-only source adapter around byte-frozen 40H research modules."""
import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / "market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0"
SOURCE = ROOT / "market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0"
START = pd.Timestamp("2025-03-01T00:00:00Z")
OLD_END = pd.Timestamp("2026-03-09T23:59:00Z")
END = pd.Timestamp("2026-10-14T23:59:00Z")
WARMUP = pd.Timestamp("2025-01-01T00:01:00Z")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str,
                                      allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def load_kernel():
    spec = importlib.util.spec_from_file_location("frozen40O_read_only_kernel", OLD / "research_kernel.py")
    kernel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kernel)
    kernel.identity()
    original = json.loads((OLD / "frozen_identity_verification.json").read_text())
    for name, digest in original["executed_frozen_code_hashes"].items():
        assert sha(kernel.SNAP / name) == digest, f"FROZEN_CODE_CHANGED: {name}"
    return kernel


def calendar_adapter(function):
    """Remove only the three frozen SHI-specific calendar admission statements."""
    tree = ast.parse(inspect.getsource(function))
    body = tree.body[0].body
    removed, kept = [], []
    for node in body:
        expression = ast.unparse(node)
        is_calendar = (
            isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
            and node.target.id == "quality" and "bars.timestamp" in expression
        ) or (isinstance(node, ast.For) and "2026-06-22" in expression
              and "bars.timestamp" in expression)
        (removed if is_calendar else kept).append(node)
    assert len(removed) == 3, "UNEXPECTED_FROZEN_CALENDAR_STRUCTURE"
    assert all("2026-" in ast.unparse(node) for node in removed)
    tree.body[0].body = kept
    ast.fix_missing_locations(tree)
    source = ast.unparse(tree) + "\n"
    # Prove the entire non-calendar AST, including every threshold, is unchanged.
    recovered = ast.parse(source)
    assert ast.dump(recovered, include_attributes=False) == ast.dump(tree, include_attributes=False)
    formula_sha = hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()
    namespace = dict(function.__globals__)
    exec(compile(tree, str(OUT / "calendar_signal_adapter.py"), "exec"), namespace)
    return namespace[function.__name__], source, {
        "removed_calendar_statements": [ast.unparse(node) for node in removed],
        "removed_count": 3, "all_noncalendar_formula_AST_unchanged": True,
        "noncalendar_formula_AST_sha256": formula_sha,
        "admission_applied_separately": "Continuous archive decisions March2025 through October14 2026; matched source comparison uses the frozen40L calendar",
    }


def install_calendar(kernel):
    namespace = kernel.hybrid_signals.__globals__
    adapted, source, evidence = calendar_adapter(namespace["signals"])
    generated = OUT / "calendar_signal_adapter.py"
    assert generated.read_text(encoding="utf-8") == source, "CALENDAR_ADAPTER_NOT_FROZEN"
    namespace["signals"] = adapted
    return evidence


def precise_data_class(kernel):
    class PreciseEntryData(kernel.ReplayData):
        """Same entry minute/open; unused future first-hour summaries not read.

        Extends the already-declared 40L last-H1 precise-entry adapter to every
        index. Precise trade_path ignores these three auxiliary tuple fields.
        """
        def entry(self, i):
            if i in self.entries:
                return self.entries[i]
            planned = self.available[i] + 2 * self.minute
            p = int(np.searchsorted(self.minute_ts, planned))
            if p >= len(self.minute_ts) or self.minute_ts[p] - planned > self.minute or not self.raw[p]:
                self.entries[i] = None
                return None
            item = (p, self.minute_ts[p] - self.minute, self.mo[p], self.mh[p], self.ml[p], bool(self.raw[p]))
            self.entries[i] = item
            return item
    return PreciseEntryData


def classify(trades):
    result = trades.copy()
    result["status_at_cutoff"] = "CLOSED"
    incomplete = result.censored
    result.loc[incomplete, "status_at_cutoff"] = "CENSORED_DATA"
    tail = incomplete & result.exit_reason.isin(["OPEN", "CENSORED_TAIL"]) & result.expiry_at.gt(END)
    result.loc[tail, "status_at_cutoff"] = "OPEN_AT_CUTOFF"
    return result


def verdict(completed, net, pf, without_best_two, censored, causal=True, frozen=True):
    if not causal or not frozen:
        return "ARCHIVE_REPLAY_INVALID"
    if censored:
        return "ARCHIVE_REPLAY_INCOMPLETE_DATA"
    if completed < 12:
        return "ARCHIVE_REPLAY_INSUFFICIENT_SAMPLE"
    pf_pass = pf == "INFINITE" or isinstance(pf, (int, float)) and pf >= 1.25
    if net > 0 and pf_pass and without_best_two > 0:
        return "ARCHIVE_REPLAY_FINANCIAL_CRITERIA_MET_SOURCE_UNVALIDATED"
    return "ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE"


def authorize_first_replay(manifest):
    assert manifest["user_authorized_archive_diagnostic_after_parity_warning"]
    assert manifest["strategy_count"] == 1 and not manifest["optimization_allowed"] and not manifest["variant_search_allowed"]
    assert not manifest["source_parity_accepted"], "THIS_IS_NOT_A_40O_PARITY_ACCEPTANCE"
    with (OUT / "first_replay_attempt.json").open("x", encoding="utf-8") as stream:
        json.dump({"attempt": 1, "run_manifest_sha256": sha(OUT / "run_manifest.json"),
                   "source_parity_accepted": False, "optimization": False}, stream, indent=2)
