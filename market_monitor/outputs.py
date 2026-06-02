from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.events import (
    EVENT_LOG_COLUMNS,
    MARKET_MOVE_GROUP_COLUMNS,
    build_event_log,
    build_market_move_groups,
    event_stats,
)
from market_monitor.label_taxonomy import (
    SWEEP_LABEL_SUMMARY_COLUMNS,
    SWEEP_LABEL_TAXONOMY_COLUMNS,
    build_sweep_label_frames,
    label_stats,
)
from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS, build_liquidity_map
from market_monitor.pattern_structures import (
    PATTERN_STRUCTURES_COLUMNS,
    build_pattern_structures,
)
from market_monitor.post_sweep_observation import (
    POST_SWEEP_OBSERVATION_COLUMNS,
    build_post_sweep_observations,
    observation_stats,
)
from market_monitor.structure import STRUCTURE_LEVEL_COLUMNS, build_structure_levels
from market_monitor.summary import write_market_summary
from market_monitor.zone_registry import (
    REGISTRY_COLUMNS,
    build_zone_registry,
    forward_liquidity_from_registry,
    load_registry,
    write_registry,
)


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

REQUIRED_CSV_SCHEMAS = {
    "market_state_timeline.csv": MARKET_STATE_TIMELINE_COLUMNS,
    "liquidity_map.csv": LIQUIDITY_MAP_COLUMNS,
    "structure_levels.csv": STRUCTURE_LEVEL_COLUMNS,
    "volume_delta_state.csv": VOLUME_DELTA_STATE_COLUMNS,
    "accumulation_zones.csv": ACCUMULATION_ZONES_COLUMNS,
    "event_log.csv": EVENT_LOG_COLUMNS,
    "pattern_structures.csv": PATTERN_STRUCTURES_COLUMNS,
    "market_move_groups.csv": MARKET_MOVE_GROUP_COLUMNS,
    "post_sweep_observation.csv": POST_SWEEP_OBSERVATION_COLUMNS,
    "sweep_label_taxonomy.csv": SWEEP_LABEL_TAXONOMY_COLUMNS,
    "sweep_label_summary.csv": SWEEP_LABEL_SUMMARY_COLUMNS,
    "liquidity_zone_registry.csv": REGISTRY_COLUMNS,
}


def write_outputs(
    feed: pd.DataFrame,
    output_dir: Path,
    *,
    run_timestamp: str,
    input_files: list[str],
    registry_in_path: Path | None = None,
    registry_out_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_close = None if feed.empty else float(feed.iloc[-1]["ClosePrice"])
    registry_out_path = registry_out_path or output_dir / "liquidity_zone_registry.csv"

    structure_levels = build_structure_levels(feed)
    liquidity_map = build_liquidity_map(structure_levels, latest_close)
    registry_in = load_registry(registry_in_path)
    volume_delta_state = build_volume_delta_state(feed)
    liquidity_zone_registry, registry_stats = build_zone_registry(
        liquidity_map=liquidity_map,
        feed=feed,
        registry_in=registry_in,
    )
    pattern_structures = build_pattern_structures(
        structure_levels=structure_levels,
        liquidity_zone_registry=liquidity_zone_registry,
    )
    forward_liquidity_map = forward_liquidity_from_registry(liquidity_zone_registry, latest_close)
    event_log = build_event_log(
        registry=liquidity_zone_registry,
        feed=feed,
        volume_delta_state=volume_delta_state,
        previous_registry=registry_in,
    )
    market_move_groups = build_market_move_groups(event_log)
    post_sweep_observation = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=volume_delta_state,
    )
    sweep_label_taxonomy, sweep_label_summary = build_sweep_label_frames(
        observations=post_sweep_observation,
        market_move_groups=market_move_groups,
    )
    market_state_timeline = build_market_state_timeline(feed)
    accumulation_zones = pd.DataFrame(columns=ACCUMULATION_ZONES_COLUMNS)

    frames = {
        "market_state_timeline.csv": market_state_timeline,
        "liquidity_map.csv": forward_liquidity_map,
        "structure_levels.csv": structure_levels,
        "volume_delta_state.csv": volume_delta_state,
        "accumulation_zones.csv": accumulation_zones,
        "event_log.csv": event_log,
        "pattern_structures.csv": pattern_structures,
        "market_move_groups.csv": market_move_groups,
        "post_sweep_observation.csv": post_sweep_observation,
        "sweep_label_taxonomy.csv": sweep_label_taxonomy,
        "sweep_label_summary.csv": sweep_label_summary,
        "liquidity_zone_registry.csv": liquidity_zone_registry,
    }
    for filename, columns in REQUIRED_CSV_SCHEMAS.items():
        frame = frames[filename].reindex(columns=columns)
        output_path = registry_out_path if filename == "liquidity_zone_registry.csv" else output_dir / filename
        frame.to_csv(output_path, index=False)
        frames[filename] = frame
    if registry_out_path != output_dir / "liquidity_zone_registry.csv":
        write_registry(liquidity_zone_registry, output_dir / "liquidity_zone_registry.csv")

    write_market_summary(
        output_dir / "market_summary.md",
        feed=feed,
        liquidity_map=forward_liquidity_map,
        structure_levels=structure_levels,
        event_log=event_log,
        run_timestamp=run_timestamp,
        input_files=input_files,
        output_dir=output_dir,
        registry_input=registry_in_path,
        registry_output=registry_out_path,
        registry_stats=registry_stats,
        event_stats=event_stats(event_log),
        observation_stats=observation_stats(post_sweep_observation),
        label_stats=label_stats(sweep_label_taxonomy),
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
