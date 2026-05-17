"""Sprint 06 event-level discovery kill-or-continue test.

This script tests only two discovery families:

- EXHAUSTION_REVERSAL
- VWAP_DEVIATION_REVERSION

It does not run Analyzer v1, Backtester, Executor, live trading, or promotion.
Forward outcomes are labels/ranking fields only and are never used to create
events.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CONTAMINATED_START = pd.Timestamp("2026-04-23 17:05:00", tz="UTC")
CONTAMINATED_END = pd.Timestamp("2026-05-06 22:51:00", tz="UTC")
HORIZONS = (3, 6, 12, 24, 60)
OUTCOME_COST_HARD = 0.00015
OUTCOME_COST_WARN = 0.00020
MIN_USABLE_ROWS = 1000

FAMILY_EXHAUSTION = "EXHAUSTION_REVERSAL"
FAMILY_VWAP = "VWAP_DEVIATION_REVERSION"


FEATURE_COLUMNS = [
    "Timestamp",
    "Date",
    "OpenPrice",
    "HiPrice",
    "LowPrice",
    "ClosePrice",
    "TotalQty",
    "BuyQty",
    "SellQty",
    "DeltaQty",
    "DeltaPct",
    "Session",
    "DayVWAP",
    "VWAPDistancePct",
    "RollingVolume_15m",
    "RollingVolume_60m",
    "VolumeQuantile_60m",
    "RangePct_1m",
    "RangePct_15m",
    "ReturnPct_1m",
    "ReturnPct_5m",
    "ReturnPct_15m",
    "ReturnPct_60m",
    "RealizedVol_15m",
    "RealizedVol_60m",
    "CloseLocationInRange",
    "UpperWickPct",
    "LowerWickPct",
    "TrendSlope_60m",
    "ATRLike_60m",
    "RegimeLabel",
    "DataQualityFlag",
    "DataSource",
    "LineageNote",
]

EVENT_COLUMNS = [
    "discovery_event_id",
    "raw_event_id",
    "family",
    "side",
    "event_time",
    "event_date",
    "event_type",
    "event_version",
    "source_timeframe",
    "cluster_id",
    "cluster_rank",
    "clustered_event",
    "raw_events_in_cluster",
    "event_strength",
    "observable_predicates",
    "session",
    "regime",
    "vwap_distance_bucket",
    "volume_quantile_bucket",
    "rejection_strength_bucket",
    "volume_bucket",
    "trend_slope_bucket",
    "rejection_flag",
    "data_source",
    "lineage_note",
    "no_lookahead_predicates",
]

OUTCOME_COLUMNS = [
    "discovery_event_id",
    "family",
    "side",
    "event_time",
    "horizon_bars",
    "forward_return_3",
    "forward_return_6",
    "forward_return_12",
    "forward_return_24",
    "forward_return_60",
    "outcome_start_ts",
    "outcome_end_ts",
    "forward_return",
    "forward_return_bp",
    "MFE_12",
    "MAE_12",
    "MFE_60",
    "MAE_60",
    "time_to_vwap_touch",
    "reversal_label",
    "vwap_reversion_label",
    "outcome_status",
]

SURFACE_COLUMNS = [
    "surface_id",
    "family",
    "side",
    "horizon",
    "session",
    "regime",
    "vwap_bucket",
    "volume_bucket",
    "rejection_bucket",
    "raw_events",
    "clustered_events",
    "independent_trade_days",
    "events_per_day_max",
    "largest_day_event_share",
    "mean_return",
    "median_return",
    "positive_rate",
    "avg_mfe",
    "avg_mae",
    "mfe_mae_ratio",
    "day_concentration_max_share",
    "session_distribution",
    "gross_edge_bp",
    "net_edge_bp_after_0_00015",
    "net_edge_bp_after_0_00020",
    "verdict",
    "verdict_reason",
]


@dataclass(frozen=True)
class CleanDay:
    date: str
    source: str
    frame: pd.DataFrame
    raw_rows: int
    synthetic_rows: int
    zero_ohlc_rows: int
    volume_sum: float
    min_timestamp: str
    max_timestamp: str
    usable_for_discovery: bool
    reason_if_not_usable: str
    lineage_note: str


def _safe_numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([default] * len(frame.index), index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def _read_feed(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Timestamp" not in frame.columns:
        raise ValueError(f"{path} is missing Timestamp")
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
    for column in [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "BuyQty",
        "SellQty",
        "VWAP",
        "IsSynthetic",
    ]:
        frame[column] = _safe_numeric(frame, column)
    return frame


def recovered_lineage_available(recovered_root: Path, recovered_manifest: Path) -> bool:
    return recovered_root.exists() and recovered_manifest.exists()


def build_clean_days(
    *,
    feed_root: Path,
    recovered_root: Path,
    recovered_manifest: Path,
    use_recovered_gap: bool,
) -> list[CleanDay]:
    if not feed_root.exists():
        raise SystemExit(f"Feed root not found: {feed_root}")
    recovered_ok = use_recovered_gap and recovered_lineage_available(recovered_root, recovered_manifest)
    today_utc = pd.Timestamp.utcnow().date()
    days: list[CleanDay] = []

    for primary_path in sorted(feed_root.glob("*.csv")):
        try:
            day = pd.Timestamp(primary_path.stem).date()
        except ValueError:
            continue
        if day >= today_utc:
            continue

        primary = _read_feed(primary_path)
        in_gap = primary["Timestamp"].between(CONTAMINATED_START, CONTAMINATED_END, inclusive="both")
        parts = [primary.loc[~in_gap].copy()]
        source = "primary"
        lineage_note = "primary_clean_outside_contaminated_window"

        if in_gap.any():
            source = "primary_gap_excluded"
            lineage_note = "contaminated_primary_window_excluded"
            recovered_path = recovered_root / primary_path.name
            if recovered_ok and recovered_path.exists():
                recovered = _read_feed(recovered_path)
                recovered_in_gap = recovered["Timestamp"].between(
                    CONTAMINATED_START, CONTAMINATED_END, inclusive="both"
                )
                parts.append(recovered.loc[recovered_in_gap].copy())
                source = "primary_plus_recovered_gap"
                lineage_note = "primary outside outage; feed_recovered inside outage; degraded OI/funding/liquidations"

        combined = (
            pd.concat(parts, ignore_index=True)
            .drop_duplicates(subset=["Timestamp"], keep="last")
            .sort_values("Timestamp")
            .reset_index(drop=True)
        )
        raw_rows = int(len(combined.index))
        synthetic_rows = int(_safe_numeric(combined, "IsSynthetic").ne(0).sum())
        zero_ohlc = combined[["Open", "High", "Low", "Close"]].le(0).any(axis=1)
        zero_ohlc_rows = int(zero_ohlc.sum())
        clean = combined.loc[_safe_numeric(combined, "IsSynthetic").eq(0) & ~zero_ohlc].copy()
        clean = clean.sort_values("Timestamp").reset_index(drop=True)

        volume_sum = float(_safe_numeric(clean, "Volume").sum())
        valid_ts = combined["Timestamp"].dropna()
        min_ts = "" if valid_ts.empty else valid_ts.min().isoformat()
        max_ts = "" if valid_ts.empty else valid_ts.max().isoformat()

        reasons: list[str] = []
        if raw_rows == 0:
            reasons.append("empty_after_gap_exclusion")
        if len(clean.index) < MIN_USABLE_ROWS:
            reasons.append("clean_rows_below_1000")
        if volume_sum <= 0:
            reasons.append("zero_clean_volume")
        if in_gap.any() and not source == "primary_plus_recovered_gap":
            reasons.append("contaminated_window_without_recovered_lineage")
        usable = not reasons
        days.append(
            CleanDay(
                date=primary_path.stem,
                source=source,
                frame=clean,
                raw_rows=raw_rows,
                synthetic_rows=synthetic_rows,
                zero_ohlc_rows=zero_ohlc_rows,
                volume_sum=volume_sum,
                min_timestamp=min_ts,
                max_timestamp=max_ts,
                usable_for_discovery=usable,
                reason_if_not_usable="PASS" if usable else ";".join(reasons),
                lineage_note=lineage_note,
            )
        )
    return days


def session_name(ts: pd.Timestamp) -> str:
    hour = int(ts.hour)
    if hour < 7:
        return "ASIA"
    if hour < 13:
        return "LONDON"
    if hour < 20:
        return "US"
    return "LATE_US"


def rolling_quantile_last(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    last = values.iloc[-1]
    return float((values <= last).mean())


def rolling_realized_vol(close: pd.Series, window: int) -> pd.Series:
    returns = close.pct_change().fillna(0.0)
    return (returns.rolling(window, min_periods=2).std().fillna(0.0) * math.sqrt(window)).astype(float)


def bucket_vwap(distance: float) -> str:
    abs_distance = abs(distance)
    if abs_distance >= 1.0:
        return "EXTREME_GE_1_0"
    if abs_distance >= 0.6:
        return "HIGH_0_6_1_0"
    if abs_distance >= 0.3:
        return "MID_0_3_0_6"
    return "LOW_LT_0_3"


def bucket_volume(quantile: float) -> str:
    if quantile >= 0.95:
        return "Q95_PLUS"
    if quantile >= 0.90:
        return "Q90_95"
    if quantile >= 0.75:
        return "Q75_90"
    return "BELOW_Q75"


def bucket_rejection(value: float) -> str:
    if value >= 0.45:
        return "STRONG_GE_0_45"
    if value >= 0.25:
        return "MID_0_25_0_45"
    return "LOW_LT_0_25"


def bucket_slope(value: float) -> str:
    if value >= 0.35:
        return "UP_STRONG"
    if value > 0.05:
        return "UP_WEAK"
    if value <= -0.35:
        return "DOWN_STRONG"
    if value < -0.05:
        return "DOWN_WEAK"
    return "FLAT"


def build_features(days: list[CleanDay]) -> pd.DataFrame:
    feature_parts: list[pd.DataFrame] = []
    for day in days:
        if not day.usable_for_discovery:
            continue
        frame = day.frame.copy()
        if frame.empty:
            continue
        frame["Date"] = day.date
        frame["OpenPrice"] = frame["Open"].astype(float)
        frame["HiPrice"] = frame["High"].astype(float)
        frame["LowPrice"] = frame["Low"].astype(float)
        frame["ClosePrice"] = frame["Close"].astype(float)
        frame["TotalQty"] = frame["Volume"].astype(float)
        frame["BuyQty"] = _safe_numeric(frame, "BuyQty")
        frame["SellQty"] = _safe_numeric(frame, "SellQty")
        frame["DeltaQty"] = frame["BuyQty"] - frame["SellQty"]
        frame["DeltaPct"] = frame["DeltaQty"] / frame["TotalQty"].where(frame["TotalQty"] > 0)
        frame["DeltaPct"] = frame["DeltaPct"].fillna(0.0)
        frame["Session"] = frame["Timestamp"].apply(session_name)

        typical_value = (frame["ClosePrice"] * frame["TotalQty"]).cumsum()
        volume_cum = frame["TotalQty"].cumsum()
        frame["DayVWAP"] = typical_value / volume_cum.where(volume_cum > 0)
        frame["DayVWAP"] = frame["DayVWAP"].ffill().fillna(frame["ClosePrice"])
        frame["VWAPDistancePct"] = (frame["ClosePrice"] / frame["DayVWAP"] - 1.0) * 100.0
        frame["RollingVolume_15m"] = frame["TotalQty"].rolling(15, min_periods=1).sum()
        frame["RollingVolume_60m"] = frame["TotalQty"].rolling(60, min_periods=1).sum()
        frame["VolumeQuantile_60m"] = frame["TotalQty"].rolling(60, min_periods=10).apply(rolling_quantile_last)
        frame["VolumeQuantile_60m"] = frame["VolumeQuantile_60m"].fillna(0.0)
        frame["RangePct_1m"] = (frame["HiPrice"] - frame["LowPrice"]) / frame["ClosePrice"] * 100.0
        high_15 = frame["HiPrice"].rolling(15, min_periods=1).max()
        low_15 = frame["LowPrice"].rolling(15, min_periods=1).min()
        frame["RangePct_15m"] = (high_15 - low_15) / frame["ClosePrice"] * 100.0
        for bars in (1, 5, 15, 60):
            frame[f"ReturnPct_{bars}m"] = (frame["ClosePrice"] / frame["ClosePrice"].shift(bars) - 1.0) * 100.0
        frame["RealizedVol_15m"] = rolling_realized_vol(frame["ClosePrice"], 15) * 100.0
        frame["RealizedVol_60m"] = rolling_realized_vol(frame["ClosePrice"], 60) * 100.0
        range_abs = (frame["HiPrice"] - frame["LowPrice"]).where(lambda series: series > 0)
        frame["CloseLocationInRange"] = ((frame["ClosePrice"] - frame["LowPrice"]) / range_abs).fillna(0.5)
        frame["UpperWickPct"] = ((frame["HiPrice"] - frame[["OpenPrice", "ClosePrice"]].max(axis=1)) / range_abs).fillna(0.0)
        frame["LowerWickPct"] = ((frame[["OpenPrice", "ClosePrice"]].min(axis=1) - frame["LowPrice"]) / range_abs).fillna(0.0)
        frame["TrendSlope_60m"] = frame["ReturnPct_60m"].fillna(0.0)
        frame["ATRLike_60m"] = frame["RangePct_1m"].rolling(60, min_periods=10).mean().fillna(0.0)

        expansion = (frame["RangePct_15m"] >= frame["RangePct_15m"].rolling(240, min_periods=60).quantile(0.75)) | (
            frame["RealizedVol_60m"] >= frame["RealizedVol_60m"].rolling(240, min_periods=60).quantile(0.75)
        )
        reversal_candidate = (
            (frame["UpperWickPct"] >= 0.35) & (frame["ReturnPct_15m"] > 0.2)
        ) | ((frame["LowerWickPct"] >= 0.35) & (frame["ReturnPct_15m"] < -0.2))
        frame["RegimeLabel"] = "UNKNOWN"
        frame.loc[frame["TrendSlope_60m"] >= 0.35, "RegimeLabel"] = "TREND_UP"
        frame.loc[frame["TrendSlope_60m"] <= -0.35, "RegimeLabel"] = "TREND_DOWN"
        frame.loc[frame["TrendSlope_60m"].abs() < 0.12, "RegimeLabel"] = "CHOP"
        frame.loc[expansion.fillna(False), "RegimeLabel"] = "EXPANSION"
        frame.loc[reversal_candidate.fillna(False), "RegimeLabel"] = "REVERSAL_CANDIDATE"
        frame["DataQualityFlag"] = "CLEAN"
        frame["DataSource"] = day.source
        frame["LineageNote"] = day.lineage_note
        feature_parts.append(frame[FEATURE_COLUMNS])

    if not feature_parts:
        return pd.DataFrame(columns=FEATURE_COLUMNS)
    features = pd.concat(feature_parts, ignore_index=True)
    return features.replace([math.inf, -math.inf], pd.NA).fillna(0.0)


def event_id(prefix: str, row: pd.Series) -> str:
    raw = f"{prefix}|{row['Timestamp'].isoformat()}|{row.get('side', '')}|{row.get('event_strength', '')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def build_raw_events(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    rows: list[dict[str, Any]] = []
    features = features.copy()
    features["abs_vwap"] = features["VWAPDistancePct"].abs()
    features["abs_delta"] = features["DeltaPct"].abs()

    for _, row in features.iterrows():
        timestamp = row["Timestamp"]
        volume_q = float(row["VolumeQuantile_60m"])
        vwap_distance = float(row["VWAPDistancePct"])
        close_loc = float(row["CloseLocationInRange"])
        upper_wick = float(row["UpperWickPct"])
        lower_wick = float(row["LowerWickPct"])
        ret_15 = float(row["ReturnPct_15m"])
        ret_60 = float(row["ReturnPct_60m"])
        delta_pct = float(row["DeltaPct"])
        abs_vwap = abs(vwap_distance)

        base = {
            "event_date": str(row["Date"]),
            "session": row["Session"],
            "regime": row["RegimeLabel"],
            "data_source": row["DataSource"],
            "lineage_note": row["LineageNote"],
            "source_timeframe": "M1",
            "event_version": "SPRINT06_DISCOVERY_V1",
            "no_lookahead_predicates": True,
        }

        if (
            ret_15 >= 0.35
            and volume_q >= 0.90
            and (close_loc <= 0.72 or upper_wick >= 0.25)
            and delta_pct >= 0.15
            and vwap_distance >= 0.25
        ):
            strength = abs_vwap + volume_q + upper_wick + abs(ret_15)
            predicate = {
                "prev_impulse": "up",
                "return_15m": round(ret_15, 6),
                "return_60m": round(ret_60, 6),
                "volume_quantile_60m": round(volume_q, 6),
                "close_location": round(close_loc, 6),
                "upper_wick_pct": round(upper_wick, 6),
                "delta_pct": round(delta_pct, 6),
                "vwap_distance_pct": round(vwap_distance, 6),
            }
            raw_id = event_id("EXH_SHORT", pd.Series({"Timestamp": timestamp, "side": "SHORT", "event_strength": strength}))
            rows.append(
                {
                    **base,
                    "raw_event_id": raw_id,
                    "discovery_event_id": raw_id,
                    "family": FAMILY_EXHAUSTION,
                    "side": "SHORT",
                    "event_time": timestamp.isoformat(),
                    "event_type": "CLIMAX_REJECTION_SHORT",
                    "event_strength": round(float(strength), 6),
                    "observable_predicates": json.dumps(predicate, sort_keys=True),
                    "vwap_distance_bucket": bucket_vwap(vwap_distance),
                    "volume_quantile_bucket": bucket_volume(volume_q),
                    "rejection_strength_bucket": bucket_rejection(upper_wick),
                    "volume_bucket": bucket_volume(volume_q),
                    "trend_slope_bucket": bucket_slope(ret_60),
                    "rejection_flag": upper_wick >= 0.25,
                }
            )

        if (
            ret_15 <= -0.35
            and volume_q >= 0.90
            and (close_loc >= 0.28 or lower_wick >= 0.25)
            and delta_pct <= -0.15
            and vwap_distance <= -0.25
        ):
            strength = abs_vwap + volume_q + lower_wick + abs(ret_15)
            predicate = {
                "prev_impulse": "down",
                "return_15m": round(ret_15, 6),
                "return_60m": round(ret_60, 6),
                "volume_quantile_60m": round(volume_q, 6),
                "close_location": round(close_loc, 6),
                "lower_wick_pct": round(lower_wick, 6),
                "delta_pct": round(delta_pct, 6),
                "vwap_distance_pct": round(vwap_distance, 6),
            }
            raw_id = event_id("EXH_LONG", pd.Series({"Timestamp": timestamp, "side": "LONG", "event_strength": strength}))
            rows.append(
                {
                    **base,
                    "raw_event_id": raw_id,
                    "discovery_event_id": raw_id,
                    "family": FAMILY_EXHAUSTION,
                    "side": "LONG",
                    "event_time": timestamp.isoformat(),
                    "event_type": "CLIMAX_REJECTION_LONG",
                    "event_strength": round(float(strength), 6),
                    "observable_predicates": json.dumps(predicate, sort_keys=True),
                    "vwap_distance_bucket": bucket_vwap(vwap_distance),
                    "volume_quantile_bucket": bucket_volume(volume_q),
                    "rejection_strength_bucket": bucket_rejection(lower_wick),
                    "volume_bucket": bucket_volume(volume_q),
                    "trend_slope_bucket": bucket_slope(ret_60),
                    "rejection_flag": lower_wick >= 0.25,
                }
            )

        # VWAP deviation is intentionally wider than exhaustion: it tests pure
        # deviation/reversion with rejection or stall as observable context.
        stall_or_reject_short = upper_wick >= 0.20 or close_loc <= 0.65 or abs(float(row["ReturnPct_5m"])) <= 0.08
        if vwap_distance >= 0.45 and abs_vwap >= 0.45 and stall_or_reject_short:
            strength = abs_vwap + max(0.0, upper_wick) + volume_q
            predicate = {
                "vwap_distance_pct": round(vwap_distance, 6),
                "volume_quantile_60m": round(volume_q, 6),
                "upper_wick_pct": round(upper_wick, 6),
                "close_location": round(close_loc, 6),
                "trend_slope_60m": round(ret_60, 6),
                "stall_or_reject": bool(stall_or_reject_short),
            }
            raw_id = event_id("VWAP_SHORT", pd.Series({"Timestamp": timestamp, "side": "SHORT", "event_strength": strength}))
            rows.append(
                {
                    **base,
                    "raw_event_id": raw_id,
                    "discovery_event_id": raw_id,
                    "family": FAMILY_VWAP,
                    "side": "SHORT",
                    "event_time": timestamp.isoformat(),
                    "event_type": "ABOVE_VWAP_REVERSION_SHORT",
                    "event_strength": round(float(strength), 6),
                    "observable_predicates": json.dumps(predicate, sort_keys=True),
                    "vwap_distance_bucket": bucket_vwap(vwap_distance),
                    "volume_quantile_bucket": bucket_volume(volume_q),
                    "rejection_strength_bucket": bucket_rejection(upper_wick),
                    "volume_bucket": bucket_volume(volume_q),
                    "trend_slope_bucket": bucket_slope(ret_60),
                    "rejection_flag": bool(upper_wick >= 0.20),
                }
            )

        stall_or_reject_long = lower_wick >= 0.20 or close_loc >= 0.35 or abs(float(row["ReturnPct_5m"])) <= 0.08
        if vwap_distance <= -0.45 and abs_vwap >= 0.45 and stall_or_reject_long:
            strength = abs_vwap + max(0.0, lower_wick) + volume_q
            predicate = {
                "vwap_distance_pct": round(vwap_distance, 6),
                "volume_quantile_60m": round(volume_q, 6),
                "lower_wick_pct": round(lower_wick, 6),
                "close_location": round(close_loc, 6),
                "trend_slope_60m": round(ret_60, 6),
                "stall_or_reject": bool(stall_or_reject_long),
            }
            raw_id = event_id("VWAP_LONG", pd.Series({"Timestamp": timestamp, "side": "LONG", "event_strength": strength}))
            rows.append(
                {
                    **base,
                    "raw_event_id": raw_id,
                    "discovery_event_id": raw_id,
                    "family": FAMILY_VWAP,
                    "side": "LONG",
                    "event_time": timestamp.isoformat(),
                    "event_type": "BELOW_VWAP_REVERSION_LONG",
                    "event_strength": round(float(strength), 6),
                    "observable_predicates": json.dumps(predicate, sort_keys=True),
                    "vwap_distance_bucket": bucket_vwap(vwap_distance),
                    "volume_quantile_bucket": bucket_volume(volume_q),
                    "rejection_strength_bucket": bucket_rejection(lower_wick),
                    "volume_bucket": bucket_volume(volume_q),
                    "trend_slope_bucket": bucket_slope(ret_60),
                    "rejection_flag": bool(lower_wick >= 0.20),
                }
            )

    raw_events = pd.DataFrame(rows)
    if raw_events.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    return raw_events.sort_values(["family", "side", "event_time"]).reset_index(drop=True)


def cluster_events(raw_events: pd.DataFrame) -> pd.DataFrame:
    if raw_events.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    clustered: list[pd.DataFrame] = []
    cluster_counter = 0
    for (_, _), group in raw_events.groupby(["family", "side"], sort=False):
        group = group.copy()
        group["event_ts"] = pd.to_datetime(group["event_time"], utc=True)
        current_members: list[int] = []
        current_start: pd.Timestamp | None = None
        for idx, row in group.iterrows():
            ts = row["event_ts"]
            if current_start is None or ts > current_start + pd.Timedelta(minutes=15):
                if current_members:
                    clustered.append(mark_cluster(group.loc[current_members].copy(), cluster_counter))
                    cluster_counter += 1
                current_members = [idx]
                current_start = ts
            else:
                current_members.append(idx)
        if current_members:
            clustered.append(mark_cluster(group.loc[current_members].copy(), cluster_counter))
            cluster_counter += 1
    out = pd.concat(clustered, ignore_index=True)
    out["event_ts"] = pd.to_datetime(out["event_time"], utc=True)
    out = out.sort_values(["event_ts", "family", "side"]).reset_index(drop=True)
    return out[EVENT_COLUMNS]


def mark_cluster(group: pd.DataFrame, cluster_counter: int) -> pd.DataFrame:
    group = group.sort_values(["event_strength", "event_time"], ascending=[False, True]).copy()
    group["cluster_rank"] = range(1, len(group.index) + 1)
    group["clustered_event"] = group["cluster_rank"].eq(1)
    group["raw_events_in_cluster"] = int(len(group.index))
    group["cluster_id"] = f"SPRINT06_CLUSTER_{cluster_counter:06d}"
    winner_id = str(group.iloc[0]["raw_event_id"])
    group.loc[group["clustered_event"], "discovery_event_id"] = winner_id
    group.loc[~group["clustered_event"], "discovery_event_id"] = group.loc[~group["clustered_event"], "raw_event_id"]
    return group.sort_values("event_time")


def side_return(side: str, entry: float, future: float) -> float:
    if entry <= 0 or future <= 0:
        return 0.0
    raw = future / entry - 1.0
    return raw if side == "LONG" else -raw


def side_excursions(side: str, entry: float, future_high: pd.Series, future_low: pd.Series) -> tuple[float, float]:
    if entry <= 0 or future_high.empty or future_low.empty:
        return 0.0, 0.0
    if side == "LONG":
        mfe = float(future_high.max() / entry - 1.0)
        mae = float(future_low.min() / entry - 1.0)
    else:
        mfe = float(entry / future_low.min() - 1.0) if future_low.min() > 0 else 0.0
        mae = float(entry / future_high.max() - 1.0)
    return mfe, mae


def time_to_vwap_touch(side: str, entry_idx: int, features: pd.DataFrame, max_horizon: int = 60) -> int:
    subset = features.iloc[entry_idx + 1 : entry_idx + max_horizon + 1]
    if subset.empty:
        return -1
    if side == "SHORT":
        mask = subset["ClosePrice"] <= subset["DayVWAP"]
    else:
        mask = subset["ClosePrice"] >= subset["DayVWAP"]
    if not mask.any():
        return -1
    return int(mask.idxmax() - entry_idx)


def build_outcomes(features: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    clustered = events[events["clustered_event"].astype(bool)].copy()
    if clustered.empty:
        return pd.DataFrame(columns=OUTCOME_COLUMNS)
    features = features.sort_values("Timestamp").reset_index(drop=True).copy()
    features["TimestampISO"] = features["Timestamp"].apply(lambda ts: ts.isoformat())
    event_to_idx = {ts: idx for idx, ts in enumerate(features["TimestampISO"])}
    rows: list[dict[str, Any]] = []
    for _, event in clustered.iterrows():
        event_time = str(event["event_time"])
        if event_time not in event_to_idx:
            continue
        idx = event_to_idx[event_time]
        entry = float(features.loc[idx, "ClosePrice"])
        side = str(event["side"])
        vwap_touch = time_to_vwap_touch(side, idx, features, 60)
        forward_by_horizon: dict[int, float] = {}
        end_ts_by_horizon: dict[int, pd.Timestamp] = {}
        for horizon in HORIZONS:
            end_idx = idx + horizon
            if end_idx >= len(features.index):
                continue
            expected_end = features.loc[idx, "Timestamp"] + pd.Timedelta(minutes=horizon)
            actual_end = features.loc[end_idx, "Timestamp"]
            if actual_end != expected_end:
                continue
            future_close = float(features.loc[end_idx, "ClosePrice"])
            forward_by_horizon[horizon] = side_return(side, entry, future_close)
            end_ts_by_horizon[horizon] = actual_end
        for horizon in HORIZONS:
            if horizon not in forward_by_horizon:
                continue
            end_idx = idx + horizon
            actual_end = end_ts_by_horizon[horizon]
            future = features.iloc[idx + 1 : end_idx + 1]
            forward_return = forward_by_horizon[horizon]
            mfe_12, mae_12 = side_excursions(
                side,
                entry,
                features.iloc[idx + 1 : min(idx + 12, len(features.index) - 1) + 1]["HiPrice"],
                features.iloc[idx + 1 : min(idx + 12, len(features.index) - 1) + 1]["LowPrice"],
            )
            mfe_60, mae_60 = side_excursions(
                side,
                entry,
                features.iloc[idx + 1 : min(idx + 60, len(features.index) - 1) + 1]["HiPrice"],
                features.iloc[idx + 1 : min(idx + 60, len(features.index) - 1) + 1]["LowPrice"],
            )
            label = "REVERSAL_POSITIVE" if forward_return > 0 else "REVERSAL_NEGATIVE"
            rows.append(
                {
                    "discovery_event_id": event["discovery_event_id"],
                    "family": event["family"],
                    "side": side,
                    "event_time": event_time,
                    "horizon_bars": horizon,
                    "forward_return_3": round(float(forward_by_horizon.get(3, 0.0)), 10),
                    "forward_return_6": round(float(forward_by_horizon.get(6, 0.0)), 10),
                    "forward_return_12": round(float(forward_by_horizon.get(12, 0.0)), 10),
                    "forward_return_24": round(float(forward_by_horizon.get(24, 0.0)), 10),
                    "forward_return_60": round(float(forward_by_horizon.get(60, 0.0)), 10),
                    "outcome_start_ts": features.loc[idx + 1, "Timestamp"].isoformat() if not future.empty else "",
                    "outcome_end_ts": actual_end.isoformat(),
                    "forward_return": round(float(forward_return), 10),
                    "forward_return_bp": round(float(forward_return * 10000.0), 6),
                    "MFE_12": round(float(mfe_12), 10),
                    "MAE_12": round(float(mae_12), 10),
                    "MFE_60": round(float(mfe_60), 10),
                    "MAE_60": round(float(mae_60), 10),
                    "time_to_vwap_touch": vwap_touch,
                    "reversal_label": label if event["family"] == FAMILY_EXHAUSTION else "",
                    "vwap_reversion_label": "VWAP_TOUCH" if vwap_touch != -1 else "NO_VWAP_TOUCH",
                    "outcome_status": "FULL_HORIZON",
                }
            )
    return pd.DataFrame(rows, columns=OUTCOME_COLUMNS)


def verdict_for_surface(row: dict[str, Any]) -> tuple[str, str]:
    reasons: list[str] = []
    clustered_events = int(row["clustered_events"])
    independent_days = int(row["independent_trade_days"])
    median_return = float(row["median_return"])
    positive_rate = float(row["positive_rate"])
    net_15 = float(row["net_edge_bp_after_0_00015"])
    concentration = float(row["day_concentration_max_share"])
    mfe_mae_ratio = float(row["mfe_mae_ratio"])

    replay_pass = (
        clustered_events >= 100
        and independent_days >= 25
        and concentration <= 0.15
        and median_return > 0
        and positive_rate >= 0.55
        and net_15 > 0
        and 0.2 <= mfe_mae_ratio <= 10.0
    )
    if replay_pass:
        return "NEEDS_REPLAY_SPEC", "passes discovery replay-spec gates; still not promotion"

    review_pass = (
        clustered_events >= 50
        and independent_days >= 15
        and median_return > 0
        and positive_rate >= 0.53
    )
    if review_pass:
        if net_15 <= 0:
            reasons.append("cost_0_00015_not_positive")
        if concentration > 0.15:
            reasons.append("day_concentration_above_0_15")
        return "DISCOVERY_REVIEW", ";".join(reasons) if reasons else "gross edge present but below replay-spec gate"

    if clustered_events < 50:
        reasons.append("sample_below_50")
    if independent_days < 15:
        reasons.append("independent_days_below_15")
    if median_return <= 0:
        reasons.append("median_return_non_positive")
    if positive_rate < 0.53:
        reasons.append("positive_rate_below_0_53")
    if net_15 <= 0:
        reasons.append("cost_0_00015_kills_edge")
    if concentration > 0.15:
        reasons.append("day_concentration_above_0_15")
    return "REJECT_DISCOVERY_SURFACE", ";".join(reasons)


def build_surface_summary(events: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    clustered_events = events[events["clustered_event"].astype(bool)].copy()
    if clustered_events.empty or outcomes.empty:
        return pd.DataFrame(columns=SURFACE_COLUMNS)

    merged = outcomes.merge(
        clustered_events[
            [
                "discovery_event_id",
                "session",
                "regime",
                "vwap_distance_bucket",
                "volume_bucket",
                "rejection_strength_bucket",
            ]
        ],
        on="discovery_event_id",
        how="left",
    )
    raw_counts = events.groupby(["family", "side"]).size().to_dict()
    rows: list[dict[str, Any]] = []
    grouping = [
        "family",
        "side",
        "horizon_bars",
        "session",
        "regime",
        "vwap_distance_bucket",
        "volume_bucket",
        "rejection_strength_bucket",
    ]
    for keys, group in merged.groupby(grouping, dropna=False):
        (
            family,
            side,
            horizon,
            session,
            regime,
            vwap_bucket,
            volume_bucket,
            rejection_bucket,
        ) = keys
        event_dates = pd.to_datetime(group["event_time"], utc=True, format="ISO8601").dt.strftime("%Y-%m-%d")
        day_counts = event_dates.value_counts()
        clustered_count = int(group["discovery_event_id"].nunique())
        independent_days = int(day_counts.count())
        events_per_day_max = int(day_counts.max()) if not day_counts.empty else 0
        concentration = float(events_per_day_max / clustered_count) if clustered_count else 1.0
        returns = pd.to_numeric(group["forward_return"], errors="coerce").fillna(0.0)
        mfe = pd.to_numeric(group["MFE_60" if int(horizon) == 60 else "MFE_12"], errors="coerce").fillna(0.0)
        mae = pd.to_numeric(group["MAE_60" if int(horizon) == 60 else "MAE_12"], errors="coerce").fillna(0.0)
        avg_mfe = float(mfe.mean()) if len(mfe.index) else 0.0
        avg_mae_abs = abs(float(mae.mean())) if len(mae.index) else 0.0
        mfe_mae_ratio = avg_mfe / avg_mae_abs if avg_mae_abs > 0 else 999.0
        mean_return = float(returns.mean())
        median_return = float(returns.median())
        gross_edge_bp = mean_return * 10000.0
        row = {
            "surface_id": "|".join(map(str, keys)),
            "family": family,
            "side": side,
            "horizon": int(horizon),
            "session": session,
            "regime": regime,
            "vwap_bucket": vwap_bucket,
            "volume_bucket": volume_bucket,
            "rejection_bucket": rejection_bucket,
            "raw_events": int(raw_counts.get((family, side), 0)),
            "clustered_events": clustered_count,
            "independent_trade_days": independent_days,
            "events_per_day_max": events_per_day_max,
            "largest_day_event_share": round(concentration, 6),
            "mean_return": round(mean_return, 10),
            "median_return": round(median_return, 10),
            "positive_rate": round(float((returns > 0).mean()), 6),
            "avg_mfe": round(avg_mfe, 10),
            "avg_mae": round(float(mae.mean()) if len(mae.index) else 0.0, 10),
            "mfe_mae_ratio": round(float(mfe_mae_ratio), 6),
            "day_concentration_max_share": round(concentration, 6),
            "session_distribution": json.dumps(group["session"].value_counts().to_dict(), sort_keys=True),
            "gross_edge_bp": round(gross_edge_bp, 6),
            "net_edge_bp_after_0_00015": round(gross_edge_bp - OUTCOME_COST_HARD * 10000.0, 6),
            "net_edge_bp_after_0_00020": round(gross_edge_bp - OUTCOME_COST_WARN * 10000.0, 6),
        }
        row["verdict"], row["verdict_reason"] = verdict_for_surface(row)
        rows.append(row)
    return pd.DataFrame(rows, columns=SURFACE_COLUMNS).sort_values(
        ["verdict", "net_edge_bp_after_0_00015"], ascending=[True, False]
    )


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame, columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(path, index=False)
        return
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns or (list(rows[0]) if rows else []))
        writer.writeheader()
        writer.writerows(rows)


def write_data_quality(days: list[CleanDay], csv_path: Path, md_path: Path) -> None:
    rows = [
        {
            "date": day.date,
            "source": day.source,
            "rows": day.raw_rows,
            "synthetic_rows": day.synthetic_rows,
            "zero_ohlc_rows": day.zero_ohlc_rows,
            "volume_sum": round(day.volume_sum, 6),
            "min_timestamp": day.min_timestamp,
            "max_timestamp": day.max_timestamp,
            "usable_for_discovery": day.usable_for_discovery,
            "reason_if_not_usable": day.reason_if_not_usable,
        }
        for day in days
    ]
    write_csv(csv_path, rows)
    usable = [row for row in rows if row["usable_for_discovery"]]
    lines = [
        "# Sprint 06 Data Quality Report",
        "",
        f"Rows audited: {len(rows)} days",
        f"Usable for discovery: {len(usable)} days",
        "",
        "Rules: primary contaminated window is excluded; recovered feed is used inside the outage only with lineage; synthetic and zero-OHLC rows are excluded from discovery features/events.",
        "",
        "| date | source | rows | synthetic_rows | zero_ohlc_rows | volume_sum | usable | reason |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['date']} | {row['source']} | {row['rows']} | {row['synthetic_rows']} | {row['zero_ohlc_rows']} | {row['volume_sum']} | {row['usable_for_discovery']} | {row['reason_if_not_usable']} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_report(
    *,
    report_path: Path,
    no_edge_path: Path,
    replay_path: Path,
    days: list[CleanDay],
    features: pd.DataFrame,
    events: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    clustered = events[events["clustered_event"].astype(bool)].copy() if not events.empty else events
    verdict_counts = summary["verdict"].value_counts().to_dict() if not summary.empty else {}
    needs = summary[summary["verdict"].eq("NEEDS_REPLAY_SPEC")].copy() if not summary.empty else summary
    review = summary[summary["verdict"].eq("DISCOVERY_REVIEW")].copy() if not summary.empty else summary
    top_gross = summary.sort_values("gross_edge_bp", ascending=False).head(10) if not summary.empty else summary
    top_net = summary.sort_values("net_edge_bp_after_0_00015", ascending=False).head(10) if not summary.empty else summary
    usable_days = [day for day in days if day.usable_for_discovery]
    family_counts = clustered["family"].value_counts().to_dict() if not clustered.empty else {}
    managerial_verdict = "CONTINUE_WITH_REPLAY_SPEC" if not needs.empty else "CONTINUE_WITH_MORE_DATA_ONLY"
    if needs.empty and review.empty:
        managerial_verdict = "CHANGE_UNIVERSE_OR_DATA"

    def markdown_table(frame: pd.DataFrame, cols: list[str]) -> list[str]:
        if frame.empty:
            return ["None."]
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for _, row in frame.iterrows():
            out.append("| " + " | ".join(str(row[col]) for col in cols) + " |")
        return out

    lines = [
        "# Sprint 06 Event Discovery Report",
        "",
        "## 1. Executive Verdict",
        "",
        f"Managerial verdict: `{managerial_verdict}`.",
        "",
        "Sprint 06 tested only `EXHAUSTION_REVERSAL` and `VWAP_DEVIATION_REVERSION`. It did not test Momentum Continuation and did not rerun Analyzer v1 broad failed-break/reclaim.",
        "",
        "No `PROMOTE` was created. This is discovery only.",
        "",
        "## Managerial Answer",
        "",
        f"- Replay-worthy surfaces: {len(needs.index)}.",
        f"- Discovery-review surfaces: {len(review.index)}.",
        f"- BTC-only research should {'continue into replay-spec drafting for the listed surfaces' if not needs.empty else 'not move to replay yet; collect more data or broaden market/data if review surfaces do not mature'}.",
        "- Market/universe/data: current BTC-only feed shows behavior surfaces, but replay-spec work is justified only for `NEEDS_REPLAY_SPEC`; otherwise broaden data/universe before spending more effort.",
        "- Analyzer v1 should remain baseline/control only.",
        "",
        "## 2. Data Used",
        "",
        f"- Clean usable days: {len(usable_days)}.",
        f"- Discovery feature rows: {len(features.index)}.",
        f"- Sources: {json.dumps(pd.Series([day.source for day in usable_days]).value_counts().to_dict(), sort_keys=True)}.",
        "",
        "## 3. Data Excluded",
        "",
        "- Primary contaminated window: `2026-04-23 17:05:00` -> `2026-05-06 22:51:00` UTC.",
        "- Synthetic rows.",
        "- Zero/nonpositive OHLC rows.",
        "- Partial current UTC day.",
        "- Events without enough future bars for the requested horizon.",
        "",
        "## 4. Families Tested",
        "",
        f"- `{FAMILY_EXHAUSTION}` clustered events: {family_counts.get(FAMILY_EXHAUSTION, 0)}.",
        f"- `{FAMILY_VWAP}` clustered events: {family_counts.get(FAMILY_VWAP, 0)}.",
        "",
        "## 5. Top Surfaces By Gross Edge",
        "",
        *markdown_table(
            top_gross,
            [
                "family",
                "side",
                "horizon",
                "session",
                "regime",
                "clustered_events",
                "independent_trade_days",
                "gross_edge_bp",
                "verdict",
            ],
        ),
        "",
        "## 6. Top Surfaces By Net Edge After 0.00015",
        "",
        *markdown_table(
            top_net,
            [
                "family",
                "side",
                "horizon",
                "session",
                "regime",
                "clustered_events",
                "independent_trade_days",
                "net_edge_bp_after_0_00015",
                "verdict",
            ],
        ),
        "",
        "## 7. Surfaces Rejected And Why",
        "",
        *markdown_table(
            summary[summary["verdict"].eq("REJECT_DISCOVERY_SURFACE")].head(20) if not summary.empty else summary,
            ["family", "side", "horizon", "session", "regime", "clustered_events", "verdict_reason"],
        ),
        "",
        "## 8. Surfaces Needing Review",
        "",
        *markdown_table(
            review.head(20),
            [
                "family",
                "side",
                "horizon",
                "session",
                "regime",
                "clustered_events",
                "independent_trade_days",
                "net_edge_bp_after_0_00015",
                "verdict_reason",
            ],
        ),
        "",
        "## 9. Surfaces Needing Replay Spec",
        "",
        *markdown_table(
            needs,
            [
                "family",
                "side",
                "horizon",
                "session",
                "regime",
                "clustered_events",
                "independent_trade_days",
                "net_edge_bp_after_0_00015",
                "verdict_reason",
            ],
        ),
        "",
        "## 10. Research Perspective",
        "",
        "The project still has research perspective only if discovery surfaces survive replay-spec formalization and later Backtester/holdout gates. Discovery is not strategy validation.",
        "",
        "## 11. BTC-Only Current Feed Edge",
        "",
        "BTC-only feed has visible descriptive event surfaces. Confirmed edge remains unproven until a replayable spec passes deterministic replay, cost, same-bar, concentration, and holdout gates.",
        "",
        "## 12. Next Action",
        "",
        "If `NEEDS_REPLAY_SPEC` surfaces exist, draft a formal replay spec without tuning predicates. If none exist, do not force replay; gather more data or change universe/data before more BTC-only rule work.",
        "",
        "## Boundary Confirmation",
        "",
        "- Analyzer v1 remains baseline/control.",
        "- Sprint 06 did not change Analyzer v1 contract.",
        "- Sprint 06 did not change Backtester.",
        "- Sprint 06 did not change CTX holdout.",
        "- Sprint 06 did not touch Executor/live.",
        "",
        "## Verdict Counts",
        "",
        json.dumps(verdict_counts, sort_keys=True),
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    if needs.empty:
        no_edge_lines = [
            "# Sprint 06 No Edge Found Report",
            "",
            "No surface met `NEEDS_REPLAY_SPEC` gates in Sprint 06.",
            "",
            f"Verdict counts: `{json.dumps(verdict_counts, sort_keys=True)}`",
            "",
            "This does not prove no BTC edge exists. It means the two tested discovery families did not produce a replay-worthy surface under the current gates.",
        ]
        no_edge_path.write_text("\n".join(no_edge_lines), encoding="utf-8")
        if replay_path.exists():
            replay_path.unlink()
    else:
        replay_lines = [
            "# Sprint 06 Replay Spec Candidates",
            "",
            "These are not strategies and not promotions. Each surface needs a formal ruleset spec, deterministic mapper, Backtester replay, cost stress, same-bar review, and true holdout.",
            "",
            *markdown_table(
                needs,
                [
                    "family",
                    "side",
                    "horizon",
                    "session",
                    "regime",
                    "vwap_bucket",
                    "volume_bucket",
                    "rejection_bucket",
                    "clustered_events",
                    "net_edge_bp_after_0_00015",
                ],
            ),
            "",
        ]
        replay_path.write_text("\n".join(replay_lines), encoding="utf-8")
        if no_edge_path.exists():
            no_edge_path.unlink()


def run(args: argparse.Namespace) -> None:
    output_root = Path(args.output_root)
    canonical_root = Path(args.canonical_root)
    days = build_clean_days(
        feed_root=Path(args.feed_root),
        recovered_root=Path(args.recovered_root),
        recovered_manifest=Path(args.recovered_manifest),
        use_recovered_gap=not args.no_recovered_gap,
    )
    write_data_quality(
        days,
        output_root / "sprint_06_data_quality_report.csv",
        output_root / "sprint_06_data_quality_report.md",
    )
    features = build_features(days)
    raw_events = build_raw_events(features)
    events = cluster_events(raw_events)
    outcomes = build_outcomes(features, events)
    summary = build_surface_summary(events, outcomes)

    write_csv(output_root / "sprint_06_discovery_features.csv", features[FEATURE_COLUMNS])
    write_csv(output_root / "sprint_06_discovery_events.csv", events[EVENT_COLUMNS])
    write_csv(output_root / "sprint_06_discovery_outcomes.csv", outcomes[OUTCOME_COLUMNS])
    write_csv(output_root / "sprint_06_discovery_surface_summary.csv", summary[SURFACE_COLUMNS])
    verdicts = summary[
        [
            "surface_id",
            "family",
            "side",
            "horizon",
            "clustered_events",
            "independent_trade_days",
            "net_edge_bp_after_0_00015",
            "verdict",
            "verdict_reason",
        ]
    ].copy() if not summary.empty else pd.DataFrame(
        columns=[
            "surface_id",
            "family",
            "side",
            "horizon",
            "clustered_events",
            "independent_trade_days",
            "net_edge_bp_after_0_00015",
            "verdict",
            "verdict_reason",
        ]
    )
    write_csv(output_root / "sprint_06_discovery_verdicts.csv", verdicts)
    write_report(
        report_path=canonical_root / "SPRINT_06_EVENT_DISCOVERY_REPORT.md",
        no_edge_path=canonical_root / "SPRINT_06_NO_EDGE_FOUND_REPORT.md",
        replay_path=canonical_root / "SPRINT_06_REPLAY_SPEC_CANDIDATES.md",
        days=days,
        features=features,
        events=events,
        summary=summary,
    )

    clustered_events = events[events["clustered_event"].astype(bool)] if not events.empty else events
    print(f"usable_days={sum(day.usable_for_discovery for day in days)}")
    print(f"feature_rows={len(features.index)}")
    print(f"raw_events={len(raw_events.index)}")
    print(f"clustered_events={len(clustered_events.index)}")
    print(f"verdicts={summary['verdict'].value_counts().to_dict() if not summary.empty else {}}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 06 event discovery kill-or-continue.")
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--recovered-root", default="feed_recovered")
    parser.add_argument("--recovered-manifest", default="research/canonical/FEED_RECOVERED_MANIFEST.csv")
    parser.add_argument("--output-root", default="research/results")
    parser.add_argument("--canonical-root", default="research/canonical")
    parser.add_argument("--no-recovered-gap", action="store_true")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
