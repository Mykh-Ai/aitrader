from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd


ARMED_REVIEW_VERSION = "SHI_RESET_38B_ARMED_SETUP_MANUAL_REVIEW_PACK_V0"

ARMED_REVIEW_CSV = "armed_setup_manual_review.csv"
ARMED_REVIEW_SUMMARY_MD = "armed_setup_manual_review_summary.md"
ARMED_REVIEW_MANIFEST_JSON = "armed_setup_manual_review_manifest.json"

MANUAL_REVIEW_QUESTION = (
    "1. Is the setup visually coherent? "
    "2. Is the setup late? "
    "3. Is the target zone logical? "
    "4. Is the invalidation logical? "
    "5. Did price move favorably before invalidation? "
    "6. Should this setup_type be kept for wider replay, modified, or rejected?"
)

ARMED_REVIEW_COLUMNS = [
    "setup_id",
    "interval_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "source_time_precision",
    "source_window_start",
    "source_window_end",
    "market_state",
    "dominant_side",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "invalidation_reference",
    "stop_reference",
    "target_reference",
    "target_reference_zone",
    "target_touched",
    "target_touched_at",
    "invalidation_touched",
    "invalidation_touched_at",
    "first_event",
    "max_favorable_excursion_pct",
    "max_adverse_excursion_pct",
    "chart_window_start",
    "chart_window_end",
    "chart_data_path",
    "manual_review_question",
]


class ArmedSetupReviewPackError(RuntimeError):
    """Raised when the ARMED setup review pack cannot be built."""


@dataclass(frozen=True)
class ReviewIntervalInput:
    interval_id: str
    start: str
    end: str
    setup_timeline_path: Path
    selected_zones_path: Path | None = None


@dataclass(frozen=True)
class ArmedSetupReviewPackResult:
    output_dir: Path
    review_path: Path
    summary_path: Path
    manifest_path: Path
    armed_count: int
    chart_data_count: int


