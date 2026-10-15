from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest, usable_observations
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, metrics

spec = json.loads((OUT / "selected_strategy.json").read_text())
assert all(digest(ROOT / name) == value for name, value in spec["code_hashes"].items())
feed, old_contract = verified_inputs(ROOT, ROOT / spec["source_preparation"])
bars = features(feed)
data = ReplayData(feed, bars)
direction = hybrid_signals(bars, spec["long"], spec["short"])
trades = replay_hybrid(data, direction, spec["long"], spec["short"])
seed = pd.read_csv(OUT / "hybrid_seed_trade_ledger.csv")
date_fields = ["decision_at", "entry_at", "exit_at", "expiry_at"]
for field in date_fields:
    seed[field] = pd.to_datetime(seed[field], utc=True)
pd.testing.assert_frame_equal(trades, seed, check_exact=False, rtol=1e-11, atol=1e-11)
assert not trades.censored.any()
assert not trades.short_gap_conservative_mark.any()
assert trades.gap_policy.eq("CENSOR").all()
assert not trades.duplicated(["decision_at", "direction"]).any()
assert np.diff(data.times).min() == data.hour and np.diff(data.times).max() == data.hour

# Actual nontrivial source-prefix test, not just a synthetic fixture.
prefix_feed = feed.loc[feed.Timestamp <= pd.Timestamp("2026-06-20T23:59:00Z")]
prefix_bars = features(prefix_feed)
asof = bars.loc[bars.available_at <= prefix_feed.Timestamp.max()].reset_index(drop=True)
pd.testing.assert_frame_equal(asof, prefix_bars)
np.testing.assert_array_equal(direction[:len(prefix_bars)], hybrid_signals(prefix_bars, spec["long"], spec["short"]))
assert np.count_nonzero(direction[:len(prefix_bars)]) > 0

raw = usable_observations(feed).set_index("Timestamp", drop=False)
previous_exit = None
minute = pd.Timedelta(minutes=1)
for row in trades.to_dict("records"):
    if previous_exit is not None:
        assert row["entry_at"] > previous_exit + pd.Timedelta(minutes=3)
    previous_exit = row["exit_at"]
    i, side = row["signal_index"], row["direction"]
    assert pd.Timestamp(data.available[i], tz="UTC") == row["decision_at"]
    assert direction[i] == side
    assert row["entry_at"] >= row["decision_at"] + minute
    assert row["entry_at"] <= row["decision_at"] + 2 * minute
    first = raw.loc[row["entry_at"] + minute]
    assert first.OpenPrice == row["entry_price"]
    assert row["decision_at"] <= bars.available_at.iloc[i]
    assert bars.context_usable.iloc[i]
    path = raw.loc[(raw.Timestamp >= row["entry_at"] + minute) & (raw.Timestamp <= row["exit_at"])]
    assert path.DataQuality.eq("RAW").all()
    assert (pd.DatetimeIndex(path.Timestamp)[1:] - pd.DatetimeIndex(path.Timestamp)[:-1]).max() <= 2 * minute
    assert row["exit_at"] <= row["expiry_at"] + minute
    quantity = 3000.0 / row["entry_price"]
    risk = abs(row["entry_price"] - row["stop_price"])
    assert row["target_price"] > row["entry_price"] > row["stop_price"] if side == 1 else row["target_price"] < row["entry_price"] < row["stop_price"]
    gross = side * (row["exit_price"] - row["entry_price"]) * quantity
    slip = (row["entry_price"] + row["exit_price"]) * quantity * .0002
    np.testing.assert_allclose([row["initial_risk_usd"], row["gross_usd"], row["commission_usd"], row["slippage_usd"], row["net_usd"]],
                               [risk * quantity, gross, 5, slip, gross - 5 - slip], atol=1e-10)
    np.testing.assert_allclose(abs(row["target_price"] - row["entry_price"]) / risk, row["target_R"])
    config = spec["long"] if side == 1 else spec["short"]
    structural = bars.iloc[i][f"lower{config['exit']['stop_lookback']}" if side == 1 else f"upper{config['exit']['stop_lookback']}"]
    expected_stop = min(structural * .9995, row["entry_price"] - bars.atr.iloc[i] * config["exit"]["atr_floor"]) if side == 1 else max(structural * 1.0005, row["entry_price"] + bars.atr.iloc[i] * config["exit"]["atr_floor"])
    np.testing.assert_allclose(row["stop_price"], expected_stop, atol=1e-8)
    # Verify the first observable terminal touch independently in vector form.
    before_exit = path.loc[path.Timestamp < row["exit_at"]]
    stop_hits = before_exit.LowPrice.le(row["stop_price"]) if side == 1 else before_exit.HiPrice.ge(row["stop_price"])
    target_hits = before_exit.HiPrice.ge(row["target_price"]) if side == 1 else before_exit.LowPrice.le(row["target_price"])
    assert not stop_hits.any() and not target_hits.any()
    if row["exit_reason"] == "TARGET":
        last = path.iloc[-1]
        assert last.HiPrice >= row["target_price"] if side == 1 else last.LowPrice <= row["target_price"]
        assert row["exit_price"] == row["target_price"]
    elif row["exit_reason"] in {"STOP", "STOP_GAP"}:
        last = path.iloc[-1]
        assert last.LowPrice <= row["stop_price"] if side == 1 else last.HiPrice >= row["stop_price"]
    elif row["exit_reason"] == "EXPIRY":
        assert row["exit_at"] == row["expiry_at"]
        assert row["exit_price"] == path.ClosePrice.iloc[-1]
    else:
        assert row["exit_reason"] == "EXPIRY_NEXT_REAL_OPEN"

