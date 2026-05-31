from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from market_monitor.score_instrumentation import (
    HARD_WIDE_ZONE_WIDTH_PCT,
    SCORE_INSTRUMENTATION_COLUMNS,
    precision_status_for_width,
    score_instrumentation_fields,
)


LIQUIDITY_MAP_COLUMNS = [
    "zone_id",
    "created_at",
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
    "touch_count",
    "sweep_count",
    "distance_from_close_pct",
    "data_quality",
    "invalidation_reason",
    *SCORE_INSTRUMENTATION_COLUMNS,
]

ZONE_TYPE_BY_LEVEL = {
    "PDH": "PDH_ZONE",
    "PDL": "PDL_ZONE",
    "ASIA_HIGH": "ASIA_HIGH_ZONE",
    "ASIA_LOW": "ASIA_LOW_ZONE",
    "EUROPE_HIGH": "EUROPE_HIGH_ZONE",
    "EUROPE_LOW": "EUROPE_LOW_ZONE",
    "US_HIGH": "US_HIGH_ZONE",
    "US_LOW": "US_LOW_ZONE",
    "H1_SWING_HIGH": "H1_SWING_HIGH_ZONE",
    "H1_SWING_LOW": "H1_SWING_LOW_ZONE",
    "H4_SWING_HIGH": "H4_SWING_HIGH_ZONE",
    "H4_SWING_LOW": "H4_SWING_LOW_ZONE",
    "EQUAL_HIGHS": "EQUAL_HIGHS_ZONE",
    "EQUAL_LOWS": "EQUAL_LOWS_ZONE",
    # Backward-compatible aliases for Sprint 1 tests and ad hoc callers.
    "SESSION_HIGH": "ASIA_HIGH_ZONE",
    "SESSION_LOW": "ASIA_LOW_ZONE",
}

CROSSED_BY_LATEST_CLOSE_REASON = "CROSSED_BY_LATEST_CLOSE_NO_SWEEP_CLASSIFICATION"
MIN_CONFIDENCE_SCORE = 25


@dataclass(frozen=True)
class SourceEvidence:
    level_ids: tuple[str, ...]
    timeframes: tuple[str, ...]
    level_types: tuple[str, ...]
    data_quality: str
    touch_count: int
    cluster_member_count: int = 1


def build_liquidity_map(levels: pd.DataFrame, latest_close: float | None) -> pd.DataFrame:
    if levels.empty:
        return pd.DataFrame(columns=LIQUIDITY_MAP_COLUMNS)

    preliminary = _preliminary_zones(levels, latest_close)
    if not preliminary:
        return pd.DataFrame(columns=LIQUIDITY_MAP_COLUMNS)

    merged = _merge_zones(preliminary, latest_close)
    rows = [_finalize_zone(zone, latest_close) for zone in merged]
    rows = [_apply_status(row, latest_close) for row in rows]
    rows = [row for row in rows if row["status"] != "INVALIDATED"]
    rows = [row for row in rows if _passes_pruning(row)]

    zones = pd.DataFrame(rows, columns=LIQUIDITY_MAP_COLUMNS)
    if zones.empty:
        return zones
    zones = zones.sort_values(
        ["created_at", "side", "zone_type", "price_mid", "source_level_ids"],
        kind="mergesort",
    ).reset_index(drop=True)
    zones["zone_id"] = [f"zone_{idx + 1:06d}" for idx in range(len(zones))]
    return zones


def _preliminary_zones(
    levels: pd.DataFrame, latest_close: float | None
) -> list[dict[str, object]]:
    zones: list[dict[str, object]] = []
    for _, level in levels.iterrows():
        if level["side"] not in {"BUY_SIDE", "SELL_SIDE"}:
            continue
        zone_type = ZONE_TYPE_BY_LEVEL.get(level["level_type"])
        if zone_type is None:
            continue
        price_mid = float(level["price"])
        band = max(abs(price_mid) * 0.0005, 10.0)
        source_ids = _source_ids_for_level(level)
        evidence = SourceEvidence(
            level_ids=tuple(source_ids),
            timeframes=(str(level["timeframe"]),),
            level_types=(str(level["level_type"]),),
            data_quality=str(level["data_quality"]),
            touch_count=int(level["touch_count"]),
            cluster_member_count=1,
        )
        zones.append(
            {
                "created_at": level["created_at"],
                "last_updated_at": level["created_at"],
                "side": level["side"],
                "zone_type": zone_type,
                "price_lower": price_mid - band,
                "price_upper": price_mid + band,
                "price_mid": price_mid,
                "evidence": evidence,
            }
        )
    return zones


