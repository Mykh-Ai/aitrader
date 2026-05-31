import pandas as pd

from market_monitor.events import build_event_log


def test_buy_side_cross_with_sufficient_evidence_emits_unresolved_sweep_candidate():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=1.6,
    )

    assert event_log["event_type"].tolist() == [
        "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED",
        "LIQUIDITY_SWEEP_UNRESOLVED",
    ]
    unresolved = event_log.iloc[1]
    assert unresolved["reaction_status"] == "UNRESOLVED"
    assert unresolved["excursion_abs"] == 15


def test_sell_side_cross_with_sufficient_evidence_emits_unresolved_sweep_candidate():
    event_log = _event_log(
        side="SELL_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=120,
        event_low=85,
        delta_zscore=-1.6,
    )

    assert event_log["event_type"].tolist() == [
        "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED",
        "LIQUIDITY_SWEEP_UNRESOLVED",
    ]
    assert event_log.iloc[1]["reaction_status"] == "UNRESOLVED"
    assert event_log.iloc[1]["excursion_abs"] == 15


def test_cross_without_pre_existing_zone_does_not_emit_unresolved_sweep():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:01:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=1.6,
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def test_cross_below_minimum_excursion_does_not_emit_unresolved_sweep():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=115,
        event_low=90,
        volume_zscore=1.6,
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def test_cross_without_activity_evidence_does_not_emit_unresolved_sweep():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=0,
        delta_zscore=0,
        oi_change=0,
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def test_degraded_data_does_not_use_untrusted_activity_fields_as_evidence():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=4,
        delta_zscore=4,
        oi_change=10,
        data_quality="RECOVERED_DEGRADED",
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def test_too_wide_zone_does_not_emit_unresolved_sweep_candidate():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=1.6,
        precision_status="TOO_WIDE",
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def test_low_precision_zone_keeps_precision_status_in_unresolved_evidence():
    event_log = _event_log(
        side="BUY_SIDE",
        first_seen_at="2026-05-08T00:00:00Z",
        event_high=125,
        event_low=90,
        volume_zscore=1.6,
        precision_status="LOW_PRECISION",
    )

    unresolved = event_log[event_log["event_type"] == "LIQUIDITY_SWEEP_UNRESOLVED"].iloc[0]
    assert '"precision_status":"LOW_PRECISION"' in unresolved["evidence_json"]


def test_prior_crossed_zone_does_not_emit_unresolved_without_new_current_run_transition():
    previous_registry = pd.DataFrame(
        [_registry_row("BUY_SIDE", "2026-05-07T00:00:00Z", "RAW")]
    )
    previous_registry.loc[0, "status"] = "CROSSED_UNCLASSIFIED"
    registry = previous_registry.copy()
    feed = pd.DataFrame(
        [
            _row("2026-05-08T00:00:00Z", high=125, low=120, close=124),
            _row("2026-05-08T00:01:00Z", high=126, low=121, close=125),
        ]
    )

    event_log = build_event_log(
        registry=registry,
        feed=feed,
        volume_delta_state=_volume_delta(feed, volume_zscore=4, oi_change=1),
        previous_registry=previous_registry,
    )

    assert event_log["event_type"].tolist() == ["LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED"]


def _event_log(
    *,
    side,
    first_seen_at,
    event_high,
    event_low,
    volume_zscore=0,
    delta_zscore=0,
    oi_change=0,
    data_quality="RAW",
    precision_status="PRECISE",
):
    registry = pd.DataFrame([_registry_row(side, first_seen_at, data_quality, precision_status)])
    initial_high = 95 if side == "BUY_SIDE" else 120
    initial_low = 90 if side == "BUY_SIDE" else 115
    feed = pd.DataFrame(
        [
            _row(
                "2026-05-08T00:00:00Z",
                high=initial_high,
                low=initial_low,
                close=(initial_high + initial_low) / 2,
                data_quality=data_quality,
            ),
            _row(
                "2026-05-08T00:01:00Z",
                high=event_high,
                low=event_low,
                close=(event_high + event_low) / 2,
                data_quality=data_quality,
            ),
        ]
    )
    return build_event_log(
        registry=registry,
        feed=feed,
        volume_delta_state=_volume_delta(
            feed,
            volume_zscore=volume_zscore,
            delta_zscore=delta_zscore,
            oi_change=oi_change,
        ),
    )


def _registry_row(side, first_seen_at, data_quality, precision_status="PRECISE"):
    return {
        "zone_id": "zone_000001",
        "first_seen_at": first_seen_at,
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE" if side == "BUY_SIDE" else "H1_SWING_LOW_ZONE",
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
        "data_quality": data_quality,
        "invalidation_reason": "",
        "precision_status": precision_status,
    }


def _row(ts, *, high, low, close, data_quality="RAW"):
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
        "DataQuality": data_quality,
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
