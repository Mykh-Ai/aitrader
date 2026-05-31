from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.liquidity_zones import LIQUIDITY_MAP_COLUMNS
from market_monitor.score_instrumentation import (
    SCORE_INSTRUMENTATION_COLUMNS,
    score_instrumentation_fields,
)


REGISTRY_COLUMNS = [
    "zone_id",
    "first_seen_at",
    "last_seen_at",
    "last_updated_at",
    "side",
    "zone_type",
    "price_lower",
    "price_upper",
    "price_mid",
    "source_level_ids",
    "source_timeframes",
    "status",
    "confidence_score",
    "confidence_tier",
    "age_bars",
    "age_days",
    "touch_count",
    "cross_count",
    "active_days",
    "last_touch_at",
    "last_cross_at",
    "merged_into_zone_id",
    "data_quality",
    "invalidation_reason",
    *SCORE_INSTRUMENTATION_COLUMNS,
]

CARRY_FORWARD_STATUSES = {
    "ACTIVE",
    "APPROACHED",
    "TOUCHED",
    "CROSSED_UNCLASSIFIED",
}
INACTIVE_STATUSES = {"INVALIDATED", "EXPIRED", "MERGED"}
MAX_ZONE_AGE_DAYS = 7
MAX_ZONE_AGE_REASON = "MAX_ZONE_AGE_DAYS_EXCEEDED"


