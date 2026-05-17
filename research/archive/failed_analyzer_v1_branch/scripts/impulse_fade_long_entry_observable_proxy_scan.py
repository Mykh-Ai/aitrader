"""Entry-observable proxy scan for IMPULSE_FADE_RECLAIM_LONG_V1.

This is a bounded research diagnostic. It reads existing Analyzer and
Backtester artifacts, joins entry-time observable features, and writes
namespaced research outputs. It does not modify Analyzer grammar, Backtester
rulesets, routine markers, collector/live/docker files, or feed files.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


SETUP_TYPE = "IMPULSE_FADE_RECLAIM_LONG_V1"
VARIANT_ID = SETUP_TYPE

PRE_GAP_START = date(2026, 3, 17)
PRE_GAP_END = date(2026, 4, 22)
POST_RECOVERY_START = date(2026, 5, 7)

MIN_TRADES = 18
MIN_PRE_TRADES = 12
MIN_POST_TRADES = 3

SPIKE_COLUMNS = [
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
]

FEATURE_COLUMNS = [
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "AggTrades",
    "BuyQty",
    "SellQty",
    "VWAP",
    "OpenInterest",
    "FundingRate",
    "Delta",
    "CVD",
    "DeltaPct",
    "BarRange",
    "BodySize",
    "UpperWick",
    "LowerWick",
    "CloseLocation",
    "BodyToRange",
    "UpperWickToRange",
    "LowerWickToRange",
    "OI_Change",
    "LiqTotal",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "AbsorptionScore_v1",
    "session",
    "minutes_from_eu_open",
    "minutes_from_us_open",
    "ImpulseRangeRatio_20_v1",
    "ImpulseVolumeRatio_v1",
    "ImpulseDeltaRatio_v1",
    "ImpulseOIRatio_v1",
    "ImpulseLiqConfirmed_v1",
    "PreCompression_6v20_v1",
    "PreCompressionTag_v1",
    "ImpulseAnchorHigh_v1",
    "ImpulseAnchorLow_v1",
    "ImpulseAnchorMid_v1",
    "ImpulseAnchorVWAP_v1",
]

DAY_REGIME_COLUMNS = [
    "RunDate",
    "EventDensityClass",
    "RangeExpansionClass",
    "FlowStressClass",
    "PhaseHeuristicLabel",
    "EventCount",
    "SetupCount",
    "ShortlistCount",
    "FormalizationEligibleCount",
    "MedianBarRange",
    "MedianVolume",
    "MedianAbsDelta",
    "MedianAbsOIChange",
    "MedianLiqTotal",
    "RelVolumeMedian",
    "SyntheticBarRatio",
]


@dataclass(frozen=True)
class Predicate:
    name: str
    family: str
    mask_fn: Callable[[pd.DataFrame], pd.Series]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--end-date", default=None, help="Latest completed post-recovery clean day.")
    parser.add_argument("--results-dir", default="research/results", type=Path)
    parser.add_argument("--findings-dir", default="research/findings", type=Path)
    return parser.parse_args()


def iter_days(start: date, end: date) -> Iterable[date]:
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def parse_day_from_run_id(name: str) -> date | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2})_to_\1_run_\d+", name)
    if not match:
        return None
    return date.fromisoformat(match.group(1))


def infer_latest_completed_clean_day(repo_root: Path) -> date:
    today_utc = datetime.now(timezone.utc).date()
    max_allowed = today_utc - timedelta(days=1)
    candidates: list[date] = []
    analyzer_root = repo_root / "analyzer_runs"
    for path in analyzer_root.glob("*_run_*"):
        day = parse_day_from_run_id(path.name)
        if day is None:
            continue
        if day < POST_RECOVERY_START or day > max_allowed:
            continue
        run_id = f"{day.isoformat()}_to_{day.isoformat()}_run_001"
        bt = latest_backtest_run_dir(repo_root / "backtest_runs", run_id)
        if bt is not None and is_completed_backtest(bt):
            candidates.append(day)
    if not candidates:
        raise RuntimeError("No completed post-recovery clean day with backtest artifacts found.")
    return max(candidates)


def latest_backtest_run_dir(backtest_runs_dir: Path, run_id: str) -> Path | None:
    matches = [
        *backtest_runs_dir.glob(f"{run_id}_routine_*"),
        *backtest_runs_dir.glob(f"{run_id}_archive_*"),
    ]
    if not matches:
        return None
    return max(matches, key=_backtest_run_sort_key)


def _backtest_run_sort_key(path: Path) -> tuple[int, int, str]:
    match = re.search(r"_(routine|archive)_(\d{8})$", path.name)
    if not match:
        return (0, 0, path.name)
    # Prefer the newest run date; routine/archive tie breaks by name only.
    return (int(match.group(2)), 1 if match.group(1) == "routine" else 0, path.name)


def is_completed_backtest(backtest_dir: Path) -> bool:
    manifest_path = backtest_dir / "backtest_orchestration_manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return manifest.get("completion_state") == "COMPLETED"


def find_derived_run(backtest_run_dir: Path) -> Path | None:
    candidates: list[Path] = []
    for ruleset_path in sorted(backtest_run_dir.rglob("backtest_rulesets.csv")):
        if ruleset_path.parent == backtest_run_dir:
            continue
        rulesets = pd.read_csv(ruleset_path)
        if len(rulesets.index) != 1:
            continue
        if str(rulesets.loc[0].get("setup_type")) == SETUP_TYPE:
            candidates.append(ruleset_path.parent)
    if not candidates:
        return None
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise ValueError(f"Multiple {SETUP_TYPE} derived runs found in {backtest_run_dir}: {names}")
    return candidates[0]


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def bool_value(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def bool_series(series: pd.Series) -> pd.Series:
    return series.map(bool_value).astype(bool)


def num(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(float("nan"), index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.where(denominator != 0)
    return numerator / denominator


def spike_count_from_row(row: pd.Series | dict[str, Any]) -> int:
    return sum(1 for column in SPIKE_COLUMNS if bool_value(row.get(column)))


def spike_signature_from_row(row: pd.Series | dict[str, Any]) -> str:
    parts: list[str] = []
    mapping = [
        ("CtxRelVolumeSpike_v1", "REL"),
        ("CtxDeltaSpike_v1", "DELTA"),
        ("CtxOISpike_v1", "OI"),
        ("CtxLiqSpike_v1", "LIQ"),
    ]
    for column, label in mapping:
        if bool_value(row.get(column)):
            parts.append(label)
    return "+".join(parts) if parts else "NONE"


def period_for_day(day: date) -> str:
    if PRE_GAP_START <= day <= PRE_GAP_END:
        return "pre_gap"
    if day >= POST_RECOVERY_START:
        return "post_recovery"
    return "excluded"


def make_prefixed_features(features: pd.DataFrame, prefix: str, ts_column: str) -> pd.DataFrame:
    selected = features.loc[:, [column for column in FEATURE_COLUMNS if column in features.columns]].copy()
    selected[ts_column] = pd.to_datetime(selected["Timestamp"], utc=True)
    rename_map = {column: f"{prefix}_{column}" for column in selected.columns if column != ts_column}
    return selected.rename(columns=rename_map)


def load_outcomes(analyzer_dir: Path) -> pd.DataFrame:
    outcomes = read_optional_csv(analyzer_dir / "analyzer_setup_outcomes.csv")
    if outcomes.empty:
        return pd.DataFrame(columns=["SetupId", "H2_Post3Label_v1", "H2_Post6Label_v1", "H2_Post12Label_v1"])
    columns = ["SetupId", "H2_Post3Label_v1", "H2_Post6Label_v1", "H2_Post12Label_v1"]
    return outcomes.loc[:, [column for column in columns if column in outcomes.columns]].copy()


def load_day_regime(analyzer_dir: Path) -> dict[str, Any]:
    report = read_optional_csv(analyzer_dir / "analyzer_day_regime_report.csv")
    if report.empty:
        return {}
    row = report.iloc[0].to_dict()
    return {column: row.get(column) for column in DAY_REGIME_COLUMNS if column in row}


def read_rows_for_day(
    *,
    repo_root: Path,
    day: date,
    coverage_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    run_id = f"{day.isoformat()}_to_{day.isoformat()}_run_001"
    analyzer_dir = repo_root / "analyzer_runs" / run_id
    if not analyzer_dir.exists():
        coverage_rows.append({"Date": day.isoformat(), "Status": "missing_analyzer", "BacktestRunId": ""})
        return pd.DataFrame()

    backtest_dir = latest_backtest_run_dir(repo_root / "backtest_runs", run_id)
    if backtest_dir is None:
        coverage_rows.append({"Date": day.isoformat(), "Status": "missing_backtest", "BacktestRunId": ""})
        return pd.DataFrame()
    if not is_completed_backtest(backtest_dir):
        coverage_rows.append({"Date": day.isoformat(), "Status": "backtest_not_completed", "BacktestRunId": backtest_dir.name})
        return pd.DataFrame()

    derived_dir = find_derived_run(backtest_dir)
    if derived_dir is None:
        coverage_rows.append({"Date": day.isoformat(), "Status": "completed_backtest_no_long_derived", "BacktestRunId": backtest_dir.name})
        return pd.DataFrame()

    paths = {
        "trades": derived_dir / "backtest_trades.csv",
        "rulesets": derived_dir / "backtest_rulesets.csv",
        "setups": analyzer_dir / "analyzer_setups.csv",
        "features": analyzer_dir / "analyzer_features.csv",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        coverage_rows.append(
            {
                "Date": day.isoformat(),
                "Status": "missing_required_artifact:" + "|".join(missing),
                "BacktestRunId": backtest_dir.name,
            }
        )
        return pd.DataFrame()

    trades = pd.read_csv(paths["trades"])
    ruleset = pd.read_csv(paths["rulesets"]).iloc[0]
    setups = pd.read_csv(paths["setups"])
    features = pd.read_csv(paths["features"])

    trades = trades.loc[trades["direction"] == "LONG"].copy()
    setups = setups.loc[setups["SetupType"] == SETUP_TYPE].copy()
    if trades.empty or setups.empty:
        coverage_rows.append({"Date": day.isoformat(), "Status": "long_derived_zero_trades", "BacktestRunId": backtest_dir.name})
        return pd.DataFrame()

    outcomes = load_outcomes(analyzer_dir)
    day_regime = load_day_regime(analyzer_dir)

    merged = trades.merge(
        setups,
        left_on="source_setup_id",
        right_on="SetupId",
        how="inner",
        suffixes=("", "_setup"),
    )
    if not outcomes.empty:
        merged = merged.merge(outcomes, on="SetupId", how="left")

    merged["SetupBarTsParsed"] = pd.to_datetime(merged["SetupBarTs"], utc=True)
    merged["ReferenceEventTsParsed"] = pd.to_datetime(merged["ReferenceEventTs"], utc=True)
    merged["EntryTs"] = pd.to_datetime(merged["entry_signal_ts"], utc=True)
    merged["EntryHourUTC"] = merged["EntryTs"].dt.hour

    setup_features = make_prefixed_features(features, "Setup", "SetupBarTsParsed")
    impulse_features = make_prefixed_features(features, "Impulse", "ReferenceEventTsParsed")
    merged = merged.merge(setup_features, on="SetupBarTsParsed", how="left")
    merged = merged.merge(impulse_features, on="ReferenceEventTsParsed", how="left")

    for key, value in day_regime.items():
        merged[key] = value

    merged["VariantId"] = VARIANT_ID
    merged["Date"] = day.isoformat()
    merged["AnalyzerRunId"] = analyzer_dir.name
    merged["BacktestRunId"] = backtest_dir.name
    merged["DerivedRunId"] = derived_dir.name
    merged["RulesetId"] = ruleset["ruleset_id"]
    merged["EntrySignalTs"] = merged["entry_signal_ts"]
    merged["EntryActivationTs"] = merged["entry_activation_ts"]
    merged["ExitTs"] = merged["exit_ts"]
    merged["ExitReason"] = merged["exit_reason"]
    merged["ExitReasonCategory"] = merged["exit_reason_category"]
    merged["TradeReturnPct"] = pd.to_numeric(merged["trade_return_pct"], errors="coerce")
    merged["TradePnl"] = pd.to_numeric(merged["trade_pnl"], errors="coerce")
    merged["Resolved"] = merged["ExitTs"].notna() & (merged["ExitReason"].fillna("").astype(str).str.len() > 0)
    merged["Win"] = merged["TradePnl"] > 0
    merged["Period"] = period_for_day(day)
    merged["FullFade"] = merged["H2_Post12Label_v1"].fillna("").astype(str).eq("FULL_FADE")
    merged["NoFade"] = merged["H2_Post12Label_v1"].fillna("").astype(str).eq("NO_FADE")
    merged["SpikeCount"] = merged.apply(spike_count_from_row, axis=1)
    merged["SpikeSignature"] = merged.apply(spike_signature_from_row, axis=1)
    merged["ReclaimDelayBars"] = (
        (merged["SetupBarTsParsed"] - merged["ReferenceEventTsParsed"]).dt.total_seconds() / 60.0
    )

    setup_close = num(merged, "Setup_Close")
    reference_level = num(merged, "ReferenceLevel")
    setup_range = num(merged, "Setup_BarRange")
    impulse_high = num(merged, "Impulse_High")
    impulse_low = num(merged, "Impulse_Low")
    impulse_range = num(merged, "Impulse_BarRange")

    merged["ReclaimDepthUsd"] = setup_close - reference_level
    merged["ReclaimDepthPct"] = safe_div(merged["ReclaimDepthUsd"], reference_level)
    merged["ReclaimDepthToSetupRange"] = safe_div(merged["ReclaimDepthUsd"], setup_range)
    merged["ReclaimDepthToImpulseRange"] = safe_div(merged["ReclaimDepthUsd"], impulse_range)
    merged["SetupCloseLocationInImpulseRange"] = safe_div(setup_close - impulse_low, impulse_high - impulse_low)

    coverage_rows.append(
        {
            "Date": day.isoformat(),
            "Status": "completed_long_trades",
            "BacktestRunId": backtest_dir.name,
            "DerivedRunId": derived_dir.name,
            "Trades": len(merged.index),
        }
    )
    return merged


def output_columns(df: pd.DataFrame) -> list[str]:
    base_columns = [
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
        "SpikeSignature",
        "H2_Post3Label_v1",
        "H2_Post6Label_v1",
        "H2_Post12Label_v1",
        "Period",
        *DAY_REGIME_COLUMNS,
        "EntryTs",
        "EntryHourUTC",
        "FullFade",
        "NoFade",
        "SetupBarTs",
        "ReferenceEventTs",
        "ReferenceLevel",
        "LifecycleStatus",
        "InvalidatedAt",
        "ExpiredAt",
        "SetupBarTsParsed",
        "ReferenceEventTsParsed",
    ]
    feature_prefixed = [
        f"{prefix}_{column}"
        for prefix in ("Setup", "Impulse")
        for column in FEATURE_COLUMNS
        if f"{prefix}_{column}" in df.columns
    ]
    derived = [
        "ReclaimDelayBars",
        "ReclaimDepthPct",
        "ReclaimDepthUsd",
        "ReclaimDepthToSetupRange",
        "ReclaimDepthToImpulseRange",
        "SetupCloseLocationInImpulseRange",
    ]
    return [column for column in [*base_columns, *feature_prefixed, *derived] if column in df.columns]


def metrics_for(selector: str, condition_count: int, df: pd.DataFrame, base_full_fade_rate: float) -> dict[str, Any]:
    trades = len(df.index)
    resolved = int(df["Resolved"].sum()) if "Resolved" in df.columns else trades
    wins = int(df["Win"].sum()) if "Win" in df.columns else 0
    pnl = float(num(df, "TradePnl").fillna(0.0).sum())
    pre = df.loc[df["Period"] == "pre_gap"].copy()
    post = df.loc[df["Period"] == "post_recovery"].copy()
    day_split = day_split_metrics(df)
    return {
        "Selector": selector,
        "Conditions": condition_count,
        "Trades": trades,
        "Resolved": resolved,
        "Wins": wins,
        "WinRate": wins / trades if trades else math.nan,
        "FullFadeRate": rate(df, "FullFade"),
        "FullFadeLift": rate(df, "FullFade") - base_full_fade_rate if trades else math.nan,
        "NoFadeRate": rate(df, "NoFade"),
        "PartialFadeRate": label_rate(df, "PARTIAL_FADE"),
        "Pnl": pnl,
        "AvgPnl": pnl / trades if trades else math.nan,
        "MedianPnl": float(num(df, "TradePnl").median()) if trades else math.nan,
        "MaxDrawdownPnl": max_drawdown_pnl(df),
        "Top1Pnl": top_n_winners(df, 1),
        "Bottom1Pnl": bottom_n_losers(df, 1),
        "PreTrades": len(pre.index),
        "PreWinRate": rate(pre, "Win"),
        "PreFullFadeRate": rate(pre, "FullFade"),
        "PreNoFadeRate": rate(pre, "NoFade"),
        "PrePnl": float(num(pre, "TradePnl").fillna(0.0).sum()),
        "PostTrades": len(post.index),
        "PostWinRate": rate(post, "Win"),
        "PostFullFadeRate": rate(post, "FullFade"),
        "PostNoFadeRate": rate(post, "NoFade"),
        "PostPnl": float(num(post, "TradePnl").fillna(0.0).sum()),
        **day_split,
    }


def rate(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return math.nan
    return float(df[column].fillna(False).astype(bool).mean())


def label_rate(df: pd.DataFrame, label: str) -> float:
    if df.empty or "H2_Post12Label_v1" not in df.columns:
        return math.nan
    return float(df["H2_Post12Label_v1"].fillna("").astype(str).eq(label).mean())


def max_drawdown_pnl(df: pd.DataFrame) -> float:
    if df.empty:
        return math.nan
    ordered = df.sort_values("EntryTs")
    equity = num(ordered, "TradePnl").fillna(0.0).cumsum()
    drawdown = equity - equity.cummax()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def top_n_winners(df: pd.DataFrame, n: int) -> float:
    pnl = num(df, "TradePnl").dropna()
    winners = pnl.loc[pnl > 0].sort_values(ascending=False).head(n)
    return float(winners.sum()) if not winners.empty else 0.0


def bottom_n_losers(df: pd.DataFrame, n: int) -> float:
    pnl = num(df, "TradePnl").dropna()
    losers = pnl.loc[pnl < 0].sort_values(ascending=True).head(n)
    return float(losers.sum()) if not losers.empty else 0.0


def day_split_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "DayCount": 0,
            "PositiveDayCount": 0,
            "NegativeDayCount": 0,
            "FlatDayCount": 0,
            "BestDay": "",
            "BestDayTrades": 0,
            "BestDayPnl": math.nan,
            "WorstDay": "",
            "WorstDayTrades": 0,
            "WorstDayPnl": math.nan,
            "MedianDayPnl": math.nan,
        }
    grouped = df.groupby("Date", dropna=False).agg(Trades=("SetupId", "count"), Pnl=("TradePnl", "sum"))
    best_idx = grouped["Pnl"].idxmax()
    worst_idx = grouped["Pnl"].idxmin()
    return {
        "DayCount": int(len(grouped.index)),
        "PositiveDayCount": int((grouped["Pnl"] > 0).sum()),
        "NegativeDayCount": int((grouped["Pnl"] < 0).sum()),
        "FlatDayCount": int((grouped["Pnl"] == 0).sum()),
        "BestDay": best_idx,
        "BestDayTrades": int(grouped.loc[best_idx, "Trades"]),
        "BestDayPnl": float(grouped.loc[best_idx, "Pnl"]),
        "WorstDay": worst_idx,
        "WorstDayTrades": int(grouped.loc[worst_idx, "Trades"]),
        "WorstDayPnl": float(grouped.loc[worst_idx, "Pnl"]),
        "MedianDayPnl": float(grouped["Pnl"].median()),
    }


def build_predicates() -> list[Predicate]:
    def gt(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) > threshold).fillna(False)

    def ge(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) >= threshold).fillna(False)

    def le(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) <= threshold).fillna(False)

    def eq_str(column: str, value: str) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: df[column].fillna("").astype(str).eq(value) if column in df else pd.Series(False, index=df.index)

    def is_true(column: str) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: bool_series(df[column]) if column in df else pd.Series(False, index=df.index)

    def low_stress(df: pd.DataFrame) -> pd.Series:
        return (
            le("RelVolume_20", 1.5)(df)
            & le("DeltaAbsRatio_20", 2.0)(df)
            & le("OIChangeAbsRatio_20", 5.0)(df)
            & le("SpikeCount", 2)(df)
        )

    def high_stress(df: pd.DataFrame) -> pd.Series:
        return (
            gt("RelVolume_20", 1.5)(df)
            | gt("DeltaAbsRatio_20", 2.0)(df)
            | gt("OIChangeAbsRatio_20", 5.0)(df)
            | ge("SpikeCount", 3)(df)
        ).fillna(False)

    def zero_spike(df: pd.DataFrame) -> pd.Series:
        return num(df, "SpikeCount").fillna(-1).eq(0)

    def wick_reclaim_long(df: pd.DataFrame) -> pd.Series:
        return ge("Setup_LowerWickToRange", 0.25)(df) & ge("Setup_CloseLocation", 0.75)(df)

    return [
        Predicate("low_stress_long", "stress", low_stress),
        Predicate("high_stress_long", "stress", high_stress),
        Predicate("zero_spike_long", "spike", zero_spike),
        Predicate("spike_count_ge_2", "spike", ge("SpikeCount", 2)),
        Predicate("spike_count_ge_3", "spike", ge("SpikeCount", 3)),
        Predicate("rel_volume_le_1p0", "setup_stress", le("RelVolume_20", 1.0)),
        Predicate("rel_volume_le_1p5", "setup_stress", le("RelVolume_20", 1.5)),
        Predicate("rel_volume_gt_1p5", "setup_stress", gt("RelVolume_20", 1.5)),
        Predicate("delta_abs_le_2p0", "setup_stress", le("DeltaAbsRatio_20", 2.0)),
        Predicate("delta_abs_gt_2p0", "setup_stress", gt("DeltaAbsRatio_20", 2.0)),
        Predicate("oi_abs_le_5p0", "setup_stress", le("OIChangeAbsRatio_20", 5.0)),
        Predicate("oi_abs_gt_5p0", "setup_stress", gt("OIChangeAbsRatio_20", 5.0)),
        Predicate("liq_ratio_eq_0", "setup_stress", le("LiqTotalRatio_20", 0.0)),
        Predicate("ctx_rel_spike", "spike", is_true("CtxRelVolumeSpike_v1")),
        Predicate("ctx_delta_spike", "spike", is_true("CtxDeltaSpike_v1")),
        Predicate("ctx_oi_spike", "spike", is_true("CtxOISpike_v1")),
        Predicate("ctx_liq_spike", "spike", is_true("CtxLiqSpike_v1")),
        Predicate("depth_impulse_gt_0p3", "deep_reclaim", gt("ReclaimDepthToImpulseRange", 0.3)),
        Predicate("depth_impulse_gt_0p4", "deep_reclaim", gt("ReclaimDepthToImpulseRange", 0.4)),
        Predicate("depth_impulse_gt_0p5", "deep_reclaim", gt("ReclaimDepthToImpulseRange", 0.5)),
        Predicate("depth_impulse_gt_0p6", "deep_reclaim", gt("ReclaimDepthToImpulseRange", 0.6)),
        Predicate("depth_setup_gt_0p5", "deep_reclaim", gt("ReclaimDepthToSetupRange", 0.5)),
        Predicate("depth_setup_gt_1p0", "deep_reclaim", gt("ReclaimDepthToSetupRange", 1.0)),
        Predicate("setup_in_impulse_ge_0p5", "reclaim_location", ge("SetupCloseLocationInImpulseRange", 0.5)),
        Predicate("setup_in_impulse_ge_0p75", "reclaim_location", ge("SetupCloseLocationInImpulseRange", 0.75)),
        Predicate("setup_in_impulse_ge_1p0", "reclaim_location", ge("SetupCloseLocationInImpulseRange", 1.0)),
        Predicate("setup_body_gt_0p5", "setup_shape", gt("Setup_BodyToRange", 0.5)),
        Predicate("setup_body_gt_0p75", "setup_shape", gt("Setup_BodyToRange", 0.75)),
        Predicate("setup_close_loc_ge_0p75", "setup_shape", ge("Setup_CloseLocation", 0.75)),
        Predicate("setup_close_loc_ge_0p9", "setup_shape", ge("Setup_CloseLocation", 0.9)),
        Predicate("setup_lower_wick_ge_0p25", "setup_shape", ge("Setup_LowerWickToRange", 0.25)),
        Predicate("setup_lower_wick_ge_0p4", "setup_shape", ge("Setup_LowerWickToRange", 0.4)),
        Predicate("setup_upper_wick_le_0p25", "setup_shape", le("Setup_UpperWickToRange", 0.25)),
        Predicate("wick_reclaim_long", "setup_shape", wick_reclaim_long),
        Predicate("session_asia", "session", eq_str("Setup_session", "ASIA")),
        Predicate("session_eu", "session", eq_str("Setup_session", "EU")),
        Predicate("session_us", "session", eq_str("Setup_session", "US")),
        Predicate("entry_hour_0_7", "session", lambda df: num(df, "EntryHourUTC").between(0, 7, inclusive="both").fillna(False)),
        Predicate("entry_hour_8_15", "session", lambda df: num(df, "EntryHourUTC").between(8, 15, inclusive="both").fillna(False)),
        Predicate("entry_hour_16_23", "session", lambda df: num(df, "EntryHourUTC").between(16, 23, inclusive="both").fillna(False)),
        Predicate("impulse_body_gt_0p75", "impulse_shape", gt("Impulse_BodyToRange", 0.75)),
        Predicate("impulse_close_loc_le_0p25", "impulse_shape", le("Impulse_CloseLocation", 0.25)),
        Predicate("impulse_lower_wick_le_0p25", "impulse_shape", le("Impulse_LowerWickToRange", 0.25)),
        Predicate("impulse_range_ratio_gt_1p5", "impulse_stress", gt("Impulse_ImpulseRangeRatio_20_v1", 1.5)),
        Predicate("impulse_range_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseRangeRatio_20_v1", 2.0)),
        Predicate("impulse_volume_ratio_gt_1p5", "impulse_stress", gt("Impulse_ImpulseVolumeRatio_v1", 1.5)),
        Predicate("impulse_delta_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseDeltaRatio_v1", 2.0)),
        Predicate("impulse_oi_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseOIRatio_v1", 2.0)),
        Predicate("impulse_liq_confirmed", "impulse_stress", is_true("Impulse_ImpulseLiqConfirmed_v1")),
        Predicate("impulse_precompression_tag", "compression", is_true("Impulse_PreCompressionTag_v1")),
        Predicate("impulse_precompression_lt_0p8", "compression", le("Impulse_PreCompression_6v20_v1", 0.8)),
        Predicate("impulse_precompression_lt_1p0", "compression", le("Impulse_PreCompression_6v20_v1", 1.0)),
    ]


def scan_predicates(df: pd.DataFrame, predicates: list[Predicate], base_full_fade_rate: float) -> pd.DataFrame:
    masks = {predicate.name: predicate.mask_fn(df).fillna(False).astype(bool) for predicate in predicates}
    rows: list[dict[str, Any]] = []
    for condition_count in (1, 2, 3):
        for combo in itertools.combinations(predicates, condition_count):
            selector = " & ".join(predicate.name for predicate in combo)
            mask = pd.Series(True, index=df.index)
            for predicate in combo:
                mask &= masks[predicate.name]
            subset = df.loc[mask].copy()
            if len(subset.index) < MIN_TRADES:
                continue
            if int((subset["Period"] == "pre_gap").sum()) < MIN_PRE_TRADES:
                continue
            if int((subset["Period"] == "post_recovery").sum()) < MIN_POST_TRADES:
                continue
            row = metrics_for(selector, condition_count, subset, base_full_fade_rate)
            row["Families"] = "+".join(sorted({predicate.family for predicate in combo}))
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    scan = pd.DataFrame(rows)
    scan = scan.sort_values(
        ["FullFadeLift", "Pnl", "PostPnl", "Trades"],
        ascending=[False, False, False, False],
        kind="mergesort",
    ).reset_index(drop=True)
    return scan


def stable_scan(scan: pd.DataFrame, base_full_fade_rate: float, base_no_fade_rate: float) -> pd.DataFrame:
    if scan.empty:
        return scan.copy()
    stable = scan.loc[
        (scan["Pnl"] > 0)
        & (scan["PrePnl"] > 0)
        & (scan["PostPnl"] > 0)
        & (scan["FullFadeRate"] >= base_full_fade_rate)
        & (scan["NoFadeRate"] <= base_no_fade_rate)
        & (scan["PositiveDayCount"] >= scan["NegativeDayCount"])
    ].copy()
    return stable.reset_index(drop=True)


def threshold_sweep(df: pd.DataFrame, base_full_fade_rate: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for threshold in (0.3, 0.4, 0.5, 0.6):
        for body_threshold in (None, 0.75):
            mask = num(df, "ReclaimDepthToImpulseRange") > threshold
            selector = f"depth_impulse_gt_{threshold:.1f}"
            if body_threshold is not None:
                mask &= num(df, "Setup_BodyToRange") > body_threshold
                selector += f"_body_gt_{body_threshold:.2f}"
            subset = df.loc[mask.fillna(False)].copy()
            row = metrics_for(selector, 1 if body_threshold is None else 2, subset, base_full_fade_rate)
            row["Threshold"] = threshold
            row["BodyThreshold"] = body_threshold
            rows.append(row)
    return pd.DataFrame(rows)


def selector_mask(df: pd.DataFrame, selector: str, predicates_by_name: dict[str, Predicate]) -> pd.Series:
    if selector == "raw_all":
        return pd.Series(True, index=df.index)
    mask = pd.Series(True, index=df.index)
    for name in selector.split(" & "):
        predicate = predicates_by_name[name]
        mask &= predicate.mask_fn(df).fillna(False).astype(bool)
    return mask


def choose_candidate_selectors(scan: pd.DataFrame, stable: pd.DataFrame) -> list[str]:
    selectors: list[str] = ["raw_all"]
    preferred = [
        "depth_impulse_gt_0p3",
        "depth_impulse_gt_0p4",
        "depth_impulse_gt_0p5",
        "depth_impulse_gt_0p6",
        "low_stress_long",
        "high_stress_long",
        "zero_spike_long",
        "setup_body_gt_0p75",
        "wick_reclaim_long",
        "impulse_precompression_tag",
        "session_asia",
        "session_eu",
        "session_us",
    ]
    scan_selectors = set(scan["Selector"]) if not scan.empty else set()
    for selector in preferred:
        if selector in scan_selectors:
            selectors.append(selector)
    top_source = stable if not stable.empty else scan
    for selector in top_source.head(10)["Selector"].tolist() if not top_source.empty else []:
        selectors.append(selector)

    deduped: list[str] = []
    for selector in selectors:
        if selector not in deduped:
            deduped.append(selector)
    return deduped[:20]


def cluster_first(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes == 0 or df.empty:
        return df.copy()
    ordered = df.sort_values("EntryTs")
    keep_indices: list[Any] = []
    last_kept: pd.Timestamp | None = None
    for idx, row in ordered.iterrows():
        ts = row["EntryTs"]
        if pd.isna(ts):
            continue
        if last_kept is None or (ts - last_kept).total_seconds() >= minutes * 60:
            keep_indices.append(idx)
            last_kept = ts
    return ordered.loc[keep_indices].copy()


def cluster_summary(
    df: pd.DataFrame,
    selectors: list[str],
    predicates_by_name: dict[str, Predicate],
    base_full_fade_rate: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    windows = [0, 30, 60, 120, 240, 480, 1440]
    for selector in selectors:
        raw = df.loc[selector_mask(df, selector, predicates_by_name)].copy()
        for window in windows:
            clustered = cluster_first(raw, window)
            row = metrics_for(selector, selector.count("&") + 1 if selector != "raw_all" else 0, clustered, base_full_fade_rate)
            row["Candidate"] = selector
            row["ClusterWindowMinutes"] = window
            row["RawTradesBeforeCluster"] = len(raw.index)
            row["DroppedDuplicates"] = len(raw.index) - len(clustered.index)
            rows.append(row)
    return pd.DataFrame(rows)


def pnl_concentration(
    df: pd.DataFrame,
    selectors: list[str],
    predicates_by_name: dict[str, Predicate],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for selector in selectors:
        subset = df.loc[selector_mask(df, selector, predicates_by_name)].copy()
        total_pnl = float(num(subset, "TradePnl").fillna(0.0).sum())
        gross_loss = float(abs(num(subset, "TradePnl").loc[num(subset, "TradePnl") < 0].sum()))
        for n in (1, 2, 3):
            top_winners = top_n_winners(subset, n)
            bottom_losers = bottom_n_losers(subset, n)
            rows.append(
                {
                    "Candidate": selector,
                    "TopN": n,
                    "Trades": len(subset.index),
                    "TopNWinnerPnl": top_winners,
                    "TopNLoserPnl": bottom_losers,
                    "TotalPnl": total_pnl,
                    "TopWinnerShareOfTotal": top_winners / total_pnl if total_pnl else math.nan,
                    "BottomLoserShareOfGrossLoss": abs(bottom_losers) / gross_loss if gross_loss else math.nan,
                }
            )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 10) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, [column for column in columns if column in df.columns]].head(max_rows).copy()
    for column in view.columns:
        if pd.api.types.is_float_dtype(view[column]):
            view[column] = view[column].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
    header = "| " + " | ".join(view.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    lines = [header, sep]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in view.columns) + " |")
    return "\n".join(lines)


def write_finding(
    *,
    path: Path,
    window: str,
    latest_completed_day: date,
    feature_path: Path,
    scan_path: Path,
    stable_path: Path,
    sweep_path: Path,
    cluster_path: Path,
    concentration_path: Path,
    coverage: pd.DataFrame,
    base: dict[str, Any],
    scan: pd.DataFrame,
    stable: pd.DataFrame,
    sweep: pd.DataFrame,
    cluster: pd.DataFrame,
    concentration: pd.DataFrame,
) -> None:
    missing = coverage.loc[coverage["Status"].isin(["missing_analyzer", "missing_backtest", "backtest_not_completed"])]
    completed_no_long = coverage.loc[coverage["Status"].eq("completed_backtest_no_long_derived")]
    top_source = stable if not stable.empty else scan
    top_rows = top_source.head(8).copy()
    raw_cluster = cluster.loc[cluster["Candidate"].eq("raw_all")].copy()

    deep_rows = sweep.loc[sweep["BodyThreshold"].isna()].copy()
    deep_06 = deep_rows.loc[deep_rows["Threshold"].eq(0.6)]
    deep_06_row = deep_06.iloc[0].to_dict() if not deep_06.empty else {}

    if stable.empty:
        lead_text = "No stable long-side proxy passed the split-positive stability filter."
    else:
        lead = stable.iloc[0]
        lead_text = (
            f"Best stable selector by this scan is `{lead['Selector']}` with "
            f"{int(lead['Trades'])} trades, PnL {lead['Pnl']:.2f}, "
            f"winrate {lead['WinRate']:.2%}, FULL_FADE {lead['FullFadeRate']:.2%}."
        )

    deep_text = "Deep reclaim was not available at the requested thresholds."
    if deep_06_row:
        deep_text = (
            "`ReclaimDepthToImpulseRange > 0.6` produced "
            f"{int(deep_06_row['Trades'])} trades, PnL {deep_06_row['Pnl']:.2f}, "
            f"winrate {deep_06_row['WinRate']:.2%}, FULL_FADE {deep_06_row['FullFadeRate']:.2%}, "
            f"post-recovery trades {int(deep_06_row['PostTrades'])}."
        )

    stable_conclusion = (
        "Forward watchlist candidate exists, but it remains research-only."
        if not stable.empty
        else "No forward-watchlist candidate should be promoted from this scan."
    )

    text = f"""# IMPULSE_FADE_RECLAIM_LONG_V1 Entry-Observable Proxy Scan

