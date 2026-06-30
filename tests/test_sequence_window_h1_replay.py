from __future__ import annotations

import pandas as pd

from market_monitor.run_sequence_window_h1_replay import run_sequence_window_replay


def test_sequence_window_links_pre_setup_qualified_reclaim():
    h1 = _h1_sequence(entry_offset_hours=2)
    classification = pd.DataFrame(
        [
            _setup(
                setup_id="setup_primary",
                setup_formed_at="2026-05-26T16:59:00+00:00",
                manual="MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP",
            )
        ]
    )

    events, links = run_sequence_window_replay(classification=classification, h1=h1, lookback_h1_bars=8)

    link = links.iloc[0]
    assert not events.empty
    assert link["qualified_sequence_found"] == "true"
    assert link["qualified_h1_sweep_ts"] == "2026-05-26T14:59:00Z"
    assert link["entry_candidate_ts"] == "2026-05-26T15:59:00Z"
    assert link["sequence_age_h1_bars_at_setup"] == 1.0
    assert link["sequence_valid_for_setup"] == "true"
    assert link["manual_match_status"] == "MATCH"


def test_sequence_window_marks_old_qualified_reclaim_as_late_review():
    h1 = _h1_sequence(entry_offset_hours=5)
    classification = pd.DataFrame(
        [
            _setup(
                setup_id="setup_late",
                setup_formed_at="2026-05-26T20:59:00+00:00",
                manual="LATE_LAST_WAGON",
            )
        ]
    )

    _, links = run_sequence_window_replay(classification=classification, h1=h1, lookback_h1_bars=8)

    link = links.iloc[0]
    assert link["qualified_sequence_found"] == "true"
    assert link["sequence_valid_for_setup"] == "false"
    assert link["sequence_reject_reason"] == "qualified_sequence_too_old_for_primary_setup"
    assert link["manual_match_status"] == "MATCH_CONTROL"


def _h1_sequence(*, entry_offset_hours: int) -> pd.DataFrame:
    rows = []
    ts = pd.Timestamp("2026-05-26T00:59:00Z")
    while ts < pd.Timestamp("2026-05-26T14:59:00Z"):
        rows.append(
            {
                "timestamp": ts,
                "open": 99.0,
                "high": 99.8,
                "low": 95.0,
                "close": 95.5,
                "volume": 100.0,
                "completed": True,
            }
        )
        ts += pd.Timedelta(hours=1)
    rows.append(
        {
            "timestamp": pd.Timestamp("2026-05-26T14:59:00Z"),
            "open": 99.8,
            "high": 101.2,
            "low": 99.0,
            "close": 99.5,
            "volume": 180.0,
            "completed": True,
        }
    )
    rows.append(
        {
            "timestamp": pd.Timestamp("2026-05-26T15:59:00Z"),
            "open": 100.1,
            "high": 99.8,
            "low": 98.0,
            "close": 98.8,
            "volume": 140.0,
            "completed": True,
        }
    )
    setup_ts = pd.Timestamp("2026-05-26T15:59:00Z") + pd.Timedelta(hours=entry_offset_hours)
    ts = pd.Timestamp("2026-05-26T16:59:00Z")
    while ts <= setup_ts:
        rows.append(
            {
                "timestamp": ts,
                "open": 98.8,
                "high": 99.4,
                "low": 96.0,
                "close": 97.0,
                "volume": 120.0,
                "completed": True,
            }
        )
        ts += pd.Timedelta(hours=1)
    return pd.DataFrame(rows)


def _setup(*, setup_id: str, setup_formed_at: str, manual: str) -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "setup_formed_at": setup_formed_at,
        "setup_type": "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
        "direction_context": "DOWN",
        "setup_reference_level": 100.0,
        "source_window_start": "2026-05-26T06:59:00Z",
        "selected_research_stop_type": "local_swing_stop",
        "manual_corrected_classification": manual,
        "setup_role_classification": manual,
    }
