from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "SHI_RESET_40F_direction_expiry_stop_interventions_v0"
sys.path.insert(0, str(ENGINE))
from test_interventions import specimen
from interventions import intervention_path
from research.strategy_search.replay import ReplayData, ExitRules


def test_one_R_does_not_arm_two_R_protection():
    feed, bars = specimen()
    feed.loc[3, ["HiPrice", "LowPrice"]] = [100.4, 98.8]
    row = intervention_path(ReplayData(feed, bars), 0, -1, ExitRules(6, 1, 6, 0, 2), lock_trigger_r=2)
    assert not row["lock_armed"] and not row["lock_active"]
    assert row["exit_reason"] == "EXPIRY"


def test_two_R_trigger_keeps_quarter_R_stop_and_one_minute_latency():
    feed, bars = specimen()
    feed.loc[3, ["HiPrice", "LowPrice"]] = [100.4, 97.8]
    feed.loc[4, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [97.8, 97.9, 97.7, 97.8]
    feed.loc[5, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [99.6, 99.9, 99.5, 99.6]
    row = intervention_path(ReplayData(feed, bars), 0, -1, ExitRules(6, 1, 6, 0, 2), lock_trigger_r=2)
    assert row["stop_amendment_decision_at"] == feed.Timestamp.iloc[3]
    assert row["stop_amendment_active_at"] == feed.Timestamp.iloc[4]
    assert row["exit_reason"] == "LOCK_STOP" and row["exit_at"] == feed.Timestamp.iloc[5]
    risk = row["stop_price"] - row["entry_price"]
    assert row["exit_price"] == pytest.approx(row["entry_price"] - .25 * risk)
