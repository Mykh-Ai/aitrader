from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from market_monitor.qualified_h1_sweep_reclaim import (
    OUTPUT_COLUMNS,
    QUALIFIED_H1_SWEEP_RECLAIM_VERSION,
    evaluate_qualified_h1_sweep_reclaim_at,
)


RUN_VERSION = "SHI_RESET_38N_QUALIFIED_H1_SWEEP_RECLAIM_REPLAY_ON_38J_WINDOW_V0"

TARGET_TIMESTAMPS = {
    "2026-05-26T16:59:00+00:00",
    "2026-05-27T05:59:00+00:00",
    "2026-06-01T00:59:00+00:00",
    "2026-06-05T16:59:00+00:00",
    "2026-06-09T17:59:00+00:00",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run 38N qualified H1 sweep/reclaim replay over the 38J window.")
    parser.add_argument("--classification", required=True, help="Path to wider_setup_classification_corrected.csv.")
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    parser.add_argument("--out-dir", required=True, help="Output directory for 38N artifacts.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    classification = pd.read_csv(args.classification)
    feed = _load_feed(Path(args.feed_dir), date.fromisoformat(args.start), date.fromisoformat(args.end))
    h1 = _build_h1_bars(feed)

    events = _evaluate_setup_rows(classification, h1)
    comparison = _compare_to_manual(classification, events)

    events_path = out_dir / "qualified_h1_sweep_reclaim_events.csv"
    comparison_path = out_dir / "qualified_h1_vs_manual_verdicts.csv"
    summary_path = out_dir / "qualified_h1_sweep_reclaim_summary.md"
    manifest_path = out_dir / "qualified_h1_sweep_reclaim_manifest.json"

    events.to_csv(events_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    summary_path.write_text(_summary(comparison), encoding="utf-8")
    manifest = {
        "run_version": RUN_VERSION,
        "qualified_layer_version": QUALIFIED_H1_SWEEP_RECLAIM_VERSION,
        "research_only": True,
        "uses_executor": False,
        "uses_backtester": False,
        "uses_orders": False,
        "uses_live_trading": False,
        "uses_pnl": False,
        "uses_position_sizing": False,
        "classification_path": str(args.classification),
        "feed_dir": str(args.feed_dir),
        "start": args.start,
        "end": args.end,
        "setup_rows_evaluated": int(len(classification)),
        "raw_sweep_rows": int((events["raw_sweep"].astype(str).str.lower() == "true").sum()),
        "qualified_h1_sweep_rows": int((events["qualified_h1_sweep"].astype(str).str.lower() == "true").sum()),
        "qualified_h1_failed_reclaim_rows": int(
            (events["qualified_h1_failed_reclaim"].astype(str).str.lower() == "true").sum()
        ),
        "outputs": {
            "qualified_h1_sweep_reclaim_events": str(events_path),
            "qualified_h1_vs_manual_verdicts": str(comparison_path),
            "summary": str(summary_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(
        "38N qualified H1 replay complete: "
        f"rows={len(comparison)} "
        f"raw_sweep={manifest['raw_sweep_rows']} "
        f"qualified_sweep={manifest['qualified_h1_sweep_rows']} "
        f"qualified_failed_reclaim={manifest['qualified_h1_failed_reclaim_rows']} "
        f"summary={summary_path}"
    )
    return 0


def _evaluate_setup_rows(classification: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, setup in classification.iterrows():
        formed_at = _format_ts(pd.Timestamp(setup["setup_formed_at"]))
        direction = "BEARISH" if str(setup.get("direction_context")) == "DOWN" else "BULLISH"
        level = _float_value(setup.get("setup_reference_level"))
        reference_type = _reference_type(setup)
        confirmed_at = _cell(setup.get("source_window_start")) or _cell(setup.get("setup_formed_at"))
        event = evaluate_qualified_h1_sweep_reclaim_at(
            h1_bars=h1,
            reference_level=level,
            reference_type=reference_type,
            direction=direction,
            confirmed_at=confirmed_at,
            sweep_h1_close_ts=formed_at,
            reference_id=str(setup.get("setup_id")),
            swing_center_timestamp=confirmed_at,
        )
        event.update(
            {
                "setup_id": str(setup.get("setup_id")),
                "setup_formed_at": str(setup.get("setup_formed_at")),
                "setup_type": str(setup.get("setup_type")),
                "manual_corrected_classification": str(setup.get("manual_corrected_classification", "")),
                "corrected_setup_role_classification": str(setup.get("setup_role_classification", "")),
            }
        )
        rows.append(event)
    columns = ["setup_id", "setup_formed_at", "setup_type", "corrected_setup_role_classification", "manual_corrected_classification"] + OUTPUT_COLUMNS
    return pd.DataFrame(rows).reindex(columns=columns)


def _compare_to_manual(classification: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    merged = classification.merge(
        events,
        on=["setup_id", "setup_formed_at", "setup_type"],
        how="left",
        suffixes=("", "_qualified"),
    )
    rows = []
    for _, row in merged.iterrows():
        manual = str(row.get("manual_corrected_classification", "") or row.get("setup_role_classification", ""))
        qualified_reclaim = str(row.get("qualified_h1_failed_reclaim", "")).lower() == "true"
        qualified_sweep = str(row.get("qualified_h1_sweep", "")).lower() == "true"
        raw_sweep = str(row.get("raw_sweep", "")).lower() == "true"
        match = _manual_match_status(manual, raw_sweep, qualified_sweep, qualified_reclaim)
        rows.append(
            {
                "setup_id": row.get("setup_id", ""),
                "setup_formed_at": row.get("setup_formed_at", ""),
                "setup_type": row.get("setup_type", ""),
                "target_case": str(row.get("setup_formed_at", "")) in TARGET_TIMESTAMPS,
                "manual_or_corrected_classification": manual,
                "original_38j_classification": row.get("original_38j_setup_role_classification", ""),
                "raw_sweep": row.get("raw_sweep", ""),
                "qualified_h1_sweep": row.get("qualified_h1_sweep", ""),
                "qualified_h1_failed_reclaim": row.get("qualified_h1_failed_reclaim", ""),
                "sweep_h1_close_ts": row.get("sweep_h1_close_ts", ""),
                "reclaim_h1_close_ts": row.get("reclaim_h1_close_ts", ""),
                "entry_candidate_ts": row.get("entry_candidate_ts", ""),
                "qualified_reject_reason": row.get("qualified_h1_sweep_reject_reason", ""),
                "reclaim_reject_reason": row.get("reclaim_reject_reason", ""),
                "manual_match_status": match,
                "policy_replay_allowed_corrected": row.get("policy_replay_allowed", ""),
                "immediate_entry_valid_corrected": row.get("immediate_entry_valid", ""),
                "evidence_summary": row.get("evidence_summary_qualified", row.get("evidence_summary", "")),
            }
        )
    return pd.DataFrame(rows)


def _manual_match_status(manual: str, raw_sweep: bool, qualified_sweep: bool, qualified_reclaim: bool) -> str:
    if manual == "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP":
        return "MATCH" if qualified_reclaim else "MANUAL_EXPECTS_PRIMARY_TRIGGER_BUT_QUALIFIED_RECLAIM_MISSING"
    if manual == "FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW":
        return "MATCH_REVIEW" if raw_sweep or qualified_sweep else "NO_LOCAL_SWEEP_FOR_CONTINUATION_REVIEW"
    if manual == "LATE_LAST_WAGON":
        return "MATCH_CONTROL" if not qualified_reclaim else "QUALIFIED_RECLAIM_BUT_MANUAL_LATE_CONTROL"
    if manual == "PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW":
        return "MATCH_CONTROL" if not qualified_reclaim else "QUALIFIED_RECLAIM_CONFLICTS_WITH_FAILED_CONTINUATION"
    return "NO_MANUAL_VERDICT"


def _summary(comparison: pd.DataFrame) -> str:
    lines = [
        "# SHI RESET 38N Qualified H1 Sweep/Reclaim Replay",
        "",
        "Research-only replay of the 38J window through the 38M qualified H1 sweep/reclaim layer.",
        "",
        f"- Rows evaluated: {len(comparison)}",
        f"- Raw H1 sweep rows: {_count_true(comparison, 'raw_sweep')}",
        f"- Qualified H1 sweep rows: {_count_true(comparison, 'qualified_h1_sweep')}",
        f"- Qualified H1 failed reclaim rows: {_count_true(comparison, 'qualified_h1_failed_reclaim')}",
        f"- Manual match status counts: {json.dumps(comparison['manual_match_status'].value_counts().to_dict(), sort_keys=True)}",
        "",
        "## Focus Cases",
        "",
        _markdown_table(
            comparison[comparison["target_case"].astype(bool)],
            [
                "setup_id",
                "setup_formed_at",
                "manual_or_corrected_classification",
                "raw_sweep",
                "qualified_h1_sweep",
                "qualified_h1_failed_reclaim",
                "manual_match_status",
                "qualified_reject_reason",
                "reclaim_reject_reason",
            ],
        ),
        "",
        "No Executor, orders, live trading, PnL, position sizing, Backtester execution logic, or strategy promotion is used.",
    ]
    return "\n".join(lines) + "\n"


def _load_feed(feed_dir: Path, start: date, end: date) -> pd.DataFrame:
    frames = []
    day = start
    while day <= end:
        path = feed_dir / f"{day.isoformat()}.csv"
        if path.exists():
            frames.append(pd.read_csv(path))
        day += timedelta(days=1)
    if not frames:
        return pd.DataFrame()
    frame = pd.concat(frames, ignore_index=True, sort=False)
    columns = {str(column).lower(): column for column in frame.columns}
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[columns["timestamp"]], utc=True, errors="coerce"),
            "open": pd.to_numeric(frame[columns["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[columns["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[columns["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[columns["close"]], errors="coerce"),
            "volume": pd.to_numeric(frame[columns["volume"]], errors="coerce") if "volume" in columns else 0.0,
        }
    ).dropna(subset=["timestamp", "open", "high", "low", "close"])


def _build_h1_bars(feed: pd.DataFrame) -> pd.DataFrame:
    if feed.empty:
        return pd.DataFrame()
    frame = feed.sort_values("timestamp", kind="mergesort").set_index("timestamp")
    grouped = frame.resample("1h", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        rows=("close", "size"),
    )
    grouped = grouped.dropna(subset=["open", "high", "low", "close"]).reset_index()
    grouped["timestamp"] = grouped["timestamp"] + pd.Timedelta(minutes=59)
    grouped["completed"] = grouped["rows"] >= 45
    return grouped[["timestamp", "open", "high", "low", "close", "volume", "completed"]]


def _reference_type(setup: pd.Series) -> str:
    if str(setup.get("selected_research_stop_type", "")) == "structural_zone_stop":
        return "ACTIVE_STRUCTURAL_LIQUIDITY_ZONE"
    return "H1_SWING_HIGH" if str(setup.get("direction_context", "")) == "DOWN" else "H1_SWING_LOW"


def _float_value(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _cell(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def _format_ts(value: object) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.isoformat().replace("+00:00", "Z")


def _count_true(frame: pd.DataFrame, column: str) -> int:
    return int((frame[column].astype(str).str.lower() == "true").sum()) if column in frame else 0


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].iterrows():
        lines.append("| " + " | ".join(_cell(row[column]).replace("|", "\\|") for column in columns) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
