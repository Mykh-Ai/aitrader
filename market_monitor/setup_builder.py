from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


SETUP_BUILDER_VERSION = "SHI_RESET_37K_LIVE_REPLAY_SETUP_TIMELINE_V0"
SETUP_RESEARCH_CANDIDATES_CSV = "setup_research_timeline.csv"
SETUP_BUILDER_MANIFEST_JSON = "setup_builder_manifest.json"
SETUP_BUILDER_SUMMARY_MD = "setup_builder_summary.md"

TRIGGER_STATUS_VALUES = {"WATCH", "ARMED", "TRIGGERED", "INVALIDATED", "EXPIRED"}

SETUP_BUILDER_COLUMNS = [
    "setup_id",
    "start_timestamp",
    "end_timestamp",
    "setup_formed_at",
    "source_window_start",
    "source_window_end",
    "source_time_precision",
    "setup_type",
    "direction_context",
    "countertrend_flag",
    "trigger_status",
    "market_state",
    "dominant_side",
    "candidate_strength",
    "nearest_zone_side",
    "zone_position_context",
    "sweep_status",
    "reclaim_status",
    "compression_score",
    "delta_pct",
    "range_pct",
    "close_position",
    "open_interest_change",
    "seller_pressure_score",
    "buyer_response_score",
    "entry_reference_level",
    "invalidation_level",
    "target_reference_zone",
    "evidence_summary",
]

SELLER_DOMINANT_STATES = {
    "MARKDOWN_ABOVE_SUPPORT",
    "PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE",
    "FAILED_BREAKOUT_SELLER_RECLAIM",
    "EXPANSION_DOWN",
}
DEMAND_UP_RAW_LABELS = {
    "DOWNTREND_EXHAUSTION_CANDIDATE",
    "BUYER_ABSORPTION_CANDIDATE",
    "HIDDEN_ACCUMULATION_UP_CANDIDATE",
}
SUPPLY_DOWN_RAW_LABELS = {
    "SELLER_ABSORPTION_CANDIDATE",
    "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
    "UPTREND_EXHAUSTION_CANDIDATE",
}
BEARISH_RETEST_LABELS = {
    "NORMALIZATION_AFTER_MARKDOWN",
    "SELLER_ABSORPTION_CANDIDATE",
    "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
    "COMPRESSION_BEFORE_EXPANSION_CANDIDATE",
}
FORBIDDEN_OUTPUT_TERMS = {
    "OPEN_LONG",
    "OPEN_SHORT",
    "BUY_NOW",
    "SELL_NOW",
    "ENTRY_SIGNAL",
    "EXIT_SIGNAL",
    "TAKE_PROFIT",
    "STOP_LOSS",
    "LIVE_READY",
    "EXECUTION_READY",
}


@dataclass(frozen=True)
class SetupBuilderResult:
    output_dir: Path
    candidates_path: Path
    manifest_path: Path
    summary_path: Path
    candidate_count: int


