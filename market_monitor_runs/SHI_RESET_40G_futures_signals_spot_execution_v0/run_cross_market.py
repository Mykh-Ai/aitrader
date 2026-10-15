from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
sys.path.insert(0, str(PRIOR))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals
from research.strategy_search.replay import ExitRules, ReplayData, metrics
from interventions import h4_inventory, candidate_map
from cross_market import execution_references, h4_regimes, apply_long_regime, portfolio, trade


def main():
    manifest = json.loads((OUT / "execution_manifest_v1.json").read_text())
    spec = manifest["baseline_spec"]
    assert all(digest(ROOT / p) == sha for p, sha in manifest["preserved_hashes"].items())
    assert all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items())
    assert digest(OUT / "spot_BTCUSDC/spot_minutes.csv") == manifest["spot_csv_sha256"]
    feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
    spot_all = pd.read_csv(OUT / "spot_BTCUSDC/spot_minutes.csv", parse_dates=["Timestamp"])
    spot_all.Timestamp = pd.to_datetime(spot_all.Timestamp, utc=True)
    spot_all = spot_all.loc[spot_all.Timestamp.between(feed.Timestamp.min(), feed.Timestamp.max())].reset_index(drop=True)
    spot = spot_all.loc[spot_all.DataQuality.eq("RAW")].copy().reset_index(drop=True)
    bars = features(feed)
    future_data = ReplayData(feed, bars)
    execution_bars, known = execution_references(feed, spot, bars)
    native_bars, _ = execution_references(feed, spot, bars, native=True)
    spot_data, native_data = ReplayData(spot, execution_bars), ReplayData(spot, native_bars)
    original = hybrid_signals(bars, spec["long"], spec["short"])
    candidates, rejected = candidate_map(future_data, original, spec, {"short_space_1r": True}, h4_inventory(feed, bars))
    short_space = np.zeros_like(original)
    for i, row in candidates.items():
        short_space[i] = row["side"]
    pd.DataFrame(rejected).to_csv(OUT / "futures_short_space_rejections.csv", index=False)
    regimes = h4_regimes(feed, bars)
    regimes.to_csv(OUT / "futures_h4_regimes.csv", index=False)
    known.to_csv(OUT / "decision_basis_quotes.csv", index=False)
    print("Futures features, spot execution references and causal H4 state prepared", flush=True)

    cutoff = pd.Timestamp("2026-06-20T23:59:00Z")
    prefix_feed = feed.loc[feed.Timestamp <= cutoff]
    prefix_spot = spot.loc[spot.Timestamp <= cutoff]
    prefix_bars = features(prefix_feed)
    visible = bars.available_at.le(cutoff)
    pd.testing.assert_frame_equal(prefix_bars, bars.loc[visible].reset_index(drop=True))
    prefix_exec, prefix_known = execution_references(prefix_feed, prefix_spot, prefix_bars)
    pd.testing.assert_frame_equal(prefix_exec, execution_bars.loc[visible].reset_index(drop=True))
    pd.testing.assert_frame_equal(prefix_known, known.loc[visible].reset_index(drop=True))
    pd.testing.assert_frame_equal(h4_regimes(prefix_feed, prefix_bars), regimes.loc[visible].reset_index(drop=True))

    ledgers = OUT / "variant_ledgers"
    ledgers.mkdir(exist_ok=True)
    summaries, controls = [], 0
    for variant in manifest["variants"]:
        source_signals = short_space if variant["short_space"] else original
        directions = apply_long_regime(source_signals, regimes, variant["h4_mode"])
        execution = future_data if variant["market"] == "FUTURES_PROXY" else native_data if variant["native_stops"] else spot_data
        trades = portfolio(execution, directions, spec, variant["management"])
        if variant["id"] in ["FUTURES_40D_CONTROL", "FUTURES_40F_CONTROL"]:
            previous_root = ROOT / "market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0" if variant["id"] == "FUTURES_40D_CONTROL" else PRIOR
            previous = pd.read_csv(previous_root / "selected_trade_ledger_usd.csv")
            for field in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
                previous[field] = pd.to_datetime(previous[field], utc=True)
            fields = [c for c in trades.columns if c in previous.columns]
            pd.testing.assert_frame_equal(trades[fields], previous[fields], check_exact=False, rtol=1e-10, atol=1e-10)
            controls += 1
        trades["variant"] = variant["id"]
        trades["execution_market"] = variant["market"]
        trades["signal_market"] = "BTCUSDT_PERPETUAL_FUTURES"
        trades["h4_regime"] = [regimes.h4_regime.iloc[int(i)] for i in trades.signal_index]
        trades["basis_ratio_at_decision"] = [known.basis_ratio.iloc[int(i)] if variant["market"] != "FUTURES_PROXY" else 1. for i in trades.signal_index]
        trades["basis_spot_close_at"] = [known.spot_close_at.iloc[int(i)] if variant["market"] != "FUTURES_PROXY" else pd.NaT for i in trades.signal_index]
        trades["basis_futures_close_at"] = [known.futures_close_at.iloc[int(i)] for i in trades.signal_index]
        trades["notional_quote"] = 3000.
        trades["quantity_btc"] = 3000. / trades.entry_price
        trades["holding_hours"] = (trades.exit_at - trades.entry_at).dt.total_seconds() / 3600
        previous_exit = None
        for row in trades.itertuples():
            if previous_exit is not None:
                assert row.entry_at > previous_exit + pd.Timedelta(minutes=3)
            previous_exit = row.expiry_at if row.censored else row.exit_at
            if variant["market"] != "FUTURES_PROXY":
                assert row.basis_spot_close_at <= row.decision_at and row.basis_futures_close_at <= row.decision_at
            if not row.censored:
                fills = json.loads(row.fills_json)
                gross = sum(row.direction * (x["price"] - row.entry_price) * x["fraction"] * row.quantity_btc for x in fills)
                slippage = (row.entry_price + sum(x["price"] * x["fraction"] for x in fills)) * row.quantity_btc * .0002
                np.testing.assert_allclose([row.gross_usd, row.slippage_usd, row.net_usd], [gross, slippage, gross - 5 - slippage], atol=1e-8)
            for action in json.loads(row.amendments_json):
                assert action["reference_at"] <= action["decision_at"]
                if action["active_at"] is not None:
                    assert action["active_at"] >= action["decision_at"] + execution.minute
        trades.to_csv(ledgers / f'{variant["id"]}.csv', index=False)
        closed = trades.loc[~trades.censored]
        core = trades.loc[trades.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
        short = closed.loc[closed.direction.lt(0)]
        record = {"variant": variant["id"], "market": variant["market"], "h4_mode": variant["h4_mode"], "management": variant["management"],
                  **metrics(trades), "six_month_net_usd": metrics(core)["net_usd"], "six_month_censored": metrics(core)["censored"],
                  "positive_trades": int(closed.net_usd.gt(0).sum()), "negative_trades": int(closed.net_usd.lt(0).sum()),
                  "stops": int(closed.exit_reason.isin(["STOP", "STOP_GAP"]).sum()), "trail_stops": int(closed.exit_reason.str.startswith("TRAIL_STOP").sum()),
                  "targets": int(closed.exit_reason.eq("TARGET").sum()), "expiries": int(closed.exit_reason.str.startswith("EXPIRY").sum()),
                  "partial_trades": int(closed.partial_filled.sum()), "short_trades": len(short), "short_net_usd": float(short.net_usd.sum()),
                  "long_trades": int(closed.direction.gt(0).sum()), "long_net_usd": float(closed.loc[closed.direction.gt(0), "net_usd"].sum()),
                  "isolated_spot_omissions": int(trades.omitted_minutes.sum())}
        summaries.append(record)
        pd.DataFrame(summaries).to_csv(OUT / "cross_market_results.csv", index=False)
        print(f'{variant["id"]}: trades={len(trades)} positive={record["positive_trades"]} negative={record["negative_trades"]} censored={record["censored"]} net={record["net_usd"]:.2f}', flush=True)
    assert controls == 2
    # Fixed-entry attribution is diagnostic; do not sum possibly overlapping paths as a portfolio.
    fixed = pd.read_csv(PRIOR / "selected_trade_ledger_usd.csv")
    comparisons = []
    for r in fixed.itertuples():
        case = trade(spot_data, int(r.signal_index), int(r.direction), ExitRules(**spec["long" if r.direction > 0 else "short"]["exit"]))
        if case:
            comparisons.append({"signal_index": r.signal_index, "direction": r.direction, "original_proxy_net": r.net_usd,
                                "spot_case_net": case["net_usd"], "proxy_entry": r.entry_price, "spot_entry": case["entry_price"],
                                "proxy_reason": r.exit_reason, "spot_reason": case["exit_reason"], "censored": case["censored"]})
    pd.DataFrame(comparisons).to_csv(OUT / "fixed_21_entry_market_comparison_DIAGNOSTIC.csv", index=False)
    for name in ["FUTURES_40F_CONTROL", "SPOT_40F_FIXED"]:
        t = pd.read_csv(ledgers / f"{name}.csv")
        g = t.loc[t.direction.gt(0)].groupby("h4_regime").agg(trades=("net_usd", "size"), positive=("net_usd", lambda x: int(x.gt(0).sum())),
                         negative=("net_usd", lambda x: int(x.lt(0).sum())), net_usd=("net_usd", "sum"))
        g.to_csv(OUT / f"{name}_long_h4_breakdown.csv")
    verification = {"all_13_declared_runs_completed": len(summaries) == 13, "both_futures_controls_reproduced": controls == 2,
                    "real_prefix_future_feature_h4_regime_and_basis_invariance": True, "asof_mapping_no_future_quotes": True,
                    "global_book_fill_cash_and_amendment_clocks_verified": True,
                    "futures_and_spot_sources_separate": True, "all_official_archive_checksums_verified": True,
                    "source_and_original_artifacts_unchanged": all(digest(ROOT / p) == sha for p, sha in manifest["preserved_hashes"].items()),
                    "study_code_unchanged": all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items()),
                    "execution_is_spot_price_model_not_borrow_or_orderbook_proof": True}
    assert all(verification.values())
    (OUT / "run_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
