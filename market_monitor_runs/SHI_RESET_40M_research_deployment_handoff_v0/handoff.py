"""Offline documentation snapshot and read-only transfer verification; stdlib only."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
ROADMAP = ROOT / "research/canonical/SHI_RESET_40M_RESEARCH_AND_DEPLOYMENT_ROADMAP_AUDIT_2026_10_15.md"
L = ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0"
POINTERS = ["research/active_own_signal_selection.json", "research/latest_own_signal_replay.json"]
CACHE = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args, input=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=input, text=True, capture_output=True, check=False)


def local_links():
    targets = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", ROADMAP.read_text(encoding="utf-8")):
        raw = match.group(1).strip().strip("<>")
        if raw.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = (ROADMAP.parent / unquote(raw.split("#", 1)[0])).resolve()
        assert path.is_relative_to(ROOT), f"Link outside repository: {raw}"
        targets.append(path)
    return targets


def admissible(path):
    if path.is_symlink() or not path.is_file() or path.suffix in {".pyc", ".pyo"}:
        return False
    relative = path.relative_to(ROOT)
    if any(part in CACHE for part in relative.parts):
        return False
    # Historical pytest basetemp fixtures are not research trials.
    if any(part.startswith("test_") for part in relative.parts[:-1]):
        return False
    return True


def inventory():
    tracked = set(git("ls-files", "-z").stdout.split("\0")) - {""}
    paths = {ROOT / name for name in tracked if (ROOT / name).exists()}
    for folder in [ROOT / "research/canonical", ROOT / "research/own_signal_run", ROOT / "research/strategy_search"]:
        paths.update(p for p in folder.rglob("*") if admissible(p))
    runs = []
    for folder in sorted((ROOT / "market_monitor_runs").glob("SHI_RESET_40*")):
        if not folder.is_dir() or folder == OUT or "_checks_" in folder.name:
            continue
        runs.append(folder.relative_to(ROOT).as_posix())
        paths.update(p for p in folder.rglob("*") if admissible(p))
    old_replay = ROOT / "market_monitor_runs/SHI_RESET_38W1_fix_chronological_tp1_stop_labels_v0"
    paths.update(p for p in old_replay.rglob("*") if admissible(p))
    manifest = json.loads((L / "study_manifest.json").read_text())
    for name, expected in manifest["source_hashes"].items():
        path = ROOT / name
        assert digest(path) == expected, f"Frozen source changed: {name}"
        paths.add(path)
    paths.update(ROOT / name for name in POINTERS)
    paths.add(Path(__file__).resolve())
    paths.update(p for p in local_links() if p.is_file() and p.parent != OUT)
    names = sorted(p.relative_to(ROOT).as_posix() for p in paths if admissible(p))
    ignored = set(git("check-ignore", "--stdin", "-z", input="\0".join(names) + "\0").stdout.split("\0")) - {""}
    rows = []
    for name in names:
        path = ROOT / name
        role = "FROZEN_RAW_INPUT" if name in manifest["source_hashes"] else "RESEARCH_EVIDENCE" if name.startswith("market_monitor_runs/") else "REPOSITORY_SNAPSHOT"
        rows.append({"path": name, "sha256": digest(path), "bytes": path.stat().st_size, "role": role,
                     "git_tracked_at_snapshot": name in tracked, "git_ignored_at_snapshot": name in ignored})
    with (OUT / "handoff_inventory.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows, runs


def verify_core():
    index = json.loads((OUT / "handoff_index.json").read_text(encoding="utf-8"))
    assert digest(OUT / "handoff_inventory.csv") == index["inventory_sha256"]
    with (OUT / "handoff_inventory.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == index["files"]
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(), f"Missing snapshot file: {row['path']}"
        assert path.stat().st_size == int(row["bytes"]), f"Size changed: {row['path']}"
        assert digest(path) == row["sha256"], f"Bytes changed: {row['path']}"
    targets = local_links()
    assert all(p.exists() for p in targets), "Missing roadmap links: " + ", ".join(str(p) for p in targets if not p.exists())
    for name, expected in index["pointer_hashes"].items():
        assert digest(ROOT / name) == expected
    selected = json.loads((ROOT / POINTERS[0]).read_text())
    assert selected["user_selected_candidate"] == "40H" and selected["selected_variant"] == "LONG_DELTA4_POS_BOTH_BAND4"
    for field in ["selected_contract", "selected_result", "selected_ledger"]:
        assert digest(ROOT / selected[field]) == selected[field + "_sha256"]
    latest = json.loads((ROOT / POINTERS[1]).read_text())
    for field in ["selected_rule_pointer", "journal", "result", "study_manifest", "artifact_hashes"]:
        assert digest(ROOT / latest[field]) == latest[field + "_sha256"]
    for name, expected in json.loads((L / "artifact_hashes.json").read_text()).items():
        assert digest(L / name) == expected
    result = json.loads((L / "result.json").read_text())
    full = result["cohorts"]["full_history"]
    with (L / "trade_journal_usdc.csv").open(newline="", encoding="utf-8") as stream:
        trades = list(csv.DictReader(stream))
    buckets = {"March": [], "April_September": [], "October": []}
    for trade in trades:
        month = int(trade["entry_at"][5:7])
        buckets["March" if month == 3 else "October" if month == 10 else "April_September"].append(trade)
        assert trade["status_at_cutoff"] == "CLOSED"
        e, x, side = float(trade["entry_price"]), float(trade["exit_price"]), int(trade["direction"])
        expected = side * (x - e) * 3000 / e - 5 - (e + x) * 3000 / e * .0002
        assert abs(expected - float(trade["net_usd"])) < 1e-8
    counts = {name: len(group) for name, group in buckets.items()}
    money = {name: sum(float(t["net_usd"]) for t in group) for name, group in buckets.items()}
    assert counts == {"March": 1, "April_September": 12, "October": 1}
    assert len(trades) == full["closed"] == 14
    assert abs(sum(money.values()) - full["net_usd"]) < 1e-8
    assert abs(full["gross_usd"] - full["commission_usd"] - full["slippage_usd"] - full["net_usd"]) < 1e-8
    assert full["open_at_cutoff"] == full["data_censored"] == 0
    return {"status": "PASS_DOCUMENTATION_AND_SNAPSHOT_VERIFIED", "inventory_files": len(rows),
            "roadmap_local_links_checked": len(targets), "all_snapshot_hashes_match": True,
            "chosen40H_and_latest40L_bindings_unchanged": True, "prior40L_artifact_hashes_unchanged": True,
            "March_April_September_October_counts": counts, "net_usdc_by_entry_period": money,
            "full_net_usdc": full["net_usd"], "trade_cash_reconciliation": True,
            "new_financial_replay": False, "new_trading_tests": False,
            "historical40L_validation": "15 tests and14 independent paths; not rerun for documentation task"}


def snapshot():
    assert not (OUT / "handoff_index.json").exists(), "Frozen handoff already exists; verify it or create a successor"
    print("Inventorying existing research evidence and232 frozen sources", flush=True)
    rows, runs = inventory()
    save("handoff_index.json", {"task": "SHI_RESET_40M", "date": "2026-10-15", "status": "DOCUMENTATION_HANDOFF_ONLY",
         "roadmap": ROADMAP.relative_to(ROOT).as_posix(), "roadmap_sha256": digest(ROADMAP),
         "inventory_sha256": digest(OUT / "handoff_inventory.csv"), "files": len(rows), "bytes": sum(r["bytes"] for r in rows),
         "git_head": git("rev-parse", "HEAD").stdout.strip(), "git_worktree_status_at_snapshot": git("status", "--short").stdout.splitlines(),
         "git_head_alone_is_insufficient": True, "included_research_run_roots": runs,
         "excluded": ["Python/test caches", "temporary pytest fixture trees and *_checks_* roots", "symlinks", "credentials/runtime logs/outside-repository Executor"],
         "pointer_hashes": {name: digest(ROOT / name) for name in POINTERS},
         "local_python": platform.python_version(), "recorded_offline_libraries": {"pandas": "2.3.0", "numpy": "2.2.6", "pytest": "9.0.2"},
         "production_promoted": False, "network_or_deployment_performed": False, "source_data_modified": False})
    save("verification.json", {"phase": "VERIFYING_SNAPSHOT"})
    report = verify_core()
    save("verification.json", report)
    package_names = ["handoff.py", "handoff_inventory.csv", "handoff_index.json", "verification.json"]
    save("handoff_package_hashes.json", {name: digest(OUT / name) for name in package_names})
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["snapshot", "verify"])
    args = parser.parse_args()
    if args.mode == "snapshot":
        snapshot()
    else:
        for name, expected in json.loads((OUT / "handoff_package_hashes.json").read_text()).items():
            assert digest(OUT / name) == expected, f"Handoff package changed: {name}"
        print(json.dumps(verify_core(), indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
