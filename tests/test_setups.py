from __future__ import annotations

import pandas as pd

from analyzer.setups import SETUP_COLUMNS, SETUP_TTL_BARS, extract_setup_candidates


def _features_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Timestamp",
            "Close",
            "AbsorptionScore_v1",
            "CtxRelVolumeSpike_v1",
            "CtxDeltaSpike_v1",
            "CtxOISpike_v1",
            "CtxLiqSpike_v1",
            "CtxWickReclaim_v1",
            "RelVolume_20",
            "DeltaAbsRatio_20",
            "OIChangeAbsRatio_20",
            "LiqTotalRatio_20",
        ]
    )


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

    features = _features_df()
    features.loc[0] = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        100.0,
        4,
        True,
        False,
        True,
        False,
        True,
        2.5,
        1.2,
        1.7,
        1.1,
    ]

    setups = extract_setup_candidates(features, events)

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
    assert row["AbsorptionScore_v1"] == 4
    assert row["CtxRelVolumeSpike_v1"]
    assert row["CtxDeltaSpike_v1"] == False
    assert row["CtxOISpike_v1"]
    assert row["CtxLiqSpike_v1"] == False
    assert row["CtxWickReclaim_v1"]
    assert row["RelVolume_20"] == 2.5
    assert row["DeltaAbsRatio_20"] == 1.2
    assert row["OIChangeAbsRatio_20"] == 1.7
    assert row["LiqTotalRatio_20"] == 1.1


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

    features = _features_df()
    features.loc[0] = [
        pd.Timestamp("2025-01-01T00:10:00Z"),
        110.0,
        2,
        False,
        True,
        False,
        True,
        False,
        1.8,
        1.9,
        1.6,
        1.5,
    ]

    setups = extract_setup_candidates(features, events)

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

    setups = extract_setup_candidates(_features_df(), events)

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

    setups = extract_setup_candidates(_features_df(), events)

    assert setups.empty
    assert setups.columns.tolist() == SETUP_COLUMNS


def test_empty_events_returns_empty_with_exact_schema():
    setups = extract_setup_candidates(_features_df(), _events_df())

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

    features = _features_df()
    features.loc[0] = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        100.0,
        4,
        True,
        False,
        True,
        False,
        True,
        2.5,
        1.2,
        1.7,
        1.1,
    ]

    setups1 = extract_setup_candidates(features, events)
    features.loc[0, "AbsorptionScore_v1"] = 1
    features.loc[0, "RelVolume_20"] = 4.4
    setups2 = extract_setup_candidates(features, events)

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

    features = _features_df()
    features.loc[0] = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        100.0,
        4,
        True,
        False,
        True,
        False,
        True,
        2.5,
        1.2,
        1.7,
        1.1,
    ]

    setups = extract_setup_candidates(features, events)

    assert len(setups) == 1


def test_missing_enrichment_column_fails_loudly():
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
    features = _features_df().drop(columns=["CtxWickReclaim_v1"])

    try:
        extract_setup_candidates(features, events)
        assert False, "Expected KeyError"
    except KeyError as exc:
        assert "Missing required feature columns for setup enrichment" in str(exc)


def test_missing_matching_feature_timestamp_fails_loudly():
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
    features = _features_df()
    features.loc[0] = [
        pd.Timestamp("2025-01-01T00:04:00Z"),
        99.0,
        4,
        True,
        False,
        True,
        False,
        True,
        2.5,
        1.2,
        1.7,
        1.1,
    ]

    try:
        extract_setup_candidates(features, events)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Expected exactly one feature row per setup SetupBarTs" in str(exc)


def test_duplicate_matching_feature_timestamp_fails_loudly():
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
    features = _features_df()
    feature_row = [
        pd.Timestamp("2025-01-01T00:05:00Z"),
        100.0,
        4,
        True,
        False,
        True,
        False,
        True,
        2.5,
        1.2,
        1.7,
        1.1,
    ]
    features.loc[0] = feature_row
    features.loc[1] = feature_row

    try:
        extract_setup_candidates(features, events)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Expected exactly one feature row per setup SetupBarTs" in str(exc)


