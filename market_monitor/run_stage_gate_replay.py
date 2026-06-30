from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from market_monitor.policy_replay_fixed_stops import (
    SELECTED_STOP_TARGET_POLICY,
    TP1_BE_WITH_SELECTED_STOP_POLICY,
    _evaluate_forward_path,
    _load_feed_range,
    _selected_stop_outcome,
    _target_distance,
    _tp1_outcome,
    _tp1_price,
)
from market_monitor.run_qualified_h1_replay_38j_window import _build_h1_bars, _load_feed
from market_monitor.run_sequence_window_h1_replay import run_sequence_window_replay


RUN_VERSION = "SHI_RESET_38P_FULL_WINDOW_STAGE_GATE_REPLAY_V0"
DEFAULT_OUT_DIR = "market_monitor_runs/SHI_RESET_38P_full_window_stage_gate_replay_v0"
STOP_BUFFER_USD = 0.0

SETUP_ROW_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "trigger_status",
    "source_time_precision",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "corrected_research_classification",
    "stage_0_monitor_found",
    "stage_1_raw_context_or_raw_sweep",
    "stage_2_qualified_h1_sweep",
    "stage_3_qualified_h1_failed_reclaim",
    "stage_4_sequence_linked_setup",
    "stage_5_policy_replay_allowed",
    "final_stage_reached",
    "stage_gate_status",
    "stage_gate_reject_reason",
    "immediate_entry_valid",
    "policy_replay_allowed",
    "evidence_summary",
]

SEQUENCE_LINK_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "corrected_research_classification",
    "qualified_sequence_found",
    "qualified_h1_sweep_ts",
    "qualified_h1_failed_reclaim",
    "reclaim_h1_close_ts",
    "entry_candidate_ts",
    "entry_candidate_price",
    "swept_level",
    "swept_level_type",
    "sweep_h1_high",
    "sweep_h1_low",
    "sweep_h1_close",
    "sweep_h1_volume",
    "sweep_volume_ratio",
    "level_age_h1_bars",
    "reaction_abs",
    "penetration_abs",
    "wick_quality",
    "reclaim_bar_number_after_sweep",
    "sequence_age_h1_bars_at_setup",
    "sequence_valid_for_setup",
    "setup_review_lag_h1_bars",
    "sequence_reject_reason",
    "stage_gate_status",
    "evidence_summary",
]

POLICY_COLUMNS = [
    "setup_id",
    "setup_review_ts",
    "entry_candidate_ts",
    "entry_candidate_price",
    "setup_type",
    "direction_context",
    "policy_name",
    "selected_stop_reference",
    "selected_stop_type",
    "target_reference",
    "stop_distance_usd",
    "target_distance_usd",
    "r_to_target",
    "tp1_price",
    "first_event",
    "first_event_ts",
    "target_touched_at",
    "selected_stop_touched_at",
    "tp1_touched_at",
    "be_touched_at",
    "policy_outcome_label",
    "policy_replay_allowed",
    "evidence_summary",
]

FAILURE_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "corrected_research_classification",
    "failed_stage",
    "reject_reason",
    "raw_sweep_present",
    "qualified_h1_sweep",
    "qualified_h1_failed_reclaim",
    "sequence_valid_for_setup",
    "policy_replay_allowed",
    "evidence_summary",
]


