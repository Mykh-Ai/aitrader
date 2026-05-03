"""Run a narrow SHORT reclaim context replay experiment.

This script materializes temporary filtered Analyzer artifact directories and
uses the existing backtester PHASE3_MAPPING_ONLY path. It does not modify
Analyzer artifacts, core ruleset logic, replay semantics, or production code.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import mean, median

import pandas as pd

from backtester.orchestrator import run_backtester


EXPERIMENT_SETUP_TYPE = "EXPERIMENT_SHORT_RECLAIM"
REPLAY_SEMANTICS_VERSION = "REPLAY_V0_1"
SAME_BAR_POLICY_ID = "SAME_BAR_CONSERVATIVE_V0_1"
COST_MODEL_ID = "COST_MODEL_ZERO_SKELETON_ONLY"

COPY_FILES = [
    "analyzer_features.csv",
    "analyzer_events.csv",
    "analyzer_setup_shortlist.csv",
    "analyzer_setup_shortlist_explanations.csv",
    "analyzer_research_summary.csv",
    "analyzer_setup_outcomes.csv",
    "run_manifest.json",
]

SUMMARY_COLUMNS = [
    "slice",
    "status",
    "runs_attempted",
    "runs_completed",
    "runs_skipped_no_setups",
    "runs_failed",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "win_rate",
    "mean_return",
    "median_return",
    "positive_run_rate",
    "largest_run_trade_share",
    "promotion_decisions",
    "validation_statuses",
    "robustness_statuses",
    "notes",
]

RUN_COLUMNS = [
    "slice",
    "run_id",
    "status",
    "selected_setups",
    "output_dir",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "win_rate",
    "mean_return",
    "median_return",
    "promotion_decision",
    "validation_status",
    "robustness_status",
    "notes",
]


@dataclass(frozen=True)
class SliceSpec:
    name: str
    notes: str


SLICES = [
    SliceSpec("baseline_short_reclaim", "SHORT setups whose SetupType contains RECLAIM"),
    SliceSpec("ctx_spike_count_ge2", "baseline + >=2 boolean context spike flags active"),
    SliceSpec("high_stress_all3_ge_median", "baseline + AbsorptionScore/RelVolume/DeltaAbsRatio >= global medians"),
    SliceSpec("absorption_low_le1", "baseline + AbsorptionScore_v1 <= 1 avoid/downweight check"),
]


def bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def float_value(value: object) -> float | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def int_value(value: object) -> int:
    maybe = float_value(value)
    return int(maybe) if maybe is not None else 0


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def ctx_spike_count(row: pd.Series) -> int:
    fields = [
        "CtxRelVolumeSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxOISpike_v1",
        "CtxLiqSpike_v1",
        "CtxWickReclaim_v1",
    ]
    return sum(1 for field in fields if bool_value(row.get(field)))


def eligible_base(setups: pd.DataFrame) -> pd.Series:
    return (
        (setups["Direction"].astype(str) == "SHORT")
        & setups["SetupType"].astype(str).str.contains("RECLAIM", na=False)
    )


def collect_global_medians(runs_dir: Path) -> dict[str, float]:
    frames: list[pd.DataFrame] = []
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        setups = read_csv(run_dir / "analyzer_setups.csv")
        if setups.empty or not {"Direction", "SetupType"}.issubset(setups.columns):
            continue
        frames.append(setups.loc[eligible_base(setups)].copy())
    if not frames:
        raise SystemExit(f"no SHORT reclaim setup rows found in {runs_dir}")
    all_rows = pd.concat(frames, ignore_index=True)
    return {
        "AbsorptionScore_v1": float(all_rows["AbsorptionScore_v1"].astype(float).median()),
        "RelVolume_20": float(all_rows["RelVolume_20"].astype(float).median()),
        "DeltaAbsRatio_20": float(all_rows["DeltaAbsRatio_20"].astype(float).median()),
    }


def select_setups(setups: pd.DataFrame, slice_name: str, medians: dict[str, float]) -> pd.DataFrame:
    selected = setups.loc[eligible_base(setups)].copy()
    if selected.empty:
        return selected

    if slice_name == "baseline_short_reclaim":
        return selected
    if slice_name == "ctx_spike_count_ge2":
        mask = selected.apply(ctx_spike_count, axis=1) >= 2
        return selected.loc[mask].copy()
    if slice_name == "high_stress_all3_ge_median":
        mask = (
            selected["AbsorptionScore_v1"].astype(float).ge(medians["AbsorptionScore_v1"])
            & selected["RelVolume_20"].astype(float).ge(medians["RelVolume_20"])
            & selected["DeltaAbsRatio_20"].astype(float).ge(medians["DeltaAbsRatio_20"])
        )
        return selected.loc[mask].copy()
    if slice_name == "absorption_low_le1":
        return selected.loc[selected["AbsorptionScore_v1"].astype(float).le(1.0)].copy()
    raise ValueError(f"unknown slice: {slice_name}")


def materialize_filtered_artifacts(
    *,
    source_dir: Path,
    filtered_dir: Path,
    selected_setups: pd.DataFrame,
    slice_name: str,
) -> None:
    filtered_dir.mkdir(parents=True, exist_ok=True)
    for filename in COPY_FILES:
        src = source_dir / filename
        if src.exists():
            shutil.copy2(src, filtered_dir / filename)

    setups_out = selected_setups.copy()
    setups_out["SetupTypeOriginal"] = setups_out["SetupType"].astype(str)
    setups_out["SetupType"] = EXPERIMENT_SETUP_TYPE
    setups_out["Direction"] = "SHORT"
    setups_out.to_csv(filtered_dir / "analyzer_setups.csv", index=False)

    mapping = pd.DataFrame(
        [
            {
                "SourceReport": "experiment",
                "GroupType": "ContextFilter",
                "GroupValue": slice_name,
                "RulesetId": f"RULESET_EXPERIMENT_SHORT_RECLAIM_{slice_name.upper()}_BASE",
                "RulesetContractVersion": "V1",
                "MappingStatus": "READY",
                "ReplaySemanticsVersion": REPLAY_SEMANTICS_VERSION,
                "SetupFamily": EXPERIMENT_SETUP_TYPE,
                "Direction": "SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP|IMPULSE_UP",
                "ReplayIntegrationStatus": "READY_FOR_BINDING",
                "EntryTriggerMapping": "FILTERED_ANALYZER_SETUPS",
                "EntryBoundaryMapping": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "ExitBoundaryMapping": "BARS_AFTER_ACTIVATION:12",
                "RiskMapping": "REFERENCE_LEVEL_HARD_STOP|FIXED_R_MULTIPLE:1.5",
            }
        ]
    )
    mapping.to_csv(filtered_dir / "phase3_ruleset_mapping.csv", index=False)


def first_row(path: Path, scope: str) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("scope") == scope:
                return row
    return {}


def trade_returns(path: Path) -> list[float]:
    if not path.exists():
        return []
    values: list[float] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            value = float_value(row.get("trade_return_pct"))
            if value is not None:
                values.append(value)
    return values


def summarize_run(slice_name: str, run_id: str, selected_count: int, output_dir: Path) -> dict[str, str]:
    metrics = first_row(output_dir / "backtest_trade_metrics.csv", "ALL_TRADES")
    validation = first_row(output_dir / "backtest_validation_summary.csv", "ALL_TRADES")
    robustness = first_row(output_dir / "backtest_robustness_summary.csv", "ALL_TRADES")
    promotion = first_row(output_dir / "backtest_promotion_decisions.csv", "ALL_TRADES")
    returns = trade_returns(output_dir / "backtest_trades.csv")
    return {
        "slice": slice_name,
        "run_id": run_id,
        "status": "COMPLETED",
        "selected_setups": str(selected_count),
        "output_dir": str(output_dir),
        "trade_count": metrics.get("trade_count", ""),
        "resolved_trade_count": metrics.get("resolved_trade_count", ""),
        "unresolved_trade_count": metrics.get("unresolved_trade_count", ""),
        "win_rate": metrics.get("win_rate", ""),
        "mean_return": f"{mean(returns):.6f}" if returns else "",
        "median_return": f"{median(returns):.6f}" if returns else "",
        "promotion_decision": promotion.get("promotion_decision", ""),
        "validation_status": validation.get("validation_status", ""),
        "robustness_status": robustness.get("robustness_status", ""),
        "notes": "",
    }


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def aggregate_summary(run_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in run_rows:
        grouped[row["slice"]].append(row)

    for spec in SLICES:
        rows = grouped.get(spec.name, [])
        completed = [row for row in rows if row["status"] == "COMPLETED"]
        returns = [value for row in completed for value in [float_value(row.get("mean_return"))] if value is not None]
        trade_count = sum(int_value(row.get("trade_count")) for row in completed)
        largest_run = max((int_value(row.get("trade_count")) for row in completed), default=0)
        positive_runs = sum(1 for value in returns if value > 0)
        out.append(
            {
                "slice": spec.name,
                "status": "COMPLETED" if completed else "NO_COMPLETED_RUNS",
                "runs_attempted": str(len(rows)),
                "runs_completed": str(len(completed)),
                "runs_skipped_no_setups": str(sum(1 for row in rows if row["status"] == "SKIPPED_NO_SETUPS")),
                "runs_failed": str(sum(1 for row in rows if row["status"] == "FAILED")),
                "trade_count": str(trade_count),
                "resolved_trade_count": str(sum(int_value(row.get("resolved_trade_count")) for row in completed)),
                "unresolved_trade_count": str(sum(int_value(row.get("unresolved_trade_count")) for row in completed)),
                "win_rate": "",
                "mean_return": f"{mean(returns):.6f}" if returns else "",
                "median_return": f"{median(returns):.6f}" if returns else "",
                "positive_run_rate": f"{100.0 * positive_runs / len(returns):.2f}" if returns else "",
                "largest_run_trade_share": f"{100.0 * largest_run / trade_count:.2f}" if trade_count else "",
                "promotion_decisions": ";".join(f"{k}:{v}" for k, v in sorted(Counter(row.get("promotion_decision", "") or "NA" for row in completed).items())),
                "validation_statuses": ";".join(f"{k}:{v}" for k, v in sorted(Counter(row.get("validation_status", "") or "NA" for row in completed).items())),
                "robustness_statuses": ";".join(f"{k}:{v}" for k, v in sorted(Counter(row.get("robustness_status", "") or "NA" for row in completed).items())),
                "notes": spec.notes,
            }
        )
    return out


def write_note(path: Path, summary_rows: list[dict[str, str]], run_csv: Path) -> None:
    lines = [
        "# Short Reclaim Context Replay Experiment",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Narrow replay experiment over temporary filtered analyzer artifacts.",
        "No core Analyzer/Backtester code or production behavior was changed.",
        "",
        "## Results",
        "",
    ]
    for row in summary_rows:
        lines.append(
            f"- `{row['slice']}`: completed={row['runs_completed']}, skipped={row['runs_skipped_no_setups']}, "
            f"failed={row['runs_failed']}, trades={row['trade_count']}, resolved={row['resolved_trade_count']}, "
            f"mean_run_return={row['mean_return']}, positive_run_rate={row['positive_run_rate']}%, "
            f"promotion={row['promotion_decisions']}, validation={row['validation_statuses']}, "
            f"robustness={row['robustness_statuses']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- This is a research replay experiment, not a live-trading signal.",
            "- Filtered artifact directories normalize selected setup types to one experiment setup family.",
            "- Compare against baseline before considering any persistent ruleset changes.",
            f"- Per-run details: `{run_csv.as_posix()}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="analyzer_runs")
    parser.add_argument("--work-dir", default=f"/tmp/short_reclaim_context_replay_experiment_{date.today().isoformat()}")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_context_replay_experiment_{date.today().isoformat()}.csv")
    parser.add_argument("--run-csv", default=f"research/results/short_reclaim_context_replay_experiment_runs_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_context_replay_experiment_{date.today().isoformat()}.md")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    work_dir = Path(args.work_dir)
    artifacts_root = work_dir / "artifacts"
    backtests_root = work_dir / "backtests"
    medians = collect_global_medians(runs_dir)

    run_rows: list[dict[str, str]] = []
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir() and (path / "analyzer_setups.csv").exists())
    for source_dir in run_dirs:
        setups = read_csv(source_dir / "analyzer_setups.csv")
        if setups.empty or not {"Direction", "SetupType"}.issubset(setups.columns):
            continue
        for spec in SLICES:
            selected = select_setups(setups, spec.name, medians)
            if selected.empty:
                run_rows.append(
                    {
                        "slice": spec.name,
                        "run_id": source_dir.name,
                        "status": "SKIPPED_NO_SETUPS",
                        "selected_setups": "0",
                        "notes": "no selected setups for slice",
                    }
                )
                continue

            filtered_dir = artifacts_root / spec.name / source_dir.name
            output_dir = backtests_root / spec.name / source_dir.name
            try:
                materialize_filtered_artifacts(
                    source_dir=source_dir,
                    filtered_dir=filtered_dir,
                    selected_setups=selected,
                    slice_name=spec.name,
                )
                run_backtester(
                    artifact_dir=filtered_dir,
                    output_dir=output_dir,
                    ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
                    variant_names=("BASE",),
                    cost_model_id=COST_MODEL_ID,
                    same_bar_policy_id=SAME_BAR_POLICY_ID,
                    replay_semantics_version=REPLAY_SEMANTICS_VERSION,
                )
                run_rows.append(summarize_run(spec.name, source_dir.name, len(selected), output_dir))
            except Exception as exc:  # preserve experiment progress across failed slices
                run_rows.append(
                    {
                        "slice": spec.name,
                        "run_id": source_dir.name,
                        "status": "FAILED",
                        "selected_setups": str(len(selected)),
                        "output_dir": str(output_dir),
                        "notes": f"{type(exc).__name__}: {exc}",
                    }
                )

    summary_rows = aggregate_summary(run_rows)
    write_csv(Path(args.summary_csv), summary_rows, SUMMARY_COLUMNS)
    write_csv(Path(args.run_csv), run_rows, RUN_COLUMNS)
    write_note(Path(args.note), summary_rows, Path(args.run_csv))

    print(json.dumps({
        "runs_considered": len(run_dirs),
        "summary_csv": args.summary_csv,
        "run_csv": args.run_csv,
        "note": args.note,
        "work_dir": str(work_dir),
        "summary": summary_rows,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