Date: {datetime.now(timezone.utc).date().isoformat()}

Status: research diagnostic only. No Analyzer grammar change, no Backtester ruleset change, no live implication.

## Clean Windows

- Pre-gap clean archive: 2026-03-17..2026-04-22.
- Post-recovery clean archive: 2026-05-07..{latest_completed_day.isoformat()}.
- Broken feed gap excluded: 2026-04-23 17:05 UTC..2026-05-06 22:51 UTC.
- Window label: `{window}`.

## Inputs

- Entry-observable feature table: `{feature_path.as_posix()}`.
- Full proxy scan: `{scan_path.as_posix()}`.
- Stable proxy subset: `{stable_path.as_posix()}`.
- Deep reclaim threshold sweep: `{sweep_path.as_posix()}`.
- Cluster-first summary: `{cluster_path.as_posix()}`.
- PnL concentration: `{concentration_path.as_posix()}`.

`H2_Post12Label_v1` is used only as a target label: `FULL_FADE`, `PARTIAL_FADE`, `NO_FADE`. It is not used in entry predicates.

## Coverage

Base completed long trades: {int(base['Trades'])}

Pre-gap trades: {int(base['PreTrades'])}; post-recovery trades: {int(base['PostTrades'])}.

Missing completed-backtest coverage:

