from pathlib import Path
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
from research.strategy_search.hybrid import hybrid_signals
from research.strategy_search.replay import ReplayData, metrics
from interventions import h4_inventory, portfolio


def main():
    manifest = json.loads((OUT / "study_manifest.json").read_text())
    spec = manifest["baseline_spec"]
    source = ROOT / manifest["baseline_root"]
    assert all(digest(source / p) == sha for p, sha in manifest["baseline_artifact_hashes"].items())
    assert all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items())
    assert all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items())
    feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
    bars = features(feed)
    data = ReplayData(feed, bars)
    original = hybrid_signals(bars, spec["long"], spec["short"])
    inventory = h4_inventory(feed, bars)
    print("Verified frozen input; causal H4 inventory ready", flush=True)
    # Real-feed prefix check: formation and retirement cannot consume future bars.
    cutoff = pd.Timestamp("2026-06-20T23:59:00Z")
    prefix = feed.loc[feed.Timestamp <= cutoff]
    prefix_bars = features(prefix)
    pd.testing.assert_frame_equal(prefix_bars, bars.loc[bars.available_at <= cutoff].reset_index(drop=True))
    prefix_inventory = h4_inventory(prefix, prefix_bars)
    assert all(inventory[i] == prefix_inventory[i] for i in prefix_inventory)
    np.testing.assert_array_equal(original[:len(prefix_bars)], hybrid_signals(prefix_bars, spec["long"], spec["short"]))

    baseline = pd.read_csv(source / "selected_trade_ledger_usd.csv")
    for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        baseline[col] = pd.to_datetime(baseline[col], utc=True)
    baseline_ids = set(zip(baseline.signal_index, baseline.direction))
    ledgers = OUT / "variant_ledgers"
    ledgers.mkdir(exist_ok=True)
    summaries, matched = [], False
    for variant in manifest["variants"]:
        trades, rejected = portfolio(data, original, spec, variant, inventory)
        if variant["id"] == "BASELINE":
            columns = [c for c in baseline.columns if c in trades.columns]
            pd.testing.assert_frame_equal(trades[columns], baseline[columns], check_exact=False, rtol=1e-11, atol=1e-11)
            matched = True
        trades.to_csv(ledgers / f'{variant["id"]}.csv', index=False)
        rejected.to_csv(ledgers / f'{variant["id"]}_rejections.csv', index=False)
        previous = None
        for row in trades.itertuples():
            assert row.source_index <= row.signal_index
            assert row.decision_at == pd.Timestamp(data.available[row.signal_index], tz="UTC")
            assert row.entry_at >= row.decision_at + pd.Timedelta(minutes=1)
            if previous is not None:
                assert row.entry_at > previous + pd.Timedelta(minutes=3)
            previous = row.expiry_at if row.censored else row.exit_at
            if pd.notna(row.reference_available_at):
                assert row.reference_available_at <= row.decision_at
            if pd.notna(row.exit_decision_at) and row.exit_reason == "REFERENCE_INVALIDATION":
                assert row.exit_at >= row.exit_decision_at + pd.Timedelta(minutes=1)
            if pd.notna(row.stop_amendment_active_at):
                assert row.stop_amendment_active_at >= row.stop_amendment_decision_at + pd.Timedelta(minutes=1)
            if not row.censored:
                quantity = 3000 / row.entry_price
                gross = row.direction * (row.exit_price - row.entry_price) * quantity
                slippage = (row.entry_price + row.exit_price) * quantity * .0002
                np.testing.assert_allclose([row.gross_usd, row.slippage_usd, row.net_usd], [gross, slippage, gross - 5 - slippage], atol=1e-8)
                assert row.commission_usd == 5
                end_label = row.exit_at.value + (data.minute if row.exit_price_clock == "MINUTE_OPEN" else 0)
                start, end = np.searchsorted(data.minute_ts, row.entry_at.value + data.minute), np.searchsorted(data.minute_ts, end_label, side="right")
                stamps = np.r_[row.entry_at.value, data.minute_ts[start:end]]
                assert data.raw[start:end].all() and np.diff(stamps).max() <= 2 * data.minute
        core = trades.loc[trades.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
        core_metrics = metrics(core)
        closed = trades.loc[~trades.censored]
        ids = set(zip(trades.signal_index, trades.direction))
        record = {"variant": variant["id"], **metrics(trades), "six_month_net_usd": core_metrics["net_usd"],
                  "six_month_censored": core_metrics["censored"], "positive_trades": int(closed.net_usd.gt(0).sum()),
                  "negative_trades": int(closed.net_usd.lt(0).sum()), "net_win_rate": float(closed.net_usd.gt(0).mean()),
                  "stops": int(closed.exit_reason.isin(["STOP", "STOP_GAP"]).sum()),
                  "lock_stops": int(closed.exit_reason.str.startswith("LOCK_STOP").sum()),
                  "invalidations": int(closed.exit_reason.eq("REFERENCE_INVALIDATION").sum()),
                  "targets": int(closed.exit_reason.eq("TARGET").sum()), "expiries": int(closed.exit_reason.str.startswith("EXPIRY").sum()),
                  "same_baseline_entries": len(ids & baseline_ids), "new_entries": len(ids - baseline_ids),
                  "removed_baseline_entries": len(baseline_ids - ids), "signal_rejections": len(rejected),
                  "long_net_usd": float(closed.loc[closed.direction.eq(1), "net_usd"].sum()),
                  "short_net_usd": float(closed.loc[closed.direction.eq(-1), "net_usd"].sum())}
        summaries.append(record)
        pd.DataFrame(summaries).to_csv(OUT / "intervention_results.csv", index=False)
        print(f'{variant["id"]}: trades={len(trades)} wins={record["positive_trades"]} losses={record["negative_trades"]} censored={record["censored"]} net={record["net_usd"]:.2f}', flush=True)
    assert matched and len(summaries) == len(manifest["variants"])

    # All six original deadline exits, with explicit unrealized extreme labels.
    expiry_rows = []
    for trade in baseline.loc[baseline.exit_reason.str.startswith("EXPIRY")].to_dict("records"):
        entry, exit_at, side = trade["entry_at"], trade["exit_at"], trade["direction"]
        start = np.searchsorted(data.minute_ts, entry.value + data.minute)
        end = np.searchsorted(data.minute_ts, exit_at.value, side="right")
        favorable = side * ((data.mh[start:end] if side > 0 else data.ml[start:end]) - trade["entry_price"])
        offset = int(np.argmax(favorable))
        peak_price = data.mh[start + offset] if side > 0 else data.ml[start + offset]
        risk = abs(trade["entry_price"] - trade["stop_price"])
        quantity = 3000 / trade["entry_price"]
        extreme_gross = favorable[offset] * quantity
        extreme_net = extreme_gross - 5 - (trade["entry_price"] + peak_price) * quantity * .0002
        row = {**trade, "side": "LONG" if side > 0 else "SHORT", "mfe_R": favorable[offset] / risk,
               "mfe_minute_available_at": pd.Timestamp(data.minute_ts[start + offset], tz="UTC"),
               "hours_to_mfe": (data.minute_ts[start + offset] - entry.value) / data.hour,
               "unrealized_extreme_gross_usd_not_fill": extreme_gross,
               "unrealized_extreme_net_usd_not_fill": extreme_net, "giveback_from_unrealized_extreme_usd": extreme_net - trade["net_usd"]}
        for hours in [24, 48, 72, 96, 120, 144, 168]:
            stamp = entry.value + hours * data.hour
            point = np.searchsorted(data.minute_ts, stamp)
            if point < len(data.minute_ts) and data.minute_ts[point] == stamp and data.raw[point]:
                price = data.mc[point]
                row[f"snapshot_net_{hours}h_usd"] = side * (price - trade["entry_price"]) * quantity - 5 - (trade["entry_price"] + price) * quantity * .0002
            else:
                row[f"snapshot_net_{hours}h_usd"] = None
        expiry_rows.append(row)
    pd.DataFrame(expiry_rows).to_csv(OUT / "all_six_expiry_cases.csv", index=False)
    original_details = pd.read_csv(ROOT / "market_monitor_runs/SHI_RESET_40E_hybrid_stop_diagnosis_v0/all_trade_diagnostics.csv")
    original_details.groupby("stopped")[["mfe_before_terminal_R", "entry_volume_ratio", "entry_delta_signed", "entry_trend_efficiency24", "opposing_h4_barrier_R"]].median().to_csv(OUT / "all_stops_vs_other_outcomes.csv")
    verification = {"baseline_reproduced": matched, "real_feed_prefix_h4_inventory_invariance": True,
                    "real_feed_prefix_feature_and_signal_invariance": True, "all_six_expiry_cases_accounted": len(expiry_rows) == 6,
                    "all_declared_variants_completed": len(summaries) == len(manifest["variants"]),
                    "global_book_latency_causal_reference_and_cash_checks": True,
                    "source_identity_verified": True,
                    "baseline_artifacts_unchanged": all(digest(source / p) == sha for p, sha in manifest["baseline_artifact_hashes"].items()),
                    "original_code_identity_unchanged": all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items()),
                    "study_code_identity_unchanged": all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items()),
                    "historical_selection_not_holdout": True, "production_policy_unchanged": True}
    assert all(verification.values())
    (OUT / "run_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")
    print(pd.DataFrame(expiry_rows)[["side", "entry_at", "net_usd", "mfe_R", "hours_to_mfe", "giveback_from_unrealized_extreme_usd"]].to_string(index=False))


if __name__ == "__main__":
    main()
