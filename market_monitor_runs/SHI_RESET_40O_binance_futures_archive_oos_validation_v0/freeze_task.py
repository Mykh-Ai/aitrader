"""Initial40O identities/governance frozen before any source/OOS returns."""
from pathlib import Path
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PUBLICATION = "def5060680b31b6639c39d3e00b061ccf147d4c9"
H = ROOT / "market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == PUBLICATION
    contract = json.loads((H / "selected_research_contract.json").read_text())
    assert contract["selected_variant"] == "LONG_DELTA4_POS_BOTH_BAND4"
    assert contract["rules_sha256"] == sha(H / "filters.py") == "ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4"
    assert contract["filter_manifest_sha256"] == sha(H / "filter_manifest.json") == "32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56"
    fixed_paths = [H / n for n in ["selected_research_contract.json", "filters.py", "filter_manifest.json", "study.py"]]
    fixed_paths += list((ROOT / "research/strategy_search").glob("*.py"))
    fixed_paths += [ROOT / "binance_aggregator_shi.py", ROOT / "research/own_signal_run/feed.py", ROOT / "research/active_own_signal_selection.json",
                    ROOT / "research/latest_own_signal_replay.json", ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/interventions.py",
                    ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/policy.py"]
    record = {"task": "SHI_RESET_40O_BINANCE_FUTURES_ARCHIVE_OOS_VALIDATION_V0", "date": "2026-10-15",
        "starting_commit": head, "publication_commit_preserved": PUBLICATION, "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "mode": "RESEARCH_VALIDATION_ONLY", "strategy_variant": contract["selected_variant"], "strategy_version": contract["version"],
        "rules_sha256": contract["rules_sha256"], "filter_manifest_sha256": contract["filter_manifest_sha256"],
        "immutable_source_and_strategy_hashes": {p.relative_to(ROOT).as_posix(): sha(p) for p in fixed_paths},
        "frozen_reproduction_commit": "0862342", "normalization_initial_code_sha256": sha(OUT / "archive_source.py"),
        "source_validation_windows": [["2026-07-01T00:00:00Z", "2026-07-31T23:59:00Z"], ["2026-09-01T00:00:00Z", "2026-09-30T23:59:00Z"]],
        "source_context_plan": "If both validation archives exist, independently archive-reconstruct known SHI history fromMarch11 13:45 throughSeptember30; dailyMarch11-31 plus monthlyApril-September; noMarch1-9 archive during parity.",
        "gate": "100percent final candidate/gate decision parity; unexplained feature/state/stop/target crossings fail. Raw mismatches all retained.",
        "fallback": "One official aggTrades diagnostic only if kline taker-buy/sell discrepancy changes decisions; no trading-rule change.",
        "OOS_warmup_start": "2025-02-01T00:00:00Z", "OOS_scored_start": "2025-03-01T00:00:00Z", "OOS_scored_end": "2026-03-09T23:59:00Z",
        "OOS_boundary_policy": "No entry before scored start; no observation after scored end; unresolved tail separate, never forced future expiry. Raw candidates restricted to scored decision clocks with observed eligible entry.",
        "calendar_adapter_if_OOS_allowed": "Date-neutral admission only: replace fixed2026 warmup/outage calendar with declared OOS warmup/start/end, keeping every causal formula/rolling lookback unchanged and real UTC clocks. Original frozen source remains immutable; adapter/formula AST equality recorded before OOS.",
        "execution_market": "FUTURES_PRICE_PROXY", "notional_quote_equivalent": 3000, "completed_trade_fee_quote_equivalent": 5,
        "slippage_bps_per_fill": 2, "entry_latency_minutes": 1, "cooldown_minutes": 3, "one_global_book": True,
        "verdict_criteria": {"OOS_SUPPORTS_CONTINUED_VALIDATION": {"completed_trades_minimum": 12, "net_strictly_greater_than": 0,
             "profit_factor_minimum": 1.25, "net_excluding_best_two_strictly_greater_than": 0, "no_causality_violation": True,
             "no_strategy_rule_hash_change": True, "source_parity_passed_first": True},
             "OOS_INSUFFICIENT_SAMPLE": "completed<12; no tuning", "OOS_REJECTS_CURRENT_CANDIDATE": "completed>=12 but financial robustness criterion fails",
             "BINANCE_KLINE_SURROGATE_PARITY_FAILED": "Required strategy decision/source parity fails; no OOS replay",
             "BINANCE_ARCHIVE_SOURCE_NOT_REPLAYABLE": "Official required overlap archive/source unavailable or invalid; no OOS replay"},
        "strategy_count": 1, "variant_search_allowed": False, "optimization_allowed": False, "OOS_result_attempt_limit": 1,
        "OOS_download_before_parity_allowed": False, "OOS_returns_before_parity_allowed": False, "spot_download_allowed": False,
        "live_orders_borrow_deploy_API_keys_allowed": False, "production_promotion": False}
    dest = OUT / "run_manifest.json"
    if dest.exists():
        assert json.loads(dest.read_text()) == record
    else:
        dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("40O strategy identities and predeclared phase/OOS verdict criteria frozen", flush=True)


if __name__ == "__main__":
    main()
