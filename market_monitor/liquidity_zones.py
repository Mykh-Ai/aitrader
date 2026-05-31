from __future__ import annotations

import pandas as pd


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
]

ZONE_TYPE_BY_LEVEL = {
    "PDH": "PDH_ZONE",
    "PDL": "PDL_ZONE",
    "SESSION_HIGH": "SESSION_HIGH_ZONE",
    "SESSION_LOW": "SESSION_LOW_ZONE",
    "H1_SWING_HIGH": "BUY_SIDE_SWING_ZONE",
    "H1_SWING_LOW": "SELL_SIDE_SWING_ZONE",
}

CROSSED_BY_LATEST_CLOSE_REASON = "CROSSED_BY_LATEST_CLOSE_NO_SWEEP_CLASSIFICATION"


def build_liquidity_map(levels: pd.DataFrame, latest_close: float | None) -> pd.DataFrame:
    if levels.empty:
        return pd.DataFrame(columns=LIQUIDITY_MAP_COLUMNS)

    rows: list[dict[str, object]] = []
    for _, level in levels.iterrows():
        if level["side"] not in {"BUY_SIDE", "SELL_SIDE"}:
            continue
        zone_type = ZONE_TYPE_BY_LEVEL.get(level["level_type"])
        if zone_type is None:
            continue
        price_mid = float(level["price"])
        band = max(abs(price_mid) * 0.0005, 0.01)
        price_lower = price_mid - band
        price_upper = price_mid + band
        confidence_score = _confidence_score(level)
        status, invalidation_reason = _zone_status(
            side=level["side"],
            price_lower=price_lower,
            price_upper=price_upper,
            latest_close=latest_close,
        )
        rows.append(
            {
                "zone_id": "",
                "created_at": level["created_at"],
                "last_updated_at": level["created_at"],
                "side": level["side"],
                "zone_type": zone_type,
                "price_lower": price_lower,
                "price_upper": price_upper,
                "price_mid": price_mid,
                "source_level_ids": level["level_id"],
                "source_timeframes": level["timeframe"],
                "status": status,
                "confidence_score": confidence_score,
                "confidence_tier": _confidence_tier(confidence_score),
                "touch_count": int(level["touch_count"]),
                "sweep_count": 0,
                "distance_from_close_pct": _distance_from_close(price_mid, latest_close),
                "data_quality": level["data_quality"],
                "invalidation_reason": invalidation_reason,
            }
        )

    zones = pd.DataFrame(rows, columns=LIQUIDITY_MAP_COLUMNS)
    if zones.empty:
        return zones
    zones = zones.sort_values(
        ["created_at", "side", "zone_type", "price_mid"], kind="mergesort"
    ).reset_index(drop=True)
    zones["zone_id"] = [f"zone_{idx + 1:06d}" for idx in range(len(zones))]
    return zones


def _confidence_score(level: pd.Series) -> int:
    score = 20
    if level["timeframe"] == "D1":
        score += 25
    elif level["timeframe"] == "H1":
        score += 18
    elif level["timeframe"] == "SESSION":
        score += 12
    if level["level_type"] in {"PDH", "PDL"}:
        score += 20
    score += min(int(level["touch_count"]) * 5, 15)
    if level["data_quality"] != "RAW":
        score -= 15
    return max(0, min(100, score))


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
