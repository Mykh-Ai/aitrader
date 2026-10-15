from dataclasses import asdict
from pathlib import Path
import json
import sys
import time

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.strategy_search.features import features, signals
from research.strategy_search.replay import ExitRules, ReplayData, metrics, replay
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest

started = time.monotonic()
declared = json.loads((OUT / "batch_01_grid.json").read_text())
assert all(digest(ROOT / name) == value for name, value in declared["code_hashes"].items())
table = pd.read_csv(OUT / "batch_01_development_results.csv")
eligible = table.loc[(table.trades >= 6) & (table.censored == 0) & (table.net_usd > 0)]
ids = set(eligible.id)
candidates = [c for c in declared["variants"] if c["id"] in ids]
manifest = OUT / "batch_02_expanded_selection.json"
if manifest.exists():
    raise ValueError("Preserve completed or partial batch")
manifest.write_text(json.dumps({"candidate_count": len(candidates), "candidates": candidates,
                               "selection": "Every positive uncensored development variant with at least six trades",
                               "same_variant_grid": True, "adaptation": "Expanded the original development shortlist; validation is previously observed",
                               "pristine_holdout": False, "script_sha256": digest(Path(__file__))}, indent=2) + "\n")
feed, _ = verified_inputs(ROOT, ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1")
bars = features(feed)
data = ReplayData(feed, bars)
folder = OUT / "expanded_minute_finalists"
folder.mkdir()
rows, cache = [], {}
for n, config in enumerate(candidates, 1):
    key = tuple(config[k] for k in ["family", "lookback", "flow", "volume", "trend"])
    if key not in cache:
        cache[key] = signals(bars, *key)
    trades = replay(data, cache[key], ExitRules(**config["exit"]), precise=True)
    trades.to_csv(folder / f"{config['id']}_trades.csv", index=False)
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
    if n % 25 == 0 or n == len(candidates):
        pd.DataFrame(rows).to_csv(OUT / "batch_02_minute_results.csv", index=False)
        print(json.dumps({"phase": "expanded_minute_verification", "completed": n, "total": len(candidates),
                          "qualified_count": sum(r["qualified"] for r in rows), "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)
(OUT / "batch_02_completion.json").write_text(json.dumps({"qualified_ids": [r["id"] for r in rows if r["qualified"]],
                                                         "elapsed_seconds": time.monotonic() - started}, indent=2) + "\n")
