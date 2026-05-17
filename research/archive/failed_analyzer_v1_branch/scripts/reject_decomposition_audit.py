"""Decompose rejected backtest runs without changing rulesets.

This is a research diagnostic, not an optimizer. It scans existing backtester
artifacts and classifies why replayed rulesets were rejected where the artifacts
make that visible.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import mean, median
from typing import Iterable


ROUTINE_SUFFIX_RE = re.compile(r"_routine_\d{8}$")


OUTPUT_COLUMNS = [
    "analyzer_run_id",
    "backtest_run_dir",
    "derived_run",
    "scope",
    "ruleset_id",
    "source_candidate_group",
    "direction",
    "setup_type",
    "promotion_decision",
    "validation_status",
    "robustness_status",
    "sample_sufficiency_status",
    "expectancy_status",
    "drawdown_status",
    "source_concentration_status",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "long_trade_count",
    "short_trade_count",
    "win_rate",
    "expectancy",
    "trade_return_count",
    "trade_return_mean",
    "trade_return_median",
    "exit_reason_categories",
    "reject_class",
    "reject_reason",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def index_by(rows: Iterable[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if value:
            out[value] = row
    return out


def int_value(value: str | None) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def float_value(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def find_run_dirs(backtest_runs_dir: Path) -> list[Path]:
    return sorted(
        path.parent
        for path in backtest_runs_dir.rglob("backtest_trade_metrics.csv")
        if path.is_file()
    )


def infer_run_ids(run_dir: Path, backtest_runs_dir: Path) -> tuple[str, str, str]:
    derived_run = run_dir.name if run_dir.name.startswith("derived_run_") else ""
    parent_dir = run_dir.parent if derived_run else run_dir
    backtest_run_dir = str(parent_dir.relative_to(backtest_runs_dir))
    analyzer_run_id = ROUTINE_SUFFIX_RE.sub("", parent_dir.name)
    return analyzer_run_id, backtest_run_dir, derived_run


def ruleset_for_scope(
    scope: str,
    ruleset_rows: list[dict[str, str]],
    trades: list[dict[str, str]],
) -> dict[str, str]:
    by_id = index_by(ruleset_rows, "ruleset_id")
    if scope in by_id:
        return by_id[scope]

    scope_trades = [row for row in trades if row.get("ruleset_id") == scope]
    if scope_trades and scope_trades[0].get("ruleset_id") in by_id:
        return by_id[scope_trades[0]["ruleset_id"]]

    if len(ruleset_rows) == 1 and scope not in {"ALL_TRADES", "RESOLVED_ONLY"}:
        return ruleset_rows[0]

    return {}


def trade_stats(scope: str, trades: list[dict[str, str]]) -> dict[str, str]:
    if scope == "ALL_TRADES":
        scoped = trades
    elif scope == "RESOLVED_ONLY":
        scoped = [row for row in trades if row.get("exit_reason_category") != "UNRESOLVED"]
    else:
        scoped = [row for row in trades if row.get("ruleset_id") == scope]

    returns = [
        value
        for value in (float_value(row.get("trade_return_pct")) for row in scoped)
        if value is not None
    ]
    categories = Counter(row.get("exit_reason_category", "") or "UNKNOWN" for row in scoped)

    return {
        "trade_return_count": str(len(returns)),
        "trade_return_mean": format_float(mean(returns) if returns else None),
        "trade_return_median": format_float(median(returns) if returns else None),
        "exit_reason_categories": ";".join(f"{key}:{value}" for key, value in sorted(categories.items())),
    }


def classify(row: dict[str, str]) -> tuple[str, str]:
    trade_count = int_value(row.get("trade_count"))
    resolved = int_value(row.get("resolved_trade_count"))
    unresolved = int_value(row.get("unresolved_trade_count"))
    validation = row.get("validation_status", "")
    robustness = row.get("robustness_status", "")
    sample_status = row.get("sample_sufficiency_status", "")
    expectancy_status = row.get("expectancy_status", "")
    source_concentration = row.get("source_concentration_status", "")
    return_count = int_value(row.get("trade_return_count"))
    return_mean = float_value(row.get("trade_return_mean"))
    scope = row.get("scope", "")

    if scope == "RESOLVED_ONLY" and trade_count == 0:
        return "NO_RESOLVED_TRADES", "RESOLVED_ONLY scope has no closed/resolved trades"
    if trade_count == 0:
        return "DEAD_REJECT", "trade_count=0"
    if resolved == 0 and unresolved > 0:
        return "LIVE_UNRESOLVED_NO_RETURN", "non-zero trades but all unresolved; return metrics unavailable"
    if sample_status == "FAIL":
        return "LOW_SAMPLE", "sample_sufficiency_status=FAIL"
    if return_count > 0 and return_mean is not None and return_mean < 0:
        return "LIVE_BUT_NEGATIVE", "negative mean trade_return_pct"
    if robustness in {"UNSTABLE", "FRAGILE"}:
        return "LIVE_BUT_UNSTABLE", f"robustness_status={robustness}"
    if source_concentration == "FAIL":
        return "VALIDATION_GATE_FAIL", "source_concentration_status=FAIL"
    if validation == "FAIL":
        return "VALIDATION_GATE_FAIL", f"validation_status=FAIL; expectancy_status={expectancy_status or 'NA'}"
    return "NEEDS_MANUAL_REVIEW", "artifact surface insufficient for automatic class"


def audit(backtest_runs_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for run_dir in find_run_dirs(backtest_runs_dir):
        analyzer_run_id, backtest_run_dir, derived_run = infer_run_ids(run_dir, backtest_runs_dir)
        metrics = index_by(read_csv(run_dir / "backtest_trade_metrics.csv"), "scope")
        validation = index_by(read_csv(run_dir / "backtest_validation_summary.csv"), "scope")
        robustness = index_by(read_csv(run_dir / "backtest_robustness_summary.csv"), "scope")
        promotion = index_by(read_csv(run_dir / "backtest_promotion_decisions.csv"), "scope")
        rulesets = read_csv(run_dir / "backtest_rulesets.csv")
        trades = read_csv(run_dir / "backtest_trades.csv")

        scopes = sorted(set(metrics) | set(validation) | set(robustness) | set(promotion))
        for scope in scopes:
            combined: dict[str, str] = {
                "analyzer_run_id": analyzer_run_id,
                "backtest_run_dir": backtest_run_dir,
                "derived_run": derived_run,
                "scope": scope,
            }
            combined.update(metrics.get(scope, {}))
            combined.update(validation.get(scope, {}))
            combined.update(robustness.get(scope, {}))
            combined.update(promotion.get(scope, {}))

            ruleset = ruleset_for_scope(scope, rulesets, trades)
            combined["ruleset_id"] = ruleset.get("ruleset_id", scope if scope.startswith("RULESET_") else "")
            combined["source_candidate_group"] = ruleset.get("source_candidate_group", "")
            combined["direction"] = ruleset.get("direction", "")
            combined["setup_type"] = ruleset.get("setup_type", "")
            combined.update(trade_stats(scope, trades))

            reject_class, reject_reason = classify(combined)
            combined["reject_class"] = reject_class
            combined["reject_reason"] = reject_reason

            rows.append({column: combined.get(column, "") for column in OUTPUT_COLUMNS})
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_note(path: Path, rows: list[dict[str, str]], csv_path: Path) -> None:
    class_counts = Counter(row["reject_class"] for row in rows)
    decision_counts = Counter(row["promotion_decision"] or "NA" for row in rows)
    direction_counts = Counter(row["direction"] or "NA" for row in rows)
    scope_counts = Counter(row["scope"] for row in rows)

    lines = [
        "# Reject Decomposition Audit",
        "",
        f"Generated: {date.today().isoformat()}",
        f"Source CSV: `{csv_path.as_posix()}`",
        "",
        "## Summary",
        "",
        f"- Rows audited: {len(rows)}",
        f"- Backtest runs: {len(set(row['backtest_run_dir'] for row in rows))}",
        f"- Derived runs: {len(set(row['derived_run'] for row in rows if row['derived_run']))}",
        "",
        "## Promotion Decisions",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(decision_counts.items()))
    lines.extend(["", "## Reject Classes", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(class_counts.items()))
    lines.extend(["", "## Directions", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(direction_counts.items()))
    lines.extend(["", "## Scope Mix", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(scope_counts.items()))
    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- This audit classifies existing replay artifacts only.",
            "- It does not tune parameters and does not create a new ruleset.",
            "- `LIVE_UNRESOLVED_NO_RETURN` means trades exist but resolved return evidence is absent.",
            "- A filter experiment should only follow if non-zero surfaces are visible and the failure mode is not simply dead/no-sample.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backtest-runs-dir", default="backtest_runs")
    parser.add_argument("--output-csv", default=f"research/results/reject_decomposition_audit_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/reject_decomposition_audit_{date.today().isoformat()}.md")
    args = parser.parse_args()

    backtest_runs_dir = Path(args.backtest_runs_dir)
    if not backtest_runs_dir.exists():
        raise SystemExit(f"backtest runs dir not found: {backtest_runs_dir}")

    rows = audit(backtest_runs_dir)
    write_csv(Path(args.output_csv), rows)
    write_note(Path(args.note), rows, Path(args.output_csv))

    print(json.dumps({
        "rows": len(rows),
        "backtest_runs": len(set(row["backtest_run_dir"] for row in rows)),
        "derived_runs": len(set(row["derived_run"] for row in rows if row["derived_run"])),
        "reject_classes": dict(sorted(Counter(row["reject_class"] for row in rows).items())),
        "output_csv": args.output_csv,
        "note": args.note,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
