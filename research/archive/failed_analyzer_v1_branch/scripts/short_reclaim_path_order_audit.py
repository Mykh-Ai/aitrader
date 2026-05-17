"""Raw-feed path order audit for SHORT reclaim context replay mismatches."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "scope",
    "trade_count",
    "activation_first_event_counts",
    "setup_first_event_counts",
    "activation_target_hit_share",
    "activation_stop_hit_share",
    "setup_target_hit_share",
    "setup_stop_hit_share",
    "setup_target_before_stop_share",
    "setup_stop_before_target_share",
    "setup_same_bar_share",
    "target_after_replay_exit_share",
    "median_setup_target_offset",
    "median_setup_stop_offset",
    "median_activation_target_offset",
    "median_activation_stop_offset",
]

DETAIL_COLUMNS = [
    "run_id",
    "setup_id",
    "setup_bar_ts",
    "entry_activation_ts",
    "exit_ts",
    "exit_reason_category",
    "holding_bars",
    "activation_first_event",
    "activation_target_offset",
    "activation_stop_offset",
    "setup_first_event",
    "setup_target_offset",
    "setup_stop_offset",
    "target_after_replay_exit",
    "stop_after_replay_exit",
    "entry_price_effective",
    "initial_stop_price",
    "initial_target_price",
    "trade_return",
    "outcome_return",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def float_value(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fmt_float(value: float | None) -> str:
    return f"{value:.8f}" if value is not None else ""


def fmt_offset(value: int | None) -> str:
    return str(value) if value is not None else ""


def load_manifest_feed_path(artifact_dir: Path) -> Path | None:
    import json as json_module

    manifest = artifact_dir / "run_manifest.json"
    if not manifest.exists():
        return None
    data = json_module.loads(manifest.read_text(encoding="utf-8"))
    paths = data.get("input_feed_paths") or []
    return Path(paths[0]) if paths else None


def load_feed(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(path):
        high = float_value(row.get("High"))
        low = float_value(row.get("Low"))
        if high is None or low is None:
            continue
        rows.append({"ts": parse_ts(row["Timestamp"]), "high": high, "low": low})
    return rows


def window(feed: list[dict[str, object]], start_ts: datetime, include_start: bool, bars: int) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for row in feed:
        ts = row["ts"]
        if not isinstance(ts, datetime):
            continue
        if (include_start and ts >= start_ts) or ((not include_start) and ts > start_ts):
            selected.append(row)
            if len(selected) >= bars:
                break
    return selected


def path_hits(rows: list[dict[str, object]], stop: float, target: float) -> dict[str, object]:
    target_offset: int | None = None
    stop_offset: int | None = None
    for offset, row in enumerate(rows):
        high = float(row["high"])
        low = float(row["low"])
        if target_offset is None and low <= target:
            target_offset = offset
        if stop_offset is None and high >= stop:
            stop_offset = offset
        if target_offset is not None and stop_offset is not None:
            break

    if target_offset is None and stop_offset is None:
        first = "NONE"
    elif target_offset is not None and stop_offset is not None and target_offset == stop_offset:
        first = "SAME_BAR"
    elif target_offset is not None and (stop_offset is None or target_offset < stop_offset):
        first = "TARGET_FIRST"
    else:
        first = "STOP_FIRST"

    return {
        "first_event": first,
        "target_offset": target_offset,
        "stop_offset": stop_offset,
    }


def load_mismatch_rows(work_dir: Path, slice_name: str) -> list[dict[str, object]]:
    artifact_root = work_dir / "artifacts" / slice_name
    backtest_root = work_dir / "backtests" / slice_name
    feed_cache: dict[Path, list[dict[str, object]]] = {}
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    for artifact_dir in sorted(path for path in artifact_root.iterdir() if path.is_dir()):
        run_id = artifact_dir.name
        backtest_dir = backtest_root / run_id
        feed_path = load_manifest_feed_path(artifact_dir)
        if feed_path is None:
            continue
        feed = feed_cache.setdefault(feed_path, load_feed(feed_path))
        outcomes = {
            row.get("SetupId", ""): row
            for row in read_csv(artifact_dir / "analyzer_setup_outcomes.csv")
            if row.get("SetupId")
        }

        for trade in read_csv(backtest_dir / "backtest_trades.csv"):
            setup_id = trade.get("source_setup_id", "")
            if not setup_id or setup_id in seen:
                continue
            outcome = outcomes.get(setup_id)
            if not outcome:
                continue
            trade_return = float_value(trade.get("trade_return_pct"))
            close_return_pct = float_value(outcome.get("CloseReturn_Pct"))
            entry = float_value(trade.get("entry_price_effective"))
            stop = float_value(trade.get("initial_stop_price"))
            target = float_value(trade.get("initial_target_price"))
            if None in (trade_return, close_return_pct, entry, stop, target):
                continue

            outcome_return = float(close_return_pct) / 100.0
            if not (outcome_return > 0 and float(trade_return) <= 0):
                seen.add(setup_id)
                continue

            setup_ts = parse_ts(outcome["SetupBarTs"])
            activation_ts = parse_ts(trade["entry_activation_ts"])
            exit_ts = parse_ts(trade["exit_ts"])
            activation_hits = path_hits(window(feed, activation_ts, include_start=True, bars=12), float(stop), float(target))
            setup_hits = path_hits(window(feed, setup_ts, include_start=False, bars=12), float(stop), float(target))
            target_offset = setup_hits["target_offset"]
            stop_offset = setup_hits["stop_offset"]

            target_after_exit = False
            stop_after_exit = False
            setup_forward = window(feed, setup_ts, include_start=False, bars=12)
            if target_offset is not None:
                target_ts = setup_forward[int(target_offset)]["ts"]
                target_after_exit = isinstance(target_ts, datetime) and target_ts > exit_ts
            if stop_offset is not None:
                stop_ts = setup_forward[int(stop_offset)]["ts"]
                stop_after_exit = isinstance(stop_ts, datetime) and stop_ts > exit_ts

            rows.append(
                {
                    "run_id": run_id,
                    "setup_id": setup_id,
                    "setup_bar_ts": outcome["SetupBarTs"],
                    "entry_activation_ts": trade.get("entry_activation_ts", ""),
                    "exit_ts": trade.get("exit_ts", ""),
                    "exit_reason_category": trade.get("exit_reason_category", ""),
                    "holding_bars": trade.get("holding_bars", ""),
                    "activation_first_event": activation_hits["first_event"],
                    "activation_target_offset": activation_hits["target_offset"],
                    "activation_stop_offset": activation_hits["stop_offset"],
                    "setup_first_event": setup_hits["first_event"],
                    "setup_target_offset": target_offset,
                    "setup_stop_offset": stop_offset,
                    "target_after_replay_exit": target_after_exit,
                    "stop_after_replay_exit": stop_after_exit,
                    "entry_price_effective": float(entry),
                    "initial_stop_price": float(stop),
                    "initial_target_price": float(target),
                    "trade_return": float(trade_return),
                    "outcome_return": outcome_return,
                }
            )
            seen.add(setup_id)
    return rows


def pct(count: int, total: int) -> str:
    return f"{100.0 * count / total:.2f}" if total else ""


def median_offset(rows: list[dict[str, object]], column: str) -> str:
    values = [int(row[column]) for row in rows if row.get(column) is not None]
    return f"{median(values):.2f}" if values else ""


def summarize(rows: list[dict[str, object]]) -> dict[str, str]:
    total = len(rows)
    activation_counts = Counter(str(row["activation_first_event"]) for row in rows)
    setup_counts = Counter(str(row["setup_first_event"]) for row in rows)
    return {
        "scope": "outcome_positive_replay_negative",
        "trade_count": str(total),
        "activation_first_event_counts": ";".join(f"{key}:{value}" for key, value in sorted(activation_counts.items())),
        "setup_first_event_counts": ";".join(f"{key}:{value}" for key, value in sorted(setup_counts.items())),
        "activation_target_hit_share": pct(sum(1 for row in rows if row["activation_target_offset"] is not None), total),
        "activation_stop_hit_share": pct(sum(1 for row in rows if row["activation_stop_offset"] is not None), total),
        "setup_target_hit_share": pct(sum(1 for row in rows if row["setup_target_offset"] is not None), total),
        "setup_stop_hit_share": pct(sum(1 for row in rows if row["setup_stop_offset"] is not None), total),
        "setup_target_before_stop_share": pct(sum(1 for row in rows if row["setup_first_event"] == "TARGET_FIRST"), total),
        "setup_stop_before_target_share": pct(sum(1 for row in rows if row["setup_first_event"] == "STOP_FIRST"), total),
        "setup_same_bar_share": pct(sum(1 for row in rows if row["setup_first_event"] == "SAME_BAR"), total),
        "target_after_replay_exit_share": pct(sum(1 for row in rows if row["target_after_replay_exit"]), total),
        "median_setup_target_offset": median_offset(rows, "setup_target_offset"),
        "median_setup_stop_offset": median_offset(rows, "setup_stop_offset"),
        "median_activation_target_offset": median_offset(rows, "activation_target_offset"),
        "median_activation_stop_offset": median_offset(rows, "activation_stop_offset"),
    }


def detail_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        detail = {column: "" for column in DETAIL_COLUMNS}
        for column in DETAIL_COLUMNS:
            value = row.get(column)
            if isinstance(value, float):
                detail[column] = fmt_float(value)
            elif isinstance(value, bool):
                detail[column] = "True" if value else "False"
            elif isinstance(value, int):
                detail[column] = fmt_offset(value)
            elif value is not None:
                detail[column] = str(value)
        out.append(detail)
    return out


def write_note(path: Path, summary: dict[str, str], summary_csv: Path, detail_csv: Path) -> None:
    lines = [
        "# Short Reclaim Path Order Audit",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Key Read",
        "",
        f"- mismatch trades: {summary['trade_count']}",
        f"- activation first events: {summary['activation_first_event_counts']}",
        f"- setup-window first events: {summary['setup_first_event_counts']}",
        f"- activation target hit share: {summary['activation_target_hit_share']}%",
        f"- setup target hit share: {summary['setup_target_hit_share']}%",
        f"- setup target before stop share: {summary['setup_target_before_stop_share']}%",
        f"- target after replay exit share: {summary['target_after_replay_exit_share']}%",
        f"- median setup target offset: {summary['median_setup_target_offset']}",
        f"- median activation stop offset: {summary['median_activation_stop_offset']}",
        "",
        "## Interpretation",
        "",
        "This audit checks raw-feed order for the outcome-positive / replay-negative mismatches. `activation` starts at replay entry activation; `setup-window` matches analyzer fixed-horizon semantics by starting after `SetupBarTs`.",
        "",
        f"Summary CSV: `{summary_csv.as_posix()}`",
        f"Detail CSV: `{detail_csv.as_posix()}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", default="/tmp/short_reclaim_context_replay_experiment_2026-05-03")
    parser.add_argument("--slice", default="ctx_spike_count_ge2")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_path_order_audit_{date.today().isoformat()}.csv")
    parser.add_argument("--detail-csv", default=f"research/results/short_reclaim_path_order_audit_details_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_path_order_audit_{date.today().isoformat()}.md")
    args = parser.parse_args()

    rows = load_mismatch_rows(Path(args.work_dir), args.slice)
    summary = summarize(rows)
    write_csv(Path(args.summary_csv), [summary], SUMMARY_COLUMNS)
    write_csv(Path(args.detail_csv), detail_rows(rows), DETAIL_COLUMNS)
    write_note(Path(args.note), summary, Path(args.summary_csv), Path(args.detail_csv))
    print(json.dumps({
        "rows": len(rows),
        "summary": summary,
        "summary_csv": args.summary_csv,
        "detail_csv": args.detail_csv,
        "note": args.note,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
