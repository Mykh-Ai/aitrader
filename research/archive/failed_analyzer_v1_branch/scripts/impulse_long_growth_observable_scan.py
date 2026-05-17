"""Entry-observable growth scan for long-oriented impulse surfaces.

Research-only diagnostic. It reads existing Analyzer artifacts and scans
entry-time observable predicates against forward growth outcomes. It does not
modify Analyzer grammar, Backtester rulesets, collector/live/docker files, or
feed files.

Surfaces:
- RECLAIM_LONG: IMPULSE_FADE_RECLAIM_LONG_V1 setup rows, using Analyzer setup
  outcomes.
- IMPULSE_UP_CONTINUATION: raw IMPULSE_UP feature rows, using an internal
  12-bar forward outcome calculation from analyzer_features.csv.
"""

from __future__ import annotations

import argparse
import hashlib
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


PRE_GAP_START = date(2026, 3, 17)
PRE_GAP_END = date(2026, 4, 22)
POST_RECOVERY_START = date(2026, 5, 7)

RECLAIM_SETUP_TYPE = "IMPULSE_FADE_RECLAIM_LONG_V1"
OUTCOME_HORIZON_BARS = 12

MIN_ROWS = 18
MIN_PRE_ROWS = 12
MIN_POST_ROWS = 3

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
    "ImpulseDetected_v1",
    "ImpulseDirection_v1",
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
    max_allowed = datetime.now(timezone.utc).date() - timedelta(days=1)
    candidates: list[date] = []
    for path in (repo_root / "analyzer_runs").glob("*_run_*"):
        day = parse_day_from_run_id(path.name)
        if day is None or day < POST_RECOVERY_START or day > max_allowed:
            continue
        required = [path / "analyzer_features.csv", path / "analyzer_setups.csv", path / "analyzer_setup_outcomes.csv"]
        if all(item.exists() for item in required):
            candidates.append(day)
    if not candidates:
        raise RuntimeError("No completed post-recovery Analyzer day found.")
    return max(candidates)


def period_for_day(day: date) -> str:
    if PRE_GAP_START <= day <= PRE_GAP_END:
        return "pre_gap"
    if day >= POST_RECOVERY_START:
        return "post_recovery"
    return "excluded"


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


def bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    return df[column].map(bool_value).astype(bool)


