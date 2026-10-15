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
for family, lookback, flow, volume, trend, maturity, impulse, target, hold in product(
    ["ACCEPTED_BREAK", "BREAKOUT", "TREND_RETEST"], [24, 48, 96], [0.0, 0.04], [0.8, 1.3],
    ["NONE", "EMA", "PRESSURE"], [1.5, 2.5, 4.0, 100.0], [2.0, 100.0], [3.0, 6.0, 10.0], [24, 72, 168]):
    config = {"family": family, "lookback": lookback, "flow": flow, "volume": volume, "trend": trend,
              "maximum_ema24_distance_atr": maturity, "maximum_h1_range_atr": impulse,
              "exit": asdict(ExitRules(6, 1.5, target, 0, hold))}
    config["id"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    grid.append(config)
manifest = OUT / "batch_03_maturity_grid.json"
if manifest.exists():
    raise ValueError("Preserve previous batch")
manifest.write_text(json.dumps({"variants": grid, "variant_count": len(grid),
                               "hypothesis": "Avoid chasing extended displacement; compare direction-neutral and trend-conditioned accepted breaks/retests",
                               "prior_evidence": "39A prior-move maturity; 37E/37F broad pressure asymmetry; 40C narrow targets",
                               "selection_uses_previously_researched_history": True, "pristine_holdout": False,
                               "costs": {"notional_usd": 3000, "round_trip_commission_usd": 5, "slippage_bps_per_fill": 2},
                               "script_sha256": digest(Path(__file__)),
                               "code_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT / "research/strategy_search").glob("*.py"))}}, indent=2) + "\n")
rows, cache = [], {}
for n, config in enumerate(grid, 1):
    key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
    if key not in cache:
        cache[key] = signals(bars, *key)
    direction = cache[key].copy()
    extended = (bars.close - bars.ema24).abs() / bars.atr
    impulse = (bars.high - bars.low) / bars.atr
    direction[(extended > config["maximum_ema24_distance_atr"]) | (impulse > config["maximum_h1_range_atr"])] = 0
    trades = replay(data, direction, ExitRules(**config["exit"]))
    if trades.empty:
        continue
    dev = trades.loc[trades.decision_at < pd.Timestamp("2026-06-22T00:00:00Z")]
    val = trades.loc[trades.decision_at.between(pd.Timestamp("2026-06-29T00:00:00Z"), pd.Timestamp("2026-08-25T00:00:00Z"), inclusive="left")]
    later = trades.loc[trades.decision_at >= pd.Timestamp("2026-09-01T00:00:00Z")]
    core = trades.loc[trades.decision_at >= pd.Timestamp("2026-04-01T00:00:00Z")]
    all_m, dev_m, val_m, late_m, core_m = map(metrics, [trades, dev, val, later, core])
    qualifies = all_m["censored"] == 0 and core_m["net_usd"] >= 500 and dev_m["net_usd"] > 0 and val_m["net_usd"] > 0 and late_m["net_usd"] > 0
    rows.append({"id": config["id"], "family": config["family"], "qualified": qualifies, **all_m,
                 "development_net_usd": dev_m["net_usd"], "development_trades": dev_m["trades"],
                 "validation_net_usd": val_m["net_usd"], "validation_trades": val_m["trades"],
                 "later_net_usd": late_m["net_usd"], "later_trades": late_m["trades"],
                 "six_month_net_usd": core_m["net_usd"], "six_month_trades": core_m["trades"]})
    if n % 500 == 0 or n == len(grid):
        pd.DataFrame(rows).to_csv(OUT / "batch_03_coarse_results.csv", index=False)
        print(json.dumps({"phase": "maturity_search", "completed": n, "total": len(grid), "preliminary_passes": sum(r["qualified"] for r in rows), "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)
coarse = pd.DataFrame(rows)
coarse.to_csv(OUT / "batch_03_coarse_results.csv", index=False)
shortlist = coarse.loc[coarse.qualified].sort_values("development_net_usd", ascending=False).head(30)
ids = set(shortlist.id)
finalists = [c for c in grid if c["id"] in ids]
(OUT / "batch_03_finalists.json").write_text(json.dumps(finalists, indent=2) + "\n")
folder = OUT / "maturity_minute_finalists"
folder.mkdir()
verified = []
for n, config in enumerate(finalists, 1):
    key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
    direction = cache[key].copy()
    extended = (bars.close - bars.ema24).abs() / bars.atr
    impulse = (bars.high - bars.low) / bars.atr
    direction[(extended > config["maximum_ema24_distance_atr"]) | (impulse > config["maximum_h1_range_atr"])] = 0
    trades = replay(data, direction, ExitRules(**config["exit"]), precise=True)
    trades.to_csv(folder / f"{config['id']}_trades.csv", index=False)
    dev = trades.loc[trades.decision_at < pd.Timestamp("2026-06-22T00:00:00Z")]
    val = trades.loc[trades.decision_at.between(pd.Timestamp("2026-06-29T00:00:00Z"), pd.Timestamp("2026-08-25T00:00:00Z"), inclusive="left")]
    later = trades.loc[trades.decision_at >= pd.Timestamp("2026-09-01T00:00:00Z")]
    core = trades.loc[trades.decision_at >= pd.Timestamp("2026-04-01T00:00:00Z")]
    all_m, dev_m, val_m, late_m, core_m = map(metrics, [trades, dev, val, later, core])
    qualifies = all_m["censored"] == 0 and core_m["net_usd"] >= 500 and dev_m["net_usd"] > 0 and val_m["net_usd"] > 0 and late_m["net_usd"] > 0
    verified.append({"id": config["id"], "family": config["family"], "qualified": qualifies, **all_m,
                     "development_net_usd": dev_m["net_usd"], "development_trades": dev_m["trades"],
                     "validation_net_usd": val_m["net_usd"], "validation_trades": val_m["trades"],
                     "later_net_usd": late_m["net_usd"], "later_trades": late_m["trades"],
                     "six_month_net_usd": core_m["net_usd"], "six_month_trades": core_m["trades"]})
    pd.DataFrame(verified).to_csv(OUT / "batch_03_minute_results.csv", index=False)
    print(json.dumps({"phase": "maturity_minute_verification", "completed": n, "total": len(finalists), "qualified": sum(r["qualified"] for r in verified)}), flush=True)
(OUT / "batch_03_completion.json").write_text(json.dumps({"elapsed_seconds": time.monotonic() - started, "qualified_ids": [r["id"] for r in verified if r["qualified"]]}, indent=2) + "\n")
