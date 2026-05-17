"""IMPULSE_FADE_RECLAIM_SHORT_V1 low-stress sidecar diagnostic.

This is a bounded research variant only. It reads existing Analyzer and
Backtester artifacts, applies an explicit context filter to the baseline short
ruleset trades, and writes namespaced research outputs. It does not modify
Analyzer grammar, Backtester rulesets, or routine processing markers.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


VARIANT_ID = "IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS"
BASELINE_SETUP_TYPE = "IMPULSE_FADE_RECLAIM_SHORT_V1"
DEFAULT_START_DATE = "2026-05-08"
DEFAULT_END_DATE = "2026-05-12"

SPIKE_COLUMNS = [
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
]

DETAIL_COLUMNS = [
    "VariantId",
    "Date",
    "AnalyzerRunId",
    "BacktestRunId",
    "DerivedRunId",
    "RulesetId",
    "SetupId",
    "EntrySignalTs",
    "EntryActivationTs",
    "ExitTs",
    "ExitReason",
    "ExitReasonCategory",
    "TradeReturnPct",
    "TradePnl",
    "Resolved",
    "Win",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "SpikeCount",
    "CandidateFilterPass",
    "FilterFailureReason",
    "H2_Post3Label_v1",
    "H2_Post6Label_v1",
    "H2_Post12Label_v1",
]


@dataclass(frozen=True)
class LowStressConfig:
    max_rel_volume_20: float = 1.5
    max_delta_abs_ratio_20: float = 2.0
    max_oi_change_abs_ratio_20: float = 5.0
    max_spike_count: int = 2


LOW_STRESS_V1_CONFIG = LowStressConfig()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def iter_dates(start: date, end: date) -> list[date]:
    days: list[date] = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def bool_value(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def bool_mask(values: pd.Series) -> pd.Series:
    return values.map(bool_value).astype(bool)


def spike_count(row: pd.Series | dict[str, object]) -> int:
    return sum(1 for column in SPIKE_COLUMNS if bool_value(row.get(column, False)))


def low_stress_failure_reasons(
    row: pd.Series | dict[str, object],
    config: LowStressConfig = LOW_STRESS_V1_CONFIG,
) -> list[str]:
    reasons: list[str] = []
    rel_volume = pd.to_numeric(row.get("RelVolume_20"), errors="coerce")
    delta_abs = pd.to_numeric(row.get("DeltaAbsRatio_20"), errors="coerce")
    oi_abs = pd.to_numeric(row.get("OIChangeAbsRatio_20"), errors="coerce")
    spikes = int(row.get("SpikeCount", spike_count(row)))

    if pd.isna(rel_volume) or float(rel_volume) > config.max_rel_volume_20:
        reasons.append("rel_volume_20_gt_1_5_or_missing")
    if pd.isna(delta_abs) or float(delta_abs) > config.max_delta_abs_ratio_20:
        reasons.append("delta_abs_ratio_20_gt_2_0_or_missing")
    if pd.isna(oi_abs) or float(oi_abs) > config.max_oi_change_abs_ratio_20:
        reasons.append("oi_change_abs_ratio_20_gt_5_0_or_missing")
    if spikes > config.max_spike_count:
        reasons.append("spike_count_gt_2")
    return reasons


def passes_low_stress_filter(
    row: pd.Series | dict[str, object],
    config: LowStressConfig = LOW_STRESS_V1_CONFIG,
) -> bool:
    return not low_stress_failure_reasons(row, config)


def analyzer_run_dir(analyzer_runs_dir: Path, day: date) -> Path:
    run_id = f"{day.isoformat()}_to_{day.isoformat()}_run_001"
    return analyzer_runs_dir / run_id


def latest_backtest_run_dir(backtest_runs_dir: Path, run_id: str) -> Path | None:
    matches = [
        *backtest_runs_dir.glob(f"{run_id}_routine_*"),
        *backtest_runs_dir.glob(f"{run_id}_archive_*"),
    ]
    if not matches:
        return None
    return max(matches, key=_backtest_run_sort_key)


def _backtest_run_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"_(?:routine|archive)_(\d{8})$", path.name)
    date_key = int(match.group(1)) if match else 0
    return date_key, path.name


def find_short_derived_run(backtest_run_dir: Path) -> Path | None:
    candidates: list[Path] = []
    for ruleset_path in sorted(backtest_run_dir.rglob("backtest_rulesets.csv")):
        if ruleset_path.parent == backtest_run_dir:
            continue
        rulesets = pd.read_csv(ruleset_path)
        if len(rulesets.index) != 1:
            continue
        if str(rulesets.loc[0, "setup_type"]) == BASELINE_SETUP_TYPE:
            candidates.append(ruleset_path.parent)
    if not candidates:
        return None
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise ValueError(f"Multiple short derived runs found in {backtest_run_dir}: {names}")
    return candidates[0]


def _load_outcomes(analyzer_dir: Path) -> pd.DataFrame:
    path = analyzer_dir / "analyzer_setup_outcomes.csv"
    if not path.exists():
        return pd.DataFrame(columns=["SetupId", "H2_Post3Label_v1", "H2_Post6Label_v1", "H2_Post12Label_v1"])
    outcomes = pd.read_csv(path)
    columns = ["SetupId", "H2_Post3Label_v1", "H2_Post6Label_v1", "H2_Post12Label_v1"]
    return outcomes.loc[:, [column for column in columns if column in outcomes.columns]].copy()


def _read_short_rows_for_day(
    *,
    day: date,
    analyzer_runs_dir: Path,
    backtest_runs_dir: Path,
) -> pd.DataFrame:
    analyzer_dir = analyzer_run_dir(analyzer_runs_dir, day)
    if not analyzer_dir.exists():
        return pd.DataFrame(columns=DETAIL_COLUMNS)

    analyzer_run_id = analyzer_dir.name
    backtest_dir = latest_backtest_run_dir(backtest_runs_dir, analyzer_run_id)
    if backtest_dir is None:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    derived_dir = find_short_derived_run(backtest_dir)
    if derived_dir is None:
        return pd.DataFrame(columns=DETAIL_COLUMNS)

    trades_path = derived_dir / "backtest_trades.csv"
    rulesets_path = derived_dir / "backtest_rulesets.csv"
    setups_path = analyzer_dir / "analyzer_setups.csv"
    if not trades_path.exists() or not rulesets_path.exists() or not setups_path.exists():
        return pd.DataFrame(columns=DETAIL_COLUMNS)

    ruleset = pd.read_csv(rulesets_path).iloc[0]
    trades = pd.read_csv(trades_path)
    setups = pd.read_csv(setups_path)
    setups = setups.loc[setups["SetupType"] == BASELINE_SETUP_TYPE].copy()
    outcomes = _load_outcomes(analyzer_dir)

    merged = trades.merge(
        setups,
        left_on="source_setup_id",
        right_on="SetupId",
        how="inner",
        suffixes=("", "_setup"),
    )
    if not outcomes.empty:
        merged = merged.merge(outcomes, on="SetupId", how="left")

    rows: list[dict[str, object]] = []
    for row in merged.to_dict("records"):
        row["SpikeCount"] = spike_count(row)
        reasons = low_stress_failure_reasons(row)
        trade_return = pd.to_numeric(row.get("trade_return_pct"), errors="coerce")
        trade_pnl = pd.to_numeric(row.get("trade_pnl"), errors="coerce")
        resolved = pd.notna(row.get("exit_ts")) and str(row.get("exit_reason", "")).strip() != ""
        rows.append(
            {
                "VariantId": VARIANT_ID,
                "Date": day.isoformat(),
                "AnalyzerRunId": analyzer_run_id,
                "BacktestRunId": backtest_dir.name,
                "DerivedRunId": derived_dir.name,
                "RulesetId": ruleset["ruleset_id"],
                "SetupId": row["SetupId"],
                "EntrySignalTs": row.get("entry_signal_ts"),
                "EntryActivationTs": row.get("entry_activation_ts"),
                "ExitTs": row.get("exit_ts"),
                "ExitReason": row.get("exit_reason"),
                "ExitReasonCategory": row.get("exit_reason_category"),
                "TradeReturnPct": trade_return,
                "TradePnl": trade_pnl,
                "Resolved": resolved,
                "Win": bool(pd.notna(trade_pnl) and float(trade_pnl) > 0),
                "RelVolume_20": row.get("RelVolume_20"),
                "DeltaAbsRatio_20": row.get("DeltaAbsRatio_20"),
                "OIChangeAbsRatio_20": row.get("OIChangeAbsRatio_20"),
                "LiqTotalRatio_20": row.get("LiqTotalRatio_20"),
                "CtxRelVolumeSpike_v1": bool_value(row.get("CtxRelVolumeSpike_v1")),
                "CtxDeltaSpike_v1": bool_value(row.get("CtxDeltaSpike_v1")),
                "CtxOISpike_v1": bool_value(row.get("CtxOISpike_v1")),
                "CtxLiqSpike_v1": bool_value(row.get("CtxLiqSpike_v1")),
                "CtxWickReclaim_v1": bool_value(row.get("CtxWickReclaim_v1")),
                "SpikeCount": row["SpikeCount"],
                "CandidateFilterPass": not reasons,
                "FilterFailureReason": ";".join(reasons),
                "H2_Post3Label_v1": row.get("H2_Post3Label_v1"),
                "H2_Post6Label_v1": row.get("H2_Post6Label_v1"),
                "H2_Post12Label_v1": row.get("H2_Post12Label_v1"),
            }
        )

    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def build_variant_table(
    *,
    analyzer_runs_dir: Path,
    backtest_runs_dir: Path,
    start: date,
    end: date,
) -> pd.DataFrame:
    frames = [
        _read_short_rows_for_day(
            day=day,
            analyzer_runs_dir=analyzer_runs_dir,
            backtest_runs_dir=backtest_runs_dir,
        )
        for day in iter_dates(start, end)
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    table = pd.concat(frames, ignore_index=True, sort=False)
    if table.empty:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    return table.loc[:, DETAIL_COLUMNS].copy()


def max_drawdown(values: pd.Series) -> float:
    pnl = pd.to_numeric(values, errors="coerce").fillna(0.0)
    if pnl.empty:
        return 0.0
    equity = pnl.cumsum()
    peak = equity.cummax()
    drawdown = equity - peak
    return float(drawdown.min())


def _summarize_slice(label: str, df: pd.DataFrame) -> dict[str, object]:
    resolved = df.loc[bool_mask(df["Resolved"])] if not df.empty else df
    wins = int(bool_mask(resolved["Win"]).sum()) if not resolved.empty else 0
    trades = int(len(resolved.index))
    return {
        "Slice": label,
        "Trades": trades,
        "Wins": wins,
        "Losses": trades - wins,
        "WinRate": wins / trades if trades else pd.NA,
        "TotalReturnPct": pd.to_numeric(resolved.get("TradeReturnPct"), errors="coerce").sum() if trades else 0.0,
        "TotalPnl": pd.to_numeric(resolved.get("TradePnl"), errors="coerce").sum() if trades else 0.0,
        "MaxDrawdownPnl": max_drawdown(resolved.get("TradePnl", pd.Series(dtype=float))),
        "AvgRelVolume_20": pd.to_numeric(resolved.get("RelVolume_20"), errors="coerce").mean() if trades else pd.NA,
        "AvgDeltaAbsRatio_20": pd.to_numeric(resolved.get("DeltaAbsRatio_20"), errors="coerce").mean() if trades else pd.NA,
        "AvgOIChangeAbsRatio_20": pd.to_numeric(resolved.get("OIChangeAbsRatio_20"), errors="coerce").mean() if trades else pd.NA,
        "RelSpikeRate": bool_mask(resolved["CtxRelVolumeSpike_v1"]).mean() if trades else pd.NA,
        "DeltaSpikeRate": bool_mask(resolved["CtxDeltaSpike_v1"]).mean() if trades else pd.NA,
        "OISpikeRate": bool_mask(resolved["CtxOISpike_v1"]).mean() if trades else pd.NA,
    }


def summarize_variant(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame(
            [
                _summarize_slice("baseline", table),
                _summarize_slice("low_stress_pass", table),
                _summarize_slice("low_stress_drop", table),
            ]
        )
    pass_mask = bool_mask(table["CandidateFilterPass"])
    passed = table.loc[pass_mask].copy()
    dropped = table.loc[~pass_mask].copy()
    return pd.DataFrame(
        [
            _summarize_slice("baseline", table),
            _summarize_slice("low_stress_pass", passed),
            _summarize_slice("low_stress_drop", dropped),
        ]
    )


def _markdown_table(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["_No rows._"]
    view = df.copy()
    for column in view.columns:
        view[column] = view[column].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in view.astype(str).values.tolist()]
    return [header, separator, *rows]


def write_finding(
    *,
    table: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
    detail_path: Path,
    summary_path: Path,
    start: date,
    end: date,
) -> Path:
    by_day = (
        table.groupby(["Date", "CandidateFilterPass"], dropna=False)
        .agg(Trades=("SetupId", "count"), Wins=("Win", "sum"), Pnl=("TradePnl", "sum"))
        .reset_index()
        if not table.empty
        else pd.DataFrame(columns=["Date", "CandidateFilterPass", "Trades", "Wins", "Pnl"])
    )
    lines = [
        f"# {VARIANT_ID}",
        "",
        f"Window: `{start.isoformat()}` to `{end.isoformat()}`.",
        "",
        "Status: bounded research sidecar only. Baseline Analyzer grammar and Backtester rulesets are unchanged.",
        "",
        "## Filter",
        "",
        "- `RelVolume_20 <= 1.5`",
        "- `DeltaAbsRatio_20 <= 2.0`",
        "- `OIChangeAbsRatio_20 <= 5.0`",
        "- spike count <= 2 across rel-volume/delta/OI/liquidation context spikes",
        "",
        "## Outputs",
        "",
        f"- Detail CSV: `{detail_path.as_posix()}`",
        f"- Summary CSV: `{summary_path.as_posix()}`",
        "",
        "## Summary",
        "",
        *_markdown_table(summary),
        "",
        "## Day Split",
        "",
        *_markdown_table(by_day),
        "",
        "## Research Read",
        "",
        "- This is not a promotion decision and not a live strategy.",
        "- Use it as the tracked low-stress candidate on the next valid post-gap days.",
        "- If pass-slice quality persists out of sample, consider formalizing a separate ruleset variant; do not mutate the baseline short grammar from this evidence alone.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_diagnostic(
    *,
    analyzer_runs_dir: Path,
    backtest_runs_dir: Path,
    start: date,
    end: date,
    detail_output: Path,
    summary_output: Path,
    finding_output: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    table = build_variant_table(
        analyzer_runs_dir=analyzer_runs_dir,
        backtest_runs_dir=backtest_runs_dir,
        start=start,
        end=end,
    )
    summary = summarize_variant(table)
    detail_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(detail_output, index=False, encoding="utf-8")
    summary.to_csv(summary_output, index=False, encoding="utf-8")
    if finding_output is not None:
        write_finding(
            table=table,
            summary=summary,
            output_path=finding_output,
            detail_path=detail_output,
            summary_path=summary_output,
            start=start,
            end=end,
        )
    return table, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyzer-runs-dir", type=Path, default=Path("analyzer_runs"))
    parser.add_argument("--backtest-runs-dir", type=Path, default=Path("backtest_runs"))
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--detail-output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--finding-output", type=Path, default=None)
    args = parser.parse_args()

    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    if end < start:
        raise ValueError("end-date must be >= start-date")

    suffix = f"{start.isoformat()}_to_{end.isoformat()}"
    detail_output = args.detail_output or Path(
        f"research/results/impulse_fade_reclaim_short_low_stress_v1_{suffix}.csv"
    )
    summary_output = args.summary_output or Path(
        f"research/results/impulse_fade_reclaim_short_low_stress_v1_summary_{suffix}.csv"
    )
    finding_output = args.finding_output
    if finding_output is None:
        finding_output = Path(f"research/findings/{VARIANT_ID}_{suffix}.md")

    table, summary = run_diagnostic(
        analyzer_runs_dir=args.analyzer_runs_dir,
        backtest_runs_dir=args.backtest_runs_dir,
        start=start,
        end=end,
        detail_output=detail_output,
        summary_output=summary_output,
        finding_output=finding_output,
    )
    print(f"wrote {len(table.index)} {VARIANT_ID} rows to {detail_output}")
    print(f"wrote summary to {summary_output}")
    print(summary.to_string(index=False))
    if finding_output is not None:
        print(f"wrote finding to {finding_output}")


if __name__ == "__main__":
    main()
