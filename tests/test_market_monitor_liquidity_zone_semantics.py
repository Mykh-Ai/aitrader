from pathlib import Path

import pandas as pd

from market_monitor.config import BOUNDARY_STATEMENT
from market_monitor.liquidity_zones import (
    CROSSED_BY_LATEST_CLOSE_REASON,
    build_liquidity_map,
)
from market_monitor.summary import write_market_summary


def test_buy_side_zone_below_latest_close_is_invalidated_and_not_summarized(tmp_path: Path):
    levels = pd.DataFrame(
        [
            _level("level_below", "BUY_SIDE", "SESSION_HIGH", 80.0),
            _level("level_above", "BUY_SIDE", "SESSION_HIGH", 120.0),
        ]
    )
    zones = build_liquidity_map(levels, latest_close=101.0)

    behind_zone = zones[zones["source_level_ids"] == "level_below"].iloc[0]
    assert behind_zone["status"] == "INVALIDATED"
    assert behind_zone["invalidation_reason"] == CROSSED_BY_LATEST_CLOSE_REASON
    assert behind_zone["distance_from_close_pct"] < 0

    summary = _write_summary(tmp_path, zones, latest_close=101.0)
    assert "level_below" not in summary
    assert "zone_000001@80" not in summary
    assert "Nearest active buy-side liquidity zones: zone_000002@120 LOW" in summary
    assert "Touched/invalidated liquidity zones: touched=0, invalidated=1" in summary


def test_sell_side_zone_above_latest_close_is_invalidated_and_not_summarized(tmp_path: Path):
    levels = pd.DataFrame(
        [
            _level("level_below", "SELL_SIDE", "SESSION_LOW", 80.0),
            _level("level_above", "SELL_SIDE", "SESSION_LOW", 122.0),
        ]
    )
    zones = build_liquidity_map(levels, latest_close=101.0)

    behind_zone = zones[zones["source_level_ids"] == "level_above"].iloc[0]
    assert behind_zone["status"] == "INVALIDATED"
    assert behind_zone["invalidation_reason"] == CROSSED_BY_LATEST_CLOSE_REASON
    assert behind_zone["distance_from_close_pct"] > 0

    summary = _write_summary(tmp_path, zones, latest_close=101.0)
    assert "level_above" not in summary
    assert "zone_000002@122" not in summary
    assert "Nearest active sell-side liquidity zones: zone_000001@80 LOW" in summary
    assert "Touched/invalidated liquidity zones: touched=0, invalidated=1" in summary


def test_zone_containing_latest_close_is_touched():
    levels = pd.DataFrame([_level("level_touch", "BUY_SIDE", "SESSION_HIGH", 100.0)])

    zones = build_liquidity_map(levels, latest_close=100.0)

    assert zones.loc[0, "status"] == "TOUCHED"
    assert zones.loc[0, "invalidation_reason"] == ""
    assert zones.loc[0, "distance_from_close_pct"] == 0


def test_distance_from_close_pct_remains_signed_and_deterministic():
    levels = pd.DataFrame(
        [
            _level("level_above", "BUY_SIDE", "SESSION_HIGH", 110.0),
            _level("level_below", "SELL_SIDE", "SESSION_LOW", 90.0),
        ]
    )

    first = build_liquidity_map(levels, latest_close=100.0)
    second = build_liquidity_map(levels, latest_close=100.0)

    assert first["distance_from_close_pct"].tolist() == [10.0, -10.0]
    assert first["distance_from_close_pct"].tolist() == second[
        "distance_from_close_pct"
    ].tolist()


def _level(level_id: str, side: str, level_type: str, price: float) -> dict[str, object]:
    return {
        "level_id": level_id,
        "created_at": "2025-01-01T00:00:00Z",
        "level_timestamp": "2025-01-01T00:00:00Z",
        "timeframe": "SESSION",
        "level_type": level_type,
        "side": side,
        "price": price,
        "source_start": "2025-01-01T00:00:00Z",
        "source_end": "2025-01-01T00:00:00Z",
        "touch_count": 1,
        "strength_score": 55,
        "status": "ACTIVE",
        "data_quality": "RAW",
    }


def _write_summary(tmp_path: Path, zones: pd.DataFrame, latest_close: float) -> str:
    path = tmp_path / "market_summary.md"
    feed = pd.DataFrame(
        [
            {
                "ClosePrice": latest_close,
                "DataQuality": "RAW",
            }
        ]
    )
    write_market_summary(
        path,
        feed=feed,
        liquidity_map=zones,
        structure_levels=pd.DataFrame(index=[0, 1]),
        event_log=pd.DataFrame(),
        run_timestamp="2026-05-31T00:00:00Z",
        input_files=["synthetic.csv"],
        output_dir=tmp_path,
    )
    summary = path.read_text(encoding="utf-8")
    assert BOUNDARY_STATEMENT in summary
    return summary
