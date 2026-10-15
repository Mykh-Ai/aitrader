"""One fixed-rule 40H continuation, full prior state and two separate feeds."""
from pathlib import Path
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
H = ROOT / "market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
K = ROOT / "market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0"
J = ROOT / "market_monitor_runs/SHI_RESET_40J_short_delta4_mirror_v0"
for path in [ROOT, H, OUT]:
    sys.path.insert(0, str(path))
from study import load, entry_metrics, digest, features, ReplayData, h4_inventory, candidate_map, replay_hybrid, metrics, execution_references
from filters import filtered_directions
from research.own_signal_run.feed import read_sources
from research.strategy_search.hybrid import hybrid_signals as frozen_hybrid
from policy import hybrid_signals, TailAwareReplayData, classify_tail, open_marks

CUTOFF = pd.Timestamp("2026-10-14T23:59:00Z")
OCTOBER = pd.Timestamp("2026-10-01T00:00:00Z")
RULES = {"rules": ["L_D4_POS", "B_D24_BAND4"]}


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n", encoding="utf-8")


def freeze():
    inventory = pd.read_csv(K / "updated_futures_source_inventory.csv")
    sources = {r.path: r.sha256 for r in inventory.loc[inventory.status.eq("READ")].itertuples()}
    assert len(sources) == 232
    paths = [ROOT / "research/active_own_signal_selection.json", H / "artifact_hashes.json", K / "data_readiness.json",
             K / "updated_futures_source_inventory.csv", K / "spot_BTCUSDC/spot_minutes.csv"]
    paths += [H / name for name in json.loads((H / "artifact_hashes.json").read_text())]
    paths += list((ROOT / "research/strategy_search").glob("*.py"))
    paths += list((ROOT / "research/own_signal_run").glob("*.py"))
    paths += [ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/interventions.py",
              ROOT / "market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/cross_market.py",
              ROOT / "market_monitor/market_structure_state.py", ROOT / "market_monitor/feed_adapter.py", J / "run_study.py"]
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    assert all(digest(ROOT / p) == sha for p, sha in sources.items())
    manifest = {"task": "SHI_RESET_40L", "phase": "FIXED_BEFORE_EXTENDED_FINANCIAL_RETURNS", "cutoff": CUTOFF,
                "history_start": "2026-03-11T13:45:00Z", "selected_candidate": "40H_LONG_DELTA4_POS_BOTH_BAND4",
                "changes": ["Admit October1-14 closed-H1 decisions; remove only old October calendar exclusion and extend old entry_end.",
                            "Use40K extended sources; preserve original13 trades as control.",
                            "Permit last-closed-H1 precise entry only when its actual next-minute price observation exists; no fabricated future H1."],
                "preserved_rules": "All40H families/thresholds/short-space1R/delta gates/stops/full10R-long6R-short/168h expiry/latency/cooldown/global book/isolated-minute policy.",
                "notional_usdc": 3000, "commission_per_completed_trade_usdc": 5, "slippage_bps_per_fill": 2,
                "signal_market": "BTCUSDT_PERPETUAL_FUTURES", "execution_market": "BTCUSDC_SPOT_MARGIN_PRICE_MODEL",
                "open_tail": "No realized credit or forced exit; mark from last RAW spot close at/before common cutoff separately.",
                "actual_borrowing_in_net": False, "production_promoted": False, "pristine_holdout": False,
                "prior_exposure": "October1-12 already available to earlier research as context;13/14 newly acquired, retrospective continuation not prospective proof.",
                "variants": 1, "source_hashes": sources, "preserved_hashes": hashes,
                "code_hashes": {name: digest(OUT / name) for name in ["policy.py", "run_study.py", "test_policy.py"]},
                **{name: False for name in ["market_state_reset", "structure_levels_reset", "liquidity_zones_reset", "qualified_h1_state_reset", "setup_context_reset"]},
                "continuity_scope": "Whole prior research feature/H4-inventory/global-book state, not full Monitor lifecycle promotion."}
    # Convert timestamps before an exact immutable comparison on rerun.
    manifest = json.loads(json.dumps(manifest, default=str))
    if (OUT / "study_manifest.json").exists():
        assert json.loads((OUT / "study_manifest.json").read_text()) == manifest, "Use a versioned successor"
    else:
        save("study_manifest.json", manifest)
    return manifest