def run_setup_builder(
    *,
    state_timeline_path: str | Path,
    regime_windows_path: str | Path,
    selected_zones_path: str | Path,
    output_dir: str | Path,
    hidden_flow_candidates_path: str | Path | None = None,
) -> SetupBuilderResult:
    state_path = Path(state_timeline_path)
    windows_path = Path(regime_windows_path)
    zones_path = Path(selected_zones_path)
    hidden_path = Path(hidden_flow_candidates_path) if hidden_flow_candidates_path else None
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates_path = out_dir / SETUP_RESEARCH_CANDIDATES_CSV
    manifest_path = out_dir / SETUP_BUILDER_MANIFEST_JSON
    summary_path = out_dir / SETUP_BUILDER_SUMMARY_MD

    missing_inputs = [str(path) for path in [state_path, windows_path, zones_path] if not path.exists()]
    optional_hidden_loaded = hidden_path is not None and hidden_path.exists()
    if missing_inputs:
        candidates = pd.DataFrame(columns=SETUP_BUILDER_COLUMNS)
        _write_outputs(
            candidates=candidates,
            candidates_path=candidates_path,
            manifest_path=manifest_path,
            summary_path=summary_path,
            state_path=state_path,
            windows_path=windows_path,
            zones_path=zones_path,
            hidden_path=hidden_path,
            optional_hidden_loaded=optional_hidden_loaded,
            missing_inputs=missing_inputs,
        )
        return SetupBuilderResult(out_dir, candidates_path, manifest_path, summary_path, 0)

    states = _read_csv(state_path)
    windows = _prepare_windows(_read_csv(windows_path))
    zones = _visible_zones(_read_csv(zones_path))
    hidden_candidates = _read_csv(hidden_path) if optional_hidden_loaded and hidden_path is not None else pd.DataFrame()
    if not hidden_candidates.empty:
        windows = pd.concat(
            [windows, _prepare_windows(_promoted_candidates_as_windows(hidden_candidates))],
            ignore_index=True,
            sort=False,
        )

    rows = _build_rows(states=states, windows=windows, zones=zones, hidden_candidates=hidden_candidates)
    candidates = pd.DataFrame(rows, columns=SETUP_BUILDER_COLUMNS)
    _assert_no_forbidden_output(candidates)
    _write_outputs(
        candidates=candidates,
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        state_path=state_path,
        windows_path=windows_path,
        zones_path=zones_path,
        hidden_path=hidden_path,
        optional_hidden_loaded=optional_hidden_loaded,
        missing_inputs=[],
    )
    return SetupBuilderResult(out_dir, candidates_path, manifest_path, summary_path, int(len(candidates)))


def _build_rows(
    *,
    states: pd.DataFrame,
    windows: pd.DataFrame,
    zones: pd.DataFrame,
    hidden_candidates: pd.DataFrame,
) -> list[dict[str, object]]:
    if states.empty:
        return []
    states = states.copy()
    states["_start_ts"] = pd.to_datetime(states["start_timestamp"], errors="coerce", utc=True)
    states["_end_ts"] = pd.to_datetime(states["end_timestamp"], errors="coerce", utc=True)
    rows: list[dict[str, object]] = []
    for _, state in states.sort_values(["_end_ts", "_start_ts"], kind="mergesort").iterrows():
        state_windows = _windows_for_state(windows, state)
        context = _state_context(state)
        for candidate in [
            _seller_dominance_retest_down(state, state_windows, zones, context),
            _supply_sweep_reclaim_down(state, state_windows, zones, context),
            _demand_sweep_reclaim_up(state, state_windows, zones, context),
            _accepted_breakout_up(state, state_windows, zones, context),
        ]:
            if candidate is not None:
                rows.append(candidate)
    deduped: dict[tuple[object, ...], dict[str, object]] = {}
    for row in rows:
        key = (row["start_timestamp"], row["end_timestamp"], row["setup_type"], row["entry_reference_level"])
        deduped.setdefault(key, row)
    ordered = sorted(deduped.values(), key=lambda row: (str(row["end_timestamp"]), str(row["setup_type"])))
    for index, row in enumerate(ordered, start=1):
        row["setup_id"] = f"setup_{index:06d}"
    return ordered


