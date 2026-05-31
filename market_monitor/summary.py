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
) -> None:
    latest_close_value = None if feed.empty else float(feed.iloc[-1]["ClosePrice"])
    latest_close = "" if latest_close_value is None else f"{latest_close_value:.8g}"
    quality_summary = _quality_summary(feed)
    buy_zones = _nearest_active_zones(liquidity_map, "BUY_SIDE", latest_close_value)
    sell_zones = _nearest_active_zones(liquidity_map, "SELL_SIDE", latest_close_value)
    touched_count = _status_count(liquidity_map, "TOUCHED")
    invalidated_count = _status_count(liquidity_map, "INVALIDATED")
    lines = [
        "# Market State Monitor Summary",
        "",
        f"- Run timestamp: {run_timestamp}",
        f"- Input files: {', '.join(input_files)}",
        f"- Input row count: {len(feed)}",
        f"- Output directory: {output_dir}",
        f"- Latest close price: {latest_close}",
        f"- Data quality summary: {quality_summary}",
        f"- Nearest active buy-side liquidity zones: {buy_zones}",
        f"- Nearest active sell-side liquidity zones: {sell_zones}",
        (
            "- Touched/invalidated liquidity zones: "
            f"touched={touched_count}, invalidated={invalidated_count}"
        ),
        f"- Number of structure levels: {len(structure_levels)}",
        f"- Number of liquidity zones: {len(liquidity_map)}",
        f"- Number of events: {len(event_log)}",
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