{markdown_table(missing, ['Date', 'Status', 'BacktestRunId'], max_rows=40)}

Completed backtest days with no long derived run:

{markdown_table(completed_no_long, ['Date', 'Status', 'BacktestRunId'], max_rows=40)}

## Baseline Long Set

| Metric | Value |
| --- | ---: |
| Trades | {int(base['Trades'])} |
| Winrate | {base['WinRate']:.2%} |
| PnL | {base['Pnl']:.2f} |
| Max drawdown PnL | {base['MaxDrawdownPnl']:.2f} |
| FULL_FADE rate | {base['FullFadeRate']:.2%} |
| NO_FADE rate | {base['NoFadeRate']:.2%} |
| Pre-gap PnL | {base['PrePnl']:.2f} |
| Post-recovery PnL | {base['PostPnl']:.2f} |

## Main Result

{lead_text}

Top stable/proxy rows:

{markdown_table(top_rows, ['Selector', 'Conditions', 'Trades', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'PreTrades', 'PrePnl', 'PostTrades', 'PostPnl', 'WorstDay', 'WorstDayPnl'], max_rows=8)}

## Deep Reclaim

LONG reclaim depth is calculated as:

`(setup_close - ReferenceLevel) / impulse_bar_range`.

{deep_text}

Threshold sweep:

{markdown_table(sweep, ['Selector', 'Trades', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'PreTrades', 'PostTrades', 'PrePnl', 'PostPnl'], max_rows=12)}

## Cluster-First Robustness

Raw baseline cluster view:

{markdown_table(raw_cluster, ['Candidate', 'ClusterWindowMinutes', 'Trades', 'DroppedDuplicates', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'PreTrades', 'PostTrades'], max_rows=8)}

Best candidate cluster rows:

{markdown_table(cluster.loc[~cluster['Candidate'].eq('raw_all')], ['Candidate', 'ClusterWindowMinutes', 'Trades', 'DroppedDuplicates', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'PreTrades', 'PostTrades'], max_rows=18)}

## PnL Concentration

{markdown_table(concentration, ['Candidate', 'TopN', 'Trades', 'TopNWinnerPnl', 'TopNLoserPnl', 'TotalPnl', 'TopWinnerShareOfTotal'], max_rows=24)}

## Interpretation

- Long-side research lead: {stable_conclusion}
- Deep reclaim for long: see threshold sweep above; do not assume short-side symmetry.
- Context: compare low-stress/high-stress/zero-spike/session/compression rows in the proxy scan before selecting any sidecar.
- Do not promote: no baseline Analyzer grammar or Backtester ruleset promotion is justified from this diagnostic alone.
- Next narrow step: forward-watch only the best split-stable selector(s) on new clean days and re-run the same raw/cluster/concentration tables.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    latest_day = date.fromisoformat(args.end_date) if args.end_date else infer_latest_completed_clean_day(repo_root)
    window = f"{PRE_GAP_START.isoformat()}_to_{latest_day.isoformat()}"

    results_dir = (repo_root / args.results_dir).resolve()
    findings_dir = (repo_root / args.findings_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    findings_dir.mkdir(parents=True, exist_ok=True)

    coverage_rows: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    clean_days = [*iter_days(PRE_GAP_START, PRE_GAP_END), *iter_days(POST_RECOVERY_START, latest_day)]
    for day in clean_days:
        frame = read_rows_for_day(repo_root=repo_root, day=day, coverage_rows=coverage_rows)
        if not frame.empty:
            frames.append(frame)

    if not frames:
        raise RuntimeError(f"No {SETUP_TYPE} completed trades found in clean windows.")

    features = pd.concat(frames, ignore_index=True)
    features = features.sort_values(["EntryTs", "SetupId"]).reset_index(drop=True)
    coverage = pd.DataFrame(coverage_rows)

    feature_path = results_dir / f"impulse_fade_long_entry_observable_features_{window}.csv"
    scan_path = results_dir / f"impulse_fade_long_proxy_scan_{window}.csv"
    stable_path = results_dir / f"impulse_fade_long_proxy_stable_{window}.csv"
    sweep_path = results_dir / f"impulse_fade_long_deep_reclaim_threshold_sweep_{window}.csv"
    cluster_path = results_dir / f"impulse_fade_long_cluster_summary_{window}.csv"
    concentration_path = results_dir / f"impulse_fade_long_pnl_concentration_{window}.csv"
    coverage_path = results_dir / f"impulse_fade_long_coverage_{window}.csv"
    finding_path = findings_dir / f"IMPULSE_FADE_LONG_ENTRY_OBSERVABLE_PROXY_SCAN_{window}.md"

    features.loc[:, output_columns(features)].to_csv(feature_path, index=False)
    coverage.to_csv(coverage_path, index=False)

    base = metrics_for("raw_all", 0, features, base_full_fade_rate=0.0)
    base_full_fade_rate = base["FullFadeRate"]
    base_no_fade_rate = base["NoFadeRate"]

    predicates = build_predicates()
    predicates_by_name = {predicate.name: predicate for predicate in predicates}
    scan = scan_predicates(features, predicates, base_full_fade_rate)
    stable = stable_scan(scan, base_full_fade_rate, base_no_fade_rate)
    sweep = threshold_sweep(features, base_full_fade_rate)
    selectors = choose_candidate_selectors(scan, stable)
    cluster = cluster_summary(features, selectors, predicates_by_name, base_full_fade_rate)
    concentration = pnl_concentration(features, selectors, predicates_by_name)

    scan.to_csv(scan_path, index=False)
    stable.to_csv(stable_path, index=False)
    sweep.to_csv(sweep_path, index=False)
    cluster.to_csv(cluster_path, index=False)
    concentration.to_csv(concentration_path, index=False)

    write_finding(
        path=finding_path,
        window=window,
        latest_completed_day=latest_day,
        feature_path=feature_path.relative_to(repo_root),
        scan_path=scan_path.relative_to(repo_root),
        stable_path=stable_path.relative_to(repo_root),
        sweep_path=sweep_path.relative_to(repo_root),
        cluster_path=cluster_path.relative_to(repo_root),
        concentration_path=concentration_path.relative_to(repo_root),
        coverage=coverage,
        base=base,
        scan=scan,
        stable=stable,
        sweep=sweep,
        cluster=cluster,
        concentration=concentration,
    )

    print(
        json.dumps(
            {
                "window": window,
                "latest_completed_clean_day": latest_day.isoformat(),
                "trades": int(len(features.index)),
                "pre_gap_trades": int((features["Period"] == "pre_gap").sum()),
                "post_recovery_trades": int((features["Period"] == "post_recovery").sum()),
                "scan_rows": int(len(scan.index)),
                "stable_rows": int(len(stable.index)),
                "outputs": [
                    str(feature_path.relative_to(repo_root)),
                    str(scan_path.relative_to(repo_root)),
                    str(stable_path.relative_to(repo_root)),
                    str(sweep_path.relative_to(repo_root)),
                    str(cluster_path.relative_to(repo_root)),
                    str(concentration_path.relative_to(repo_root)),
                    str(finding_path.relative_to(repo_root)),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