trades["trade_id"] = [hashlib.sha256(f"{spec['version']}|{r.family}|{r.decision_at}|{r.direction}".encode()).hexdigest()[:24] for r in trades.itertuples()]
trades["notional_usd"] = 3000.0
trades["quantity_btc"] = 3000.0 / trades.entry_price
trades["planned_target_profit_usd"] = (trades.target_price - trades.entry_price).abs() * trades.quantity_btc
trades["holding_hours"] = (trades.exit_at - trades.entry_at).dt.total_seconds() / 3600
trades["net_R_sum_component"] = trades.net_R
trades.to_csv(OUT / "selected_trade_ledger_usd.csv", index=False)
core = trades.loc[trades.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
overall = metrics(trades)
six = metrics(core)
actual_targets = trades.loc[trades.exit_reason.eq("TARGET")]
assert overall["net_usd"] >= 500 and six["net_usd"] >= 500
summary = {"status": "HISTORICAL_CANDIDATE_MEETS_USER_MONETARY_BENCHMARK", "strategy": spec["version"],
           "full_history": overall, "six_month_entry_cohort": six,
           "six_month_entry_start": "2026-04-01T00:00:00Z", "six_month_entry_end_exclusive": "2026-10-01T00:00:00Z",
           "full_history_net_R_sum": float(trades.net_R.sum()), "six_month_net_R_sum": float(core.net_R.sum()),
           "mean_planned_target_R": float(trades.target_R.mean()),
           "mean_planned_target_profit_usd": float(trades.planned_target_profit_usd.mean()),
           "mean_initial_stop_risk_usd": float(trades.initial_risk_usd.mean()),
           "minimum_initial_stop_risk_usd": float(trades.initial_risk_usd.min()), "maximum_initial_stop_risk_usd": float(trades.initial_risk_usd.max()),
           "mean_holding_hours": float(trades.holding_hours.mean()), "actual_exit_counts": trades.exit_reason.value_counts().to_dict(),
           "actual_target_mean_net_usd": float(actual_targets.net_usd.mean()),
           "actual_target_mean_gross_usd": float(actual_targets.gross_usd.mean()),
           "actual_target_mean_R": float(actual_targets.target_R.mean()),
           "actual_target_mean_holding_hours": float(actual_targets.holding_hours.mean()),
           "net_win_rate": float(trades.net_usd.gt(0).mean()), "long_trades": int(trades.direction.eq(1).sum()), "short_trades": int(trades.direction.eq(-1).sum()),
           "isolated_omissions_in_trades": int(trades.omitted_minutes.sum()), "conservative_gap_marks_in_selected_result": 0,
           "historically_selected_after_parameter_search": True, "pristine_holdout": False,
           "borrow_cost_modelled": False, "execution_market": "BTCUSDT_FEED_PRICE_PROXY_USD_REPORTING",
           "commission_usd_per_round_trip": 5, "slippage_bps_per_fill": 2, "position_notional_usd": 3000,
           "source_code_identity_verified": True, "independent_money_and_first_touch_checks_passed": True,
           "real_feed_future_append_invariance_passed": True, "one_global_book_and_cooldown_verified": True,
           "seed_reproduction_exact": True, "no_live_or_production_promotion": True}
summary.update(full_regression_passed=762, full_regression_warnings=11, full_regression_seconds=56.75,
               full_regression_log_sha256=digest(OUT / "full_regression_20261014.txt"))
(OUT / "selected_result.json").write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n")
monthly = trades.assign(entry_month=trades.entry_at.dt.strftime("%Y-%m")).groupby("entry_month").agg(trades=("trade_id", "size"), gross_usd=("gross_usd", "sum"), commission_usd=("commission_usd", "sum"), slippage_usd=("slippage_usd", "sum"), net_usd=("net_usd", "sum")).reset_index()
monthly.to_csv(OUT / "selected_monthly_results.csv", index=False)
(OUT / "selected_artifact_hashes.json").write_text(json.dumps({name: digest(OUT / name) for name in ["selected_strategy.json", "selected_trade_ledger_usd.csv", "selected_result.json", "selected_monthly_results.csv", "result.md"]}, sort_keys=True, indent=2) + "\n")
print(json.dumps(summary, indent=2, allow_nan=False))
