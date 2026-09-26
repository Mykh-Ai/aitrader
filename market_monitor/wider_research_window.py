from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


WIDER_RESEARCH_VERSION = "SHI_RESET_38J_WIDER_RESEARCH_WINDOW_CLASSIFIER_V0"

WIDER_SETUP_TIMELINE_CSV = "wider_setup_timeline.csv"
WIDER_SETUP_CLASSIFICATION_CSV = "wider_setup_classification.csv"
WIDER_STRUCTURAL_STOPS_CSV = "wider_structural_stop_candidates.csv"
WIDER_POLICY_REPLAY_CSV = "wider_policy_replay_results.csv"
WIDER_SUMMARY_MD = "wider_research_summary.md"
WIDER_MANIFEST_JSON = "wider_research_manifest.json"
MANUAL_REVIEW_SHORTLIST_CSV = "manual_review_shortlist.csv"

ENTRY_ROLES = {
    "FAILED_RECLAIM_TRIGGER_CANDIDATE",
    "STRUCTURAL_RETEST_TRIGGER_CANDIDATE",
    "CORRECTION_END_ENTRY_CANDIDATE",
    "CONFIRMATION_ENTRY_CANDIDATE",
    "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP",
}
NO_POLICY_ROLES = {
    "CONTEXT_ONLY",
    "PRE_TRIGGER_CONTEXT",
    "RAW_SWEEP_OBSERVATION",
    "LATE_LAST_WAGON",
    "REJECT",
}

CLASSIFICATION_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "trigger_status",
    "source_time_precision",
    "market_state",
    "dominant_side",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "target_reference",
    "stop_reference",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "source_window_start",
    "source_window_end",
    "source_window_rows",
    "source_window_high",
    "source_window_low",
    "local_swing_high_candidate",
    "local_swing_low_candidate",
    "structural_zone_context",
    "setup_role_classification",
    "immediate_entry_valid",
    "retest_rejection_required",
    "failed_reclaim_required",
    "late_last_wagon_flag",
    "policy_replay_allowed",
    "classification_reason",
    "evidence_summary",
]

STOP_COLUMNS = [
    "setup_id",
    "direction_context",
    "tradable_entry_anchor",
    "source_window_stop_reference",
    "source_window_stop_type",
    "local_swing_stop_reference",
    "local_swing_stop_type",
    "structural_zone_stop_reference",
    "structural_zone_stop_type",
    "original_invalidation_stop",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "stop_selection_reason",
]

POLICY_COLUMNS = [
    "setup_id",
    "policy_name",
    "setup_role_classification",
    "direction_context",
    "setup_formed_at",
    "tradable_entry_anchor",
    "target_reference",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "policy_replay_allowed",
    "policy_outcome_label",
    "first_event_at",
    "target_touched_at",
    "selected_stop_touched_at",
    "tp1_touched_at",
    "be_touched_at",
    "forward_rows",
    "evidence_summary",
]


class WiderResearchWindowError(RuntimeError):
    """Raised when the wider research classification cannot be generated."""


@dataclass(frozen=True)
class WiderResearchWindowResult:
    output_dir: Path
    setup_timeline_path: Path
    classification_path: Path
    structural_stops_path: Path
    policy_replay_path: Path
    manual_review_path: Path
    summary_path: Path
    manifest_path: Path
    setup_count: int
    policy_replay_count: int


