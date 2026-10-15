import numpy as np
import pandas as pd

from research.strategy_search.features import features
from research.strategy_search.replay import ExitRules, ReplayData, trade_path
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid


def specimen():
    ts = pd.date_range("2026-03-20T00:00:00Z", periods=181, freq="min")
    feed = pd.DataFrame({"Timestamp": ts, "OpenPrice": 100.0, "HiPrice": 100.1, "LowPrice": 99.9,
                         "ClosePrice": 100.0, "TotalQty": 1.0, "BuyQty": 0.5, "SellQty": 0.5,
                         "OpenInterest": 10.0, "LiqBuyQty": 0.0, "LiqSellQty": 0.0,
                         "DataQuality": "RAW", "IsRecovered": False, "IsSynthetic": 0})
    clock = pd.date_range(ts[0], periods=4, freq="h")
    bars = pd.DataFrame({"timestamp": clock, "available_at": clock, "open": 100.0,
                         "high": 100.1, "low": 99.9, "close": 100.0, "atr": 0.2,
                         "usable": True, "lower6": 99.0, "upper6": 101.0})
    return feed, bars


def test_minute_chronology_target_before_later_stop_and_dollar_costs():
    feed, bars = specimen()
    feed.loc[3, "HiPrice"] = 103.0
    feed.loc[4, "LowPrice"] = 98.0
    bars.loc[1, ["high", "low"]] = [103.0, 98.0]
    data = ReplayData(feed, bars)
    rules = ExitRules(6, 1, 2, 0, 1)
    coarse = trade_path(data, 0, 1, rules)
    exact = trade_path(data, 0, 1, rules, precise=True)
    assert coarse["exit_reason"] == "STOP"
    assert exact["exit_reason"] == "TARGET"
    assert exact["entry_at"] == pd.Timestamp("2026-03-20T00:01:00Z")
    assert exact["exit_at"] == pd.Timestamp("2026-03-20T00:03:00Z")
    assert exact["commission_usd"] == 5
    assert exact["initial_risk_usd"] == (100 - 99 * 0.9995) * 30
    np.testing.assert_allclose(exact["net_usd"], exact["gross_usd"] - 5 - exact["slippage_usd"])


def test_risk_is_structural_and_different_for_each_trade():
    feed, bars = specimen()
    rules = ExitRules(6, 1, 2, 0, 1)
    first = trade_path(ReplayData(feed, bars), 0, 1, rules, precise=True)
    bars.loc[1, "lower6"] = 98.0
    second = trade_path(ReplayData(feed, bars), 1, 1, rules, precise=True)
    assert second["initial_risk_usd"] > first["initial_risk_usd"]
    assert first["commission_usd"] == second["commission_usd"] == 5


def test_one_synthetic_minute_does_not_end_trade():
    feed, bars = specimen()
    feed.loc[3, "IsSynthetic"] = 1
    feed.loc[3, "HiPrice"] = 9999
    feed.loc[4, "HiPrice"] = 103
    exact = trade_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 2, 0, 1), precise=True)
    assert exact["exit_reason"] == "TARGET"
    assert exact["exit_at"] == feed.Timestamp.iloc[4]
    assert exact["omitted_minutes"] == 1


def test_entry_after_isolated_omission_preserves_actual_time():
    feed, bars = specimen()
    feed = feed.drop(2).reset_index(drop=True)
    exact = trade_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 2, 0, 1), precise=True)
    assert exact["entry_at"] == pd.Timestamp("2026-03-20T00:02:00Z")


def test_closed_features_are_invariant_to_appending_future():
    feed, bars = specimen()
    prefix = features(feed)
    extra = feed.iloc[-60:].copy()
    extra.Timestamp += pd.Timedelta(hours=1)
    extra.HiPrice = 9999.0
    extended = features(pd.concat([feed, extra], ignore_index=True))
    extended = extended.loc[extended.available_at <= feed.Timestamp.iloc[-1]].reset_index(drop=True)
    pd.testing.assert_frame_equal(prefix, extended)


def test_missing_expiry_minute_cannot_capture_a_later_target():
    feed, bars = specimen()
    feed = feed.loc[feed.Timestamp.ne(pd.Timestamp("2026-03-20T01:01:00Z"))].copy().reset_index(drop=True)
    feed.loc[feed.Timestamp.eq(pd.Timestamp("2026-03-20T01:02:00Z")), "HiPrice"] = 103
    exact = trade_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 2, 0, 1), precise=True)
    assert exact["exit_reason"] == "EXPIRY_NEXT_REAL_OPEN"
    assert exact["exit_price"] == 100


def test_three_minute_primary_gap_is_a_labelled_loss_scenario():
    feed, bars = specimen()
    feed.loc[3:5, "IsSynthetic"] = 1
    data = ReplayData(feed, bars)
    rules = ExitRules(6, 1, 2, 0, 1)
    strict = trade_path(data, 0, 1, rules, precise=True)
    stressed = trade_path(data, 0, 1, rules, precise=True, gap_policy="STOP_BOUND_PRIMARY_SHORT_GAP")
    assert strict["censored"]
    assert stressed["exit_reason"] == "CONSERVATIVE_SHORT_GAP_STOP_BOUND"
    assert stressed["short_gap_conservative_mark"]
    assert stressed["exit_price"] == stressed["stop_price"]
    assert stressed["net_usd"] < -stressed["initial_risk_usd"]
    assert stressed["omitted_minutes"] == 3


def test_recovered_gap_is_not_promoted_into_a_resolved_trade():
    feed, bars = specimen()
    feed.loc[3, "DataQuality"] = "RECOVERED_DEGRADED"
    feed.loc[3, "IsRecovered"] = True
    stressed = trade_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 2, 0, 1), precise=True, gap_policy="STOP_BOUND_PRIMARY_SHORT_GAP")
    assert stressed["censored"]
    assert not stressed["short_gap_conservative_mark"]


def test_hybrid_conflicting_families_skip_without_outcome_selection(monkeypatch):
    _, bars = specimen()
    bars["ema24"] = 100.0
    def fake_signals(bars, family, *rest):
        return np.array([1, 1, 0, 0]) if family == "TREND_RETEST" else np.array([0, -1, -1, 0])
    monkeypatch.setattr("research.strategy_search.hybrid.signals", fake_signals)
    long = {"family": "TREND_RETEST", "lookback": 96, "flow": .04, "volume": 1.3, "trend": "EMA", "maturity": 1.5, "impulse": 2}
    short = {"family": "ACCEPTED_BREAK", "lookback": 48, "flow": 0, "volume": 1.3, "trend": "PRESSURE"}
    np.testing.assert_array_equal(hybrid_signals(bars, long, short), [1, 0, -1, 0])


def test_hybrid_uses_one_global_position_not_independent_family_books():
    feed, bars = specimen()
    exits = {"stop_lookback": 6, "atr_floor": 1, "target_r": 2, "trail_atr": 0, "hold_hours": 2}
    long, short = {"family": "TREND_RETEST", "exit": exits}, {"family": "ACCEPTED_BREAK", "exit": exits}
    ledger = replay_hybrid(ReplayData(feed, bars), np.array([1, -1, -1, 0]), long, short)
    assert len(ledger) == 1
    assert ledger.family.iloc[0] == "TREND_RETEST"
    assert ledger.exit_reason.iloc[0] == "EXPIRY"
