import pandas as pd

from market_monitor.zone_registry import MAX_ZONE_AGE_REASON, build_zone_registry


def test_buy_side_zone_touched_and_crossed_statuses():
    touched, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "BUY_SIDE", 100, 110)]),
        feed=_path_feed([95, 105]),
    )
    crossed, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "BUY_SIDE", 100, 110)]),
        feed=_path_feed([95, 111]),
    )

    assert touched.loc[0, "status"] == "TOUCHED"
    assert touched.loc[0, "touch_count"] == 1
    assert crossed.loc[0, "status"] == "CROSSED_UNCLASSIFIED"
    assert crossed.loc[0, "cross_count"] == 1
    assert "SWEPT_REJECTED" not in crossed["status"].tolist()
    assert "SWEPT_ACCEPTED" not in crossed["status"].tolist()


def test_sell_side_zone_touched_and_crossed_statuses():
    touched, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "SELL_SIDE", 100, 110)]),
        feed=_path_feed([115, 105]),
    )
    crossed, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "SELL_SIDE", 100, 110)]),
        feed=_path_feed([115, 99]),
    )

    assert touched.loc[0, "status"] == "TOUCHED"
    assert crossed.loc[0, "status"] == "CROSSED_UNCLASSIFIED"
    assert crossed.loc[0, "cross_count"] == 1


def test_expiry_marks_stale_non_exempt_zone_expired():
    registry_in = pd.DataFrame([_registry_row("zone_000001", age_days=8)])

    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed([90], day="2026-05-16"),
        registry_in=registry_in,
    )

    assert registry.loc[0, "status"] == "EXPIRED"
    assert registry.loc[0, "invalidation_reason"] == MAX_ZONE_AGE_REASON


def test_high_confidence_h4_cluster_is_expiry_exempt():
    registry_in = pd.DataFrame(
        [
            _registry_row(
                "zone_000001",
                age_days=8,
                zone_type="CLUSTERED_BUY_SIDE_ZONE",
                source_timeframes="H1|H4",
                confidence_score=90,
                confidence_tier="HIGH",
                lower=70000,
                upper=70100,
            )
        ]
    )

    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map([]),
        feed=_path_feed([65000], day="2026-05-16"),
        registry_in=registry_in,
    )

    assert registry.loc[0, "status"] == "ACTIVE"


def test_worst_data_quality_survives_merge():
    registry_in = pd.DataFrame(
        [_registry_row("zone_000001", lower=70000, upper=70080, data_quality="RECOVERED_DEGRADED")]
    )
    current = _liquidity_map([_zone("zone_000002", "BUY_SIDE", 70040, 70120, "RAW")])

    registry, _ = build_zone_registry(
        liquidity_map=current,
        feed=_path_feed([65000]),
        registry_in=registry_in,
    )

    active = registry[registry["status"] == "ACTIVE"].iloc[0]
    assert active["data_quality"] == "RECOVERED_DEGRADED"


def _registry_row(
    zone_id,
    age_days=0,
    zone_type="H1_SWING_HIGH_ZONE",
    source_timeframes="H1",
    confidence_score=65,
    confidence_tier="MEDIUM",
    data_quality="RAW",
    lower=100,
    upper=110,
):
    return {
        "zone_id": zone_id,
        "first_seen_at": "2026-05-07T00:00:00Z",
        "last_seen_at": "2026-05-07T23:59:00Z",
        "last_updated_at": "2026-05-07T23:59:00Z",
        "side": "BUY_SIDE",
        "zone_type": zone_type,
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_old",
        "source_timeframes": source_timeframes,
        "status": "ACTIVE",
        "confidence_score": confidence_score,
        "confidence_tier": confidence_tier,
        "age_bars": 1440,
        "age_days": age_days,
        "touch_count": 0,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "",
        "last_cross_at": "",
        "merged_into_zone_id": "",
        "data_quality": data_quality,
        "invalidation_reason": "",
    }


def _liquidity_map(rows):
    return pd.DataFrame(rows)


def _zone(zone_id, side, lower, upper, quality="RAW"):
    return {
        "zone_id": zone_id,
        "created_at": "2026-05-08T00:00:00Z",
        "last_updated_at": "2026-05-08T00:00:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE" if side == "BUY_SIDE" else "H1_SWING_LOW_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_new",
        "source_timeframes": "H1",
        "status": "ACTIVE",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "touch_count": 1,
        "sweep_count": 0,
        "distance_from_close_pct": 0,
        "data_quality": quality,
        "invalidation_reason": "",
    }


def _path_feed(closes, day="2026-05-08"):
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
