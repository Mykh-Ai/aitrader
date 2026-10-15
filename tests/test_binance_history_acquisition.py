"""Research-only data partition and acquisition contract checks; no replay."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest


PATH = Path(__file__).resolve().parents[1] / "market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/acquire_history.py"
spec = importlib.util.spec_from_file_location("binance_history_acquisition_test", PATH)
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


def test_declared_archive_plan_includes_warmup_and_label_boundary():
    plan = history.archive_plan()
    assert len(plan) == 23
    assert plan[0] == {"date": "2025-01-31", "cadence": "daily", "role": "LEFT_BOUNDARY_MINUTE"}
    assert [row["date"] for row in plan if row["cadence"] == "monthly"] == [
        ts.strftime("%Y-%m") for ts in pd.date_range("2025-02-01", "2026-02-01", freq="MS")]
    assert plan[-1]["date"] == "2026-03-09"
    assert len({row["date"] for row in plan}) == len(plan)


def test_warmup_and_right_close_endpoints_are_distinct_from_scored_data():
    times = pd.to_datetime(["2025-01-31T23:59Z", "2025-02-01T00:00Z", "2025-02-28T23:59Z",
                            "2025-03-01T00:00Z", "2026-03-09T23:59Z", "2026-03-10T00:00Z"], utc=True)
    result = history.partition(pd.DataFrame({"Timestamp": times}))
    assert result.Timestamp.tolist() == times[1:5].tolist()
    assert result.HistoryRole.tolist() == ["WARMUP_ONLY", "WARMUP_ONLY",
                                          "HISTORICAL_EVALUATION_SOURCE", "HISTORICAL_EVALUATION_SOURCE"]


def test_grid_rejects_single_missing_or_duplicate_minute():
    full = pd.DataFrame({"Timestamp": pd.date_range(history.DATA_START, history.DATA_END, freq="min")})
    assert history.check_grid(full) == len(full)
    with pytest.raises(AssertionError, match="MISSING_MINUTES"):
        history.check_grid(full.drop(index=100))
    duplicate = pd.concat([full.iloc[:100], full.iloc[[99]], full.iloc[100:]], ignore_index=True)
    with pytest.raises(AssertionError, match="DUPLICATE_MINUTES"):
        history.check_grid(duplicate)