def _seller_dominance_retest_down(
    state: pd.Series,
    windows: pd.DataFrame,
    zones: pd.DataFrame,
    context: dict[str, object],
) -> dict[str, object] | None:
    market_state = str(state.get("market_state", ""))
    dominant_side = str(context["dominant_side"])
    seller_pressure = float(context["seller_pressure_score"])
    buyer_response = float(context["buyer_response_score"])
    resistance_upper = _float_value(state.get("active_resistance_price_upper"))
    if pd.isna(resistance_upper):
        return None
    if market_state not in SELLER_DOMINANT_STATES and dominant_side != "SELLER":
        return None
    if dominant_side != "SELLER" or seller_pressure < 70 or buyer_response > 35:
        return None
    if _float_value(state.get("close_position"), 1.0) > 0.45:
        return None

    raw = _best_window(windows, _is_bearish_retest_raw)
    status = "WATCH"
    if raw is not None:
        status = "ARMED"
    if market_state == "FAILED_BREAKOUT_SELLER_RECLAIM":
        status = "TRIGGERED"
    return _row(
        state=state,
        raw=raw,
        zones=zones,
        context=context,
        setup_type="SELLER_DOMINANCE_RETEST_DOWN_SETUP",
        direction_context="DOWN",
        countertrend_flag="false",
        trigger_status=status,
        sweep_status="not_required_for_retest_context",
        reclaim_status="failed_reclaim_or_failed_bounce_context" if raw is not None else "state_context_only",
        entry_reference_level=resistance_upper,
        invalidation_level=resistance_upper,
        target_side="SELL_SIDE",
        evidence_note="setup candidate; research-only trigger; invalidation reference above rejected resistance; replay required",
    )


def _supply_sweep_reclaim_down(
    state: pd.Series,
    windows: pd.DataFrame,
    zones: pd.DataFrame,
    context: dict[str, object],
) -> dict[str, object] | None:
    resistance_lower = _float_value(state.get("active_resistance_price_lower"))
    resistance_upper = _float_value(state.get("active_resistance_price_upper"))
    if pd.isna(resistance_lower) or pd.isna(resistance_upper):
        return None
    overhead_supply = float(context["overhead_supply_score"])
    seller_pressure = float(context["seller_pressure_score"])
    raw = _best_window(windows, _is_supply_sweep_raw)
    if raw is None:
        return None
    if overhead_supply < 70 or seller_pressure < 50:
        return None
    status = "TRIGGERED" if str(state.get("market_state", "")) == "FAILED_BREAKOUT_SELLER_RECLAIM" else "ARMED"
    return _row(
        state=state,
        raw=raw,
        zones=zones,
        context=context,
        setup_type="SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
        direction_context="DOWN",
        countertrend_flag=_countertrend(context["dominant_side"], "DOWN"),
        trigger_status=status,
        sweep_status="sweep_above_supply_or_local_high_context",
        reclaim_status="return_below_rejected_supply_context",
        entry_reference_level=resistance_lower,
        invalidation_level=resistance_upper,
        target_side="SELL_SIDE",
        evidence_note="setup candidate; research-only trigger; invalidation reference above supply; replay required",
    )


def _demand_sweep_reclaim_up(
    state: pd.Series,
    windows: pd.DataFrame,
    zones: pd.DataFrame,
    context: dict[str, object],
) -> dict[str, object] | None:
    support_lower = _float_value(state.get("active_support_price_lower"))
    support_upper = _float_value(state.get("active_support_price_upper"))
    if pd.isna(support_lower) or pd.isna(support_upper):
        return None
    raw = _best_window(windows, _is_demand_reclaim_raw)
    if raw is None:
        return None
    underlying_demand = float(context["underlying_demand_score"])
    buyer_response = float(context["buyer_response_score"])
    if underlying_demand < 55 and buyer_response < 25:
        return None
    close_position = _raw_close_position(raw)
    status = "ARMED" if close_position >= 0.65 and buyer_response >= 35 else "WATCH"
    return _row(
        state=state,
        raw=raw,
        zones=zones,
        context=context,
        setup_type="DEMAND_SWEEP_RECLAIM_UP_SETUP",
        direction_context="UP",
        countertrend_flag=_countertrend(context["dominant_side"], "UP"),
        trigger_status=status,
        sweep_status="possible_sweep_below_demand_or_local_low",
        reclaim_status="reclaim_requires_asof_confirmation" if status == "WATCH" else "reclaim_started_confirmation_incomplete",
        entry_reference_level=support_upper,
        invalidation_level=support_lower,
        target_side="BUY_SIDE",
        evidence_note="setup candidate; research-only trigger; invalidation reference below demand; target reference zone; replay required",
    )


