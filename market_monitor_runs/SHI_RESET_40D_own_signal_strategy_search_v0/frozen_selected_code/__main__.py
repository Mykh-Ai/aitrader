from __future__ import annotations

from dataclasses import asdict
from itertools import product
from pathlib import Path
import argparse
import hashlib
import json
import time

import pandas as pd

from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest
from .features import features, signals
from .replay import ExitRules, ReplayData, metrics, replay

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0"


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")


def variants():
    for family, lookback, flow, volume, trend, stop, floor, target, trail, hold in product(
        ["ACCEPTED_BREAK", "BREAKOUT", "TREND_RETEST", "SWEEP_RECLAIM"], [24, 48, 96], [0.0, 0.04],
        [1.0, 1.3], ["EMA", "PRESSURE"], [6, 12], [1.0, 1.5], [2.0, 4.0, 6.0], [0.0, 2.0], [48, 168]):
        config = {"family": family, "lookback": lookback, "flow": flow, "volume": volume, "trend": trend,
                  "exit": asdict(ExitRules(stop, floor, target, trail, hold))}
        config["id"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
        yield config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["search", "verify"])
    args = parser.parse_args()
    started = time.monotonic()
    feed, original = verified_inputs(ROOT, ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1")
    bars = features(feed)
    data = ReplayData(feed, bars)
    bars.to_csv(OUT / "causal_h1_features.csv", index=False)
    code = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    if args.mode == "verify":
        declared = json.loads((OUT / "batch_01_grid.json").read_text())
        assert declared["code_hashes"] == code
        candidates = json.loads((OUT / "development_finalists.json").read_text())
    else:
        grid = list(variants())
        target = OUT / "batch_01_development_results.csv"
        if target.exists():
            raise ValueError("Preserve previous batch results")
        save(OUT / "batch_01_grid.json", {
            "variant_count": len(grid), "variants": grid, "code_hashes": code,
            "notional_usd": 3000, "commission_usd_per_round_trip": 5, "slippage_bps_per_fill": 2,
            "development_entry_end": "2026-06-22T00:00:00Z", "validation_start": "2026-06-29T00:00:00Z",
            "maximum_horizon_hours": 168, "core_six_month_entry_interval": ["2026-04-01T00:00:00Z", "2026-10-01T00:00:00Z"],
            "selection": "Top development results per family; no validation-return ranking for finalist selection",
            "finalist_requirements": {"development_trades_min": 10, "development_net_positive": True,
                                      "core_net_usd_min": 500, "validation_net_positive": True,
                                      "later_validation_net_positive": True, "censored_trades_max": 0},
            "historical_parameter_search": True, "pristine_holdout": False})
        rows = []
        signal_cache = {}
        for n, config in enumerate(grid, 1):
            key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
            if key not in signal_cache:
                signal_cache[key] = signals(bars, *key)
            trades = replay(data, signal_cache[key], ExitRules(**config["exit"]), cutoff="2026-06-22T00:00:00Z")
            result = metrics(trades)
            rows.append({"id": config["id"], "family": config["family"], **result})
            if n % 200 == 0:
                pd.DataFrame(rows).to_csv(target.with_name("batch_01_progress.csv"), index=False)
                print(json.dumps({"phase": "development_search", "completed": n, "total": len(grid), "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)
        table = pd.DataFrame(rows)
        table.to_csv(target, index=False)
        eligible = table.loc[(table.trades >= 10) & (table.censored == 0) & (table.net_usd > 0)]
        selected = eligible.sort_values("net_usd", ascending=False).groupby("family", sort=False).head(12)
        ids = set(selected.id)
        candidates = [x for x in grid if x["id"] in ids]
        save(OUT / "development_finalists.json", candidates)
        print(json.dumps({"phase": "development_complete", "finalists": len(candidates), "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)

    rows = []
    folder = OUT / "minute_finalists"
    folder.mkdir(exist_ok=True)
    for n, config in enumerate(candidates, 1):
        key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
        direction = signals(bars, *key)
        trades = replay(data, direction, ExitRules(**config["exit"]), precise=True)
        trades.to_csv(folder / f"{config['id']}_trades.csv", index=False)
        if trades.empty:
            continue
        development = trades.loc[trades.decision_at < pd.Timestamp("2026-06-22T00:00:00Z")]
        validation = trades.loc[trades.decision_at.between(pd.Timestamp("2026-06-29T00:00:00Z"), pd.Timestamp("2026-08-25T00:00:00Z"), inclusive="left")]
        later = trades.loc[trades.decision_at >= pd.Timestamp("2026-09-01T00:00:00Z")]
        core = trades.loc[trades.decision_at >= pd.Timestamp("2026-04-01T00:00:00Z")]
        overall, dev, val, late, six = map(metrics, [trades, development, validation, later, core])
        qualified = overall["censored"] == 0 and six["net_usd"] >= 500 and dev["net_usd"] > 0 and val["net_usd"] > 0 and late["net_usd"] > 0
        rows.append({"id": config["id"], "family": config["family"], "qualified": qualified, **overall,
                     "development_net_usd": dev["net_usd"], "development_trades": dev["trades"],
                     "validation_net_usd": val["net_usd"], "validation_trades": val["trades"],
                     "later_net_usd": late["net_usd"], "later_trades": late["trades"],
                     "six_month_net_usd": six["net_usd"], "six_month_trades": six["trades"]})
        pd.DataFrame(rows).to_csv(OUT / "batch_01_minute_results.csv", index=False)
        print(json.dumps({"phase": "minute_verification", "completed": n, "total": len(candidates), "qualified_candidates": sum(x["qualified"] for x in rows)}, default=str), flush=True)
    save(OUT / "batch_01_completion.json", {"elapsed_seconds": round(time.monotonic() - started, 2), "code_hashes": code,
                                           "qualified_ids": [x["id"] for x in rows if x["qualified"]],
                                           "source_identity_reverified": len(verified_inputs(ROOT, ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1")[0]) == len(feed)})


if __name__ == "__main__":
    main()
