from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.config import BOUNDARY_STATEMENT


def write_market_summary(
    path: Path,
    *,
    feed: pd.DataFrame,
    liquidity_map: pd.DataFrame,
    structure_levels: pd.DataFrame,
    event_log: pd.DataFrame,
    run_timestamp: str,
    input_files: list[str],
    output_dir: Path,
    registry_input=None,
    registry_output=None,
    registry_stats: dict[str, int] | None = None,
    event_stats: dict[str, object] | None = None,
    observation_stats: dict[str, int] | None = None,
) -> None:
    latest_close_value = None if feed.empty else float(feed.iloc[-1]["ClosePrice"])
    latest_close = "" if latest_close_value is None else f"{latest_close_value:.8g}"
    quality_summary = _quality_summary(feed)
    buy_zones = _nearest_active_zones(liquidity_map, "BUY_SIDE", latest_close_value)
    sell_zones = _nearest_active_zones(liquidity_map, "SELL_SIDE", latest_close_value)
    touched_count = _status_count(liquidity_map, "TOUCHED")
    invalidated_count = _status_count(liquidity_map, "INVALIDATED")
    tier_counts = _column_counts(liquidity_map, "confidence_tier")
    precision_counts = _column_counts(liquidity_map, "precision_status")
    status_counts = _column_counts(liquidity_map, "status")
    clustered_count = _clustered_count(liquidity_map)
    top_source_types = _top_source_types(liquidity_map)
    score_stats = _score_instrumentation_stats(liquidity_map)
    registry_stats = registry_stats or {}
    event_stats = event_stats or {
        "total": len(event_log),
        "by_type": "none",
        "approached": 0,
        "touched": 0,
        "crossed_unclassified": 0,
        "merged": 0,
        "expired": 0,
        "unresolved_sweep": 0,
        "unresolved_sweep_by_side": "BUY_SIDE=0, SELL_SIDE=0",
        "unresolved_sweep_by_data_quality": "RAW=0, RECOVERED_DEGRADED=0",
        "crossed_without_sweep_evidence": 0,
    }
    observation_stats = observation_stats or {
        "total": 0,
        "complete": 0,
        "incomplete": 0,
        "window_bars": 30,
    }
    lines = [
        "# Market State Monitor Summary",
        "",
        f"- Run timestamp: {run_timestamp}",
        f"- Input files: {', '.join(input_files)}",
        f"- Input row count: {len(feed)}",
        f"- Output directory: {output_dir}",
        f"- Registry input: {registry_input or 'none'}",
        f"- Registry output: {registry_output or output_dir / 'liquidity_zone_registry.csv'}",
        f"- Carried zones loaded: {registry_stats.get('carried_loaded', 0)}",
        f"- New zones created: {registry_stats.get('new_created', 0)}",
        f"- Zones carried forward: {registry_stats.get('carried_forward', 0)}",
        f"- Zones merged: {registry_stats.get('merged', 0)}",
        f"- Zones expired: {registry_stats.get('expired', 0)}",
        f"- Zones crossed unclassified: {registry_stats.get('crossed_unclassified', 0)}",
        f"- Active registry zones: {registry_stats.get('active_registry', 0)}",
        f"- Latest close price: {latest_close}",
        f"- Data quality summary: {quality_summary}",
        f"- Number of structure levels: {len(structure_levels)}",
        f"- Number of liquidity zones: {len(liquidity_map)}",
        f"- Zones by confidence tier: {tier_counts}",
        f"- Zones by precision status: {precision_counts}",
        f"- Zones by status: {status_counts}",
        f"- Number of merged/clustered zones: {clustered_count}",
        f"- Nearest active buy-side liquidity zones: {buy_zones}",
        f"- Nearest active sell-side liquidity zones: {sell_zones}",
        (
            "- Touched/invalidated liquidity zones: "
            f"touched={touched_count}, invalidated={invalidated_count}"
        ),
        f"- Top source types: {top_source_types}",
        f"- Score instrumentation: {score_stats['enabled']}",
        f"- Zones with score_components_json: {score_stats['with_components']}",
        f"- Zones with H4 source: {score_stats['with_h4']}",
        f"- Zones with session source: {score_stats['with_session']}",
        f"- Zones with equal-level source: {score_stats['with_equal']}",
        f"- Number of events: {len(event_log)}",
        f"- Number of lifecycle events: {event_stats.get('total', 0)}",
        f"- Events by type: {event_stats.get('by_type', 'none')}",
        f"- Approached zones: {event_stats.get('approached', 0)}",
        f"- Touched zones: {event_stats.get('touched', 0)}",
        f"- Crossed unclassified zones: {event_stats.get('crossed_unclassified', 0)}",
        f"- Merged zones with events: {event_stats.get('merged', 0)}",
        f"- Expired zones with events: {event_stats.get('expired', 0)}",
        f"- Unresolved liquidity sweep candidates: {event_stats.get('unresolved_sweep', 0)}",
        (
            "- Unresolved sweep candidates by side: "
            f"{event_stats.get('unresolved_sweep_by_side', 'BUY_SIDE=0, SELL_SIDE=0')}"
        ),
        (
            "- Unresolved sweep candidates by data quality: "
            f"{event_stats.get('unresolved_sweep_by_data_quality', 'RAW=0, RECOVERED_DEGRADED=0')}"
        ),
        (
            "- Crossed zones without sufficient sweep evidence: "
            f"{event_stats.get('crossed_without_sweep_evidence', 0)}"
        ),
        f"- Post-sweep observations: {observation_stats.get('total', 0)}",
        f"- Complete post-sweep observations: {observation_stats.get('complete', 0)}",
        f"- Incomplete post-sweep observations: {observation_stats.get('incomplete', 0)}",
        f"- Observation window bars: {observation_stats.get('window_bars', 30)}",
        "",
        "## Boundary Statement",
        "",
        BOUNDARY_STATEMENT,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _quality_summary(feed: pd.DataFrame) -> str:
    if feed.empty:
        return "none"
    counts = feed["DataQuality"].value_counts().sort_index()
    return ", ".join(f"{name}={count}" for name, count in counts.items())


def _nearest_active_zones(
    liquidity_map: pd.DataFrame, side: str, latest_close: float | None
) -> str:
    if liquidity_map.empty or latest_close is None:
        return "none"
    zones = liquidity_map[
        (liquidity_map["side"] == side) & (liquidity_map["status"] == "ACTIVE")
    ].copy()
    if side == "BUY_SIDE":
        zones = zones[zones["price_lower"] > latest_close]
    elif side == "SELL_SIDE":
        zones = zones[zones["price_upper"] < latest_close]
    if zones.empty:
        return "none"
    zones["abs_distance"] = zones["distance_from_close_pct"].abs()
    zones = zones.sort_values(["abs_distance", "price_mid"], kind="mergesort").head(3)
    return "; ".join(
        f"{row.zone_id}@{row.price_mid:.8g} {row.confidence_tier}"
        for row in zones.itertuples()
    )


def _status_count(liquidity_map: pd.DataFrame, status: str) -> int:
    if liquidity_map.empty:
        return 0
    return int((liquidity_map["status"] == status).sum())


def _column_counts(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "none"
    counts = frame[column].value_counts().sort_index()
    return ", ".join(f"{name}={count}" for name, count in counts.items())


def _clustered_count(liquidity_map: pd.DataFrame) -> int:
    if liquidity_map.empty:
        return 0
    source_counts = liquidity_map["source_level_ids"].fillna("").map(
        lambda value: len([part for part in str(value).split("|") if part])
    )
    explicit_cluster = liquidity_map["zone_type"].fillna("").str.startswith("CLUSTERED_")
    return int(((source_counts > 1) | explicit_cluster).sum())


def _top_source_types(liquidity_map: pd.DataFrame) -> str:
    if liquidity_map.empty:
        return "none"
    counts = liquidity_map["zone_type"].value_counts().sort_values(
        ascending=False, kind="mergesort"
    )
    return ", ".join(f"{name}={count}" for name, count in counts.head(5).items())


def _score_instrumentation_stats(liquidity_map: pd.DataFrame) -> dict[str, object]:
    if liquidity_map.empty or "score_components_json" not in liquidity_map.columns:
        return {
            "enabled": "no",
            "with_components": 0,
            "with_h4": 0,
            "with_session": 0,
            "with_equal": 0,
        }
    return {
        "enabled": "yes",
        "with_components": int(
            liquidity_map["score_components_json"].fillna("").astype(str).str.len().gt(0).sum()
        ),
        "with_h4": _truthy_count(liquidity_map, "has_h4_source"),
        "with_session": _truthy_count(liquidity_map, "has_session_source"),
        "with_equal": _truthy_count(liquidity_map, "has_equal_level_source"),
    }


def _truthy_count(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().isin({"true", "1"}).sum())
