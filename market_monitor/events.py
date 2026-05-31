from __future__ import annotations

import json

import pandas as pd


APPROACH_THRESHOLD_FRACTION = 0.001
APPROACH_THRESHOLD_MIN_USD = 20.0

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

LIFECYCLE_EVENT_TYPES = {
    "LIQUIDITY_ZONE_APPROACHED",
    "LIQUIDITY_ZONE_TOUCHED",
    "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED",
    "LIQUIDITY_ZONE_MERGED",
    "LIQUIDITY_ZONE_EXPIRED",
}


def build_event_log(
    *,
    registry: pd.DataFrame,
    feed: pd.DataFrame,
    volume_delta_state: pd.DataFrame,
    previous_registry: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if registry.empty or feed.empty:
        return pd.DataFrame(columns=EVENT_LOG_COLUMNS)

    frame = feed.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)
    run_start = frame["Timestamp"].min()
    run_end = frame["Timestamp"].max()
    previous_status = _previous_status_map(previous_registry)
    context = _context_map(volume_delta_state)
    events: list[dict[str, object]] = []

    for _, row in registry.iterrows():
        zone = row.to_dict()
        events.extend(_interaction_events(zone, frame, previous_status, context))
        lifecycle_event = _registry_lifecycle_event(
            zone, run_start, run_end, previous_status, context
        )
        if lifecycle_event is not None:
            events.append(lifecycle_event)

    if not events:
        return pd.DataFrame(columns=EVENT_LOG_COLUMNS)
    out = pd.DataFrame(events, columns=EVENT_LOG_COLUMNS)
    out = out[out["event_type"].isin(LIFECYCLE_EVENT_TYPES)]
    out = out.sort_values(
        ["event_timestamp", "event_type", "zone_id"], kind="mergesort"
    ).reset_index(drop=True)
    out["event_id"] = [f"event_{idx + 1:06d}" for idx in range(len(out))]
    return out[EVENT_LOG_COLUMNS]


def event_stats(event_log: pd.DataFrame) -> dict[str, object]:
    if event_log.empty:
        return {
            "total": 0,
            "by_type": "none",
            "approached": 0,
            "touched": 0,
            "crossed_unclassified": 0,
            "merged": 0,
            "expired": 0,
        }
    counts = event_log["event_type"].value_counts().sort_index()
    return {
        "total": len(event_log),
        "by_type": ", ".join(f"{name}={count}" for name, count in counts.items()),
        "approached": int((event_log["event_type"] == "LIQUIDITY_ZONE_APPROACHED").sum()),
        "touched": int((event_log["event_type"] == "LIQUIDITY_ZONE_TOUCHED").sum()),
        "crossed_unclassified": int(
            (event_log["event_type"] == "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED").sum()
        ),
        "merged": int((event_log["event_type"] == "LIQUIDITY_ZONE_MERGED").sum()),
        "expired": int((event_log["event_type"] == "LIQUIDITY_ZONE_EXPIRED").sum()),
    }


def _interaction_events(
    zone: dict[str, object],
    feed: pd.DataFrame,
    previous_status: dict[str, str],
    context: dict[str, dict[str, float]],
) -> list[dict[str, object]]:
    if str(zone.get("status", "")) in {"MERGED", "EXPIRED"}:
        return []
    first_seen = pd.Timestamp(zone["first_seen_at"])
    run_slice = feed[feed["Timestamp"] >= first_seen].copy()
    if run_slice.empty:
        return []

    cross_row = _first_cross(zone, run_slice)
    touch_row = _first_touch(zone, run_slice)
    if cross_row is not None:
        return [
            _market_event(
                zone=zone,
                event_type="LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED",
                candle=cross_row,
                feed=feed,
                previous_status=previous_status,
                context=context,
                trigger="price_crossed_zone_far_side",
                excursion_abs=_cross_excursion(zone, cross_row),
                new_status="CROSSED_UNCLASSIFIED",
            )
        ]
    if touch_row is not None:
        return [
            _market_event(
                zone=zone,
                event_type="LIQUIDITY_ZONE_TOUCHED",
                candle=touch_row,
                feed=feed,
                previous_status=previous_status,
                context=context,
                trigger="price_entered_zone_range",
                excursion_abs=0,
                new_status="TOUCHED",
            )
        ]

    approach_row = _first_approach(zone, run_slice)
    if approach_row is not None:
        return [
            _market_event(
                zone=zone,
                event_type="LIQUIDITY_ZONE_APPROACHED",
                candle=approach_row,
                feed=feed,
                previous_status=previous_status,
                context=context,
                trigger="price_reached_approach_threshold_without_touch",
                excursion_abs=0,
                new_status="APPROACHED",
            )
        ]
    return []


