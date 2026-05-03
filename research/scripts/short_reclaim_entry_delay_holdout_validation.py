"""Pseudo-holdout and concentration validation for SHORT reclaim entry_delay_1."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "scope",
    "variant",
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
    "mean_after_cost_00005",
    "mean_after_cost_00010",
    "mean_after_cost_00015",
    "sum_after_cost_00005",
    "sum_after_cost_00010",
    "sum_after_cost_00015",
    "notes",
]

PAIR_COLUMNS = [
    "scope",
    "pair_count",
    "delay_better_count",
    "baseline_better_count",
    "tie_count",
    "delay_better_share",
    "mean_delta",
    "median_delta",
    "sum_delta",
    "baseline_mean",
    "delay_mean",
    "baseline_pos_rate",
    "delay_pos_rate",
]

LODO_COLUMNS = [
    "variant",
    "omitted_day",
    "remaining_trade_count",
    "remaining_days",
    "pos_rate",
    "mean_return",
    "median_return",
    "sum_return",
]


def read_dict_csv(path: Path) -> list[dict[str, str]]:
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


def fmt(value: float | None) -> str:
    return f"{value:.8f}" if value is not None else ""


def day(row: dict[str, str]) -> str:
    ts = row.get("entry_signal_ts") or row.get("entry_activation_ts") or ""
    return ts[:10] if len(ts) >= 10 else "UNKNOWN"


def load_trades(path: Path, variants: set[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in read_dict_csv(path):
        variant = row.get("variant", "")
        if variant not in variants:
            continue
        ret = float_value(row.get("trade_return_pct"))
        setup_id = row.get("source_setup_id", "")
        if ret is None or not setup_id:
            continue
        key = (variant, setup_id)
        if key in seen:
            continue
        seen.add(key)
        enriched: dict[str, object] = dict(row)
        enriched["_return"] = ret
        enriched["_day"] = day(row)
        rows.append(enriched)
    return rows


def max_drawdown(returns: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for ret in returns:
        equity += ret
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return max_dd


def split_scopes(trades: list[dict[str, object]]) -> dict[str, set[str]]:
    days = sorted({str(row["_day"]) for row in trades if str(row["_day"]) != "UNKNOWN"})
    if not days:
        return {"all": set()}
    half = max(1, len(days) // 2)
    final_third = max(1, len(days) - (len(days) * 2 // 3))
    return {
        "all": set(days),
        "early_half": set(days[:half]),
        "late_half_pseudo_holdout": set(days[half:]),
        "final_third_pseudo_holdout": set(days[-final_third:]),
    }


def metric_row(scope: str, variant: str, rows: list[dict[str, object]], notes: str) -> dict[str, str]:
    ordered = sorted(rows, key=lambda row: str(row.get("entry_signal_ts", "")))
    returns = [float(row["_return"]) for row in ordered]
    positives = [ret for ret in returns if ret > 0]
    day_returns: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        day_returns[str(row["_day"])].append(float(row["_return"]))
    day_sums = {key: sum(values) for key, values in day_returns.items()}
    positive_day_count = sum(1 for value in day_sums.values() if value > 0)
    largest_day_trade = max((len(values) for values in day_returns.values()), default=0)
    positive_sum = sum(value for value in day_sums.values() if value > 0)
    largest_day_return = max((value for value in day_sums.values() if value > 0), default=0.0)
    best_day, best_value = max(day_sums.items(), key=lambda item: item[1], default=("", 0.0))
    worst_day, worst_value = min(day_sums.items(), key=lambda item: item[1], default=("", 0.0))
    return {
        "scope": scope,
        "variant": variant,
        "trade_count": str(len(returns)),
        "days": str(len(day_returns)),
        "pos_rate": f"{100.0 * len(positives) / len(returns):.2f}" if returns else "",
        "mean_return": fmt(mean(returns) if returns else None),
        "median_return": fmt(median(returns) if returns else None),
        "sum_return": fmt(sum(returns) if returns else None),
        "max_drawdown": fmt(max_drawdown(returns) if returns else None),
        "positive_day_rate": f"{100.0 * positive_day_count / len(day_returns):.2f}" if day_returns else "",
        "largest_day_trade_share": f"{100.0 * largest_day_trade / len(returns):.2f}" if returns else "",
        "largest_day_return_share": f"{100.0 * largest_day_return / positive_sum:.2f}" if positive_sum else "",
        "best_day": best_day,
        "best_day_sum_return": fmt(best_value),
        "worst_day": worst_day,
        "worst_day_sum_return": fmt(worst_value),
        "mean_after_cost_00005": fmt((mean(returns) - 0.00005) if returns else None),
        "mean_after_cost_00010": fmt((mean(returns) - 0.00010) if returns else None),
        "mean_after_cost_00015": fmt((mean(returns) - 0.00015) if returns else None),
        "sum_after_cost_00005": fmt((sum(returns) - 0.00005 * len(returns)) if returns else None),
        "sum_after_cost_00010": fmt((sum(returns) - 0.00010 * len(returns)) if returns else None),
        "sum_after_cost_00015": fmt((sum(returns) - 0.00015 * len(returns)) if returns else None),
        "notes": notes,
    }


def paired_rows(trades: list[dict[str, object]], *, scope_days: set[str]) -> tuple[list[float], list[float], list[float]]:
    by_variant_setup: dict[tuple[str, str], dict[str, object]] = {}
    for row in trades:
        if scope_days and str(row["_day"]) not in scope_days:
            continue
        by_variant_setup[(str(row["variant"]), str(row["source_setup_id"]))] = row
    setup_ids = {
        setup_id
        for variant, setup_id in by_variant_setup
        if variant == "baseline_current" and ("entry_delay_1", setup_id) in by_variant_setup
    }
    baseline = [float(by_variant_setup[("baseline_current", setup_id)]["_return"]) for setup_id in sorted(setup_ids)]
    delay = [float(by_variant_setup[("entry_delay_1", setup_id)]["_return"]) for setup_id in sorted(setup_ids)]
    deltas = [d - b for b, d in zip(baseline, delay, strict=True)]
    return baseline, delay, deltas


def pair_row(scope: str, trades: list[dict[str, object]], scope_days: set[str]) -> dict[str, str]:
    baseline, delay, deltas = paired_rows(trades, scope_days=scope_days)
    better = sum(1 for value in deltas if value > 0)
    worse = sum(1 for value in deltas if value < 0)
    ties = len(deltas) - better - worse
    return {
        "scope": scope,
        "pair_count": str(len(deltas)),
        "delay_better_count": str(better),
        "baseline_better_count": str(worse),
        "tie_count": str(ties),
        "delay_better_share": f"{100.0 * better / len(deltas):.2f}" if deltas else "",
        "mean_delta": fmt(mean(deltas) if deltas else None),
        "median_delta": fmt(median(deltas) if deltas else None),
        "sum_delta": fmt(sum(deltas) if deltas else None),
        "baseline_mean": fmt(mean(baseline) if baseline else None),
        "delay_mean": fmt(mean(delay) if delay else None),
        "baseline_pos_rate": f"{100.0 * sum(1 for value in baseline if value > 0) / len(baseline):.2f}" if baseline else "",
        "delay_pos_rate": f"{100.0 * sum(1 for value in delay if value > 0) / len(delay):.2f}" if delay else "",
    }


def leave_one_day_rows(trades: list[dict[str, object]], variant: str) -> list[dict[str, str]]:
    variant_rows = [row for row in trades if row["variant"] == variant]
    days = sorted({str(row["_day"]) for row in variant_rows})
    out: list[dict[str, str]] = []
    for omitted in days:
        rows = [row for row in variant_rows if row["_day"] != omitted]
        returns = [float(row["_return"]) for row in rows]
        positives = [ret for ret in returns if ret > 0]
        out.append(
            {
                "variant": variant,
                "omitted_day": omitted,
                "remaining_trade_count": str(len(returns)),
                "remaining_days": str(len({str(row["_day"]) for row in rows})),
                "pos_rate": f"{100.0 * len(positives) / len(returns):.2f}" if returns else "",
                "mean_return": fmt(mean(returns) if returns else None),
                "median_return": fmt(median(returns) if returns else None),
                "sum_return": fmt(sum(returns) if returns else None),
            }
        )
    return out


def drop_top_days_row(trades: list[dict[str, object]], variant: str, drop_n: int) -> dict[str, str]:
    rows = [row for row in trades if row["variant"] == variant]
    day_sums: dict[str, float] = defaultdict(float)
    for row in rows:
        day_sums[str(row["_day"])] += float(row["_return"])
    drop_days = {day for day, _ in sorted(day_sums.items(), key=lambda item: item[1], reverse=True)[:drop_n]}
    kept = [row for row in rows if str(row["_day"]) not in drop_days]
    return metric_row(f"drop_top_{drop_n}_days", variant, kept, f"omitted best days: {','.join(sorted(drop_days))}")


def write_note(path: Path, summary_rows: list[dict[str, str]], pair_rows_out: list[dict[str, str]], lodo_rows: list[dict[str, str]], summary_csv: Path, pair_csv: Path, lodo_csv: Path) -> None:
    by_key = {(row["scope"], row["variant"]): row for row in summary_rows}
    all_delay = by_key.get(("all", "entry_delay_1"), {})
    late_delay = by_key.get(("late_half_pseudo_holdout", "entry_delay_1"), {})
    final_delay = by_key.get(("final_third_pseudo_holdout", "entry_delay_1"), {})
    all_pair = next((row for row in pair_rows_out if row["scope"] == "all"), {})
    delay_lodo = [row for row in lodo_rows if row["variant"] == "entry_delay_1"]
    min_lodo_sum = min((float(row["sum_return"]) for row in delay_lodo if row["sum_return"]), default=0.0)
    min_lodo_mean = min((float(row["mean_return"]) for row in delay_lodo if row["mean_return"]), default=0.0)
    lines = [
        "# Short Reclaim Entry Delay Holdout Validation",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Pseudo-holdout / concentration validation for `entry_delay_1` using already generated timing diagnostic trades.",
        "This is not a true unseen holdout; true holdout requires future analyzer runs after this decision.",
        "",
        "## Key Read",
        "",
        f"- all `entry_delay_1`: trades={all_delay.get('trade_count', '')}, mean={all_delay.get('mean_return', '')}, median={all_delay.get('median_return', '')}, sum={all_delay.get('sum_return', '')}",
        f"- late-half `entry_delay_1`: trades={late_delay.get('trade_count', '')}, mean={late_delay.get('mean_return', '')}, median={late_delay.get('median_return', '')}, sum={late_delay.get('sum_return', '')}",
        f"- final-third `entry_delay_1`: trades={final_delay.get('trade_count', '')}, mean={final_delay.get('mean_return', '')}, median={final_delay.get('median_return', '')}, sum={final_delay.get('sum_return', '')}",
        f"- paired all mean delta: {all_pair.get('mean_delta', '')}, delay better share: {all_pair.get('delay_better_share', '')}%",
        f"- entry_delay_1 min leave-one-day-out sum: {min_lodo_sum:.8f}",
        f"- entry_delay_1 min leave-one-day-out mean: {min_lodo_mean:.8f}",
        "",
        "## Interpretation",
        "",
        "Use this as a stability check, not as promotion evidence. Passing this check means `entry_delay_1` deserves true future holdout; failing it means the in-sample improvement is likely concentrated or regime-specific.",
        "",
        f"Summary CSV: `{summary_csv.as_posix()}`",
        f"Pair CSV: `{pair_csv.as_posix()}`",
        f"Leave-one-day-out CSV: `{lodo_csv.as_posix()}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades-csv", default="research/results/short_reclaim_timing_survival_diagnostic_trades_2026-05-03.csv")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_entry_delay_holdout_validation_{date.today().isoformat()}.csv")
    parser.add_argument("--pair-csv", default=f"research/results/short_reclaim_entry_delay_holdout_validation_pairs_{date.today().isoformat()}.csv")
    parser.add_argument("--lodo-csv", default=f"research/results/short_reclaim_entry_delay_holdout_validation_lodo_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_entry_delay_holdout_validation_{date.today().isoformat()}.md")
    args = parser.parse_args()

    variants = {"baseline_current", "entry_delay_1"}
    trades = load_trades(Path(args.trades_csv), variants)
    scopes = split_scopes(trades)
    summary_rows: list[dict[str, str]] = []
    pair_rows_out: list[dict[str, str]] = []

    for scope, days in scopes.items():
        scoped = [row for row in trades if not days or str(row["_day"]) in days]
        for variant in sorted(variants):
            rows = [row for row in scoped if row["variant"] == variant]
            summary_rows.append(metric_row(scope, variant, rows, "pseudo-holdout split by entry_signal day"))
        pair_rows_out.append(pair_row(scope, trades, days))

    summary_rows.append(drop_top_days_row(trades, "entry_delay_1", 1))
    summary_rows.append(drop_top_days_row(trades, "entry_delay_1", 3))
    lodo_rows = leave_one_day_rows(trades, "baseline_current") + leave_one_day_rows(trades, "entry_delay_1")

    write_csv(Path(args.summary_csv), summary_rows, SUMMARY_COLUMNS)
    write_csv(Path(args.pair_csv), pair_rows_out, PAIR_COLUMNS)
    write_csv(Path(args.lodo_csv), lodo_rows, LODO_COLUMNS)
    write_note(Path(args.note), summary_rows, pair_rows_out, lodo_rows, Path(args.summary_csv), Path(args.pair_csv), Path(args.lodo_csv))

    print(json.dumps({
        "trades": len(trades),
        "summary_csv": args.summary_csv,
        "pair_csv": args.pair_csv,
        "lodo_csv": args.lodo_csv,
        "note": args.note,
        "key_rows": [
            row for row in summary_rows
            if row["variant"] == "entry_delay_1" and row["scope"] in {"all", "late_half_pseudo_holdout", "final_third_pseudo_holdout", "drop_top_1_days", "drop_top_3_days"}
        ],
        "pair_rows": pair_rows_out,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
