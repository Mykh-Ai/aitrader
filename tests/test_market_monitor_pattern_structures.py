import pandas as pd

from market_monitor.liquidity_zones import build_liquidity_map
from market_monitor.pattern_structures import (
    PATTERN_STRUCTURES_COLUMNS,
    build_pattern_structures,
)
from market_monitor.zone_registry import build_zone_registry


def test_double_top_creates_pattern_derived_liquidity_zone():
    levels = _levels("BUY_SIDE")
    liquidity_map = build_liquidity_map(levels, latest_close=90)

    assert "DOUBLE_TOP_LIQUIDITY_ZONE" in liquidity_map["zone_type"].tolist()

    registry, _ = build_zone_registry(liquidity_map=liquidity_map, feed=_feed())
    patterns = build_pattern_structures(levels, registry)
    double_top = patterns[patterns["pattern_type"] == "DOUBLE_TOP"].iloc[0]

    assert patterns.columns.tolist() == PATTERN_STRUCTURES_COLUMNS
    assert double_top["linked_zone_id"]
    assert double_top["pattern_role"] == "BUY_SIDE_LIQUIDITY"


def test_double_bottom_creates_pattern_derived_liquidity_zone():
    levels = _levels("SELL_SIDE")
    liquidity_map = build_liquidity_map(levels, latest_close=130)

    assert "DOUBLE_BOTTOM_LIQUIDITY_ZONE" in liquidity_map["zone_type"].tolist()

    registry, _ = build_zone_registry(liquidity_map=liquidity_map, feed=_feed(close=130))
    patterns = build_pattern_structures(levels, registry)
    double_bottom = patterns[patterns["pattern_type"] == "DOUBLE_BOTTOM"].iloc[0]

    assert double_bottom["linked_zone_id"]
    assert double_bottom["pattern_role"] == "SELL_SIDE_LIQUIDITY"


def test_head_and_shoulders_scaffold_does_not_emit_active_false_positive():
    levels = pd.DataFrame(
        [
            _level("level_000001", "H1_SWING_HIGH", "BUY_SIDE", "2026-05-08T00:00:00Z", 100),
            _level("level_000002", "H1_SWING_HIGH", "BUY_SIDE", "2026-05-08T02:00:00Z", 120),
            _level("level_000003", "H1_SWING_HIGH", "BUY_SIDE", "2026-05-08T04:00:00Z", 101),
        ]
    )

    patterns = build_pattern_structures(levels)

    assert not set(patterns["pattern_type"]) & {"HEAD_AND_SHOULDERS", "INVERSE_HEAD_AND_SHOULDERS"}


def test_pattern_created_at_is_after_second_source_confirmation():
    levels = _levels("BUY_SIDE")

    patterns = build_pattern_structures(levels)
    double_top = patterns[patterns["pattern_type"] == "DOUBLE_TOP"].iloc[0]

    assert pd.Timestamp(double_top["created_at"]) >= pd.Timestamp("2026-05-08T02:00:00Z")


def _levels(side: str) -> pd.DataFrame:
    if side == "BUY_SIDE":
        rows = [
            _level("level_000001", "H1_SWING_HIGH", "BUY_SIDE", "2026-05-08T00:00:00Z", 100),
            _level("level_000002", "H1_SWING_HIGH", "BUY_SIDE", "2026-05-08T02:00:00Z", 100.03),
            _level(
                "level_000003",
                "EQUAL_HIGHS",
                "BUY_SIDE",
                "2026-05-08T02:00:00Z",
                100.015,
                source_level_ids="level_000001|level_000002",
            ),
            _level(
                "level_000004",
                "DOUBLE_TOP_HIGH",
                "BUY_SIDE",
                "2026-05-08T02:00:00Z",
                100.015,
                source_level_ids="level_000001|level_000002",
            ),
        ]
    else:
        rows = [
            _level("level_000001", "H1_SWING_LOW", "SELL_SIDE", "2026-05-08T00:00:00Z", 100),
            _level("level_000002", "H1_SWING_LOW", "SELL_SIDE", "2026-05-08T02:00:00Z", 99.98),
            _level(
                "level_000003",
                "EQUAL_LOWS",
                "SELL_SIDE",
                "2026-05-08T02:00:00Z",
                99.99,
                source_level_ids="level_000001|level_000002",
            ),
            _level(
                "level_000004",
                "DOUBLE_BOTTOM_LOW",
                "SELL_SIDE",
                "2026-05-08T02:00:00Z",
                99.99,
                source_level_ids="level_000001|level_000002",
            ),
        ]
    return pd.DataFrame(rows)


def _level(level_id, level_type, side, created_at, price, *, source_level_ids=""):
    return {
        "level_id": level_id,
        "created_at": created_at,
        "level_timestamp": created_at,
        "timeframe": "H1" if level_type.startswith("H1") else "PATTERN",
        "level_type": level_type,
        "side": side,
        "price": price,
        "source_start": created_at,
        "source_end": created_at,
        "touch_count": 2,
        "strength_score": 80,
        "status": "ACTIVE",
        "data_quality": "RAW",
        "source_level_ids": source_level_ids,
    }


def _feed(close=90):
    return pd.DataFrame(
        [
            {
                "Timestamp": pd.Timestamp("2026-05-08T03:00:00Z"),
                "OpenPrice": close,
                "HiPrice": close + 1,
                "LowPrice": close - 1,
                "ClosePrice": close,
                "TotalQty": 10,
                "Trades": 1,
                "BuyQty": 5,
                "SellQty": 5,
                "OpenInterest": 1000,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceFile": "synthetic.csv",
            }
        ]
    )