def _registry_lifecycle_event(
    zone: dict[str, object],
    run_start: pd.Timestamp,
    run_end: pd.Timestamp,
    previous_status: dict[str, str],
    context: dict[str, dict[str, float]],
) -> dict[str, object] | None:
    status = str(zone.get("status", ""))
    if status not in {"MERGED", "EXPIRED"}:
        return None
    prior_status = previous_status.get(str(zone["zone_id"]), "")
    if prior_status == status:
        return None
    event_ts = pd.Timestamp(zone.get("last_updated_at") or zone.get("last_seen_at"))
    if event_ts < run_start or event_ts > run_end + pd.Timedelta(days=1):
        return None
    event_type = (
        "LIQUIDITY_ZONE_MERGED"
        if status == "MERGED"
        else "LIQUIDITY_ZONE_EXPIRED"
    )
    evidence = _base_evidence(
        zone=zone,
        previous_status=prior_status,
        new_status=status,
        trigger="registry_lifecycle_update",
        candle_timestamp=_format_ts(event_ts),
        candle_high=0,
        candle_low=0,
        candle_close=0,
        context={"volume_zscore": 0.0, "delta_zscore": 0.0, "oi_change": 0.0},
    )
    if status == "MERGED":
        evidence["merged_from_zone_id"] = str(zone["zone_id"])
        evidence["merged_into_zone_id"] = str(zone.get("merged_into_zone_id", ""))
    else:
        evidence["age_days"] = int(float(zone.get("age_days", 0) or 0))
        evidence["max_zone_age_days"] = 7
        evidence["invalidation_reason"] = str(zone.get("invalidation_reason", ""))
    return {
        "event_id": "",
        "event_timestamp": _format_ts(event_ts),
        "event_type": event_type,
        "zone_id": zone["zone_id"],
        "side": zone["side"],
        "price_before": "",
        "event_high": "",
        "event_low": "",
        "event_close": "",
        "excursion_abs": 0,
        "excursion_atr": 0,
        "volume_zscore": 0,
        "delta_zscore": 0,
        "oi_change": 0,
        "reaction_status": "UNCLASSIFIED",
        "evidence_json": _json(evidence),
        "data_quality": zone["data_quality"],
    }


def _market_event(
    *,
    zone: dict[str, object],
    event_type: str,
    candle: pd.Series,
    feed: pd.DataFrame,
    previous_status: dict[str, str],
    context: dict[str, dict[str, float]],
    trigger: str,
    excursion_abs: float,
    new_status: str,
) -> dict[str, object]:
    event_ts = _format_ts(candle["Timestamp"])
    ctx = context.get(event_ts, {"volume_zscore": 0.0, "delta_zscore": 0.0, "oi_change": 0.0})
    evidence = _base_evidence(
        zone=zone,
        previous_status=previous_status.get(str(zone["zone_id"]), ""),
        new_status=new_status,
        trigger=trigger,
        candle_timestamp=event_ts,
        candle_high=float(candle["HiPrice"]),
        candle_low=float(candle["LowPrice"]),
        candle_close=float(candle["ClosePrice"]),
        context=ctx,
    )
    return {
        "event_id": "",
        "event_timestamp": event_ts,
        "event_type": event_type,
        "zone_id": zone["zone_id"],
        "side": zone["side"],
        "price_before": _price_before(feed, candle["Timestamp"]),
        "event_high": float(candle["HiPrice"]),
        "event_low": float(candle["LowPrice"]),
        "event_close": float(candle["ClosePrice"]),
        "excursion_abs": float(excursion_abs),
        "excursion_atr": 0,
        "volume_zscore": ctx["volume_zscore"],
        "delta_zscore": ctx["delta_zscore"],
        "oi_change": ctx["oi_change"],
        "reaction_status": "UNCLASSIFIED",
        "evidence_json": _json(evidence),
        "data_quality": zone["data_quality"],
    }


