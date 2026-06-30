from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from market_monitor.qualified_h1_sweep_reclaim import (
    QUALIFIED_H1_SWEEP_RECLAIM_VERSION,
    evaluate_qualified_h1_sweep_reclaim_at,
)
from market_monitor.run_qualified_h1_replay_38j_window import _build_h1_bars, _load_feed, _reference_type


RUN_VERSION = "SHI_RESET_38O_SEQUENCE_WINDOW_QUALIFIED_H1_REPLAY_V0"
LOOKBACK_H1_BARS = 8
PRIMARY_SEQUENCE_MAX_AGE_H1_BARS = 3

TARGET_TIMESTAMPS = {
    "2026-05-26T16:59:00+00:00",
    "2026-05-27T05:59:00+00:00",
    "2026-06-01T00:59:00+00:00",
    "2026-06-05T16:59:00+00:00",
    "2026-06-09T17:59:00+00:00",
}

EVENT_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "candidate_h1_close_ts",
    "sequence_window_start",
    "sequence_window_end",
    "raw_sweep",
    "qualified_h1_sweep",
    "qualified_h1_failed_reclaim",
    "reclaim_h1_close_ts",
    "entry_candidate_ts",
    "sweep_reference_level",
    "sweep_reference_type",
    "reaction_abs",
    "penetration_abs",
    "sweep_wick_present",
    "sweep_body_direction",
    "sweep_volume_ratio",
    "qualified_h1_sweep_reject_reason",
    "reclaim_reject_reason",
    "evidence_summary",
]

