"""Audit exit and placement mechanics for SHORT reclaim context replay mismatches."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "group",
    "trade_count",
    "exit_reason_categories",
    "same_bar_collision_count",
    "holding_bars_mean",
    "holding_bars_median",
    "holding_bars_le1_share",
    "holding_bars_le3_share",
    "mean_trade_return",
    "median_trade_return",
    "mean_outcome_return",
    "median_outcome_return",
    "mean_replay_minus_outcome",
    "median_replay_minus_outcome",
    "mean_stop_distance",
    "median_stop_distance",
    "mean_target_distance",
    "median_target_distance",
    "mean_target_to_stop_ratio",
    "median_target_to_stop_ratio",
    "horizon_mfe_reached_target_share",
    "horizon_adverse_reached_stop_share",
    "both_target_and_stop_in_horizon_share",
    "mean_mfe_to_target",
    "median_mfe_to_target",
    "mean_adverse_to_stop",
    "median_adverse_to_stop",
]

DETAIL_COLUMNS = [
    "group",
    "run_id",
    "setup_id",
    "entry_signal_ts",
    "entry_activation_ts",
    "exit_ts",
    "exit_reason",
    "exit_reason_category",
    "holding_bars",
    "entry_price_effective",
    "initial_stop_price",
    "initial_target_price",
    "exit_price_effective",
    "trade_return",
    "outcome_return",
    "mfe",
    "mae",
    "replay_minus_outcome",
    "stop_distance",
    "target_distance",
    "target_to_stop_ratio",
    "mfe_to_target",
    "adverse_to_stop",
    "horizon_mfe_reached_target",
    "horizon_adverse_reached_stop",
    "same_bar_collision",
    "notes",
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


def bool_str(value: bool) -> str:
    return "True" if value else "False"


def fmt(value: float | None) -> str:
    return f"{value:.8f}" if value is not None else ""


def group_name(outcome_positive: bool, replay_positive: bool) -> str:
    if outcome_positive and replay_positive:
        return "both_positive"
    if outcome_positive and not replay_positive:
        return "outcome_positive_replay_negative"
    if not outcome_positive and replay_positive:
        return "outcome_negative_replay_positive"
    return "both_negative"


def load_rows(work_dir: Path, slice_name: str) -> list[dict[str, object]]:
    artifact_root = work_dir / "artifacts" / slice_name
    backtest_root = work_dir / "backtests" / slice_name
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    for artifact_dir in sorted(path for path in artifact_root.iterdir() if path.is_dir()):
        run_id = artifact_dir.name
        backtest_dir = backtest_root / run_id
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

            entry = float_value(trade.get("entry_price_effective"))
            stop = float_value(trade.get("initial_stop_price"))
            target = float_value(trade.get("initial_target_price"))
            exit_price = float_value(trade.get("exit_price_effective"))
            trade_return = float_value(trade.get("trade_return_pct"))
            close_return_pct = float_value(outcome.get("CloseReturn_Pct"))
            mfe_pct = float_value(outcome.get("MFE_Pct"))
            mae_pct = float_value(outcome.get("MAE_Pct"))
            holding_bars = float_value(trade.get("holding_bars"))

            required = [entry, stop, target, exit_price, trade_return, close_return_pct, mfe_pct, mae_pct]
            if any(value is None for value in required):
                continue

            # Analyzer outcomes are percent units; replay returns are decimal units.
            outcome_return = float(close_return_pct) / 100.0
            mfe = float(mfe_pct) / 100.0
            mae = float(mae_pct) / 100.0
            trade_ret = float(trade_return)
            entry_price = float(entry)
            stop_distance = abs(float(stop) - entry_price) / entry_price if entry_price else None
            target_distance = abs(entry_price - float(target)) / entry_price if entry_price else None
            adverse = max(0.0, -mae)
            target_to_stop = target_distance / stop_distance if stop_distance not in (None, 0.0) and target_distance is not None else None
            mfe_to_target = mfe / target_distance if target_distance not in (None, 0.0) else None
            adverse_to_stop = adverse / stop_distance if stop_distance not in (None, 0.0) else None
            reached_target = bool(target_distance is not None and mfe >= target_distance)
            reached_stop = bool(stop_distance is not None and adverse >= stop_distance)
            outcome_positive = outcome_return > 0
            replay_positive = trade_ret > 0
            notes = trade.get("notes", "")

            rows.append(
                {
                    "group": group_name(outcome_positive, replay_positive),
                    "run_id": run_id,
                    "setup_id": setup_id,
                    "entry_signal_ts": trade.get("entry_signal_ts", ""),
                    "entry_activation_ts": trade.get("entry_activation_ts", ""),
                    "exit_ts": trade.get("exit_ts", ""),
                    "exit_reason": trade.get("exit_reason", ""),
                    "exit_reason_category": trade.get("exit_reason_category", ""),
                    "holding_bars": holding_bars,
                    "entry_price_effective": entry_price,
                    "initial_stop_price": float(stop),
                    "initial_target_price": float(target),
                    "exit_price_effective": float(exit_price),
                    "trade_return": trade_ret,
                    "outcome_return": outcome_return,
                    "mfe": mfe,
                    "mae": mae,
                    "replay_minus_outcome": trade_ret - outcome_return,
                    "stop_distance": stop_distance,
                    "target_distance": target_distance,
                    "target_to_stop_ratio": target_to_stop,
                    "mfe_to_target": mfe_to_target,
                    "adverse_to_stop": adverse_to_stop,
                    "horizon_mfe_reached_target": reached_target,
                    "horizon_adverse_reached_stop": reached_stop,
                    "same_bar_collision": "same_bar_collision" in notes,
                    "notes": notes,
                }
            )
            seen.add(setup_id)
    return rows


def mean_or_none(values: list[float]) -> float | None:
    return mean(values) if values else None


def median_or_none(values: list[float]) -> float | None:
    return median(values) if values else None


def summarize_group(group: str, rows: list[dict[str, object]]) -> dict[str, str]:
    if not rows:
        return {column: "" for column in SUMMARY_COLUMNS} | {"group": group, "trade_count": "0"}

    def floats(name: str) -> list[float]:
        return [float(row[name]) for row in rows if row.get(name) is not None]

    holding = floats("holding_bars")
    exits = Counter(str(row["exit_reason_category"] or "UNKNOWN") for row in rows)
    reached_target = sum(1 for row in rows if row["horizon_mfe_reached_target"])
    reached_stop = sum(1 for row in rows if row["horizon_adverse_reached_stop"])
    both = sum(1 for row in rows if row["horizon_mfe_reached_target"] and row["horizon_adverse_reached_stop"])
    same_bar = sum(1 for row in rows if row["same_bar_collision"])

    return {
        "group": group,
        "trade_count": str(len(rows)),
        "exit_reason_categories": ";".join(f"{key}:{value}" for key, value in sorted(exits.items())),
        "same_bar_collision_count": str(same_bar),
        "holding_bars_mean": fmt(mean_or_none(holding)),
        "holding_bars_median": fmt(median_or_none(holding)),
        "holding_bars_le1_share": f"{100.0 * sum(1 for value in holding if value <= 1) / len(rows):.2f}",
        "holding_bars_le3_share": f"{100.0 * sum(1 for value in holding if value <= 3) / len(rows):.2f}",
        "mean_trade_return": fmt(mean_or_none(floats("trade_return"))),
        "median_trade_return": fmt(median_or_none(floats("trade_return"))),
        "mean_outcome_return": fmt(mean_or_none(floats("outcome_return"))),
        "median_outcome_return": fmt(median_or_none(floats("outcome_return"))),
        "mean_replay_minus_outcome": fmt(mean_or_none(floats("replay_minus_outcome"))),
        "median_replay_minus_outcome": fmt(median_or_none(floats("replay_minus_outcome"))),
        "mean_stop_distance": fmt(mean_or_none(floats("stop_distance"))),
        "median_stop_distance": fmt(median_or_none(floats("stop_distance"))),
        "mean_target_distance": fmt(mean_or_none(floats("target_distance"))),
        "median_target_distance": fmt(median_or_none(floats("target_distance"))),
        "mean_target_to_stop_ratio": fmt(mean_or_none(floats("target_to_stop_ratio"))),
        "median_target_to_stop_ratio": fmt(median_or_none(floats("target_to_stop_ratio"))),
        "horizon_mfe_reached_target_share": f"{100.0 * reached_target / len(rows):.2f}",
        "horizon_adverse_reached_stop_share": f"{100.0 * reached_stop / len(rows):.2f}",
        "both_target_and_stop_in_horizon_share": f"{100.0 * both / len(rows):.2f}",
        "mean_mfe_to_target": fmt(mean_or_none(floats("mfe_to_target"))),
        "median_mfe_to_target": fmt(median_or_none(floats("mfe_to_target"))),
        "mean_adverse_to_stop": fmt(mean_or_none(floats("adverse_to_stop"))),
        "median_adverse_to_stop": fmt(median_or_none(floats("adverse_to_stop"))),
    }


def detail_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        detail = {column: "" for column in DETAIL_COLUMNS}
        for column in DETAIL_COLUMNS:
            value = row.get(column)
            if isinstance(value, float):
                detail[column] = fmt(value)
            elif isinstance(value, bool):
                detail[column] = bool_str(value)
            elif value is not None:
                detail[column] = str(value)
        out.append(detail)
    return out


def write_note(path: Path, summary_rows: list[dict[str, str]], output_csv: Path, detail_csv: Path) -> None:
    by_group = {row["group"]: row for row in summary_rows}
    mismatch = by_group.get("outcome_positive_replay_negative", {})
    lines = [
        "# Short Reclaim Exit Placement Audit",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Key Read",
        "",
        f"- mismatch trades: {mismatch.get('trade_count', '')}",
        f"- mismatch exits: {mismatch.get('exit_reason_categories', '')}",
        f"- mismatch same-bar collisions: {mismatch.get('same_bar_collision_count', '')}",
        f"- mismatch median holding bars: {mismatch.get('holding_bars_median', '')}",
        f"- mismatch horizon MFE reached target share: {mismatch.get('horizon_mfe_reached_target_share', '')}%",
        f"- mismatch horizon adverse reached stop share: {mismatch.get('horizon_adverse_reached_stop_share', '')}%",
        f"- mismatch both target and stop in horizon share: {mismatch.get('both_target_and_stop_in_horizon_share', '')}%",
        f"- mismatch median MFE / target distance: {mismatch.get('median_mfe_to_target', '')}",
        f"- mismatch median adverse / stop distance: {mismatch.get('median_adverse_to_stop', '')}",
        "",
        "## Interpretation",
        "",
        "This audit does not test new parameters. It profiles whether the replay collapse is explained by stop/target placement, same-bar collisions, expiry, or short holding time.",
        "For mismatches, `horizon_mfe_reached_target_share` means the fixed-horizon analyzer path had enough favorable excursion to reach the current target at some point in the horizon. `horizon_adverse_reached_stop_share` means the fixed-horizon path also had enough adverse excursion to touch the current stop at some point.",
        "",
        f"Summary CSV: `{output_csv.as_posix()}`",
        f"Detail CSV: `{detail_csv.as_posix()}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", default="/tmp/short_reclaim_context_replay_experiment_2026-05-03")
    parser.add_argument("--slice", default="ctx_spike_count_ge2")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_exit_placement_audit_{date.today().isoformat()}.csv")
    parser.add_argument("--detail-csv", default=f"research/results/short_reclaim_exit_placement_audit_details_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_exit_placement_audit_{date.today().isoformat()}.md")
    args = parser.parse_args()

    rows = load_rows(Path(args.work_dir), args.slice)
    groups = [
        "all",
        "both_positive",
        "outcome_positive_replay_negative",
        "outcome_negative_replay_positive",
        "both_negative",
    ]
    summary_rows = []
    for group in groups:
        selected = rows if group == "all" else [row for row in rows if row["group"] == group]
        summary_rows.append(summarize_group(group, selected))

    mismatch_rows = [row for row in rows if row["group"] == "outcome_positive_replay_negative"]
    write_csv(Path(args.summary_csv), summary_rows, SUMMARY_COLUMNS)
    write_csv(Path(args.detail_csv), detail_rows(mismatch_rows), DETAIL_COLUMNS)
    write_note(Path(args.note), summary_rows, Path(args.summary_csv), Path(args.detail_csv))

    print(json.dumps({
        "rows": len(rows),
        "mismatch_rows": len(mismatch_rows),
        "summary_csv": args.summary_csv,
        "detail_csv": args.detail_csv,
        "note": args.note,
        "mismatch_summary": next(row for row in summary_rows if row["group"] == "outcome_positive_replay_negative"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
