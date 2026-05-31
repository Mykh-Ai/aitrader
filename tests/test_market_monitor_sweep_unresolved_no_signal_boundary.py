import json

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
FORBIDDEN_EVENT_TYPES = {
    "SWEPT_REJECTED",
    "SWEPT_ACCEPTED",
    "FAILED_BREAKOUT",
    "ACCEPTED_BREAKOUT",
}
FORBIDDEN_EVIDENCE_TERMS = {
    "signal",
    "entry",
    "exit",
    "order",
    "position",
    "leverage",
    "stop_loss",
    "take_profit",
    "risk",
    "swept_rejected",
    "swept_accepted",
    "failed_breakout",
    "accepted_breakout",
    "long",
    "short",
}


def test_unresolved_sweep_event_log_has_no_signal_order_position_or_classification_terms():
    event_log = build_event_log(
        registry=pd.DataFrame([_registry_row()]),
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert {column.lower() for column in event_log.columns}.isdisjoint(FORBIDDEN_COLUMNS)
    assert set(event_log["event_type"]).isdisjoint(FORBIDDEN_EVENT_TYPES)
    assert "LIQUIDITY_SWEEP_UNRESOLVED" in event_log["event_type"].tolist()
    unresolved = event_log[event_log["event_type"] == "LIQUIDITY_SWEEP_UNRESOLVED"].iloc[0]
    assert unresolved["reaction_status"] == "UNRESOLVED"

    evidence = json.loads(unresolved["evidence_json"])
    evidence_text = json.dumps(evidence, sort_keys=True).lower()
    assert all(term not in evidence_text for term in FORBIDDEN_EVIDENCE_TERMS)


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
        "status": "ACTIVE",
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
    }


def _feed():
    return pd.DataFrame(
        [
            _row("2026-05-08T00:00:00Z", 95, 90, 92),
            _row("2026-05-08T00:01:00Z", 125, 90, 120),
        ]
    )


def _row(ts, high, low, close):
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


def _volume_delta():
    return pd.DataFrame(
        {
            "timestamp": ["2026-05-08T00:00:00Z", "2026-05-08T00:01:00Z"],
            "volume_zscore": [0.0, 2.0],
            "delta_zscore": [0.0, 2.0],
            "oi_change": [0.0, 1.0],
        }
    )
