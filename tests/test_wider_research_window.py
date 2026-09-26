from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.wider_research_window import run_wider_research_window


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


def test_actual_setup_price_is_tradable_anchor_not_setup_reference_level(tmp_path: Path):
    paths = _write_fixture(
        tmp_path,
        setups=[
            _setup(
                setup_id="setup_down",
                setup_type="SELLER_DOMINANCE_RETEST_DOWN_SETUP",
                setup_formed_at="2026-06-01T00:03:00Z",
                trigger_status="ARMED",
                source_time_precision="RAW_REGIME_WINDOW_60M",
                setup_reference_level=105.0,
                target_reference_zone="zone_demand:SELL_SIDE:90-92",
                stop_reference=106.0,
            )
        ],
    )

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    row = pd.read_csv(result.classification_path).iloc[0]

    assert row["setup_reference_level"] == 105.0
    assert row["actual_setup_price"] == 100.0
    assert row["tradable_entry_anchor"] == 100.0
    assert row["setup_reference_level"] != row["tradable_entry_anchor"]
    assert row["setup_role_classification"] == "STRUCTURAL_RETEST_TRIGGER_CANDIDATE"
    assert str(row["policy_replay_allowed"]).lower() == "true"


def test_broad_raw_window_is_context_not_immediate_entry_or_policy(tmp_path: Path):
    paths = _write_fixture(
        tmp_path,
        setups=[
            _setup(
                setup_id="setup_broad",
                setup_type="SELLER_DOMINANCE_RETEST_DOWN_SETUP",
                trigger_status="ARMED",
                source_time_precision="RAW_REGIME_WINDOW_1440M",
                source_window_start="2026-06-01T00:00:00Z",
                source_window_end="2026-06-01T23:59:00Z",
                target_reference_zone="zone_demand:SELL_SIDE:90-92",
                stop_reference=106.0,
            )
        ],
    )

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    classification = pd.read_csv(result.classification_path)
    policy = pd.read_csv(result.policy_replay_path)
    row = classification.iloc[0]

    assert row["setup_role_classification"] == "PRE_TRIGGER_CONTEXT"
    assert str(row["immediate_entry_valid"]).lower() == "false"
    assert str(row["policy_replay_allowed"]).lower() == "false"
    assert policy.iloc[0]["policy_outcome_label"] == "POLICY_NOT_APPLIED_CONTEXT_ONLY"


def test_local_swing_stop_wins_over_source_window_context_stop(tmp_path: Path):
    paths = _write_fixture(
        tmp_path,
        setups=[
            _setup(
                setup_id="setup_stop",
                setup_type="SELLER_DOMINANCE_RETEST_DOWN_SETUP",
                setup_formed_at="2026-06-01T00:03:00Z",
                trigger_status="ARMED",
                source_time_precision="RAW_REGIME_WINDOW_60M",
                target_reference_zone="zone_demand:SELL_SIDE:90-92",
                stop_reference=106.0,
            )
        ],
        include_zone_above_entry=False,
    )

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    stop = pd.read_csv(result.structural_stops_path).iloc[0]

    assert stop["source_window_stop_type"] == "source_window_stop_context_only"
    assert stop["selected_research_stop_type"] == "local_swing_stop"
    assert stop["selected_research_stop_reference"] == 104.0
    assert stop["source_window_stop_reference"] == 104.0


def test_selected_stop_before_tp1_is_terminal_in_tp1_be_policy(tmp_path: Path):
    paths = _write_fixture(
        tmp_path,
        setups=[
            _setup(
                setup_id="setup_tp1",
                setup_type="SELLER_DOMINANCE_RETEST_DOWN_SETUP",
                setup_formed_at="2026-06-01T00:03:00Z",
                trigger_status="ARMED",
                source_time_precision="RAW_REGIME_WINDOW_60M",
                target_reference_zone="zone_demand:SELL_SIDE:90-92",
                stop_reference=103.0,
            )
        ],
        forward_rows=[
            {"timestamp": "2026-06-01T00:04:00Z", "open": 100, "high": 104.5, "low": 99, "close": 102},
            {"timestamp": "2026-06-01T00:05:00Z", "open": 102, "high": 102, "low": 92, "close": 94},
        ],
        include_zone_above_entry=False,
    )

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    policy = pd.read_csv(result.policy_replay_path)
    tp1 = policy[policy["policy_name"] == "TP1_BE_WITH_SELECTED_STOP_POLICY"].iloc[0]

    assert tp1["policy_outcome_label"] == "NO_TP1_SELECTED_STOP"
    assert tp1["selected_stop_touched_at"] == "2026-06-01T00:04:00Z"
    assert tp1["tp1_touched_at"] == "2026-06-01T00:05:00Z"


