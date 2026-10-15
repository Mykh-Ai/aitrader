from dataclasses import asdict
from itertools import product
from pathlib import Path
import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.strategy_search.features import features, signals
from research.strategy_search.replay import ExitRules, ReplayData, metrics, replay
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest

started = time.monotonic()
feed, _ = verified_inputs(ROOT, ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1")
bars = features(feed)
data = ReplayData(feed, bars)
grid = []
for flow, volume, maturity, impulse, stop, floor, target, hold, sides in product(
    [0.04, 0.08], [1.3, 1.6], [1.5, 2.5], [2.0, 2.5], [6, 12], [2.0, 2.5, 3.0],
    [6.0, 10.0, 12.0], [240, 336], ["BOTH", "LONG_ONLY"]):
    config = {"family": "TREND_RETEST", "lookback": 96, "flow": flow, "volume": volume, "trend": "EMA",
              "maximum_ema24_distance_atr": maturity, "maximum_h1_range_atr": impulse, "sides": sides,
              "exit": asdict(ExitRules(stop, floor, target, 0, hold))}
    config["id"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    grid.append(config)
manifest = OUT / "batch_05_retest_grid.json"
if manifest.exists():
    raise ValueError("Preserve prior batch")
manifest.write_text(json.dumps({"variants": grid, "variant_count": len(grid),
                               "hypothesis": "Long-horizon trend retests; periods are descriptive entry cohorts, not independent holdout",
                               "selection_on_previously_researched_full_history": True, "pristine_holdout": False,
                               "qualification": "At least 15 trades, no unresolved/gap-marked trade, full-history and six-month net both >=500, development positive",
                               "gap_policy": "CENSOR", "costs": {"notional_usd": 3000, "commission_usd": 5, "slippage_bps_per_fill": 2},
                               "script_sha256": digest(Path(__file__)),
                               "code_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT / "research/strategy_search").glob("*.py"))}}, indent=2) + "\n")
cache, rows = {}, []
for n, config in enumerate(grid, 1):
    key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
    if key not in cache:
        cache[key] = signals(bars, *key)
    direction = cache[key].copy()
    extended = (bars.close - bars.ema24).abs() / bars.atr
    impulse = (bars.high - bars.low) / bars.atr
    direction[(extended > config["maximum_ema24_distance_atr"]) | (impulse > config["maximum_h1_range_atr"])] = 0
    if config["sides"] == "LONG_ONLY":
        direction[direction < 0] = 0
    trades = replay(data, direction, ExitRules(**config["exit"]))
    if trades.empty:
        continue
    dev = trades.loc[trades.decision_at < pd.Timestamp("2026-06-22T00:00:00Z")]
    val = trades.loc[trades.decision_at.between(pd.Timestamp("2026-06-29T00:00:00Z"), pd.Timestamp("2026-08-25T00:00:00Z"), inclusive="left")]
    later = trades.loc[trades.decision_at >= pd.Timestamp("2026-09-01T00:00:00Z")]
    core = trades.loc[trades.decision_at >= pd.Timestamp("2026-04-01T00:00:00Z")]
    all_m, dev_m, val_m, late_m, core_m = map(metrics, [trades, dev, val, later, core])
    qualifies = all_m["trades"] >= 15 and all_m["censored"] == 0 and all_m["net_usd"] >= 500 and core_m["net_usd"] >= 500 and dev_m["net_usd"] > 0
    rows.append({"id": config["id"], "qualified": qualifies, **all_m,
                 "development_net_usd": dev_m["net_usd"], "development_trades": dev_m["trades"],
                 "validation_net_usd": val_m["net_usd"], "validation_trades": val_m["trades"],
                 "later_net_usd": late_m["net_usd"], "later_trades": late_m["trades"],
                 "six_month_net_usd": core_m["net_usd"], "six_month_trades": core_m["trades"]})
    if n % 200 == 0 or n == len(grid):
        pd.DataFrame(rows).to_csv(OUT / "batch_05_coarse_results.csv", index=False)
        print(json.dumps({"phase": "retest_refinement", "completed": n, "total": len(grid), "preliminary_passes": sum(r["qualified"] for r in rows), "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)
table = pd.DataFrame(rows)
table.to_csv(OUT / "batch_05_coarse_results.csv", index=False)
eligible = table.loc[table.qualified].sort_values("development_net_usd", ascending=False).head(30)
ids = set(eligible.id)
finalists = [c for c in grid if c["id"] in ids]
(OUT / "batch_05_finalists.json").write_text(json.dumps(finalists, indent=2) + "\n")
folder = OUT / "long_horizon_minute_finalists"
folder.mkdir()
verified = []
for n, config in enumerate(finalists, 1):
    key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
    direction = cache[key].copy()
    extended = (bars.close - bars.ema24).abs() / bars.atr
    impulse = (bars.high - bars.low) / bars.atr
    direction[(extended > config["maximum_ema24_distance_atr"]) | (impulse > config["maximum_h1_range_atr"])] = 0
    if config["sides"] == "LONG_ONLY":
        direction[direction < 0] = 0
    trades = replay(data, direction, ExitRules(**config["exit"]), precise=True)
    trades.to_csv(folder / f"{config['id']}_trades.csv", index=False)
    dev = trades.loc[trades.decision_at < pd.Timestamp("2026-06-22T00:00:00Z")]
    val = trades.loc[trades.decision_at.between(pd.Timestamp("2026-06-29T00:00:00Z"), pd.Timestamp("2026-08-25T00:00:00Z"), inclusive="left")]
    later = trades.loc[trades.decision_at >= pd.Timestamp("2026-09-01T00:00:00Z")]
    core = trades.loc[trades.decision_at >= pd.Timestamp("2026-04-01T00:00:00Z")]
    all_m, dev_m, val_m, late_m, core_m = map(metrics, [trades, dev, val, later, core])
    qualifies = all_m["trades"] >= 15 and all_m["censored"] == 0 and all_m["net_usd"] >= 500 and core_m["net_usd"] >= 500 and dev_m["net_usd"] > 0
    verified.append({"id": config["id"], "qualified": qualifies, **all_m,
                     "development_net_usd": dev_m["net_usd"], "development_trades": dev_m["trades"],
                     "validation_net_usd": val_m["net_usd"], "validation_trades": val_m["trades"],
                     "later_net_usd": late_m["net_usd"], "later_trades": late_m["trades"],
                     "six_month_net_usd": core_m["net_usd"], "six_month_trades": core_m["trades"]})
    pd.DataFrame(verified).to_csv(OUT / "batch_05_minute_results.csv", index=False)
    print(json.dumps({"phase": "refined_retest_minute_verification", "completed": n, "total": len(finalists), "qualified": sum(r["qualified"] for r in verified)}), flush=True)
(OUT / "batch_05_completion.json").write_text(json.dumps({"elapsed_seconds": time.monotonic() - started, "qualified_ids": [r["id"] for r in verified if r["qualified"]]}, indent=2) + "\n")
