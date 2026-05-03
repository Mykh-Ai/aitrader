"""Timing / stop-survival diagnostic for SHORT reclaim ctx_spike_count_ge2.

This is a diagnostic-only replay experiment over the existing narrow replay
surface. It materializes temporary analyzer artifacts with pre-registered
entry/confirmation transforms and runs the unchanged backtester.
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
    "variant",
    "runs_attempted",
    "runs_completed",
    "runs_skipped_no_setups",
    "runs_failed",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "pos_rate",
    "mean_return",
    "median_return",
    "sum_return",
    "max_drawdown",
    "positive_day_rate",
    "largest_day_trade_share",
    "largest_day_return_share",
    "avg_win",
    "avg_loss",
    "payoff_ratio",
    "exit_reason_categories",
    "validation_statuses",
    "robustness_statuses",
    "promotion_decisions",
    "notes",
]

RUN_COLUMNS = [
    "variant",
    "run_id",
    "status",
    "source_setups",
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

DETAIL_COLUMNS = [
    "variant",
    "run_id",
    "trade_id",
    "source_setup_id",
    "entry_signal_ts",
    "entry_activation_ts",
    "exit_ts",
    "exit_reason_category",
    "holding_bars",
    "trade_return_pct",
]


@dataclass(frozen=True)
class VariantSpec:
    name: str
    delay_bars: int
    confirmation: str
    notes: str


VARIANTS = [
    VariantSpec("baseline_current", 0, "none", "current ctx_spike_count_ge2 replay semantics"),
    VariantSpec("entry_delay_1", 1, "none", "shift SetupBarTs forward 1 raw bar; enter on following open"),
    VariantSpec("entry_delay_2", 2, "none", "shift SetupBarTs forward 2 raw bars; enter on following open"),
    VariantSpec(
        "survival_confirm_1",
        1,
        "first_bar_survives_original_stop",
        "keep only setups where first post-signal bar does not touch original stop, then delay 1 bar",
    ),
    VariantSpec(
        "favorable_close_confirm_1",
        1,
        "first_bar_short_close",
        "keep only setups where first post-signal bar closes below its open, then delay 1 bar",
    ),
]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


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


def first_row(path: Path, scope: str) -> dict[str, str]:
    for row in read_dict_csv(path):
        if row.get("scope") == scope:
            return row
    return {}


def trade_returns(path: Path) -> list[float]:
    values: list[float] = []
    for row in read_dict_csv(path):
        value = float_value(row.get("trade_return_pct"))
        if value is not None:
            values.append(value)
    return values


def load_raw_for_artifact(artifact_dir: Path) -> pd.DataFrame:
    manifest_path = artifact_dir / "run_manifest.json"
    if not manifest_path.exists():
        return pd.DataFrame()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = manifest.get("input_feed_paths") or []
    if not paths:
        return pd.DataFrame()
    raw = pd.read_csv(paths[0])
    raw["Timestamp"] = pd.to_datetime(raw["Timestamp"], utc=True, errors="raise")
    return raw.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)


def timestamp_at_offset(raw: pd.DataFrame, setup_ts: pd.Timestamp, offset: int) -> pd.Timestamp | None:
    idx = raw.index[raw["Timestamp"] == setup_ts]
    if len(idx) != 1:
        return None
    target_idx = int(idx[0]) + offset
    if target_idx < 0 or target_idx >= len(raw.index):
        return None
    return pd.Timestamp(raw.loc[target_idx, "Timestamp"])


def first_post_signal_bar(raw: pd.DataFrame, setup_ts: pd.Timestamp) -> pd.Series | None:
    idx = raw.index[raw["Timestamp"] == setup_ts]
    if len(idx) != 1:
        return None
    target_idx = int(idx[0]) + 1
    if target_idx >= len(raw.index):
        return None
    return raw.loc[target_idx]


def passes_confirmation(setup: pd.Series, raw: pd.DataFrame, spec: VariantSpec) -> bool:
    if spec.confirmation == "none":
        return True
    setup_ts = pd.Timestamp(setup["SetupBarTs"])
    first_bar = first_post_signal_bar(raw, setup_ts)
    if first_bar is None:
        return False

    if spec.confirmation == "first_bar_survives_original_stop":
        stop = float_value(setup.get("ReferenceLevel"))
        if stop is None:
            return False
        direction = str(setup.get("Direction", "")).upper()
        if direction == "SHORT":
            return float(first_bar["High"]) < stop
        if direction == "LONG":
            return float(first_bar["Low"]) > stop
        return False

    if spec.confirmation == "first_bar_short_close":
        return str(setup.get("Direction", "")).upper() == "SHORT" and float(first_bar["Close"]) < float(first_bar["Open"])

    raise ValueError(f"unknown confirmation: {spec.confirmation}")


def transform_setups(setups: pd.DataFrame, raw: pd.DataFrame, spec: VariantSpec) -> pd.DataFrame:
    if setups.empty:
        return setups
    out_rows: list[pd.Series] = []
    base = setups.copy()
    base["SetupBarTs"] = pd.to_datetime(base["SetupBarTs"], utc=True, errors="raise")
    for _, setup in base.iterrows():
        if not passes_confirmation(setup, raw, spec):
            continue
        shifted_ts = timestamp_at_offset(raw, pd.Timestamp(setup["SetupBarTs"]), spec.delay_bars)
        if shifted_ts is None:
            continue
        row = setup.copy()
        row["SetupBarTsOriginal"] = setup["SetupBarTs"]
        row["SetupBarTs"] = shifted_ts
        if "DetectedAt" in row.index:
            row["DetectedAt"] = shifted_ts
        row["TimingVariant"] = spec.name
        row["TimingConfirmation"] = spec.confirmation
        row["TimingDelayBars"] = spec.delay_bars
        out_rows.append(row)
    return pd.DataFrame(out_rows, columns=[*base.columns, "SetupBarTsOriginal", "TimingVariant", "TimingConfirmation", "TimingDelayBars"])


def materialize_variant_artifacts(
    *,
    source_dir: Path,
    filtered_dir: Path,
    selected_setups: pd.DataFrame,
    variant: str,
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
                "GroupType": "TimingVariant",
                "GroupValue": variant,
                "RulesetId": f"RULESET_EXPERIMENT_SHORT_RECLAIM_TIMING_{variant.upper()}_BASE",
                "RulesetContractVersion": "V1",
                "MappingStatus": "READY",
                "ReplaySemanticsVersion": REPLAY_SEMANTICS_VERSION,
                "SetupFamily": EXPERIMENT_SETUP_TYPE,
                "Direction": "SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP|IMPULSE_UP",
                "ReplayIntegrationStatus": "READY_FOR_BINDING",
                "EntryTriggerMapping": "FILTERED_ANALYZER_SETUPS_WITH_TIMING_TRANSFORM",
                "EntryBoundaryMapping": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "ExitBoundaryMapping": "BARS_AFTER_ACTIVATION:12",
                "RiskMapping": "REFERENCE_LEVEL_HARD_STOP|FIXED_R_MULTIPLE:1.5",
            }
        ]
    )
    mapping.to_csv(filtered_dir / "phase3_ruleset_mapping.csv", index=False)


def summarize_run(variant: str, run_id: str, source_count: int, selected_count: int, output_dir: Path) -> dict[str, str]:
    metrics = first_row(output_dir / "backtest_trade_metrics.csv", "ALL_TRADES")
    validation = first_row(output_dir / "backtest_validation_summary.csv", "ALL_TRADES")
    robustness = first_row(output_dir / "backtest_robustness_summary.csv", "ALL_TRADES")
    promotion = first_row(output_dir / "backtest_promotion_decisions.csv", "ALL_TRADES")
    returns = trade_returns(output_dir / "backtest_trades.csv")
    return {
        "variant": variant,
        "run_id": run_id,
        "status": "COMPLETED",
        "source_setups": str(source_count),
        "selected_setups": str(selected_count),
        "output_dir": str(output_dir),
        "trade_count": metrics.get("trade_count", ""),
        "resolved_trade_count": metrics.get("resolved_trade_count", ""),
        "unresolved_trade_count": metrics.get("unresolved_trade_count", ""),
        "win_rate": metrics.get("win_rate", ""),
        "mean_return": f"{mean(returns):.8f}" if returns else "",
        "median_return": f"{median(returns):.8f}" if returns else "",
        "promotion_decision": promotion.get("promotion_decision", ""),
        "validation_status": validation.get("validation_status", ""),
        "robustness_status": robustness.get("robustness_status", ""),
        "notes": "",
    }


def load_trades(run_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    trades: list[dict[str, str]] = []
    for run in run_rows:
        if run.get("status") != "COMPLETED":
            continue
        output_dir = Path(run.get("output_dir", ""))
        for trade in read_dict_csv(output_dir / "backtest_trades.csv"):
            ret = float_value(trade.get("trade_return_pct"))
            if ret is None:
                continue
            enriched = dict(trade)
            enriched["variant"] = run.get("variant", "")
            enriched["run_id"] = run.get("run_id", "")
            enriched["_return"] = ret
            enriched["_day"] = (trade.get("entry_signal_ts") or "")[:10]
            trades.append(enriched)
    return trades


def dedupe_trades(trades: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for trade in sorted(trades, key=lambda row: (row["variant"], row.get("entry_signal_ts", ""), row.get("source_setup_id", ""))):
        key = (trade["variant"], trade.get("source_setup_id", "") or trade.get("trade_id", ""))
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


def aggregate_summary(run_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    trades = dedupe_trades(load_trades(run_rows))
    by_variant: dict[str, list[dict[str, str]]] = defaultdict(list)
    for trade in trades:
        by_variant[trade["variant"]].append(trade)

    rows_out: list[dict[str, str]] = []
    for spec in VARIANTS:
        variant_runs = [row for row in run_rows if row.get("variant") == spec.name]
        completed = [row for row in variant_runs if row.get("status") == "COMPLETED"]
        variant_trades = sorted(by_variant.get(spec.name, []), key=lambda row: row.get("entry_signal_ts", ""))
        returns = [float(row["_return"]) for row in variant_trades]
        positives = [value for value in returns if value > 0]
        negatives = [value for value in returns if value < 0]
        day_returns: dict[str, list[float]] = defaultdict(list)
        for trade in variant_trades:
            day_returns[trade["_day"]].append(float(trade["_return"]))
        day_sums = {day: sum(values) for day, values in day_returns.items()}
        positive_day_count = sum(1 for value in day_sums.values() if value > 0)
        largest_day_trade = max((len(values) for values in day_returns.values()), default=0)
        positive_sum = sum(value for value in day_sums.values() if value > 0)
        largest_day_return = max((value for value in day_sums.values() if value > 0), default=0.0)
        exits = Counter(str(trade.get("exit_reason_category") or "UNKNOWN") for trade in variant_trades)
        avg_win = mean(positives) if positives else None
        avg_loss = mean(negatives) if negatives else None
        payoff = abs(avg_win / avg_loss) if avg_win is not None and avg_loss not in (None, 0.0) else None
        rows_out.append(
            {
                "variant": spec.name,
                "runs_attempted": str(len(variant_runs)),
                "runs_completed": str(len(completed)),
                "runs_skipped_no_setups": str(sum(1 for row in variant_runs if row.get("status") == "SKIPPED_NO_SETUPS")),
                "runs_failed": str(sum(1 for row in variant_runs if row.get("status") == "FAILED")),
                "trade_count": str(len(returns)),
                "resolved_trade_count": str(len(returns)),
                "unresolved_trade_count": "0",
                "pos_rate": f"{100.0 * len(positives) / len(returns):.2f}" if returns else "",
                "mean_return": f"{mean(returns):.8f}" if returns else "",
                "median_return": f"{median(returns):.8f}" if returns else "",
                "sum_return": f"{sum(returns):.8f}" if returns else "",
                "max_drawdown": f"{max_drawdown(returns):.8f}" if returns else "",
                "positive_day_rate": f"{100.0 * positive_day_count / len(day_returns):.2f}" if day_returns else "",
                "largest_day_trade_share": f"{100.0 * largest_day_trade / len(returns):.2f}" if returns else "",
                "largest_day_return_share": f"{100.0 * largest_day_return / positive_sum:.2f}" if positive_sum else "",
                "avg_win": f"{avg_win:.8f}" if avg_win is not None else "",
                "avg_loss": f"{avg_loss:.8f}" if avg_loss is not None else "",
                "payoff_ratio": f"{payoff:.4f}" if payoff is not None else "",
                "exit_reason_categories": ";".join(f"{key}:{value}" for key, value in sorted(exits.items())),
                "validation_statuses": ";".join(f"{key}:{value}" for key, value in sorted(Counter(row.get("validation_status") or "NA" for row in completed).items())),
                "robustness_statuses": ";".join(f"{key}:{value}" for key, value in sorted(Counter(row.get("robustness_status") or "NA" for row in completed).items())),
                "promotion_decisions": ";".join(f"{key}:{value}" for key, value in sorted(Counter(row.get("promotion_decision") or "NA" for row in completed).items())),
                "notes": spec.notes,
            }
        )
    return rows_out


def detail_rows(run_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for trade in dedupe_trades(load_trades(run_rows)):
        rows.append(
            {
                "variant": trade.get("variant", ""),
                "run_id": trade.get("run_id", ""),
                "trade_id": trade.get("trade_id", ""),
                "source_setup_id": trade.get("source_setup_id", ""),
                "entry_signal_ts": trade.get("entry_signal_ts", ""),
                "entry_activation_ts": trade.get("entry_activation_ts", ""),
                "exit_ts": trade.get("exit_ts", ""),
                "exit_reason_category": trade.get("exit_reason_category", ""),
                "holding_bars": trade.get("holding_bars", ""),
                "trade_return_pct": f"{float(trade['_return']):.8f}",
            }
        )
    return rows


def write_note(path: Path, summary_rows: list[dict[str, str]], summary_csv: Path, run_csv: Path, detail_csv: Path) -> None:
    lines = [
        "# Short Reclaim Timing Survival Diagnostic",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Diagnostic-only replay experiment over the existing `ctx_spike_count_ge2` surface.",
        "Variants are pre-registered entry/confirmation transforms materialized as temporary analyzer artifacts.",
        "Backtester core replay semantics are unchanged.",
        "",
        "## Results",
        "",
    ]
    for row in summary_rows:
        lines.append(
            f"- `{row['variant']}`: trades={row['trade_count']}, pos_rate={row['pos_rate']}%, "
            f"mean={row['mean_return']}, median={row['median_return']}, sum={row['sum_return']}, "
            f"max_dd={row['max_drawdown']}, exits={row['exit_reason_categories']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- This is not optimizer output and not a production signal.",
            "- Any improvement must be compared against `baseline_current` and still survive costs, concentration, and sample checks.",
            "- Delay variants shift `SetupBarTs`; stop remains the original `ReferenceLevel`.",
            "",
            f"Summary CSV: `{summary_csv.as_posix()}`",
            f"Run CSV: `{run_csv.as_posix()}`",
            f"Detail CSV: `{detail_csv.as_posix()}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-work-dir", default="/tmp/short_reclaim_context_replay_experiment_2026-05-03")
    parser.add_argument("--source-slice", default="ctx_spike_count_ge2")
    parser.add_argument("--work-dir", default=f"/tmp/short_reclaim_timing_survival_diagnostic_{date.today().isoformat()}")
    parser.add_argument("--summary-csv", default=f"research/results/short_reclaim_timing_survival_diagnostic_{date.today().isoformat()}.csv")
    parser.add_argument("--run-csv", default=f"research/results/short_reclaim_timing_survival_diagnostic_runs_{date.today().isoformat()}.csv")
    parser.add_argument("--detail-csv", default=f"research/results/short_reclaim_timing_survival_diagnostic_trades_{date.today().isoformat()}.csv")
    parser.add_argument("--note", default=f"research/findings/short_reclaim_timing_survival_diagnostic_{date.today().isoformat()}.md")
    args = parser.parse_args()

    source_artifacts = Path(args.source_work_dir) / "artifacts" / args.source_slice
    work_dir = Path(args.work_dir)
    artifacts_root = work_dir / "artifacts"
    backtests_root = work_dir / "backtests"
    run_rows: list[dict[str, str]] = []

    run_dirs = sorted(path for path in source_artifacts.iterdir() if path.is_dir() and (path / "analyzer_setups.csv").exists())
    for source_dir in run_dirs:
        source_setups = read_csv(source_dir / "analyzer_setups.csv")
        raw = load_raw_for_artifact(source_dir)
        if source_setups.empty or raw.empty:
            continue
        for spec in VARIANTS:
            selected = transform_setups(source_setups, raw, spec)
            if selected.empty:
                run_rows.append(
                    {
                        "variant": spec.name,
                        "run_id": source_dir.name,
                        "status": "SKIPPED_NO_SETUPS",
                        "source_setups": str(len(source_setups)),
                        "selected_setups": "0",
                        "notes": "no selected setups after timing transform",
                    }
                )
                continue
            filtered_dir = artifacts_root / spec.name / source_dir.name
            output_dir = backtests_root / spec.name / source_dir.name
            try:
                materialize_variant_artifacts(
                    source_dir=source_dir,
                    filtered_dir=filtered_dir,
                    selected_setups=selected,
                    variant=spec.name,
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
                run_rows.append(summarize_run(spec.name, source_dir.name, len(source_setups), len(selected), output_dir))
            except Exception as exc:
                run_rows.append(
                    {
                        "variant": spec.name,
                        "run_id": source_dir.name,
                        "status": "FAILED",
                        "source_setups": str(len(source_setups)),
                        "selected_setups": str(len(selected)),
                        "output_dir": str(output_dir),
                        "notes": f"{type(exc).__name__}: {exc}",
                    }
                )

    summary_rows = aggregate_summary(run_rows)
    write_csv(Path(args.summary_csv), summary_rows, SUMMARY_COLUMNS)
    write_csv(Path(args.run_csv), run_rows, RUN_COLUMNS)
    write_csv(Path(args.detail_csv), detail_rows(run_rows), DETAIL_COLUMNS)
    write_note(Path(args.note), summary_rows, Path(args.summary_csv), Path(args.run_csv), Path(args.detail_csv))

    print(json.dumps({
        "runs_considered": len(run_dirs),
        "summary_csv": args.summary_csv,
        "run_csv": args.run_csv,
        "detail_csv": args.detail_csv,
        "note": args.note,
        "work_dir": str(work_dir),
        "summary": summary_rows,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
