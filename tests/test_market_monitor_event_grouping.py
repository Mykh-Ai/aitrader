import json

import pandas as pd

from market_monitor.events import (
    GROUPING_WINDOW_MODE,
    MARKET_MOVE_GROUP_WINDOW_MINUTES,
    MARKET_MOVE_GROUP_COLUMNS,
    assign_market_move_groups,
    build_market_move_groups,
)


def test_single_unresolved_event_gets_primary_market_move_metadata():
    grouped = assign_market_move_groups(
        pd.DataFrame([_event("event_000001", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_1")])
    )

    row = grouped.iloc[0]
    assert row["market_move_id"].startswith("move_20260508_000100_BUY_SIDE_")
    assert row["market_move_role"] == "PRIMARY"
    assert row["market_move_event_count"] == 1
    assert row["group_start_timestamp"] == "2026-05-08T00:01:00Z"
    assert row["group_end_timestamp"] == "2026-05-08T00:01:00Z"
    assert row["group_span_minutes"] == 0
    assert row["grouping_window_mode"] == GROUPING_WINDOW_MODE


def test_same_side_same_timestamp_events_share_one_market_move_without_dropping_rows():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event("event_000001", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_1"),
                _event("event_000002", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_2"),
            ]
        )
    )

    assert len(grouped) == 2
    assert grouped["market_move_id"].nunique() == 1
    assert grouped["market_move_event_count"].tolist() == [2, 2]
    assert sorted(grouped["market_move_role"].tolist()) == ["PRIMARY", "SECONDARY"]
    assert grouped["group_span_minutes"].tolist() == [0, 0]


def test_same_side_events_within_anchored_two_minute_window_group_and_outside_window_split():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event("event_000001", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_1"),
                _event("event_000002", "2026-05-08T00:03:00Z", "BUY_SIDE", "zone_2"),
                _event("event_000003", "2026-05-08T00:06:00Z", "BUY_SIDE", "zone_3"),
            ]
        )
    )

    assert grouped["market_move_id"].nunique() == 2
    assert grouped["market_move_event_count"].tolist() == [2, 2, 1]
    assert grouped["group_span_minutes"].tolist() == [2, 2, 0]


def test_chained_events_beyond_anchored_window_split_without_dropping_rows():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event("event_000001", "2026-05-08T11:06:00Z", "BUY_SIDE", "zone_1"),
                _event("event_000002", "2026-05-08T11:08:00Z", "BUY_SIDE", "zone_2"),
                _event("event_000003", "2026-05-08T11:10:00Z", "BUY_SIDE", "zone_3"),
            ]
        )
    )

    assert len(grouped) == 3
    assert grouped["market_move_id"].nunique() == 2
    assert grouped["market_move_event_count"].tolist() == [2, 2, 1]
    assert grouped["market_move_role"].tolist().count("PRIMARY") == 2
    assert pd.to_numeric(grouped["group_span_minutes"]).max() <= MARKET_MOVE_GROUP_WINDOW_MINUTES


def test_opposite_sides_at_same_timestamp_remain_separate_market_moves():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event("event_000001", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_1"),
                _event("event_000002", "2026-05-08T00:01:00Z", "SELL_SIDE", "zone_2"),
            ]
        )
    )

    assert grouped["market_move_id"].nunique() == 2
    assert grouped["market_move_role"].tolist() == ["PRIMARY", "PRIMARY"]


def test_primary_market_move_event_uses_score_excursion_width_zone_and_event_tiebreaks():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event(
                    "event_000001",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_3",
                    confidence_score=80,
                    excursion_abs=20,
                    zone_width_pct=0.10,
                ),
                _event(
                    "event_000002",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_2",
                    confidence_score=80,
                    excursion_abs=20,
                    zone_width_pct=0.08,
                ),
                _event(
                    "event_000003",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_1",
                    confidence_score=79,
                    excursion_abs=99,
                    zone_width_pct=0.01,
                ),
            ]
        )
    )

    primary = grouped[grouped["market_move_role"] == "PRIMARY"].iloc[0]
    assert primary["event_id"] == "event_000002"
    assert primary["zone_id"] == "zone_2"