def num(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(float("nan"), index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.where(denominator != 0)


def spike_count_from_row(row: pd.Series | dict[str, Any], prefix: str = "Signal") -> int:
    return sum(1 for column in SPIKE_COLUMNS if bool_value(row.get(f"{prefix}_{column}")))


def spike_signature_from_row(row: pd.Series | dict[str, Any], prefix: str = "Signal") -> str:
    mapping = [
        ("CtxRelVolumeSpike_v1", "REL"),
        ("CtxDeltaSpike_v1", "DELTA"),
        ("CtxOISpike_v1", "OI"),
        ("CtxLiqSpike_v1", "LIQ"),
    ]
    parts = [label for column, label in mapping if bool_value(row.get(f"{prefix}_{column}"))]
    return "+".join(parts) if parts else "NONE"


def make_prefixed_features(features: pd.DataFrame, prefix: str, ts_column: str) -> pd.DataFrame:
    selected = features.loc[:, [column for column in FEATURE_COLUMNS if column in features.columns]].copy()
    selected[ts_column] = pd.to_datetime(selected["Timestamp"], utc=True)
    rename_map = {column: f"{prefix}_{column}" for column in selected.columns if column != ts_column}
    return selected.rename(columns=rename_map)


def day_regime(analyzer_dir: Path) -> dict[str, Any]:
    report = read_optional_csv(analyzer_dir / "analyzer_day_regime_report.csv")
    if report.empty:
        return {}
    row = report.iloc[0].to_dict()
    return {
        column: row.get(column)
        for column in [
            "RunDate",
            "EventDensityClass",
            "RangeExpansionClass",
            "FlowStressClass",
            "PhaseHeuristicLabel",
            "SyntheticBarRatio",
        ]
        if column in row
    }


def add_growth_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["CloseReturn_Pct"] = num(df, "CloseReturn_Pct")
    df["MFE_Pct"] = num(df, "MFE_Pct")
    df["MAE_Pct"] = num(df, "MAE_Pct")
    df["PositiveClose"] = df["CloseReturn_Pct"] > 0
    df["GrowthQuality"] = (df["CloseReturn_Pct"] > 0) & (df["MFE_Pct"] > df["MAE_Pct"].abs())
    df["StrongMFE_0p15"] = df["MFE_Pct"] >= 0.15
    df["StrongClose_0p05"] = df["CloseReturn_Pct"] >= 0.05
    return df


def load_reclaim_long_rows(analyzer_dir: Path, day: date) -> pd.DataFrame:
    setups = read_optional_csv(analyzer_dir / "analyzer_setups.csv")
    outcomes = read_optional_csv(analyzer_dir / "analyzer_setup_outcomes.csv")
    features = read_optional_csv(analyzer_dir / "analyzer_features.csv")
    if setups.empty or outcomes.empty or features.empty:
        return pd.DataFrame()

    setups = setups.loc[setups["SetupType"].eq(RECLAIM_SETUP_TYPE)].copy()
    if setups.empty:
        return pd.DataFrame()

    merged = setups.merge(outcomes, on="SetupId", how="inner", suffixes=("", "_outcome"))
    if merged.empty:
        return pd.DataFrame()

    merged["SignalTsParsed"] = pd.to_datetime(merged["SetupBarTs"], utc=True)
    merged["ReferenceEventTsParsed"] = pd.to_datetime(merged["ReferenceEventTs"], utc=True)
    signal_features = make_prefixed_features(features, "Signal", "SignalTsParsed")
    impulse_features = make_prefixed_features(features, "Impulse", "ReferenceEventTsParsed")
    merged = merged.merge(signal_features, on="SignalTsParsed", how="left")
    merged = merged.merge(impulse_features, on="ReferenceEventTsParsed", how="left")

    merged["SourceSurface"] = "RECLAIM_LONG"
    merged["EventId"] = merged["SetupId"]
    merged["Date"] = day.isoformat()
    merged["Period"] = period_for_day(day)
    merged["AnalyzerRunId"] = analyzer_dir.name
    merged["SignalTs"] = merged["SetupBarTs"]
    merged["SignalTsParsed"] = pd.to_datetime(merged["SignalTs"], utc=True)
    merged["SignalHourUTC"] = merged["SignalTsParsed"].dt.hour
    merged["SpikeCount"] = merged.apply(spike_count_from_row, axis=1)
    merged["SpikeSignature"] = merged.apply(spike_signature_from_row, axis=1)

    signal_close = num(merged, "Signal_Close")
    reference_level = num(merged, "ReferenceLevel")
    signal_range = num(merged, "Signal_BarRange")
    impulse_high = num(merged, "Impulse_High")
    impulse_low = num(merged, "Impulse_Low")
    impulse_range = num(merged, "Impulse_BarRange")
    merged["ReclaimDepthUsd"] = signal_close - reference_level
    merged["ReclaimDepthToSetupRange"] = safe_div(merged["ReclaimDepthUsd"], signal_range)
    merged["ReclaimDepthToImpulseRange"] = safe_div(merged["ReclaimDepthUsd"], impulse_range)
    merged["SetupCloseLocationInImpulseRange"] = safe_div(signal_close - impulse_low, impulse_high - impulse_low)

    for key, value in day_regime(analyzer_dir).items():
        merged[key] = value
    return add_growth_targets(merged)


def impulse_up_event_id(day: date, ts: pd.Timestamp) -> str:
    payload = f"IMPULSE_UP_CONTINUATION|{day.isoformat()}|{ts.isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def load_impulse_up_rows(analyzer_dir: Path, day: date) -> pd.DataFrame:
    features = read_optional_csv(analyzer_dir / "analyzer_features.csv")
    if features.empty:
        return pd.DataFrame()

    features = features.copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)
    features = features.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    regime = day_regime(analyzer_dir)

    for idx, row in features.iterrows():
        if not bool_value(row.get("ImpulseDetected_v1")):
            continue
        if str(row.get("ImpulseDirection_v1")) != "IMPULSE_UP":
            continue

        forward = features.iloc[idx + 1 : idx + 1 + OUTCOME_HORIZON_BARS].copy()
        observed = len(forward.index)
        signal_close = pd.to_numeric(row.get("Close"), errors="coerce")
        if pd.isna(signal_close) or float(signal_close) == 0.0 or observed == 0:
            continue

        best_high = float(pd.to_numeric(forward["High"], errors="coerce").max())
        best_low = float(pd.to_numeric(forward["Low"], errors="coerce").min())
        final_close = float(pd.to_numeric(forward["Close"], errors="coerce").iloc[-1])
        close = float(signal_close)
        ts = pd.Timestamp(row["Timestamp"])
        out: dict[str, Any] = {
            "SourceSurface": "IMPULSE_UP_CONTINUATION",
            "EventId": impulse_up_event_id(day, ts),
            "SetupId": "",
            "SetupType": "IMPULSE_UP_CONTINUATION",
            "Direction": "LONG",
            "Date": day.isoformat(),
            "Period": period_for_day(day),
            "AnalyzerRunId": analyzer_dir.name,
            "SignalTs": ts,
            "SignalTsParsed": ts,
            "ReferenceEventTs": ts,
            "ReferenceEventTsParsed": ts,
            "ReferenceEventType": "IMPULSE_UP",
            "ReferenceLevel": close,
            "OutcomeHorizonBars": OUTCOME_HORIZON_BARS,
            "OutcomeBarsObserved": observed,
            "OutcomeStatus": "FULL_HORIZON" if observed == OUTCOME_HORIZON_BARS else "PARTIAL_HORIZON",
            "BestHigh": best_high,
            "BestLow": best_low,
            "FinalClose": final_close,
            "OutcomeEndTs": forward["Timestamp"].iloc[-1],
            "MFE_Pct": ((best_high - close) / close) * 100,
            "MAE_Pct": ((best_low - close) / close) * 100,
            "CloseReturn_Pct": ((final_close - close) / close) * 100,
            "H2_Post3Label_v1": "",
            "H2_Post6Label_v1": "",
            "H2_Post12Label_v1": "",
        }
        for column in FEATURE_COLUMNS:
            if column in row.index:
                out[f"Signal_{column}"] = row[column]
                out[f"Impulse_{column}"] = row[column]
        for key, value in regime.items():
            out[key] = value
        rows.append(out)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["SignalHourUTC"] = pd.to_datetime(df["SignalTs"], utc=True).dt.hour
    df["SpikeCount"] = df.apply(spike_count_from_row, axis=1)
    df["SpikeSignature"] = df.apply(spike_signature_from_row, axis=1)
    df["ReclaimDepthUsd"] = math.nan
    df["ReclaimDepthToSetupRange"] = math.nan
    df["ReclaimDepthToImpulseRange"] = math.nan
    df["SetupCloseLocationInImpulseRange"] = math.nan
    return add_growth_targets(df)


def read_day_rows(repo_root: Path, day: date, coverage_rows: list[dict[str, Any]]) -> pd.DataFrame:
    run_id = f"{day.isoformat()}_to_{day.isoformat()}_run_001"
    analyzer_dir = repo_root / "analyzer_runs" / run_id
    if not analyzer_dir.exists():
        coverage_rows.append({"Date": day.isoformat(), "Status": "missing_analyzer"})
        return pd.DataFrame()
    required = [analyzer_dir / "analyzer_features.csv", analyzer_dir / "analyzer_setups.csv", analyzer_dir / "analyzer_setup_outcomes.csv"]
    if not all(path.exists() for path in required):
        coverage_rows.append({"Date": day.isoformat(), "Status": "missing_required_analyzer_artifact"})
        return pd.DataFrame()

    reclaim = load_reclaim_long_rows(analyzer_dir, day)
    impulse_up = load_impulse_up_rows(analyzer_dir, day)
    frames = [frame for frame in [reclaim, impulse_up] if not frame.empty]
    rows = sum(len(frame.index) for frame in frames)
    coverage_rows.append(
        {
            "Date": day.isoformat(),
            "Status": "loaded",
            "ReclaimLongRows": len(reclaim.index),
            "ImpulseUpRows": len(impulse_up.index),
            "Rows": rows,
        }
    )
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def output_columns(df: pd.DataFrame) -> list[str]:
    base = [
        "SourceSurface",
        "EventId",
        "Date",
        "Period",
        "AnalyzerRunId",
        "SetupId",
        "SetupType",
        "Direction",
        "SignalTs",
        "ReferenceEventTs",
        "ReferenceEventType",
        "ReferenceLevel",
        "SignalHourUTC",
        "SpikeCount",
        "SpikeSignature",
        "OutcomeHorizonBars",
        "OutcomeBarsObserved",
        "OutcomeStatus",
        "MFE_Pct",
        "MAE_Pct",
        "CloseReturn_Pct",
        "BestHigh",
        "BestLow",
        "FinalClose",
        "OutcomeEndTs",
        "PositiveClose",
        "GrowthQuality",
        "StrongMFE_0p15",
        "StrongClose_0p05",
        "H2_Post3Label_v1",
        "H2_Post6Label_v1",
        "H2_Post12Label_v1",
        "LifecycleStatus",
        "InvalidatedAt",
        "ExpiredAt",
        "ReclaimDepthUsd",
        "ReclaimDepthToSetupRange",
        "ReclaimDepthToImpulseRange",
        "SetupCloseLocationInImpulseRange",
        "RunDate",
        "EventDensityClass",
        "RangeExpansionClass",
        "FlowStressClass",
        "PhaseHeuristicLabel",
        "SyntheticBarRatio",
    ]
    prefixed = [
        f"{prefix}_{column}"
        for prefix in ("Signal", "Impulse")
        for column in FEATURE_COLUMNS
        if f"{prefix}_{column}" in df.columns
    ]
    return [column for column in [*base, *prefixed] if column in df.columns]


def metrics_for(scope: str, selector: str, condition_count: int, df: pd.DataFrame, base_pos_rate: float, base_quality_rate: float) -> dict[str, Any]:
    rows = len(df.index)
    pre = df.loc[df["Period"].eq("pre_gap")].copy()
    post = df.loc[df["Period"].eq("post_recovery")].copy()
    day = day_split_metrics(df)
    return {
        "Scope": scope,
        "Selector": selector,
        "Conditions": condition_count,
        "Rows": rows,
        "PositiveCloseRate": rate(df, "PositiveClose"),
        "PositiveCloseLift": rate(df, "PositiveClose") - base_pos_rate if rows else math.nan,
        "GrowthQualityRate": rate(df, "GrowthQuality"),
        "GrowthQualityLift": rate(df, "GrowthQuality") - base_quality_rate if rows else math.nan,
        "StrongMFERate_0p15": rate(df, "StrongMFE_0p15"),
        "StrongCloseRate_0p05": rate(df, "StrongClose_0p05"),
        "MeanCloseReturnPct": float(num(df, "CloseReturn_Pct").mean()) if rows else math.nan,
        "MedianCloseReturnPct": float(num(df, "CloseReturn_Pct").median()) if rows else math.nan,
        "MeanMFEPct": float(num(df, "MFE_Pct").mean()) if rows else math.nan,
        "MedianMFEPct": float(num(df, "MFE_Pct").median()) if rows else math.nan,
        "MeanMAEPct": float(num(df, "MAE_Pct").mean()) if rows else math.nan,
        "MedianMAEPct": float(num(df, "MAE_Pct").median()) if rows else math.nan,
        "SumCloseReturnPct": float(num(df, "CloseReturn_Pct").fillna(0.0).sum()),
        "MaxDrawdownCloseReturnPct": max_drawdown(df, "CloseReturn_Pct"),
        "PreRows": len(pre.index),
        "PrePositiveCloseRate": rate(pre, "PositiveClose"),
        "PreMeanCloseReturnPct": float(num(pre, "CloseReturn_Pct").mean()) if not pre.empty else math.nan,
        "PreSumCloseReturnPct": float(num(pre, "CloseReturn_Pct").fillna(0.0).sum()),
        "PostRows": len(post.index),
        "PostPositiveCloseRate": rate(post, "PositiveClose"),
        "PostMeanCloseReturnPct": float(num(post, "CloseReturn_Pct").mean()) if not post.empty else math.nan,
        "PostSumCloseReturnPct": float(num(post, "CloseReturn_Pct").fillna(0.0).sum()),
        **day,
        "Top1CloseReturnPct": top_n(df, "CloseReturn_Pct", 1),
        "Bottom1CloseReturnPct": bottom_n(df, "CloseReturn_Pct", 1),
    }


def rate(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return math.nan
    return float(df[column].fillna(False).astype(bool).mean())


def max_drawdown(df: pd.DataFrame, column: str) -> float:
    if df.empty:
        return math.nan
    ordered = df.sort_values("SignalTsParsed")
    equity = num(ordered, column).fillna(0.0).cumsum()
    drawdown = equity - equity.cummax()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def top_n(df: pd.DataFrame, column: str, n: int) -> float:
    values = num(df, column).dropna()
    winners = values.loc[values > 0].sort_values(ascending=False).head(n)
    return float(winners.sum()) if not winners.empty else 0.0


def bottom_n(df: pd.DataFrame, column: str, n: int) -> float:
    values = num(df, column).dropna()
    losers = values.loc[values < 0].sort_values(ascending=True).head(n)
    return float(losers.sum()) if not losers.empty else 0.0


def day_split_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "DayCount": 0,
            "PositiveDayCount": 0,
            "NegativeDayCount": 0,
            "FlatDayCount": 0,
            "PreDayCount": 0,
            "PostDayCount": 0,
            "BestDay": "",
            "BestDaySumCloseReturnPct": math.nan,
            "WorstDay": "",
            "WorstDaySumCloseReturnPct": math.nan,
        }
    grouped = df.groupby(["Date", "Period"], dropna=False).agg(SumCloseReturnPct=("CloseReturn_Pct", "sum"), Rows=("EventId", "count")).reset_index()
    best = grouped.loc[grouped["SumCloseReturnPct"].idxmax()]
    worst = grouped.loc[grouped["SumCloseReturnPct"].idxmin()]
    return {
        "DayCount": int(grouped["Date"].nunique()),
        "PositiveDayCount": int((grouped["SumCloseReturnPct"] > 0).sum()),
        "NegativeDayCount": int((grouped["SumCloseReturnPct"] < 0).sum()),
        "FlatDayCount": int((grouped["SumCloseReturnPct"] == 0).sum()),
        "PreDayCount": int(grouped.loc[grouped["Period"].eq("pre_gap"), "Date"].nunique()),
        "PostDayCount": int(grouped.loc[grouped["Period"].eq("post_recovery"), "Date"].nunique()),
        "BestDay": best["Date"],
        "BestDaySumCloseReturnPct": float(best["SumCloseReturnPct"]),
        "WorstDay": worst["Date"],
        "WorstDaySumCloseReturnPct": float(worst["SumCloseReturnPct"]),
    }


def build_predicates() -> list[Predicate]:
    def gt(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) > threshold).fillna(False)

    def ge(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) >= threshold).fillna(False)

    def le(column: str, threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: (num(df, column) <= threshold).fillna(False)

    def eq_str(column: str, value: str) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: df[column].fillna("").astype(str).eq(value) if column in df.columns else pd.Series(False, index=df.index)

    def is_true(column: str) -> Callable[[pd.DataFrame], pd.Series]:
        return lambda df: bool_series(df, column)

    def low_stress(df: pd.DataFrame) -> pd.Series:
        return (
            le("Signal_RelVolume_20", 1.5)(df)
            & le("Signal_DeltaAbsRatio_20", 2.0)(df)
            & le("Signal_OIChangeAbsRatio_20", 5.0)(df)
            & le("SpikeCount", 2)(df)
        )

    def high_stress(df: pd.DataFrame) -> pd.Series:
        return (
            gt("Signal_RelVolume_20", 1.5)(df)
            | gt("Signal_DeltaAbsRatio_20", 2.0)(df)
            | gt("Signal_OIChangeAbsRatio_20", 5.0)(df)
            | ge("SpikeCount", 3)(df)
        ).fillna(False)

    def zero_spike(df: pd.DataFrame) -> pd.Series:
        return num(df, "SpikeCount").fillna(-1).eq(0)

    return [
        Predicate("low_stress", "stress", low_stress),
        Predicate("high_stress", "stress", high_stress),
        Predicate("zero_spike", "spike", zero_spike),
        Predicate("spike_count_ge_2", "spike", ge("SpikeCount", 2)),
        Predicate("ctx_rel_spike", "spike", is_true("Signal_CtxRelVolumeSpike_v1")),
        Predicate("ctx_delta_spike", "spike", is_true("Signal_CtxDeltaSpike_v1")),
        Predicate("ctx_oi_spike", "spike", is_true("Signal_CtxOISpike_v1")),
        Predicate("ctx_liq_spike", "spike", is_true("Signal_CtxLiqSpike_v1")),
        Predicate("rel_volume_le_1p0", "signal_stress", le("Signal_RelVolume_20", 1.0)),
        Predicate("rel_volume_le_1p5", "signal_stress", le("Signal_RelVolume_20", 1.5)),
        Predicate("rel_volume_gt_1p5", "signal_stress", gt("Signal_RelVolume_20", 1.5)),
        Predicate("delta_abs_le_2p0", "signal_stress", le("Signal_DeltaAbsRatio_20", 2.0)),
        Predicate("delta_abs_gt_2p0", "signal_stress", gt("Signal_DeltaAbsRatio_20", 2.0)),
        Predicate("oi_abs_le_5p0", "signal_stress", le("Signal_OIChangeAbsRatio_20", 5.0)),
        Predicate("oi_abs_gt_5p0", "signal_stress", gt("Signal_OIChangeAbsRatio_20", 5.0)),
        Predicate("liq_ratio_eq_0", "signal_stress", le("Signal_LiqTotalRatio_20", 0.0)),
        Predicate("session_asia", "session", eq_str("Signal_session", "ASIA")),
        Predicate("session_eu", "session", eq_str("Signal_session", "EU")),
        Predicate("session_us", "session", eq_str("Signal_session", "US")),
        Predicate("hour_0_7", "session", lambda df: num(df, "SignalHourUTC").between(0, 7, inclusive="both").fillna(False)),
        Predicate("hour_8_15", "session", lambda df: num(df, "SignalHourUTC").between(8, 15, inclusive="both").fillna(False)),
        Predicate("hour_16_23", "session", lambda df: num(df, "SignalHourUTC").between(16, 23, inclusive="both").fillna(False)),
        Predicate("signal_body_gt_0p5", "signal_shape", gt("Signal_BodyToRange", 0.5)),
        Predicate("signal_body_gt_0p75", "signal_shape", gt("Signal_BodyToRange", 0.75)),
        Predicate("signal_close_loc_ge_0p75", "signal_shape", ge("Signal_CloseLocation", 0.75)),
        Predicate("signal_close_loc_ge_0p9", "signal_shape", ge("Signal_CloseLocation", 0.9)),
        Predicate("signal_upper_wick_le_0p25", "signal_shape", le("Signal_UpperWickToRange", 0.25)),
        Predicate("signal_lower_wick_ge_0p25", "signal_shape", ge("Signal_LowerWickToRange", 0.25)),
        Predicate("impulse_body_gt_0p75", "impulse_shape", gt("Impulse_BodyToRange", 0.75)),
        Predicate("impulse_close_loc_ge_0p75", "impulse_shape", ge("Impulse_CloseLocation", 0.75)),
        Predicate("impulse_close_loc_le_0p25", "impulse_shape", le("Impulse_CloseLocation", 0.25)),
        Predicate("impulse_upper_wick_le_0p25", "impulse_shape", le("Impulse_UpperWickToRange", 0.25)),
        Predicate("impulse_range_ratio_gt_1p5", "impulse_stress", gt("Impulse_ImpulseRangeRatio_20_v1", 1.5)),
        Predicate("impulse_range_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseRangeRatio_20_v1", 2.0)),
        Predicate("impulse_volume_ratio_gt_1p5", "impulse_stress", gt("Impulse_ImpulseVolumeRatio_v1", 1.5)),
        Predicate("impulse_delta_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseDeltaRatio_v1", 2.0)),
        Predicate("impulse_oi_ratio_gt_2p0", "impulse_stress", gt("Impulse_ImpulseOIRatio_v1", 2.0)),
        Predicate("impulse_liq_confirmed", "impulse_stress", is_true("Impulse_ImpulseLiqConfirmed_v1")),
        Predicate("impulse_precompression_tag", "compression", is_true("Impulse_PreCompressionTag_v1")),
        Predicate("impulse_precompression_lt_0p8", "compression", le("Impulse_PreCompression_6v20_v1", 0.8)),
        Predicate("impulse_precompression_lt_1p0", "compression", le("Impulse_PreCompression_6v20_v1", 1.0)),
        Predicate("depth_impulse_gt_0p3", "reclaim_depth", gt("ReclaimDepthToImpulseRange", 0.3)),
        Predicate("depth_impulse_gt_0p4", "reclaim_depth", gt("ReclaimDepthToImpulseRange", 0.4)),
        Predicate("depth_impulse_gt_0p5", "reclaim_depth", gt("ReclaimDepthToImpulseRange", 0.5)),
        Predicate("setup_in_impulse_ge_0p75", "reclaim_location", ge("SetupCloseLocationInImpulseRange", 0.75)),
    ]


