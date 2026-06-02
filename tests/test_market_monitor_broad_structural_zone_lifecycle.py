import pandas as pd

from market_monitor.zone_registry import build_zone_registry


def test_broad_zone_many_inside_touches_does_not_become_chopped_through():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([102, 104, 106, 108, 105] * 5),
    )

    row = registry.iloc[0]
    assert row["structural_zone_mode"] == "BROAD_STRUCTURAL_ZONE"
    assert row["bars_inside_zone_lifetime"] >= 20
    assert row["consumption_status"] != "CHOPPED_THROUGH"
    assert row["active_forward"] == "true"


def test_broad_zone_true_two_sided_full_zone_chop_becomes_chopped_through():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([95, 115, 95, 115, 95]),
    )

    row = registry.iloc[0]
    assert row["consumption_status"] == "CHOPPED_THROUGH"
    assert row["consumption_reason"] == "broad_full_zone_two_sided_chop"
    assert row["active_forward"] == "false"


def test_broad_zone_failed_acceptance_above_sets_distribution_role():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([104, 112, 108, 106]),
    )

    row = registry.iloc[0]
    assert row["zone_behavior_state"] in {"FAILED_ACCEPTANCE", "DISTRIBUTION_CANDIDATE"}
    assert row["failed_acceptance_count"] >= 1
    assert row["active_forward_role"] == "DISTRIBUTION_ZONE"
    assert row["consumption_status"] != "CHOPPED_THROUGH"


def test_broad_zone_drift_away_sets_reaction_role_and_timestamp():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([104, 112, 108, 98]),
    )

    row = registry.iloc[0]
    assert row["zone_behavior_state"] == "DRIFT_AWAY_FROM_ZONE"
    assert row["drift_away_confirmed_at"] == "2026-05-08T00:03:00Z"
    assert row["active_forward_role"] == "REACTION_ZONE"


def test_broad_buy_side_zone_accepted_above_gets_state():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([104, 112, 113, 114]),
    )

    row = registry.iloc[0]
    assert row["zone_behavior_state"] == "ACCEPTED_ABOVE_ZONE"
    assert row["accepted_above_at"] == "2026-05-08T00:03:00Z"
    assert row["active_forward_role"] == "RETEST_ZONE"


def test_broad_sell_side_zone_accepted_below_gets_state():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(side="SELL_SIDE", structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=_feed([106, 98, 97, 96]),
    )

    row = registry.iloc[0]
    assert row["zone_behavior_state"] == "ACCEPTED_BELOW_ZONE"
    assert row["accepted_below_at"] == "2026-05-08T00:03:00Z"
    assert row["active_forward_role"] == "RETEST_ZONE"


def test_broad_zone_resweep_increments_resweep_count():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map(structural_zone_mode="BROAD_STRUCTURAL_ZONE"),
        feed=pd.DataFrame(
            [
                _candle("2026-05-08T00:00:00Z", high=108, low=101, close=105),
                _candle("2026-05-08T00:01:00Z", high=112, low=104, close=109),
                _candle("2026-05-08T00:02:00Z", high=108, low=101, close=105),
                _candle("2026-05-08T00:03:00Z", high=113, low=104, close=109),
            ]
        ),
    )

    row = registry.iloc[0]
    assert row["first_sweep_at"] == "2026-05-08T00:01:00Z"
    assert row["resweep_count"] == 1
    assert row["zone_behavior_state"] == "REPEATED_SWEEP_ZONE"


def _liquidity_map(*, side="BUY_SIDE", structural_zone_mode="THIN_LEVEL"):
    return pd.DataFrame(
        [
            {
                "zone_id": "zone_000001",
                "created_at": "2026-05-08T00:00:00Z",
                "last_updated_at": "2026-05-08T00:00:00Z",
                "side": side,
                "zone_type": "CLUSTERED_BUY_SIDE_ZONE" if side == "BUY_SIDE" else "CLUSTERED_SELL_SIDE_ZONE",
                "price_lower": 100,
                "price_upper": 110,
                "price_mid": 105,
                "source_level_ids": "level_000001|level_000002",
                "source_timeframes": "CLUSTER|SESSION",
                "status": "ACTIVE",
                "confidence_score": 80,
                "confidence_tier": "HIGH",
                "touch_count": 0,
                "sweep_count": 0,
                "distance_from_close_pct": 0,
                "data_quality": "RAW",
                "invalidation_reason": "",
                "precision_status": "PRECISE",
                "zone_outer_lower": 100,
                "zone_outer_upper": 110,
                "zone_core_lower": 102,
                "zone_core_upper": 108,
                "zone_origin_start": "2026-05-08T00:00:00Z",
                "zone_origin_end": "2026-05-08T00:00:00Z",
                "structural_zone_mode": structural_zone_mode,
                "zone_behavior_state": "NONE",
                "active_forward_role": "FRESH_LIQUIDITY",
            }
        ]
    )


def _feed(closes):
    return pd.DataFrame(
        [
            _candle(
                f"2026-05-08T00:{idx:02d}:00Z",
                high=close + 1,
                low=close - 1,
                close=close,
            )
            for idx, close in enumerate(closes)
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
