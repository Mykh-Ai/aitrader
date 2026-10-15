import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
from research.strategy_search.replay import ExitRules, ReplayData, trade_path
from interventions import candidate_map, intervention_path


def specimen():
    ts = pd.date_range("2026-03-20T00:00:00Z", periods=241, freq="min")
    feed = pd.DataFrame({"Timestamp": ts, "OpenPrice": 100., "HiPrice": 100.1, "LowPrice": 99.9,
                         "ClosePrice": 100., "TotalQty": 1., "BuyQty": .5, "SellQty": .5,
                         "OpenInterest": 10., "DataQuality": "RAW", "IsRecovered": False, "IsSynthetic": 0})
    clock = pd.date_range(ts[0], periods=5, freq="h")
    bars = pd.DataFrame({"timestamp": clock, "available_at": clock, "open": 100., "high": 100.1,
                         "low": 99.9, "close": 100., "atr": .2, "usable": True, "context_usable": True,
                         "lower6": 99., "upper6": 101., "lower48": 99., "ema24": 100.})
    return feed, bars


@pytest.mark.parametrize("side", [1, -1])
def test_no_intervention_matches_existing_engine(side):
    feed, bars = specimen()
    data, rules = ReplayData(feed, bars), ExitRules(6, 1, 6, 0, 2)
    expected = trade_path(data, 0, side, rules, precise=True)
    actual = intervention_path(data, 0, side, rules)
    assert {k: actual[k] for k in expected} == expected


def test_reference_exit_uses_delayed_open_without_later_minute_low():
    feed, bars = specimen()
    bars.loc[1, "close"] = 99.8
    feed.loc[62, "LowPrice"] = 98.
    row = intervention_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 6, 0, 2), 3)
    assert row["exit_reason"] == "REFERENCE_INVALIDATION"
    assert row["exit_decision_at"] == bars.available_at.iloc[1]
    assert row["exit_at"] == feed.Timestamp.iloc[61]
    assert row["exit_price"] == feed.OpenPrice.iloc[62] == 100.
    assert row["net_usd"] == pytest.approx(-6.2)


def test_scheduled_exit_respects_protective_gap_at_open():
    feed, bars = specimen()
    bars.loc[1, "close"] = 99.8
    feed.loc[62, "OpenPrice"] = 98.
    row = intervention_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 6, 0, 2), 3)
    assert row["exit_reason"] == "STOP_GAP"
    assert row["exit_at"] == feed.Timestamp.iloc[61]
    assert row["exit_price"] == 98.


def test_lock_cannot_retroactively_stop_trigger_minute_and_has_latency():
    feed, bars = specimen()
    feed.loc[3, ["HiPrice", "LowPrice"]] = [100.4, 98.8]
    feed.loc[4, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [98.8, 98.9, 98.7, 98.8]
    feed.loc[5, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [99.6, 99.9, 99.5, 99.6]
    row = intervention_path(ReplayData(feed, bars), 0, -1, ExitRules(6, 1, 6, 0, 2), lock_trigger_r=1)
    assert row["exit_reason"] == "LOCK_STOP"
    assert row["stop_amendment_decision_at"] == feed.Timestamp.iloc[3]
    assert row["stop_amendment_active_at"] == feed.Timestamp.iloc[4]
    assert row["exit_at"] == feed.Timestamp.iloc[5]
    risk = row["stop_price"] - row["entry_price"]
    assert row["exit_price"] == pytest.approx(100 - .25 * risk)
    qty = 3000 / row["entry_price"]
    assert row["net_usd"] == pytest.approx((100 - row["exit_price"]) * qty - 5 - (100 + row["exit_price"]) * qty * .0002)


def test_original_stop_wins_over_lock_trigger_in_same_minute():
    feed, bars = specimen()
    feed.loc[3, ["HiPrice", "LowPrice"]] = [102., 98.8]
    row = intervention_path(ReplayData(feed, bars), 0, -1, ExitRules(6, 1, 6, 0, 2), lock_trigger_r=1)
    assert row["exit_reason"] == "STOP"
    assert not row["lock_armed"]
    assert row["exit_at"] == feed.Timestamp.iloc[3]


def test_isolated_omission_delays_scheduled_exit_without_compressing_clock():
    feed, bars = specimen()
    bars.loc[1, "close"] = 99.8
    feed = feed.drop(62).reset_index(drop=True)
    row = intervention_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 6, 0, 2), 3)
    assert row["exit_reason"] == "REFERENCE_INVALIDATION"
    assert row["omitted_minutes"] == 1
    assert row["exit_at"] == pd.Timestamp("2026-03-20T01:02:00Z")


def test_extended_gap_before_action_is_not_a_resolved_profit():
    feed, bars = specimen()
    bars.loc[1, "close"] = 99.8
    feed = feed.drop([61, 62, 63]).reset_index(drop=True)
    row = intervention_path(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 6, 0, 2), 3)
    assert row["censored"] and row["exit_reason"] == "CENSORED_DATA"
    assert row["net_usd"] is None


def test_space_gate_uses_known_close_independent_of_future_entry_open():
    feed, bars = specimen()
    spec = {"short": {"exit": {"stop_lookback": 6, "atr_floor": 1, "target_r": 6, "trail_atr": 0, "hold_hours": 2}}}
    original = np.array([-1, 0, 0, 0, 0])
    inventory = {0: [{"side": -1, "price": 99.3, "available_at": bars.available_at.iloc[0]}]}
    variant = {"short_space_1r": True}
    first, rejected1 = candidate_map(ReplayData(feed, bars), original, spec, variant, inventory)
    feed.loc[2, "OpenPrice"] = 200.
    second, rejected2 = candidate_map(ReplayData(feed, bars), original, spec, variant, inventory)
    assert first == second == {}
    assert rejected1 == rejected2 and rejected1[0]["reason"] == "OPPOSING_H4_WITHIN_1R"


def test_long_confirmation_has_new_decision_clock():
    feed, bars = specimen()
    bars.loc[1, "close"] = 100.2
    candidates, _ = candidate_map(ReplayData(feed, bars), np.array([1, 0, 0, 0, 0]), {}, {"long_confirm_1h": True}, {})
    assert list(candidates) == [1]
    assert candidates[1]["source_index"] == 0
    assert candidates[1]["decision_at"] == bars.available_at.iloc[1]
