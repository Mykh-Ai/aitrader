from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd


SETUP_REPLAY_VERSION = "SHI_RESET_38A_SETUP_REPLAY_VALIDATION_V0"

SETUP_REPLAY_RESULTS_CSV = "setup_replay_results.csv"
SETUP_REPLAY_SUMMARY_MD = "setup_replay_summary.md"
SETUP_REPLAY_MANIFEST_JSON = "setup_replay_manifest.json"

OUTCOME_LABELS = {
    "TARGET_FIRST",
    "INVALIDATION_FIRST",
    "BOTH_TARGET_AND_INVALIDATION_TARGET_FIRST",
    "BOTH_TARGET_AND_INVALIDATION_INVALIDATION_FIRST",
    "NO_DECISIVE_OUTCOME",
    "INSUFFICIENT_FORWARD_DATA",
    "TARGET_OR_INVALIDATION_UNRESOLVED",
}

SETUP_REPLAY_COLUMNS = [
    "setup_id",
    "interval_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "trigger_status",
    "source_time_precision",
    "evaluation_start",
    "evaluation_end",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "entry_reference_price",
    "invalidation_reference",
    "stop_reference",
    "target_reference",
    "target_reference_zone",
    "max_favorable_excursion_pct",
    "max_adverse_excursion_pct",
    "target_touched",
    "target_touched_at",
    "invalidation_touched",
    "invalidation_touched_at",
    "first_event",
    "outcome_label",
    "evidence_summary",
]


class SetupReplayValidationError(RuntimeError):
    """Raised when setup replay validation cannot complete."""


@dataclass(frozen=True)
class ReplayInterval:
    interval_id: str
    start: str
    end: str
    setup_timeline_path: Path
    setup_manifest_path: Path | None = None


@dataclass(frozen=True)
class SetupReplayValidationResult:
    output_dir: Path
    results_path: Path
    summary_path: Path
    manifest_path: Path
    result_count: int


