import pandas as pd

from market_monitor.events import build_event_log
from market_monitor.zone_registry import build_zone_registry, forward_liquidity_from_registry


def test_repeated_closes_above_below_zone_become_chopped_through():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(),
        feed=_feed([95, 115, 95, 115, 95]),
    )

    row = registry.iloc[0]
    assert row["consumption_status"] == "CHOPPED_THROUGH"
    assert row["alternating_close_count"] >= 3
    assert row["active_forward"] == "false"


def test_cross_through_count_threshold_becomes_consumed():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(),
        feed=_cross_through_feed(),
    )

    row = registry.iloc[0]
    assert row["consumption_status"] == "CONSUMED"
    assert row["cross_through_count"] >= 3
    assert row["active_forward"] == "false"


def test_consumed_zone_not_in_active_forward_liquidity_map():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(),
        feed=_cross_through_feed(),
    )

    forward = forward_liquidity_from_registry(registry, latest_close=90)

    assert forward.empty


def test_consumed_zone_cannot_emit_unresolved_sweep():
    registry = _registry_row(consumption_status="CONSUMED", consumed_at="2026-05-08T00:00:30Z")
    feed = pd.DataFrame(
        [
            _candle("2026-05-08T00:00:00Z", high=95, low=90, close=92),
            _candle("2026-05-08T00:01:00Z", high=130, low=90, close=125),
        ]
    )

    event_log = build_event_log(
        registry=pd.DataFrame([registry]),
        feed=feed,
        volume_delta_state=_volume_delta(feed, volume_zscore=4, oi_change=1),
    )

    assert "LIQUIDITY_SWEEP_UNRESOLVED" not in event_log["event_type"].tolist()


def test_clean_sweep_reaction_sets_reacted_consumption_status():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(),
        feed=_feed([95, 115, 105, 94]),
    )

    row = registry.iloc[0]
    assert row["consumption_status"] == "REACTED"
    assert row["status"] == "REACTED"
    assert row["last_clean_reaction_at"] == "2026-05-08T00:03:00Z"


def _liquidity_map():
    return pd.DataFrame(
        [
            {
                "zone_id": "zone_000001",
                "created_at": "2026-05-08T00:00:00Z",
                "last_updated_at": "2026-05-08T00:00:00Z",
                "side": "BUY_SIDE",
                "zone_type": "ASIA_HIGH_ZONE",
                "price_lower": 100,
                "price_upper": 110,
                "price_mid": 105,
                "source_level_ids": "level_000001",
                "source_timeframes": "SESSION",
                "status": "ACTIVE",
                "confidence_score": 65,
                "confidence_tier": "MEDIUM",
                "touch_count": 0,
                "sweep_count": 0,
                "distance_from_close_pct": 0,
                "data_quality": "RAW",
                "invalidation_reason": "",
                "precision_status": "PRECISE",
            }
        ]
    )


def _registry_row(*, consumption_status="", consumed_at=""):
    return {
        "zone_id": "zone_000001",
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": "BUY_SIDE",
        "zone_type": "ASIA_HIGH_ZONE",
        "price_lower": 100,
        "price_upper": 110,
        "price_mid": 105,
        "source_level_ids": "level_000001",
        "source_timeframes": "SESSION",
        "status": "ACTIVE",
        "consumption_status": consumption_status,
        "active_forward": "false" if consumption_status else "true",
        "cross_through_count": 0,
        "close_above_count": 0,
        "close_below_count": 0,
        "alternating_close_count": 0,
        "bars_inside_zone_lifetime": 0,
        "last_clean_reaction_at": "",
        "consumed_at": consumed_at,
        "consumption_reason": "",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "age_bars": 2,
        "age_days": 0,
        "touch_count": 0,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "",
        "last_cross_at": "",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
        "precision_status": "PRECISE",
    }


def _feed(closes):
    return pd.DataFrame(
        [
            _candle(
                f"2026-05-08T00:0{idx}:00Z",
                high=close + 1,
                low=close - 1,
                close=close,
            )
            for idx, close in enumerate(closes)
        ]
    )


def _cross_through_feed():
    return pd.DataFrame(
        [
            _candle("2026-05-08T00:00:00Z", high=116, low=94, close=105),
            _candle("2026-05-08T00:01:00Z", high=117, low=93, close=105),
            _candle("2026-05-08T00:02:00Z", high=118, low=92, close=105),
        ]
    )


def _candle(ts, *, high, low, close):
    return {
        "Timestamp": pd.Timestamp(ts),
        "OpenPrice": close,
        "HiPrice": high,
        "LowPrice": low,
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


def _volume_delta(feed, *, volume_zscore=0, delta_zscore=0, oi_change=0):
    return pd.DataFrame(
        {
            "timestamp": feed["Timestamp"].map(lambda value: value.isoformat().replace("+00:00", "Z")),
            "volume_zscore": [0.0, float(volume_zscore)],
            "delta_zscore": [0.0, float(delta_zscore)],
            "oi_change": [0.0, float(oi_change)],
        }
    )
