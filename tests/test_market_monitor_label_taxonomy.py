import json
from pathlib import Path

import pandas as pd

from market_monitor.label_taxonomy import (
    ALLOWED_SWEEP_LABELS,
    SWEEP_ACCEPTED,
    SWEEP_INVALID_SAMPLE,
    SWEEP_LABEL_TAXONOMY_COLUMNS,
    SWEEP_NO_LABEL,
    SWEEP_REJECTED,
    SWEEP_UNRESOLVED,
    build_sweep_label_frames,
    build_sweep_label_outputs,
)


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
    "pnl",
    "win",
    "loss",
    "profit",
}


def test_exactly_one_label_per_market_move_and_secondary_rows_are_context_only():
    observations = pd.DataFrame(
        [
            _observation("move_1", role="PRIMARY", observation_id="observation_1"),
            _observation("move_1", role="SECONDARY", observation_id="observation_2"),
        ]
    )

    labels, _ = build_sweep_label_frames(
        observations=observations,
        market_move_groups=_groups([_group("move_1")]),
    )

    assert len(labels) == 1
    assert labels["market_move_id"].tolist() == ["move_1"]
    assert labels.loc[0, "primary_observation_id"] == "observation_1"


def test_buy_side_rejected_semantics():
    labels, _ = build_sweep_label_frames(
        observations=pd.DataFrame(
            [
                _observation(
                    "move_buy_rejected",
                    side="BUY_SIDE",
                    first_close_inside_at="2026-05-08T00:06:00Z",
                    first_return_inside_at="2026-05-08T00:03:00Z",
                    bars_inside_zone=5,
                    max_return_inside_zone=6,
                    close_at_window_end=108,
                )
            ]
        ),
        market_move_groups=_groups([_group("move_buy_rejected")]),
    )

    assert labels.loc[0, "label"] == SWEEP_REJECTED


def test_sell_side_rejected_semantics():
    labels, _ = build_sweep_label_frames(
        observations=pd.DataFrame(
            [
                _observation(
                    "move_sell_rejected",
                    side="SELL_SIDE",
                    first_close_inside_at="2026-05-08T00:06:00Z",
                    first_return_inside_at="2026-05-08T00:03:00Z",
                    bars_inside_zone=5,
                    max_return_inside_zone=6,
                    close_at_window_end=102,
                )
            ]
        ),
        market_move_groups=_groups([_group("move_sell_rejected", side="SELL_SIDE")]),
    )

    assert labels.loc[0, "label"] == SWEEP_REJECTED


def test_buy_side_accepted_semantics():
    labels, _ = build_sweep_label_frames(
        observations=pd.DataFrame(
            [
                _observation(
                    "move_buy_accepted",
                    side="BUY_SIDE",
                    first_close_inside_at="",
                    first_return_inside_at="",
                    bars_inside_zone=2,
                    bars_above_zone=24,
                    max_return_inside_zone=4,
                    close_at_window_end=111,
                )
            ]
        ),
        market_move_groups=_groups([_group("move_buy_accepted")]),
    )

    assert labels.loc[0, "label"] == SWEEP_ACCEPTED


def test_sell_side_accepted_semantics():
    labels, _ = build_sweep_label_frames(
        observations=pd.DataFrame(
            [
                _observation(
                    "move_sell_accepted",
                    side="SELL_SIDE",
                    first_close_inside_at="",
                    first_return_inside_at="",
                    bars_inside_zone=2,
                    bars_below_zone=24,
                    max_return_inside_zone=4,
                    close_at_window_end=99,
                )
            ]
        ),
        market_move_groups=_groups([_group("move_sell_accepted", side="SELL_SIDE")]),
    )

    assert labels.loc[0, "label"] == SWEEP_ACCEPTED


def test_unresolved_fallback_for_clean_ambiguous_market_move():
    labels, _ = build_sweep_label_frames(
        observations=pd.DataFrame(
            [
                _observation(
                    "move_unresolved",
                    first_close_inside_at="2026-05-08T00:20:00Z",
                    bars_inside_zone=2,
                    bars_above_zone=10,
                    max_return_inside_zone=2,
                    close_at_window_end=115,
                )
            ]
        ),
        market_move_groups=_groups([_group("move_unresolved")]),
    )

    assert labels.loc[0, "label"] == SWEEP_UNRESOLVED


def test_no_label_exclusions_for_incomplete_low_precision_mixed_precision_and_large_group():
    observations = pd.DataFrame(
        [
            _observation("move_incomplete", observation_complete=False),
            _observation("move_low", precision_status="LOW_PRECISION"),
            _observation("move_mixed"),
            _observation("move_large", market_move_event_count=4),
        ]
    )
    groups = _groups(
        [
            _group("move_incomplete"),
            _group("move_low", precision_statuses="LOW_PRECISION"),
            _group("move_mixed", precision_statuses="PRECISE|LOW_PRECISION"),
            _group("move_large", event_count=4),
        ]
    )

    labels, _ = build_sweep_label_frames(observations=observations, market_move_groups=groups)

    assert labels["label"].tolist() == [
        SWEEP_NO_LABEL,
        SWEEP_NO_LABEL,
        SWEEP_NO_LABEL,
        SWEEP_NO_LABEL,
    ]