def _base_evidence(
    *,
    zone: dict[str, object],
    previous_status: str,
    new_status: str,
    trigger: str,
    candle_timestamp: str,
    candle_high: float,
    candle_low: float,
    candle_close: float,
    context: dict[str, float],
) -> dict[str, object]:
    return {
        "candle_close": candle_close,
        "candle_high": candle_high,
        "candle_low": candle_low,
        "candle_timestamp": candle_timestamp,
        "confidence_score": int(float(zone.get("confidence_score", 0) or 0)),
        "confidence_tier": str(zone.get("confidence_tier", "")),
        "data_quality": str(zone.get("data_quality", "")),
        "delta_zscore": float(context["delta_zscore"]),
        "new_status": new_status,
        "oi_change": float(context["oi_change"]),
        "previous_status": previous_status,
        "price_lower": float(zone["price_lower"]),
        "price_mid": float(zone["price_mid"]),
        "price_upper": float(zone["price_upper"]),
        "side": str(zone["side"]),
        "source_timeframes": str(zone.get("source_timeframes", "")),
        "trigger": trigger,
        "volume_zscore": float(context["volume_zscore"]),
        "zone_id": str(zone["zone_id"]),
        "zone_type": str(zone["zone_type"]),
    }


def _first_cross(zone: dict[str, object], feed: pd.DataFrame) -> pd.Series | None:
    if zone["side"] == "BUY_SIDE":
        crossed = feed[feed["HiPrice"] > float(zone["price_upper"])]
    else:
        crossed = feed[feed["LowPrice"] < float(zone["price_lower"])]
    if crossed.empty:
        return None
    return crossed.iloc[0]


def _first_touch(zone: dict[str, object], feed: pd.DataFrame) -> pd.Series | None:
    lower = float(zone["price_lower"])
    upper = float(zone["price_upper"])
    if zone["side"] == "BUY_SIDE":
        touched = feed[(feed["HiPrice"] >= lower) & (feed["HiPrice"] <= upper)]
    else:
        touched = feed[(feed["LowPrice"] <= upper) & (feed["LowPrice"] >= lower)]
    if touched.empty:
        return None
    return touched.iloc[0]


def _first_approach(zone: dict[str, object], feed: pd.DataFrame) -> pd.Series | None:
    latest_close = float(feed.iloc[-1]["ClosePrice"])
    threshold = max(APPROACH_THRESHOLD_MIN_USD, latest_close * APPROACH_THRESHOLD_FRACTION)
    lower = float(zone["price_lower"])
    upper = float(zone["price_upper"])
    if zone["side"] == "BUY_SIDE":
        approached = feed[(feed["HiPrice"] >= lower - threshold) & (feed["HiPrice"] < lower)]
    else:
        approached = feed[(feed["LowPrice"] <= upper + threshold) & (feed["LowPrice"] > upper)]
    if approached.empty:
        return None
    return approached.iloc[0]


def _cross_excursion(zone: dict[str, object], candle: pd.Series) -> float:
    if zone["side"] == "BUY_SIDE":
        return max(0.0, float(candle["HiPrice"]) - float(zone["price_upper"]))
    return max(0.0, float(zone["price_lower"]) - float(candle["LowPrice"]))


def _price_before(feed: pd.DataFrame, timestamp) -> float | str:
    previous = feed[feed["Timestamp"] < pd.Timestamp(timestamp)]
    if previous.empty:
        return ""
    return float(previous.iloc[-1]["ClosePrice"])


def _previous_status_map(previous_registry: pd.DataFrame | None) -> dict[str, str]:
    if previous_registry is None or previous_registry.empty:
        return {}
    return {
        str(row["zone_id"]): str(row["status"])
        for _, row in previous_registry.iterrows()
    }


def _context_map(volume_delta_state: pd.DataFrame) -> dict[str, dict[str, float]]:
    if volume_delta_state.empty:
        return {}
    return {
        str(row["timestamp"]): {
            "volume_zscore": float(row["volume_zscore"]),
            "delta_zscore": float(row["delta_zscore"]),
            "oi_change": float(row["oi_change"]),
        }
        for _, row in volume_delta_state.iterrows()
    }


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