@dataclass(frozen=True)
class StageGateReplayResult:
    output_dir: Path
    setup_rows_path: Path
    sequence_links_path: Path
    policy_results_path: Path
    failures_path: Path
    summary_path: Path
    manifest_path: Path
    audit_path: Path
    setup_count: int
    policy_allowed_count: int
    policy_result_count: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run 38P full-window stage-gated research replay.")
    parser.add_argument("--classification", required=True, help="Path to wider_setup_classification_corrected.csv.")
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Output directory for 38P artifacts.")
    parser.add_argument(
        "--audit-path",
        default="research/canonical/SHI_RESET_38P_FULL_WINDOW_STAGE_GATE_REPLAY_AUDIT_2026_06_30.md",
        help="Canonical audit markdown path.",
    )
    args = parser.parse_args(argv)

    result = run_stage_gate_replay(
        classification_path=Path(args.classification),
        feed_dir=Path(args.feed_dir),
        start=date.fromisoformat(args.start),
        end=date.fromisoformat(args.end),
        output_dir=Path(args.out_dir),
        audit_path=Path(args.audit_path),
    )
    print(
        "38P stage-gate replay complete: "
        f"setups={result.setup_count} "
        f"policy_allowed={result.policy_allowed_count} "
        f"policy_rows={result.policy_result_count} "
        f"summary={result.summary_path}"
    )
    return 0


