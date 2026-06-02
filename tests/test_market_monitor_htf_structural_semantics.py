import pandas as pd

from market_monitor.events import EVENT_LOG_COLUMNS
from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS
from market_monitor.structure import STRUCTURE_LEVEL_COLUMNS, build_structure_levels
from market_monitor.visual_overlay import _h4_65500_audit, _htf_structural_levels
from market_monitor.zone_registry import (
    LOCAL_CONTEXT_ACTIVE_FORWARD_ROLES,
    REGISTRY_COLUMNS,
    build_zone_registry,
    forward_liquidity_from_registry,
    local_session_context_role,
)


def test_h4_local_low_carries_htf_origin_fields_from_synthetic_fixture():
    feed = pd.DataFrame(
        [
            _candle("2026-03-27T12:00:00Z", high=67000, low=66000, close=66500),
            _candle("2026-03-27T16:00:00Z", high=66800, low=66000, close=66600),
            _candle("2026-03-27T17:00:00Z", high=66600, low=65500, close=65600),
            _candle("2026-03-27T20:00:00Z", high=67500, low=67000, close=67200),
        ]
    )

    levels = build_structure_levels(feed)
    h4_low = levels[
        (levels["level_type"] == "H4_SWING_LOW")
        & (levels["price"] == 65500)
    ].iloc[0]

    assert h4_low["source_timeframe_primary"] == "H4"
    assert h4_low["htf_level_type"] == "H4_SWING_LOW"
    assert h4_low["htf_origin_timestamp"] == "2026-03-27T17:00:00Z"
    assert h4_low["htf_origin_price"] == 65500
    assert h4_low["htf_confirmation_timestamp"] == "2026-03-27T20:00:00Z"


def test_m1_repeated_touches_do_not_increment_htf_sweep_count():
    registry, _ = build_zone_registry(
        liquidity_map=_htf_liquidity_map(),
        feed=_feed_from_lows([100.5, 100.4, 100.6, 100.3], close=103),
    )

    row = registry.iloc[0]
    assert row["m1_interaction_count"] == 4
    assert row["htf_sweep_count"] == 0
    assert row["htf_lifecycle_status"] == "HTF_ACTIVE"


def test_h4_level_is_not_consumed_by_m1_chop():
    registry, _ = build_zone_registry(
        liquidity_map=_htf_liquidity_map(),
        feed=pd.DataFrame(
            [
                _candle("2026-03-29T20:00:00Z", high=102, low=98.5, close=103),
                _candle("2026-03-29T20:01:00Z", high=102, low=98.0, close=97),
                _candle("2026-03-29T20:02:00Z", high=103, low=98.2, close=103),
                _candle("2026-03-29T20:03:00Z", high=102, low=98.1, close=97),
                _candle("2026-03-29T20:04:00Z", high=103, low=98.3, close=103),
            ]
        ),
    )

    row = registry.iloc[0]
    assert row["cross_through_count"] >= 3
    assert row["htf_sweep_count"] == 1
    assert row["consumption_status"] == "SWEPT_ONCE"
    assert row["consumption_status"] not in {"CONSUMED", "CHOPPED_THROUGH"}
    assert row["sweep_importance_class"] == "HTF_STRUCTURAL_SWEEP"
    assert row["active_forward_role"] not in LOCAL_CONTEXT_ACTIVE_FORWARD_ROLES


def test_h4_sweep_count_requires_boundary_cross():
    touched_registry, _ = build_zone_registry(
        liquidity_map=_htf_liquidity_map(),
        feed=_feed_from_lows([99.5, 99.2, 99.1], close=103),
    )
    swept_registry, _ = build_zone_registry(
        liquidity_map=_htf_liquidity_map(),
        feed=_feed_from_lows([100.5, 98.9, 100.6], close=103),
    )

    assert touched_registry.iloc[0]["htf_sweep_count"] == 0
    assert swept_registry.iloc[0]["htf_sweep_count"] == 1


def test_local_session_sweep_is_not_structural_sweep():
    registry, _ = build_zone_registry(
        liquidity_map=_session_liquidity_map(),
        feed=pd.DataFrame(
            [
                _candle("2026-03-28T00:00:00Z", high=100.5, low=99.5, close=100),
                _candle("2026-03-28T00:01:00Z", high=102.5, low=100.5, close=101.8),
            ]
        ),
    )

    row = registry.iloc[0]
    assert row["sweep_importance_class"] == "LOCAL_SESSION_SWEEP"
    assert row["htf_lifecycle_status"] == "LOCAL_ONLY"


