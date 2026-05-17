"""Audit why observational SHORT reclaim signal changes under replay."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "slice",
    "joined_trades",
    "outcome_pos_rate",
    "replay_pos_rate",
    "both_positive",
    "outcome_positive_replay_negative",
    "outcome_negative_replay_positive",
    "both_negative",
    "mean_close_return_pct",
    "median_close_return_pct",
    "mean_trade_return_pct",
    "median_trade_return_pct",
    "mean_replay_minus_outcome",
    "median_replay_minus_outcome",
    "exit_reason_categories",
]

DETAIL_COLUMNS = [
    "slice",
    "run_id",
    "setup_id",
    "setup_type_original",
    "entry_signal_ts",
    "exit_reason",
    "exit_reason_category",
    "close_return_pct",
    "mfe_pct",
    "mae_pct",
    "trade_return_pct",
    "replay_minus_outcome",
    "outcome_positive",
    "replay_positive",
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


def load_joined(work_dir: Path, slice_name: str) -> list[dict[str, object]]:
    artifact_root = work_dir / "artifacts" / slice_name
    backtest_root = work_dir / "backtests" / slice_name
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for artifact_dir in sorted(path for path in artifact_root.iterdir() if path.is_dir()):
        run_id = artifact_dir.name
        backtest_dir = backtest_root / run_id
        selected_setups = {
            row.get("SetupId", ""): row
            for row in read_csv(artifact_dir / "analyzer_setups.csv")
            if row.get("SetupId")
        }
        outcomes = {
            row.get("SetupId", ""): row
            for row in read_csv(artifact_dir / "analyzer_setup_outcomes.csv")
            if row.get("SetupId")
        }
        for trade in read_csv(backtest_dir / "backtest_trades.csv"):
            setup_id = trade.get("source_setup_id", "")
            if not setup_id or setup_id in seen:
                continue
            trade_return = float_value(trade.get("trade_return_pct"))
            outcome = outcomes.get(setup_id)
            if trade_return is None or not outcome:
                continue
            close_return_pct = float_value(outcome.get("CloseReturn_Pct"))
            mfe_pct = float_value(outcome.get("MFE_Pct"))
            mae_pct = float_value(outcome.get("MAE_Pct"))
            if close_return_pct is None or mfe_pct is None or mae_pct is None:
                continue
            # Analyzer outcome fields are percent units (0.05 means 0.05%).
            # Ledger trade_return_pct is a decimal return (0.0005 means 0.05%).
            close_return = close_return_pct / 100.0
            mfe = mfe_pct / 100.0
            mae = mae_pct / 100.0
            setup = selected_setups.get(setup_id, {})
            rows.append(
                {
                    "slice": slice_name,
                    "run_id": run_id,
                    "setup_id": setup_id,
                    "setup_type_original": setup.get("SetupTypeOriginal", setup.get("SetupType", "")),
                    "entry_signal_ts": trade.get("entry_signal_ts", ""),
                    "exit_reason": trade.get("exit_reason", ""),
                    "exit_reason_category": trade.get("exit_reason_category", ""),
                    "close_return_pct": close_return,
                    "mfe_pct": mfe,
                    "mae_pct": mae,
                    "trade_return_pct": trade_return,
                    "replay_minus_outcome": trade_return - close_return,
                    "outcome_positive": close_return > 0,
                    "replay_positive": trade_return > 0,
                }
            )
            seen.add(setup_id)
    return rows


def fmt(value: float | None) -> str:
    return f"{value:.8f}" if value is not None else ""


def summarize(slice_name: str, rows: list[dict[str, object]]) -> dict[str, str]:
    close_returns = [float(row["close_return_pct"]) for row in rows]
    trade_returns = [float(row["trade_return_pct"]) for row in rows]
    deltas = [float(row["replay_minus_outcome"]) for row in rows]
    both_pos = sum(1 for row in rows if row["outcome_positive"] and row["replay_positive"])
    out_pos_rep_neg = sum(1 for row in rows if row["outcome_positive"] and not row["replay_positive"])
    out_neg_rep_pos = sum(1 for row in rows if not row["outcome_positive"] and row["replay_positive"])
    both_neg = sum(1 for row in rows if not row["outcome_positive"] and not row["replay_positive"])
    exits = Counter(str(row["exit_reason_category"] or "UNKNOWN") for row in rows)
    return {
        "slice": slice_name,
        "joined_trades": str(len(rows)),
        "outcome_pos_rate": f"{100.0 * sum(1 for value in close_returns if value > 0) / len(close_returns):.2f}" if rows else "",
        "replay_pos_rate": f"{100.0 * sum(1 for value in trade_returns if value > 0) / len(trade_returns):.2f}" if rows else "",
        "both_positive": str(both_pos),
        "outcome_positive_replay_negative": str(out_pos_rep_neg),
        "outcome_negative_replay_positive": str(out_neg_rep_pos),
        "both_negative": str(both_neg),
        "mean_close_return_pct": fmt(mean(close_returns) if close_returns else None),
        "median_close_return_pct": fmt(median(close_returns) if close_returns else None),
        "mean_trade_return_pct": fmt(mean(trade_returns) if trade_returns else None),
        "median_trade_return_pct": fmt(median(trade_returns) if trade_returns else None),
        "mean_replay_minus_outcome": fmt(mean(deltas) if deltas else None),
        "median_replay_minus_outcome": fmt(median(deltas) if deltas else None),
        "exit_reason_categories": ";".join(f"{key}:{value}" for key, value in sorted(exits.items())),
    }


def detail_csv_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "slice": str(row["slice"]),
                "run_id": str(row["run_id"]),
                "setup_id": str(row["setup_id"]),
                "setup_type_original": str(row["setup_type_original"]),
                "entry_signal_ts": str(row["entry_signal_ts"]),
                "exit_reason": str(row["exit_reason"]),
                "exit_reason_category": str(row["exit_reason_category"]),
                "close_return_pct": fmt(float(row["close_return_pct"])),
                "mfe_pct": fmt(float(row["mfe_pct"])),
                "mae_pct": fmt(float(row["mae_pct"])),
                "trade_return_pct": fmt(float(row["trade_return_pct"])),
                "replay_minus_outcome": fmt(float(row["replay_minus_outcome"])),
                "outcome_positive": str(bool(row["outcome_positive"])),
                "replay_positive": str(bool(row["replay_positive"])),
            }
        )
    return out


def write_note(path: Path, summary: dict[str, str], detail_csv: Path) -> None:
    lines = [
        "# Short Reclaim Replay Mismatch Audit",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Key Read",
        "",
        f"- joined trades: {summary['joined_trades']}",
        f"- observational outcome pos_rate: {summary['outcome_pos_rate']}%",
        f"- replay trade pos_rate: {summary['replay_pos_rate']}%",
        f"- outcome positive but replay negative: {summary['outcome_positive_replay_negative']}",
        f"- outcome negative but replay positive: {summary['outcome_negative_replay_positive']}",
        f"- mean close return: {summary['mean_close_return_pct']}",
        f"- mean trade return: {summary['mean_trade_return_pct']}",
        f"- mean replay minus outcome: {summary['mean_replay_minus_outcome']}",
        f"- exits: {summary['exit_reason_categories']}",
        "",
        "## Interpretation",
        "",
        "This audit measures the gap between fixed-horizon analyzer outcomes and deterministic replay returns for the same setup ids.",
        "A large drop from outcome pos_rate to replay pos_rate points to entry/exit/placement semantics, not only raw signal quality.",
        "",
        f"Detail CSV: `{detail_csv.as_posix()}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", default="/tmp/short_reclaim_context_replay_experiment_2026-05-03")
    parser.add_argument("--slice", default="ctx_spike_count_ge2")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_replay_mismatch_audit_{date.today().isoformat()}.csv")
    parser.add_argument("--detail-csv", default=f"research/results/short_reclaim_replay_mismatch_audit_details_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_replay_mismatch_audit_{date.today().isoformat()}.md")
    args = parser.parse_args()

    rows = load_joined(Path(args.work_dir), args.slice)
    summary = summarize(args.slice, rows)
    write_csv(Path(args.summary_csv), [summary], SUMMARY_COLUMNS)
    write_csv(Path(args.detail_csv), detail_csv_rows(rows), DETAIL_COLUMNS)
    write_note(Path(args.note), summary, Path(args.detail_csv))
    print(json.dumps({
        "summary": summary,
        "summary_csv": args.summary_csv,
        "detail_csv": args.detail_csv,
        "note": args.note,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
