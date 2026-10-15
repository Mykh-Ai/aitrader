"""Read-only verification and descriptive reporting for the frozen 40C run."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))

from research.own_signal_run.__main__ import code_hashes, save_json, verified_inputs
from research.own_signal_run.contracts import contract_hash, validate_signal
from research.own_signal_run.feed import digest, usable_observations

feed, contract = verified_inputs(ROOT, OUT)
working = usable_observations(feed).set_index("Timestamp", drop=False)
decisions = pd.read_csv(OUT / "signals/candidate_decisions.csv")
timeline = pd.read_csv(OUT / "signals/state_continuity.csv")
ledger = pd.read_csv(OUT / "financial_proxy_replay/trade_ledger.csv")
admission = pd.read_csv(OUT / "financial_proxy_replay/entry_admission.csv")
periods = pd.read_csv(OUT / "financial_proxy_replay/family_period_results.csv")
generation = json.loads((OUT / "signals/generation_manifest.json").read_text())
assert generation["contract_sha256"] == contract_hash(contract)
assert generation["code_hashes"] == code_hashes(ROOT)
assert generation["candidate_decisions_sha256"] == digest(OUT / "signals/candidate_decisions.csv")
assert generation["state_continuity_sha256"] == digest(OUT / "signals/state_continuity.csv")
accepted = decisions.loc[decisions.accepted].copy()
assert not accepted.candidate_id.duplicated().any()
for signal in accepted.to_dict("records"):
    validate_signal(signal, contract)
assert set(admission.candidate_id) == set(accepted.candidate_id)
assert set(ledger.candidate_id) == set(admission.loc[admission.admitted, "candidate_id"])
assert ledger.groupby("candidate_id").size().eq(3).all()
assert not ledger.duplicated(["candidate_id", "cost_scenario"]).any()
assert len(periods) == 27
assert not periods.duplicated(["family", "cost_scenario", "period"]).any()
once = ledger.loc[ledger.cost_scenario.eq("ZERO_COST_DIAGNOSTIC")].copy()
assert not once.candidate_id.duplicated().any()
for family, trades in once.groupby("family"):
    ordered = trades.sort_values(["entry_open_at", "candidate_id"])
    for previous, following in zip(ordered.to_dict("records"), ordered.to_dict("records")[1:]):
        assert pd.Timestamp(following["entry_open_at"]) > pd.Timestamp(previous["exit_at"])
for trade in once.to_dict("records"):
    decision = pd.Timestamp(trade["decision_at"])
    assert not any(pd.Timestamp(x["start"]) <= decision < pd.Timestamp(x["end"]) for x in contract["entry_exclusions"])
    expected_period = next(x["name"] for x in contract["periods"] if pd.Timestamp(x["start"]) <= decision < pd.Timestamp(x["end"]))
    assert expected_period == trade["period"] and "CONTEXT_ONLY" not in expected_period
cost_pivot = ledger.loc[~ledger.censored].pivot(index="candidate_id", columns="cost_scenario", values="net_R")
assert (cost_pivot.ZERO_COST_DIAGNOSTIC >= cost_pivot.ASSUMED_BASE_5_2_0_1).all()
assert (cost_pivot.ASSUMED_BASE_5_2_0_1 >= cost_pivot.ASSUMED_STRESS_10_5_0_2).all()
reset_fields = ["market_state_reset", "structure_levels_reset", "liquidity_zones_reset", "qualified_h1_state_reset", "setup_context_reset"]
assert not timeline[reset_fields].to_numpy().any()
clock = pd.to_datetime(timeline.decision_at, utc=True)
nominal = pd.to_datetime(timeline.h1_close_at, utc=True)
assert clock.is_monotonic_increasing and not clock.duplicated().any()
assert nominal.diff().iloc[1:].eq(pd.Timedelta(hours=1)).all()
assert (pd.to_datetime(timeline.prefix_last_close, utc=True) <= clock).all()
assert timeline.prefix_rows.is_monotonic_increasing
prep = ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1"
smoke_decisions = pd.read_csv(prep / "causal_smoke/candidate_decisions.csv")
smoke_timeline = pd.read_csv(prep / "causal_smoke/state_continuity.csv")
smoke_end = pd.Timestamp("2026-03-25T14:00:00Z")
pd.testing.assert_frame_equal(decisions.loc[pd.to_datetime(decisions.decision_at, utc=True) <= smoke_end].reset_index(drop=True), smoke_decisions)
pd.testing.assert_frame_equal(timeline.loc[clock <= smoke_end].reset_index(drop=True), smoke_timeline)

costs = {x["id"]: x for x in contract["cost_scenarios"]}
for row in ledger.to_dict("records"):
    actual_entry = pd.Timestamp(row["entry_open_at"])
    raw_label = pd.Timestamp(row["entry_raw_close_label"])
    assert actual_entry + pd.Timedelta(minutes=1) == raw_label
    assert float(working.loc[raw_label, "OpenPrice"]) == row["entry_price_raw"]
    assert pd.Timestamp(row["decision_at"]) < actual_entry
    assert actual_entry <= pd.Timestamp(row["expiry_at"])
    if row["censored"]:
        assert pd.isna(row["net_R"])
        continue
    exit_at = pd.Timestamp(row["exit_at"])
    assert exit_at >= actual_entry
    sign = 1 if row["direction"] == "LONG" else -1
    entry, exit_price, risk = row["entry_price_raw"], row["exit_price_raw"], row["risk_price_distance"]
    case = costs[row["cost_scenario"]]
    fee = case["fee_bps_per_fill"] / 10000
    slip = case["slippage_bps_per_fill"] / 10000
    hours = (exit_at - actual_entry).total_seconds() / 3600
    expected = {
        "gross_R": sign * (exit_price - entry) / risk,
        "slippage_R": (entry + exit_price) * slip / risk,
        "fee_R": (entry * (1 + sign * slip) + exit_price * (1 - sign * slip)) * fee / risk,
        "assumed_carry_R": entry * hours * case["adverse_carry_bps_per_hour"] / 10000 / risk,
    }
    expected["net_R"] = expected["gross_R"] - expected["slippage_R"] - expected["fee_R"] - expected["assumed_carry_R"]
    for field, value in expected.items():
        np.testing.assert_allclose(row[field], value, rtol=1e-10, atol=1e-10)

economic = ledger.loc[~ledger.censored].copy()
economic["holding_hours"] = (pd.to_datetime(economic.exit_at, utc=True) - pd.to_datetime(economic.entry_open_at, utc=True)).dt.total_seconds() / 3600
rows = []
for family in contract["families"]:
    for case in contract["cost_scenarios"]:
        all_trades = ledger.loc[ledger.family.eq(family) & ledger.cost_scenario.eq(case["id"])]
        closed = economic.loc[economic.family.eq(family) & economic.cost_scenario.eq(case["id"])].sort_values(["exit_at", "candidate_id"])
        net = closed.net_R
        curve = np.r_[0, net.cumsum().to_numpy()]
        loss = -net.loc[net < 0].sum()
        rows.append({
            "family": family, "cost_scenario": case["id"],
            "signal_gate_accepted": int(accepted.family.eq(family).sum()),
            "entry_admitted": len(all_trades), "resolved": len(closed),
            "censored": int(all_trades.censored.sum()),
            "gross_R_sum": float(closed.gross_R.sum()),
            "fee_R_sum": float(closed.fee_R.sum()),
            "slippage_R_sum": float(closed.slippage_R.sum()),
            "assumed_carry_R_sum": float(closed.assumed_carry_R.sum()),
            "net_R_sum": float(net.sum()),
            "net_R_mean": float(net.mean()) if len(net) else None,
            "net_wins": int(net.gt(0).sum()), "net_losses": int(net.lt(0).sum()),
            "win_rate": float(net.gt(0).mean()) if len(net) else None,
            "profit_factor": float(net.loc[net > 0].sum() / loss) if loss > 0 else None,
            "max_drawdown_R": float((np.maximum.accumulate(curve) - curve).max()),
            "net_R_without_best_three": float(net.sum() - net.nlargest(3).sum()) if len(net) else None,
            "mean_holding_hours": float(closed.holding_hours.mean()) if len(net) else None,
            "target_exits": int(closed.exit_reason.eq("TARGET").sum()),
            "stop_exits": int(closed.exit_reason.str.startswith("STOP").sum()),
            "expiry_exits": int(closed.exit_reason.str.startswith("EXPIRY").sum()),
            "interpretation": "INDEPENDENT_FAMILY_R_BOOK_NOT_ACCOUNT_EQUITY",
        })
overall = pd.DataFrame(rows)
overall.to_csv(OUT / "family_overall_results.csv", index=False)
if not economic.empty:
    economic["entry_month"] = pd.to_datetime(economic.entry_open_at, utc=True).dt.strftime("%Y-%m")
    monthly = economic.groupby(["family", "cost_scenario", "entry_month"]).agg(resolved=("candidate_id", "size"), gross_R_sum=("gross_R", "sum"), net_R_sum=("net_R", "sum")).reset_index()
    monthly.to_csv(OUT / "family_month_results.csv", index=False)
    economic.to_csv(OUT / "resolved_trade_economics.csv", index=False)

reason_rows = []
for family, group in decisions.loc[~decisions.accepted].groupby("family"):
    counts = group.rejection_reasons.str.split("|").explode().value_counts()
    reason_rows += [{"family": family, "reason": reason, "candidate_rows_with_reason": int(n)} for reason, n in counts.items()]
pd.DataFrame(reason_rows).to_csv(OUT / "candidate_rejection_counts.csv", index=False)
admission.groupby(["family", "admitted", "reason"], dropna=False).size().rename("count").reset_index().to_csv(OUT / "entry_admission_counts.csv", index=False)

check = {
    "status": "FROZEN_HISTORICAL_PROXY_RUN_COMPLETED",
    "source_and_code_hashes_verified_before_and_after_run": True,
    "frozen_contract_unchanged": True,
    "generation_journal_hashes_verified": True,
    "all_accepted_evidence_clocks_validated": True,
    "original_smoke_prefix_preserved_exactly": True,
    "state_reset_fields_all_false": True,
    "nominal_h1_chronology_contiguous": True,
    "independent_entry_price_and_cost_arithmetic_checked": True,
    "no_overlap_within_family_books": True,
    "trade_periods_and_exclusions_verified": True,
    "all_27_family_period_cost_combinations_present": True,
    "cost_sensitivity_monotonic_per_trade": True,
    "h1_steps": len(timeline), "candidate_decisions": len(decisions),
    "signal_gate_accepted": len(accepted),
    "entry_admitted": int(admission.admitted.sum()),
    "distinct_research_trades": int(ledger.candidate_id.nunique()),
    "resolved_distinct_trades": int(economic.candidate_id.nunique()),
    "censored_distinct_trades": int(ledger.loc[ledger.censored, "candidate_id"].nunique()),
    "ledger_rows_all_cost_scenarios": len(ledger),
    "accepted_by_family": accepted.family.value_counts().to_dict(),
    "entry_rejection_counts": admission.loc[~admission.admitted, "reason"].value_counts().to_dict(),
    "primary_skipped_rows": len(feed) - len(working),
    "accepted_with_context_omissions": int(accepted.context_omitted_minutes.gt(0).sum()),
    "resolved_trades_with_isolated_omissions": int(once.trade_omitted_minutes.gt(0).sum()),
    "resolved_entry_minutes_delayed_by_omission": int(once.entry_omitted_minutes.gt(0).sum()),
    "research_regression_previously_passed": 752,
    "production_code_changed_in_this_run": False,
    "source_data_changed_in_this_run": False,
    "live_authority": False,
    "pristine_holdout_claim": False,
    "execution_market": contract["execution_market"],
    "costs_verified": False,
}
save_json(OUT / "run_verification.json", check)
save_json(OUT / "result_identity.json", {p.relative_to(OUT).as_posix(): digest(p) for p in sorted(OUT.rglob("*.csv"))})
print(json.dumps(check, indent=2))
print(overall.to_string(index=False))
print(periods.loc[periods.cost_scenario.eq("ASSUMED_BASE_5_2_0_1")].to_string(index=False))
