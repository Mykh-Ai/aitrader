import pandas as pd

from market_monitor.zone_registry import build_zone_registry


def test_active_carried_zone_keeps_stable_zone_id_across_days():
    day1, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "BUY_SIDE", 100, 110)]),
        feed=_path_feed("2026-05-07", [90, 95]),
    )

    day2, stats = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed("2026-05-08", [92, 96]),
        registry_in=day1,
    )

    active = day2[day2["status"] == "ACTIVE"].iloc[0]
    assert active["zone_id"] == "zone_000001"
    assert stats["carried_loaded"] == 1
    assert stats["active_registry"] == 1


def test_invalidated_expired_and_merged_zones_are_not_carried_as_active():
    registry_in = pd.DataFrame(
        [
            _registry_row("zone_000001", "INVALIDATED"),
            _registry_row("zone_000002", "EXPIRED"),
            _registry_row("zone_000003", "MERGED"),
        ]
    )

    registry_out, stats = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed("2026-05-08", [90, 95]),
        registry_in=registry_in,
    )

    assert stats["carried_loaded"] == 0
    assert stats["active_registry"] == 0
    assert set(registry_out["status"]) == {"INVALIDATED", "EXPIRED", "MERGED"}


def test_carried_plus_new_compatible_zone_preserves_carried_id_and_marks_merged_away():
    registry_in = pd.DataFrame([_registry_row("zone_000010", "ACTIVE", lower=70000, upper=70080)])
    current = _liquidity_map([_zone("zone_000001", "BUY_SIDE", 70040, 70120)])

    registry_out, _ = build_zone_registry(
        liquidity_map=current,
        feed=_path_feed("2026-05-08", [65000, 65001]),
        registry_in=registry_in,
    )

    active = registry_out[registry_out["status"] == "ACTIVE"].iloc[0]
    merged = registry_out[registry_out["status"] == "MERGED"].iloc[0]
    assert active["zone_id"] == "zone_000010"
    assert merged["merged_into_zone_id"] == "zone_000010"
    assert active["source_level_ids"] == "level_000001|level_old"


def test_registry_carry_forward_does_not_widen_zone_above_hard_precision_cap():
    registry_in = pd.DataFrame(
        [_registry_row("zone_000010", "ACTIVE", lower=70000, upper=70300)]
    )
    current = _liquidity_map([_zone("zone_000001", "BUY_SIDE", 70320, 70400)])

    registry_out, _ = build_zone_registry(
        liquidity_map=current,
        feed=_path_feed("2026-05-08", [65000, 65001]),
        registry_in=registry_in,
    )

    active = registry_out[registry_out["status"] == "ACTIVE"]
    assert len(active) == 2
    assert all(active["zone_width_pct"] < 0.50)
    assert not (registry_out["status"] == "MERGED").any()


def test_wide_high_h4_carried_zone_is_not_expiry_exempt_when_stale():
    registry_in = pd.DataFrame(
        [
            _registry_row(
                "zone_000010",
                "ACTIVE",
                lower=70000,
                upper=70550,
                first_seen_at="2026-05-01T00:00:00Z",
                source_timeframes="H4",
                zone_type="CLUSTERED_BUY_SIDE_ZONE",
                confidence_score=88,
                confidence_tier="HIGH",
            )
        ]
    )

    registry_out, _ = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed("2026-05-10", [65000, 65001]),
        registry_in=registry_in,
    )

    row = registry_out.iloc[0]
    assert row["precision_status"] == "TOO_WIDE"
    assert row["status"] == "EXPIRED"
    assert row["invalidation_reason"] == "MAX_ZONE_AGE_DAYS_EXCEEDED"


def test_stale_low_precision_h4_cluster_is_not_expiry_exempt_without_compact_evidence():
    registry_in = pd.DataFrame(
        [
            _registry_row(
                "zone_000010",
                "ACTIVE",
                lower=70000,
                upper=70300,
                first_seen_at="2026-05-01T00:00:00Z",
                source_timeframes="H1|H4",
                zone_type="CLUSTERED_BUY_SIDE_ZONE",
                confidence_score=90,
                confidence_tier="HIGH",
            )
        ]
    )

    registry_out, _ = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed("2026-05-10", [65000, 65001]),
        registry_in=registry_in,
    )

    row = registry_out.iloc[0]
    assert row["precision_status"] == "LOW_PRECISION"
    assert row["status"] == "EXPIRED"
    assert row["invalidation_reason"] == "MAX_ZONE_AGE_DAYS_EXCEEDED"


def _registry_row(
    zone_id,
    status,
    lower=100,
    upper=110,
    first_seen_at="2026-05-07T00:00:00Z",
    source_timeframes="H1",
    zone_type="H1_SWING_HIGH_ZONE",
    confidence_score=65,
    confidence_tier="MEDIUM",
):
    return {
        "zone_id": zone_id,
        "first_seen_at": first_seen_at,
        "last_seen_at": "2026-05-07T23:59:00Z",
        "last_updated_at": "2026-05-07T23:59:00Z",
        "side": "BUY_SIDE",
        "zone_type": zone_type,
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_old",
        "source_timeframes": source_timeframes,
        "status": status,
        "confidence_score": confidence_score,
        "confidence_tier": confidence_tier,
        "age_bars": 1440,
        "age_days": 0,
        "touch_count": 0,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "",
        "last_cross_at": "",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _liquidity_map(rows):
    return pd.DataFrame(rows)


def _zone(zone_id, side, lower, upper):
    return {
        "zone_id": zone_id,
        "created_at": "2026-05-08T00:00:00Z",
        "last_updated_at": "2026-05-08T00:00:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": "ACTIVE",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "touch_count": 1,
        "sweep_count": 0,
        "distance_from_close_pct": 0,
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _path_feed(day, closes):
    rows = []
    for idx, close in enumerate(closes):
        rows.append(
            {
                "Timestamp": pd.Timestamp(f"{day}T00:0{idx}:00Z"),
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
