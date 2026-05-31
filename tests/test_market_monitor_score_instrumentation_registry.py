import json

import pandas as pd

from market_monitor.liquidity_zones import build_liquidity_map
from market_monitor.score_instrumentation import SCORE_INSTRUMENTATION_COLUMNS
from market_monitor.zone_registry import REGISTRY_COLUMNS, build_zone_registry


def test_registry_includes_score_instrumentation_columns():
    liquidity_map = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "H4", "H4_SWING_HIGH", 100.0)]),
        latest_close=90.0,
    )

    registry, _ = build_zone_registry(
        liquidity_map=liquidity_map,
        feed=_feed("2026-05-07", [90, 91]),
    )

    assert all(column in REGISTRY_COLUMNS for column in SCORE_INSTRUMENTATION_COLUMNS)
    assert all(column in registry.columns for column in SCORE_INSTRUMENTATION_COLUMNS)
    components = json.loads(registry.iloc[0]["score_components_json"])
    assert components["final_confidence_score"] == int(registry.iloc[0]["confidence_score"])
    assert registry.iloc[0]["source_level_count"] == 1
    assert registry.iloc[0]["zone_width"] == (
        registry.iloc[0]["price_upper"] - registry.iloc[0]["price_lower"]
    )


def test_registry_merge_instrumentation_exposes_prior_score_without_changing_score():
    prior = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "H4", "H4_SWING_HIGH", 100.0)]),
        latest_close=90.0,
    )
    registry_in, _ = build_zone_registry(
        liquidity_map=prior,
        feed=_feed("2026-05-07", [90, 91]),
    )
    current = build_liquidity_map(
        pd.DataFrame([_level("level_000002", "BUY_SIDE", "H1", "H1_SWING_HIGH", 100.04)]),
        latest_close=90.0,
    )

    registry_out, _ = build_zone_registry(
        liquidity_map=current,
        feed=_feed("2026-05-08", [90, 91]),
        registry_in=registry_in,
    )

    active = registry_out[registry_out["status"] != "MERGED"].iloc[0]
    components = json.loads(active["score_components_json"])
    assert components["carry_forward_prior_score"] == 82
    assert components["source_count_bonus"] == 4
    assert components["h4_component"] == 8
    assert components["final_confidence_score"] == int(active["confidence_score"])
    assert active["confidence_score"] == 94
    assert active["confidence_tier"] == "HIGH"
    assert active["source_level_count"] == 2


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