def _accepted_breakout_up(
    state: pd.Series,
    windows: pd.DataFrame,
    zones: pd.DataFrame,
    context: dict[str, object],
) -> dict[str, object] | None:
    resistance_lower = _float_value(state.get("active_resistance_price_lower"))
    resistance_upper = _float_value(state.get("active_resistance_price_upper"))
    if pd.isna(resistance_lower) or pd.isna(resistance_upper):
        return None
    raw = _best_window(windows, _is_breakout_up_raw)
    if raw is None:
        return None
    buyer_response = float(context["buyer_response_score"])
    seller_pressure = float(context["seller_pressure_score"])
    price_close = _float_value(state.get("price_close"))
    if buyer_response <= seller_pressure:
        return None
    if not pd.isna(price_close) and price_close < resistance_upper:
        return None
    status = "TRIGGERED" if _raw_close_position(raw) >= 0.82 else "ARMED"
    return _row(
        state=state,
        raw=raw,
        zones=zones,
        context=context,
        setup_type="ACCEPTED_BREAKOUT_UP_SETUP",
        direction_context="UP",
        countertrend_flag=_countertrend(context["dominant_side"], "UP"),
        trigger_status=status,
        sweep_status="not_required_for_breakout_context",
        reclaim_status="accepted_breakout_context",
        entry_reference_level=resistance_upper,
        invalidation_level=resistance_lower,
        target_side="BUY_SIDE",
        evidence_note="setup candidate; research-only trigger; invalidation reference below resistance; target reference zone; replay required",
    )


def _row(
    *,
    state: pd.Series,
    raw: pd.Series | None,
    zones: pd.DataFrame,
    context: dict[str, object],
    setup_type: str,
    direction_context: str,
    countertrend_flag: str,
    trigger_status: str,
    sweep_status: str,
    reclaim_status: str,
    entry_reference_level: float,
    invalidation_level: float,
    target_side: str,
    evidence_note: str,
) -> dict[str, object]:
    if trigger_status not in TRIGGER_STATUS_VALUES:
        raise ValueError(f"unsupported trigger status: {trigger_status}")
    return {
        "setup_id": "",
        "start_timestamp": _cell(state.get("start_timestamp")),
        "end_timestamp": _cell(state.get("end_timestamp")),
        "setup_formed_at": _formed_at(state, raw),
        "source_window_start": _source_window_start(state, raw),
        "source_window_end": _source_window_end(state, raw),
        "source_time_precision": _source_time_precision(raw),
        "setup_type": setup_type,
        "direction_context": direction_context,
        "countertrend_flag": countertrend_flag,
        "trigger_status": trigger_status,
        "market_state": _cell(state.get("market_state")),
        "dominant_side": context["dominant_side"],
        "candidate_strength": _cell(state.get("candidate_strength")),
        "nearest_zone_side": _cell(raw.get("nearest_zone_side") if raw is not None else ""),
        "zone_position_context": _cell(raw.get("zone_position_context") if raw is not None else ""),
        "sweep_status": sweep_status,
        "reclaim_status": reclaim_status,
        "compression_score": _round(raw.get("compression_score") if raw is not None else ""),
        "delta_pct": _round(raw.get("delta_pct") if raw is not None else state.get("delta_pct")),
        "range_pct": _round(raw.get("range_pct") if raw is not None else state.get("range_pct")),
        "close_position": _round(_raw_close_position(raw) if raw is not None else state.get("close_position")),
        "open_interest_change": _round(raw.get("open_interest_change") if raw is not None else state.get("open_interest_change")),
        "seller_pressure_score": _round(context["seller_pressure_score"]),
        "buyer_response_score": _round(context["buyer_response_score"]),
        "entry_reference_level": _round(entry_reference_level),
        "invalidation_level": _round(invalidation_level),
        "target_reference_zone": _target_reference_zone(zones, target_side, _float_value(state.get("price_close"))),
        "evidence_summary": _evidence_summary(state, raw, evidence_note),
    }


