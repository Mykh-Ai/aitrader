"""Certify a carried checkpoint across strictly bounded performance edits.

Runs the actual old and current canonical functions, never a replay adapter.
Does not mutate the original checkpoint or bless an unrelated state revision.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from market_monitor import zone_registry, events, label_taxonomy
from tools.verify_market_monitor_integrity import OUT, digest, sources, decision_digest


def main():
    base = "572cbbdaef330e014e8cc6f7a05e7d60ecdf1acd"
    path = OUT / "publication_full_state.pkl"
    saved = pickle.loads(path.read_bytes())
    changes = {
        "market_monitor/zone_registry.py": (zone_registry, {"_sweep_transition_timestamps", "_consecutive_threshold_at", "_unchanged_interaction_cache"}),
        "market_monitor/events.py": (events, {"build_market_move_groups"}),
        "market_monitor/label_taxonomy.py": (label_taxonomy, {"build_sweep_label_frames", "_groups_by_move"}),
    }
    identity = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "market_monitor").glob("*.py"))}
    assert set(identity) == set(saved["identity"])
    replacements = []
    function_pairs = []
    for filename, old_hash in saved["identity"].items():
        git_name = Path(filename).as_posix()
        old_bytes = subprocess.check_output(["git", "show", base + ":" + git_name], cwd=ROOT)
        if git_name in changes:
            # The published receipt pins normalized Git blobs as well as the
            # raw Windows working-file hashes used by the old checkpoint.
            receipt = json.loads((OUT / "publication_verification.json").read_text())
            assert receipt["canonical_code_identity"][filename] == old_hash
            blob = subprocess.check_output(["git", "rev-parse", base + ":" + git_name], cwd=ROOT, text=True).strip()
            assert receipt["remote_file_blobs"][git_name] == blob
        if git_name not in changes:
            assert identity[filename] == old_hash
            continue
        module, allowed = changes[git_name]
        old_tree = ast.parse(old_bytes.decode("utf-8"))
        new_tree = ast.parse((ROOT / filename).read_text())
        def remainder(tree):
            return ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n, ast.FunctionDef) or n.name not in allowed], type_ignores=[]), include_attributes=False)
        assert remainder(old_tree) == remainder(new_tree), filename
        for node in old_tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in allowed:
                current = getattr(module, node.name)
                exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), module.__dict__)
                replacements.append((module, node.name, current))
                function_pairs.append((current, getattr(module, node.name)))
    # Canonical consumers import some functions directly. The reference run
    # must replace those bound imports too, not merely module attributes.
    old_by_id = {id(current): old for current, old in function_pairs}
    for imported in list(sys.modules.values()):
        if imported is None or not getattr(imported, "__name__", "").startswith("market_monitor."):
            continue
        for name, value in list(vars(imported).items()):
            if id(value) in old_by_id:
                replacements.append((imported, name, value))
                setattr(imported, name, old_by_id[id(value)])
    monitor = saved["monitor"]
    first = monitor.cutoff + pd.Timedelta(hours=1)
    feed, files = sources(first + pd.Timedelta(hours=1))
    old_times, new_times, expected = [], [], []
    for cutoff in [first, first + pd.Timedelta(hours=1)]:
        start = time.monotonic()
        decision = monitor.update(feed, cutoff)
        expected.append(decision_digest(decision))
        old_times.append(time.monotonic() - start)
    baseline = monitor
    for module, name, current in replacements:
        setattr(module, name, current)
    saved = pickle.loads(path.read_bytes())
    monitor = saved["monitor"]
    for index, cutoff in enumerate([first, first + pd.Timedelta(hours=1)]):
        start = time.monotonic()
        decision = monitor.update(feed, cutoff)
        assert decision_digest(decision) == expected[index], str(cutoff)
        new_times.append(time.monotonic() - start)
    for field in ["registry", "events", "completed_observations", "market_moves", "taxonomy", "review_windows"]:
        pd.testing.assert_frame_equal(getattr(monitor, field), getattr(baseline, field), check_exact=True)
    pd.testing.assert_frame_equal(monitor.structure.levels, baseline.structure.levels, check_exact=True)
    for field in ["flow_rows", "previous_states", "setup_context", "decision_count", "cutoff"]:
        assert json.dumps(getattr(monitor, field), sort_keys=True, default=str) == json.dumps(getattr(baseline, field), sort_keys=True, default=str), field
    certificate = {"source_checkpoint": str(path), "source_checkpoint_sha256": digest(path),
        "source_code_identity": saved["identity"], "target_code_identity": identity,
        "bounded_functions": {k: sorted(v[1]) for k, v in changes.items()},
        "exact_decision_and_carried_state_parity": True, "verified_hours": [str(first), str(first + pd.Timedelta(hours=1))],
        "old_seconds": old_times, "new_seconds": new_times,
        "source_files": files, "state_reset": False}
    (OUT / "runtime_checkpoint_certificate.json").write_text(json.dumps(certificate, indent=2))
    # Keep the original cutoff and every carried-state field, not the two
    # diagnostic advances. Only the proven-compatible code identity changes.
    saved = pickle.loads(path.read_bytes())
    saved["identity"] = identity
    saved["performance_migration_certificate"] = digest(OUT / "runtime_checkpoint_certificate.json")
    (OUT / "runtime_certified_seed.pkl").write_bytes(pickle.dumps(saved, protocol=pickle.HIGHEST_PROTOCOL))
    print(json.dumps({"status": "EXACT_PARITY", "old_seconds": old_times, "new_seconds": new_times,
        "resumable_from": str(saved["monitor"].cutoff)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