def pipeline(feed, spot, spec):
    bars = features(feed)
    original = hybrid_signals(bars, spec["long"], spec["short"])
    fdata = ReplayData(feed, bars)
    inventory = h4_inventory(feed, bars)
    cands, rejected = candidate_map(fdata, original, spec, {"short_space_1r": True}, inventory)
    space = np.zeros_like(original)
    for i, c in cands.items():
        space[i] = c["side"]
    f = entry_metrics(feed, bars, original, np.flatnonzero(original), spec)
    final, allowed = filtered_directions(space, f, RULES)
    f["short_space_allowed"] = space[f.signal_index.to_numpy(dtype=int)] != 0
    f["delta_rules_allowed"] = allowed
    f["all_entry_gates_allowed"] = final[f.signal_index.to_numpy(dtype=int)] != 0
    ebars, quotes = execution_references(feed, spot, bars)
    data = TailAwareReplayData(spot, ebars)
    return bars, original, final, f, quotes, data, cands, rejected


def outcome(trades):
    closed = trades.loc[trades.status_at_cutoff.eq("CLOSED")]
    m = metrics(closed)
    return {**m, "entries": len(trades), "closed": len(closed), "open_at_cutoff": int(trades.status_at_cutoff.eq("OPEN_AT_CUTOFF").sum()),
            "data_censored": int(trades.status_at_cutoff.eq("CENSORED_DATA").sum()),
            "wins": int(closed.net_usd.gt(0).sum()), "losses": int(closed.net_usd.lt(0).sum()),
            "mean_target_R": float(closed.target_R.mean()) if len(closed) else None,
            "quote_currency": "USDC", "actual_borrow_interest_included": False}


def verify_paths(trades, spot, final, quotes):
    # Independent vector first-touch/cash verifier from40J, frozen as an input.
    sys.path.insert(0, str(J))
    module_spec = importlib.util.spec_from_file_location("verification40J", J / "run_study.py")
    verifier = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(verifier)
    closed = trades.loc[trades.status_at_cutoff.eq("CLOSED")]
    count = verifier.verify_path(closed, spot, final, quotes)
    previous = None
    for r in trades.itertuples():
        assert r.entry_at <= CUTOFF and r.decision_at < r.entry_at
        assert final[r.signal_index] == r.direction
        if previous is not None:
            assert r.entry_at > previous + pd.Timedelta(minutes=3)
        previous = r.expiry_at if r.censored else r.exit_at
        if not r.censored:
            assert r.exit_at <= CUTOFF
            continue
        assert r.status_at_cutoff == "OPEN_AT_CUTOFF", "Data-censored path requires explicit separate evidence"
        assert r.expiry_at > CUTOFF
        path = spot.loc[spot.Timestamp.gt(r.entry_at) & spot.Timestamp.le(CUTOFF)]
        assert path.DataQuality.eq("RAW").all()
        assert path.Timestamp.iloc[0] == r.entry_at + pd.Timedelta(minutes=1)
        assert path.Timestamp.diff().dropna().le(pd.Timedelta(minutes=2)).all()
        stop = path.LowPrice.le(r.stop_price) if r.direction > 0 else path.HiPrice.ge(r.stop_price)
        target = path.HiPrice.ge(r.target_price) if r.direction > 0 else path.LowPrice.le(r.target_price)
        assert not (stop | target).any()
        for q in [quotes.spot_close_at.iloc[r.signal_index], quotes.futures_close_at.iloc[r.signal_index]]:
            assert q <= r.decision_at and r.decision_at - q <= pd.Timedelta(minutes=1)
    return count


