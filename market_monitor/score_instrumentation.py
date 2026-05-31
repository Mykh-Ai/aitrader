from __future__ import annotations

import json


SCORE_INSTRUMENTATION_COLUMNS = [
    "score_components_json",
    "source_level_count",
    "cluster_member_count",
    "zone_width",
    "zone_width_pct",
    "has_h1_source",
    "has_h4_source",
    "has_session_source",
    "has_equal_level_source",
    "has_pdh_pdl_source",
]


def unique_pipe_parts(value) -> list[str]:
    return sorted({part for part in str(value or "").split("|") if part})


def score_instrumentation_fields(
    *,
    source_level_ids,
    source_timeframes,
    zone_type,
    price_lower,
    price_upper,
    price_mid,
    confidence_score,
    confidence_tier,
    score_components: dict[str, object],
) -> dict[str, object]:
    source_ids = unique_pipe_parts(source_level_ids)
    timeframes = set(unique_pipe_parts(source_timeframes))
    zone_type_text = str(zone_type or "")
    evidence_text = "|".join(
        [
            zone_type_text,
            str(score_components.get("level_types") or ""),
            str(score_components.get("source_zone_types") or ""),
        ]
    )
    lower = float(price_lower)
    upper = float(price_upper)
    mid = float(price_mid)
    width = upper - lower
    source_level_count = len(source_ids)
    cluster_member_count = int(score_components.get("cluster_member_count") or 1)
    fields = {
        "source_level_count": source_level_count,
        "cluster_member_count": cluster_member_count,
        "zone_width": width,
        "zone_width_pct": (width / mid * 100.0) if mid > 0 else "",
        "has_h1_source": "H1" in timeframes,
        "has_h4_source": "H4" in timeframes,
        "has_session_source": "SESSION" in timeframes,
        "has_equal_level_source": "EQUAL_HIGHS" in evidence_text
        or "EQUAL_LOWS" in evidence_text
        or "EQUAL_" in evidence_text,
        "has_pdh_pdl_source": "PDH" in evidence_text or "PDL" in evidence_text,
    }
    payload = {
        **score_components,
        **fields,
        "final_confidence_score": int(confidence_score),
        "confidence_tier": str(confidence_tier),
        "source_level_count": source_level_count,
        "source_timeframes": str(source_timeframes or ""),
        "zone_type": zone_type_text,
    }
    fields["score_components_json"] = deterministic_json(payload)
    return fields


def deterministic_json(payload: dict[str, object]) -> str:
    normalized = {key: _json_value(value) for key, value in payload.items()}
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _json_value(value):
    if value == "":
        return None
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return value
