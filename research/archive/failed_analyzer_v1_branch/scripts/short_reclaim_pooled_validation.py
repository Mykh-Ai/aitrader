"""Pooled validation for SHORT reclaim context replay experiment outputs.

Consumes trade ledgers from `short_reclaim_context_replay_experiment.py` and
evaluates campaign-level behavior after deduplicating repeated setup ids.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "slice",
    "basis",
    "trade_count",
    "days",
    "pos_rate",
    "mean_return",
    "median_return",
    "sum_return",
    "max_drawdown",
    "positive_day_rate",
    "largest_day_trade_share",
    "largest_day_return_share",
    "best_day",
    "best_day_sum_return",
    "worst_day",
    "worst_day_sum_return",
    "avg_win",
    "avg_loss",
    "payoff_ratio",
    "notes",
]

COST_COLUMNS = [
    "slice",
    "basis",
    "cost_per_trade",
    "trade_count",
    "pos_rate_after_cost",
    "mean_return_after_cost",
    "median_return_after_cost",
    "sum_return_after_cost",
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


def day_from_trade(row: dict[str, str]) -> str:
    ts = row.get("entry_signal_ts") or row.get("entry_activation_ts") or ""
    return ts[:10] if len(ts) >= 10 else "UNKNOWN"


def load_trades(run_csv: Path) -> list[dict[str, str]]:
    run_rows = read_csv(run_csv)
    trades: list[dict[str, str]] = []
    for run in run_rows:
        if run.get("status") != "COMPLETED":
            continue
        output_dir = Path(run.get("output_dir", ""))
        trade_path = output_dir / "backtest_trades.csv"
        for trade in read_csv(trade_path):
            ret = float_value(trade.get("trade_return_pct"))
            if ret is None:
                continue
            enriched = dict(trade)
            enriched["slice"] = run.get("slice", "")
            enriched["run_id"] = run.get("run_id", "")
            enriched["_return"] = ret
            enriched["_day"] = day_from_trade(trade)
            trades.append(enriched)
    return trades


def dedupe_trades(trades: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for trade in sorted(trades, key=lambda row: (row["slice"], row.get("entry_signal_ts", ""), row.get("source_setup_id", ""))):
        key = (trade["slice"], trade.get("source_setup_id", "") or trade.get("trade_id", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(trade)
    return out


def max_drawdown(returns: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for ret in returns:
        equity += ret
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return max_dd


def metric_row(slice_name: str, basis: str, trades: list[dict[str, str]], notes: str) -> dict[str, str]:
    ordered = sorted(trades, key=lambda row: row.get("entry_signal_ts", ""))
    returns = [float(row["_return"]) for row in ordered]
    day_returns: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        day_returns[row["_day"]].append(float(row["_return"]))
    day_sums = {day: sum(values) for day, values in day_returns.items()}
    positives = [value for value in returns if value > 0]
    negatives = [value for value in returns if value < 0]
    positive_day_count = sum(1 for value in day_sums.values() if value > 0)
    largest_day_trade = max((len(values) for values in day_returns.values()), default=0)
    positive_sum = sum(value for value in day_sums.values() if value > 0)
    largest_day_return = max((value for value in day_sums.values() if value > 0), default=0.0)
    best_day, best_value = max(day_sums.items(), key=lambda item: item[1], default=("", 0.0))
    worst_day, worst_value = min(day_sums.items(), key=lambda item: item[1], default=("", 0.0))
    avg_win = mean(positives) if positives else None
    avg_loss = mean(negatives) if negatives else None
    payoff = abs(avg_win / avg_loss) if avg_win is not None and avg_loss not in (None, 0.0) else None
    return {
        "slice": slice_name,
        "basis": basis,
        "trade_count": str(len(returns)),
        "days": str(len(day_returns)),
        "pos_rate": f"{100.0 * len(positives) / len(returns):.2f}" if returns else "",
        "mean_return": f"{mean(returns):.8f}" if returns else "",
        "median_return": f"{median(returns):.8f}" if returns else "",
        "sum_return": f"{sum(returns):.8f}" if returns else "",
        "max_drawdown": f"{max_drawdown(returns):.8f}" if returns else "",
        "positive_day_rate": f"{100.0 * positive_day_count / len(day_returns):.2f}" if day_returns else "",
        "largest_day_trade_share": f"{100.0 * largest_day_trade / len(returns):.2f}" if returns else "",
        "largest_day_return_share": f"{100.0 * largest_day_return / positive_sum:.2f}" if positive_sum else "",
        "best_day": best_day,
        "best_day_sum_return": f"{best_value:.8f}",
        "worst_day": worst_day,
        "worst_day_sum_return": f"{worst_value:.8f}",
        "avg_win": f"{avg_win:.8f}" if avg_win is not None else "",
        "avg_loss": f"{avg_loss:.8f}" if avg_loss is not None else "",
        "payoff_ratio": f"{payoff:.4f}" if payoff is not None else "",
        "notes": notes,
    }


def cost_rows(slice_name: str, basis: str, trades: list[dict[str, str]], costs: list[float]) -> list[dict[str, str]]:
    returns = [float(row["_return"]) for row in trades]
    rows: list[dict[str, str]] = []
    for cost in costs:
        adjusted = [ret - cost for ret in returns]
        positives = [ret for ret in adjusted if ret > 0]
        rows.append(
            {
                "slice": slice_name,
                "basis": basis,
                "cost_per_trade": f"{cost:.8f}",
                "trade_count": str(len(adjusted)),
                "pos_rate_after_cost": f"{100.0 * len(positives) / len(adjusted):.2f}" if adjusted else "",
                "mean_return_after_cost": f"{mean(adjusted):.8f}" if adjusted else "",
                "median_return_after_cost": f"{median(adjusted):.8f}" if adjusted else "",
                "sum_return_after_cost": f"{sum(adjusted):.8f}" if adjusted else "",
            }
        )
    return rows


def write_note(path: Path, summary_rows: list[dict[str, str]], cost_summary: list[dict[str, str]], output_csv: Path, cost_csv: Path) -> None:
    by_key = {(row["slice"], row["basis"]): row for row in summary_rows}
    ctx = by_key.get(("ctx_spike_count_ge2", "dedup_all"), {})
    fair = by_key.get(("baseline_short_reclaim", "ctx_active_days"), {})
    ctx_costs = [row for row in cost_summary if row["slice"] == "ctx_spike_count_ge2" and row["basis"] == "dedup_all"]
    lines = [
        "# Short Reclaim Pooled Validation",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Campaign-level validation over trade ledgers from the narrow replay experiment.",
        "Trades are deduplicated by `source_setup_id` per slice to remove same-day rerun duplicates.",
        "",
        "## Key Read",
        "",
        f"- `ctx_spike_count_ge2` dedup trades: {ctx.get('trade_count', '')}",
        f"- `ctx_spike_count_ge2` pos_rate: {ctx.get('pos_rate', '')}%",
        f"- `ctx_spike_count_ge2` mean_return: {ctx.get('mean_return', '')}",
        f"- `ctx_spike_count_ge2` median_return: {ctx.get('median_return', '')}",
        f"- `ctx_spike_count_ge2` max_drawdown: {ctx.get('max_drawdown', '')}",
        f"- fair baseline on ctx active days mean_return: {fair.get('mean_return', '')}",
        "",
        "## Cost Sensitivity",
        "",
    ]
    for row in ctx_costs:
        lines.append(
            f"- cost `{row['cost_per_trade']}`: mean={row['mean_return_after_cost']}, "
            f"median={row['median_return_after_cost']}, pos_rate={row['pos_rate_after_cost']}%"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This validates whether the candidate survives pooled comparison and simple cost stress.",
            "It is still research-only: no exchange costs, slippage, execution constraints, or production controls are implemented here.",
            "",
            f"Summary CSV: `{output_csv.as_posix()}`",
            f"Cost CSV: `{cost_csv.as_posix()}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-csv", default="research/results/short_reclaim_context_replay_experiment_runs_2026-05-03.csv")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_pooled_validation_{date.today().isoformat()}.csv")
    parser.add_argument("--cost-csv", default=f"research/results/short_reclaim_pooled_validation_costs_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_pooled_validation_{date.today().isoformat()}.md")
    args = parser.parse_args()

    trades = dedupe_trades(load_trades(Path(args.run_csv)))
    by_slice: dict[str, list[dict[str, str]]] = defaultdict(list)
    for trade in trades:
        by_slice[trade["slice"]].append(trade)

    ctx_days = {trade["_day"] for trade in by_slice.get("ctx_spike_count_ge2", [])}
    summary_rows: list[dict[str, str]] = []
    cost_summary: list[dict[str, str]] = []
    costs = [0.0, 0.000025, 0.00005, 0.0001, 0.0002, 0.0005]

    for slice_name, slice_trades in sorted(by_slice.items()):
        summary_rows.append(metric_row(slice_name, "dedup_all", slice_trades, "deduplicated all available trades"))
        cost_summary.extend(cost_rows(slice_name, "dedup_all", slice_trades, costs))
        if slice_name == "baseline_short_reclaim":
            fair = [trade for trade in slice_trades if trade["_day"] in ctx_days]
            summary_rows.append(metric_row(slice_name, "ctx_active_days", fair, "baseline restricted to days where ctx_spike_count_ge2 has trades"))
            cost_summary.extend(cost_rows(slice_name, "ctx_active_days", fair, costs))

    write_csv(Path(args.summary_csv), summary_rows, SUMMARY_COLUMNS)
    write_csv(Path(args.cost_csv), cost_summary, COST_COLUMNS)
    write_note(Path(args.note), summary_rows, cost_summary, Path(args.summary_csv), Path(args.cost_csv))

    print(json.dumps({
        "trades_loaded_deduped": len(trades),
        "slice_counts": {key: len(value) for key, value in sorted(by_slice.items())},
        "summary_csv": args.summary_csv,
        "cost_csv": args.cost_csv,
        "note": args.note,
        "reject_duplicate_setup_ids_removed": len(load_trades(Path(args.run_csv))) - len(trades),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