def main():
    manifest = freeze()
    print("40L scope/source/code frozen before returns; reproducing40H control", flush=True)
    oldfeed, oldspot, oldbars, _, olddata, oldspace, oldoriginal, spec, oldquotes = load()
    oldf = entry_metrics(oldfeed, oldbars, oldoriginal, np.flatnonzero(oldoriginal), spec)
    oldfinal, _ = filtered_directions(oldspace, oldf, RULES)
    control = replay_hybrid(olddata, oldfinal, spec["long"], spec["short"])
    saved = pd.read_csv(H / "selected_trade_ledger_usdc.csv")
    for name in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        saved[name] = pd.to_datetime(saved[name], utc=True)
    pd.testing.assert_frame_equal(control, saved[control.columns], check_exact=False, rtol=1e-10, atol=1e-10)
    assert len(control) == 13
    control.to_csv(OUT / "control_40H_reproduced.csv", index=False)
    print("All13 original trades reproduced; loading full extended chronology", flush=True)
    feed, source_inventory = read_sources(ROOT, manifest["history_start"], str(CUTOFF))
    actual_sources = dict(zip(source_inventory.loc[source_inventory.status.eq("READ"), "path"], source_inventory.loc[source_inventory.status.eq("READ"), "sha256"]))
    assert actual_sources == manifest["source_hashes"]
    spot = pd.read_csv(K / "spot_BTCUSDC/spot_minutes.csv")
    spot.Timestamp = pd.to_datetime(spot.Timestamp, utc=True)
    spot = spot.loc[spot.Timestamp.between(feed.Timestamp.min(), CUTOFF) & spot.DataQuality.eq("RAW")].reset_index(drop=True)
    assert feed.Timestamp.max() == spot.Timestamp.max() == CUTOFF
    bars, original, final, f, quotes, data, cands, rejected = pipeline(feed, spot, spec)
    pd.testing.assert_frame_equal(oldbars, bars.iloc[:len(oldbars)].reset_index(drop=True))
    pd.testing.assert_frame_equal(oldquotes, quotes.iloc[:len(oldquotes)].reset_index(drop=True))
    before = bars.timestamp.lt(OCTOBER).to_numpy()
    np.testing.assert_array_equal(original[before], frozen_hybrid(bars, spec["long"], spec["short"])[before])
    trades = classify_tail(replay_hybrid(data, final, spec["long"], spec["short"]), CUTOFF)
    retained = trades.loc[trades.entry_at.lt(OCTOBER)]
    pd.testing.assert_frame_equal(control.reset_index(drop=True), retained[control.columns].reset_index(drop=True), check_exact=False, rtol=1e-10, atol=1e-10)
    print("Extended global-book replay complete; checking real-prefix stability and independent fills", flush=True)
    # Real old-cutoff prefix, reconstructed from all prior data without resetting.
    pb, po, pf, pmetrics, pq, _, pcands, prejected = pipeline(oldfeed, oldspot, spec)
    np.testing.assert_array_equal(po, original[:len(pb)])
    np.testing.assert_array_equal(pf, final[:len(pb)])
    compare_fields = [c for c in pmetrics if c != "h4_regime"]
    pd.testing.assert_frame_equal(pmetrics[compare_fields], f.loc[f.signal_index.lt(len(pb)), compare_fields].reset_index(drop=True))
    assert pcands == {i: row for i, row in cands.items() if i < len(pb)}
    assert prejected == [row for row in rejected if row["signal_index"] < len(pb)]
    checked = verify_paths(trades, spot, final, quotes)
    closed = trades.loc[trades.status_at_cutoff.eq("CLOSED")].copy()
    opened = trades.loc[trades.status_at_cutoff.eq("OPEN_AT_CUTOFF")].copy()
    marks = open_marks(opened, spot, CUTOFF)
    for label, stamp in [("decision_at_budapest", "decision_at"), ("entry_at_budapest", "entry_at"), ("exit_at_budapest", "exit_at"), ("expiry_at_budapest", "expiry_at")]:
        trades[label] = trades[stamp].dt.tz_convert("Europe/Budapest")
    trades["direction_label"] = np.where(trades.direction.gt(0), "LONG", "SHORT")
    trades["execution_currency"] = "USDC"
    trades["notional_usdc"] = 3000
    trades["signal_market"] = "BTCUSDT_PERPETUAL_FUTURES"
    trades["execution_market"] = "BTCUSDC_SPOT_MARGIN_PRICE_MODEL"
    trades["borrow_interest_included"] = False
    trades = trades.merge(f.drop(columns=["direction", "decision_at"]), on="signal_index", validate="one_to_one")
    trades = trades.merge(quotes.assign(signal_index=np.arange(len(quotes))).drop(columns=["available_at"]), on="signal_index", validate="one_to_one")
    trades = trades.merge(marks, on="signal_index", how="left", validate="one_to_one")
    trades.to_csv(OUT / "trade_journal_usdc.csv", index=False)
    trades.loc[trades.status_at_cutoff.eq("CLOSED")].to_csv(OUT / "closed_trade_ledger_usdc.csv", index=False)
    trades.loc[trades.status_at_cutoff.eq("OPEN_AT_CUTOFF")].to_csv(OUT / "open_positions_at_cutoff.csv", index=False)
    october = trades.loc[trades.entry_at.ge(OCTOBER)]
    october.to_csv(OUT / "october_trade_journal_usdc.csv", index=False)
    f.to_csv(OUT / "candidate_entry_metrics.csv", index=False)
    quotes.to_csv(OUT / "asof_execution_quotes.csv", index=False)
    pd.DataFrame([{"signal_index": i, **row} for i, row in cands.items()]).to_csv(OUT / "h4_space_candidates.csv", index=False)
    pd.DataFrame(rejected).to_csv(OUT / "h4_space_rejections.csv", index=False)
    source_inventory.to_csv(OUT / "source_inventory.csv", index=False)
    cohorts = {"full_history": outcome(trades), "April_September_entries": outcome(trades.loc[trades.entry_at.ge(pd.Timestamp("2026-04-01", tz="UTC")) & trades.entry_at.lt(OCTOBER)]),
               "October_entries": outcome(october), "October1_12_entries": outcome(october.loc[october.entry_at.lt(pd.Timestamp("2026-10-13", tz="UTC"))]),
               "October13_14_entries": outcome(october.loc[october.entry_at.ge(pd.Timestamp("2026-10-13", tz="UTC"))])}
    by_direction = {name: outcome(trades.loc[trades.direction.eq(side)]) for name, side in [("LONG", 1), ("SHORT", -1)]}
    monthly = []
    for month, group in trades.groupby(trades.entry_at.dt.strftime("%Y-%m")):
        monthly.append({"entry_month_utc": month, **outcome(group)})
    pd.DataFrame(monthly).to_csv(OUT / "monthly_entry_results_usdc.csv", index=False)
    np.testing.assert_allclose(cohorts["full_history"]["net_usd"] - control.net_usd.sum(), cohorts["October_entries"]["net_usd"], atol=1e-8)
    assert all((f[f"window{h}_last_observation_at"] <= f.decision_at).all() for h in [1, 4, 24, 72])
    assert all(digest(ROOT / p) == sha for p, sha in {**manifest["preserved_hashes"], **manifest["source_hashes"]}.items())
    assert all(digest(OUT / p) == sha for p, sha in manifest["code_hashes"].items())
    verification = {"all13_control_trades_reproduced_and_retained": True, "real_old_cutoff_prefix_features_signals_filters_H4_quotes_identical": True,
                    "preOctober_formula_parity": True, "independent_closed_first_touch_cash_paths": checked, "open_paths_no_prior_exit": len(opened),
                    "one_global_book_no_overlap": True, "all_data_source_and_prior_code_hashes_unchanged": True,
                    "cutoff": CUTOFF, "last_closed_H1": bars.timestamp.iloc[-1], "futures_rows": len(feed), "spot_rows_to_common_cutoff": len(spot),
                    "raw_candidates": len(f), "eligible_after_all_gates": int(np.count_nonzero(final)),
                    "October_raw_candidates": int(f.decision_at.ge(OCTOBER).sum()),
                    "October_eligible": int(np.count_nonzero(final[bars.available_at.ge(OCTOBER)])), "open_realized_credit": 0,
                    "no_data_censored_trades": bool(not trades.status_at_cutoff.eq("CENSORED_DATA").any())}
    save("verification.json", verification)
    result = {"task": "SHI_RESET_40L", "cutoff_utc": CUTOFF, "selected_rule_contract": "40H unchanged trading rules; October calendar extension",
              "cohorts": cohorts, "by_direction": by_direction, "control_net_usdc": float(control.net_usd.sum()),
              "realized_change_usdc": float(closed.net_usd.sum() - control.net_usd.sum()), "open_marks": json.loads(marks.to_json(orient="records", date_format="iso")),
              "actual_borrowing_in_net": False, "pristine_holdout": False, "production_promoted": False}
    save("result.json", result)
    full, octr = cohorts["full_history"], cohorts["October_entries"]
    lines = ["#40L — 40H chronological continuation through October14", "", f"Common cutoff: {CUTOFF}; last complete H1: {bars.timestamp.iloc[-1]}.", "",
             "|Entry cohort|Entries|Closed|Open|Wins/losses|Realized net USDC|", "|---|---:|---:|---:|---:|---:|"]
    for name, m in cohorts.items():
        lines.append(f"|{name}|{m['entries']}|{m['closed']}|{m['open_at_cutoff']}|{m['wins']}/{m['losses']}|{m['net_usd']:+.2f}|")
    lines += ["", f"Full cash reconciliation: gross {full['gross_usd']:.8f} - commissions {full['commission_usd']:.8f} - slippage {full['slippage_usd']:.8f} = {full['net_usd']:.8f} USDC.",
              f"All13 original trades retained exactly; October realized change {octr['net_usd']:+.8f}USDC. No open-position value is included in realized net.",
              "", "3000USDC notional,5USDC/completed trade,2bps adverse slippage/fill; before actual borrow interest. Futures signals, BTCUSDC spot fills, one global book.",
              "October1-12 was already available context; this retrospective extension is not pristine holdout. Original40H selection is unchanged; no production or legacy Backtester gate promoted.",
              "", "Details: trade_journal_usdc.csv; open_positions_at_cutoff.csv; monthly_entry_results_usdc.csv; verification.json; study_manifest.json."]
    (OUT / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