def test_zone_000064_shape_routes_to_local_repeated_interaction_context():
    row = _zone_000064_registry_row()

    forward = forward_liquidity_from_registry(pd.DataFrame([row]), latest_close=65000)

    assert local_session_context_role(row) == "LOCAL_REPEATED_INTERACTION"
    assert forward.empty


def test_local_session_repeated_interaction_zone_is_not_fresh_forward_liquidity():
    registry, _ = build_zone_registry(
        liquidity_map=_session_liquidity_map(),
        feed=_local_session_repeated_feed(),
    )

    row = registry.iloc[0]
    forward = forward_liquidity_from_registry(registry, latest_close=98)

    assert row["source_timeframe_primary"] == "SESSION"
    assert row["htf_lifecycle_status"] == "LOCAL_ONLY"
    assert row["sweep_importance_class"] == "LOCAL_SESSION_SWEEP"
    assert row["resweep_count"] >= 1
    assert row["active_forward_role"] == "LOCAL_REPEATED_INTERACTION"
    assert row["active_forward"] == "false"
    assert forward.empty


def test_local_session_heavy_m1_interaction_is_not_active_forward_fresh_liquidity():
    row = _zone_000064_registry_row()
    row.update(
        {
            "status": "ACTIVE",
            "consumption_status": "FRESH",
            "first_sweep_at": "",
            "resweep_count": 0,
            "failed_acceptance_count": 0,
            "m1_interaction_count": 300,
            "sweep_importance_class": "LOCAL_SESSION_ZONE",
            "active_forward_role": "FRESH_LIQUIDITY",
            "active_forward": "true",
        }
    )

    forward = forward_liquidity_from_registry(pd.DataFrame([row]), latest_close=65000)

    assert local_session_context_role(row) == "LOCAL_NOISY_ZONE"
    assert forward.empty


def test_zone_000065_h4_shape_is_not_downgraded_to_local_context():
    row = _h4_registry_row()

    assert local_session_context_role(row) == ""
    assert row["htf_lifecycle_status"] == "HTF_SWEPT"
    assert row["sweep_importance_class"] == "HTF_STRUCTURAL_SWEEP"


def test_visual_htf_section_ignores_session_rows_with_nan_htf_fields():
    zones = pd.DataFrame(
        [
            {
                "zone_id": "zone_session",
                "source_timeframe_primary": "SESSION",
                "source_timeframes": "SESSION",
                "htf_level_type": pd.NA,
                "sweep_importance_class": "LOCAL_SESSION_SWEEP",
            },
            {
                "zone_id": "zone_h4",
                "source_timeframe_primary": "H4",
                "source_timeframes": "H4|SESSION",
                "htf_level_type": "H4_SWING_LOW",
                "sweep_importance_class": "HTF_STRUCTURAL_SWEEP",
            },
        ]
    )

    assert _htf_structural_levels(zones)["zone_id"].tolist() == ["zone_h4"]


def test_2026_03_29_h4_65500_candidate_audit_reports_htf_sweep_window():
    audit = _h4_65500_audit(
        registry=pd.DataFrame([_h4_registry_row()]),
        structure_levels=pd.DataFrame([_h4_structure_level()]),
        event_log=pd.DataFrame(
            [
                {
                    "event_timestamp": "2026-03-29T22:46:00Z",
                    "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
                    "zone_id": "zone_000065",
                }
            ]
        ),
        timestamp=pd.Timestamp("2026-03-29T22:00:00Z"),
    )

    assert "classification: HTF_STRUCTURAL_SWEEP" in audit
    assert "h4_level_exists: true" in audit
    assert "registry_zone_exists: true" in audit
    assert "sweep_inside_plus_minus_1h: true 2026-03-29T22:46:00Z" in audit
    assert "model_blind_spot_htf_structure: false" in audit


def test_2026_03_29_h4_65500_audit_uses_registry_lineage_when_daily_structure_is_empty():
    audit = _h4_65500_audit(
        registry=pd.DataFrame([_h4_registry_row()]),
        structure_levels=pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS),
        event_log=pd.DataFrame(columns=EVENT_LOG_COLUMNS),
        timestamp=pd.Timestamp("2026-03-29T22:00:00Z"),
    )

    assert "classification: HTF_STRUCTURAL_SWEEP" in audit
    assert "h4_level_exists: true" in audit
    assert "h4_level_source: liquidity_zone_registry.csv" in audit
    assert "registry_zone_exists: true" in audit
    assert "h4_origin_timestamp: 2026-03-27T17:00:00Z" in audit
    assert "model_blind_spot_htf_structure: false" in audit