def run_wider_research_window(
    *,
    setup_timeline_path: str | Path,
    feed_dir: str | Path,
    selected_zones_path: str | Path,
    output_dir: str | Path,
    start: str | date,
    end: str | date,
) -> WiderResearchWindowResult:
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if start_date > end_date:
        raise WiderResearchWindowError("start must be <= end")
    setup_path = Path(setup_timeline_path)
    feed_root = Path(feed_dir)
    zones_path = Path(selected_zones_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not setup_path.exists():
        raise WiderResearchWindowError(f"setup timeline not found: {setup_path}")
    if not feed_root.exists():
        raise WiderResearchWindowError(f"feed dir not found: {feed_root}")

    timeline = _read_csv(setup_path)
    feed = _load_feed_window(feed_root, start_date, end_date)
    zones = _read_csv(zones_path) if zones_path.exists() else pd.DataFrame()

    timeline = _filter_timeline(timeline, start_date, end_date)
    classification, stops = _classify_timeline(timeline=timeline, feed=feed, zones=zones)
    policy = _policy_replay(classification=classification, feed=feed)
    manual_review = _manual_review_shortlist(classification, policy)

    setup_timeline_out = out_dir / WIDER_SETUP_TIMELINE_CSV
    classification_path = out_dir / WIDER_SETUP_CLASSIFICATION_CSV
    stops_path = out_dir / WIDER_STRUCTURAL_STOPS_CSV
    policy_path = out_dir / WIDER_POLICY_REPLAY_CSV
    manual_review_path = out_dir / MANUAL_REVIEW_SHORTLIST_CSV
    summary_path = out_dir / WIDER_SUMMARY_MD
    manifest_path = out_dir / WIDER_MANIFEST_JSON

    timeline.to_csv(setup_timeline_out, index=False)
    classification.reindex(columns=CLASSIFICATION_COLUMNS).to_csv(classification_path, index=False)
    stops.reindex(columns=STOP_COLUMNS).to_csv(stops_path, index=False)
    policy.reindex(columns=POLICY_COLUMNS).to_csv(policy_path, index=False)
    manual_review.to_csv(manual_review_path, index=False)
    summary_path.write_text(
        _render_summary(
            setup_count=len(timeline),
            classification=classification,
            policy=policy,
            manual_review=manual_review,
            feed=feed,
            start_date=start_date,
            end_date=end_date,
        ),
        encoding="utf-8",
    )
    manifest = {
        "wider_research_version": WIDER_RESEARCH_VERSION,
        "research_only": True,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "setup_timeline_path": str(setup_path),
        "feed_dir": str(feed_root),
        "selected_zones_path": str(zones_path),
        "uses_future_labels": False,
        "changes_setup_detection": False,
        "changes_setup_builder_rules": False,
        "uses_backtester": False,
        "uses_executor": False,
        "output_is_trading_signal": False,
        "setup_reference_level_is_entry": False,
        "uses_actual_setup_price": True,
        "uses_tradable_entry_anchor": True,
        "uses_structural_stop_candidates": True,
        "tp1_be_selected_stop_before_tp1_terminal": True,
        "outputs": {
            "wider_setup_timeline_csv": str(setup_timeline_out),
            "wider_setup_classification_csv": str(classification_path),
            "wider_structural_stop_candidates_csv": str(stops_path),
            "wider_policy_replay_results_csv": str(policy_path),
            "manual_review_shortlist_csv": str(manual_review_path),
            "summary_md": str(summary_path),
            "manifest_json": str(manifest_path),
        },
        "setup_count": int(len(timeline)),
        "policy_replay_rows": int(len(policy)),
        "repo_commit": _repo_commit(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return WiderResearchWindowResult(
        output_dir=out_dir,
        setup_timeline_path=setup_timeline_out,
        classification_path=classification_path,
        structural_stops_path=stops_path,
        policy_replay_path=policy_path,
        manual_review_path=manual_review_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        setup_count=int(len(timeline)),
        policy_replay_count=int(len(policy)),
    )


def _classify_timeline(*, timeline: pd.DataFrame, feed: pd.DataFrame, zones: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    stop_rows = []
    if timeline.empty:
        return pd.DataFrame(columns=CLASSIFICATION_COLUMNS), pd.DataFrame(columns=STOP_COLUMNS)
    for _, setup in timeline.sort_values("setup_formed_at", kind="mergesort").iterrows():
        enriched = _enrich_setup(setup, feed, zones)
        stop_row = _stop_candidates(enriched, feed, zones)
        role, flags, reason = _classify_role(enriched, stop_row)
        policy_allowed = (
            role in ENTRY_ROLES
            and not pd.isna(_float_value(enriched.get("tradable_entry_anchor")))
            and not pd.isna(_float_value(stop_row.get("selected_research_stop_reference")))
            and not pd.isna(_float_value(enriched.get("target_reference")))
        )
        rows.append(
            {
                "setup_id": _cell(enriched.get("setup_id")),
                "setup_formed_at": _cell(enriched.get("setup_formed_at")),
                "setup_type": _cell(enriched.get("setup_type")),
                "direction_context": _cell(enriched.get("direction_context")),
                "trigger_status": _cell(enriched.get("trigger_status")),
                "source_time_precision": _cell(enriched.get("source_time_precision")),
                "market_state": _cell(enriched.get("market_state")),
                "dominant_side": _cell(enriched.get("dominant_side")),
                "setup_reference_level": _round(enriched.get("setup_reference_level")),
                "actual_setup_price": _round(enriched.get("actual_setup_price")),
                "tradable_entry_anchor": _round(enriched.get("tradable_entry_anchor")),
                "target_reference": _round(enriched.get("target_reference")),
                "stop_reference": _round(enriched.get("stop_reference")),
                "selected_research_stop_reference": _round(stop_row.get("selected_research_stop_reference")),
                "selected_research_stop_type": _cell(stop_row.get("selected_research_stop_type")),
                "source_window_start": _cell(enriched.get("source_window_start")),
                "source_window_end": _cell(enriched.get("source_window_end")),
                "source_window_rows": int(enriched.get("source_window_rows", 0)),
                "source_window_high": _round(enriched.get("source_window_high")),
                "source_window_low": _round(enriched.get("source_window_low")),
                "local_swing_high_candidate": _round(stop_row.get("local_swing_high_candidate")),
                "local_swing_low_candidate": _round(stop_row.get("local_swing_low_candidate")),
                "structural_zone_context": _cell(stop_row.get("structural_zone_context")),
                "setup_role_classification": role,
                "immediate_entry_valid": str(bool(flags["immediate_entry_valid"])).lower(),
                "retest_rejection_required": str(bool(flags["retest_rejection_required"])).lower(),
                "failed_reclaim_required": str(bool(flags["failed_reclaim_required"])).lower(),
                "late_last_wagon_flag": str(bool(flags["late_last_wagon_flag"])).lower(),
                "policy_replay_allowed": str(bool(policy_allowed)).lower(),
                "classification_reason": reason,
                "evidence_summary": _cell(enriched.get("evidence_summary")),
            }
        )
        stop_rows.append(stop_row)
    return pd.DataFrame(rows, columns=CLASSIFICATION_COLUMNS), pd.DataFrame(stop_rows, columns=STOP_COLUMNS)


def _enrich_setup(setup: pd.Series, feed: pd.DataFrame, zones: pd.DataFrame) -> dict[str, object]:
    row = setup.to_dict()
    formed_at = pd.Timestamp(row.get("setup_formed_at"))
    if formed_at.tzinfo is None:
        formed_at = formed_at.tz_localize("UTC")
    price = _price_at_or_before(feed, formed_at)
    row["actual_setup_price"] = price
    row["tradable_entry_anchor"] = price
    row["target_reference"] = _target_price(row)
    row["stop_reference"] = _float_value(row.get("stop_reference"), _float_value(row.get("invalidation_level")))
    row["setup_reference_level"] = _float_value(
        row.get("setup_reference_level"),
        _float_value(row.get("entry_reference_level")),
    )
    source = _source_window(feed, row)
    row["source_window_rows"] = int(len(source))
    row["source_window_high"] = float(source["high"].max()) if not source.empty else float("nan")
    row["source_window_low"] = float(source["low"].min()) if not source.empty else float("nan")
    return row


def _stop_candidates(row: dict[str, object], feed: pd.DataFrame, zones: pd.DataFrame) -> dict[str, object]:
    direction = _cell(row.get("direction_context"))
    entry = _float_value(row.get("tradable_entry_anchor"))
    source_high = _float_value(row.get("source_window_high"))
    source_low = _float_value(row.get("source_window_low"))
    local = _local_swing(feed, pd.Timestamp(row["setup_formed_at"]))
    local_high = local["high"]
    local_low = local["low"]
    original = _float_value(row.get("stop_reference"))
    structural = _structural_zone_stop(row, zones)

    source_stop = source_high if direction == "DOWN" else source_low
    local_stop = local_high if direction == "DOWN" else local_low
    structural_stop = structural["stop"]
    selected, selected_type, selection_reason = _select_stop(
        direction=direction,
        entry=entry,
        structural_stop=structural_stop,
        local_stop=local_stop,
        structural_stop_type=structural["type"],
        original_stop=original,
        source_stop=source_stop,
    )
    return {
        "setup_id": _cell(row.get("setup_id")),
        "direction_context": direction,
        "tradable_entry_anchor": _round(entry),
        "source_window_stop_reference": _round(source_stop),
        "source_window_stop_type": "source_window_stop_context_only",
        "local_swing_stop_reference": _round(local_stop),
        "local_swing_stop_type": "local_swing_stop",
        "structural_zone_stop_reference": _round(structural_stop),
        "structural_zone_stop_type": structural["type"],
        "original_invalidation_stop": _round(original),
        "selected_research_stop_reference": _round(selected),
        "selected_research_stop_type": selected_type,
        "stop_selection_reason": selection_reason,
        "local_swing_high_candidate": _round(local_high),
        "local_swing_low_candidate": _round(local_low),
        "structural_zone_context": structural["context"],
    }


def _classify_role(row: dict[str, object], stop_row: dict[str, object]) -> tuple[str, dict[str, bool], str]:
    setup_type = _cell(row.get("setup_type"))
    trigger = _cell(row.get("trigger_status"))
    precision = _cell(row.get("source_time_precision"))
    source_rows = int(row.get("source_window_rows", 0))
    broad = _is_broad_precision(precision) or source_rows >= 720
    raw_sweep = _boolish(row.get("raw_sweep")) or "sweep" in _cell(row.get("sweep_status")).lower()
    qualified_h1_sweep = _boolish(row.get("qualified_h1_sweep"))
    qualified_h1_failed_reclaim = _boolish(row.get("qualified_h1_failed_reclaim"))
    flags = {
        "immediate_entry_valid": False,
        "retest_rejection_required": False,
        "failed_reclaim_required": False,
        "late_last_wagon_flag": False,
    }
    if trigger in {"WATCH", "CONTEXT_ONLY"}:
        role = "PRE_TRIGGER_CONTEXT" if precision.startswith("RAW_REGIME_WINDOW") else "CONTEXT_ONLY"
        return role, flags, "watch/context row; not counted as entry"
    if raw_sweep and not qualified_h1_sweep:
        return "RAW_SWEEP_OBSERVATION", flags, "raw_sweep_not_qualified"
    if broad and qualified_h1_failed_reclaim and setup_type in {
        "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
        "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
    }:
        flags["failed_reclaim_required"] = True
        flags["immediate_entry_valid"] = True
        return "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP", flags, "qualified H1 sweep/failed reclaim overrides broad-window demotion"
    if broad:
        return "PRE_TRIGGER_CONTEXT", flags, "broad raw/source window remains context without qualified local trigger"
    if trigger not in {"ARMED", "TRIGGERED"}:
        return "UNRESOLVED_REVIEW_REQUIRED", flags, "non-watch trigger state requires review"

    if setup_type == "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP":
        if not qualified_h1_failed_reclaim:
            return "RAW_SWEEP_OBSERVATION" if raw_sweep else "PRE_TRIGGER_CONTEXT", flags, "raw_sweep_not_qualified"
        flags["failed_reclaim_required"] = True
        flags["immediate_entry_valid"] = True
        return "FAILED_RECLAIM_TRIGGER_CANDIDATE", flags, "qualified H1 failed reclaim evidence"
    if setup_type == "SELLER_DOMINANCE_RETEST_DOWN_SETUP":
        flags["retest_rejection_required"] = True
        flags["immediate_entry_valid"] = True
        return "STRUCTURAL_RETEST_TRIGGER_CANDIDATE", flags, "seller-dominance retest row requires structural rejection review"
    if setup_type == "DEMAND_SWEEP_RECLAIM_UP_SETUP":
        flags["immediate_entry_valid"] = True
        return "CORRECTION_END_ENTRY_CANDIDATE", flags, "demand reclaim row after exhaustion/correction context"
    if setup_type == "ACCEPTED_BREAKOUT_UP_SETUP":
        flags["immediate_entry_valid"] = True
        return "CONFIRMATION_ENTRY_CANDIDATE", flags, "accepted breakout confirmation context"
    return "UNRESOLVED_REVIEW_REQUIRED", flags, "setup type not mapped by 38J classifier"


def _policy_replay(*, classification: pd.DataFrame, feed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if classification.empty:
        return pd.DataFrame(columns=POLICY_COLUMNS)
    for _, setup in classification.iterrows():
        allowed = str(setup.get("policy_replay_allowed", "")).lower() == "true"
        role = _cell(setup.get("setup_role_classification"))
        if not allowed:
            label = "POLICY_NOT_APPLIED_LATE_LAST_WAGON" if role == "LATE_LAST_WAGON" else "POLICY_NOT_APPLIED_CONTEXT_ONLY"
            rows.append(_policy_row(setup, policy_name="POLICY_FILTER", allowed=False, outcome=label, path={}))
            continue
        rows.append(_replay_selected_stop_to_target(setup, feed))
        rows.append(_replay_tp1_be(setup, feed))
    return pd.DataFrame(rows, columns=POLICY_COLUMNS)


def _replay_selected_stop_to_target(setup: pd.Series, feed: pd.DataFrame) -> dict[str, object]:
    path = _forward_path(setup, feed)
    if path["target"] is None or path["stop"] is None:
        outcome = "TARGET_OR_STOP_UNRESOLVED"
    elif path["forward_rows"] == 0:
        outcome = "INSUFFICIENT_FORWARD_DATA"
    elif path["target_at"] and (not path["stop_at"] or path["target_at"] < path["stop_at"]):
        outcome = "TARGET_BEFORE_SELECTED_STOP"
    elif path["stop_at"] and (not path["target_at"] or path["stop_at"] < path["target_at"]):
        outcome = "SELECTED_STOP_BEFORE_TARGET"
    else:
        outcome = "NO_DECISIVE_OUTCOME"
    return _policy_row(setup, policy_name="SELECTED_STOP_TO_TARGET_RESEARCH_POLICY", allowed=True, outcome=outcome, path=path)


def _replay_tp1_be(setup: pd.Series, feed: pd.DataFrame) -> dict[str, object]:
    path = _forward_path(setup, feed, include_tp1=True)
    if path["target"] is None or path["stop"] is None:
        outcome = "TARGET_OR_STOP_UNRESOLVED"
    elif path["forward_rows"] == 0:
        outcome = "INSUFFICIENT_FORWARD_DATA"
    elif path["stop_at"] and (not path["tp1_at"] or path["stop_at"] < path["tp1_at"]):
        outcome = "NO_TP1_SELECTED_STOP"
    elif not path["tp1_at"]:
        outcome = "NO_TP1_SELECTED_STOP" if path["stop_at"] else "NO_DECISIVE_OUTCOME"
    else:
        after_tp1 = [event for event in [("target", path["target_at"]), ("be", path["be_at"]), ("stop", path["stop_at"])] if event[1] and event[1] > path["tp1_at"]]
        if not after_tp1:
            outcome = "NO_DECISIVE_OUTCOME"
        else:
            first = sorted(after_tp1, key=lambda item: item[1])[0][0]
            outcome = "TP1_THEN_TARGET" if first == "target" else "TP1_THEN_BE" if first == "be" else "NO_TP1_SELECTED_STOP"
    return _policy_row(setup, policy_name="TP1_BE_WITH_SELECTED_STOP_POLICY", allowed=True, outcome=outcome, path=path)


def _forward_path(setup: pd.Series, feed: pd.DataFrame, *, include_tp1: bool = False) -> dict[str, object]:
    formed_at = pd.Timestamp(setup["setup_formed_at"])
    if formed_at.tzinfo is None:
        formed_at = formed_at.tz_localize("UTC")
    direction = _cell(setup["direction_context"])
    entry = _float_value(setup["tradable_entry_anchor"])
    target = _float_value(setup["target_reference"])
    stop = _float_value(setup["selected_research_stop_reference"])
    forward = feed[feed["timestamp"] > formed_at].sort_values("timestamp", kind="mergesort")
    path = {"entry": entry, "target": target, "stop": stop, "forward_rows": int(len(forward)), "target_at": "", "stop_at": "", "tp1_at": "", "be_at": ""}
    if forward.empty or pd.isna(entry) or pd.isna(target) or pd.isna(stop):
        return path
    tp1 = _tp1(entry, target) if include_tp1 else float("nan")
    for _, bar in forward.iterrows():
        ts = _format_ts(bar["timestamp"])
        high = float(bar["high"])
        low = float(bar["low"])
        if not path["target_at"] and _level_touched(direction, high, low, target, target=True):
            path["target_at"] = ts
        if not path["stop_at"] and _level_touched(direction, high, low, stop, target=False):
            path["stop_at"] = ts
        if include_tp1 and not path["tp1_at"] and not pd.isna(tp1) and _level_touched(direction, high, low, tp1, target=True):
            path["tp1_at"] = ts
        if include_tp1 and path["tp1_at"] and not path["be_at"] and _level_touched(direction, high, low, entry, target=False):
            path["be_at"] = ts
        if path["target_at"] and path["stop_at"] and (not include_tp1 or (path["tp1_at"] and (path["be_at"] or path["target_at"]))):
            break
    return path


def _policy_row(setup: pd.Series, *, policy_name: str, allowed: bool, outcome: str, path: dict[str, object]) -> dict[str, object]:
    first_event = _first_event(path)
    return {
        "setup_id": _cell(setup.get("setup_id")),
        "policy_name": policy_name,
        "setup_role_classification": _cell(setup.get("setup_role_classification")),
        "direction_context": _cell(setup.get("direction_context")),
        "setup_formed_at": _cell(setup.get("setup_formed_at")),
        "tradable_entry_anchor": _round(setup.get("tradable_entry_anchor")),
        "target_reference": _round(setup.get("target_reference")),
        "selected_research_stop_reference": _round(setup.get("selected_research_stop_reference")),
        "selected_research_stop_type": _cell(setup.get("selected_research_stop_type")),
        "policy_replay_allowed": str(bool(allowed)).lower(),
        "policy_outcome_label": outcome,
        "first_event_at": first_event,
        "target_touched_at": _cell(path.get("target_at")),
        "selected_stop_touched_at": _cell(path.get("stop_at")),
        "tp1_touched_at": _cell(path.get("tp1_at")),
        "be_touched_at": _cell(path.get("be_at")),
        "forward_rows": int(path.get("forward_rows", 0) or 0),
        "evidence_summary": f"38J research replay; selected_stop_before_tp1_terminal=true; allowed={allowed}",
    }


def _manual_review_shortlist(classification: pd.DataFrame, policy: pd.DataFrame) -> pd.DataFrame:
    if classification.empty:
        return classification.copy()
    mask = classification["setup_role_classification"].isin(ENTRY_ROLES | {"UNRESOLVED_REVIEW_REQUIRED"})
    mask |= classification["late_last_wagon_flag"].astype(str).str.lower() == "true"
    mask |= (
        classification["source_time_precision"].astype(str).str.contains("720M|1440M", regex=True)
        & classification["trigger_status"].isin(["ARMED", "TRIGGERED"])
    )
    return classification.loc[mask].sort_values(["setup_formed_at", "setup_id"], kind="mergesort").head(20).copy()


def _render_summary(
    *,
    setup_count: int,
    classification: pd.DataFrame,
    policy: pd.DataFrame,
    manual_review: pd.DataFrame,
    feed: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> str:
    lines = [
        "# SHI RESET 38J Wider Research Window Summary",
        "",
        "Research-only classification run. This is not a trading run and does not create orders, entries/exits, PnL, position sizing, Executor actions, or live-readiness claims.",
        "",
        f"- Interval: {start_date.isoformat()} -> {end_date.isoformat()}",
        f"- Total setup rows found: {setup_count}",
        f"- Rows by setup_type: {_counts(classification, 'setup_type')}",
        f"- Rows by direction_context: {_counts(classification, 'direction_context')}",
        f"- Rows by trigger_status: {_counts(classification, 'trigger_status')}",
        f"- Rows by source_time_precision: {_counts(classification, 'source_time_precision')}",
        f"- Rows by setup_role_classification: {_counts(classification, 'setup_role_classification')}",
        f"- immediate_entry_valid=true: {_count_bool(classification, 'immediate_entry_valid')}",
        f"- context-only rows: {_count_role(classification, 'CONTEXT_ONLY')}",
        f"- pre-trigger context rows: {_count_role(classification, 'PRE_TRIGGER_CONTEXT')}",
        f"- failed-reclaim trigger candidates: {_count_role(classification, 'FAILED_RECLAIM_TRIGGER_CANDIDATE')}",
        f"- structural-retest trigger candidates: {_count_role(classification, 'STRUCTURAL_RETEST_TRIGGER_CANDIDATE')}",
        f"- correction-end entry candidates: {_count_role(classification, 'CORRECTION_END_ENTRY_CANDIDATE')}",
        f"- late/last-wagon rows: {_count_role(classification, 'LATE_LAST_WAGON')}",
        f"- rejects: {_count_role(classification, 'REJECT')}",
        f"- Policy replay outcomes by role: {_policy_counts(policy)}",
        "",
        "## Manual Lessons Encoded In Classification Summary",
        "",
        "- Bearish context alone is not entry.",
        "- If price moves upward after bearish context and then sweeps a local swing, the entry candidate is only after failed reclaim / close back below swept level.",
        "- Local swing sweep and structural resistance retest are separated in role classification.",
        "- Broad raw-window rows are downgraded to context or late/last-wagon unless local trigger evidence is present.",
        "",
        "## Top Manual Review Candidates",
        "",
        _markdown_table(manual_review.head(20), ["setup_id", "setup_formed_at", "setup_type", "setup_role_classification", "trigger_status", "classification_reason"]),
        "",
        "## Rows Excluded From Policy Replay",
        "",
        _markdown_table(
            classification[classification["policy_replay_allowed"].astype(str) != "true"].head(40),
            ["setup_id", "setup_formed_at", "setup_role_classification", "classification_reason"],
        ),
        "",
        "## Data Quality Notes By Day",
        "",
        _data_quality_notes(feed),
    ]
    return "\n".join(lines) + "\n"


def _load_feed_window(feed_dir: Path, start_date: date, end_date: date) -> pd.DataFrame:
    frames = []
    for day in _date_range(start_date, end_date):
        path = feed_dir / f"{day.isoformat()}.csv"
        if not path.exists():
            raise WiderResearchWindowError(f"missing feed file: {path}")
        frame = pd.read_csv(path)
        frames.append(_normalize_feed(frame, path))
    feed = pd.concat(frames, ignore_index=True, sort=False)
    return feed.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _normalize_feed(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
    columns = {column.lower(): column for column in frame.columns}
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[columns["timestamp"]], utc=True, errors="coerce"),
            "open": pd.to_numeric(frame[columns["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[columns["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[columns["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[columns["close"]], errors="coerce"),
            "source_file": str(path),
        }
    )
    if "is synthetic" in columns:
        out["is_synthetic"] = frame[columns["is synthetic"]]
    elif "issynthetic" in columns:
        out["is_synthetic"] = frame[columns["issynthetic"]]
    else:
        out["is_synthetic"] = 0
    return out.dropna(subset=["timestamp", "close"]).copy()


def _filter_timeline(timeline: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    if timeline.empty:
        return timeline.copy()
    frame = timeline.copy()
    formed = pd.to_datetime(frame["setup_formed_at"], utc=True, errors="coerce")
    start_ts = pd.Timestamp(start_date.isoformat(), tz="UTC")
    end_ts = pd.Timestamp((end_date + timedelta(days=1)).isoformat(), tz="UTC")
    return frame[(formed >= start_ts) & (formed < end_ts)].copy()


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _source_window(feed: pd.DataFrame, row: dict[str, object]) -> pd.DataFrame:
    start = pd.Timestamp(row.get("source_window_start"))
    end = pd.Timestamp(row.get("source_window_end"))
    if start.tzinfo is None:
        start = start.tz_localize("UTC")
    if end.tzinfo is None:
        end = end.tz_localize("UTC")
    return feed[(feed["timestamp"] >= start) & (feed["timestamp"] <= end)].copy()


def _local_swing(feed: pd.DataFrame, formed_at: pd.Timestamp, minutes: int = 180) -> dict[str, float]:
    if formed_at.tzinfo is None:
        formed_at = formed_at.tz_localize("UTC")
    start = formed_at - pd.Timedelta(minutes=minutes)
    window = feed[(feed["timestamp"] >= start) & (feed["timestamp"] <= formed_at)]
    if window.empty:
        return {"high": float("nan"), "low": float("nan")}
    return {"high": float(window["high"].max()), "low": float(window["low"].min())}


def _select_stop(
    *,
    direction: str,
    entry: float,
    structural_stop: float,
    structural_stop_type: str,
    local_stop: float,
    original_stop: float,
    source_stop: float,
) -> tuple[float, str, str]:
    valid = {
        "structural_zone_stop": structural_stop_type == "structural_zone_stop"
        and _valid_stop(direction, entry, structural_stop),
        "local_swing_stop": _valid_stop(direction, entry, local_stop),
        "original_invalidation_stop": _valid_stop(direction, entry, original_stop),
        "source_window_stop": _valid_stop(direction, entry, source_stop),
    }
    if valid["structural_zone_stop"]:
        return structural_stop, "structural_zone_stop", "selected structural zone stop; source-window stop context only"
    if valid["local_swing_stop"]:
        return local_stop, "local_swing_stop", "selected local swing stop; source-window stop context only"
    if valid["original_invalidation_stop"]:
        return original_stop, "original_invalidation_stop", "selected original invalidation stop"
    if valid["source_window_stop"]:
        return source_stop, "source_window_stop", "fallback only because no structural/local stop resolved"
    return float("nan"), "", "no valid stop resolved"


def _valid_stop(direction: str, entry: float, stop: float) -> bool:
    if pd.isna(entry) or pd.isna(stop):
        return False
    return stop > entry if direction == "DOWN" else stop < entry if direction == "UP" else False


def _structural_zone_stop(row: dict[str, object], zones: pd.DataFrame) -> dict[str, object]:
    stop = _float_value(row.get("stop_reference"))
    if zones.empty or pd.isna(stop):
        return {"stop": stop, "type": "original_invalidation_stop", "context": "selected_zones_unavailable"}
    direction = _cell(row.get("direction_context"))
    side = "BUY_SIDE" if direction == "DOWN" else "SELL_SIDE"
    frame = zones[zones.get("side", pd.Series(dtype=str)).astype(str) == side].copy()
    if frame.empty:
        return {"stop": stop, "type": "original_invalidation_stop", "context": "no_matching_structural_zone"}
    frame["_lower"] = pd.to_numeric(frame.get("price_lower"), errors="coerce")
    frame["_upper"] = pd.to_numeric(frame.get("price_upper"), errors="coerce")
    entry = _float_value(row.get("tradable_entry_anchor"))
    if direction == "DOWN":
        candidates = frame[frame["_lower"] >= entry]
        if candidates.empty:
            return {"stop": stop, "type": "original_invalidation_stop", "context": "no_buy_side_zone_above_entry"}
        selected = candidates.sort_values("_lower", kind="mergesort").iloc[0]
        return {"stop": float(selected["_upper"]), "type": "structural_zone_stop", "context": f"{selected.get('zone_id','')}:BUY_SIDE"}
    candidates = frame[frame["_upper"] <= entry]
    if candidates.empty:
        return {"stop": stop, "type": "original_invalidation_stop", "context": "no_sell_side_zone_below_entry"}
    selected = candidates.sort_values("_upper", ascending=False, kind="mergesort").iloc[0]
    return {"stop": float(selected["_lower"]), "type": "structural_zone_stop", "context": f"{selected.get('zone_id','')}:SELL_SIDE"}


def _target_price(row: dict[str, object]) -> float:
    target = _float_value(row.get("target_reference"))
    if not pd.isna(target):
        return target
    text = _cell(row.get("target_reference_zone"))
    match = re.search(r":(BUY_SIDE|SELL_SIDE):([0-9.]+)-([0-9.]+)", text)
    if not match:
        return float("nan")
    side, lower, upper = match.group(1), float(match.group(2)), float(match.group(3))
    direction = _cell(row.get("direction_context"))
    if direction == "DOWN":
        return upper
    if direction == "UP":
        return lower
    return lower if side == "BUY_SIDE" else upper


def _price_at_or_before(feed: pd.DataFrame, timestamp: pd.Timestamp) -> float:
    rows = feed[feed["timestamp"] <= timestamp]
    if rows.empty:
        return float("nan")
    return float(rows.iloc[-1]["close"])


def _is_broad_precision(precision: str) -> bool:
    match = re.search(r"RAW_REGIME_WINDOW_(\d+)M", precision)
    return bool(match and int(match.group(1)) >= 720)


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _tp1(entry: float, target: float) -> float:
    if pd.isna(entry) or pd.isna(target):
        return float("nan")
    return entry + ((target - entry) * 0.5)


def _level_touched(direction: str, high: float, low: float, level: float, *, target: bool) -> bool:
    if pd.isna(level):
        return False
    if direction == "DOWN":
        return low <= level if target else high >= level
    if direction == "UP":
        return high >= level if target else low <= level
    return False


def _first_event(path: dict[str, object]) -> str:
    events = [value for value in [path.get("target_at"), path.get("stop_at"), path.get("tp1_at"), path.get("be_at")] if value]
    return min(events) if events else ""


def _counts(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame:
        return "{}"
    return json.dumps(frame[column].value_counts(dropna=False).to_dict(), sort_keys=True)


def _policy_counts(policy: pd.DataFrame) -> str:
    if policy.empty:
        return "{}"
    counts = (
        policy.groupby(["setup_role_classification", "policy_outcome_label"], dropna=False)
        .size()
        .reset_index(name="rows")
        .to_dict(orient="records")
    )
    return json.dumps(counts, sort_keys=True)


def _count_role(frame: pd.DataFrame, role: str) -> int:
    if frame.empty:
        return 0
    return int((frame["setup_role_classification"] == role).sum())


def _count_bool(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int((frame[column].astype(str).str.lower() == "true").sum())


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    available = [column for column in columns if column in frame.columns]
    lines = ["| " + " | ".join(available) + " |", "| " + " | ".join(["---"] * len(available)) + " |"]
    for _, row in frame[available].iterrows():
        lines.append("| " + " | ".join(_cell(row[column]).replace("|", "\\|") for column in available) + " |")
    return "\n".join(lines)


def _data_quality_notes(feed: pd.DataFrame) -> str:
    if feed.empty:
        return "No feed rows loaded."
    frame = feed.copy()
    frame["day"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
    grouped = frame.groupby("day").agg(rows=("timestamp", "size"), synthetic_rows=("is_synthetic", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).sum()))).reset_index()
    return _markdown_table(grouped, ["day", "rows", "synthetic_rows"])


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _format_ts(value: object) -> str:
    if pd.isna(value):
        return ""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.isoformat().replace("+00:00", "Z")


def _cell(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def _float_value(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if not math.isnan(number) else default


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""