def run_stage_gate_replay(
    *,
    classification_path: Path,
    feed_dir: Path,
    start: date,
    end: date,
    output_dir: Path,
    audit_path: Path,
) -> StageGateReplayResult:
    classification = pd.read_csv(classification_path)
    feed = _load_feed(feed_dir, start, end)
    h1 = _build_h1_bars(feed)
    events, links = run_sequence_window_replay(classification=classification, h1=h1)
    frames = build_stage_gate_frames(
        classification=classification,
        sequence_events=events,
        sequence_links=links,
        feed_dir=feed_dir,
        replay_end_ts=pd.Timestamp(f"{end.isoformat()}T23:59:00Z"),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    setup_rows_path = output_dir / "stage_gate_setup_rows.csv"
    sequence_links_path = output_dir / "stage_gate_sequence_links.csv"
    policy_results_path = output_dir / "stage_gate_policy_replay_results.csv"
    failures_path = output_dir / "stage_gate_failures.csv"
    summary_path = output_dir / "stage_gate_summary.md"
    manifest_path = output_dir / "stage_gate_manifest.json"

    frames["setup_rows"].to_csv(setup_rows_path, index=False)
    frames["sequence_links"].to_csv(sequence_links_path, index=False)
    frames["policy_results"].to_csv(policy_results_path, index=False)
    frames["failures"].to_csv(failures_path, index=False)
    summary = _summary_text(frames=frames, start=start, end=end)
    summary_path.write_text(summary, encoding="utf-8")
    audit_path.write_text(_audit_text(summary), encoding="utf-8")

    setup_rows = frames["setup_rows"]
    policy_results = frames["policy_results"]
    manifest = {
        "run_version": RUN_VERSION,
        "research_only": True,
        "uses_future_labels": False,
        "uses_backtester": False,
        "uses_executor": False,
        "uses_orders": False,
        "uses_live_trading": False,
        "uses_entries_exits_module": False,
        "uses_position_sizing": False,
        "live_readiness_claim": False,
        "strategy_promotion": False,
        "changes_setup_detection_rules": False,
        "changes_setup_builder_rules": False,
        "raw_sweep_alone_can_pass_policy_replay": False,
        "entry_timestamp_source": "entry_candidate_ts_from_qualified_failed_reclaim",
        "setup_timestamp_semantics": "review_time_only",
        "classification_path": str(classification_path),
        "feed_dir": str(feed_dir),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "setup_rows": int(len(setup_rows)),
        "policy_replay_allowed_rows": int(_count_true(setup_rows, "policy_replay_allowed")),
        "policy_result_rows": int(len(policy_results)),
        "outputs": {
            "stage_gate_setup_rows_csv": str(setup_rows_path),
            "stage_gate_sequence_links_csv": str(sequence_links_path),
            "stage_gate_policy_replay_results_csv": str(policy_results_path),
            "stage_gate_failures_csv": str(failures_path),
            "stage_gate_summary_md": str(summary_path),
            "stage_gate_manifest_json": str(manifest_path),
            "canonical_audit_md": str(audit_path),
        },
        "repo_commit": _repo_commit(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return StageGateReplayResult(
        output_dir=output_dir,
        setup_rows_path=setup_rows_path,
        sequence_links_path=sequence_links_path,
        policy_results_path=policy_results_path,
        failures_path=failures_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        audit_path=audit_path,
        setup_count=int(len(setup_rows)),
        policy_allowed_count=int(_count_true(setup_rows, "policy_replay_allowed")),
        policy_result_count=int(len(policy_results)),
    )


def build_stage_gate_frames(
    *,
    classification: pd.DataFrame,
    sequence_events: pd.DataFrame,
    sequence_links: pd.DataFrame,
    feed_dir: Path,
    replay_end_ts: pd.Timestamp,
) -> dict[str, pd.DataFrame]:
    setup_rows: list[dict[str, object]] = []
    link_rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []
    policy_rows: list[dict[str, object]] = []

    events_by_setup = {key: frame for key, frame in sequence_events.groupby("setup_id", dropna=False)} if not sequence_events.empty else {}
    links_by_setup = {str(row["setup_id"]): row for _, row in sequence_links.iterrows()} if not sequence_links.empty else {}

    for _, setup in classification.iterrows():
        setup_id = _cell(setup.get("setup_id"))
        link = links_by_setup.get(setup_id, pd.Series(dtype=object))
        events = events_by_setup.get(setup_id, pd.DataFrame())
        stage = _stage_status(setup=setup, link=link, events=events)
        setup_rows.append(_setup_row(setup=setup, link=link, stage=stage))
        link_rows.append(_sequence_link_row(link=link, stage=stage))
        if not stage["policy_allowed"]:
            failure_rows.append(_failure_row(setup=setup, events=events, link=link, stage=stage))
        else:
            policy_rows.extend(_policy_rows(setup=setup, link=link, feed_dir=feed_dir, replay_end_ts=replay_end_ts))

    return {
        "setup_rows": pd.DataFrame(setup_rows, columns=SETUP_ROW_COLUMNS),
        "sequence_links": pd.DataFrame(link_rows, columns=SEQUENCE_LINK_COLUMNS),
        "policy_results": pd.DataFrame(policy_rows, columns=POLICY_COLUMNS),
        "failures": pd.DataFrame(failure_rows, columns=FAILURE_COLUMNS),
    }


def _stage_status(*, setup: pd.Series, link: pd.Series, events: pd.DataFrame) -> dict[str, object]:
    monitor_found = True
    raw_context = _raw_context_present(setup, events)
    qualified_sweep = _boolish(link.get("qualified_sequence_found")) or _events_true(events, "qualified_h1_sweep")
    qualified_reclaim = _boolish(link.get("qualified_h1_failed_reclaim")) or _events_true(events, "qualified_h1_failed_reclaim")
    sequence_linked = _boolish(link.get("qualified_sequence_found"))
    sequence_valid = _boolish(link.get("sequence_valid_for_setup"))
    policy_allowed = bool(sequence_valid)
    flags = [
        ("STAGE_0_MONITOR_FOUND", monitor_found),
        ("STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP", raw_context),
        ("STAGE_2_QUALIFIED_H1_SWEEP", qualified_sweep),
        ("STAGE_3_QUALIFIED_H1_FAILED_RECLAIM", qualified_reclaim),
        ("STAGE_4_SEQUENCE_LINKED_SETUP", sequence_linked),
        ("STAGE_5_POLICY_REPLAY_ALLOWED", policy_allowed),
    ]
    final = "NO_STAGE_REACHED"
    failed = ""
    for name, passed in flags:
        if passed:
            final = name
            continue
        failed = name
        break
    reject = "" if policy_allowed else _reject_reason(failed=failed, link=link, events=events)
    return {
        "monitor_found": monitor_found,
        "raw_context": raw_context,
        "qualified_sweep": qualified_sweep,
        "qualified_reclaim": qualified_reclaim,
        "sequence_linked": sequence_linked,
        "sequence_valid": sequence_valid,
        "policy_allowed": policy_allowed,
        "final_stage": final,
        "failed_stage": failed,
        "status": "POLICY_REPLAY_ALLOWED" if policy_allowed else "REJECTED_BEFORE_POLICY_REPLAY",
        "reject_reason": reject,
    }


def _setup_row(*, setup: pd.Series, link: pd.Series, stage: dict[str, object]) -> dict[str, object]:
    return {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_formed_at": _cell(setup.get("setup_formed_at")),
        "setup_type": _cell(setup.get("setup_type")),
        "direction_context": _cell(setup.get("direction_context")),
        "trigger_status": _cell(setup.get("trigger_status")),
        "source_time_precision": _cell(setup.get("source_time_precision")),
        "setup_reference_level": _round(setup.get("setup_reference_level")),
        "actual_setup_price": _round(setup.get("actual_setup_price")),
        "tradable_entry_anchor": _round(link.get("entry_candidate_price")) if stage["policy_allowed"] else "",
        "corrected_research_classification": _manual_classification(setup),
        "stage_0_monitor_found": _bool_cell(stage["monitor_found"]),
        "stage_1_raw_context_or_raw_sweep": _bool_cell(stage["raw_context"]),
        "stage_2_qualified_h1_sweep": _bool_cell(stage["qualified_sweep"]),
        "stage_3_qualified_h1_failed_reclaim": _bool_cell(stage["qualified_reclaim"]),
        "stage_4_sequence_linked_setup": _bool_cell(stage["sequence_linked"]),
        "stage_5_policy_replay_allowed": _bool_cell(stage["policy_allowed"]),
        "final_stage_reached": stage["final_stage"],
        "stage_gate_status": stage["status"],
        "stage_gate_reject_reason": stage["reject_reason"],
        "immediate_entry_valid": _bool_cell(stage["policy_allowed"]),
        "policy_replay_allowed": _bool_cell(stage["policy_allowed"]),
        "evidence_summary": _stage_evidence(setup=setup, link=link, stage=stage),
    }


def _sequence_link_row(*, link: pd.Series, stage: dict[str, object]) -> dict[str, object]:
    row = {column: _cell(link.get(column)) for column in SEQUENCE_LINK_COLUMNS if column not in {"stage_gate_status"}}
    row["stage_gate_status"] = stage["status"]
    return row


def _failure_row(*, setup: pd.Series, events: pd.DataFrame, link: pd.Series, stage: dict[str, object]) -> dict[str, object]:
    return {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_formed_at": _cell(setup.get("setup_formed_at")),
        "setup_type": _cell(setup.get("setup_type")),
        "corrected_research_classification": _manual_classification(setup),
        "failed_stage": stage["failed_stage"],
        "reject_reason": stage["reject_reason"],
        "raw_sweep_present": _bool_cell(_events_true(events, "raw_sweep")),
        "qualified_h1_sweep": _bool_cell(stage["qualified_sweep"]),
        "qualified_h1_failed_reclaim": _bool_cell(stage["qualified_reclaim"]),
        "sequence_valid_for_setup": _bool_cell(stage["sequence_valid"]),
        "policy_replay_allowed": _bool_cell(stage["policy_allowed"]),
        "evidence_summary": _stage_evidence(setup=setup, link=link, stage=stage),
    }


def _policy_rows(*, setup: pd.Series, link: pd.Series, feed_dir: Path, replay_end_ts: pd.Timestamp) -> list[dict[str, object]]:
    entry_ts = _ts(link.get("entry_candidate_ts"))
    entry = _float_value(link.get("entry_candidate_price"))
    direction = _cell(setup.get("direction_context")).upper()
    stop_anchor = _sequence_linked_stop_anchor(setup=setup, link=link, direction=direction, entry=entry)
    stop = stop_anchor["selected_stop"]
    target = _target_zone(setup.get("target_reference"))
    forward = _load_feed_range(feed_root=feed_dir, start_ts=entry_ts + pd.Timedelta(minutes=1), end_ts=replay_end_ts)
    stop_distance = abs(stop - entry) if not pd.isna(stop) and not pd.isna(entry) else float("nan")
    target_distance = _target_distance(direction=direction, entry=entry, target=target)
    r_to_target = target_distance / stop_distance if _positive(stop_distance) and not pd.isna(target_distance) else float("nan")
    tp1_price = _tp1_price(direction=direction, entry=entry, stop_distance=stop_distance)
    path = _evaluate_forward_path(
        forward=forward,
        direction=direction,
        entry=entry,
        selected_stop=stop,
        target=target,
        stop_distance=stop_distance,
        tp1_price=tp1_price,
    )
    base = {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_review_ts": _cell(setup.get("setup_formed_at")),
        "entry_candidate_ts": _format_ts(entry_ts),
        "entry_candidate_price": _round(entry),
        "setup_type": _cell(setup.get("setup_type")),
        "direction_context": direction,
        "selected_stop_reference": _round(stop),
        "selected_stop_type": stop_anchor["selected_stop_type"],
        "target_reference": _cell(setup.get("target_reference")),
        "stop_distance_usd": _round(stop_distance),
        "target_distance_usd": _round(target_distance),
        "r_to_target": _round(r_to_target),
        "tp1_price": _round(tp1_price),
        "target_touched_at": _format_optional(path.get("target_touched_at")),
        "selected_stop_touched_at": _format_optional(path.get("stop_touched_at")),
        "tp1_touched_at": _format_optional(path.get("tp1_touched_at")),
        "be_touched_at": _format_optional(path.get("be_hit_after_tp1_at")),
        "policy_replay_allowed": "true",
    }
    selected_first = _cell(path.get("selected_stop_first_event"))
    tp1_first = _cell(path.get("tp1_policy_first_event"))
    return [
        {
            **base,
            "policy_name": SELECTED_STOP_TARGET_POLICY,
            "first_event": selected_first,
            "first_event_ts": _event_ts(path, selected_first),
            "policy_outcome_label": _selected_stop_outcome(
                path=path,
                unresolved=_unresolved(direction, entry, stop, target),
                insufficient=forward.empty,
            ),
            "evidence_summary": _policy_evidence(setup=setup, link=link, policy=SELECTED_STOP_TARGET_POLICY, stop_anchor=stop_anchor),
        },
        {
            **base,
            "policy_name": TP1_BE_WITH_SELECTED_STOP_POLICY,
            "first_event": tp1_first,
            "first_event_ts": _event_ts(path, tp1_first),
            "policy_outcome_label": _tp1_outcome(
                path=path,
                unresolved=_unresolved(direction, entry, stop, target),
                insufficient=forward.empty,
            ),
            "evidence_summary": _policy_evidence(setup=setup, link=link, policy=TP1_BE_WITH_SELECTED_STOP_POLICY, stop_anchor=stop_anchor),
        },
    ]


def _raw_context_present(setup: pd.Series, events: pd.DataFrame) -> bool:
    text = " ".join(
        [
            _cell(setup.get("source_time_precision")),
            _cell(setup.get("evidence_summary")),
            _cell(setup.get("market_state")),
            _cell(setup.get("setup_type")),
        ]
    ).lower()
    return _events_true(events, "raw_sweep") or any(token in text for token in ["raw", "sweep", "markdown", "candidate", "window"])


def _reject_reason(*, failed: str, link: pd.Series, events: pd.DataFrame) -> str:
    if failed == "STAGE_2_QUALIFIED_H1_SWEEP":
        return _cell(link.get("sequence_reject_reason")) or "raw_context_without_qualified_h1_sweep"
    if failed == "STAGE_3_QUALIFIED_H1_FAILED_RECLAIM":
        return _cell(link.get("sequence_reject_reason")) or "qualified_sweep_without_failed_reclaim"
    if failed == "STAGE_4_SEQUENCE_LINKED_SETUP":
        return _cell(link.get("sequence_reject_reason")) or "qualified_failed_reclaim_not_linked_to_setup"
    if failed == "STAGE_5_POLICY_REPLAY_ALLOWED":
        return _cell(link.get("sequence_reject_reason")) or "sequence_not_valid_for_setup"
    if failed:
        return failed.lower()
    return _cell(link.get("sequence_reject_reason")) or "rejected_before_policy_replay"


def _stage_evidence(*, setup: pd.Series, link: pd.Series, stage: dict[str, object]) -> str:
    if stage["policy_allowed"]:
        return (
            "stage-gated research candidate; setup_formed_at_is_review_time; "
            f"entry_candidate_ts={_cell(link.get('entry_candidate_ts'))}; raw_sweep_alone_is_not_entry_trigger"
        )
    return (
        f"rejected at {stage['failed_stage']}; {stage['reject_reason']}; "
        "setup_row_is_not_entry_by_default; raw_sweep_alone_is_not_entry_trigger"
    )


def _policy_evidence(*, setup: pd.Series, link: pd.Series, policy: str, stop_anchor: dict[str, object]) -> str:
    return (
        f"policy={policy}; policy_replay_allowed_by_sequence_gate=true; "
        f"setup_review_ts={_cell(setup.get('setup_formed_at'))}; "
        f"entry_candidate_ts={_cell(link.get('entry_candidate_ts'))}; "
        "entry_candidate_price_from_qualified_failed_reclaim=true; setup_formed_at_not_used_as_entry=true; "
        f"stop_anchor_source={stop_anchor['selected_stop_type']}; "
        f"stop_anchor_reason={stop_anchor['stop_anchor_reason']}; "
        f"rejected_stop_reference={stop_anchor['rejected_stop_reference']}; "
        f"stop_buffer_usd={stop_anchor['stop_buffer_usd']}; "
        "selected_stop_before_tp1_terminal=true"
    )



def _sequence_linked_stop_anchor(*, setup: pd.Series, link: pd.Series, direction: str, entry: float) -> dict[str, object]:
    original_stop = _float_value(setup.get("selected_research_stop_reference"))
    original_type = _cell(setup.get("selected_research_stop_type")) or "original_selected_stop"
    sweep_high = _float_value(link.get("sweep_h1_high"))
    sweep_low = _float_value(link.get("sweep_h1_low"))
    if direction == "DOWN" and not pd.isna(sweep_high):
        minimum_stop = sweep_high + STOP_BUFFER_USD
        if not pd.isna(original_stop) and original_stop >= minimum_stop:
            return {
                "selected_stop": original_stop,
                "selected_stop_type": original_type,
                "stop_anchor_reason": "STRUCTURAL_STOP_OUTSIDE_SWEEP_RANGE",
                "rejected_stop_reference": "",
                "stop_buffer_usd": STOP_BUFFER_USD,
            }
        return {
            "selected_stop": minimum_stop,
            "selected_stop_type": "sweep_h1_high_stop",
            "stop_anchor_reason": "INVALID_STOP_INSIDE_SWEEP_RANGE: structural stop below sweep_h1_high; using sweep_h1_high_plus_buffer",
            "rejected_stop_reference": _round(original_stop),
            "stop_buffer_usd": STOP_BUFFER_USD,
        }
    if direction == "UP" and not pd.isna(sweep_low):
        maximum_stop = sweep_low - STOP_BUFFER_USD
        if not pd.isna(original_stop) and original_stop <= maximum_stop:
            return {
                "selected_stop": original_stop,
                "selected_stop_type": original_type,
                "stop_anchor_reason": "STRUCTURAL_STOP_OUTSIDE_SWEEP_RANGE",
                "rejected_stop_reference": "",
                "stop_buffer_usd": STOP_BUFFER_USD,
            }
        return {
            "selected_stop": maximum_stop,
            "selected_stop_type": "sweep_h1_low_stop",
            "stop_anchor_reason": "INVALID_STOP_INSIDE_SWEEP_RANGE: structural stop above sweep_h1_low; using sweep_h1_low_minus_buffer",
            "rejected_stop_reference": _round(original_stop),
            "stop_buffer_usd": STOP_BUFFER_USD,
        }
    return {
        "selected_stop": original_stop,
        "selected_stop_type": original_type,
        "stop_anchor_reason": "NO_SEQUENCE_SWEEP_EXTREME_AVAILABLE; using original selected stop",
        "rejected_stop_reference": "",
        "stop_buffer_usd": STOP_BUFFER_USD,
    }
def _target_zone(value: object) -> dict[str, float] | None:
    text = _cell(value)
    number = _float_value(text)
    if not pd.isna(number):
        return {"lower": number, "upper": number}
    parts = text.split(":")
    if len(parts) == 3 and "-" in parts[2]:
        lower, upper = parts[2].split("-", 1)
        low = _float_value(lower)
        high = _float_value(upper)
        if not pd.isna(low) and not pd.isna(high):
            return {"lower": min(low, high), "upper": max(low, high)}
    return None


def _summary_text(*, frames: dict[str, pd.DataFrame], start: date, end: date) -> str:
    setup_rows = frames["setup_rows"]
    links = frames["sequence_links"]
    policy = frames["policy_results"]
    failures = frames["failures"]
    valid = setup_rows[setup_rows["policy_replay_allowed"].astype(str).str.lower() == "true"]
    focus_ts = {
        "2026-05-26T16:59:00+00:00",
        "2026-05-27T05:59:00+00:00",
        "2026-06-01T00:59:00+00:00",
        "2026-06-05T16:59:00+00:00",
        "2026-06-09T17:59:00+00:00",
    }
    focus = setup_rows[setup_rows["setup_formed_at"].isin(focus_ts)]
    reproduced = bool(
        (
            (links["setup_id"] == "setup_000002")
            & (links["entry_candidate_ts"] == "2026-05-26T15:59:00Z")
            & (links["sequence_valid_for_setup"].astype(str).str.lower() == "true")
        ).any()
    )
    lines = [
        "# SHI RESET 38P Full Window Stage-Gate Replay",
        "",
        "Research-only replay. This is not live-ready and does not use Executor, orders, live trading, entries/exits modules, position sizing, or strategy promotion.",
        "",
        f"- Window: {start.isoformat()} -> {end.isoformat()}",
        f"- Total setup rows found: {len(setup_rows)}",
        f"- Count by setup_type: {_counts(setup_rows, 'setup_type')}",
        f"- Count by corrected_research_classification: {_counts(setup_rows, 'corrected_research_classification')}",
        f"- Count by final_stage_reached: {_counts(setup_rows, 'final_stage_reached')}",
        f"- Count passing STAGE_1: {_count_true(setup_rows, 'stage_1_raw_context_or_raw_sweep')}",
        f"- Count passing STAGE_2: {_count_true(setup_rows, 'stage_2_qualified_h1_sweep')}",
        f"- Count passing STAGE_3: {_count_true(setup_rows, 'stage_3_qualified_h1_failed_reclaim')}",
        f"- Count passing STAGE_4: {_count_true(setup_rows, 'stage_4_sequence_linked_setup')}",
        f"- Count passing STAGE_5: {_count_true(setup_rows, 'stage_5_policy_replay_allowed')}",
        f"- Count failing each stage: {_counts(failures, 'failed_stage')}",
        f"- Policy replay outcomes: {_policy_counts(policy)}",
        f"- 2026-05-26 sequence reproduced: {str(reproduced).lower()}",
        f"- New sequence-linked candidates vs 38O: {max(0, _count_true(links, 'sequence_valid_for_setup') - 1)}",
        "",
        "## Sequence Valid Rows",
        "",
        _markdown_table(valid, ["setup_id", "setup_formed_at", "corrected_research_classification", "tradable_entry_anchor", "final_stage_reached"]),
        "",
        "## Policy Replay Allowed Rows",
        "",
        _markdown_table(policy, ["setup_id", "entry_candidate_ts", "policy_name", "policy_outcome_label", "first_event", "first_event_ts"]),
        "",
        "## Focus Rows",
        "",
        _markdown_table(
            focus,
            [
                "setup_id",
                "setup_formed_at",
                "corrected_research_classification",
                "final_stage_reached",
                "stage_gate_status",
                "stage_gate_reject_reason",
            ],
        ),
        "",
        "## Data Quality Notes",
        "",
        "- Uses existing feed/ rows for 2026-05-23 through 2026-06-10.",
        "- Future labels are not read by this runner.",
        "- Historical 38J/38K/38L/38N/38O artifact roots are not rewritten.",
        "- Raw sweep alone cannot pass to policy replay.",
    ]
    return "\n".join(lines) + "\n"


def _audit_text(summary: str) -> str:
    return (
        "# SHI RESET 38P Full Window Stage-Gate Replay Audit\n\n"
        "Verdict: RESEARCH_STAGE_GATE_REPLAY_COMPLETE\n\n"
        "This audit records the 38P stage-gated full-window replay. The runner treats setup rows as review context by default and only allows policy replay after a valid qualified H1 failed-reclaim sequence link.\n\n"
        + summary
    )


def _manual_classification(setup: pd.Series) -> str:
    value = _cell(setup.get("manual_corrected_classification"))
    return value if value else _cell(setup.get("setup_role_classification"))


def _events_true(events: pd.DataFrame, column: str) -> bool:
    return bool(not events.empty and column in events and (events[column].astype(str).str.lower() == "true").any())


def _boolish(value: object) -> bool:
    return _cell(value).lower() == "true"


def _bool_cell(value: object) -> str:
    return str(bool(value)).lower()


def _count_true(frame: pd.DataFrame, column: str) -> int:
    return int((frame[column].astype(str).str.lower() == "true").sum()) if column in frame else 0


def _counts(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return "{}"
    return json.dumps(frame[column].fillna("").astype(str).value_counts().to_dict(), sort_keys=True)


def _policy_counts(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "{}"
    counts = frame.groupby(["policy_name", "policy_outcome_label"], dropna=False).size().to_dict()
    return json.dumps({f"{key[0]}::{key[1]}": int(value) for key, value in counts.items()}, sort_keys=True)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.reindex(columns=columns).iterrows():
        lines.append("| " + " | ".join(_cell(row[column]).replace("|", "\\|") for column in columns) + " |")
    return "\n".join(lines)


def _event_ts(path: dict[str, object], event: str) -> str:
    if event == "TARGET":
        return _format_optional(path.get("target_touched_at"))
    if event == "SELECTED_STOP":
        return _format_optional(path.get("stop_touched_at"))
    if event == "TP1":
        return _format_optional(path.get("tp1_touched_at"))
    if event == "BE":
        return _format_optional(path.get("be_hit_after_tp1_at"))
    if event == "AMBIGUOUS_SAME_BAR":
        return _format_optional(path.get("stop_touched_at")) or _format_optional(path.get("tp1_touched_at"))
    return ""


def _unresolved(direction: str, entry: float, selected_stop: float, target: dict[str, float] | None) -> bool:
    return direction not in {"UP", "DOWN"} or pd.isna(entry) or pd.isna(selected_stop) or target is None


def _positive(value: float) -> bool:
    return not pd.isna(value) and value > 0


def _ts(value: object) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts


def _format_ts(value: object) -> str:
    return _ts(value).isoformat().replace("+00:00", "Z")


def _format_optional(value: object) -> str:
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    if value in {"", None}:
        return ""
    return _format_ts(value)


def _float_value(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _cell(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
