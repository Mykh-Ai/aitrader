"""Diagnostic for pre-registered SHORT reclaim context filters.

This script checks a small fixed set of filters suggested by prior evidence.
It is intentionally not an optimizer and does not search arbitrary parameter
combinations.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median


SUMMARY_COLUMNS = [
    "slice",
    "n",
    "days",
    "pos_rate",
    "mean_ret",
    "median_ret",
    "mean_mfe",
    "mean_mae",
    "positive_day_rate",
    "largest_day_share",
    "notes",
]

DAILY_COLUMNS = [
    "slice",
    "day",
    "n",
    "pos_rate",
    "mean_ret",
    "median_ret",
    "mean_mfe",
    "mean_mae",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def float_value(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def bool_value(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def setup_day(row: dict[str, str]) -> str:
    ts = row.get("SetupBarTs") or row.get("DetectedAt") or ""
    return ts[:10] if len(ts) >= 10 else "UNKNOWN"


def load_joined_setups(runs_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        setups = read_csv(run_dir / "analyzer_setups.csv")
        outcomes = {
            row.get("SetupId", ""): row
            for row in read_csv(run_dir / "analyzer_setup_outcomes.csv")
            if row.get("SetupId")
        }
        for setup in setups:
            setup_id = setup.get("SetupId", "")
            if not setup_id or setup_id in seen:
                continue
            if setup.get("Direction") != "SHORT":
                continue
            if "RECLAIM" not in setup.get("SetupType", ""):
                continue
            outcome = outcomes.get(setup_id)
            if not outcome:
                continue
            close_ret = float_value(outcome.get("CloseReturn_Pct"))
            mfe = float_value(outcome.get("MFE_Pct"))
            mae = float_value(outcome.get("MAE_Pct"))
            if close_ret is None or mfe is None or mae is None:
                continue
            joined = dict(setup)
            joined.update({
                "CloseReturn_Pct": str(close_ret),
                "MFE_Pct": str(mfe),
                "MAE_Pct": str(mae),
                "_day": setup_day(setup),
                "_run_id": run_dir.name,
            })
            rows.append(joined)
            seen.add(setup_id)
    return rows


def numeric_values(rows: list[dict[str, str]], column: str) -> list[float]:
    return [value for value in (float_value(row.get(column)) for row in rows) if value is not None]


def ctx_spike_count(row: dict[str, str]) -> int:
    fields = [
        "CtxRelVolumeSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxOISpike_v1",
        "CtxLiqSpike_v1",
        "CtxWickReclaim_v1",
    ]
    return sum(1 for field in fields if bool_value(row.get(field)))


def metric_row(slice_name: str, rows: list[dict[str, str]], notes: str) -> dict[str, str]:
    returns = numeric_values(rows, "CloseReturn_Pct")
    mfes = numeric_values(rows, "MFE_Pct")
    maes = numeric_values(rows, "MAE_Pct")
    day_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        day_groups[row["_day"]].append(row)

    positive_days = 0
    for day_rows in day_groups.values():
        day_returns = numeric_values(day_rows, "CloseReturn_Pct")
        if day_returns and mean(day_returns) > 0:
            positive_days += 1

    n = len(rows)
    largest_day = max((len(day_rows) for day_rows in day_groups.values()), default=0)
    return {
        "slice": slice_name,
        "n": str(n),
        "days": str(len(day_groups)),
        "pos_rate": f"{100.0 * sum(1 for value in returns if value > 0) / len(returns):.2f}" if returns else "",
        "mean_ret": f"{mean(returns):.6f}" if returns else "",
        "median_ret": f"{median(returns):.6f}" if returns else "",
        "mean_mfe": f"{mean(mfes):.6f}" if mfes else "",
        "mean_mae": f"{mean(maes):.6f}" if maes else "",
        "positive_day_rate": f"{100.0 * positive_days / len(day_groups):.2f}" if day_groups else "",
        "largest_day_share": f"{100.0 * largest_day / n:.2f}" if n else "",
        "notes": notes,
    }


def daily_rows(slice_name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["_day"]].append(row)
    return [metric_row(slice_name, day_rows, "") | {"day": day} for day, day_rows in sorted(grouped.items())]


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def write_note(path: Path, summary_rows: list[dict[str, str]], daily_csv: Path) -> None:
    by_name = {row["slice"]: row for row in summary_rows}
    baseline = by_name.get("baseline_short_reclaim", {})
    lines = [
        "# Short Reclaim Context Filter Diagnostic",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Diagnostic only. No ruleset changes, no parameter search, no optimizer.",
        "Population: deduplicated SHORT setups whose `SetupType` contains `RECLAIM` and which have setup outcomes.",
        "",
        "## Baseline",
        "",
        f"- n: {baseline.get('n', '')}",
        f"- days: {baseline.get('days', '')}",
        f"- pos_rate: {baseline.get('pos_rate', '')}%",
        f"- mean_ret: {baseline.get('mean_ret', '')}",
        f"- median_ret: {baseline.get('median_ret', '')}",
        "",
        "## Pre-Registered Slice Results",
        "",
    ]
    for row in summary_rows:
        if row["slice"] == "baseline_short_reclaim":
            continue
        lines.append(
            f"- `{row['slice']}`: n={row['n']}, days={row['days']}, "
            f"pos_rate={row['pos_rate']}%, mean_ret={row['mean_ret']}, "
            f"median_ret={row['median_ret']}, positive_day_rate={row['positive_day_rate']}%, "
            f"largest_day_share={row['largest_day_share']}%"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Use this as evidence for whether a targeted filter experiment is worth designing.",
            "A slice is not actionable unless it has enough `n`, survives day-level concentration checks,",
            "and improves on baseline without relying on a single outlier day.",
            "",
            f"Daily detail CSV: `{daily_csv.as_posix()}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="analyzer_runs")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_context_filter_diagnostic_{date.today().isoformat()}.csv")
    parser.add_argument("--daily-csv", default=f"research/results/short_reclaim_context_filter_diagnostic_daily_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_context_filter_diagnostic_{date.today().isoformat()}.md")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    rows = load_joined_setups(runs_dir)
    if not rows:
        raise SystemExit(f"no joined SHORT reclaim rows found in {runs_dir}")

    abs_values = numeric_values(rows, "AbsorptionScore_v1")
    rel_values = numeric_values(rows, "RelVolume_20")
    delta_values = numeric_values(rows, "DeltaAbsRatio_20")
    abs_median = median(abs_values)
    rel_median = median(rel_values)
    delta_median = median(delta_values)

    slices: list[tuple[str, list[dict[str, str]], str]] = [
        ("baseline_short_reclaim", rows, "all SHORT reclaim setups"),
        (
            "high_stress_all3_ge_median",
            [
                row for row in rows
                if (float_value(row.get("AbsorptionScore_v1")) or 0.0) >= abs_median
                and (float_value(row.get("RelVolume_20")) or 0.0) >= rel_median
                and (float_value(row.get("DeltaAbsRatio_20")) or 0.0) >= delta_median
            ],
            f"AbsorptionScore_v1>={abs_median:.6f}; RelVolume_20>={rel_median:.6f}; DeltaAbsRatio_20>={delta_median:.6f}",
        ),
        (
            "ctx_spike_count_ge2",
            [row for row in rows if ctx_spike_count(row) >= 2],
            ">=2 boolean context spike flags active",
        ),
        (
            "absorption_high_ge3",
            [row for row in rows if (float_value(row.get("AbsorptionScore_v1")) or 0.0) >= 3.0],
            "AbsorptionScore_v1 >= 3",
        ),
        (
            "absorption_low_le1",
            [row for row in rows if (float_value(row.get("AbsorptionScore_v1")) or 0.0) <= 1.0],
            "AbsorptionScore_v1 <= 1",
        ),
        (
            "liq_spike_true",
            [row for row in rows if bool_value(row.get("CtxLiqSpike_v1"))],
            "CtxLiqSpike_v1 == True",
        ),
    ]

    summary = [metric_row(name, slice_rows, notes) for name, slice_rows, notes in slices]
    daily = [row for name, slice_rows, _ in slices for row in daily_rows(name, slice_rows)]

    write_csv(Path(args.summary_csv), summary, SUMMARY_COLUMNS)
    write_csv(Path(args.daily_csv), daily, DAILY_COLUMNS)
    write_note(Path(args.note), summary, Path(args.daily_csv))

    print(json.dumps({
        "rows": len(rows),
        "summary_csv": args.summary_csv,
        "daily_csv": args.daily_csv,
        "note": args.note,
        "slices": {row["slice"]: row["n"] for row in summary},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