def test_every_group_has_exactly_one_primary_and_no_unresolved_group_missing_id():
    grouped = assign_market_move_groups(
        pd.DataFrame(
            [
                _event("event_000001", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_1"),
                _event("event_000002", "2026-05-08T00:01:00Z", "BUY_SIDE", "zone_2"),
                _event("event_000003", "2026-05-08T00:04:00Z", "BUY_SIDE", "zone_3"),
                _event("event_000004", "2026-05-08T00:04:00Z", "SELL_SIDE", "zone_4"),
            ]
        )
    )

    assert grouped["market_move_id"].fillna("").astype(str).str.len().gt(0).all()
    for _, group in grouped.groupby("market_move_id"):
        assert (group["market_move_role"] == "PRIMARY").sum() == 1


def test_market_move_groups_summary_is_written_from_raw_event_metadata():
    event_log = assign_market_move_groups(
        pd.DataFrame(
            [
                _event(
                    "event_000001",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_1",
                    confidence_score=80,
                    confidence_tier="HIGH",
                    precision_status="PRECISE",
                ),
                _event(
                    "event_000002",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_2",
                    confidence_score=70,
                    confidence_tier="MEDIUM",
                    precision_status="LOW_PRECISION",
                ),
            ]
        )
    )

    groups = build_market_move_groups(event_log)

    assert groups.columns.tolist() == MARKET_MOVE_GROUP_COLUMNS
    assert len(groups) == 1
    row = groups.iloc[0]
    assert row["group_start_timestamp"] == "2026-05-08T00:01:00Z"
    assert row["group_end_timestamp"] == "2026-05-08T00:01:00Z"
    assert row["group_span_minutes"] == 0
    assert row["grouping_window_minutes"] == MARKET_MOVE_GROUP_WINDOW_MINUTES
    assert row["grouping_window_mode"] == GROUPING_WINDOW_MODE
    assert row["event_count"] == 2
    assert row["zone_ids"] == "zone_1|zone_2"
    assert row["event_ids"] == "event_000001|event_000002"
    assert row["primary_event_id"] == "event_000001"
    assert row["primary_selection_reason"] == "highest_confidence_score"
    assert row["precision_statuses"] == "PRECISE|LOW_PRECISION"
    assert row["confidence_tiers"] == "HIGH|MEDIUM"
    components = json.loads(row["primary_selection_components_json"])
    assert components == {
        "selected_confidence_score": 80.0,
        "selected_event_id": "event_000001",
        "selected_excursion_abs": 15.0,
        "selected_zone_id": "zone_1",
        "selected_zone_width_pct": 0.1,
        "tie_breakers_used": [],
    }
    evidence = json.loads(row["evidence_json"])
    assert evidence["grouping_rule"] == "same_side_within_anchored_2_minute_window"
    assert evidence["grouping_window_mode"] == GROUPING_WINDOW_MODE
    assert evidence["event_count"] == 2


def test_primary_selection_diagnostics_record_tiebreakers_deterministically():
    event_log = assign_market_move_groups(
        pd.DataFrame(
            [
                _event(
                    "event_000001",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_2",
                    confidence_score=80,
                    excursion_abs=10,
                    zone_width_pct=0.10,
                ),
                _event(
                    "event_000002",
                    "2026-05-08T00:01:00Z",
                    "BUY_SIDE",
                    "zone_1",
                    confidence_score=80,
                    excursion_abs=12,
                    zone_width_pct=0.20,
                ),
            ]
        )
    )

    row = build_market_move_groups(event_log).iloc[0]
    assert row["primary_event_id"] == "event_000002"
    assert row["primary_selection_reason"] == "highest_excursion_abs_tiebreak"
    components = json.loads(row["primary_selection_components_json"])
    assert components["tie_breakers_used"] == ["highest_excursion_abs"]


def _event(
    event_id,
    event_timestamp,
    side,
    zone_id,
    *,
    confidence_score=80,
    confidence_tier="HIGH",
    excursion_abs=15,
    zone_width_pct=0.1,
    precision_status="PRECISE",
):
    evidence = {
        "confidence_score": confidence_score,
        "confidence_tier": confidence_tier,
        "price_lower": 100,
        "price_mid": 105,
        "price_upper": 110,
        "precision_status": precision_status,
        "zone_width_pct": zone_width_pct,
    }
    return {
        "event_id": event_id,
        "event_timestamp": event_timestamp,
        "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
        "zone_id": zone_id,
        "side": side,
        "price_before": 95,
        "event_high": 125,
        "event_low": 90,
        "event_close": 120,
        "excursion_abs": excursion_abs,
        "excursion_atr": 0,
        "volume_zscore": 2,
        "delta_zscore": -3,
        "oi_change": 1,
        "reaction_status": "UNRESOLVED",
        "evidence_json": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
        "data_quality": "RAW",
    }
