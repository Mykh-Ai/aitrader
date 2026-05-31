import json

import pandas as pd

from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS, build_liquidity_map
from market_monitor.score_instrumentation import SCORE_INSTRUMENTATION_COLUMNS


def test_liquidity_map_includes_score_instrumentation_columns_and_valid_json():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 100.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 100.04),
            ]
        ),
        latest_close=90.0,
    )

    assert all(column in zones.columns for column in SCORE_INSTRUMENTATION_COLUMNS)
    assert all(column in LIQUIDITY_MAP_COLUMNS for column in SCORE_INSTRUMENTATION_COLUMNS)
    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])

    assert components["final_confidence_score"] == int(row["confidence_score"])
    assert components["confidence_tier"] == row["confidence_tier"]
    assert components["h1_component"] == 38
    assert components["h4_component"] == 55
    assert components["source_count_bonus"] == 8
    assert row["source_level_count"] == 2
    assert row["cluster_member_count"] == 2
    assert bool(row["has_h1_source"]) is True
    assert bool(row["has_h4_source"]) is True
    assert bool(row["has_session_source"]) is False
    assert row["zone_width"] == row["price_upper"] - row["price_lower"]
    assert row["zone_width_pct"] == row["zone_width"] / row["price_mid"] * 100
    assert row["score_components_json"] == json.dumps(
        components, sort_keys=True, separators=(",", ":")
    )


def test_confidence_score_and_tier_values_do_not_change_for_fixed_fixture():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "SESSION", "ASIA_HIGH", 100.0),
            _level("level_000002", "BUY_SIDE", "H1", "H1_SWING_HIGH", 200.0),
            _level("level_000003", "BUY_SIDE", "H4", "H4_SWING_HIGH", 300.0),
            _level("level_000004", "BUY_SIDE", "D1", "PDH", 400.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=50.0)
    scores = dict(zip(zones["source_level_ids"], zones["confidence_score"]))
    tiers = dict(zip(zones["source_level_ids"], zones["confidence_tier"]))

    assert scores == {
        "level_000001": 27,
        "level_000002": 65,
        "level_000003": 82,
        "level_000004": 57,
    }
    assert tiers == {
        "level_000001": "LOW",
        "level_000002": "MEDIUM",
        "level_000003": "HIGH",
        "level_000004": "MEDIUM",
    }


def test_equal_and_pdh_pdl_source_flags_are_set_from_level_type_evidence():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "CLUSTER", "EQUAL_HIGHS", 100.0),
                _level("level_000002", "SELL_SIDE", "D1", "PDL", 50.0),
            ]
        ),
        latest_close=75.0,
    )

    equal = zones[zones["zone_type"] == "EQUAL_HIGHS_ZONE"].iloc[0]
    pdl = zones[zones["zone_type"] == "PDL_ZONE"].iloc[0]
    assert bool(equal["has_equal_level_source"]) is True
    assert bool(pdl["has_pdh_pdl_source"]) is True


def _level(level_id, side, timeframe, level_type, price, quality="RAW"):
    return {
        "level_id": level_id,
        "created_at": "2026-05-07T00:00:00Z",
        "level_timestamp": "2026-05-07T00:00:00Z",
        "timeframe": timeframe,
        "level_type": level_type,
        "side": side,
        "price": price,
        "source_start": "2026-05-07T00:00:00Z",
        "source_end": "2026-05-07T00:00:00Z",
        "touch_count": 1,
        "strength_score": 65,
        "status": "ACTIVE",
        "data_quality": quality,
        "source_level_ids": "",
    }
