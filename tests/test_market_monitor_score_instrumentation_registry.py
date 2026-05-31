import json

import pandas as pd

from market_monitor.liquidity_zones import build_liquidity_map
from market_monitor.score_instrumentation import SCORE_INSTRUMENTATION_COLUMNS
from market_monitor.zone_registry import REGISTRY_COLUMNS, build_zone_registry


def test_registry_includes_score_instrumentation_columns():
    liquidity_map = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70000.0)]),
        latest_close=65000.0,
    )

    registry, _ = build_zone_registry(
        liquidity_map=liquidity_map,
        feed=_feed("2026-05-07", [65000, 65001]),
    )

    assert all(column in REGISTRY_COLUMNS for column in SCORE_INSTRUMENTATION_COLUMNS)
    assert all(column in registry.columns for column in SCORE_INSTRUMENTATION_COLUMNS)
    components = json.loads(registry.iloc[0]["score_components_json"])
    assert components["final_confidence_score"] == int(registry.iloc[0]["confidence_score"])
    assert components["precision_status"] == registry.iloc[0]["precision_status"]
    assert registry.iloc[0]["precision_status"] == "PRECISE"
    assert registry.iloc[0]["source_level_count"] == 1
    assert registry.iloc[0]["source_ref_count"] == 1
    assert registry.iloc[0]["zone_width"] == (
        registry.iloc[0]["price_upper"] - registry.iloc[0]["price_lower"]
    )


def test_registry_merge_instrumentation_exposes_prior_score_and_disciplined_fresh_bonus():
    prior = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70000.0)]),
        latest_close=65000.0,
    )
    registry_in, _ = build_zone_registry(
        liquidity_map=prior,
        feed=_feed("2026-05-07", [65000, 65001]),
    )
    current = build_liquidity_map(
        pd.DataFrame([_level("level_000002", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70020.0)]),
        latest_close=65000.0,
    )

    registry_out, _ = build_zone_registry(
        liquidity_map=current,
        feed=_feed("2026-05-08", [65000, 65001]),
        registry_in=registry_in,
    )

    active = registry_out[registry_out["status"] != "MERGED"].iloc[0]
    components = json.loads(active["score_components_json"])
    assert components["carry_forward_prior_score"] == 41
    assert components["bounded_prior_score"] == 41
    assert components["fresh_source_count"] == 1
    assert components["source_count_bonus"] == 3
    assert components["raw_source_count_bonus"] == 3
    assert components["source_diversity_bonus"] == 2
    assert components["h4_component"] == 2
    assert components["width_penalty"] == 0
    assert components["final_confidence_score"] == int(active["confidence_score"])
    assert active["confidence_score"] == 48
    assert active["confidence_tier"] == "MEDIUM"
    assert active["source_level_count"] == 2


def test_registry_merge_does_not_repeatedly_inflate_already_known_sources():
    first_day = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
            ]
        ),
        latest_close=65000.0,
    )
    registry_in, _ = build_zone_registry(
        liquidity_map=first_day,
        feed=_feed("2026-05-07", [65000, 65001]),
    )
    repeated = build_liquidity_map(
        pd.DataFrame(
            [
                _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
                _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
            ]
        ),
        latest_close=65000.0,
    )

    registry_out, _ = build_zone_registry(
        liquidity_map=repeated,
        feed=_feed("2026-05-08", [65000, 65001]),
        registry_in=registry_in,
    )

    active = registry_out[registry_out["status"] != "MERGED"].iloc[0]
    components = json.loads(active["score_components_json"])
    assert components["carry_forward_prior_score"] == 66
    assert components["fresh_source_count"] == 0
    assert components["source_count_bonus"] == 0
    assert components["raw_source_count_bonus"] == 0
    assert components["final_confidence_score"] == int(active["confidence_score"])
    assert active["confidence_score"] < 70


def _level(level_id, side, timeframe, level_type, price):
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
        "data_quality": "RAW",
        "source_level_ids": "",
    }


def _feed(day, closes):
    rows = []
    for index, close in enumerate(closes):
        rows.append(
            {
                "Timestamp": pd.Timestamp(f"{day}T00:0{index}:00Z"),
                "OpenPrice": close,
                "HiPrice": close,
                "LowPrice": close,
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
        )
    return pd.DataFrame(rows)
