import json

import pandas as pd

from market_monitor.liquidity_zones import (
    LIQUIDITY_MAP_COLUMNS,
    _confidence_tier,
    build_liquidity_map,
)
from market_monitor.score_instrumentation import SCORE_INSTRUMENTATION_COLUMNS


def test_liquidity_map_includes_score_instrumentation_columns_and_valid_json():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
            ]
        ),
        latest_close=65000.0,
    )

    assert all(column in zones.columns for column in SCORE_INSTRUMENTATION_COLUMNS)
    assert all(column in LIQUIDITY_MAP_COLUMNS for column in SCORE_INSTRUMENTATION_COLUMNS)
    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])

    assert components["final_confidence_score"] == int(row["confidence_score"])
    assert components["confidence_tier"] == row["confidence_tier"]
    assert components["h1_component"] == 24
    assert components["h4_component"] == 40
    assert components["timeframe_component_total"] == 64
    assert components["source_diversity_bonus"] == 0
    assert components["raw_source_count_bonus"] == 0
    assert components["source_count_bonus"] == 0
    assert components["width_penalty"] == 0
    assert components["precision_status"] == "PRECISE"
    assert components["hard_wide_zone_width_pct"] == 0.5
    assert row["source_level_count"] == 2
    assert row["source_ref_count"] == 2
    assert row["cluster_member_count"] == 2
    assert row["precision_status"] == "PRECISE"
    assert bool(row["has_h1_source"]) is True
    assert bool(row["has_h4_source"]) is True
    assert bool(row["has_session_source"]) is False
    assert row["zone_width"] == row["price_upper"] - row["price_lower"]
    assert row["zone_width_pct"] == row["zone_width"] / row["price_mid"] * 100
    assert row["score_components_json"] == json.dumps(
        components, sort_keys=True, separators=(",", ":")
    )


def test_confidence_score_and_tier_values_for_fixed_fixture_reflect_patch():
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
        "level_000001": 25,
        "level_000002": 25,
        "level_000003": 41,
        "level_000004": 46,
    }
    assert tiers == {
        "level_000001": "LOW",
        "level_000002": "LOW",
        "level_000003": "MEDIUM",
        "level_000004": "MEDIUM",
    }


def test_h4_h1_alone_is_medium_not_automatic_high():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
            ]
        ),
        latest_close=65000.0,
    )

    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])
    assert row["confidence_score"] == 66
    assert row["confidence_tier"] == "MEDIUM"
    assert components["h4_component"] + components["h1_component"] == 64
    assert components["source_diversity_bonus"] == 0
    assert components["width_penalty"] == 0


def test_compact_h4_h1_distinct_session_confluence_can_be_high():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
                _level("level_000003", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70040.0),
            ]
        ),
        latest_close=65000.0,
    )

    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])
    assert row["confidence_score"] == 77
    assert row["confidence_tier"] == "HIGH"
    assert components["session_component"] == 6
    assert components["source_diversity_bonus"] == 4


def test_session_only_zone_remains_low():
    zones = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70000.0)]),
        latest_close=65000.0,
    )

    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])
    assert row["confidence_score"] == 25
    assert row["confidence_tier"] == "LOW"
    assert components["session_component"] == 24


def test_raw_source_count_accumulation_alone_does_not_guarantee_high():
    levels = [
        _level(f"level_{idx:06d}", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70000.0 + idx * 20)
        for idx in range(1, 7)
    ]

    zones = build_liquidity_map(pd.DataFrame(levels), latest_close=65000.0)

    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])
    assert row["source_level_count"] == 6
    assert components["raw_source_count_bonus"] == 6
    assert row["confidence_score"] < 70
    assert row["confidence_tier"] == "LOW"


def test_source_diversity_is_rewarded_more_safely_than_raw_count():
    raw_count_zone = build_liquidity_map(
        pd.DataFrame(
            [
                _level(f"level_{idx:06d}", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70000.0 + idx * 20)
                for idx in range(1, 7)
            ]
        ),
        latest_close=65000.0,
    ).iloc[0]
    diverse_zone = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
                _level("level_000003", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70040.0),
            ]
        ),
        latest_close=65000.0,
    ).iloc[0]

    assert diverse_zone["confidence_score"] > raw_count_zone["confidence_score"]
    assert json.loads(diverse_zone["score_components_json"])["source_diversity_bonus"] > 0


def test_equal_level_bonus_does_not_double_count_same_source_ids():
    zones = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
                _level(
                    "level_000003",
                    "BUY_SIDE",
                    "CLUSTER",
                    "EQUAL_HIGHS",
                    70010.0,
                    source_level_ids="level_000001|level_000002",
                ),
            ]
        ),
        latest_close=65000.0,
    )

    row = zones.iloc[0]
    components = json.loads(row["score_components_json"])
    assert row["source_level_count"] == 2
    assert components["equal_level_component"] == 4
    assert components["raw_source_count_bonus"] == 0


def test_zone_width_penalty_buckets_are_visible():
    no_penalty = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70100.0),
            ]
        ),
        latest_close=65000.0,
    ).iloc[0]
    moderate_penalty = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70100.0),
                _level("level_000003", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70200.0),
            ]
        ),
        latest_close=65000.0,
    ).iloc[0]
    blocked_too_wide = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70100.0),
                _level("level_000003", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70200.0),
                _level("level_000004", "BUY_SIDE", "SESSION", "EUROPE_HIGH", 70300.0),
                _level("level_000005", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70400.0),
                _level("level_000006", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70500.0),
            ]
        ),
        latest_close=65000.0,
    )

    assert json.loads(no_penalty["score_components_json"])["width_penalty"] == 0
    assert no_penalty["precision_status"] == "PRECISE"
    assert json.loads(moderate_penalty["score_components_json"])["width_penalty"] == -6
    assert moderate_penalty["precision_status"] == "LOW_PRECISION"
    assert all(blocked_too_wide["zone_width_pct"] < 0.50)
    assert "TOO_WIDE" not in set(blocked_too_wide["precision_status"])


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


def test_confidence_tier_thresholds_are_unchanged():
    assert _confidence_tier(39) == "LOW"
    assert _confidence_tier(40) == "MEDIUM"
    assert _confidence_tier(69) == "MEDIUM"
    assert _confidence_tier(70) == "HIGH"


def _level(level_id, side, timeframe, level_type, price, quality="RAW", source_level_ids=""):
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
        "source_level_ids": source_level_ids,
    }
