"""Research-only deterministic day regime/phase summary artifact layer."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .context import add_context_metadata

DAY_REGIME_REPORT_COLUMNS = [
    "RunDate",
    "InputStartDate",
    "InputEndDate",
    "BarCount",
    "EventCount",
    "SetupCount",
    "ShortlistCount",
    "FormalizationEligibleCount",
    "AsiaEventCount",
    "EUEventCount",
    "USEventCount",
    "AsiaSetupCount",
    "EUSetupCount",
    "USSetupCount",
    "SweepCount",
    "FailedBreakCount",
    "ReclaimLongCount",
    "ReclaimShortCount",
    "MedianBarRange",
    "MedianVolume",
    "MedianAbsDelta",
    "MedianAbsOIChange",
    "MedianLiqTotal",
    "EventDensityClass",
    "RangeExpansionClass",
    "FlowStressClass",
    "PhaseHeuristicLabel",
    "RelVolumeMedian",
    "AbsorptionScoreMedian",
    "AvgCloseLocation",
    "SyntheticBarRatio",
]

_EVENT_DENSITY_LOW_MAX = 0.02
_EVENT_DENSITY_MEDIUM_MAX = 0.08

_RANGE_COMPRESSED_MAX = 0.0008
_RANGE_EXPANDED_MIN = 0.0025

_FLOW_STRESS_LOW_MAX = 0.8
_FLOW_STRESS_MID_MAX = 1.6


_REQUIRED_FEATURE_COLUMNS = {
    "Timestamp",
    "Close",
    "BarRange",
    "Volume",
    "Delta",
    "OI_Change",
    "LiqTotal",
    "CloseLocation",
    "IsSynthetic",
    "RelVolume_20",
    "AbsorptionScore_v1",
}


def _safe_median(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.median())


def _safe_count_by_session(df: pd.DataFrame, timestamp_col: str) -> dict[str, int]:
    if df.empty:
        return {"ASIA": 0, "EU": 0, "US": 0}

    with_session = add_context_metadata(df[[timestamp_col]].rename(columns={timestamp_col: "Timestamp"}))
    counts = with_session["session"].value_counts().to_dict()
    return {
        "ASIA": int(counts.get("ASIA", 0)),
        "EU": int(counts.get("EU", 0)),
        "US": int(counts.get("US", 0)),
    }


def _label_event_density(bar_count: int, event_count: int, setup_count: int) -> str:
    if bar_count <= 0:
        return "LOW"

    density_score = (event_count + (2 * setup_count)) / bar_count
    if density_score < _EVENT_DENSITY_LOW_MAX:
        return "LOW"
    if density_score < _EVENT_DENSITY_MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


def _label_range_expansion(median_bar_range: float, median_close: float) -> str:
    if median_close <= 0:
        return "NORMAL"

    range_ratio = median_bar_range / median_close
    if range_ratio < _RANGE_COMPRESSED_MAX:
        return "COMPRESSED"
    if range_ratio >= _RANGE_EXPANDED_MIN:
        return "EXPANDED"
    return "NORMAL"


def _label_flow_stress(median_abs_delta: float, median_volume: float, median_abs_oi_change: float, median_liq_total: float) -> str:
    if median_volume <= 0:
        return "LOW_STRESS"

    stress_score = (
        (median_abs_delta / median_volume)
        + 0.5 * (median_abs_oi_change / median_volume)
        + 0.5 * (median_liq_total / median_volume)
    )

    if stress_score < _FLOW_STRESS_LOW_MAX:
        return "LOW_STRESS"
    if stress_score < _FLOW_STRESS_MID_MAX:
        return "MID_STRESS"
    return "HIGH_STRESS"


def _label_phase_heuristic(
    *,
    bar_count: int,
    event_count: int,
    failed_break_count: int,
    reclaim_total: int,
    event_density_class: str,
    range_expansion_class: str,
    flow_stress_class: str,
    avg_close_location: float,
) -> str:
    if bar_count <= 0:
        return "UNCLASSIFIED"

    if event_count == 0 and failed_break_count == 0 and reclaim_total == 0:
        return "UNCLASSIFIED"

    directional_bias = abs(avg_close_location - 0.5)

    if (
        event_density_class == "LOW"
        and range_expansion_class == "COMPRESSED"
        and flow_stress_class == "LOW_STRESS"
    ):
        return "ACCUMULATION"

    if (
        event_density_class == "HIGH"
        and range_expansion_class == "EXPANDED"
        and directional_bias >= 0.12
    ):
        return "MOVEMENT"

    reclaim_share = reclaim_total / failed_break_count if failed_break_count > 0 else 0.0
    if (
        event_density_class in {"MEDIUM", "HIGH"}
        and range_expansion_class in {"NORMAL", "EXPANDED"}
        and flow_stress_class in {"MID_STRESS", "HIGH_STRESS"}
        and reclaim_share >= 0.35
    ):
        return "CORRECTION"

    return "MIXED"


def _required_columns_missing(df: pd.DataFrame, required: Iterable[str]) -> list[str]:
    return sorted(set(required) - set(df.columns))


def build_day_regime_report(
    features_df: pd.DataFrame,
    events_df: pd.DataFrame,
    setups_df: pd.DataFrame,
    shortlist_df: pd.DataFrame,
    research_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build one-row research-only day regime summary from analyzer outputs."""
    missing = _required_columns_missing(features_df, _REQUIRED_FEATURE_COLUMNS)
    if missing:
        raise KeyError(f"Missing required columns for day regime report in features_df: {missing}")

    if features_df.empty:
        return pd.DataFrame(columns=DAY_REGIME_REPORT_COLUMNS)

    features = features_df.copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)

    event_counts_by_session = _safe_count_by_session(events_df, "Timestamp") if "Timestamp" in events_df else {
        "ASIA": 0,
        "EU": 0,
        "US": 0,
    }
    setup_counts_by_session = _safe_count_by_session(setups_df, "SetupBarTs") if "SetupBarTs" in setups_df else {
        "ASIA": 0,
        "EU": 0,
        "US": 0,
    }

    event_types = events_df.get("EventType", pd.Series(dtype=object)).astype(str)
    sweep_count = int(event_types.isin(["SWEEP_UP", "SWEEP_DOWN"]).sum())
    failed_break_count = int(event_types.isin(["FAILED_BREAK_UP", "FAILED_BREAK_DOWN"]).sum())

    setup_types = setups_df.get("SetupType", pd.Series(dtype=object)).astype(str)
    reclaim_long_count = int(setup_types.eq("FAILED_BREAK_RECLAIM_LONG").sum())
    reclaim_short_count = int(setup_types.eq("FAILED_BREAK_RECLAIM_SHORT").sum())

    median_bar_range = _safe_median(features["BarRange"])
    median_close = _safe_median(features["Close"].abs())
    median_volume = _safe_median(features["Volume"])
    median_abs_delta = _safe_median(features["Delta"].abs())
    median_abs_oi_change = _safe_median(features["OI_Change"].abs())
    median_liq_total = _safe_median(features["LiqTotal"])

    event_density_class = _label_event_density(len(features), len(events_df), len(setups_df))
    range_expansion_class = _label_range_expansion(median_bar_range, median_close)
    flow_stress_class = _label_flow_stress(
        median_abs_delta,
        median_volume,
        median_abs_oi_change,
        median_liq_total,
    )

    avg_close_location = float(features["CloseLocation"].mean()) if not features.empty else 0.5
    phase_heuristic = _label_phase_heuristic(
        bar_count=len(features),
        event_count=len(events_df),
        failed_break_count=failed_break_count,
        reclaim_total=reclaim_long_count + reclaim_short_count,
        event_density_class=event_density_class,
        range_expansion_class=range_expansion_class,
        flow_stress_class=flow_stress_class,
        avg_close_location=avg_close_location,
    )

    row = {
        "RunDate": features["Timestamp"].max().date().isoformat(),
        "InputStartDate": features["Timestamp"].min().date().isoformat(),
        "InputEndDate": features["Timestamp"].max().date().isoformat(),
        "BarCount": int(len(features)),
        "EventCount": int(len(events_df)),
        "SetupCount": int(len(setups_df)),
        "ShortlistCount": int(len(shortlist_df)),
        "FormalizationEligibleCount": int(
            research_summary_df.get("FormalizationEligible", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()
        ),
        "AsiaEventCount": event_counts_by_session["ASIA"],
        "EUEventCount": event_counts_by_session["EU"],
        "USEventCount": event_counts_by_session["US"],
        "AsiaSetupCount": setup_counts_by_session["ASIA"],
        "EUSetupCount": setup_counts_by_session["EU"],
        "USSetupCount": setup_counts_by_session["US"],
        "SweepCount": sweep_count,
        "FailedBreakCount": failed_break_count,
        "ReclaimLongCount": reclaim_long_count,
        "ReclaimShortCount": reclaim_short_count,
        "MedianBarRange": median_bar_range,
        "MedianVolume": median_volume,
        "MedianAbsDelta": median_abs_delta,
        "MedianAbsOIChange": median_abs_oi_change,
        "MedianLiqTotal": median_liq_total,
        "EventDensityClass": event_density_class,
        "RangeExpansionClass": range_expansion_class,
        "FlowStressClass": flow_stress_class,
        "PhaseHeuristicLabel": phase_heuristic,
        "RelVolumeMedian": _safe_median(features["RelVolume_20"]),
        "AbsorptionScoreMedian": _safe_median(features["AbsorptionScore_v1"]),
        "AvgCloseLocation": avg_close_location,
        "SyntheticBarRatio": float(features["IsSynthetic"].mean()),
    }

    return pd.DataFrame([row], columns=DAY_REGIME_REPORT_COLUMNS)
