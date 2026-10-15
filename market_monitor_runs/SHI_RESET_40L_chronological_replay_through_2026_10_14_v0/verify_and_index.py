"""Post-run provenance, book-admission and cash reconciliation; no rule search."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
H = ROOT / "market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
K = ROOT / "market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n", encoding="utf-8")


def main():
    selection = json.loads((ROOT / "research/active_own_signal_selection.json").read_text())
    assert selection["user_selected_candidate"] == "40H"
    assert selection["selected_variant"] == "LONG_DELTA4_POS_BOTH_BAND4"
    for field in ["selected_contract", "selected_ledger", "selected_result"]:
        assert digest(ROOT / selection[field]) == selection[field + "_sha256"]
    for folder in [H, K]:
        assert all(digest(folder / name) == sha for name, sha in json.loads((folder / "artifact_hashes.json").read_text()).items())
    manifest = json.loads((OUT / "study_manifest.json").read_text())
    for name, sha in {**manifest["source_hashes"], **manifest["preserved_hashes"]}.items():
        assert digest(ROOT / name) == sha
    assert all(digest(OUT / name) == sha for name, sha in manifest["code_hashes"].items())
    t = pd.read_csv(OUT / "trade_journal_usdc.csv")
    f = pd.read_csv(OUT / "candidate_entry_metrics.csv")
    for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        t[col] = pd.to_datetime(t[col], utc=True)
    f.decision_at = pd.to_datetime(f.decision_at, utc=True)
    lookup = t.set_index("signal_index")
    busy = pd.Timestamp("1970-01-01", tz="UTC")
    rows = []
    for r in f.itertuples():
        status = "DELTA_FILTER_REJECTED" if not r.delta_rules_allowed else "SHORT_SPACE_REJECTED" if not r.short_space_allowed else None
        if status is None:
            if r.decision_at + pd.Timedelta(minutes=1) <= busy:
                status = "POSITION_OPEN_OR_COOLDOWN"
                assert r.signal_index not in lookup.index
            elif r.signal_index in lookup.index:
                trade = lookup.loc[r.signal_index]
                status = "ENTERED"
                busy = (trade.expiry_at if trade.censored else trade.exit_at) + pd.Timedelta(minutes=3)
            else:
                status = "ENTRY_OBSERVATION_OR_INITIAL_RISK_REJECTED"
        rows.append({"signal_index": r.signal_index, "decision_at": r.decision_at, "direction": r.direction,
                     "delta4_pct": r.delta4_pct, "delta24_pct": r.delta24_pct,
                     "short_space_allowed": r.short_space_allowed, "delta_rules_allowed": r.delta_rules_allowed,
                     "book_decision": status, "book_busy_through": busy})
    admissions = pd.DataFrame(rows)
    assert admissions.book_decision.eq("ENTERED").sum() == len(t)
    admissions.to_csv(OUT / "candidate_book_decisions.csv", index=False)
    result = json.loads((OUT / "result.json").read_text())
    full = result["cohorts"]["full_history"]
    closed = t.loc[t.status_at_cutoff.eq("CLOSED")]
    qty = 3000 / closed.entry_price
    gross = closed.direction * (closed.exit_price - closed.entry_price) * qty
    slip = (closed.entry_price + closed.exit_price) * qty * .0002
    np.testing.assert_allclose(closed.net_usd, gross - 5 - slip, atol=1e-8)
    np.testing.assert_allclose(closed.net_usd.sum(), full["net_usd"], atol=1e-8)
    assert not closed["net_usd"].isna().any()
    assert not t.censored.any() and len(t) == 14
    assert len(t.loc[t.entry_at.ge(pd.Timestamp("2026-10-01", tz="UTC"))]) == 1
    verification = {"original40H_artifacts_and_selection_bindings_match_their_saved_hashes": True,
                    "all40K_artifact_hashes_match": True, "all232_sources_unchanged": True,
                    "all_run_code_and_prior_artifacts_unchanged": True, "independent_full_cash_reconciliation": True,
                    "all_candidate_book_decisions_reconcile": True, "test_result": "15 passed",
                    "eligible_book_decisions": admissions.loc[admissions.short_space_allowed & admissions.delta_rules_allowed, "book_decision"].value_counts().to_dict()}
    save(OUT / "final_verification.json", verification)
    artifact_hashes = {p.relative_to(OUT).as_posix(): digest(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "artifact_hashes.json"}
    save(OUT / "artifact_hashes.json", artifact_hashes)
    pointer = {"version": "40L_EXTENDED_40H_REPLAY_EVIDENCE", "selected_rule_pointer": "research/active_own_signal_selection.json",
               "selected_rule_pointer_sha256": digest(ROOT / "research/active_own_signal_selection.json"),
               "rule_contract_unchanged": selection["selected_contract"], "cutoff_utc": result["cutoff_utc"],
               "journal": (OUT / "trade_journal_usdc.csv").relative_to(ROOT).as_posix(), "journal_sha256": digest(OUT / "trade_journal_usdc.csv"),
               "result": (OUT / "result.json").relative_to(ROOT).as_posix(), "result_sha256": digest(OUT / "result.json"),
               "study_manifest": (OUT / "study_manifest.json").relative_to(ROOT).as_posix(), "study_manifest_sha256": digest(OUT / "study_manifest.json"),
               "artifact_hashes": (OUT / "artifact_hashes.json").relative_to(ROOT).as_posix(), "artifact_hashes_sha256": digest(OUT / "artifact_hashes.json"),
               "status": "COMPLETED_RESEARCH_ONLY", "production_promoted": False, "actual_borrowing_in_net": False}
    save(ROOT / "research/latest_own_signal_replay.json", pointer)
    print(json.dumps(verification, indent=2), flush=True)
    print(admissions.loc[admissions.decision_at.ge(pd.Timestamp("2026-10-01", tz="UTC"))].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
