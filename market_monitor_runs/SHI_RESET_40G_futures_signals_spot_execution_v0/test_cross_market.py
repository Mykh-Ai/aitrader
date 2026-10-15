from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "SHI_RESET_40F_direction_expiry_stop_interventions_v0"
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PRIOR))
from test_interventions import specimen
from research.strategy_search.replay import ReplayData, ExitRules, trade_path
from cross_market import execution_references, trade, portfolio, apply_long_regime


@pytest.mark.parametrize("side", [1, -1])
def test_fixed_engine_matches_original_without_management(side):
    feed, bars = specimen()
    data, rules = ReplayData(feed, bars), ExitRules(6, 1, 6, 0, 2)
    expected = trade_path(data, 0, side, rules, precise=True)
    actual = trade(data, 0, side, rules)
    assert {k: actual[k] for k in expected} == expected


def test_spot_entry_and_exit_use_spot_not_futures_prices():
    futures, bars = specimen()
    spot = futures.copy()
    spot[["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] *= 1.01
    spot.loc[3, "HiPrice"] = 104.
    execution, known = execution_references(futures, spot, bars)
    result = trade(ReplayData(spot, execution), 0, 1, ExitRules(6, 1, 2, 0, 2))
    assert result["entry_price"] == 101.
    assert known.basis_ratio.iloc[0] == pytest.approx(1.01)
    assert result["exit_reason"] == "TARGET" and result["exit_at"] == spot.Timestamp.iloc[3]
    original = trade(ReplayData(futures, bars), 0, 1, ExitRules(6, 1, 2, 0, 2))
    assert original["exit_reason"] == "EXPIRY"


def test_mapping_cannot_read_later_spot_quote():
    futures, bars = specimen()
    spot = futures.copy()
    baseline, known = execution_references(futures, spot, bars)
    spot.loc[60, "ClosePrice"] = 104.
    changed, other = execution_references(futures, spot, bars)
    pd.testing.assert_series_equal(baseline.iloc[0], changed.iloc[0])
    assert known.basis_ratio.iloc[0] == other.basis_ratio.iloc[0] == 1.
    assert other.basis_ratio.iloc[1] == 1.04


def test_missing_close_uses_previous_known_minute_not_next_close():
    futures, bars = specimen()
    spot = futures.drop(60).copy()
    spot.loc[61, "ClosePrice"] = 500.
    _, known = execution_references(futures, spot, bars)
    assert known.spot_close_at.iloc[1] == pd.Timestamp("2026-03-20T00:59:00Z")
    assert known.basis_ratio.iloc[1] == 1.


def test_half_2R_then_original_stop_has_weighted_money_and_one_fee():
    feed, bars = specimen()
    feed.loc[3, "HiPrice"] = 103.
    feed.loc[4, "LowPrice"] = 98.
    row = trade(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 10, 0, 2), "PARTIAL_HALF_2R")
    assert row["partial_filled"] and row["exit_reason"] == "STOP"
    assert row["commission_usd"] == 5
    assert row["gross_usd"] == pytest.approx(15.7425)
    assert row["net_usd"] == pytest.approx(9.5393515)
    assert [x["fraction"] for x in json.loads(row["fills_json"])] == [.5, .5]


def test_stop_wins_ambiguous_partial_minute():
    feed, bars = specimen()
    feed.loc[3, ["HiPrice", "LowPrice"]] = [103., 98.]
    row = trade(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 10, 0, 2), "PARTIAL_HALF_2R")
    assert row["exit_reason"] == "STOP" and not row["partial_filled"]
    assert len(json.loads(row["fills_json"])) == 1


def test_partial_position_does_not_release_global_book():
    feed, bars = specimen()
    feed.loc[3, "HiPrice"] = 103.
    exits = {"stop_lookback": 6, "atr_floor": 1, "target_r": 10, "trail_atr": 0, "hold_hours": 2}
    spec = {"long": {"family": "TREND_RETEST", "exit": exits}, "short": {"family": "ACCEPTED_BREAK", "exit": exits}}
    result = portfolio(ReplayData(feed, bars), np.array([1, -1, 0, 0, 0]), spec, "PARTIAL_HALF_2R")
    assert len(result) == 1 and result.partial_filled.iloc[0]


def trailing_specimen(gap=False):
    feed, bars = specimen()
    bars["confirmed_swing_low"] = 98.
    bars.loc[1, ["close", "confirmed_swing_low"]] = [104., 100.5]
    feed.loc[3, "HiPrice"] = 103.
    feed.loc[60, ["HiPrice", "ClosePrice"]] = [104.1, 104.]
    feed.loc[61, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [104., 104.1, 100., 104.]
    feed.loc[62, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [99. if gap else 104., 104.1, 98.9 if gap else 100., 104.]
    return feed, bars


def test_structural_trail_waits_for_confirmation_and_latency():
    feed, bars = trailing_specimen()
    row = trade(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 10, 0, 2), "TRAIL_H1_AFTER_2R")
    assert row["exit_reason"] == "TRAIL_STOP"
    assert row["exit_at"] == feed.Timestamp.iloc[62]
    assert row["exit_price"] == pytest.approx(100.5 * .9995)
    amendment = json.loads(row["amendments_json"])[0]
    assert amendment["decision_at"] == feed.Timestamp.iloc[60].value
    assert amendment["active_at"] == feed.Timestamp.iloc[61].value


def test_trail_adverse_gap_fills_open_not_unavailable_stop():
    feed, bars = trailing_specimen(gap=True)
    row = trade(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 10, 0, 2), "TRAIL_H1_AFTER_2R")
    assert row["exit_reason"] == "TRAIL_STOP_GAP" and row["exit_price"] == 99.


def test_trail_rejects_stop_above_current_spot_close_even_if_h1_close_was_higher():
    feed, bars = trailing_specimen()
    feed.loc[60, "ClosePrice"] = 100.
    row = trade(ReplayData(feed, bars), 0, 1, ExitRules(6, 1, 10, 0, 2), "TRAIL_H1_AFTER_2R")
    assert json.loads(row["amendments_json"]) == []


def test_h4_filter_changes_longs_only():
    directions = np.array([1, 1, -1, 1])
    regimes = pd.DataFrame({"h4_regime": ["UP", "DOWN", "DOWN", "MIXED"]})
    np.testing.assert_array_equal(apply_long_regime(directions, regimes, "NO_DOWN"), [1, 0, -1, 1])
    np.testing.assert_array_equal(apply_long_regime(directions, regimes, "UP_ONLY"), [1, 0, -1, 0])
