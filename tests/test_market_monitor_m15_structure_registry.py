import pandas as pd
import pytest

from market_monitor.events import EVENT_LOG_COLUMNS
from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS, build_liquidity_map
from market_monitor.structure import (
    STRUCTURE_LEVEL_COLUMNS,
    aggregate_timeframe,
    build_structure_levels,
)
from market_monitor.visual_overlay import (
    _htf_structural_levels,
    _local_session_zones,
    _m15_structure_zones,
    _m1_local_zones,
)
from market_monitor.zone_registry import (
    REGISTRY_COLUMNS,
    build_zone_registry,
    forward_liquidity_from_registry,
    local_session_context_role,
)


def test_m1_is_feed_only_and_m15_creates_first_class_structure_rows():
    feed = _m15_swing_feed()

    with pytest.raises(ValueError, match="Unsupported timeframe: M1"):
        aggregate_timeframe(feed, "M1")

    levels = build_structure_levels(feed)
    m15_high = levels[levels["level_type"] == "M15_SWING_HIGH"].iloc[0]

    assert "M1" not in set(levels["timeframe"])
    assert m15_high["timeframe"] == "M15"
    assert m15_high["source_timeframe_primary"] == "M15"
    assert m15_high["side"] == "BUY_SIDE"
    assert m15_high["price"] == 65500.0
    assert m15_high["level_timestamp"] == "2026-05-07T00:30:00Z"
    assert m15_high["created_at"] == "2026-05-07T01:00:00Z"
    assert m15_high["htf_level_type"] == ""
    assert m15_high["htf_origin_timestamp"] == ""
    assert m15_high["htf_origin_price"] == ""
    assert m15_high["htf_confirmation_timestamp"] == ""


def test_m15_zones_persist_through_registry_as_minimum_structure():
    feed = _m15_swing_feed()
    levels = build_structure_levels(feed)
    zones = build_liquidity_map(levels, latest_close=64000)
    m15_zone = zones[zones["source_timeframe_primary"] == "M15"].iloc[0]

    assert m15_zone["zone_type"] == "M15_SWING_HIGH_ZONE"
    assert m15_zone["sweep_importance_class"] == "M15_MINIMUM_STRUCTURE_LEVEL"
    assert m15_zone["active_forward_role"] == "M15_MINIMUM_STRUCTURE"
    assert m15_zone["htf_lifecycle_status"] == "M15_ACTIVE"
    assert m15_zone["htf_level_type"] == ""

    registry, _ = build_zone_registry(liquidity_map=zones, feed=feed)
    row = registry[registry["source_timeframe_primary"] == "M15"].iloc[0]
    forward = forward_liquidity_from_registry(registry, latest_close=64000)

    assert row["source_timeframes"] == "M15"
    assert row["zone_type"] == "M15_SWING_HIGH_ZONE"
    assert row["sweep_importance_class"] == "M15_MINIMUM_STRUCTURE_LEVEL"
    assert row["active_forward_role"] == "M15_MINIMUM_STRUCTURE"
    assert row["active_forward"] == "true"
    assert row["htf_lifecycle_status"] == "M15_ACTIVE"
    assert row["htf_sweep_count"] == 0
    assert row["htf_close_through_count"] == 0
    assert row["htf_acceptance_count"] == 0
    assert local_session_context_role(row) == ""
    assert row["active_forward_role"] != "FRESH_LIQUIDITY"
    assert not str(row["sweep_importance_class"]).startswith("HTF_STRUCTURAL")
    assert not str(row["sweep_importance_class"]).startswith("LOCAL_SESSION")

    forward_row = forward[forward["source_timeframe_primary"] == "M15"].iloc[0]
    assert forward_row["active_forward_role"] == "M15_MINIMUM_STRUCTURE"
    assert forward_row["sweep_importance_class"] == "M15_MINIMUM_STRUCTURE_LEVEL"


def test_m15_is_not_merged_into_nearby_h1_or_session_zones():
    levels = pd.DataFrame(
        [
            _level("level_h1", "H1", "H1_SWING_HIGH", "BUY_SIDE", 112.0),
            _level("level_m15", "M15", "M15_SWING_HIGH", "BUY_SIDE", 112.5),
            _level("level_session", "SESSION", "ASIA_HIGH", "BUY_SIDE", 113.0),
        ],
        columns=STRUCTURE_LEVEL_COLUMNS,
    )

    zones = build_liquidity_map(levels, latest_close=90)

    assert len(zones[zones["source_timeframe_primary"] == "M15"]) == 1
    assert len(zones[zones["source_timeframe_primary"] == "H1"]) == 1
    assert "M15" not in zones[zones["source_timeframe_primary"] == "H1"].iloc[0]["source_timeframes"]