def scan_scope(df: pd.DataFrame, scope: str, predicates: list[Predicate]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    base_pos = rate(df, "PositiveClose")
    base_quality = rate(df, "GrowthQuality")
    masks = {predicate.name: predicate.mask_fn(df).fillna(False).astype(bool) for predicate in predicates}
    rows: list[dict[str, Any]] = []
    rows.append(metrics_for(scope, "raw_all", 0, df, base_pos, base_quality))
    for condition_count in (1, 2, 3):
        for combo in itertools.combinations(predicates, condition_count):
            selector = " & ".join(predicate.name for predicate in combo)
            mask = pd.Series(True, index=df.index)
            for predicate in combo:
                mask &= masks[predicate.name]
            subset = df.loc[mask].copy()
            if len(subset.index) < MIN_ROWS:
                continue
            if int(subset["Period"].eq("pre_gap").sum()) < MIN_PRE_ROWS:
                continue
            if int(subset["Period"].eq("post_recovery").sum()) < MIN_POST_ROWS:
                continue
            row = metrics_for(scope, selector, condition_count, subset, base_pos, base_quality)
            row["Families"] = "+".join(sorted({predicate.family for predicate in combo}))
            rows.append(row)
    scan = pd.DataFrame(rows)
    return scan.sort_values(
        ["GrowthQualityLift", "MeanCloseReturnPct", "PostMeanCloseReturnPct", "Rows"],
        ascending=[False, False, False, False],
        kind="mergesort",
    ).reset_index(drop=True)


def stable_scan(scan: pd.DataFrame) -> pd.DataFrame:
    if scan.empty:
        return scan.copy()
    stable = scan.loc[
        scan["Selector"].ne("raw_all")
        & (scan["MeanCloseReturnPct"] > 0)
        & (scan["PreMeanCloseReturnPct"] > 0)
        & (scan["PostMeanCloseReturnPct"] > 0)
        & (scan["PositiveCloseLift"] >= 0)
        & (scan["GrowthQualityLift"] >= 0)
        & (scan["PositiveDayCount"] >= scan["NegativeDayCount"])
    ].copy()
    return stable.reset_index(drop=True)


def selector_mask(df: pd.DataFrame, selector: str, predicates_by_name: dict[str, Predicate]) -> pd.Series:
    if selector == "raw_all":
        return pd.Series(True, index=df.index)
    mask = pd.Series(True, index=df.index)
    for name in selector.split(" & "):
        mask &= predicates_by_name[name].mask_fn(df).fillna(False).astype(bool)
    return mask


def choose_candidate_keys(scan: pd.DataFrame, stable: pd.DataFrame) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    preferred = {
        "RECLAIM_LONG": [
            "rel_volume_le_1p0 & impulse_precompression_lt_1p0 & depth_impulse_gt_0p3",
            "rel_volume_le_1p5 & hour_16_23 & depth_impulse_gt_0p4",
            "hour_0_7 & signal_body_gt_0p75 & depth_impulse_gt_0p5",
        ],
        "IMPULSE_UP_CONTINUATION": [
            "delta_abs_le_2p0 & session_us & signal_lower_wick_ge_0p25",
            "ctx_delta_spike & delta_abs_le_2p0 & session_us",
            "session_us & hour_16_23 & signal_lower_wick_ge_0p25",
            "ctx_liq_spike & hour_8_15 & impulse_precompression_lt_0p8",
        ],
    }
    for scope in ["ALL_LONG_GROWTH", "RECLAIM_LONG", "IMPULSE_UP_CONTINUATION"]:
        keys.append((scope, "raw_all"))
        scan_selectors = set(scan.loc[scan["Scope"].eq(scope), "Selector"].astype(str))
        for selector in preferred.get(scope, []):
            if selector in scan_selectors:
                keys.append((scope, selector))
        scope_stable = stable.loc[stable["Scope"].eq(scope)].head(8)
        scope_scan = scan.loc[scan["Scope"].eq(scope) & scan["Selector"].ne("raw_all")].head(5)
        source = scope_stable if not scope_stable.empty else scope_scan
        for selector in source["Selector"].tolist():
            keys.append((scope, selector))
    deduped: list[tuple[str, str]] = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped[:36]


def cluster_first(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes == 0 or df.empty:
        return df.copy()
    ordered = df.sort_values("SignalTsParsed")
    keep_indices: list[Any] = []
    last_kept: pd.Timestamp | None = None
    for idx, row in ordered.iterrows():
        ts = row["SignalTsParsed"]
        if pd.isna(ts):
            continue
        if last_kept is None or (ts - last_kept).total_seconds() >= minutes * 60:
            keep_indices.append(idx)
            last_kept = ts
    return ordered.loc[keep_indices].copy()


def rows_for_scope(features: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "ALL_LONG_GROWTH":
        return features.copy()
    return features.loc[features["SourceSurface"].eq(scope)].copy()


def build_cluster_summary(features: pd.DataFrame, keys: list[tuple[str, str]], predicates_by_name: dict[str, Predicate]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, selector in keys:
        scoped = rows_for_scope(features, scope)
        raw = scoped.loc[selector_mask(scoped, selector, predicates_by_name)].copy()
        base_pos = rate(scoped, "PositiveClose")
        base_quality = rate(scoped, "GrowthQuality")
        for window in [0, 30, 60, 120, 240, 480, 1440]:
            clustered = cluster_first(raw, window)
            row = metrics_for(scope, selector, selector.count("&") + 1 if selector != "raw_all" else 0, clustered, base_pos, base_quality)
            row["ClusterWindowMinutes"] = window
            row["RawRowsBeforeCluster"] = len(raw.index)
            row["DroppedDuplicates"] = len(raw.index) - len(clustered.index)
            rows.append(row)
    return pd.DataFrame(rows)


def build_concentration(features: pd.DataFrame, keys: list[tuple[str, str]], predicates_by_name: dict[str, Predicate]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, selector in keys:
        scoped = rows_for_scope(features, scope)
        subset = scoped.loc[selector_mask(scoped, selector, predicates_by_name)].copy()
        total = float(num(subset, "CloseReturn_Pct").fillna(0.0).sum())
        gross_loss = float(abs(num(subset, "CloseReturn_Pct").loc[num(subset, "CloseReturn_Pct") < 0].sum()))
        for n in (1, 2, 3):
            top = top_n(subset, "CloseReturn_Pct", n)
            bottom = bottom_n(subset, "CloseReturn_Pct", n)
            rows.append(
                {
                    "Scope": scope,
                    "Selector": selector,
                    "TopN": n,
                    "Rows": len(subset.index),
                    "TopNCloseReturnPct": top,
                    "BottomNCloseReturnPct": bottom,
                    "TotalCloseReturnPct": total,
                    "TopReturnShareOfTotal": top / total if total else math.nan,
                    "BottomReturnShareOfGrossLoss": abs(bottom) / gross_loss if gross_loss else math.nan,
                }
            )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 12) -> str:
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
    feature_path: Path,
    scan_path: Path,
    stable_path: Path,
    cluster_path: Path,
    concentration_path: Path,
    coverage_path: Path,
    scan: pd.DataFrame,
    stable: pd.DataFrame,
    cluster: pd.DataFrame,
    concentration: pd.DataFrame,
    coverage: pd.DataFrame,
) -> None:
    baseline = scan.loc[scan["Selector"].eq("raw_all")].copy()
    top_by_scope = stable.groupby("Scope", group_keys=False).head(6) if not stable.empty else pd.DataFrame()
    text = f"""# IMPULSE Long Growth Observable Scan

Date: {datetime.now(timezone.utc).date().isoformat()}

Status: research diagnostic only. No Analyzer grammar change, no Backtester ruleset change, no live implication.

## Window

`{window}`

Clean windows only:

- pre-gap: 2026-03-17..2026-04-22
- post-recovery: 2026-05-07..{window.split('_to_')[-1]}

Broken feed gap is excluded. This scan does not use DeltaScout artifacts as AiTrader evidence.

## Surfaces

- `RECLAIM_LONG`: `IMPULSE_FADE_RECLAIM_LONG_V1` setup rows with Analyzer `MFE_Pct`, `MAE_Pct`, `CloseReturn_Pct`.
- `IMPULSE_UP_CONTINUATION`: raw `IMPULSE_UP` feature rows with a research-only 12-bar forward growth calculation.

Targets are growth outcomes only:

- `PositiveClose`: `CloseReturn_Pct > 0`
- `GrowthQuality`: `CloseReturn_Pct > 0` and `MFE_Pct > abs(MAE_Pct)`
- `StrongMFE_0p15`: `MFE_Pct >= 0.15`
- `StrongClose_0p05`: `CloseReturn_Pct >= 0.05`

H2 labels are diagnostics only and are not entry predicates.

## Outputs

- Feature table: `{feature_path.as_posix()}`
- Proxy scan: `{scan_path.as_posix()}`
- Stable subset: `{stable_path.as_posix()}`
- Cluster summary: `{cluster_path.as_posix()}`
- Return concentration: `{concentration_path.as_posix()}`
- Coverage: `{coverage_path.as_posix()}`

## Baseline By Scope

{markdown_table(baseline, ['Scope', 'Rows', 'PositiveCloseRate', 'GrowthQualityRate', 'StrongMFERate_0p15', 'StrongCloseRate_0p05', 'MeanCloseReturnPct', 'MedianCloseReturnPct', 'MeanMFEPct', 'MeanMAEPct', 'PreRows', 'PostRows', 'PositiveDayCount', 'NegativeDayCount'], max_rows=10)}

## Top Stable Rows

{markdown_table(top_by_scope, ['Scope', 'Selector', 'Rows', 'PositiveCloseRate', 'GrowthQualityRate', 'MeanCloseReturnPct', 'MedianCloseReturnPct', 'MeanMFEPct', 'MeanMAEPct', 'PreRows', 'PostRows', 'PreMeanCloseReturnPct', 'PostMeanCloseReturnPct', 'PositiveDayCount', 'NegativeDayCount'], max_rows=24)}

## Cluster-First Snapshot

{markdown_table(cluster.loc[cluster['Selector'].ne('raw_all')], ['Scope', 'Selector', 'ClusterWindowMinutes', 'Rows', 'DroppedDuplicates', 'PositiveCloseRate', 'GrowthQualityRate', 'MeanCloseReturnPct', 'PreRows', 'PostRows'], max_rows=30)}

## Return Concentration

{markdown_table(concentration.loc[concentration['Selector'].ne('raw_all')], ['Scope', 'Selector', 'TopN', 'Rows', 'TopNCloseReturnPct', 'BottomNCloseReturnPct', 'TotalCloseReturnPct', 'TopReturnShareOfTotal'], max_rows=30)}

## Coverage

{markdown_table(coverage, ['Date', 'Status', 'ReclaimLongRows', 'ImpulseUpRows', 'Rows'], max_rows=60)}

## Read

This is a growth research surface, not a fade/reclaim promotion argument. Treat any top row as a forward-watch candidate only until it survives new clean days with positive post-recovery mean close return and cluster-first robustness.
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
    for day in [*iter_days(PRE_GAP_START, PRE_GAP_END), *iter_days(POST_RECOVERY_START, latest_day)]:
        rows = read_day_rows(repo_root, day, coverage_rows)
        if not rows.empty:
            frames.append(rows)
    if not frames:
        raise RuntimeError("No long growth rows found in clean windows.")

    features = pd.concat(frames, ignore_index=True, sort=False)
    features = features.sort_values(["SignalTsParsed", "SourceSurface", "EventId"], kind="mergesort").reset_index(drop=True)
    coverage = pd.DataFrame(coverage_rows)

    feature_path = results_dir / f"impulse_long_growth_observable_features_{window}.csv"
    scan_path = results_dir / f"impulse_long_growth_proxy_scan_{window}.csv"
    stable_path = results_dir / f"impulse_long_growth_proxy_stable_{window}.csv"
    cluster_path = results_dir / f"impulse_long_growth_cluster_summary_{window}.csv"
    concentration_path = results_dir / f"impulse_long_growth_return_concentration_{window}.csv"
    coverage_path = results_dir / f"impulse_long_growth_coverage_{window}.csv"
    finding_path = findings_dir / f"IMPULSE_LONG_GROWTH_OBSERVABLE_SCAN_{window}.md"

    features.loc[:, output_columns(features)].to_csv(feature_path, index=False)
    coverage.to_csv(coverage_path, index=False)

    predicates = build_predicates()
    predicates_by_name = {predicate.name: predicate for predicate in predicates}
    scans = [
        scan_scope(features, "ALL_LONG_GROWTH", predicates),
        scan_scope(features.loc[features["SourceSurface"].eq("RECLAIM_LONG")].copy(), "RECLAIM_LONG", predicates),
        scan_scope(features.loc[features["SourceSurface"].eq("IMPULSE_UP_CONTINUATION")].copy(), "IMPULSE_UP_CONTINUATION", predicates),
    ]
    scan = pd.concat([item for item in scans if not item.empty], ignore_index=True, sort=False)
    stable = stable_scan(scan)
    keys = choose_candidate_keys(scan, stable)
    cluster = build_cluster_summary(features, keys, predicates_by_name)
    concentration = build_concentration(features, keys, predicates_by_name)

    scan.to_csv(scan_path, index=False)
    stable.to_csv(stable_path, index=False)
    cluster.to_csv(cluster_path, index=False)
    concentration.to_csv(concentration_path, index=False)

    write_finding(
        path=finding_path,
        window=window,
        feature_path=feature_path.relative_to(repo_root),
        scan_path=scan_path.relative_to(repo_root),
        stable_path=stable_path.relative_to(repo_root),
        cluster_path=cluster_path.relative_to(repo_root),
        concentration_path=concentration_path.relative_to(repo_root),
        coverage_path=coverage_path.relative_to(repo_root),
        scan=scan,
        stable=stable,
        cluster=cluster,
        concentration=concentration,
        coverage=coverage,
    )

    print(
        json.dumps(
            {
                "window": window,
                "latest_completed_clean_day": latest_day.isoformat(),
                "rows": int(len(features.index)),
                "reclaim_long_rows": int(features["SourceSurface"].eq("RECLAIM_LONG").sum()),
                "impulse_up_rows": int(features["SourceSurface"].eq("IMPULSE_UP_CONTINUATION").sum()),
                "scan_rows": int(len(scan.index)),
                "stable_rows": int(len(stable.index)),
                "outputs": [
                    str(feature_path.relative_to(repo_root)),
                    str(scan_path.relative_to(repo_root)),
                    str(stable_path.relative_to(repo_root)),
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
