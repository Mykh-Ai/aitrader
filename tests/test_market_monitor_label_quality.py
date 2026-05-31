from pathlib import Path

import pandas as pd

from market_monitor.label_quality import (
    LABEL_QUALITY_DESCRIPTIVE_READY,
    LABEL_QUALITY_TRACKING_ONLY,
    SUMMARY_COLUMNS,
    build_label_quality_report,
)
from market_monitor.label_taxonomy import (
    SWEEP_ACCEPTED,
    SWEEP_INVALID_SAMPLE,
    SWEEP_NO_LABEL,
    SWEEP_REJECTED,
    SWEEP_UNRESOLVED,
)


def test_label_quality_writes_report_and_summary_for_one_input_dir(tmp_path: Path):
    run_dir = _write_batch(
        tmp_path / "batch",
        [
            *[_row(SWEEP_REJECTED, idx) for idx in range(35)],
            *[_row(SWEEP_ACCEPTED, 100 + idx) for idx in range(18)],
            *[_row(SWEEP_UNRESOLVED, 200 + idx) for idx in range(32)],
            *[_row(SWEEP_NO_LABEL, 300 + idx, label_reason="low_precision_primary") for idx in range(5)],
        ],
    )
    output_dir = tmp_path / "quality"

    result = build_label_quality_report([run_dir], output_dir, run_timestamp="2026-05-31T00:00:00Z")

    assert result.markdown_path.exists()
    assert result.summary_path.exists()
    assert result.bucket_path.exists()
    assert result.behavior_path.exists()
    summary = pd.read_csv(result.summary_path)
    assert summary.columns.tolist() == SUMMARY_COLUMNS
    assert summary.loc[summary["label"] == SWEEP_REJECTED, "count"].iloc[0] == 35
    assert summary.loc[summary["label"] == SWEEP_ACCEPTED, "count"].iloc[0] == 18
    assert summary.loc[summary["label"] == "GLOBAL", "count"].iloc[0] == 90
    assert "Label Quality Report V1" in result.markdown_path.read_text(encoding="utf-8")


def test_label_quality_handles_multiple_input_dirs_and_computes_shares(tmp_path: Path):
    run_a = _write_batch(tmp_path / "batch_a", [_row(SWEEP_REJECTED, idx) for idx in range(20)])
    run_b = _write_batch(tmp_path / "batch_b", [_row(SWEEP_REJECTED, 100 + idx) for idx in range(10)])
    output_dir = tmp_path / "quality"

    result = build_label_quality_report([run_b, run_a], output_dir, run_timestamp="2026-05-31T00:00:00Z")

    summary = pd.read_csv(result.summary_path)
    rejected = summary[summary["label"] == SWEEP_REJECTED].iloc[0]
    assert rejected["count"] == 30
    assert rejected["share"] == 1.0
    assert rejected["quality_verdict"] == LABEL_QUALITY_DESCRIPTIVE_READY
    global_row = summary[summary["label"] == "GLOBAL"].iloc[0]
    assert global_row["count"] == 30


def test_label_quality_assigns_tracking_only_for_bucket_count_under_30(tmp_path: Path):
    run_dir = _write_batch(tmp_path / "batch", [_row(SWEEP_ACCEPTED, idx) for idx in range(29)])

    result = build_label_quality_report([run_dir], tmp_path / "quality")

    summary = pd.read_csv(result.summary_path)
    accepted = summary[summary["label"] == SWEEP_ACCEPTED].iloc[0]
    assert accepted["quality_verdict"] == LABEL_QUALITY_TRACKING_ONLY
    assert bool(accepted["tracking_only"]) is True


def test_label_quality_assigns_descriptive_ready_for_bucket_count_30_to_99(tmp_path: Path):
    run_dir = _write_batch(tmp_path / "batch", [_row(SWEEP_REJECTED, idx) for idx in range(30)])

    result = build_label_quality_report([run_dir], tmp_path / "quality")

    summary = pd.read_csv(result.summary_path)
    rejected = summary[summary["label"] == SWEEP_REJECTED].iloc[0]
    assert rejected["quality_verdict"] == LABEL_QUALITY_DESCRIPTIVE_READY
    assert bool(rejected["descriptive_ready"]) is True