def _merge_zones(
    preliminary: list[dict[str, object]], latest_close: float | None
) -> list[dict[str, object]]:
    merge_tolerance = max(10.0, float(latest_close or 0) * 0.0005)
    merged: list[dict[str, object]] = []
    for side in ["BUY_SIDE", "SELL_SIDE"]:
        side_zones = sorted(
            [zone for zone in preliminary if zone["side"] == side],
            key=lambda zone: (float(zone["price_lower"]), str(zone["created_at"])),
        )
        cluster: list[dict[str, object]] = []
        for zone in side_zones:
            if not cluster:
                cluster = [zone]
                continue
            current_upper = max(float(item["price_upper"]) for item in cluster)
            if (
                float(zone["price_lower"]) <= current_upper + merge_tolerance
                and _cluster_width_pct(cluster + [zone]) < HARD_WIDE_ZONE_WIDTH_PCT
            ):
                cluster.append(zone)
            else:
                merged.append(_collapse_cluster(cluster))
                cluster = [zone]
        if cluster:
            merged.append(_collapse_cluster(cluster))
    return merged


def _collapse_cluster(cluster: list[dict[str, object]]) -> dict[str, object]:
    lower = min(float(zone["price_lower"]) for zone in cluster)
    upper = max(float(zone["price_upper"]) for zone in cluster)
    evidence_items = [zone["evidence"] for zone in cluster]
    level_ids = sorted({level_id for evidence in evidence_items for level_id in evidence.level_ids})
    timeframes = sorted({tf for evidence in evidence_items for tf in evidence.timeframes})
    level_types = sorted({lt for evidence in evidence_items for lt in evidence.level_types})
    data_quality = _quality_values([evidence.data_quality for evidence in evidence_items])
    zone_types = sorted({str(zone["zone_type"]) for zone in cluster})
    side = str(cluster[0]["side"])
    zone_type = _merged_zone_type(side, zone_types)
    return {
        "created_at": max(str(zone["created_at"]) for zone in cluster),
        "last_updated_at": max(str(zone["last_updated_at"]) for zone in cluster),
        "side": side,
        "zone_type": zone_type,
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "evidence": SourceEvidence(
            level_ids=tuple(level_ids),
            timeframes=tuple(timeframes),
            level_types=tuple(level_types),
            data_quality=data_quality,
            touch_count=sum(evidence.touch_count for evidence in evidence_items),
            cluster_member_count=sum(evidence.cluster_member_count for evidence in evidence_items),
        ),
    }


def _cluster_width_pct(cluster: list[dict[str, object]]) -> float:
    lower = min(float(zone["price_lower"]) for zone in cluster)
    upper = max(float(zone["price_upper"]) for zone in cluster)
    return _zone_width_pct(lower, upper, (lower + upper) / 2)


def _merged_zone_type(side: str, zone_types: list[str]) -> str:
    if len(zone_types) == 1:
        return zone_types[0]
    if side == "BUY_SIDE":
        return "CLUSTERED_BUY_SIDE_ZONE"
    return "CLUSTERED_SELL_SIDE_ZONE"


