from __future__ import annotations

import pandas as pd

from analyzer.setups import SETUP_COLUMNS, extract_setup_candidates


def _events_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Timestamp",
            "EventType",
            "Side",
            "PriceLevel",
            "SourceTF",
            "ReferenceSwingTs",
            "ReferenceSwingPrice",
            "Confidence",
            "MetaJson",
        ]
    )


def test_failed_break_down_produces_one_long_setup():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]

    setups = extract_setup_candidates(pd.DataFrame(), events)

    assert len(setups) == 1
    row = setups.iloc[0]
    assert row["SetupType"] == "FAILED_BREAK_RECLAIM_LONG"
    assert row["Direction"] == "LONG"
    assert row["Status"] == "CANDIDATE"
    assert row["DetectedAt"] == pd.Timestamp("2025-01-01T00:05:00Z")
    assert row["SetupBarTs"] == pd.Timestamp("2025-01-01T00:05:00Z")
    assert row["ReferenceEventTs"] == pd.Timestamp("2025-01-01T00:05:00Z")
    assert row["ReferenceEventType"] == "FAILED_BREAK_DOWN"
    assert row["ReferenceEventAnchorTs"] == pd.Timestamp("2025-01-01T00:03:00Z")
    assert row["ReferenceLevel"] == 100.0


def test_failed_break_up_produces_one_short_setup():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:10:00Z"),
        "FAILED_BREAK_UP",
        "up",
        110.0,
        "H4",
        pd.Timestamp("2025-01-01T00:07:00Z"),
        110.0,
        pd.NA,
        pd.NA,
    ]

    setups = extract_setup_candidates(pd.DataFrame(), events)

    assert len(setups) == 1
    row = setups.iloc[0]
    assert row["SetupType"] == "FAILED_BREAK_RECLAIM_SHORT"
    assert row["Direction"] == "SHORT"
    assert row["ReferenceEventType"] == "FAILED_BREAK_UP"


def test_sweep_events_only_produce_no_setups():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:10:00Z"),
        "SWEEP_UP",
        "up",
        110.0,
        "H1",
        pd.Timestamp("2025-01-01T00:07:00Z"),
        110.0,
        pd.NA,
        pd.NA,
    ]

    setups = extract_setup_candidates(pd.DataFrame(), events)

    assert setups.empty
    assert setups.columns.tolist() == SETUP_COLUMNS


def test_swing_events_only_produce_no_setups():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:10:00Z"),
        "SWING_HIGH",
        "up",
        110.0,
        "H1",
        pd.Timestamp("2025-01-01T00:10:00Z"),
        110.0,
        pd.NA,
        pd.NA,
    ]

    setups = extract_setup_candidates(pd.DataFrame(), events)

    assert setups.empty
    assert setups.columns.tolist() == SETUP_COLUMNS


def test_empty_events_returns_empty_with_exact_schema():
    setups = extract_setup_candidates(pd.DataFrame(), _events_df())

    assert setups.empty
    assert setups.columns.tolist() == SETUP_COLUMNS


def test_setup_id_is_deterministic_for_identical_input():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]

    setups1 = extract_setup_candidates(pd.DataFrame(), events)
    setups2 = extract_setup_candidates(pd.DataFrame(), events)

    assert len(setups1) == 1
    assert setups1.iloc[0]["SetupId"] == setups2.iloc[0]["SetupId"]


def test_no_duplicate_setup_rows_for_same_failed_break_event():
    events = _events_df()
    row = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    events.loc[0] = row
    events.loc[1] = row

    setups = extract_setup_candidates(pd.DataFrame(), events)

    assert len(setups) == 1
