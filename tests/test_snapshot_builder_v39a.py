from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.snapshot_builder_v39a import (
    LOCAL_WINDOWS_MINUTES,
    STATE_SCHEMA_VERSION,
    build_market_monitor_snapshot_v39a,
)


def _feed(periods: int = 2_880) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01T00:00:00Z", periods=periods, freq="min")
    close = 100_000.0 + pd.Series(range(periods), dtype=float) * 0.5
    return pd.DataFrame(
        {
            "Timestamp": timestamps,
            "OpenPrice": close,
            "HiPrice": close + 10.0,
            "LowPrice": close - 10.0,
            "ClosePrice": close + 1.0,
            "TotalQty": 100.0,
            "Trades": 10,
            "BuyQty": 60.0,
            "SellQty": 40.0,
            "OpenInterest": 10_000.0,
            "FundingRate": 0.00001,
            "DataQuality": "RAW",
            "SourceFile": "fixture.csv",
        }
    )


def test_exact_closed_windows_exclude_future_rows(tmp_path: Path) -> None:
    snapshot = build_market_monitor_snapshot_v39a(
        _feed(),
        cutoff_ts="2026-01-02T00:04:00Z",
        state_path=tmp_path / "state.json",
    )

    assert tuple(int(key) for key in snapshot["windows"]) == LOCAL_WINDOWS_MINUTES
    assert all(snapshot["windows"][str(minutes)]["rows_used"] == minutes for minutes in LOCAL_WINDOWS_MINUTES)
    assert snapshot["quality"]["future_rows_excluded"] == 1_435


def test_state_carries_across_utc_midnight(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    build_market_monitor_snapshot_v39a(
        _feed(), cutoff_ts="2026-01-01T23:59:00Z", state_path=state_path, persist_state=True
    )
    snapshot = build_market_monitor_snapshot_v39a(
        _feed(), cutoff_ts="2026-01-02T00:04:00Z", state_path=state_path, persist_state=True
    )

    assert snapshot["state_memory"]["continuity"] == "CONTINUOUS_CARRY_FORWARD"
    assert snapshot["state_memory"]["daily_boundary"]["state_carried_across_boundary"] is True
    assert json.loads(state_path.read_text(encoding="utf-8"))["state_schema_version"] == STATE_SCHEMA_VERSION


def test_recovered_rows_remain_explicit(tmp_path: Path) -> None:
    frame = _feed()
    frame.loc[frame["Timestamp"] >= pd.Timestamp("2026-01-02T00:00:00Z"), "DataQuality"] = "RECOVERED_DEGRADED"
    snapshot = build_market_monitor_snapshot_v39a(
        frame, cutoff_ts="2026-01-02T00:04:00Z", state_path=tmp_path / "state.json"
    )

    assert snapshot["quality"]["readiness"] == "READY_WITH_RECOVERED_DATA"
    assert snapshot["windows"]["5"]["status"] == "COMPLETE_RECOVERED_DEGRADED"