def _finalize_zone(zone: dict[str, object], latest_close: float | None) -> dict[str, object]:
    evidence: SourceEvidence = zone["evidence"]  # type: ignore[assignment]
    zone_width_pct = _zone_width_pct(
        float(zone["price_lower"]), float(zone["price_upper"]), float(zone["price_mid"])
    )
    confidence_score = _confidence_score(evidence, zone_width_pct)
    confidence_tier = _confidence_tier(confidence_score)
    source_level_ids = "|".join(evidence.level_ids)
    source_timeframes = "|".join(evidence.timeframes)
    components = _confidence_components(evidence, zone_width_pct)
    instrumentation = score_instrumentation_fields(
        source_level_ids=source_level_ids,
        source_timeframes=source_timeframes,
        zone_type=zone["zone_type"],
        price_lower=zone["price_lower"],
        price_upper=zone["price_upper"],
        price_mid=zone["price_mid"],
        confidence_score=confidence_score,
        confidence_tier=confidence_tier,
        score_components=components,
    )
    return {
        "zone_id": "",
        "created_at": zone["created_at"],
        "last_updated_at": zone["last_updated_at"],
        "side": zone["side"],
        "zone_type": zone["zone_type"],
        "price_lower": zone["price_lower"],
        "price_upper": zone["price_upper"],
        "price_mid": zone["price_mid"],
        "source_level_ids": source_level_ids,
        "source_timeframes": source_timeframes,
        "status": "ACTIVE",
        "confidence_score": confidence_score,
        "confidence_tier": confidence_tier,
        "touch_count": evidence.touch_count,
        "sweep_count": 0,
        "distance_from_close_pct": _distance_from_close(float(zone["price_mid"]), latest_close),
        "data_quality": evidence.data_quality,
        "invalidation_reason": "",
        **instrumentation,
    }


def _apply_status(row: dict[str, object], latest_close: float | None) -> dict[str, object]:
    status, invalidation_reason = _zone_status(
        side=str(row["side"]),
        price_lower=float(row["price_lower"]),
        price_upper=float(row["price_upper"]),
        latest_close=latest_close,
    )
    row["status"] = status
    row["invalidation_reason"] = invalidation_reason
    return row


def _passes_pruning(row: dict[str, object]) -> bool:
    if int(row["confidence_score"]) >= MIN_CONFIDENCE_SCORE:
        return True
    source_timeframes = set(str(row["source_timeframes"]).split("|"))
    source_ids = str(row["source_level_ids"]).split("|")
    zone_type = str(row["zone_type"])
    if "H4" in source_timeframes:
        return True
    if zone_type in {"PDH_ZONE", "PDL_ZONE", "EQUAL_HIGHS_ZONE", "EQUAL_LOWS_ZONE"}:
        return True
    if "H4" in zone_type or "PDH" in zone_type or "PDL" in zone_type:
        return True
    return len([source_id for source_id in source_ids if source_id]) >= 2 and zone_type.startswith("EQUAL_")


def _confidence_score(evidence: SourceEvidence, zone_width_pct: float = 0.0) -> int:
    components = _confidence_components(evidence, zone_width_pct)
    return int(components["final_confidence_score"])


def _confidence_components(evidence: SourceEvidence, zone_width_pct: float = 0.0) -> dict[str, object]:
    level_types = set(evidence.level_types)
    timeframes = set(evidence.timeframes)
    source_families = _source_families(timeframes, level_types)
    h4_component = 40 if "H4" in timeframes else 0
    h1_component = 24 if "H1" in timeframes else 0
    session_component = _session_component(timeframes)
    pdh_pdl_component = 45 if level_types & {"PDH", "PDL"} else 0
    high_low_component = 0
    equal_level_component = 4 if level_types & {"EQUAL_HIGHS", "EQUAL_LOWS"} else 0
    source_diversity_bonus = min(max(len(source_families) - 2, 0) * 4, 12)
    raw_source_count_bonus = _raw_source_count_bonus(
        source_count=len(evidence.level_ids),
        source_family_count=len(source_families),
        has_equal_level=bool(level_types & {"EQUAL_HIGHS", "EQUAL_LOWS"}),
    )
    source_count_bonus = raw_source_count_bonus
    touch_bonus = min(evidence.touch_count, 3)
    width_penalty = _width_penalty(zone_width_pct, len(evidence.level_ids))
    data_quality_penalty = -15 if evidence.data_quality != "RAW" else 0
    pre_clamp_score = (
        h4_component
        + h1_component
        + session_component
        + pdh_pdl_component
        + high_low_component
        + equal_level_component
        + source_diversity_bonus
        + raw_source_count_bonus
        + touch_bonus
        + width_penalty
        + data_quality_penalty
    )
    final_score = max(0, min(100, pre_clamp_score))
    precision_status = precision_status_for_width(zone_width_pct)
    return {
        "base_score": 0,
        "timeframe_score": h4_component + h1_component,
        "timeframe_component_total": h4_component + h1_component + session_component,
        "h1_component": h1_component,
        "h4_component": h4_component,
        "session_component": session_component,
        "high_low_component": high_low_component,
        "pdh_pdl_component": pdh_pdl_component,
        "equal_level_component": equal_level_component,
        "source_diversity_bonus": source_diversity_bonus,
        "raw_source_count_bonus": raw_source_count_bonus,
        "source_count_bonus": source_count_bonus,
        "cluster_bonus": 0,
        "touch_bonus": touch_bonus,
        "width_penalty": width_penalty,
        "precision_status": precision_status,
        "hard_wide_zone_width_pct": HARD_WIDE_ZONE_WIDTH_PCT,
        "carry_forward_decay_or_penalty": None,
        "data_quality_penalty": data_quality_penalty,
        "carry_forward_prior_score": None,
        "pre_clamp_score": pre_clamp_score,
        "final_confidence_score": final_score,
        "confidence_tier": _confidence_tier(final_score),
        "source_level_count": len(evidence.level_ids),
        "cluster_member_count": evidence.cluster_member_count,
        "source_timeframes": "|".join(sorted(timeframes)),
        "source_families": "|".join(sorted(source_families)),
        "level_types": "|".join(sorted(level_types)),
        "instrumentation_limitations": (
            "confidence_score is structural-only; post-event observation metrics are not used"
        ),
    }


