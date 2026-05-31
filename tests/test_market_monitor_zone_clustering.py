import pandas as pd

from market_monitor.liquidity_zones import build_liquidity_map


def test_overlapping_same_side_zones_merge_and_preserve_source_ids():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=65000.0)

    assert len(zones) == 1
    assert zones.loc[0, "source_level_ids"] == "level_000001|level_000002"
    assert zones.loc[0, "source_timeframes"] == "H1|H4"
    assert zones.loc[0, "zone_type"] == "CLUSTERED_BUY_SIDE_ZONE"
    assert zones.loc[0, "precision_status"] == "PRECISE"


def test_merge_candidate_that_would_exceed_hard_width_cap_is_blocked():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
            _level("level_000002", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70100.0),
            _level("level_000003", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70200.0),
            _level("level_000004", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70300.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=65000.0)

    assert len(zones) == 2
    assert all(zones["zone_width_pct"] < 0.50)
    assert "level_000001|level_000002|level_000003|level_000004" not in set(
        zones["source_level_ids"]
    )


def test_intermediate_wide_merge_is_kept_with_low_precision_flag():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70100.0),
            _level("level_000003", "BUY_SIDE", "SESSION", "ASIA_HIGH", 70200.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=65000.0)

    assert len(zones) == 1
    assert 0.25 <= zones.loc[0, "zone_width_pct"] < 0.50
    assert zones.loc[0, "precision_status"] == "LOW_PRECISION"


def test_opposite_side_zones_do_not_merge():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0),
            _level("level_000002", "SELL_SIDE", "H1", "H1_SWING_LOW", 70000.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=70000.0)

    assert len(zones) == 2
    assert set(zones["side"]) == {"BUY_SIDE", "SELL_SIDE"}


def test_merged_zone_uses_worst_data_quality():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 70000.0, "RAW"),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 70020.0, "RECOVERED_DEGRADED"),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=65000.0)

    assert zones.loc[0, "data_quality"] == "RECOVERED_DEGRADED"


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