def test_missing_h4_65500_level_reports_model_blind_spot_htf_structure():
    audit = _h4_65500_audit(
        registry=pd.DataFrame(),
        structure_levels=pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS),
        event_log=pd.DataFrame(columns=EVENT_LOG_COLUMNS),
        timestamp=pd.Timestamp("2026-03-29T22:00:00Z"),
    )

    assert "classification: model_blind_spot_htf_structure" in audit
    assert "h4_level_exists: false" in audit


def test_market_monitor_outputs_do_not_add_signal_order_or_pnl_fields():
    forbidden = {"signal", "order", "entry", "exit", "pnl"}
    for columns in [STRUCTURE_LEVEL_COLUMNS, LIQUIDITY_MAP_COLUMNS, REGISTRY_COLUMNS, EVENT_LOG_COLUMNS]:
        lowered = {column.lower() for column in columns}
        assert forbidden.isdisjoint(lowered)


def _htf_liquidity_map() -> pd.DataFrame:
    row = _base_liquidity_row()
    row.update(
        {
            "side": "SELL_SIDE",
            "zone_type": "H4_SWING_LOW_ZONE",
            "source_timeframes": "H4",
            "source_timeframe_primary": "H4",
            "htf_level_type": "H4_SWING_LOW",
            "htf_origin_timestamp": "2026-03-27T17:00:00Z",
            "htf_origin_price": 100.0,
            "htf_confirmation_timestamp": "2026-03-27T20:00:00Z",
            "history_context_start": "2026-03-27T16:00:00Z",
            "sweep_importance_class": "HTF_STRUCTURAL_LEVEL",
        }
    )
    return pd.DataFrame([row])


def _session_liquidity_map() -> pd.DataFrame:
    row = _base_liquidity_row()
    row.update(
        {
            "created_at": "2026-03-28T00:00:00Z",
            "last_updated_at": "2026-03-28T00:00:00Z",
            "side": "BUY_SIDE",
            "zone_type": "ASIA_HIGH_ZONE",
            "source_timeframes": "SESSION",
            "source_timeframe_primary": "SESSION",
            "zone_origin_start": "2026-03-28T00:00:00Z",
            "zone_origin_end": "2026-03-28T00:00:00Z",
            "sweep_importance_class": "LOCAL_SESSION_ZONE",
        }
    )
    return pd.DataFrame([row])


def _local_session_repeated_feed() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _candle("2026-03-28T00:00:00Z", high=100.5, low=99.5, close=100),
            _candle("2026-03-28T00:01:00Z", high=102.5, low=100.5, close=101.8),
            _candle("2026-03-28T00:02:00Z", high=100.5, low=99.5, close=100),
            _candle("2026-03-28T00:03:00Z", high=102.7, low=100.5, close=101.9),
            _candle("2026-03-28T00:04:00Z", high=100.6, low=99.5, close=100),
        ]
    )


def _base_liquidity_row() -> dict[str, object]:
    return {
        "zone_id": "zone_000001",
        "created_at": "2026-03-29T20:00:00Z",
        "last_updated_at": "2026-03-29T20:00:00Z",
        "side": "BUY_SIDE",
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": 99.0,
        "price_upper": 101.0,
        "price_mid": 100.0,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": "ACTIVE",
        "consumption_status": "FRESH",
        "active_forward": True,
        "cross_through_count": 0,
        "close_above_count": 0,
        "close_below_count": 0,
        "alternating_close_count": 0,
        "bars_inside_zone_lifetime": 0,
        "last_clean_reaction_at": "",
        "consumed_at": "",
        "consumption_reason": "",
        "zone_outer_lower": 99.0,
        "zone_outer_upper": 101.0,
        "zone_core_lower": 99.0,
        "zone_core_upper": 101.0,
        "zone_origin_start": "2026-03-29T20:00:00Z",
        "zone_origin_end": "2026-03-29T20:00:00Z",
        "first_sweep_at": "",
        "resweep_count": 0,
        "failed_acceptance_count": 0,
        "rejection_without_sweep_count": 0,
        "drift_away_confirmed_at": "",
        "accepted_above_at": "",
        "accepted_below_at": "",
        "structural_zone_mode": "THIN_LEVEL",
        "zone_behavior_state": "NONE",
        "active_forward_role": "FRESH_LIQUIDITY",
        "htf_lifecycle_status": "",
        "m1_interaction_count": 0,
        "htf_sweep_count": 0,
        "htf_close_through_count": 0,
        "htf_acceptance_count": 0,
        "history_context_start": "",
        "history_context_incomplete": "false",
        "confidence_score": 75,
        "confidence_tier": "HIGH",
        "touch_count": 0,
        "sweep_count": 0,
        "distance_from_close_pct": 0,
        "data_quality": "RAW",
        "invalidation_reason": "",
        "precision_status": "PRECISE",
    }