def _source_families(timeframes: set[str], level_types: set[str]) -> set[str]:
    families: set[str] = set()
    for timeframe in ["H4", "H1", "SESSION"]:
        if timeframe in timeframes:
            families.add(timeframe)
    if level_types & {"PDH", "PDL"}:
        families.add("PDH_PDL")
    if level_types & {"EQUAL_HIGHS", "EQUAL_LOWS"}:
        families.add("EQUAL_LEVEL")
    return families


def _session_component(timeframes: set[str]) -> int:
    if "SESSION" not in timeframes:
        return 0
    if timeframes == {"SESSION"}:
        return 24
    return 6


def _raw_source_count_bonus(
    *, source_count: int, source_family_count: int, has_equal_level: bool
) -> int:
    if has_equal_level:
        return 0
    excess_sources = max(source_count - max(source_family_count, 1), 0)
    return min(excess_sources * 2, 6)


def _width_penalty(zone_width_pct: float, source_count: int = 1) -> int:
    if source_count <= 1:
        return 0
    if zone_width_pct >= 0.50:
        return -12
    if zone_width_pct >= 0.25:
        return -6
    return 0


def _zone_width_pct(price_lower: float, price_upper: float, price_mid: float) -> float:
    if price_mid <= 0:
        return 0.0
    return (price_upper - price_lower) / price_mid * 100.0


def _confidence_tier(score: int) -> str:
    if score <= 39:
        return "LOW"
    if score <= 69:
        return "MEDIUM"
    return "HIGH"


def _zone_status(
    *,
    side: str,
    price_lower: float,
    price_upper: float,
    latest_close: float | None,
) -> tuple[str, str]:
    if latest_close is None:
        return "ACTIVE", ""

    close = float(latest_close)
    if price_lower <= close <= price_upper:
        return "TOUCHED", ""

    if side == "BUY_SIDE" and close > price_upper:
        return "INVALIDATED", CROSSED_BY_LATEST_CLOSE_REASON
    if side == "SELL_SIDE" and close < price_lower:
        return "INVALIDATED", CROSSED_BY_LATEST_CLOSE_REASON
    return "ACTIVE", ""


def _distance_from_close(price_mid: float, latest_close: float | None) -> float:
    if latest_close is None or latest_close == 0:
        return 0.0
    return (price_mid - float(latest_close)) / float(latest_close) * 100.0


def _source_ids_for_level(level: pd.Series) -> list[str]:
    existing = str(level.get("source_level_ids", "") or "")
    if existing:
        return sorted(part for part in existing.split("|") if part)
    return [str(level["level_id"])]


def _quality_values(values) -> str:
    unique = set(values)
    if unique == {"RAW"}:
        return "RAW"
    if "RECOVERED_DEGRADED" in unique:
        return "RECOVERED_DEGRADED"
    return sorted(unique)[0]
