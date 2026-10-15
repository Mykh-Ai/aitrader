"""Terminal parity failure. Emit NOT_RUN OOS schemas, never an OOS return."""
from pathlib import Path
import json
import pandas as pd

from archive_source import OUT, save, sha
from phase_policy import verify_hashes

ROOT = OUT.parents[1]


def main():
    gate = json.loads((OUT / "parity_gate.json").read_text())
    assert gate["status"] == "BINANCE_KLINE_SURROGATE_PARITY_FAILED" and not gate["accepted"]
    assert not (OUT / "parity_acceptance.json").exists() and not (OUT / "first_oos_attempt.json").exists()
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    verify_hashes(ROOT, manifest["immutable_source_and_strategy_hashes"])
    sources = json.loads((OUT / "source_manifest.json").read_text())
    assert not sources["OOS_downloaded"] and all(r["date"] >= "2026-03-11" for r in sources["archives"])
    assert all(sha(OUT / r["archive_path"]) == r["local_sha256"] for r in sources["archives"])
    pd.DataFrame(columns=["decision_at", "direction", "family", "raw_candidate", "policy_allowed", "blocker_reasons"]).to_csv(OUT / "oos_candidates.csv", index=False)
    pd.DataFrame(columns=["decision_at", "entry_at", "exit_at", "direction", "entry_price", "stop_price", "target_price", "exit_reason", "gross", "commission", "slippage", "net", "net_R"]).to_csv(OUT / "oos_trades.csv", index=False)
    pd.DataFrame(columns=["entry_month_utc", "completed_trades", "wins", "losses", "net"]).to_csv(OUT / "oos_monthly_summary.csv", index=False)
    metric_names = ["raw_candidates", "gate_passing_candidates", "entered_trades", "completed_trades", "long_count", "short_count", "wins", "losses", "expiries", "targets", "stops", "gross", "commission", "slippage", "net", "profit_factor", "average_trade", "median_trade", "max_closed_trade_drawdown", "best_trade", "worst_trade", "best2_contribution", "best3_contribution", "net_excluding_best1", "net_excluding_best2", "net_excluding_best3", "long_net", "short_net", "signal_frequency", "average_initial_risk_distance", "R_outcome_distribution"]
    save("oos_metrics.json", {"status": "NOT_RUN_SOURCE_PARITY_FAILED", "metrics": {name: None for name in metric_names},
         "declared_scored_start": manifest["OOS_scored_start"], "declared_scored_end": manifest["OOS_scored_end"], "declared_warmup_start": manifest["OOS_warmup_start"],
         "OOS_source_downloaded": False, "OOS_returns_inspected": False, "execution_model_if_permitted": "FUTURES_PRICE_PROXY",
         "empty_CSV_files_are_schemas_not_zero_trade_performance": True})
    save("phase_state.json", {"state": "TERMINAL_SOURCE_PARITY_FAILED", "verdict": gate["status"], "OOS_download_permitted": False,
         "OOS_execution_permitted": False, "strategy_count": 1, "strategy_rule_change": False, "optimization_performed": False,
         "server_shadow_next_phase_justified": False, "live_trading_blocked": True, "exact_spot_replay_next_step": False})
    result = ["#40O — Binance futures archive source validation", "", "**BINANCE_KLINE_SURROGATE_PARITY_FAILED**", "",
         "Frozen40H LONG_DELTA4_POS_BOTH_BAND4 reproduced its original13-trade control exactly.27official BTCUSDT USD-M1m kline archives/checksums from known2026 context were verified.", "",
         "|Validation window|Raw candidates SHI/archive|Final-direction mismatch|Decision parity|", "|---|---:|---:|---:|",
         "|July2026|8 /9|1|99.865591%|", "|September2026|6 /6|0|100%|", "",
         f"Across1464H1 decisions: {gate['full_candidate_gate_decision_parity_pct']:.9f}% parity; one mismatch is enough to fail the required100% gate.",
         "July5 08:00UTC: archive permits a long, SHI has no raw candidate. Raw24h delta also differs4.077205337% versus3.940742504%, crossing the selected+4% boundary. Prior-history/H4/price source differences are separately retained; no threshold/source shift fitted.",
         "", "87,840minute labels align;72,690minutes differ in at least one price/quantity/status field beyond declared rounding tolerance.16,888of61,488feature/state comparisons differ. July9andSeptember2traded-status differences recorded.",
         "", "Both sources pass real-prefix invariance at July15 12:30UTC with3023closed H1 steps each; all rolling observations end at/before decision. No detected lookahead. No original strategy/code/source changed.",
         "", "OOS2025-03-01–2026-03-09 and warmup2025-02 remain undownloaded and outcome-unseen. OOS CSVs are empty schemas; all OOS performance metrics are null, not zero. This does not reject or validate the strategy on OOS.",
         "", "Optional aggTrades fallback was not attempted: the observed failure includes OHLC/quality/prior-history/H4 differences, not solely taker-buy mapping. No claim is made about untested aggTrades parity.",
         "", "Phase decision: do not advance on this task to server shadow; live remains blocked. Resolve source semantics in a separate declared task before OOS, then decide whether exactBTCUSDC spot replay is warranted. Existing40H/L evidence remains a separate historically selected sample.",
         "", "Artifacts: run_manifest.json;source_manifest.json;archive_inventory.csv;raw_parity_summary.json;raw_parity_mismatches.csv;feature_parity.csv;candidate_parity.csv;parity_report.md;source_semantics_diagnosis.json;causality_checks.json;frozen_identity_verification.json;oos_metrics.json."]
    (OUT / "result.md").write_text("\n".join(result) + "\n", encoding="utf-8", newline="\n")
    print("Terminal gate preserved. OOS access/replay forbidden; all OOS metrics explicitly NOT_RUN.", flush=True)


if __name__ == "__main__":
    main()