def test_visual_overlay_routes_m15_to_own_bucket():
    zones = pd.DataFrame(
        [
            _registry_zone("zone_h4", "H4", "H4_SWING_LOW_ZONE", "HTF_STRUCTURAL_LEVEL", "FRESH_LIQUIDITY", "HTF_ACTIVE"),
            _registry_zone(
                "zone_m15",
                "M15",
                "M15_SWING_HIGH_ZONE",
                "M15_MINIMUM_STRUCTURE_LEVEL",
                "M15_MINIMUM_STRUCTURE",
                "M15_ACTIVE",
            ),
            _registry_zone("zone_session", "SESSION", "ASIA_HIGH_ZONE", "LOCAL_SESSION_ZONE", "LOCAL_SESSION_CONTEXT", "LOCAL_ONLY"),
            _registry_zone("zone_m1", "LOCAL", "LOCAL_ONLY_ZONE", "M1_LOCAL_ZONE", "AUDIT_ONLY", "LOCAL_ONLY"),
        ]
    )

    assert _htf_structural_levels(zones)["zone_id"].tolist() == ["zone_h4"]
    assert _m15_structure_zones(zones)["zone_id"].tolist() == ["zone_m15"]
    assert _local_session_zones(zones)["zone_id"].tolist() == ["zone_session"]
    assert _m1_local_zones(zones)["zone_id"].tolist() == ["zone_m1"]


def test_m15_contracts_do_not_add_trading_fields():
    forbidden = {"signal", "order", "entry", "exit", "pnl"}
    for columns in [STRUCTURE_LEVEL_COLUMNS, LIQUIDITY_MAP_COLUMNS, REGISTRY_COLUMNS, EVENT_LOG_COLUMNS]:
        lowered = {column.lower() for column in columns}
        assert forbidden.isdisjoint(lowered)


def _m15_swing_feed() -> pd.DataFrame:
    highs = [65000, 65100, 65500, 65200, 65150]
    lows = [63800, 63900, 64000, 64100, 64200]
    rows = []
    for index, (high, low) in enumerate(zip(highs, lows)):
        rows.append(
            {
                "Timestamp": pd.Timestamp("2026-05-07T00:00:00Z") + pd.Timedelta(minutes=15 * index),
                "OpenPrice": 64000,
                "HiPrice": high,
                "LowPrice": low,
                "ClosePrice": 64000,
                "TotalQty": 10,
                "Trades": 1,
                "BuyQty": 5,
                "SellQty": 5,
                "OpenInterest": 1000,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceFile": "synthetic.csv",
            }
        )
    return pd.DataFrame(rows)


def _level(
    level_id: str,
    timeframe: str,
    level_type: str,
    side: str,
    price: float,
) -> dict[str, object]:
    is_htf = timeframe in {"H1", "H4"}
    return {
        "level_id": level_id,
        "created_at": "2026-05-07T01:00:00Z",
        "level_timestamp": "2026-05-07T00:30:00Z",
        "timeframe": timeframe,
        "level_type": level_type,
        "source_timeframe_primary": timeframe,
        "side": side,
        "price": price,
        "htf_level_type": level_type if is_htf else "",
        "htf_origin_timestamp": "2026-05-07T00:30:00Z" if is_htf else "",
        "htf_origin_price": price if is_htf else "",
        "htf_confirmation_timestamp": "2026-05-07T01:00:00Z" if is_htf else "",
        "source_start": "2026-05-07T00:30:00Z",
        "source_end": "2026-05-07T00:44:00Z",
        "touch_count": 1,
        "strength_score": 65,
        "status": "ACTIVE",
        "data_quality": "RAW",
        "source_level_ids": "",
    }


def _registry_zone(
    zone_id: str,
    source_timeframe: str,
    zone_type: str,
    sweep_class: str,
    active_role: str,
    lifecycle: str,
) -> dict[str, object]:
    htf = source_timeframe in {"H1", "H4"}
    return {
        "zone_id": zone_id,
        "source_timeframe_primary": source_timeframe,
        "source_timeframes": source_timeframe,
        "zone_type": zone_type,
        "htf_level_type": "H4_SWING_LOW" if htf else "",
        "sweep_importance_class": sweep_class,
        "active_forward_role": active_role,
        "htf_lifecycle_status": lifecycle,
        "structural_zone_mode": "THIN_LEVEL",
    }