def _feed_from_lows(lows: list[float], *, close: float) -> pd.DataFrame:
    rows = []
    for index, low in enumerate(lows):
        rows.append(
            _candle(
                f"2026-03-29T20:{index:02d}:00Z",
                high=max(close, 101.0),
                low=low,
                close=close,
            )
        )
    return pd.DataFrame(rows)


def _candle(ts: str, *, high: float, low: float, close: float) -> dict[str, object]:
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


def _h4_structure_level() -> dict[str, object]:
    return {
        "level_id": "level_000011",
        "created_at": "2026-03-27T20:00:00Z",
        "level_timestamp": "2026-03-27T17:00:00Z",
        "timeframe": "H4",
        "level_type": "H4_SWING_LOW",
        "source_timeframe_primary": "H4",
        "side": "SELL_SIDE",
        "price": 65501.0,
        "htf_level_type": "H4_SWING_LOW",
        "htf_origin_timestamp": "2026-03-27T17:00:00Z",
        "htf_origin_price": 65501.0,
        "htf_confirmation_timestamp": "2026-03-27T20:00:00Z",
        "source_start": "2026-03-27T16:00:00Z",
        "source_end": "2026-03-27T19:59:00Z",
        "touch_count": 1,
        "strength_score": 75,
        "status": "ACTIVE",
        "data_quality": "RAW",
        "source_level_ids": "",
    }


def _h4_registry_row() -> dict[str, object]:
    row = _h4_structure_level()
    return {
        "zone_id": "zone_000065",
        "first_seen_at": "2026-03-28T00:00:00Z",
        "last_seen_at": "2026-03-29T23:59:00Z",
        "last_updated_at": "2026-03-29T23:59:00Z",
        "side": "SELL_SIDE",
        "zone_type": "DOUBLE_BOTTOM_LIQUIDITY_ZONE",
        "price_lower": 65468.2495,
        "price_upper": 65533.7505,
        "price_mid": 65501.0,
        "source_level_ids": "level_000010|level_000011|level_000012",
        "source_timeframes": "CLUSTER|H1|H4|PATTERN|SESSION",
        "source_timeframe_primary": "H4",
        "htf_level_type": row["htf_level_type"],
        "htf_origin_timestamp": row["htf_origin_timestamp"],
        "htf_origin_price": row["htf_origin_price"],
        "htf_confirmation_timestamp": row["htf_confirmation_timestamp"],
        "status": "CROSSED_UNCLASSIFIED",
        "consumption_status": "SWEPT_ONCE",
        "active_forward": "true",
        "first_sweep_at": "2026-03-29T22:46:00Z",
        "htf_lifecycle_status": "HTF_SWEPT",
        "m1_interaction_count": 12,
        "htf_sweep_count": 1,
        "htf_close_through_count": 0,
        "htf_acceptance_count": 0,
        "sweep_importance_class": "HTF_STRUCTURAL_SWEEP",
    }


def _zone_000064_registry_row() -> dict[str, object]:
    return {
        "zone_id": "zone_000064",
        "first_seen_at": "2026-03-28T00:00:00Z",
        "last_seen_at": "2026-03-29T23:59:00Z",
        "last_updated_at": "2026-03-29T23:59:00Z",
        "side": "BUY_SIDE",
        "zone_type": "ASIA_HIGH_ZONE",
        "price_lower": 66000.0,
        "price_upper": 66030.0,
        "price_mid": 66015.0,
        "source_level_ids": "level_000064",
        "source_timeframes": "SESSION",
        "source_timeframe_primary": "SESSION",
        "htf_level_type": "",
        "htf_origin_timestamp": "",
        "htf_origin_price": 0.0,
        "htf_confirmation_timestamp": "",
        "status": "REACTED",
        "consumption_status": "REACTED",
        "active_forward": "true",
        "first_sweep_at": "2026-03-28T00:10:00Z",
        "resweep_count": 26,
        "failed_acceptance_count": 0,
        "structural_zone_mode": "THIN_LEVEL",
        "zone_behavior_state": "NONE",
        "active_forward_role": "FRESH_LIQUIDITY",
        "htf_lifecycle_status": "LOCAL_ONLY",
        "m1_interaction_count": 1328,
        "htf_sweep_count": 0,
        "htf_close_through_count": 0,
        "htf_acceptance_count": 0,
        "sweep_importance_class": "LOCAL_SESSION_SWEEP",
        "confidence_score": 55,
        "confidence_tier": "MEDIUM",
        "data_quality": "RAW",
        "precision_status": "PRECISE",
    }
