"""Post-result integrity checks only; cannot execute or optimize a strategy."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from frozen_adapter import OUT, ROOT, OLD, SOURCE, sha, save
from run_replay import verify_manifest
from reporting import metrics, markdown


def main():
    manifest = verify_manifest()
    preserved = json.loads((SOURCE / "run_manifest.json").read_text())["immutable_prior_file_hashes"]
    for name, expected in preserved.items():
        assert sha(ROOT / name) == expected, name
    for name, expected in json.loads((SOURCE / "artifact_hashes.json").read_text()).items():
        assert sha(SOURCE / name) == expected, name
    for row in manifest["archive_sources"]:
        path = ROOT / row["path"]
        official, name = path.with_name(path.name + ".CHECKSUM").read_text().split()[:2]
        assert sha(path) == official == row["local_sha256"] == row["binance_checksum_sha256"]
        assert path.stat().st_size == row["bytes"] and name.lstrip("*") == path.name
    inventory = pd.read_csv(OUT / "normalized_inventory.csv")
    for row in inventory.itertuples():
        assert sha(OUT / row.file) == row.sha256
    assert inventory.rows.sum() == 938879 and len(inventory) == 652
    saved = json.loads((OUT / "oos_metrics.json").read_text())
    all_trades = {}
    for name, expected in [("continuous_binance", saved["continuous_archive"]), *saved["source_comparison"].items()]:
        trades = pd.read_csv(OUT / f"{name}_trades.csv")
        for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
            trades[col] = pd.to_datetime(trades[col], utc=True)
        actual = metrics(trades)
        for key in ["entered_trades", "completed_trades", "wins", "losses", "gross_usd", "commission_usd", "modeled_slippage_usd", "net_usd", "profit_factor", "max_closed_trade_drawdown_usd", "net_excluding_best_1_usd", "net_excluding_best_2_usd", "net_excluding_best_3_usd"]:
            assert abs(actual[key] - expected[key]) < 1e-8, (name, key)
        assert trades.entry_at.between(manifest["entry_start"], manifest["end"]).all()
        assert trades.exit_at.le(pd.Timestamp(manifest["end"])).all()
        assert ((trades.entry_at - trades.decision_at) == pd.Timedelta(minutes=1)).all()
        assert ((trades.expiry_at - trades.entry_at) == pd.Timedelta(hours=168)).all()
        assert trades.notional_usd_equivalent.eq(3000).all()
        assert trades.execution_market.eq("FUTURES_PRICE_PROXY").all()
        assert trades.commission_usd.eq(5).all()
        assert np.allclose(trades.gross_usd - trades.commission_usd - trades.slippage_usd, trades.net_usd, atol=1e-8)
        monthly = pd.read_csv(OUT / f"{name}_monthly.csv")
        assert abs(monthly.net_usd.sum() - actual["net_usd"]) < 1e-8
        assert monthly.entered_trades.sum() == len(trades)
        all_trades[name] = trades
    earlier = pd.read_csv(OUT / "older_interval_trades_to_2026_03_09.csv")
    assert pd.to_datetime(earlier.exit_at, utc=True).le(pd.Timestamp(manifest["older_interval_end"])).all()
    assert len(earlier) == saved["older_interval"]["completed_trades"] == 35
    assert abs(earlier.net_usd.sum() - saved["older_interval"]["net_usd"]) < 1e-8
    assert saved["older_interval_verdict"] == "ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE"
    paths = json.loads((OUT / "independent_path_checks.json").read_text())
    assert {name: len(rows) for name, rows in paths["books"].items()} == {"continuous_binance": 52, "matched_binance": 14, "matched_SHI": 14}
    assert all(r["first_touch_and_cash_verified"] for rows in paths["books"].values() for r in rows)
    prior = json.loads((OLD / "run_manifest.json").read_text())
    helper = "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/policy.py"
    helper_sha = sha(ROOT / helper)
    assert helper_sha == prior["immutable_source_and_strategy_hashes"][helper]
    adapter_sha = sha(OLD / "archive_source.py")
    assert adapter_sha == json.loads((OUT / "source_context_plan.json").read_text())["adapter_sha256"]
    save("additional_executed_code_verification.json", {helper: helper_sha,
        str((OLD / "archive_source.py").relative_to(ROOT)): adapter_sha,
        "expected_hashes_preexist_in_prior40O_and_pre_result_context_plan": True,
        "post_result_verifier_sha256": sha(__file__)})
    tests = {}
    for name in ["test_contracts.xml", "test_regression.xml"]:
        suite = next(ET.parse(OUT / name).getroot().iter("testsuite"))
        assert int(suite.attrib["errors"]) == int(suite.attrib["failures"]) == 0
        tests[name] = int(suite.attrib["tests"])
    assert tests == {"test_contracts.xml": 27, "test_regression.xml": 798}
    parity = pd.read_csv(OUT / "matched_candidate_parity.csv")
    mismatches = parity.loc[~parity.decision_equal]
    mismatches.to_csv(OUT / "matched_candidate_mismatches.csv", index=False)
    summary = {"H1_states_compared": len(parity), "raw_or_final_mismatches": len(mismatches),
        "raw_direction_mismatches": int(parity.raw_direction_SHI.ne(parity.raw_direction_binance).sum()),
        "final_direction_mismatches": int(parity.final_direction_SHI.ne(parity.final_direction_binance).sum()),
        "full_decision_agreement_pct": float(parity.decision_equal.mean() * 100),
        "source_parity_accepted": False}
    save("matched_parity_summary.json", summary)
    table = pd.read_csv(OUT / "monthly_source_comparison.csv")
    compact = table[["month", "matched_binance_entries", "matched_binance_net_proxy_usd", "matched_SHI_entries", "matched_SHI_net_proxy_usd", "published40L_spot_net_usdc"]]
    full = pd.read_csv(OUT / "oos_monthly_summary.csv")[["entry_month_utc", "entered_trades", "wins", "losses", "net_usd"]]
    (OUT / "monthly_comparison.md").write_text("# Monthly frozen archive results\n\nAll amounts net after declared fees/slippage. Entry-month attribution.\n\n" + markdown(full) +
        "\n\n# Matched 2026 source comparison\n\nSame40Lcalendar and common Binance futures execution proxy. Published40L spot is a separate execution-market reference.\n\n" + markdown(compact) + "\n", encoding="utf-8", newline="\n")
    save("verification.json", {"status": "PASS", "archives": 65, "normalized_files": 652,
        "normalized_rows": 938879, "entered_paths_independently_verified": 80,
        "prior_files_unchanged": True, "source_parity_accepted": False, "tests": tests,
        "source_comparison": summary, "core_code_unchanged_after_freeze": True})
    print("PASS:65checksums/652normalized hashes/80paths/27targeted/798regression/prior evidence unchanged", flush=True)


if __name__ == "__main__":
    main()