def test_current_style_sample_global_is_descriptive_ready_and_backtester_blocked(tmp_path: Path):
    rows = [
        *[_row(SWEEP_REJECTED, idx) for idx in range(58)],
        *[_row(SWEEP_ACCEPTED, 100 + idx) for idx in range(18)],
        *[_row(SWEEP_UNRESOLVED, 200 + idx) for idx in range(82)],
        *[_row(SWEEP_NO_LABEL, 300 + idx, label_reason="low_precision_primary") for idx in range(35)],
    ]
    run_dir = _write_batch(tmp_path / "batch", rows)

    result = build_label_quality_report([run_dir], tmp_path / "quality")

    assert result.global_verdict == LABEL_QUALITY_DESCRIPTIVE_READY
    summary = pd.read_csv(result.summary_path)
    global_row = summary[summary["label"] == "GLOBAL"].iloc[0]
    assert bool(global_row["backtester_blocked"]) is True
    assert result.label_verdicts[SWEEP_ACCEPTED] == LABEL_QUALITY_TRACKING_ONLY
    assert result.label_verdicts[SWEEP_REJECTED] == LABEL_QUALITY_DESCRIPTIVE_READY
    assert result.label_verdicts[SWEEP_UNRESOLVED] == LABEL_QUALITY_DESCRIPTIVE_READY
    assert result.label_verdicts[SWEEP_INVALID_SAMPLE] == LABEL_QUALITY_TRACKING_ONLY


def test_label_quality_outputs_are_deterministic(tmp_path: Path):
    run_dir = _write_batch(tmp_path / "batch", [_row(SWEEP_REJECTED, idx) for idx in range(31)])
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"

    build_label_quality_report([run_dir], out_a, run_timestamp="2026-05-31T00:00:00Z")
    build_label_quality_report([run_dir], out_b, run_timestamp="2026-05-31T00:00:00Z")

    for filename in [
        "label_quality_report.md",
        "label_quality_summary.csv",
        "label_quality_by_bucket.csv",
        "label_quality_behavior_metrics.csv",
    ]:
        assert (out_a / filename).read_text(encoding="utf-8") == (
            out_b / filename
        ).read_text(encoding="utf-8")


def _write_batch(path: Path, rows: list[dict[str, object]]) -> Path:
    research_dir = path / "research_summary"
    research_dir.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(research_dir / "post_sweep_research_summary.csv", index=False)
    return path


def _row(label: str, idx: int, *, label_reason: str | None = None) -> dict[str, object]:
    side = "BUY_SIDE" if idx % 2 == 0 else "SELL_SIDE"
    event_day = 17 + (idx % 10)
    reason = label_reason or {
        SWEEP_REJECTED: "returned_and_closed_inside_within_10_bars",
        SWEEP_ACCEPTED: "maintained_close_beyond_swept_side",
        SWEEP_UNRESOLVED: "eligible_but_ambiguous",
        SWEEP_NO_LABEL: "low_precision_primary",
        SWEEP_INVALID_SAMPLE: "missing_required_field",
    }[label]
    return {
        "source_run_dir": "daily",
        "taxonomy_version": "SWEEP_LABEL_TAXONOMY_V1",
        "sweep_label": label,
        "label_reason": reason,
        "source_event_timestamp": f"2026-03-{event_day:02d}T00:{idx % 60:02d}:00Z",
        "market_move_id": f"move_{idx:06d}",
        "market_move_role": "PRIMARY",
        "market_move_event_count": 1,
        "side": side,
        "confidence_tier": "HIGH" if idx % 3 == 0 else "LOW",
        "source_timeframes": "CLUSTER|H1|H4|SESSION" if idx % 2 == 0 else "H1",
        "precision_status": "LOW_PRECISION" if label == SWEEP_NO_LABEL else "PRECISE",
        "has_h4_source": idx % 2 == 0,
        "has_session_source": idx % 3 == 0,
        "zone_width": 100,
        "zone_width_pct": 0.2,
        "observation_complete": label != SWEEP_NO_LABEL,
        "observation_bars_expected": 30,
        "observation_bars_available": 30 if label != SWEEP_NO_LABEL else 20,
        "max_excursion_beyond_zone": 150 + idx,
        "max_return_inside_zone": 25 + idx,
        "bars_inside_zone": 10,
        "bars_above_zone": 20 if side == "BUY_SIDE" else 0,
        "bars_below_zone": 20 if side == "SELL_SIDE" else 0,
        "first_close_inside_at": f"2026-03-{event_day:02d}T00:{(idx + 5) % 60:02d}:00Z",
        "post_delta_pct": 0.1,
        "post_oi_change": 5,
        "post_max_volume_zscore": 1.5,
        "post_max_abs_delta_zscore": 2.5,
        "data_quality": "RAW",
    }
