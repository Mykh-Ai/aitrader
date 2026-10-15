"""User-directed 2R trigger sensitivity, frozen independently from 40F."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
ENGINE = ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ENGINE))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals
from research.strategy_search.replay import ExitRules, ReplayData, metrics
from interventions import candidate_map, h4_inventory, intervention_path


def main():
    manifest = json.loads((OUT / "execution_manifest_v2.json").read_text())
    spec = manifest["baseline_spec"]
    assert digest(Path(__file__)) == manifest["driver_sha256"]
    assert digest(ENGINE / "interventions.py") == manifest["engine_sha256"]
    assert all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items())
    feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
    bars = features(feed)
    data = ReplayData(feed, bars)
    original = hybrid_signals(bars, spec["long"], spec["short"])
    inventory = h4_inventory(feed, bars)
    controls = {(False, 0): "BASELINE", (False, 1): "SHORT_LOCK_1R_TO_0_25R",
                (True, 0): "SHORT_SPACE_1R", (True, 1): "SHORT_SPACE_SHORT_LOCK"}
    ledgers = OUT / "variant_ledgers"
    ledgers.mkdir(exist_ok=True)
    summaries, control_count = [], 0
    for variant in manifest["variants"]:
        candidate_variant = {"short_space_1r": variant["short_space"]}
        candidates, rejected = candidate_map(data, original, spec, candidate_variant, inventory)
        rows, busy = [], -1
        for i, candidate in sorted(candidates.items()):
            side = candidate["side"]
            if data.available[i] + data.minute <= busy:
                continue
            config = spec["long" if side > 0 else "short"]
            trigger = variant["trigger_R"] if side < 0 else 0
            row = intervention_path(data, i, side, ExitRules(**config["exit"]), lock_trigger_r=trigger, lock_stop_r=.25)
            if row is None:
                continue
            row.update({"family": config["family"], "source_index": candidate["source_index"], "variant": variant["id"]})
            rows.append(row)
            end = row["expiry_at"] if row["censored"] else row["exit_at"]
            busy = end.value + 3 * data.minute
        trades = pd.DataFrame(rows)
        for field in ["decision_at", "entry_at", "exit_at", "expiry_at", "exit_decision_at", "stop_amendment_decision_at", "stop_amendment_active_at"]:
            trades[field] = pd.to_datetime(trades[field], utc=True)
        key = (variant["short_space"], variant["trigger_R"])
        if key in controls:
            previous = pd.read_csv(ENGINE / "variant_ledgers" / f"{controls[key]}.csv")
            for field in ["decision_at", "entry_at", "exit_at", "expiry_at", "exit_decision_at", "stop_amendment_decision_at", "stop_amendment_active_at"]:
                previous[field] = pd.to_datetime(previous[field], utc=True)
            fields = [c for c in trades.columns if c in previous.columns and c != "variant"]
            pd.testing.assert_frame_equal(trades[fields], previous[fields], check_exact=False, rtol=1e-11, atol=1e-11)
            control_count += 1
        previous_exit = None
        for row in trades.itertuples():
            if previous_exit is not None:
                assert row.entry_at > previous_exit + pd.Timedelta(minutes=3)
            previous_exit = row.expiry_at if row.censored else row.exit_at
            if pd.notna(row.stop_amendment_active_at):
                assert row.direction < 0
                assert row.stop_amendment_active_at >= row.stop_amendment_decision_at + pd.Timedelta(minutes=1)
                m = np.searchsorted(data.minute_ts, row.stop_amendment_decision_at.value)
                risk = row.stop_price - row.entry_price
                assert (row.entry_price - data.ml[m]) / risk >= variant["trigger_R"]
                np.testing.assert_allclose(row.final_stop_price, row.entry_price - .25 * risk)
            if not row.censored:
                qty = 3000 / row.entry_price
                gross = row.direction * (row.exit_price - row.entry_price) * qty
                slip = (row.entry_price + row.exit_price) * qty * .0002
                np.testing.assert_allclose([row.gross_usd, row.slippage_usd, row.net_usd], [gross, slip, gross - 5 - slip], atol=1e-8)
        trades.to_csv(ledgers / f'{variant["id"]}.csv', index=False)
        pd.DataFrame(rejected).to_csv(ledgers / f'{variant["id"]}_rejections.csv', index=False)
        closed = trades.loc[~trades.censored]
        short = closed.loc[closed.direction.lt(0)]
        core = trades.loc[trades.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
        row = {"variant": variant["id"], "short_space_filter": variant["short_space"], "trigger_R": variant["trigger_R"],
               **metrics(trades), "six_month_net_usd": metrics(core)["net_usd"],
               "positive_trades": int(closed.net_usd.gt(0).sum()), "negative_trades": int(closed.net_usd.lt(0).sum()),
               "net_win_rate": float(closed.net_usd.gt(0).mean()), "short_trades": len(short), "short_net_usd": float(short.net_usd.sum()),
               "short_positive_trades": int(short.net_usd.gt(0).sum()), "short_negative_trades": int(short.net_usd.lt(0).sum()),
               "original_stops": int(closed.exit_reason.isin(["STOP", "STOP_GAP"]).sum()),
               "protective_stops": int(closed.exit_reason.str.startswith("LOCK_STOP").sum()),
               "targets": int(closed.exit_reason.eq("TARGET").sum()),
               "long_net_usd": float(closed.loc[closed.direction.gt(0), "net_usd"].sum())}
        summaries.append(row)
        pd.DataFrame(summaries).to_csv(OUT / "comparison.csv", index=False)
        print(f'{variant["id"]}: trades={len(trades)} positive={row["positive_trades"]} negative={row["negative_trades"]} censored={row["censored"]} net={row["net_usd"]:.2f} short_net={row["short_net_usd"]:.2f}', flush=True)
    verification = {"all_six_declared_replays_completed": len(summaries) == 6, "all_four_40F_controls_match": control_count == 4,
                    "2R_is_only_new_trigger_0_25R_stop_unchanged": True,
                    "amendment_latency_causal_trigger_and_cash_checks": True, "global_position_book_verified": True,
                    "source_identity_verified": True, "code_identity_unchanged": digest(ENGINE / "interventions.py") == manifest["engine_sha256"],
                    "original_code_identity_unchanged": all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items()),
                    "baseline_artifacts_preserved": all(digest(ROOT / p) == sha for p, sha in manifest["preserved_artifact_hashes"].items()),
                    "historically_exposed_not_holdout": True}
    assert all(verification.values())
    (OUT / "run_verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
