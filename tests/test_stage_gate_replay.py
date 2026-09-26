from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.run_sequence_window_h1_replay import run_sequence_window_replay
from market_monitor.run_stage_gate_replay import build_stage_gate_frames


def test_stage_gate_allows_policy_only_after_valid_sequence(tmp_path: Path):
    classification = pd.DataFrame([_setup()])
    h1 = _h1_sequence()
    events, links = run_sequence_window_replay(classification=classification, h1=h1, lookback_h1_bars=8)
    _write_feed(tmp_path)

    frames = build_stage_gate_frames(
        classification=classification,
        sequence_events=events,
        sequence_links=links,
        feed_dir=tmp_path,
        replay_end_ts=pd.Timestamp("2026-05-26T23:59:00Z"),
    )

    setup_row = frames["setup_rows"].iloc[0]
    assert setup_row["stage_5_policy_replay_allowed"] == "true"
    assert setup_row["tradable_entry_anchor"] == 98.8
    assert setup_row["setup_formed_at"] == "2026-05-26T16:59:00+00:00"
    assert len(frames["policy_results"]) == 2
    assert set(frames["policy_results"]["entry_candidate_ts"]) == {"2026-05-26T15:59:00Z"}
    assert set(frames["policy_results"]["entry_candidate_price"]) == {98.8}
    assert not frames["failures"].shape[0]


def test_raw_context_without_qualified_sequence_cannot_enter_policy(tmp_path: Path):
    classification = pd.DataFrame([_setup(setup_id="setup_raw", setup_formed_at="2026-05-26T12:59:00+00:00")])
    h1 = _h1_sequence_without_sweep()
    events, links = run_sequence_window_replay(classification=classification, h1=h1, lookback_h1_bars=8)
    _write_feed(tmp_path)

    frames = build_stage_gate_frames(
        classification=classification,
        sequence_events=events,
        sequence_links=links,
        feed_dir=tmp_path,
        replay_end_ts=pd.Timestamp("2026-05-26T23:59:00Z"),
    )

    setup_row = frames["setup_rows"].iloc[0]
    failure = frames["failures"].iloc[0]
    assert setup_row["stage_1_raw_context_or_raw_sweep"] == "true"
    assert setup_row["stage_5_policy_replay_allowed"] == "false"
    assert setup_row["immediate_entry_valid"] == "false"
    assert setup_row["policy_replay_allowed"] == "false"
    assert failure["failed_stage"] == "STAGE_2_QUALIFIED_H1_SWEEP"
    assert frames["policy_results"].empty


def _setup(setup_id: str = "setup_primary", setup_formed_at: str = "2026-05-26T16:59:00+00:00") -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "setup_formed_at": setup_formed_at,
        "setup_type": "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
        "direction_context": "DOWN",
        "trigger_status": "ARMED",
        "source_time_precision": "RAW_REGIME_WINDOW_720M",
        "market_state": "MARKDOWN_ABOVE_SUPPORT",
        "setup_reference_level": 100.0,
        "actual_setup_price": 97.0,
        "target_reference": 94.0,
        "selected_research_stop_reference": 101.0,
        "selected_research_stop_type": "local_swing_stop",
        "source_window_start": "2026-05-26T06:59:00Z",
        "manual_corrected_classification": "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP",
        "setup_role_classification": "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP",
        "evidence_summary": "raw_window=NORMALIZATION_AFTER_MARKDOWN; future_labels_not_used",
    }


def _h1_sequence() -> pd.DataFrame:
    rows = []
    ts = pd.Timestamp("2026-05-26T00:59:00Z")
    while ts < pd.Timestamp("2026-05-26T14:59:00Z"):
        rows.append({"timestamp": ts, "open": 99.0, "high": 99.6, "low": 95.0, "close": 95.5, "volume": 100.0, "completed": True})
        ts += pd.Timedelta(hours=1)
    rows.append({"timestamp": pd.Timestamp("2026-05-26T14:59:00Z"), "open": 99.8, "high": 101.2, "low": 99.0, "close": 99.5, "volume": 180.0, "completed": True})
    rows.append({"timestamp": pd.Timestamp("2026-05-26T15:59:00Z"), "open": 100.1, "high": 99.8, "low": 98.0, "close": 98.8, "volume": 140.0, "completed": True})
    rows.append({"timestamp": pd.Timestamp("2026-05-26T16:59:00Z"), "open": 98.8, "high": 99.4, "low": 96.0, "close": 97.0, "volume": 120.0, "completed": True})
    return pd.DataFrame(rows)


def _h1_sequence_without_sweep() -> pd.DataFrame:
    rows = []
    ts = pd.Timestamp("2026-05-26T04:59:00Z")
    while ts <= pd.Timestamp("2026-05-26T12:59:00Z"):
        rows.append({"timestamp": ts, "open": 98.0, "high": 99.0, "low": 96.0, "close": 97.0, "volume": 100.0, "completed": True})
        ts += pd.Timedelta(hours=1)
    return pd.DataFrame(rows)


def _write_feed(root: Path) -> None:
    rows = [
        {"Timestamp": "2026-05-26T16:00:00Z", "Open": 98.8, "High": 99.0, "Low": 93.8, "Close": 94.5, "Volume": 1},
        {"Timestamp": "2026-05-26T17:00:00Z", "Open": 94.5, "High": 95.0, "Low": 93.0, "Close": 94.0, "Volume": 1},
    ]
    pd.DataFrame(rows).to_csv(root / "2026-05-26.csv", index=False)

def test_sequence_linked_short_stop_uses_sweep_high_when_structural_stop_inside_sweep(tmp_path: Path):
    classification = pd.DataFrame([_setup()])
    h1 = _h1_sequence()
    events, links = run_sequence_window_replay(classification=classification, h1=h1, lookback_h1_bars=8)
    _write_feed(tmp_path)

    frames = build_stage_gate_frames(
        classification=classification,
        sequence_events=events,
        sequence_links=links,
        feed_dir=tmp_path,
        replay_end_ts=pd.Timestamp("2026-05-26T23:59:00Z"),
    )

    policy = frames["policy_results"]
    tp1 = policy[policy["policy_name"] == "TP1_BE_WITH_SELECTED_STOP_POLICY"].iloc[0]

    assert tp1["selected_stop_reference"] == 101.2
    assert tp1["selected_stop_type"] == "sweep_h1_high_stop"
    assert tp1["stop_distance_usd"] == 2.4
    assert tp1["tp1_price"] == 96.4
    assert "INVALID_STOP_INSIDE_SWEEP_RANGE" in tp1["evidence_summary"]