LINK_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "corrected_research_classification",
    "sequence_window_start",
    "sequence_window_end",
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
    "manual_match_status",
    "evidence_summary",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run 38O sequence-window qualified H1 replay.")
    parser.add_argument("--classification", required=True, help="Path to wider_setup_classification_corrected.csv.")
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD.")
    parser.add_argument("--out-dir", required=True, help="Output directory for 38O artifacts.")
    parser.add_argument("--lookback-h1-bars", type=int, default=LOOKBACK_H1_BARS)
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    classification = pd.read_csv(args.classification)
    feed = _load_feed(Path(args.feed_dir), date.fromisoformat(args.start), date.fromisoformat(args.end))
    h1 = _build_h1_bars(feed)

    events, links = run_sequence_window_replay(
        classification=classification,
        h1=h1,
        lookback_h1_bars=args.lookback_h1_bars,
    )
    comparison = links[
        [
            "setup_id",
            "setup_formed_at",
            "corrected_research_classification",
            "qualified_sequence_found",
            "qualified_h1_sweep_ts",
            "qualified_h1_failed_reclaim",
            "entry_candidate_ts",
            "sequence_age_h1_bars_at_setup",
            "sequence_valid_for_setup",
            "manual_match_status",
            "sequence_reject_reason",
        ]
    ].copy()

    events_path = out_dir / "sequence_window_qualified_h1_events.csv"
    links_path = out_dir / "sequence_window_setup_links.csv"
    comparison_path = out_dir / "sequence_window_vs_manual_verdicts.csv"
    summary_path = out_dir / "sequence_window_summary.md"
    manifest_path = out_dir / "sequence_window_manifest.json"

    events.to_csv(events_path, index=False)
    links.to_csv(links_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    summary_path.write_text(_summary(links, comparison), encoding="utf-8")
    manifest = {
        "run_version": RUN_VERSION,
        "qualified_layer_version": QUALIFIED_H1_SWEEP_RECLAIM_VERSION,
        "research_only": True,
        "uses_executor": False,
        "uses_orders": False,
        "uses_live_trading": False,
        "uses_entries_exits": False,
        "uses_pnl": False,
        "uses_position_sizing": False,
        "uses_live_readiness": False,
        "uses_strategy_promotion": False,
        "classification_path": str(args.classification),
        "feed_dir": str(args.feed_dir),
        "start": args.start,
        "end": args.end,
        "lookback_h1_bars": args.lookback_h1_bars,
        "setup_rows_evaluated": int(len(links)),
        "h1_candidate_evaluations": int(len(events)),
        "qualified_sequence_links": int((links["qualified_sequence_found"].astype(str).str.lower() == "true").sum()),
        "valid_sequence_links": int((links["sequence_valid_for_setup"].astype(str).str.lower() == "true").sum()),
        "outputs": {
            "sequence_window_qualified_h1_events": str(events_path),
            "sequence_window_setup_links": str(links_path),
            "sequence_window_vs_manual_verdicts": str(comparison_path),
            "summary": str(summary_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "38O sequence-window replay complete: "
        f"setups={len(links)} "
        f"qualified_links={manifest['qualified_sequence_links']} "
        f"valid_links={manifest['valid_sequence_links']} "
        f"summary={summary_path}"
    )
    return 0


def run_sequence_window_replay(
    *,
    classification: pd.DataFrame,
    h1: pd.DataFrame,
    lookback_h1_bars: int = LOOKBACK_H1_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_rows: list[dict[str, object]] = []
    link_rows: list[dict[str, object]] = []
    for _, setup in classification.iterrows():
        setup_events = _evaluate_sequence_for_setup(setup, h1, lookback_h1_bars)
        event_rows.extend(setup_events)
        link_rows.append(_link_row(setup, h1, setup_events))
    return (
        pd.DataFrame(event_rows, columns=EVENT_COLUMNS),
        pd.DataFrame(link_rows, columns=LINK_COLUMNS),
    )


def _evaluate_sequence_for_setup(setup: pd.Series, h1: pd.DataFrame, lookback_h1_bars: int) -> list[dict[str, object]]:
    setup_ts = _ts(setup["setup_formed_at"])
    window_end = setup_ts
    window_start = setup_ts - pd.Timedelta(hours=lookback_h1_bars)
    candidates = h1[(h1["timestamp"] >= window_start) & (h1["timestamp"] <= window_end)].copy()
    direction = "BEARISH" if str(setup.get("direction_context", "")) == "DOWN" else "BULLISH"
    level = _float_value(setup.get("setup_reference_level"))
    reference_type = _reference_type(setup)
    confirmed_at = _cell(setup.get("source_window_start")) or _cell(setup.get("setup_formed_at"))
    rows: list[dict[str, object]] = []
    for _, bar in candidates.iterrows():
        event = evaluate_qualified_h1_sweep_reclaim_at(
            h1_bars=h1,
            reference_level=level,
            reference_type=reference_type,
            direction=direction,
            confirmed_at=confirmed_at,
            sweep_h1_close_ts=_format_ts(bar["timestamp"]),
            reference_id=str(setup.get("setup_id")),
            swing_center_timestamp=confirmed_at,
        )
        rows.append(
            {
                "setup_id": _cell(setup.get("setup_id")),
                "setup_formed_at": _cell(setup.get("setup_formed_at")),
                "candidate_h1_close_ts": _format_ts(bar["timestamp"]),
                "sequence_window_start": _format_ts(window_start),
                "sequence_window_end": _format_ts(window_end),
                "raw_sweep": event.get("raw_sweep", ""),
                "qualified_h1_sweep": event.get("qualified_h1_sweep", ""),
                "qualified_h1_failed_reclaim": event.get("qualified_h1_failed_reclaim", ""),
                "reclaim_h1_close_ts": event.get("reclaim_h1_close_ts", ""),
                "entry_candidate_ts": event.get("entry_candidate_ts", ""),
                "entry_candidate_price": event.get("entry_candidate_price", ""),
                "sweep_reference_level": event.get("sweep_reference_level", ""),
                "sweep_reference_type": event.get("sweep_reference_type", ""),
                "level_age_h1_bars": event.get("level_age_h1_bars", ""),
                "reaction_abs": event.get("reaction_abs", ""),
                "penetration_abs": event.get("penetration_abs", ""),
                "sweep_wick_present": event.get("sweep_wick_present", ""),
                "sweep_body_direction": event.get("sweep_body_direction", ""),
                "sweep_volume_ratio": event.get("sweep_volume_ratio", ""),
                "reclaim_bar_number_after_sweep": event.get("reclaim_bar_number_after_sweep", ""),
                "qualified_h1_sweep_reject_reason": event.get("qualified_h1_sweep_reject_reason", ""),
                "reclaim_reject_reason": event.get("reclaim_reject_reason", ""),
                "evidence_summary": event.get("evidence_summary", ""),
            }
        )
    return rows


def _link_row(setup: pd.Series, h1: pd.DataFrame, events: list[dict[str, object]]) -> dict[str, object]:
    setup_ts = _ts(setup["setup_formed_at"])
    qualified = [
        row for row in events if str(row.get("qualified_h1_failed_reclaim", "")).lower() == "true"
    ]
    chosen = _choose_sequence_event(qualified)
    fallback = _choose_fallback_event(events)
    event = chosen or fallback or {}
    qualified_found = chosen is not None
    entry_ts = _optional_ts(event.get("entry_candidate_ts", ""))
    age = _h1_age(entry_ts, setup_ts) if entry_ts is not None else ""
    valid = bool(qualified_found and age != "" and float(age) <= PRIMARY_SEQUENCE_MAX_AGE_H1_BARS)
    manual = _manual_classification(setup)
    match = _manual_match_status(manual, qualified_found, valid)
    reject = "" if qualified_found else _sequence_reject_reason(events)
    if qualified_found and not valid:
        reject = "qualified_sequence_too_old_for_primary_setup"
    sweep_bar = _h1_bar_at(h1, event.get("candidate_h1_close_ts", ""))
    return {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_formed_at": _cell(setup.get("setup_formed_at")),
        "setup_type": _cell(setup.get("setup_type")),
        "corrected_research_classification": manual,
        "sequence_window_start": event.get("sequence_window_start", ""),
        "sequence_window_end": event.get("sequence_window_end", ""),
        "qualified_sequence_found": str(qualified_found).lower(),
        "qualified_h1_sweep_ts": event.get("candidate_h1_close_ts", "") if qualified_found else "",
        "qualified_h1_failed_reclaim": event.get("qualified_h1_failed_reclaim", "") if qualified_found else "false",
        "reclaim_h1_close_ts": event.get("reclaim_h1_close_ts", "") if qualified_found else "",
        "entry_candidate_ts": event.get("entry_candidate_ts", "") if qualified_found else "",
        "entry_candidate_price": event.get("entry_candidate_price", "") if qualified_found else "",
        "swept_level": event.get("sweep_reference_level", ""),
        "swept_level_type": event.get("sweep_reference_type", ""),
        "sweep_h1_high": _round(sweep_bar.get("high", "")),
        "sweep_h1_low": _round(sweep_bar.get("low", "")),
        "sweep_h1_close": _round(sweep_bar.get("close", "")),
        "sweep_h1_volume": _round(sweep_bar.get("volume", "")),
        "sweep_volume_ratio": event.get("sweep_volume_ratio", ""),
        "level_age_h1_bars": event.get("level_age_h1_bars", ""),
        "reaction_abs": event.get("reaction_abs", ""),
        "penetration_abs": event.get("penetration_abs", ""),
        "wick_quality": event.get("sweep_wick_present", ""),
        "reclaim_bar_number_after_sweep": event.get("reclaim_bar_number_after_sweep", "") if qualified_found else "",
        "sequence_age_h1_bars_at_setup": age,
        "sequence_valid_for_setup": str(valid).lower(),
        "setup_review_lag_h1_bars": age,
        "sequence_reject_reason": reject,
        "manual_match_status": match,
        "evidence_summary": _link_evidence(event, qualified_found, valid, reject),
    }


def _choose_sequence_event(events: list[dict[str, object]]) -> dict[str, object] | None:
    if not events:
        return None
    return sorted(events, key=lambda row: _ts(row["entry_candidate_ts"]), reverse=True)[0]


def _choose_fallback_event(events: list[dict[str, object]]) -> dict[str, object] | None:
    raw = [row for row in events if str(row.get("raw_sweep", "")).lower() == "true"]
    if raw:
        return raw[-1]
    return events[-1] if events else None


def _sequence_reject_reason(events: list[dict[str, object]]) -> str:
    raw = [row for row in events if str(row.get("raw_sweep", "")).lower() == "true"]
    if not raw:
        return "no_raw_sweep_in_sequence_window"
    reasons = [str(row.get("qualified_h1_sweep_reject_reason", "")) for row in raw if row.get("qualified_h1_sweep_reject_reason")]
    return "no_qualified_h1_failed_reclaim_in_sequence_window" + (": " + " || ".join(reasons[-3:]) if reasons else "")


def _manual_match_status(manual: str, qualified_found: bool, valid: bool) -> str:
    if manual == "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP":
        return "MATCH" if valid else "MANUAL_EXPECTS_SEQUENCE_BUT_QUALIFIED_SEQUENCE_MISSING"
    if manual == "FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW":
        return "MATCH_REVIEW" if qualified_found else "NO_QUALIFIED_SEQUENCE_FOR_CONTINUATION_REVIEW"
    if manual == "LATE_LAST_WAGON":
        return "MATCH_CONTROL" if not valid else "QUALIFIED_SEQUENCE_CONFLICTS_WITH_LATE_CONTROL"
    if manual == "PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW":
        return "MATCH_CONTROL" if not valid else "QUALIFIED_SEQUENCE_CONFLICTS_WITH_FAILED_CONTINUATION"
    return "NO_MANUAL_VERDICT"


def _manual_classification(setup: pd.Series) -> str:
    value = _cell(setup.get("manual_corrected_classification"))
    if value and value.lower() != "nan":
        return value
    return _cell(setup.get("setup_role_classification"))


def _h1_bar_at(h1: pd.DataFrame, timestamp: object) -> pd.Series:
    if not timestamp:
        return pd.Series(dtype=object)
    ts = _ts(timestamp)
    rows = h1[h1["timestamp"] == ts]
    return rows.iloc[0] if not rows.empty else pd.Series(dtype=object)


def _h1_age(entry_ts: pd.Timestamp, setup_ts: pd.Timestamp) -> float:
    return max(0.0, (setup_ts - entry_ts).total_seconds() / 3600.0)


def _optional_ts(value: object) -> pd.Timestamp | None:
    if not value:
        return None
    try:
        return _ts(value)
    except Exception:
        return None


def _link_evidence(event: dict[str, object], qualified_found: bool, valid: bool, reject: str) -> str:
    if qualified_found:
        return (
            "sequence-linked candidate; entry_candidate_ts=reclaim_close_ts; "
            f"sequence_valid_for_setup={str(valid).lower()}; reject_reason={reject}"
        )
    return f"no qualified sequence found; {reject}; raw_sweep_alone_is_not_entry_trigger"


def _summary(links: pd.DataFrame, comparison: pd.DataFrame) -> str:
    focus = links[links["setup_formed_at"].isin(TARGET_TIMESTAMPS)]
    lines = [
        "# SHI RESET 38O Sequence-Window Qualified H1 Replay",
        "",
        "Research-only replay. Setup timestamp is treated as review time; qualified trigger time remains reclaim/rejection close time.",
        "",
        f"- Setup rows evaluated: {len(links)}",
        f"- Qualified sequence links: {_count_true(links, 'qualified_sequence_found')}",
        f"- Valid sequence links for setup: {_count_true(links, 'sequence_valid_for_setup')}",
        f"- Manual match status counts: {json.dumps(comparison['manual_match_status'].value_counts().to_dict(), sort_keys=True)}",
        "",
        "## Focus Cases",
        "",
        _markdown_table(
            focus,
            [
                "setup_id",
                "setup_formed_at",
                "corrected_research_classification",
                "qualified_sequence_found",
                "qualified_h1_sweep_ts",
                "entry_candidate_ts",
                "sequence_age_h1_bars_at_setup",
                "sequence_valid_for_setup",
                "manual_match_status",
                "sequence_reject_reason",
            ],
        ),
        "",
        "No Executor, orders, live trading, entries/exits, PnL, position sizing, live-readiness, or strategy promotion is used.",
    ]
    return "\n".join(lines) + "\n"


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].iterrows():
        lines.append("| " + " | ".join(_cell(row[column]).replace("|", "\\|") for column in columns) + " |")
    return "\n".join(lines)


def _count_true(frame: pd.DataFrame, column: str) -> int:
    return int((frame[column].astype(str).str.lower() == "true").sum()) if column in frame else 0


def _ts(value: object) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts


def _format_ts(value: object) -> str:
    return _ts(value).isoformat().replace("+00:00", "Z")


def _cell(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def _float_value(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _round(value: object) -> object:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(number):
        return ""
    return round(number, 6)


if __name__ == "__main__":
    raise SystemExit(main())
