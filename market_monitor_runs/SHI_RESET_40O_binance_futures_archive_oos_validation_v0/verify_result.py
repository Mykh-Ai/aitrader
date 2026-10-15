"""Independent artifact/count/source/freeze checks for the terminal40O gate."""
from pathlib import Path
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def intended_files():
    return sorted(p for p in OUT.rglob("*") if p.is_file() and not p.is_symlink()
                  and (len(p.relative_to(OUT).parts) == 1 or p.relative_to(OUT).parts[0] in {"official_archives", "normalized_futures_feed"})
                  and p.suffix not in {".pyc", ".pyo"})


def main():
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    assert manifest["starting_commit"] == "def5060680b31b6639c39d3e00b061ccf147d4c9"
    for path, expected in manifest["immutable_source_and_strategy_hashes"].items():
        assert sha(ROOT / path) == expected, path
    prior = json.loads((ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/study_manifest.json").read_text())
    assert all(sha(ROOT / name) == expected for name, expected in prior["source_hashes"].items())
    for task, index in [("SHI_RESET_40H_loss_metrics_filter_study_v0", "artifact_hashes.json"),
                        ("SHI_RESET_40L_chronological_replay_through_2026_10_14_v0", "artifact_hashes.json"),
                        ("SHI_RESET_40D_own_signal_strategy_search_v0", "selected_artifact_hashes.json")]:
        folder = ROOT / "market_monitor_runs" / task
        saved = json.loads((folder / index).read_text())
        assert all(sha(folder / name) == expected for name, expected in saved.items()), task
    original = json.loads((OUT / "frozen_identity_verification.json").read_text())
    assert original["original_control_trades"] == 13 and abs(original["original_control_net_usdc"] - 1090.8118508490645) < 1e-8
    hashes = []
    for path, expected in original["executed_frozen_code_hashes"].items():
        actual = sha(OUT / "frozen_snapshot" / path)
        assert actual == expected, path
        hashes.append({"scope": "ORIGINAL_FROZEN_EXECUTED", "path": path, "sha256": actual})
    for p in sorted(OUT.glob("*.py")):
        hashes.append({"scope": "40O_RESEARCH_TOOLING", "path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)})
    for name in ["tests/test_binance_futures_archive_oos_validation.py", "tests/test_own_signal_run_preparation.py",
                 "tests/test_strategy_search_replay.py", "market_monitor_runs/SHI_RESET_40N_git_publication_v0/reproduce_snapshot.py"]:
        hashes.append({"scope": "TEST_OR_SNAPSHOT_RECOVERY", "path": name, "sha256": sha(ROOT / name)})
    pd.DataFrame(hashes).to_csv(OUT / "code_hashes.csv", index=False)
    execution = json.loads((OUT / "parity_execution_manifest.json").read_text())
    assert all(sha(OUT / name) == expected for name, expected in execution["task_code_hashes"].items())
    source = json.loads((OUT / "source_manifest.json").read_text())
    assert len(source["archives"]) == 27 and not source["OOS_downloaded"] and not source["OOS_outcomes_read"]
    for row in source["archives"]:
        assert row["date"] >= "2026-03-11" and row["source_type"] == "klines" and row["status"] == "CHECKSUM_VERIFIED"
        file = OUT / row["archive_path"]
        official, filename = (file.parent / (file.name + ".CHECKSUM")).read_text().strip().split()[:2]
        assert sha(file) == row["local_sha256"] == row["binance_checksum_sha256"] == official
        assert filename.lstrip("*") == file.name and file.stat().st_size == row["bytes"]
    normalization = json.loads((OUT / "normalization_manifest.json").read_text())
    assert normalization["rows"] == 292935
    assert all(sha(OUT / "normalized_futures_feed" / name) == expected for name, expected in normalization["files"].items())
    raw = json.loads((OUT / "raw_parity_summary.json").read_text())
    assert len(pd.read_csv(OUT / "raw_parity_mismatches.csv")) == raw["minutes_with_any_mismatch"] == 72690
    f = pd.read_csv(OUT / "feature_parity.csv")
    summary = json.loads((OUT / "feature_parity_summary.json").read_text())
    assert len(f) == summary["comparisons"] == 61488 and int((~f.equal).sum()) == summary["mismatches"] == 16888
    c = pd.read_csv(OUT / "candidate_parity.csv")
    assert len(c) == 1464
    assert int((~c.decision_equal).sum()) == int((~c.final_direction_equal).sum()) == 1
    bad = c.loc[~c.decision_equal].iloc[0]
    assert pd.Timestamp(bad.timestamp) == pd.Timestamp("2026-07-05T08:00Z") and bad.final_direction_shi == 0 and bad.final_direction_archive == 1
    state = pd.read_csv(OUT / "prior_history_and_reference_parity.csv")
    at = state.loc[pd.to_datetime(state.timestamp, utc=True).eq(pd.Timestamp("2026-07-05T08:00Z"))].set_index("source")
    assert not at.loc["SHI", "prior96_usable"] and at.loc["BINANCE_KLINES", "prior96_usable"]
    gate = json.loads((OUT / "parity_gate.json").read_text())
    assert gate["status"] == "BINANCE_KLINE_SURROGATE_PARITY_FAILED" and not gate["accepted"] and not gate["OOS_execution_allowed"]
    assert not (OUT / "parity_acceptance.json").exists() and not (OUT / "first_oos_attempt.json").exists()
    for name in ["oos_candidates.csv", "oos_trades.csv", "oos_monthly_summary.csv"]:
        assert pd.read_csv(OUT / name).empty
    oos = json.loads((OUT / "oos_metrics.json").read_text())
    assert oos["status"] == "NOT_RUN_SOURCE_PARITY_FAILED" and all(v is None for v in oos["metrics"].values())
    causality = json.loads((OUT / "causality_checks.json").read_text())
    assert causality["status"] == "PASS" and not causality["OOS_observations_or_returns_accessed"]
    assert all(r["all_features_H4_candidates_filters_identical"] for r in causality["real_prefix_results"])
    tests = {}
    for name in ["test_contracts.xml", "test_regression.xml"]:
        suite = next(ET.parse(OUT / name).getroot().iter("testsuite"))
        assert int(suite.attrib["errors"]) == int(suite.attrib["failures"]) == 0
        tests[name] = int(suite.attrib["tests"])
    assert tests == {"test_contracts.xml": 23, "test_regression.xml": 784}
    audit = ROOT / "research/canonical/SHI_RESET_40O_BINANCE_FUTURES_ARCHIVE_OOS_VALIDATION_AUDIT_2026_10_15.md"
    targets = []
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", audit.read_text(encoding="utf-8")):
        if not link.startswith(("https://", "http://", "#")):
            path = (audit.parent / link).resolve()
            assert path.is_relative_to(ROOT) and path.exists(), link
            targets.append(path)
    report = {"status": "PASS_TERMINAL_SOURCE_GATE_AND_ARTIFACTS_VERIFIED", "verdict": gate["status"],
              "original_strategy_control_exactly_reproduced": True, "all_executed_code_hashes_recorded": True,
              "all232protected_source_hashes_unchanged": True, "all_old40D40H40L_artifact_hashes_unchanged": True,
              "all27official_checksums_match": True, "all_normalized_source_hashes_match": True,
              "candidate_gate_mismatch_independently_counted": True, "all_OOS_metrics_null_and_outputs_not_run": True,
              "OOS_unseen_no_attempt_marker": True, "real_prefix_causality_checks_pass": True,
              "tests": tests, "canonical_local_links_checked": len(targets), "variants": 1, "optimization": False}
    save("verification.json", report)
    files = [p for p in intended_files() if p.name != "artifact_hashes.json"]
    save("artifact_hashes.json", {p.relative_to(OUT).as_posix(): sha(p) for p in files})
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
