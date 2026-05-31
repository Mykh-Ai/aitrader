import pandas as pd

from market_monitor.events import build_event_log


FORBIDDEN_COLUMNS = {
    "signal",
    "entry",
    "exit",
    "order",
    "position",
    "position_size",
    "leverage",
    "stop_loss",
    "take_profit",
    "risk",
}


def test_event_log_has_no_signal_order_position_columns_or_forbidden_event_types():
    event_log = build_event_log(
        registry=pd.DataFrame([_registry_row()]),
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert {column.lower() for column in event_log.columns}.isdisjoint(FORBIDDEN_COLUMNS)
    assert "SWEPT_REJECTED" not in event_log["event_type"].tolist()
    assert "SWEPT_ACCEPTED" not in event_log["event_type"].tolist()
    assert "LIQUIDITY_SWEEP" not in event_log["event_type"].tolist()


def _registry_row():
    return {
        "zone_id": "zone_000001",
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": "BUY_SIDE",
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": 100,
        "price_upper": 110,
        "price_mid": 105,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": "CROSSED_UNCLASSIFIED",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "age_bars": 2,
        "age_days": 0,
        "touch_count": 0,
        "cross_count": 1,
        "active_days": 1,
        "last_touch_at": "2026-05-08T00:01:00Z",
        "last_cross_at": "2026-05-08T00:01:00Z",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _feed():
    return pd.DataFrame(
        [
            _row("2026-05-08T00:00:00Z", 90),
            _row("2026-05-08T00:01:00Z", 111),
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