def _is_bearish_retest_raw(row: pd.Series) -> bool:
    label = str(row.get("candidate_label", ""))
    trend = str(row.get("trend_direction", ""))
    side = str(row.get("nearest_zone_side", ""))
    zone_context = str(row.get("zone_position_context", ""))
    close_position = _raw_close_position(row)
    if label in BEARISH_RETEST_LABELS:
        return True
    if label == "UNCLEAR_FLOW_ANOMALY" and trend == "DOWN" and close_position <= 0.35:
        return True
    return label == "COMPRESSION_BEFORE_EXPANSION_CANDIDATE" and side == "BUY_SIDE" and zone_context in {
        "near_upper_zone",
        "inside_zone",
        "between_zones",
    }


def _is_supply_sweep_raw(row: pd.Series) -> bool:
    label = str(row.get("candidate_label", ""))
    side = str(row.get("nearest_zone_side", ""))
    zone_context = str(row.get("zone_position_context", ""))
    return side == "BUY_SIDE" and zone_context in {"near_upper_zone", "inside_zone", "between_zones"} and (
        label in SUPPLY_DOWN_RAW_LABELS or _float_value(row.get("delta_pct"), 0.0) <= -0.04
    )


def _is_demand_reclaim_raw(row: pd.Series) -> bool:
    label = str(row.get("candidate_label", ""))
    side = str(row.get("nearest_zone_side", ""))
    zone_context = str(row.get("zone_position_context", ""))
    return side == "SELL_SIDE" and zone_context in {"near_lower_zone", "inside_zone", "between_zones"} and (
        label in DEMAND_UP_RAW_LABELS
    )


def _is_breakout_up_raw(row: pd.Series) -> bool:
    label = str(row.get("candidate_label", ""))
    side = str(row.get("nearest_zone_side", ""))
    compression = _float_value(row.get("compression_score"), 0.0)
    close_position = _raw_close_position(row)
    return side == "BUY_SIDE" and label == "COMPRESSION_BEFORE_EXPANSION_CANDIDATE" and compression >= 50 and close_position >= 0.5


def _best_window(windows: pd.DataFrame, predicate) -> pd.Series | None:
    if windows.empty:
        return None
    matches = windows[windows.apply(predicate, axis=1)].copy()
    if matches.empty:
        return None
    matches["_candidate_score"] = pd.to_numeric(matches.get("candidate_score", 0), errors="coerce").fillna(0.0)
    matches["_compression_score"] = pd.to_numeric(matches.get("compression_score", 0), errors="coerce").fillna(0.0)
    return matches.sort_values(
        ["_candidate_score", "_compression_score", "_end_ts"],
        ascending=[False, False, False],
        kind="mergesort",
    ).iloc[0]


def _windows_for_state(windows: pd.DataFrame, state: pd.Series) -> pd.DataFrame:
    if windows.empty:
        return windows.copy()
    start_ts = state.get("_start_ts")
    end_ts = state.get("_end_ts")
    if pd.isna(start_ts) or pd.isna(end_ts):
        return windows.copy()
    return windows[(windows["_end_ts"] >= start_ts) & (windows["_end_ts"] <= end_ts)].copy()


def _prepare_windows(windows: pd.DataFrame) -> pd.DataFrame:
    if windows.empty:
        return windows
    out = windows.copy()
    out["_start_ts"] = pd.to_datetime(out.get("start_timestamp"), errors="coerce", utc=True)
    out["_end_ts"] = pd.to_datetime(out.get("end_timestamp"), errors="coerce", utc=True)
    return out




