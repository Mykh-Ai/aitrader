import json

import pandas as pd

from market_monitor.events import build_event_log


def test_merge_creates_lifecycle_event():
    registry = pd.DataFrame([_registry_row("zone_000002", "MERGED", "zone_000001")])

    event_log = build_event_log(
        registry=registry,
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert event_log.loc[0, "event_type"] == "LIQUIDITY_ZONE_MERGED"
    evidence = json.loads(event_log.loc[0, "evidence_json"])
    assert evidence["merged_from_zone_id"] == "zone_000002"
    assert evidence["merged_into_zone_id"] == "zone_000001"


def test_expiry_creates_lifecycle_event():
    registry = pd.DataFrame([_registry_row("zone_000002", "EXPIRED", "", "MAX_ZONE_AGE_DAYS_EXCEEDED")])

    event_log = build_event_log(
        registry=registry,
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert event_log.loc[0, "event_type"] == "LIQUIDITY_ZONE_EXPIRED"
    evidence = json.loads(event_log.loc[0, "evidence_json"])
    assert evidence["invalidation_reason"] == "MAX_ZONE_AGE_DAYS_EXCEEDED"
    assert evidence["max_zone_age_days"] == 7


def test_event_log_contains_current_run_events_only():
    registry = pd.DataFrame(
        [
            _registry_row(
                "zone_000002",
                "MERGED",
                "zone_000001",
                last_updated_at="2026-05-07T00:00:00Z",
            )
        ]
    )

    event_log = build_event_log(
        registry=registry,
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert event_log.empty


def test_lifecycle_event_not_repeated_when_previous_registry_already_has_status():
    registry = pd.DataFrame([_registry_row("zone_000002", "MERGED", "zone_000001")])
    previous_registry = pd.DataFrame([_registry_row("zone_000002", "MERGED", "zone_000001")])

    event_log = build_event_log(
        registry=registry,
        feed=_feed(),
        volume_delta_state=_volume_delta(),
        previous_registry=previous_registry,
    )

    assert event_log.empty


def _registry_row(
    zone_id,
    status,
    merged_into_zone_id="",
    invalidation_reason="",
    last_updated_at="2026-05-08T00:01:00Z",
):
    return {
        "zone_id": zone_id,
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": last_updated_at,
        "last_updated_at": last_updated_at,
        "side": "BUY_SIDE",
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": 100,
        "price_upper": 110,
        "price_mid": 105,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": status,
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "age_bars": 2,
        "age_days": 8,
        "touch_count": 0,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "",
        "last_cross_at": "",
        "merged_into_zone_id": merged_into_zone_id,
        "data_quality": "RAW",
        "invalidation_reason": invalidation_reason,
    }


def _feed():
    return pd.DataFrame(
        [
            _row("2026-05-08T00:00:00Z", 90),
            _row("2026-05-08T00:01:00Z", 91),
        ]
    )


def _row(ts, close):
    return {
        "Timestamp": pd.Timestamp(ts),
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


def _volume_delta():
    return pd.DataFrame(
        {
            "timestamp": ["2026-05-08T00:00:00Z", "2026-05-08T00:01:00Z"],
            "volume_zscore": [0.0, 0.0],
            "delta_zscore": [0.0, 0.0],
            "oi_change": [0.0, 0.0],
        }
    )
