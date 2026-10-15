from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

FAMILIES = {"SELLER_DOMINANCE_RETEST_DOWN", "SUPPLY_SWEEP_RECLAIM_DOWN", "DEMAND_SWEEP_RECLAIM_UP"}


def load_contract(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(config)
    return config


def contract_hash(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_contract(config: dict) -> None:
    if set(config["families"]) != FAMILIES or len(config["families"]) != 3:
        raise ValueError("Exactly three frozen research families required")
    if config["live_execution"] or config["strategy_promotion"] or config["automatic_parameter_search"]:
        raise ValueError("Offline bounded research only")
    if config["timestamp_semantics"] != "RAW_MINUTE_CLOSE_UTC" or config["entry_latency_minutes"] != 1:
        raise ValueError("Unsupported clock contract")
    if config["exit_policy"] != "FULL_FROZEN_STRUCTURAL_TARGET_OR_STOP_OR_48H_EXPIRY" or config["expiry_hours"] != 48:
        raise ValueError("Unsupported exit experiment")
    if config["same_bar_policy"] != "STOP_FIRST":
        raise ValueError("Conservative ambiguity policy required")
    if config.get("minute_quality_policy") != "SKIP_PRIMARY_BAD_ROW_TOLERATE_ISOLATED_ONE_MINUTE" or config.get("maximum_consecutive_omitted_minutes") != 1:
        raise ValueError("Explicit user-directed single-minute tolerance required")
    if pd.Timestamp(config["source_start"]) >= pd.Timestamp(config["source_cutoff"]):
        raise ValueError("Invalid source interval")
    if any(not math.isfinite(config[k]) or config[k] <= 0 for k in ["warmup_hours", "state_window_minutes", "h1_swing_left_right", "h4_swing_left_right", "zone_half_width_bps", "level_max_age_days", "volume_median_bars", "minimum_target_r", "minimum_risk_atr_fraction"]):
        raise ValueError("Positive research thresholds required")
    if config["reclaim_window_hours"] != 3 or config["accepted_break_closes"] != 2 or config["stop_buffer_bps"] != 1:
        raise ValueError("Unsupported lifecycle/stop variant")
    if len(config["cost_scenarios"]) != 3 or len({x["id"] for x in config["cost_scenarios"]}) != 3:
        raise ValueError("Three distinct cost scenarios required")
    for cost in config["cost_scenarios"]:
        if any(not 0 <= cost[k] < 1000 for k in ["fee_bps_per_fill", "slippage_bps_per_fill", "adverse_carry_bps_per_hour"]):
            raise ValueError("Invalid cost assumption")
    last_end = None
    for period in config["periods"]:
        begin, end = pd.Timestamp(period["start"]), pd.Timestamp(period["end"])
        if begin.tzinfo is None or end.tzinfo is None or begin >= end or (last_end is not None and begin != last_end):
            raise ValueError("Contiguous, ordered, UTC evaluation periods required")
        if "CONTEXT_ONLY" in period["name"] and "PURGE" in period["name"] and end - begin < pd.Timedelta(hours=config["expiry_hours"]):
            raise ValueError("Purge shorter than maximum holding horizon")
        last_end = end


def validate_signal(signal: dict, config: dict) -> None:
    if signal["family"] not in FAMILIES or signal["direction"] not in {"LONG", "SHORT"}:
        raise ValueError("Unknown family/direction")
    expected = "LONG" if signal["family"] == "DEMAND_SWEEP_RECLAIM_UP" else "SHORT"
    if signal["direction"] != expected:
        raise ValueError("Family direction mismatch")
    decision, entry = pd.Timestamp(signal["decision_at"]), pd.Timestamp(signal["entry_open_at"])
    if decision.tzinfo is None or entry.tzinfo is None:
        raise ValueError("Explicit UTC timestamps required")
    if entry != decision + pd.Timedelta(minutes=config["entry_latency_minutes"]):
        raise ValueError("Entry clock mismatch")
    for field in ["available_at", "state_end", "flow_end", "source_level_available_at", "target_level_available_at"]:
        value = pd.Timestamp(signal[field])
        if value.tzinfo is None or value > decision:
            raise ValueError(f"Unavailable evidence: {field}")
    sweep_value = signal.get("sweep_at")
    if pd.notna(sweep_value) and str(sweep_value).strip():
        sweep = pd.Timestamp(sweep_value)
        reclaim_close = pd.Timestamp(signal.get("h1_close_at", signal["decision_at"]))
        if reclaim_close > decision or not pd.Timedelta(hours=1) <= reclaim_close - sweep <= pd.Timedelta(hours=config["reclaim_window_hours"]):
            raise ValueError("Reclaim outside next 1-3 H1 closes")
        if signal["direction"] == "SHORT" and signal["stop_price"] < signal["sweep_high"]:
            raise ValueError("Short stop inside sweep")
        if signal["direction"] == "LONG" and signal["stop_price"] > signal["sweep_low"]:
            raise ValueError("Long stop inside sweep")
    elif "SWEEP_RECLAIM" in signal["family"]:
        raise ValueError("Sweep family requires sequence evidence")
    price, stop, target = (float(signal[x]) for x in ["decision_price", "stop_price", "target_price"])
    valid = stop < price < target if signal["direction"] == "LONG" else target < price < stop
    if not valid:
        raise ValueError("Invalid signal stop/target geometry")