def run_setup_replay_validation(
    *,
    intervals: list[ReplayInterval],
    feed_dir: str | Path,
    output_dir: str | Path,
) -> SetupReplayValidationResult:
    if not intervals:
        raise SetupReplayValidationError("at least one interval is required")

    feed_root = Path(feed_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    interval_manifests: list[dict[str, object]] = []
    for interval in intervals:
        interval_rows, manifest = _evaluate_interval(interval=interval, feed_root=feed_root)
        rows.extend(interval_rows)
        interval_manifests.append(manifest)

    results = pd.DataFrame(rows, columns=SETUP_REPLAY_COLUMNS)
    _assert_allowed_outcomes(results)

    results_path = out_dir / SETUP_REPLAY_RESULTS_CSV
    summary_path = out_dir / SETUP_REPLAY_SUMMARY_MD
    manifest_path = out_dir / SETUP_REPLAY_MANIFEST_JSON

    results.to_csv(results_path, index=False)
    summary_path.write_text(_summary_text(results, interval_manifests), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "setup_replay_version": SETUP_REPLAY_VERSION,
                "research_only": True,
                "uses_forward_data_for_outcome_evaluation_only": True,
                "changes_setup_detection_logic": False,
                "uses_backtester": False,
                "uses_executor": False,
                "uses_orders": False,
                "uses_entries_exits": False,
                "uses_pnl": False,
                "uses_position_sizing": False,
                "live_readiness_claim": False,
                "strategy_promotion": False,
                "feed_dir": str(feed_root),
                "output_dir": str(out_dir),
                "result_count": int(len(results)),
                "intervals": interval_manifests,
                "outputs": {
                    "setup_replay_results_csv": str(results_path),
                    "setup_replay_summary_md": str(summary_path),
                    "setup_replay_manifest_json": str(manifest_path),
                },
                "repo_commit": _repo_commit(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return SetupReplayValidationResult(out_dir, results_path, summary_path, manifest_path, int(len(results)))


def _evaluate_interval(*, interval: ReplayInterval, feed_root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    start_ts = _parse_ts(interval.start)
    end_ts = _parse_ts(interval.end)
    if pd.isna(start_ts) or pd.isna(end_ts) or start_ts > end_ts:
        raise SetupReplayValidationError(f"invalid interval bounds for {interval.interval_id}")

    timeline_path = Path(interval.setup_timeline_path)
    if not timeline_path.exists():
        raise SetupReplayValidationError(f"missing setup timeline: {timeline_path}")
    setups = _read_csv(timeline_path)
    if setups.empty:
        setups = pd.DataFrame()
    setups["_formed_ts"] = pd.to_datetime(setups.get("setup_formed_at"), errors="coerce", utc=True)
    setups = setups[(setups["_formed_ts"] >= start_ts) & (setups["_formed_ts"] <= end_ts)].copy()

    feed = _load_feed_range(feed_root=feed_root, start_ts=start_ts, end_ts=end_ts)
    rows = [_evaluate_setup(row=row, interval=interval, end_ts=end_ts, feed=feed) for _, row in setups.iterrows()]
    manifest = {
        "interval_id": interval.interval_id,
        "start": _iso_z(start_ts),
        "end": _iso_z(end_ts),
        "setup_timeline_path": str(timeline_path),
        "setup_builder_manifest_path": str(interval.setup_manifest_path or ""),
        "setup_rows": int(len(rows)),
        "feed_rows": int(len(feed)),
        "feed_start": _iso_z(feed["_ts"].min()) if not feed.empty else "",
        "feed_end": _iso_z(feed["_ts"].max()) if not feed.empty else "",
    }
    return rows, manifest


def _evaluate_setup(
    *,
    row: pd.Series,
    interval: ReplayInterval,
    end_ts: pd.Timestamp,
    feed: pd.DataFrame,
) -> dict[str, object]:
    formed_at = _parse_ts(row.get("setup_formed_at"))
    direction = str(row.get("direction_context", "")).upper()
    setup_reference = _float_value(row.get("setup_reference_level", row.get("entry_reference_level", "")))
    actual_setup_price = _actual_setup_price(feed, formed_at)
    tradable_entry = _float_value(row.get("tradable_entry_anchor"), actual_setup_price)
    invalidation = _float_value(row.get("stop_reference", row.get("invalidation_level", row.get("invalidation_reference", ""))))
    target_reference = _cell(row.get("target_reference", row.get("target_reference_zone", "")))
    target = _parse_target_zone(target_reference)

    forward = feed[(feed["_ts"] > formed_at) & (feed["_ts"] <= end_ts)].copy()
    if pd.isna(tradable_entry) and not forward.empty:
        tradable_entry = _float_value(forward.iloc[0].get("Open"), _float_value(forward.iloc[0].get("Close")))

    evaluation_start = _iso_z(forward["_ts"].min()) if not forward.empty else ""
    evaluation_end = _iso_z(forward["_ts"].max()) if not forward.empty else ""
    mfe = float("nan")
    mae = float("nan")
    target_at = pd.NaT
    invalidation_at = pd.NaT
    first_event = ""

    unresolved = pd.isna(tradable_entry) or pd.isna(invalidation) or target is None or direction not in {"UP", "DOWN"}
    insufficient = forward.empty
    if not insufficient and not pd.isna(tradable_entry):
        high = pd.to_numeric(forward["High"], errors="coerce")
        low = pd.to_numeric(forward["Low"], errors="coerce")
        if direction == "UP":
            mfe = max(0.0, ((high.max() - tradable_entry) / tradable_entry) * 100.0)
            mae = min(0.0, ((low.min() - tradable_entry) / tradable_entry) * 100.0)
        elif direction == "DOWN":
            mfe = max(0.0, ((tradable_entry - low.min()) / tradable_entry) * 100.0)
            mae = min(0.0, ((tradable_entry - high.max()) / tradable_entry) * 100.0)

    if not insufficient and target is not None:
        target_mask = _target_touch_mask(forward, target)
        if bool(target_mask.any()):
            target_at = forward.loc[target_mask, "_ts"].iloc[0]
    if not insufficient and not pd.isna(invalidation) and direction in {"UP", "DOWN"}:
        if direction == "UP":
            invalidation_mask = pd.to_numeric(forward["Low"], errors="coerce") <= invalidation
        else:
            invalidation_mask = pd.to_numeric(forward["High"], errors="coerce") >= invalidation
        if bool(invalidation_mask.any()):
            invalidation_at = forward.loc[invalidation_mask, "_ts"].iloc[0]

    target_touched = not pd.isna(target_at)
    invalidation_touched = not pd.isna(invalidation_at)
    if target_touched and invalidation_touched:
        if target_at <= invalidation_at:
            first_event = "TARGET"
            outcome = "BOTH_TARGET_AND_INVALIDATION_TARGET_FIRST"
        else:
            first_event = "INVALIDATION"
            outcome = "BOTH_TARGET_AND_INVALIDATION_INVALIDATION_FIRST"
    elif target_touched:
        first_event = "TARGET"
        outcome = "TARGET_FIRST"
    elif invalidation_touched:
        first_event = "INVALIDATION"
        outcome = "INVALIDATION_FIRST"
    elif insufficient:
        outcome = "INSUFFICIENT_FORWARD_DATA"
    elif unresolved:
        outcome = "TARGET_OR_INVALIDATION_UNRESOLVED"
    else:
        outcome = "NO_DECISIVE_OUTCOME"

    return {
        "setup_id": _cell(row.get("setup_id")),
        "interval_id": interval.interval_id,
        "setup_formed_at": _iso_z(formed_at),
        "setup_type": _cell(row.get("setup_type")),
        "direction_context": direction,
        "trigger_status": _cell(row.get("trigger_status")),
        "source_time_precision": _cell(row.get("source_time_precision")),
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "setup_reference_level": _round(setup_reference),
        "actual_setup_price": _round(actual_setup_price),
        "tradable_entry_anchor": _round(tradable_entry),
        "entry_reference_price": _round(tradable_entry),
        "invalidation_reference": _round(invalidation),
        "stop_reference": _round(invalidation),
        "target_reference": target_reference,
        "target_reference_zone": target_reference,
        "max_favorable_excursion_pct": _round(mfe),
        "max_adverse_excursion_pct": _round(mae),
        "target_touched": str(target_touched).lower(),
        "target_touched_at": _iso_z(target_at) if target_touched else "",
        "invalidation_touched": str(invalidation_touched).lower(),
        "invalidation_touched_at": _iso_z(invalidation_at) if invalidation_touched else "",
        "first_event": first_event,
        "outcome_label": outcome,
        "evidence_summary": _evidence_summary(
            forward_rows=len(forward),
            target=target,
            unresolved=unresolved,
            insufficient=insufficient,
            source_evidence=row.get("evidence_summary", ""),
            setup_reference=setup_reference,
            actual_setup_price=actual_setup_price,
            tradable_entry=tradable_entry,
        ),
    }


def _summary_text(results: pd.DataFrame, interval_manifests: list[dict[str, object]]) -> str:
    lines = [
        "# SHI RESET 38A Setup Replay Validation Summary",
        "",
        "Research-only replay validation of existing 37K setup timeline rows.",
        "",
        "- Detection source: existing `setup_research_timeline.csv` rows only.",
        "- Forward feed rows are used only after `setup_formed_at` for outcome evaluation.",
        "- No Backtester, Executor, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.",
        "",
    ]
    for manifest in interval_manifests:
        interval_id = manifest["interval_id"]
        frame = results[results["interval_id"] == interval_id] if not results.empty else pd.DataFrame(columns=SETUP_REPLAY_COLUMNS)
        outcomes = frame["outcome_label"].value_counts().to_dict() if not frame.empty else {}
        lines.extend(
            [
                f"## {interval_id}",
                "",
                f"- Window: `{manifest['start']}` -> `{manifest['end']}`",
                f"- 37K setup rows: {len(frame)}",
                f"- Rows by setup_type: {_counts_json(frame, 'setup_type')}",
                f"- Rows by direction_context: {_counts_json(frame, 'direction_context')}",
                f"- Rows by trigger_status: {_counts_json(frame, 'trigger_status')}",
                f"- Target-first count: {_target_first_count(frame)}",
                f"- Invalidation-first count: {_invalidation_first_count(frame)}",
                f"- No-decisive-outcome count: {int(outcomes.get('NO_DECISIVE_OUTCOME', 0))}",
                f"- Unresolved count: {int(outcomes.get('TARGET_OR_INVALIDATION_UNRESOLVED', 0))}",
                f"- Median MFE: {_metric(frame, 'max_favorable_excursion_pct', 'median')}",
                f"- Median MAE: {_metric(frame, 'max_adverse_excursion_pct', 'median')}",
                f"- Worst MAE: {_metric(frame, 'max_adverse_excursion_pct', 'min')}",
                f"- Best MFE: {_metric(frame, 'max_favorable_excursion_pct', 'max')}",
                "",
            ]
        )
    return "\n".join(lines)


def _load_feed_range(*, feed_root: Path, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> pd.DataFrame:
    frames = []
    day = start_ts.date()
    while day <= end_ts.date():
        path = feed_root / f"{day.isoformat()}.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["_ts"] = pd.to_datetime(frame.get("Timestamp"), errors="coerce", utc=True)
            frames.append(frame)
        day = day + timedelta(days=1)
    if not frames:
        return pd.DataFrame(columns=["_ts", "Open", "High", "Low", "Close"])
    feed = pd.concat(frames, ignore_index=True, sort=False)
    feed = feed[(feed["_ts"] >= start_ts) & (feed["_ts"] <= end_ts)].copy()
    return feed.sort_values("_ts", kind="mergesort").reset_index(drop=True)



def _actual_setup_price(feed: pd.DataFrame, formed_at: pd.Timestamp) -> float:
    if feed.empty or pd.isna(formed_at):
        return float("nan")
    matches = feed[feed["_ts"] == formed_at]
    if matches.empty:
        return float("nan")
    row = matches.iloc[0]
    return _float_value(row.get("Close"), _float_value(row.get("VWAP"), _float_value(row.get("Open"))))

def _parse_target_zone(value: object) -> dict[str, object] | None:
    text = _cell(value)
    parts = text.split(":")
    if len(parts) != 3 or "-" not in parts[2]:
        return None
    lower_text, upper_text = parts[2].split("-", 1)
    lower = _float_value(lower_text)
    upper = _float_value(upper_text)
    if pd.isna(lower) or pd.isna(upper):
        return None
    return {"zone_id": parts[0], "side": parts[1], "lower": min(lower, upper), "upper": max(lower, upper)}


def _target_touch_mask(feed: pd.DataFrame, target: dict[str, object]) -> pd.Series:
    high = pd.to_numeric(feed["High"], errors="coerce")
    low = pd.to_numeric(feed["Low"], errors="coerce")
    lower = float(target["lower"])
    upper = float(target["upper"])
    return (high >= lower) & (low <= upper)


def _evidence_summary(
    *,
    forward_rows: int,
    target: dict[str, object] | None,
    unresolved: bool,
    insufficient: bool,
    source_evidence: object,
    setup_reference: float,
    actual_setup_price: float,
    tradable_entry: float,
) -> str:
    parts = [
        f"forward_rows={forward_rows}",
        "forward_data_after_setup_formed_at_only=true",
        f"target_resolved={str(target is not None).lower()}",
        f"reference_unresolved={str(unresolved).lower()}",
        f"insufficient_forward_data={str(insufficient).lower()}",
        f"setup_reference_level={_round(setup_reference)}",
        f"actual_setup_price={_round(actual_setup_price)}",
        f"tradable_entry_anchor={_round(tradable_entry)}",
    ]
    source = _cell(source_evidence)
    if source:
        parts.append(f"source_setup_evidence={source}")
    return "; ".join(parts)


def _counts_json(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "{}"
    return json.dumps(frame[column].value_counts().to_dict(), sort_keys=True)


def _target_first_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return int(frame["outcome_label"].isin({"TARGET_FIRST", "BOTH_TARGET_AND_INVALIDATION_TARGET_FIRST"}).sum())


def _invalidation_first_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return int(frame["outcome_label"].isin({"INVALIDATION_FIRST", "BOTH_TARGET_AND_INVALIDATION_INVALIDATION_FIRST"}).sum())


def _metric(frame: pd.DataFrame, column: str, fn: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    series = pd.to_numeric(frame[column], errors="coerce").dropna()
    if series.empty:
        return ""
    if fn == "median":
        return str(round(float(series.median()), 6))
    if fn == "min":
        return str(round(float(series.min()), 6))
    if fn == "max":
        return str(round(float(series.max()), 6))
    return ""


def _assert_allowed_outcomes(results: pd.DataFrame) -> None:
    if results.empty:
        return
    found = set(results["outcome_label"].astype(str))
    unsupported = sorted(found - OUTCOME_LABELS)
    if unsupported:
        raise SetupReplayValidationError(f"unsupported outcome labels: {unsupported}")


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _parse_ts(value: object) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce", utc=True)


def _iso_z(value: object) -> str:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return ""
    return ts.isoformat().replace("+00:00", "Z")


def _float_value(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if pd.notna(number) else default


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


