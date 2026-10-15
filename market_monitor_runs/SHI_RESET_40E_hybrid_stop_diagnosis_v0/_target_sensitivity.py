"""Controlled target-only research replay; retain the original 40D baseline."""
from copy import deepcopy
from itertools import product
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, metrics

SRC = ROOT / "market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0"
manifest = json.loads((OUT / "study_manifest.json").read_text())
spec = json.loads((SRC / "selected_strategy.json").read_text())
assert all(digest(SRC / p) == sha for p, sha in manifest["baseline_hashes"].items())
assert all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items())
feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
bars = features(feed)
data = ReplayData(feed, bars)
direction = hybrid_signals(bars, spec["long"], spec["short"])
baseline = pd.read_csv(SRC / "selected_trade_ledger_usd.csv")
for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
    baseline[col] = pd.to_datetime(baseline[col], utc=True)
baseline_ids = set(zip(baseline.signal_index, baseline.direction))
folder = OUT / "target_pair_ledgers"
folder.mkdir(exist_ok=True)
summaries, baseline_reproduced = [], False
for short_r, long_r in product([2, 4, 6, 8], [2, 4, 6, 8, 10]):
    long, short = deepcopy(spec["long"]), deepcopy(spec["short"])
    long["exit"]["target_r"] = float(long_r)
    short["exit"]["target_r"] = float(short_r)
    np.testing.assert_array_equal(direction, hybrid_signals(bars, long, short))
    trades = replay_hybrid(data, direction, long, short)
    trades.to_csv(folder / f"short_{short_r}R_long_{long_r}R.csv", index=False)
    if (short_r, long_r) == (6, 10):
        pd.testing.assert_frame_equal(trades, baseline[trades.columns], check_exact=False, rtol=1e-11, atol=1e-11)
        baseline_reproduced = True
    previous = None
    for row in trades.itertuples():
        if previous is not None:
            assert row.entry_at > previous + pd.Timedelta(minutes=3)
        previous = row.expiry_at if row.censored else row.exit_at
        assert row.initial_risk_usd > 0 and row.precise_minute_replay
        assert not row.short_gap_conservative_mark
        assert row.target_R == (long_r if row.direction == 1 else short_r)
        if not row.censored:
            quantity = 3000 / row.entry_price
            gross = row.direction * (row.exit_price - row.entry_price) * quantity
            slippage = (row.entry_price + row.exit_price) * quantity * .0002
            np.testing.assert_allclose([row.gross_usd, row.slippage_usd, row.net_usd], [gross, slippage, gross - 5 - slippage])
    core = trades.loc[trades.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
    six = metrics(core)
    ids = set(zip(trades.signal_index, trades.direction))
    record = {"short_target_R": short_r, "long_target_R": long_r, "baseline": (short_r, long_r) == (6, 10),
              **metrics(trades), "six_month_net_usd": six["net_usd"], "six_month_censored": six["censored"],
              "same_as_baseline_entry_count": len(ids & baseline_ids), "new_entry_count": len(ids - baseline_ids),
              "removed_baseline_entry_count": len(baseline_ids - ids),
              "targets": int(trades.exit_reason.eq("TARGET").sum()),
              "stops": int(trades.exit_reason.isin(["STOP", "STOP_GAP"]).sum()),
              "expiries": int(trades.exit_reason.str.startswith("EXPIRY").sum())}
    for side, sign in [("long", 1), ("short", -1)]:
        group = trades.loc[trades.direction.eq(sign)]
        side_metrics = metrics(group)
        record[f"{side}_trades"] = len(group)
        record[f"{side}_net_usd"] = side_metrics["net_usd"]
        record[f"{side}_censored"] = side_metrics["censored"]
        record[f"{side}_stops"] = int(group.exit_reason.isin(["STOP", "STOP_GAP"]).sum())
        record[f"{side}_targets"] = int(group.exit_reason.eq("TARGET").sum())
    summaries.append(record)
    pd.DataFrame(summaries).to_csv(OUT / "target_pair_portfolio_results.csv", index=False)

assert baseline_reproduced and len(summaries) == 20
verification = {"baseline_6R_short_10R_long_reproduced": baseline_reproduced,
                "pairs_completed": len(summaries), "identical_signal_array_each_pair": True,
                "single_global_book_and_cooldown_verified": True, "independent_cash_arithmetic_verified": True,
                "baseline_artifacts_unchanged": all(digest(SRC / p) == sha for p, sha in manifest["baseline_hashes"].items()),
                "code_identity_unchanged": all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items()),
                "source_identity_verified": True, "historically_exposed_sensitivity_only": True,
                "script_sha256": digest(Path(__file__))}
assert verification["baseline_artifacts_unchanged"] and verification["code_identity_unchanged"]
(OUT / "target_sensitivity_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")
table = pd.DataFrame(summaries)
print(table[["short_target_R", "long_target_R", "trades", "censored", "net_usd", "six_month_net_usd", "stops", "targets", "new_entry_count", "long_net_usd", "short_net_usd"]].to_string(index=False))