def load_registry(path: str | Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry input not found: {registry_path}")
    registry = pd.read_csv(registry_path, dtype=str)
    return _normalize_registry(registry)


def build_zone_registry(
    *,
    liquidity_map: pd.DataFrame,
    feed: pd.DataFrame,
    registry_in: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    previous = _normalize_registry(registry_in)
    current_zones = _current_zones_to_registry(liquidity_map, previous)

    historical = previous[~previous["status"].isin(CARRY_FORWARD_STATUSES)].copy()
    carry = previous[previous["status"].isin(CARRY_FORWARD_STATUSES)].copy()
    candidates = _concat_registry_frames([carry, current_zones])

    active_rows, merged_rows = _merge_registry_candidates(candidates)
    active_rows = _update_lifecycle(active_rows, feed)
    active_rows = _apply_expiry(active_rows)

    registry_out = _concat_registry_frames([historical, merged_rows, active_rows])
    registry_out = _normalize_registry(registry_out)
    registry_out = registry_out.sort_values(
        ["first_seen_at", "zone_id", "status"], kind="mergesort"
    ).reset_index(drop=True)

    stats = {
        "carried_loaded": len(carry),
        "new_created": len(current_zones),
        "carried_forward": int(registry_out["status"].isin(CARRY_FORWARD_STATUSES).sum()),
        "merged": int((registry_out["status"] == "MERGED").sum()),
        "expired": int((registry_out["status"] == "EXPIRED").sum()),
        "crossed_unclassified": int(
            (registry_out["status"] == "CROSSED_UNCLASSIFIED").sum()
        ),
        "active_registry": int((registry_out["status"] == "ACTIVE").sum()),
    }
    return registry_out, stats


def write_registry(registry: pd.DataFrame, path: str | Path) -> None:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_registry(registry).to_csv(registry_path, index=False)


def forward_liquidity_from_registry(
    registry: pd.DataFrame, latest_close: float | None
) -> pd.DataFrame:
    registry = _normalize_registry(registry)
    active = registry[registry["status"] == "ACTIVE"].copy()
    if latest_close is not None:
        close = float(latest_close)
        active = active[
            ((active["side"] == "BUY_SIDE") & (active["price_lower"].astype(float) > close))
            | ((active["side"] == "SELL_SIDE") & (active["price_upper"].astype(float) < close))
        ]
    rows = []
    for _, row in active.iterrows():
        rows.append(
            {
                "zone_id": row["zone_id"],
                "created_at": row["first_seen_at"],
                "last_updated_at": row["last_updated_at"],
                "side": row["side"],
                "zone_type": row["zone_type"],
                "price_lower": float(row["price_lower"]),
                "price_upper": float(row["price_upper"]),
                "price_mid": float(row["price_mid"]),
                "source_level_ids": row["source_level_ids"],
                "source_timeframes": row["source_timeframes"],
                "status": row["status"],
                "confidence_score": int(float(row["confidence_score"])),
                "confidence_tier": row["confidence_tier"],
                "touch_count": int(float(row["touch_count"])),
                "sweep_count": 0,
                "distance_from_close_pct": _distance_from_close(
                    float(row["price_mid"]), latest_close
                ),
                "data_quality": row["data_quality"],
                "invalidation_reason": row["invalidation_reason"],
                **_instrumentation_from_row(row),
            }
        )
    return pd.DataFrame(rows, columns=LIQUIDITY_MAP_COLUMNS)


def _current_zones_to_registry(
    liquidity_map: pd.DataFrame, previous: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    next_id = _next_zone_index(previous)
    for _, zone in liquidity_map.iterrows():
        zone_id = f"zone_{next_id:06d}"
        next_id += 1
        created = str(zone["created_at"])
        rows.append(
            {
                "zone_id": zone_id,
                "first_seen_at": created,
                "last_seen_at": created,
                "last_updated_at": created,
                "side": zone["side"],
                "zone_type": zone["zone_type"],
                "price_lower": float(zone["price_lower"]),
                "price_upper": float(zone["price_upper"]),
                "price_mid": float(zone["price_mid"]),
                "source_level_ids": zone["source_level_ids"],
                "source_timeframes": zone["source_timeframes"],
                "status": "ACTIVE",
                "confidence_score": int(zone["confidence_score"]),
                "confidence_tier": zone["confidence_tier"],
                "age_bars": 0,
                "age_days": 0,
                "touch_count": 0,
                "cross_count": 0,
                "active_days": 1,
                "last_touch_at": "",
                "last_cross_at": "",
                "merged_into_zone_id": "",
                "data_quality": zone["data_quality"],
                "invalidation_reason": "",
                **_instrumentation_from_row(zone),
            }
        )
    return _normalize_registry(pd.DataFrame(rows, columns=REGISTRY_COLUMNS))


def _merge_registry_candidates(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = _normalize_registry(candidates)
    if candidates.empty:
        return candidates, pd.DataFrame(columns=REGISTRY_COLUMNS)
    active_rows: list[dict[str, object]] = []
    merged_rows: list[dict[str, object]] = []

    for side in ["BUY_SIDE", "SELL_SIDE"]:
        side_rows = candidates[candidates["side"] == side].copy()
        side_rows = side_rows.sort_values(
            ["price_lower", "first_seen_at", "zone_id"], kind="mergesort"
        )
        cluster: list[dict[str, object]] = []
        for row in side_rows.to_dict("records"):
            if not cluster:
                cluster = [row]
                continue
            tolerance = _merge_tolerance(cluster + [row])
            current_upper = max(float(item["price_upper"]) for item in cluster)
            if float(row["price_lower"]) <= current_upper + tolerance:
                cluster.append(row)
            else:
                active, merged = _collapse_registry_cluster(cluster)
                active_rows.append(active)
                merged_rows.extend(merged)
                cluster = [row]
        if cluster:
            active, merged = _collapse_registry_cluster(cluster)
            active_rows.append(active)
            merged_rows.extend(merged)
    return (
        _normalize_registry(pd.DataFrame(active_rows, columns=REGISTRY_COLUMNS)),
        _normalize_registry(pd.DataFrame(merged_rows, columns=REGISTRY_COLUMNS)),
    )


def _collapse_registry_cluster(
    cluster: list[dict[str, object]]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    if len(cluster) == 1:
        row = cluster[0].copy()
        row["merged_into_zone_id"] = ""
        return row, []

    target = _merge_target(cluster)
    lower = min(float(row["price_lower"]) for row in cluster)
    upper = max(float(row["price_upper"]) for row in cluster)
    source_level_ids = _pipe_union(row["source_level_ids"] for row in cluster)
    source_timeframes = _pipe_union(row["source_timeframes"] for row in cluster)
    source_zone_types = sorted({str(row["zone_type"]) for row in cluster})
    confidence_components = _merged_confidence_components(
        cluster, source_timeframes, source_zone_types
    )
    confidence_score = int(confidence_components["final_confidence_score"])
    confidence_tier = _confidence_tier(confidence_score)
    instrumentation = score_instrumentation_fields(
        source_level_ids=source_level_ids,
        source_timeframes=source_timeframes,
        zone_type=_registry_merged_zone_type(str(target["side"]), source_zone_types),
        price_lower=lower,
        price_upper=upper,
        price_mid=(lower + upper) / 2,
        confidence_score=confidence_score,
        confidence_tier=confidence_tier,
        score_components=confidence_components,
    )

    active = target.copy()
    active.update(
        {
            "first_seen_at": min(str(row["first_seen_at"]) for row in cluster),
            "last_seen_at": max(str(row["last_seen_at"]) for row in cluster),
            "last_updated_at": max(str(row["last_updated_at"]) for row in cluster),
            "price_lower": lower,
            "price_upper": upper,
            "price_mid": (lower + upper) / 2,
            "source_level_ids": source_level_ids,
            "source_timeframes": source_timeframes,
            "zone_type": _registry_merged_zone_type(str(target["side"]), source_zone_types),
            "confidence_score": confidence_score,
            "confidence_tier": confidence_tier,
            "touch_count": sum(int(float(row["touch_count"])) for row in cluster),
            "cross_count": sum(int(float(row["cross_count"])) for row in cluster),
            "active_days": max(int(float(row["active_days"])) for row in cluster),
            "data_quality": _quality_values(row["data_quality"] for row in cluster),
            "merged_into_zone_id": "",
            "invalidation_reason": "",
            **instrumentation,
        }
    )

    merged: list[dict[str, object]] = []
    for row in cluster:
        if row["zone_id"] == target["zone_id"]:
            continue
        merged_row = row.copy()
        merged_row["status"] = "MERGED"
        merged_row["merged_into_zone_id"] = target["zone_id"]
        merged_row["invalidation_reason"] = ""
        merged.append(merged_row)
    return active, merged


def _merge_target(cluster: list[dict[str, object]]) -> dict[str, object]:
    return sorted(cluster, key=lambda row: (str(row["first_seen_at"]), str(row["zone_id"])))[0]


def _update_lifecycle(registry: pd.DataFrame, feed: pd.DataFrame) -> pd.DataFrame:
    registry = _normalize_registry(registry)
    if registry.empty or feed.empty:
        return registry
    frame = feed.sort_values("Timestamp", kind="mergesort")
    run_end = _format_ts(frame["Timestamp"].max())
    updated = []
    for row in registry.to_dict("records"):
        row = row.copy()
        row_first_seen = _format_ts(row["first_seen_at"])
        effective_seen = max(run_end, row_first_seen)
        status, touch_at, cross_at = _path_status(row, frame)
        if touch_at and not row.get("last_touch_at"):
            row["last_touch_at"] = touch_at
        if cross_at:
            if not row.get("last_cross_at") or row["last_cross_at"] != cross_at:
                row["cross_count"] = int(float(row["cross_count"])) + 1
            row["last_cross_at"] = cross_at
        elif touch_at:
            row["touch_count"] = int(float(row["touch_count"])) + 1
            row["last_touch_at"] = touch_at
        row["status"] = status
        row["last_seen_at"] = effective_seen
        row["last_updated_at"] = effective_seen
        row["age_bars"] = _age_bars(row["first_seen_at"], frame)
        row["age_days"] = _age_days(row["first_seen_at"], effective_seen)
        if status in CARRY_FORWARD_STATUSES:
            row["active_days"] = max(int(float(row["active_days"])), int(row["age_days"]) + 1)
        updated.append(row)
    return _normalize_registry(pd.DataFrame(updated, columns=REGISTRY_COLUMNS))


def _path_status(row: dict[str, object], feed: pd.DataFrame) -> tuple[str, str, str]:
    lower = float(row["price_lower"])
    upper = float(row["price_upper"])
    after_first_seen = feed[feed["Timestamp"] >= pd.Timestamp(row["first_seen_at"])]
    if after_first_seen.empty:
        return str(row.get("status", "ACTIVE") or "ACTIVE"), "", ""
    if row["side"] == "BUY_SIDE":
        cross = after_first_seen[after_first_seen["HiPrice"] > upper]
        touch = after_first_seen[
            (after_first_seen["HiPrice"] >= lower) & (after_first_seen["LowPrice"] <= upper)
        ]
    else:
        cross = after_first_seen[after_first_seen["LowPrice"] < lower]
        touch = after_first_seen[
            (after_first_seen["LowPrice"] <= upper) & (after_first_seen["HiPrice"] >= lower)
        ]
    touch_at = "" if touch.empty else _format_ts(touch.iloc[0]["Timestamp"])
    cross_at = "" if cross.empty else _format_ts(cross.iloc[0]["Timestamp"])
    if cross_at:
        return "CROSSED_UNCLASSIFIED", touch_at or cross_at, cross_at
    if touch_at:
        return "TOUCHED", touch_at, ""
    return "ACTIVE", "", ""


def _apply_expiry(registry: pd.DataFrame) -> pd.DataFrame:
    registry = _normalize_registry(registry)
    rows = []
    for row in registry.to_dict("records"):
        if (
            row["status"] in CARRY_FORWARD_STATUSES
            and int(float(row["age_days"])) > MAX_ZONE_AGE_DAYS
            and not _expiry_exempt(row)
        ):
            row = row.copy()
            row["status"] = "EXPIRED"
            row["invalidation_reason"] = MAX_ZONE_AGE_REASON
        rows.append(row)
    return _normalize_registry(pd.DataFrame(rows, columns=REGISTRY_COLUMNS))


def _expiry_exempt(row: dict[str, object]) -> bool:
    zone_type = str(row["zone_type"])
    source_timeframes = set(str(row["source_timeframes"]).split("|"))
    confidence_score = int(float(row["confidence_score"]))
    if row["confidence_tier"] == "HIGH" and "H4" in source_timeframes:
        return True
    if "PDH" in zone_type or "PDL" in zone_type:
        return True
    if "CLUSTERED" in zone_type and confidence_score >= 70:
        return True
    return False


def _normalize_registry(registry: pd.DataFrame | None) -> pd.DataFrame:
    if registry is None or registry.empty:
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    frame = registry.copy()
    for column in REGISTRY_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[REGISTRY_COLUMNS]
    for column in [
        "price_lower",
        "price_upper",
        "price_mid",
        "confidence_score",
        "age_bars",
        "age_days",
        "touch_count",
        "cross_count",
        "active_days",
        "source_level_count",
        "cluster_member_count",
        "zone_width",
        "zone_width_pct",
    ]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    text_columns = [column for column in REGISTRY_COLUMNS if column not in frame.select_dtypes("number").columns]
    for column in text_columns:
        frame[column] = frame[column].fillna("").astype(str)
    return frame[REGISTRY_COLUMNS]


def _concat_registry_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    populated = [frame for frame in frames if frame is not None and not frame.empty]
    if not populated:
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    return pd.concat(populated, ignore_index=True)


def _next_zone_index(registry: pd.DataFrame) -> int:
    max_index = 0
    for zone_id in registry.get("zone_id", []):
        try:
            max_index = max(max_index, int(str(zone_id).split("_")[-1]))
        except ValueError:
            continue
    return max_index + 1


def _merge_tolerance(rows: list[dict[str, object]]) -> float:
    mids = [float(row["price_mid"]) for row in rows]
    reference = sum(mids) / len(mids) if mids else 0
    return max(10.0, reference * 0.0005)


def _registry_merged_zone_type(side: str, source_zone_types: list[str]) -> str:
    if len(source_zone_types) == 1:
        return source_zone_types[0]
    if side == "BUY_SIDE":
        return "CLUSTERED_BUY_SIDE_ZONE"
    return "CLUSTERED_SELL_SIDE_ZONE"


def _merged_confidence_score(
    rows: list[dict[str, object]], source_timeframes: str, source_zone_types: list[str]
) -> int:
    return int(
        _merged_confidence_components(rows, source_timeframes, source_zone_types)[
            "final_confidence_score"
        ]
    )


def _merged_confidence_components(
    rows: list[dict[str, object]], source_timeframes: str, source_zone_types: list[str]
) -> dict[str, object]:
    prior_score = max(int(float(row["confidence_score"])) for row in rows)
    source_count = len(_pipe_union(row["source_level_ids"] for row in rows).split("|"))
    source_count_bonus = min(max(source_count - 1, 0) * 4, 16)
    h4_component = 8 if "H4" in source_timeframes else 0
    pdh_pdl_component = (
        8
        if any("PDH" in zone_type or "PDL" in zone_type for zone_type in source_zone_types)
        else 0
    )
    data_quality_penalty = (
        -5 if _quality_values(row["data_quality"] for row in rows) != "RAW" else 0
    )
    pre_clamp_score = (
        prior_score + source_count_bonus + h4_component + pdh_pdl_component + data_quality_penalty
    )
    final_score = max(0, min(100, pre_clamp_score))
    return {
        "base_score": 0,
        "timeframe_score": h4_component,
        "h1_component": None,
        "h4_component": h4_component,
        "session_component": None,
        "pdh_pdl_component": pdh_pdl_component,
        "equal_level_component": None,
        "source_count_bonus": source_count_bonus,
        "cluster_bonus": 0,
        "touch_bonus": None,
        "data_quality_penalty": data_quality_penalty,
        "carry_forward_prior_score": prior_score,
        "pre_clamp_score": pre_clamp_score,
        "final_confidence_score": final_score,
        "confidence_tier": _confidence_tier(final_score),
        "source_level_count": source_count,
        "cluster_member_count": len(rows),
        "source_timeframes": source_timeframes,
        "source_zone_types": "|".join(source_zone_types),
        "merged_from_zone_ids": sorted(str(row["zone_id"]) for row in rows),
        "registry_status_before": "|".join(sorted({str(row["status"]) for row in rows})),
        "registry_status_after": "post_merge_pre_lifecycle",
        "instrumentation_limitations": (
            "registry merge starts from prior max confidence_score; original initial "
            "score components are not separable from carried rows"
        ),
    }


def _instrumentation_from_row(row) -> dict[str, object]:
    return {column: row[column] if column in row else "" for column in SCORE_INSTRUMENTATION_COLUMNS}


def _pipe_union(values) -> str:
    parts: set[str] = set()
    for value in values:
        parts.update(part for part in str(value).split("|") if part)
    return "|".join(sorted(parts))


def _quality_values(values) -> str:
    unique = set(values)
    if unique == {"RAW"}:
        return "RAW"
    if "RECOVERED_DEGRADED" in unique:
        return "RECOVERED_DEGRADED"
    return sorted(unique)[0] if unique else "RAW"


def _confidence_tier(score: int) -> str:
    if score <= 39:
        return "LOW"
    if score <= 69:
        return "MEDIUM"
    return "HIGH"


def _distance_from_close(price_mid: float, latest_close: float | None) -> float:
    if latest_close is None or latest_close == 0:
        return 0.0
    return (price_mid - float(latest_close)) / float(latest_close) * 100.0


def _age_bars(first_seen_at: str, feed: pd.DataFrame) -> int:
    first_seen = pd.Timestamp(first_seen_at)
    if first_seen > feed["Timestamp"].max():
        return 0
    return int((feed["Timestamp"] >= first_seen).sum())


def _age_days(first_seen_at: str, run_end: str) -> int:
    return max(0, (pd.Timestamp(run_end).date() - pd.Timestamp(first_seen_at).date()).days)


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")
