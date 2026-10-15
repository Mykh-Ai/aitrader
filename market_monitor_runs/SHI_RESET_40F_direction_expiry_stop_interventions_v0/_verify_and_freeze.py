from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, metrics
from interventions import candidate_map, h4_inventory

manifest = json.loads((OUT / "study_manifest.json").read_text())
spec = manifest["baseline_spec"]
feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
bars = features(feed)
data = ReplayData(feed, bars)
signals = hybrid_signals(bars, spec["long"], spec["short"])
inventory = h4_inventory(feed, bars)
cutoff = pd.Timestamp("2026-06-20T23:59:00Z")
prefix_feed = feed.loc[feed.Timestamp <= cutoff]
prefix_bars = features(prefix_feed)
prefix_data = ReplayData(prefix_feed, prefix_bars)
prefix_signals = hybrid_signals(prefix_bars, spec["long"], spec["short"])
prefix_inventory = h4_inventory(prefix_feed, prefix_bars)
for variant in manifest["variants"]:
    complete, _ = candidate_map(data, signals, spec, variant, inventory)
    prefix, _ = candidate_map(prefix_data, prefix_signals, spec, variant, prefix_inventory)
    visible = {i: row for i, row in complete.items() if i < len(prefix_bars)}
    assert visible == prefix, variant["id"]

results = pd.read_csv(OUT / "intervention_results.csv")
complete = results.loc[results.censored.eq(0)]
selected_name = complete.sort_values("net_usd").iloc[-1].variant
assert selected_name == "SHORT_SPACE_1R"
variant = next(v for v in manifest["variants"] if v["id"] == selected_name)
candidates, _ = candidate_map(data, signals, spec, variant, inventory)
filtered = np.zeros_like(signals)
for i, row in candidates.items():
    filtered[i] = row["side"]
independent = replay_hybrid(data, filtered, spec["long"], spec["short"])
selected = pd.read_csv(OUT / "variant_ledgers/SHORT_SPACE_1R.csv")
for col in ["decision_at", "entry_at", "exit_at", "expiry_at", "reference_available_at"]:
    selected[col] = pd.to_datetime(selected[col], utc=True)
pd.testing.assert_frame_equal(selected[independent.columns], independent, check_exact=False, rtol=1e-11, atol=1e-11)
assert not selected.censored.any()
assert selected.direction.eq(-1).sum() == 6 and selected.direction.eq(1).sum() == 15
assert selected.loc[selected.reference_available_at.notna(), "reference_available_at"].le(
    selected.loc[selected.reference_available_at.notna(), "decision_at"]).all()

# Independently verify observable first terminal touch for the selected variant.
for row in selected.itertuples():
    start = np.searchsorted(data.minute_ts, row.entry_at.value + data.minute)
    end = np.searchsorted(data.minute_ts, row.exit_at.value, side="left")
    stop_hits = data.ml[start:end] <= row.stop_price if row.direction > 0 else data.mh[start:end] >= row.stop_price
    target_hits = data.mh[start:end] >= row.target_price if row.direction > 0 else data.ml[start:end] <= row.target_price
    assert not stop_hits.any() and not target_hits.any()
    terminal = np.searchsorted(data.minute_ts, row.exit_at.value)
    if row.exit_reason == "TARGET":
        assert (data.mh[terminal] >= row.target_price if row.direction > 0 else data.ml[terminal] <= row.target_price)
        assert row.exit_price == row.target_price
    elif row.exit_reason == "STOP":
        assert (data.ml[terminal] <= row.stop_price if row.direction > 0 else data.mh[terminal] >= row.stop_price)
        assert row.exit_price == row.stop_price
    elif row.exit_reason == "EXPIRY":
        assert row.exit_at == row.expiry_at
        np.testing.assert_allclose(row.exit_price, data.mc[terminal])
    else:
        raise AssertionError(row.exit_reason)

selected["trade_id"] = [hashlib.sha256(f"40F|{r.family}|{r.decision_at}|{r.direction}".encode()).hexdigest()[:24] for r in selected.itertuples()]
selected["notional_usd"] = 3000.
selected["quantity_btc"] = 3000. / selected.entry_price
selected["planned_target_profit_usd"] = selected.initial_risk_usd * selected.target_R
selected["holding_hours"] = (selected.exit_at - selected.entry_at).dt.total_seconds() / 3600
selected.to_csv(OUT / "selected_trade_ledger_usd.csv", index=False)
core = selected.loc[selected.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
freeze = {"version": "SHI_RESET_40F_SHORT_SPACE_RESEARCH_CANDIDATE_V1", "derived_from": spec["version"],
          "original_strategy_unchanged": True, "baseline_spec": spec, "intervention": variant,
          "entry_gate": "Short only: block when nearest known unretired opposite H4 swing lower band is less than1 estimated initial risk from decision H1 CLOSE; absence of a known level passes",
          "h4_reference_contract": "3 closed usable contiguous H4 bars; right-bar-close availability;30-day max age; retirement after2 usable H1 closes through5bp band",
          "reproduction": "python market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/_run_study.py",
          "study_code_hashes": manifest["study_code_hashes"], "source_preparation": spec["source_preparation"],
          "position_notional_usd": 3000, "commission_usd_round_trip": 5, "slippage_bps_per_fill": 2,
          "historically_selected_not_holdout": True, "unmodeled_borrow_interest": True, "production_promoted": False}
(OUT / "selected_research_variant.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
summary = {"status": "RESEARCH_VARIANT_IMPROVES_FROZEN_BASELINE_ON_EXPOSED_HISTORY", "variant": selected_name,
           "full_history": metrics(selected), "six_month_entry_cohort": metrics(core),
           "positive_trades": int(selected.net_usd.gt(0).sum()), "negative_trades": int(selected.net_usd.lt(0).sum()),
           "long": metrics(selected.loc[selected.direction.eq(1)]), "short": metrics(selected.loc[selected.direction.eq(-1)]),
           "mean_planned_target_R": float(selected.target_R.mean()), "net_R_sum": float(selected.net_R.sum()),
           "mean_holding_hours": float(selected.holding_hours.mean()), "isolated_minute_omissions": int(selected.omitted_minutes.sum()),
           "baseline_full_net_usd": 512.276014522229, "baseline_negative_trades": 17, "baseline_positive_trades": 9,
           "absolute_positive_count_increased": False, "new_rules_not_pristine_holdout": True}
(OUT / "selected_result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

verification = {"all_16_variant_entry_maps_future_prefix_invariant": True,
                "selected_filtered_portfolio_matches_unchanged_40D_minute_engine": True,
                "selected_independent_first_terminal_touch_verified": True,
                "all_21_selected_paths_observed": not selected.censored.any(), "no_inferred_gap_marks": not selected.short_gap_conservative_mark.any(),
                "source_identity_verified": True,
                "baseline_artifacts_unchanged": all(digest(ROOT / manifest["baseline_root"] / p) == sha for p, sha in manifest["baseline_artifact_hashes"].items()),
                "original_code_unchanged": all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items()),
                "study_code_unchanged": all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items())}
assert all(verification.values())
(OUT / "selected_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")
print(json.dumps({"selected": selected_name, "full_net_usd": summary["full_history"]["net_usd"],
                  "six_month_net_usd": summary["six_month_entry_cohort"]["net_usd"], "trades": len(selected),
                  "positive": summary["positive_trades"], "negative": summary["negative_trades"],
                  "independent_engine_and_first_touches": True}))