def test_invalid_sample_for_missing_required_fields_and_too_wide_precision():
    observations = pd.DataFrame(
        [
            _observation("move_missing_side", side=""),
            _observation("move_too_wide", precision_status="TOO_WIDE"),
            _observation("move_no_primary", role="SECONDARY"),
            _observation("move_multi_primary", observation_id="observation_a"),
            _observation("move_multi_primary", observation_id="observation_b"),
        ]
    )
    groups = _groups(
        [
            _group("move_missing_side"),
            _group("move_too_wide", precision_statuses="TOO_WIDE"),
            _group("move_no_primary"),
            _group("move_multi_primary"),
        ]
    )

    labels, _ = build_sweep_label_frames(observations=observations, market_move_groups=groups)

    assert set(labels["label"]) == {SWEEP_INVALID_SAMPLE}


def test_bar_31_style_extra_field_does_not_affect_thirty_bar_label():
    base = pd.DataFrame([_observation("move_1")])
    with_extra = base.copy()
    with_extra["bar_31_close"] = 999999

    labels_a, _ = build_sweep_label_frames(
        observations=base,
        market_move_groups=_groups([_group("move_1")]),
    )
    labels_b, _ = build_sweep_label_frames(
        observations=with_extra,
        market_move_groups=_groups([_group("move_1")]),
    )

    assert labels_a["label"].tolist() == labels_b["label"].tolist()
    assert labels_a["label_evidence_json"].tolist() == labels_b["label_evidence_json"].tolist()


def test_label_evidence_json_is_deterministic_and_has_only_allowed_labels():
    labels_a, _ = build_sweep_label_frames(
        observations=pd.DataFrame([_observation("move_1")]),
        market_move_groups=_groups([_group("move_1")]),
    )
    labels_b, _ = build_sweep_label_frames(
        observations=pd.DataFrame([_observation("move_1")]),
        market_move_groups=_groups([_group("move_1")]),
    )

    assert labels_a.loc[0, "label_evidence_json"] == labels_b.loc[0, "label_evidence_json"]
    assert set(labels_a["label"]).issubset(ALLOWED_SWEEP_LABELS)
    evidence = json.loads(labels_a.loc[0, "label_evidence_json"])
    assert list(evidence) == sorted(evidence)
    assert evidence["reaction_label_is_not_signal"] is True


def test_output_files_are_written_with_no_forbidden_columns(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame([_observation("move_1")]).to_csv(run_dir / "post_sweep_observation.csv", index=False)
    _groups([_group("move_1")]).to_csv(run_dir / "market_move_groups.csv", index=False)

    result = build_sweep_label_outputs(run_dir)

    assert result.taxonomy_path.exists()
    assert result.summary_path.exists()
    labels = pd.read_csv(result.taxonomy_path)
    assert labels.columns.tolist() == SWEEP_LABEL_TAXONOMY_COLUMNS
    assert {column.lower() for column in labels.columns}.isdisjoint(FORBIDDEN_COLUMNS)


def _observation(
    market_move_id: str,
    *,
    role: str = "PRIMARY",
    observation_id: str = "observation_1",
    side: str = "BUY_SIDE",
    observation_complete=True,
    precision_status: str = "PRECISE",
    market_move_event_count: int = 1,
    first_return_inside_at: str = "2026-05-08T00:03:00Z",
    first_close_inside_at: str = "2026-05-08T00:06:00Z",
    bars_inside_zone: int = 5,
    bars_above_zone: int = 4,
    bars_below_zone: int = 0,
    max_return_inside_zone: float = 6,
    close_at_window_end: float = 108,
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "source_event_id": f"event_{market_move_id}",
        "source_event_timestamp": "2026-05-08T00:01:00Z",
        "market_move_id": market_move_id,
        "market_move_role": role,
        "market_move_event_count": market_move_event_count,
        "group_start_timestamp": "2026-05-08T00:01:00Z",
        "group_end_timestamp": "2026-05-08T00:01:00Z",
        "group_span_minutes": 0,
        "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
        "zone_id": "zone_1",
        "side": side,
        "zone_price_lower": 100,
        "zone_price_upper": 110,
        "zone_price_mid": 105,
        "confidence_score": 80,
        "confidence_tier": "HIGH",
        "zone_width": 10,
        "zone_width_pct": 0.1,
        "precision_status": precision_status,
        "observation_start_timestamp": "2026-05-08T00:02:00Z",
        "observation_bars_expected": 30,
        "observation_bars_available": 30,
        "observation_complete": observation_complete,
        "first_return_inside_at": first_return_inside_at,
        "first_close_inside_at": first_close_inside_at,
        "bars_inside_zone": bars_inside_zone,
        "bars_above_zone": bars_above_zone,
        "bars_below_zone": bars_below_zone,
        "max_return_inside_zone": max_return_inside_zone,
        "max_excursion_beyond_zone": 20,
        "close_at_window_end": close_at_window_end,
        "data_quality": "RAW",
    }


def _group(
    market_move_id: str,
    *,
    side: str = "BUY_SIDE",
    precision_statuses: str = "PRECISE",
    event_count: int = 1,
) -> dict[str, object]:
    return {
        "market_move_id": market_move_id,
        "group_start_timestamp": "2026-05-08T00:01:00Z",
        "group_end_timestamp": "2026-05-08T00:01:00Z",
        "group_span_minutes": 0,
        "grouping_window_minutes": 2,
        "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
        "event_timestamp": "2026-05-08T00:01:00Z",
        "side": side,
        "primary_event_id": f"event_{market_move_id}",
        "primary_zone_id": "zone_1",
        "event_count": event_count,
        "precision_statuses": precision_statuses,
        "data_quality": "RAW",
    }


def _groups(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)