def _promoted_candidates_as_windows(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    frame = candidates.copy()
    out = pd.DataFrame()
    out["window_id"] = frame.get("source_window_id", frame.get("candidate_id", ""))
    out["start_timestamp"] = frame.get("start_timestamp", "")
    out["end_timestamp"] = frame.get("end_timestamp", "")
    out["window_minutes"] = frame.get("window_minutes", "")
    out["candidate_label"] = frame.get("candidate_label", "")
    out["confidence"] = frame.get("confidence", "")
    out["candidate_score"] = frame.get("candidate_score", 0.0)
    out["trend_direction"] = frame.get("trend_context", frame.get("trend_direction", ""))
    out["prior_trend_direction"] = frame.get("prior_trend_direction", "")
    out["nearest_zone_side"] = frame.get("nearest_zone_side", "")
    out["zone_position_context"] = frame.get("zone_position_context", "")
    out["compression_score"] = frame.get("compression_score", 0.0)
    out["delta_pct"] = frame.get("delta_pct", 0.0)
    out["range_pct"] = frame.get("range_pct", 0.0)
    out["close_location_in_window"] = frame.get("close_location_in_window", frame.get("close_position", 0.5))
    out["open_interest_change"] = frame.get("open_interest_change", 0.0)
    out["evidence_summary"] = frame.get("evidence_summary", "")
    return out

def _visible_zones(zones: pd.DataFrame) -> pd.DataFrame:
    if zones.empty:
        return zones
    if "visible_on_snapshot" not in zones.columns:
        return zones.copy()
    mask = zones["visible_on_snapshot"].astype(str).str.lower().isin({"true", "1", "yes"})
    return zones[mask].copy()


def _state_context(state: pd.Series) -> dict[str, object]:
    evidence = str(state.get("evidence_summary", ""))
    return {
        "dominant_side": _evidence_value(evidence, "dominant_side") or "UNKNOWN",
        "seller_pressure_score": _float_value(_evidence_value(evidence, "seller_pressure_score"), 0.0),
        "buyer_response_score": _float_value(_evidence_value(evidence, "buyer_response_score"), 0.0),
        "overhead_supply_score": _float_value(_evidence_value(evidence, "overhead_supply_score"), 0.0),
        "underlying_demand_score": _float_value(_evidence_value(evidence, "underlying_demand_score"), 0.0),
    }


def _target_reference_zone(zones: pd.DataFrame, side: str, price: float) -> str:
    if zones.empty:
        return ""
    frame = zones[zones.get("side", pd.Series(dtype=str)).astype(str) == side].copy()
    if frame.empty:
        return ""
    frame["_lower"] = pd.to_numeric(frame.get("price_lower"), errors="coerce")
    frame["_upper"] = pd.to_numeric(frame.get("price_upper"), errors="coerce")
    if side == "BUY_SIDE":
        candidates = frame[frame["_lower"] >= price] if not pd.isna(price) else frame
        if candidates.empty:
            candidates = frame
        row = candidates.sort_values(["_lower", "_upper"], kind="mergesort").iloc[0]
    else:
        candidates = frame[frame["_upper"] <= price] if not pd.isna(price) else frame
        if candidates.empty:
            candidates = frame
        row = candidates.sort_values(["_upper", "_lower"], ascending=[False, False], kind="mergesort").iloc[0]
    return f"{_cell(row.get('zone_id'))}:{side}:{_round(row.get('_lower'))}-{_round(row.get('_upper'))}"




def _formed_at(state: pd.Series, raw: pd.Series | None) -> str:
    if raw is not None:
        return _cell(raw.get("end_timestamp"))
    return _cell(state.get("end_timestamp"))


def _source_window_start(state: pd.Series, raw: pd.Series | None) -> str:
    if raw is not None:
        return _cell(raw.get("start_timestamp"))
    return _cell(state.get("start_timestamp"))


def _source_window_end(state: pd.Series, raw: pd.Series | None) -> str:
    if raw is not None:
        return _cell(raw.get("end_timestamp"))
    return _cell(state.get("end_timestamp"))


def _source_time_precision(raw: pd.Series | None) -> str:
    if raw is None:
        return "STATE_WINDOW"
    minutes = _float_value(raw.get("window_minutes") if hasattr(raw, "get") else "")
    if not pd.isna(minutes) and minutes > 0:
        return f"RAW_REGIME_WINDOW_{int(minutes)}M"
    return "RAW_REGIME_WINDOW"

def _evidence_summary(state: pd.Series, raw: pd.Series | None, note: str) -> str:
    parts = [
        note,
        f"market_state={_cell(state.get('market_state'))}",
        f"state_end={_cell(state.get('end_timestamp'))}",
    ]
    if raw is not None:
        parts.extend(
            [
                f"raw_window={_cell(raw.get('window_id'))}",
                f"raw_label={_cell(raw.get('candidate_label'))}",
                f"raw_end={_cell(raw.get('end_timestamp'))}",
            ]
        )
    else:
        parts.append("raw_window=none")
    parts.append("future_labels_not_used")
    return "; ".join(parts)


def _write_outputs(
    *,
    candidates: pd.DataFrame,
    candidates_path: Path,
    manifest_path: Path,
    summary_path: Path,
    state_path: Path,
    windows_path: Path,
    zones_path: Path,
    hidden_path: Path | None,
    optional_hidden_loaded: bool,
    missing_inputs: list[str],
) -> None:
    candidates.reindex(columns=SETUP_BUILDER_COLUMNS).to_csv(candidates_path, index=False)
    manifest = {
        "setup_builder_version": SETUP_BUILDER_VERSION,
        "research_only": True,
        "uses_future_data": False,
        "uses_backtester": False,
        "uses_executor": False,
        "output_is_trading_signal": False,
        "setup_candidates_require_replay": True,
        "state_timeline_path": str(state_path),
        "regime_windows_path": str(windows_path),
        "selected_zones_path": str(zones_path),
        "optional_hidden_flow_candidates_path": str(hidden_path) if hidden_path is not None else "",
        "optional_promoted_hidden_flow_candidates_loaded": optional_hidden_loaded,
        "missing_inputs": missing_inputs,
        "candidate_count": int(len(candidates)),
        "allowed_trigger_status": sorted(TRIGGER_STATUS_VALUES),
        "outputs": {
            "setup_research_timeline_csv": str(candidates_path),
            "manifest_json": str(manifest_path),
            "summary_md": str(summary_path),
        },
        "repo_commit": _repo_commit(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    summary_path.write_text(_summary_text(candidates, missing_inputs), encoding="utf-8")


def _summary_text(candidates: pd.DataFrame, missing_inputs: list[str]) -> str:
    counts = candidates["setup_type"].value_counts().to_dict() if not candidates.empty else {}
    return "\n".join(
        [
            "# Setup Builder Summary",
            "",
            "Research-only setup candidates generated from as-of Market Monitor artifacts.",
            "",
            f"- Version: {SETUP_BUILDER_VERSION}",
            f"- Candidates: {len(candidates)}",
            f"- Setup type counts: {json.dumps(counts, sort_keys=True)}",
            f"- Missing inputs: {json.dumps(missing_inputs)}",
            "- Future labels are not used for detection.",
            "- Replay required before any interpretation beyond research context.",
            "",
        ]
    )


def _assert_no_forbidden_output(candidates: pd.DataFrame) -> None:
    text = candidates.to_csv(index=False)
    found = sorted(term for term in FORBIDDEN_OUTPUT_TERMS if term in text)
    if found:
        raise ValueError(f"forbidden setup-builder output terms: {found}")


def _read_csv(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _evidence_value(evidence: str, key: str) -> str:
    match = re.search(rf"{re.escape(key)}=([^;]+)", evidence)
    return match.group(1).strip() if match else ""


def _raw_close_position(row: pd.Series | None) -> float:
    if row is None:
        return float("nan")
    return _float_value(row.get("close_location_in_window"), _float_value(row.get("close_position"), float("nan")))


def _countertrend(dominant_side: object, direction: str) -> str:
    side = str(dominant_side)
    if direction == "UP":
        return "true" if side == "SELLER" else "false"
    if direction == "DOWN":
        return "true" if side == "BUYER" else "false"
    return "false"


def _float_value(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if pd.notna(number) else default


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""
