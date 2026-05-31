from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS, build_liquidity_map
from market_monitor.structure import STRUCTURE_LEVEL_COLUMNS, build_structure_levels
from market_monitor.summary import write_market_summary


MARKET_STATE_TIMELINE_COLUMNS = [
    "state_id",
    "start_timestamp",
    "end_timestamp",
    "state",
    "confidence_tier",
    "evidence_json",
    "invalidation_reason",
    "data_quality",
]

VOLUME_DELTA_STATE_COLUMNS = [
    "timestamp",
    "total_qty",
    "buy_qty",
    "sell_qty",
    "delta",
    "delta_pct",
    "volume_zscore",
    "delta_zscore",
    "oi",
    "oi_change",
    "funding_rate",
    "data_quality",
]

ACCUMULATION_ZONES_COLUMNS = [
    "zone_id",
    "created_at",
    "start_timestamp",
    "end_timestamp",
    "price_lower",
    "price_upper",
    "zone_type",
    "confidence_score",
    "confidence_tier",
    "evidence_json",
    "status",
    "data_quality",
]

EVENT_LOG_COLUMNS = [
    "event_id",
    "event_timestamp",
    "event_type",
    "zone_id",
    "side",
    "price_before",
    "event_high",
    "event_low",
    "event_close",
    "excursion_abs",
    "excursion_atr",
    "volume_zscore",
    "delta_zscore",
    "oi_change",
    "reaction_status",
    "evidence_json",
    "data_quality",
]

REQUIRED_CSV_SCHEMAS = {
    "market_state_timeline.csv": MARKET_STATE_TIMELINE_COLUMNS,
    "liquidity_map.csv": LIQUIDITY_MAP_COLUMNS,
    "structure_levels.csv": STRUCTURE_LEVEL_COLUMNS,
    "volume_delta_state.csv": VOLUME_DELTA_STATE_COLUMNS,
    "accumulation_zones.csv": ACCUMULATION_ZONES_COLUMNS,
    "event_log.csv": EVENT_LOG_COLUMNS,
}


def write_outputs(
    feed: pd.DataFrame,
    output_dir: Path,
    *,
    run_timestamp: str,
    input_files: list[str],
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_close = None if feed.empty else float(feed.iloc[-1]["ClosePrice"])

    structure_levels = build_structure_levels(feed)
    liquidity_map = build_liquidity_map(structure_levels, latest_close)
    volume_delta_state = build_volume_delta_state(feed)
    market_state_timeline = build_market_state_timeline(feed)
    accumulation_zones = pd.DataFrame(columns=ACCUMULATION_ZONES_COLUMNS)
    event_log = pd.DataFrame(columns=EVENT_LOG_COLUMNS)

    frames = {
        "market_state_timeline.csv": market_state_timeline,
        "liquidity_map.csv": liquidity_map,
        "structure_levels.csv": structure_levels,
        "volume_delta_state.csv": volume_delta_state,
        "accumulation_zones.csv": accumulation_zones,
        "event_log.csv": event_log,
    }
    for filename, columns in REQUIRED_CSV_SCHEMAS.items():
        frame = frames[filename].reindex(columns=columns)
        frame.to_csv(output_dir / filename, index=False)
        frames[filename] = frame

    write_market_summary(
        output_dir / "market_summary.md",
        feed=feed,
        liquidity_map=liquidity_map,
        structure_levels=structure_levels,
        event_log=event_log,
        run_timestamp=run_timestamp,
        input_files=input_files,
        output_dir=output_dir,
    )

    return frames


def build_volume_delta_state(feed: pd.DataFrame) -> pd.DataFrame:
    if feed.empty:
        return pd.DataFrame(columns=VOLUME_DELTA_STATE_COLUMNS)

    frame = feed.sort_values("Timestamp", kind="mergesort").copy()
    delta = frame["BuyQty"] - frame["SellQty"]
    total_qty = frame["TotalQty"]
    volume_zscore = _rolling_zscore(total_qty)
    delta_zscore = _rolling_zscore(delta)
    result = pd.DataFrame(
        {
            "timestamp": frame["Timestamp"].map(_format_ts),
            "total_qty": total_qty.astype(float),
            "buy_qty": frame["BuyQty"].astype(float),
            "sell_qty": frame["SellQty"].astype(float),
            "delta": delta.astype(float),
            "delta_pct": delta.where(total_qty > 0, 0).div(total_qty.where(total_qty > 0, 1)),
            "volume_zscore": volume_zscore,
            "delta_zscore": delta_zscore,
            "oi": frame["OpenInterest"].astype(float),
            "oi_change": frame["OpenInterest"].diff().fillna(0).astype(float),
            "funding_rate": frame["FundingRate"].astype(float),
            "data_quality": frame["DataQuality"],
        }
    )
    return result[VOLUME_DELTA_STATE_COLUMNS]


def build_market_state_timeline(feed: pd.DataFrame) -> pd.DataFrame:
    if feed.empty:
        return pd.DataFrame(columns=MARKET_STATE_TIMELINE_COLUMNS)

    quality = "RAW" if set(feed["DataQuality"]) == {"RAW"} else "RECOVERED_DEGRADED"
    row = {
        "state_id": "state_000001",
        "start_timestamp": _format_ts(feed["Timestamp"].min()),
        "end_timestamp": _format_ts(feed["Timestamp"].max()),
        "state": "NO_TRADE",
        "confidence_tier": "LOW",
        "evidence_json": '{"reason":"skeleton_no_classifier"}',
        "invalidation_reason": "",
        "data_quality": quality,
    }
    return pd.DataFrame([row], columns=MARKET_STATE_TIMELINE_COLUMNS)


def _rolling_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    rolling_mean = series.rolling(window=window, min_periods=window).mean()
    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=0)
    zscore = (series - rolling_mean) / rolling_std.mask(rolling_std == 0)
    return zscore.fillna(0).astype(float)


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")