def test_long_setup_invalidates_on_first_forward_close_below_reference():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    rows = [
        ("2025-01-01T00:00:00Z", 101.0),
        ("2025-01-01T00:01:00Z", 100.0),
        ("2025-01-01T00:02:00Z", 99.9),
        ("2025-01-01T00:03:00Z", 98.0),
    ]
    for i, (ts, close) in enumerate(rows):
        features.loc[i] = [pd.Timestamp(ts), close, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "INVALIDATED"
    assert row["InvalidatedAt"] == pd.Timestamp("2025-01-01T00:02:00Z")
    assert pd.isna(row["ExpiredAt"])


def test_short_setup_invalidates_on_first_forward_close_above_reference():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_UP",
        "up",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    rows = [
        ("2025-01-01T00:00:00Z", 99.0),
        ("2025-01-01T00:01:00Z", 100.0),
        ("2025-01-01T00:02:00Z", 100.1),
    ]
    for i, (ts, close) in enumerate(rows):
        features.loc[i] = [pd.Timestamp(ts), close, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "INVALIDATED"
    assert row["InvalidatedAt"] == pd.Timestamp("2025-01-01T00:02:00Z")
    assert pd.isna(row["ExpiredAt"])


def test_equal_touch_does_not_invalidate_long_and_expires_when_no_violation():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    for i in range(SETUP_TTL_BARS + 1):
        ts = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=i)
        close = 100.0 if i == 1 else 100.2
        features.loc[i] = [ts, close, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "EXPIRED"
    assert pd.isna(row["InvalidatedAt"])


def test_equal_touch_does_not_invalidate_short_and_expires_when_no_violation():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_UP",
        "up",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    for i in range(SETUP_TTL_BARS + 1):
        ts = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=i)
        close = 100.0 if i == 1 else 99.8
        features.loc[i] = [ts, close, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "EXPIRED"
    assert pd.isna(row["InvalidatedAt"])


def test_expires_when_ttl_window_inspected_without_invalidation():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    for i in range(SETUP_TTL_BARS + 2):
        ts = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=i)
        features.loc[i] = [ts, 100.5, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    expected_expired = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=SETUP_TTL_BARS)
    assert row["LifecycleStatus"] == "EXPIRED"
    assert row["ExpiredAt"] == expected_expired
    assert pd.isna(row["InvalidatedAt"])
    assert row["LifecycleBarsForward"] == SETUP_TTL_BARS


def test_pending_when_no_forward_bars_exist():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    features.loc[0] = [pd.Timestamp("2025-01-01T00:00:00Z"), 99.0, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "PENDING"
    assert pd.isna(row["InvalidatedAt"])
    assert pd.isna(row["ExpiredAt"])
    assert row["LifecycleBarsForward"] == 0


def test_lifecycle_uses_only_forward_bars_not_setup_bar():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]
    features = _features_df()
    for i, close in enumerate([99.0, 100.5, 100.4]):
        ts = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=i)
        features.loc[i] = [ts, close, 1, False, False, False, False, False, 1, 1, 1, 1]

    setups = extract_setup_candidates(features, events)
    row = setups.iloc[0]
    assert row["LifecycleStatus"] == "EXPIRED"
    assert pd.isna(row["InvalidatedAt"])


def test_missing_close_column_fails_loudly():
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
    features = _features_df().drop(columns=["Close"])

    try:
        extract_setup_candidates(features, events)
        assert False, "Expected KeyError"
    except KeyError as exc:
        assert "Missing required feature columns for setup enrichment" in str(exc)


def test_setup_id_unchanged_by_lifecycle_outcome():
    events = _events_df()
    events.loc[0] = [
        pd.Timestamp("2025-01-01T00:00:00Z"),
        "FAILED_BREAK_DOWN",
        "down",
        100.0,
        "H1",
        pd.Timestamp("2024-12-31T23:00:00Z"),
        100.0,
        pd.NA,
        pd.NA,
    ]

    features_a = _features_df()
    features_b = _features_df()
    rows_a = [100.1, 100.2, 100.3]
    rows_b = [100.1, 99.9, 100.3]
    for i, (ca, cb) in enumerate(zip(rows_a, rows_b, strict=False)):
        ts = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(minutes=i)
        base = [ts, 0.0, 1, False, False, False, False, False, 1, 1, 1, 1]
        features_a.loc[i] = [*base[:1], ca, *base[2:]]
        features_b.loc[i] = [*base[:1], cb, *base[2:]]

    setup_a = extract_setup_candidates(features_a, events).iloc[0]
    setup_b = extract_setup_candidates(features_b, events).iloc[0]

    assert setup_a["LifecycleStatus"] == "EXPIRED"
    assert setup_b["LifecycleStatus"] == "INVALIDATED"
    assert setup_a["SetupId"] == setup_b["SetupId"]