def test_forbidden_execution_like_terms_do_not_appear(tmp_path: Path):
    paths = _write_fixture(tmp_path, setups=[_setup(setup_id="setup_context", trigger_status="WATCH")])

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    output_text = ""
    for path in [
        result.setup_timeline_path,
        result.classification_path,
        result.structural_stops_path,
        result.policy_replay_path,
        result.manual_review_path,
        result.summary_path,
        result.manifest_path,
    ]:
        output_text += path.read_text(encoding="utf-8")

    assert not any(term in output_text for term in FORBIDDEN_OUTPUT_TERMS)

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["research_only"] is True
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False
    assert manifest["uses_future_labels"] is False
    assert manifest["changes_setup_detection"] is False


def _write_fixture(
    tmp_path: Path,
    *,
    setups: list[dict[str, object]],
    forward_rows: list[dict[str, object]] | None = None,
    include_zone_above_entry: bool = True,
) -> dict[str, Path]:
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    feed_rows = [
        {"timestamp": "2026-06-01T00:00:00Z", "open": 100, "high": 104, "low": 99, "close": 101},
        {"timestamp": "2026-06-01T00:01:00Z", "open": 101, "high": 103, "low": 98, "close": 99},
        {"timestamp": "2026-06-01T00:02:00Z", "open": 99, "high": 102, "low": 97, "close": 98},
        {"timestamp": "2026-06-01T00:03:00Z", "open": 98, "high": 101, "low": 96, "close": 100},
    ]
    feed_rows.extend(forward_rows or [])
    pd.DataFrame(feed_rows).to_csv(feed_dir / "2026-06-01.csv", index=False)

    setup_path = tmp_path / "setup_research_timeline.csv"
    pd.DataFrame(setups).to_csv(setup_path, index=False)

    zones = [_zone("zone_demand", "SELL_SIDE", 90.0, 92.0)]
    if include_zone_above_entry:
        zones.append(_zone("zone_supply", "BUY_SIDE", 105.0, 107.0))
    pd.DataFrame(zones).to_csv(tmp_path / "selected_zones.csv", index=False)
    return {"feed_dir": feed_dir, "setups": setup_path, "zones": tmp_path / "selected_zones.csv"}


def _setup(
    *,
    setup_id: str,
    setup_type: str = "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
    setup_formed_at: str = "2026-06-01T00:03:00Z",
    trigger_status: str = "ARMED",
    source_time_precision: str = "STATE_WINDOW",
    source_window_start: str = "2026-06-01T00:00:00Z",
    source_window_end: str = "2026-06-01T00:03:00Z",
    setup_reference_level: float = 101.0,
    target_reference_zone: str = "zone_demand:SELL_SIDE:90-92",
    stop_reference: float = 106.0,
) -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "start_timestamp": source_window_start,
        "end_timestamp": source_window_end,
        "setup_formed_at": setup_formed_at,
        "source_window_start": source_window_start,
        "source_window_end": source_window_end,
        "source_time_precision": source_time_precision,
        "setup_type": setup_type,
        "direction_context": "DOWN",
        "countertrend_flag": "false",
        "trigger_status": trigger_status,
        "market_state": "MARKDOWN_ABOVE_SUPPORT",
        "dominant_side": "SELLER",
        "candidate_strength": "MEDIUM",
        "nearest_zone_side": "BUY_SIDE",
        "zone_position_context": "below_zone",
        "setup_reference_level": setup_reference_level,
        "entry_reference_level": setup_reference_level,
        "invalidation_level": stop_reference,
        "stop_reference": stop_reference,
        "target_reference_zone": target_reference_zone,
        "evidence_summary": "research-only setup candidate fixture",
    }


def _zone(zone_id: str, side: str, lower: float, upper: float) -> dict[str, object]:
    return {
        "zone_id": zone_id,
        "side": side,
        "price_lower": lower,
        "price_upper": upper,
        "representative_price": (lower + upper) / 2,
        "visible_on_snapshot": "true",
    }
