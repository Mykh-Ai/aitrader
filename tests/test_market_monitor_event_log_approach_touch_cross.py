import pandas as pd

from market_monitor.events import build_event_log


def test_buy_side_approach_touch_and_cross_events():
    approach = _event_for("BUY_SIDE", [89, 95], 100, 110)
    touch = _event_for("BUY_SIDE", [90, 105], 100, 110)
    cross = _event_for("BUY_SIDE", [90, 111], 100, 110)

    assert approach.loc[0, "event_type"] == "LIQUIDITY_ZONE_APPROACHED"
    assert touch.loc[0, "event_type"] == "LIQUIDITY_ZONE_TOUCHED"
    assert cross.loc[0, "event_type"] == "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"
    assert cross.loc[0, "excursion_abs"] == 1


def test_sell_side_approach_touch_and_cross_events():
    approach = _event_for("SELL_SIDE", [121, 115], 100, 110)
    touch = _event_for("SELL_SIDE", [120, 105], 100, 110)
    cross = _event_for("SELL_SIDE", [120, 99], 100, 110)

    assert approach.loc[0, "event_type"] == "LIQUIDITY_ZONE_APPROACHED"
    assert touch.loc[0, "event_type"] == "LIQUIDITY_ZONE_TOUCHED"
    assert cross.loc[0, "event_type"] == "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"
    assert cross.loc[0, "excursion_abs"] == 1


def test_cross_events_do_not_emit_sweep_or_trade_language():
    event_log = _event_for("BUY_SIDE", [90, 111], 100, 110)

    assert "SWEPT_REJECTED" not in event_log["event_type"].tolist()
    assert "SWEPT_ACCEPTED" not in event_log["event_type"].tolist()
    assert "signal" not in event_log.columns
    assert "entry" not in event_log.columns
    assert "exit" not in event_log.columns
    assert "order" not in event_log.columns
    assert "position" not in event_log.columns


def _event_for(side, closes, lower, upper):
    registry = pd.DataFrame([_registry_row(side, lower, upper)])
    feed = _feed(closes)
    return build_event_log(
        registry=registry,
        feed=feed,
        volume_delta_state=_volume_delta(feed),
    )


def _registry_row(side, lower, upper):
    return {
        "zone_id": "zone_000001",
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE" if side == "BUY_SIDE" else "H1_SWING_LOW_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
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


def _feed(closes):
    rows = []
    for idx, close in enumerate(closes):
        rows.append(
            {
                "Timestamp": pd.Timestamp(f"2026-05-08T00:0{idx}:00Z"),
                "OpenPrice": close,
                "HiPrice": close,
                "LowPrice": close,
                "ClosePrice": close,
                "TotalQty": 10,
                "Trades": 1,
                "BuyQty": 5,
                "SellQty": 5,
                "OpenInterest": 1000 + idx,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceFile": "synthetic.csv",
            }
        )
    return pd.DataFrame(rows)


def _volume_delta(feed):
    return pd.DataFrame(
        {
            "timestamp": feed["Timestamp"].map(lambda value: value.isoformat().replace("+00:00", "Z")),
            "volume_zscore": [0.0] * len(feed),
            "delta_zscore": [0.0] * len(feed),
            "oi_change": [0.0] * len(feed),
        }
    )
