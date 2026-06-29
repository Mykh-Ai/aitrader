from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.setup_builder import SETUP_BUILDER_COLUMNS, run_setup_builder


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


def test_seller_dominant_state_and_bearish_raw_window_create_down_setup(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_seller_state(), windows=[_bearish_window()], candidates=[])

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        hidden_flow_candidates_path=paths["candidates"],
        output_dir=tmp_path / "out",
    )

    setups = pd.read_csv(result.candidates_path)

    assert setups.columns.tolist() == SETUP_BUILDER_COLUMNS
    assert len(setups) == 1
    row = setups.iloc[0]
    assert row["setup_type"] == "SELLER_DOMINANCE_RETEST_DOWN_SETUP"
    assert row["direction_context"] == "DOWN"
    assert row["trigger_status"] == "ARMED"
    assert row["setup_formed_at"] == "2026-03-26T08:59:00+00:00"
    assert row["source_window_start"] == "2026-03-26T05:00:00+00:00"
    assert row["source_window_end"] == "2026-03-26T08:59:00+00:00"
    assert row["source_time_precision"] == "RAW_REGIME_WINDOW_240M"
    assert row["dominant_side"] == "SELLER"
    assert row["seller_pressure_score"] == 93.3
    assert row["buyer_response_score"] == 5.7
    assert row["nearest_zone_side"] == "SELL_SIDE"
    assert row["zone_position_context"] == "inside_zone"
    assert row["target_reference_zone"].startswith("zone_demand:SELL_SIDE:")
    assert "research-only trigger" in row["evidence_summary"]


def test_downtrend_exhaustion_near_demand_creates_up_watch_not_triggered(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_demand_state(), windows=[_exhaustion_window()], candidates=[])

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
    )

    row = pd.read_csv(result.candidates_path).iloc[0]

    assert row["setup_type"] == "DEMAND_SWEEP_RECLAIM_UP_SETUP"
    assert row["direction_context"] == "UP"
    assert str(row["countertrend_flag"]).lower() == "true"
    assert row["trigger_status"] in {"WATCH", "ARMED"}
    assert row["trigger_status"] != "TRIGGERED"
    assert row["setup_formed_at"] == "2026-03-26T08:59:00+00:00"
    assert row["source_time_precision"] == "RAW_REGIME_WINDOW_240M"
    assert row["nearest_zone_side"] == "SELL_SIDE"
    assert row["target_reference_zone"].startswith("zone_supply:BUY_SIDE:")




def test_state_only_context_creates_watch_not_armed_or_triggered(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_seller_state(), windows=[], candidates=[])

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
    )

    row = pd.read_csv(result.candidates_path).iloc[0]

    assert result.candidates_path.name == "setup_research_timeline.csv"
    assert row["setup_type"] == "SELLER_DOMINANCE_RETEST_DOWN_SETUP"
    assert row["trigger_status"] == "WATCH"
    assert row["setup_formed_at"] == "2026-03-26T09:00:00Z"
    assert row["source_window_start"] == "2026-03-26T00:00:00Z"
    assert row["source_window_end"] == "2026-03-26T09:00:00Z"
    assert row["source_time_precision"] == "STATE_WINDOW"