def run_armed_setup_review_pack(
    *,
    replay_results_path: str | Path,
    intervals: list[ReviewIntervalInput],
    feed_dir: str | Path,
    output_dir: str | Path,
) -> ArmedSetupReviewPackResult:
    replay_path = Path(replay_results_path)
    if not replay_path.exists():
        raise ArmedSetupReviewPackError(f"missing replay results: {replay_path}")
    if not intervals:
        raise ArmedSetupReviewPackError("at least one interval input is required")

    feed_root = Path(feed_dir)
    out_dir = Path(output_dir)
    chart_dir = out_dir / "chart_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_dir.mkdir(parents=True, exist_ok=True)

    replay = _read_csv(replay_path)
    if replay.empty:
        armed = pd.DataFrame(columns=ARMED_REVIEW_COLUMNS)
    else:
        armed = replay[replay.get("trigger_status", "").astype(str) == "ARMED"].copy()

    timeline_by_interval = _load_timelines(intervals)
    rows: list[dict[str, object]] = []
    chart_count = 0
    for _, replay_row in armed.iterrows():
        interval_id = _cell(replay_row.get("interval_id"))
        setup_id = _cell(replay_row.get("setup_id"))
        timeline_row = _timeline_row(timeline_by_interval.get(interval_id, pd.DataFrame()), setup_id)
        if timeline_row is None:
            timeline_row = pd.Series(dtype=object)
        review_row = _review_row(replay_row, timeline_row)
        chart_data_path = _write_chart_data(
            review_row=review_row,
            interval=_interval_by_id(intervals, interval_id),
            feed_root=feed_root,
            chart_dir=chart_dir,
        )
        review_row["chart_data_path"] = str(chart_data_path)
        rows.append(review_row)
        chart_count += 1

    review = pd.DataFrame(rows, columns=ARMED_REVIEW_COLUMNS)
    review_path = out_dir / ARMED_REVIEW_CSV
    summary_path = out_dir / ARMED_REVIEW_SUMMARY_MD
    manifest_path = out_dir / ARMED_REVIEW_MANIFEST_JSON

    review.to_csv(review_path, index=False)
    summary_path.write_text(_summary_text(review, intervals), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "armed_review_version": ARMED_REVIEW_VERSION,
                "research_only": True,
                "input_replay_results_path": str(replay_path),
                "feed_dir": str(feed_root),
                "output_dir": str(out_dir),
                "filter": "trigger_status=ARMED",
                "watch_rows_excluded": int(len(replay) - len(armed)) if not replay.empty else 0,
                "armed_rows_included": int(len(review)),
                "chart_data_count": int(chart_count),
                "changes_setup_detection_logic": False,
                "uses_future_data_for_detection": False,
                "charts_are_review_only": True,
                "uses_backtester": False,
                "uses_executor": False,
                "uses_orders": False,
                "uses_entries_exits": False,
                "uses_pnl": False,
                "live_readiness_claim": False,
                "strategy_promotion": False,
                "intervals": [
                    {
                        "interval_id": item.interval_id,
                        "start": _iso_z(item.start),
                        "end": _iso_z(item.end),
                        "setup_timeline_path": str(item.setup_timeline_path),
                        "selected_zones_path": str(item.selected_zones_path or ""),
                    }
                    for item in intervals
                ],
                "outputs": {
                    "armed_setup_manual_review_csv": str(review_path),
                    "armed_setup_manual_review_summary_md": str(summary_path),
                    "chart_data_dir": str(chart_dir),
                },
                "repo_commit": _repo_commit(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return ArmedSetupReviewPackResult(out_dir, review_path, summary_path, manifest_path, int(len(review)), chart_count)


def _load_timelines(intervals: list[ReviewIntervalInput]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for item in intervals:
        if not item.setup_timeline_path.exists():
            raise ArmedSetupReviewPackError(f"missing setup timeline: {item.setup_timeline_path}")
        frame = _read_csv(item.setup_timeline_path)
        out[item.interval_id] = frame
    return out


def _timeline_row(timeline: pd.DataFrame, setup_id: str) -> pd.Series | None:
    if timeline.empty or "setup_id" not in timeline.columns:
        return None
    matches = timeline[timeline["setup_id"].astype(str) == setup_id]
    if matches.empty:
        return None
    return matches.iloc[0]


def _review_row(replay: pd.Series, setup: pd.Series) -> dict[str, object]:
    precision = _cell(setup.get("source_time_precision", replay.get("source_time_precision", "")))
    formed_at = _parse_ts(replay.get("setup_formed_at"))
    chart_start, chart_end = _chart_window(formed_at, precision)
    return {
        "setup_id": _cell(replay.get("setup_id")),
        "interval_id": _cell(replay.get("interval_id")),
        "setup_formed_at": _iso_z(formed_at),
        "setup_type": _cell(replay.get("setup_type")),
        "direction_context": _cell(replay.get("direction_context")),
        "source_time_precision": precision,
        "source_window_start": _iso_z(setup.get("source_window_start")),
        "source_window_end": _iso_z(setup.get("source_window_end")),
        "market_state": _cell(setup.get("market_state")),
        "dominant_side": _cell(setup.get("dominant_side")),
        "setup_reference_level": _cell(replay.get("setup_reference_level", setup.get("setup_reference_level", setup.get("entry_reference_level", "")))),
        "actual_setup_price": _cell(replay.get("actual_setup_price")),
        "tradable_entry_anchor": _cell(replay.get("tradable_entry_anchor", replay.get("entry_reference_price", ""))),
        "invalidation_reference": _cell(replay.get("invalidation_reference", setup.get("invalidation_level", ""))),
        "stop_reference": _cell(replay.get("stop_reference", replay.get("invalidation_reference", setup.get("invalidation_level", "")))),
        "target_reference": _cell(replay.get("target_reference", replay.get("target_reference_zone", setup.get("target_reference", setup.get("target_reference_zone", ""))))),
        "target_reference_zone": _cell(replay.get("target_reference_zone", setup.get("target_reference_zone", ""))),
        "target_touched": _cell(replay.get("target_touched")),
        "target_touched_at": _iso_z(replay.get("target_touched_at")),
        "invalidation_touched": _cell(replay.get("invalidation_touched")),
        "invalidation_touched_at": _iso_z(replay.get("invalidation_touched_at")),
        "first_event": _cell(replay.get("first_event")),
        "max_favorable_excursion_pct": _cell(replay.get("max_favorable_excursion_pct")),
        "max_adverse_excursion_pct": _cell(replay.get("max_adverse_excursion_pct")),
        "chart_window_start": _iso_z(chart_start),
        "chart_window_end": _iso_z(chart_end),
        "chart_data_path": "",
        "manual_review_question": MANUAL_REVIEW_QUESTION,
    }


def _chart_window(formed_at: pd.Timestamp, precision: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if pd.isna(formed_at):
        return pd.NaT, pd.NaT
    if precision == "RAW_REGIME_WINDOW_1440M":
        return formed_at - timedelta(hours=24), formed_at + timedelta(hours=48)
    return formed_at - timedelta(hours=6), formed_at + timedelta(hours=24)


def _write_chart_data(
    *,
    review_row: dict[str, object],
    interval: ReviewIntervalInput,
    feed_root: Path,
    chart_dir: Path,
) -> Path:
    start_ts = _parse_ts(review_row["chart_window_start"])
    end_ts = _parse_ts(review_row["chart_window_end"])
    feed = _load_feed_range(feed_root=feed_root, start_ts=start_ts, end_ts=end_ts)
    target = _parse_target_zone(review_row.get("target_reference"))
    feed["setup_id"] = review_row["setup_id"]
    feed["setup_formed_at"] = review_row["setup_formed_at"]
    feed["direction_context"] = review_row["direction_context"]
    feed["setup_reference_level"] = review_row["setup_reference_level"]
    feed["actual_setup_price"] = review_row["actual_setup_price"]
    feed["tradable_entry_anchor"] = review_row["tradable_entry_anchor"]
    feed["stop_reference"] = review_row["stop_reference"]
    feed["invalidation_reference"] = review_row["invalidation_reference"]
    feed["target_zone_lower"] = target["lower"] if target is not None else ""
    feed["target_zone_upper"] = target["upper"] if target is not None else ""
    feed["target_zone_side"] = target["side"] if target is not None else ""
    feed["chart_window_start"] = review_row["chart_window_start"]
    feed["chart_window_end"] = review_row["chart_window_end"]
    name = f"{_safe_name(interval.interval_id)}_{_safe_name(str(review_row['setup_id']))}_chart_data.csv"
    path = chart_dir / name
    feed.to_csv(path, index=False)
    return path


def _summary_text(review: pd.DataFrame, intervals: list[ReviewIntervalInput]) -> str:
    lines = [
        "# SHI RESET 38B ARMED Setup Manual Review Pack",
        "",
        "Research-only manual review pack for ARMED setup rows from 38A replay validation.",
        "",
        "- Filter: `trigger_status = ARMED`.",
        "- WATCH rows are excluded.",
        "- Chart data is review-only and is not used for setup detection.",
        "- No Backtester, Executor, orders, entries/exits, PnL, live-readiness, or strategy promotion.",
        "",
        f"- Total ARMED rows: {len(review)}",
        f"- Rows by setup_type: {_counts_json(review, 'setup_type')}",
        f"- Rows by direction_context: {_counts_json(review, 'direction_context')}",
        f"- Rows by first_event: {_counts_json(review, 'first_event')}",
        "",
    ]
    for item in intervals:
        frame = review[review["interval_id"] == item.interval_id] if not review.empty else pd.DataFrame()
        lines.extend(
            [
                f"## {item.interval_id}",
                "",
                f"- Window: `{_iso_z(item.start)}` -> `{_iso_z(item.end)}`",
                f"- ARMED rows: {len(frame)}",
                f"- Rows by setup_type: {_counts_json(frame, 'setup_type')}",
                f"- Rows by first_event: {_counts_json(frame, 'first_event')}",
                "",
            ]
        )
    return "\n".join(lines)


def _interval_by_id(intervals: list[ReviewIntervalInput], interval_id: str) -> ReviewIntervalInput:
    for item in intervals:
        if item.interval_id == interval_id:
            return item
    raise ArmedSetupReviewPackError(f"missing interval config for {interval_id}")


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
        return pd.DataFrame(columns=["Timestamp", "Open", "High", "Low", "Close"])
    feed = pd.concat(frames, ignore_index=True, sort=False)
    feed = feed[(feed["_ts"] >= start_ts) & (feed["_ts"] <= end_ts)].copy()
    feed = feed.sort_values("_ts", kind="mergesort").reset_index(drop=True)
    feed = feed.drop(columns=["_ts"])
    return feed


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


def _counts_json(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "{}"
    return json.dumps(frame[column].fillna("").astype(str).value_counts().to_dict(), sort_keys=True)


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


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""