def test_empty_promoted_hidden_flow_candidates_do_not_block_setup_creation(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_seller_state(), windows=[_bearish_window()], candidates=[])

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        hidden_flow_candidates_path=paths["candidates"],
        output_dir=tmp_path / "out",
    )

    setups = pd.read_csv(result.candidates_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert len(setups) == 1
    assert manifest["optional_promoted_hidden_flow_candidates_loaded"] is True
    assert manifest["candidate_count"] == 1


def test_future_labels_are_not_used_for_detection(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_neutral_state(), windows=[], candidates=[])
    future_path = tmp_path / "hidden_flow_future_labels.csv"
    pd.DataFrame(
        [
            {
                "candidate_id": "future_only",
                "impulse_direction_label": "FUTURE_EXPANSION_DOWN",
                "future_window_minutes": 240,
            }
        ]
    ).to_csv(future_path, index=False)

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
    )

    setups = pd.read_csv(result.candidates_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert setups.empty
    assert manifest["uses_future_data"] is False
    assert "hidden_flow_future_labels" not in json.dumps(manifest)


def test_forbidden_execution_like_labels_do_not_appear_in_outputs(tmp_path: Path):
    paths = _write_fixture(tmp_path, state=_seller_state(), windows=[_bearish_window()], candidates=[])

    result = run_setup_builder(
        state_timeline_path=paths["state"],
        regime_windows_path=paths["windows"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
    )

    output_text = result.candidates_path.read_text(encoding="utf-8")
    output_text += result.summary_path.read_text(encoding="utf-8")
    output_text += result.manifest_path.read_text(encoding="utf-8")

    assert not any(term in output_text for term in FORBIDDEN_OUTPUT_TERMS)


def test_missing_required_inputs_write_empty_deterministic_csv_and_manifest(tmp_path: Path):
    out = tmp_path / "out"

    result = run_setup_builder(
        state_timeline_path=tmp_path / "missing_state.csv",
        regime_windows_path=tmp_path / "missing_windows.csv",
        selected_zones_path=tmp_path / "missing_zones.csv",
        output_dir=out,
    )

    setups = pd.read_csv(result.candidates_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert setups.empty
    assert setups.columns.tolist() == SETUP_BUILDER_COLUMNS
    assert manifest["candidate_count"] == 0
    assert manifest["missing_inputs"]


def _write_fixture(
    tmp_path: Path,
    *,
    state: dict[str, object],
    windows: list[dict[str, object]],
    candidates: list[dict[str, object]],
) -> dict[str, Path]:
    state_path = tmp_path / "market_structure_state_timeline.csv"
    windows_path = tmp_path / "market_regime_windows.csv"
    zones_path = tmp_path / "selected_zones.csv"
    candidates_path = tmp_path / "hidden_flow_candidates.csv"

    pd.DataFrame([state]).to_csv(state_path, index=False)
    pd.DataFrame(windows, columns=_window_columns()).to_csv(windows_path, index=False)
    pd.DataFrame(
        [
            _zone("zone_demand", "SELL_SIDE", 70040.46225, 70110.53775, 70075.5),
            _zone("zone_supply", "BUY_SIDE", 71341.81125, 71413.18875, 71377.5),
            _zone("zone_supply_next", "BUY_SIDE", 72000.0, 72100.0, 72050.0),
        ]
    ).to_csv(zones_path, index=False)
    pd.DataFrame(candidates).to_csv(candidates_path, index=False)
    return {"state": state_path, "windows": windows_path, "zones": zones_path, "candidates": candidates_path}


def _seller_state() -> dict[str, object]:
    return {
        "start_timestamp": "2026-03-26T00:00:00Z",
        "end_timestamp": "2026-03-26T09:00:00Z",
        "market_state": "PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE",
        "candidate_strength": "MEDIUM",
        "price_close": 69985.9,
        "active_support_price_lower": 68850.05775,
        "active_support_price_upper": 69879.22215,
        "active_resistance_price_lower": 71341.81125,
        "active_resistance_price_upper": 71413.18875,
        "price_change_pct": -1.830115,
        "range_pct": 2.417437,
        "close_position": 0.1562,
        "delta_pct": -6.420618,
        "open_interest_change": 663.6,
        "evidence_summary": (
            "seller_pressure_score=93.3; buyer_response_score=5.7; "
            "overhead_supply_score=98.8; underlying_demand_score=98.2; "
            "dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present"
        ),
    }


def _demand_state() -> dict[str, object]:
    return {
        **_seller_state(),
        "market_state": "MARKDOWN_ABOVE_SUPPORT",
        "price_close": 70120.0,
        "close_position": 0.42,
        "evidence_summary": (
            "seller_pressure_score=58.0; buyer_response_score=38.0; "
            "overhead_supply_score=40.0; underlying_demand_score=92.0; "
            "dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present"
        ),
    }




def _neutral_state() -> dict[str, object]:
    return {
        **_seller_state(),
        "market_state": "BALANCED_RANGE_BETWEEN_LEVELS",
        "close_position": 0.52,
        "evidence_summary": (
            "seller_pressure_score=20.0; buyer_response_score=22.0; "
            "overhead_supply_score=35.0; underlying_demand_score=35.0; "
            "dominant_side=MIXED; range_quality=BALANCED; support_context=present; resistance_context=present"
        ),
    }

def _bearish_window() -> dict[str, object]:
    return {
        "window_id": "window_000001",
        "start_timestamp": "2026-03-26T05:00:00+00:00",
        "end_timestamp": "2026-03-26T08:59:00+00:00",
        "candidate_label": "UNCLEAR_FLOW_ANOMALY",
        "confidence": "LOW",
        "window_minutes": 240,
        "candidate_score": 69.888,
        "trend_direction": "DOWN",
        "prior_trend_direction": "DOWN",
        "nearest_zone_side": "SELL_SIDE",
        "zone_position_context": "inside_zone",
        "compression_score": 28.593,
        "delta_pct": -0.061365,
        "range_pct": 1.477303,
        "close_location_in_window": 0.2389,
        "open_interest_change": 154.1,
        "evidence_summary": "raw bearish pressure window",
    }


def _exhaustion_window() -> dict[str, object]:
    return {
        **_bearish_window(),
        "candidate_label": "DOWNTREND_EXHAUSTION_CANDIDATE",
        "confidence": "HIGH",
        "candidate_score": 83.688,
        "trend_direction": "RANGE",
        "delta_pct": 0.079974,
        "close_location_in_window": 0.8123,
        "open_interest_change": 394.78,
        "evidence_summary": "raw exhaustion near demand",
    }


def _zone(zone_id: str, side: str, lower: float, upper: float, representative: float) -> dict[str, object]:
    return {
        "zone_id": zone_id,
        "side": side,
        "price_lower": lower,
        "price_upper": upper,
        "representative_price": representative,
        "visible_on_snapshot": "true",
        "bucket": "MAJOR",
    }


def _window_columns() -> list[str]:
    return [
        "window_id",
        "start_timestamp",
        "end_timestamp",
        "candidate_label",
        "confidence",
        "candidate_score",
        "window_minutes",
        "trend_direction",
        "prior_trend_direction",
        "nearest_zone_side",
        "zone_position_context",
        "compression_score",
        "delta_pct",
        "range_pct",
        "close_location_in_window",
        "open_interest_change",
        "evidence_summary",
    ]
