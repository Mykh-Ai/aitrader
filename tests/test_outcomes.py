from __future__ import annotations

import pandas as pd

from analyzer.outcomes import (
    OUTCOME_COLUMNS,
    OUTCOME_HORIZON_BARS,
    build_setup_outcomes,
)


def _features_df(rows: int = 20) -> pd.DataFrame:
    start = pd.Timestamp("2025-01-01T00:00:00Z")
    timestamps = [start + pd.Timedelta(minutes=i) for i in range(rows)]
    data = {
        "Timestamp": timestamps,
        "High": [100.0 + i for i in range(rows)],
        "Low": [99.0 + i for i in range(rows)],
        "Close": [99.5 + i for i in range(rows)],
    }
    return pd.DataFrame(data)


def _setups_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["SetupId", "SetupBarTs", "Direction", "ReferenceLevel"]
    )


def test_empty_setups_returns_empty_with_exact_schema():
    outcomes = build_setup_outcomes(_features_df(), _setups_df())

    assert outcomes.empty
    assert outcomes.columns.tolist() == OUTCOME_COLUMNS


def test_missing_required_df_column_fails_loudly():
    features = _features_df().drop(columns=["High"])
    setups = _setups_df()
    setups.loc[0] = ["s1", pd.Timestamp("2025-01-01T00:01:00Z"), "LONG", 100.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected KeyError"
    except KeyError as exc:
        assert "Missing required columns for setup outcome evaluation" in str(exc)


def test_missing_required_setup_column_fails_loudly():
    features = _features_df()
    setups = _setups_df().drop(columns=["ReferenceLevel"])

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected KeyError"
    except KeyError as exc:
        assert "Missing required columns for setup outcome evaluation" in str(exc)


def test_missing_setup_timestamp_match_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s1", pd.Timestamp("2025-01-01T23:59:00Z"), "LONG", 100.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Expected exactly one feature row per setup SetupBarTs" in str(exc)


def test_duplicate_setup_timestamp_match_fails_loudly():
    features = _features_df()
    duplicate_ts = pd.Timestamp("2025-01-01T00:05:00Z")
    features = pd.concat(
        [features, pd.DataFrame([{"Timestamp": duplicate_ts, "High": 105.0, "Low": 104.0, "Close": 104.5}])],
        ignore_index=True,
    )
    setups = _setups_df()
    setups.loc[0] = ["s1", duplicate_ts, "LONG", 100.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Expected exactly one feature row per setup SetupBarTs" in str(exc)


def test_long_full_horizon_outcome_computes_correct_values():
    features = _features_df()
    setup_ts = pd.Timestamp("2025-01-01T00:03:00Z")
    setups = _setups_df()
    setups.loc[0] = ["s-long", setup_ts, "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    row = outcomes.iloc[0]
    forward = features.iloc[4 : 4 + OUTCOME_HORIZON_BARS]
    assert row["OutcomeStatus"] == "FULL_HORIZON"
    assert row["OutcomeBarsObserved"] == OUTCOME_HORIZON_BARS
    assert row["MFE_Pct"] == ((forward["High"].max() - 100.0) / 100.0) * 100
    assert row["MAE_Pct"] == ((forward["Low"].min() - 100.0) / 100.0) * 100
    assert row["CloseReturn_Pct"] == ((forward["Close"].iloc[-1] - 100.0) / 100.0) * 100
    assert row["BestHigh"] == forward["High"].max()
    assert row["BestLow"] == forward["Low"].min()
    assert row["FinalClose"] == forward["Close"].iloc[-1]
    assert row["OutcomeEndTs"] == forward["Timestamp"].iloc[-1]


def test_short_full_horizon_outcome_computes_correct_values():
    features = _features_df()
    setup_ts = pd.Timestamp("2025-01-01T00:03:00Z")
    setups = _setups_df()
    setups.loc[0] = ["s-short", setup_ts, "SHORT", 120.0]

    outcomes = build_setup_outcomes(features, setups)

    row = outcomes.iloc[0]
    forward = features.iloc[4 : 4 + OUTCOME_HORIZON_BARS]
    assert row["OutcomeStatus"] == "FULL_HORIZON"
    assert row["OutcomeBarsObserved"] == OUTCOME_HORIZON_BARS
    assert row["MFE_Pct"] == ((120.0 - forward["Low"].min()) / 120.0) * 100
    assert row["MAE_Pct"] == ((120.0 - forward["High"].max()) / 120.0) * 100
    assert row["CloseReturn_Pct"] == ((120.0 - forward["Close"].iloc[-1]) / 120.0) * 100


def test_partial_horizon_outcome_works_correctly():
    features = _features_df(rows=8)
    setups = _setups_df()
    setups.loc[0] = ["s-partial", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    assert outcomes.iloc[0]["OutcomeStatus"] == "PARTIAL_HORIZON"
    assert outcomes.iloc[0]["OutcomeBarsObserved"] == 4


def test_no_forward_bars_outcome_works_correctly():
    features = _features_df(rows=1)
    setups = _setups_df()
    setups.loc[0] = ["s-none", pd.Timestamp("2025-01-01T00:00:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    row = outcomes.iloc[0]
    assert row["OutcomeStatus"] == "NO_FORWARD_BARS"
    assert row["OutcomeBarsObserved"] == 0
    assert pd.isna(row["MFE_Pct"])
    assert pd.isna(row["MAE_Pct"])
    assert pd.isna(row["CloseReturn_Pct"])
    assert pd.isna(row["BestHigh"])
    assert pd.isna(row["BestLow"])
    assert pd.isna(row["FinalClose"])
    assert pd.isna(row["OutcomeEndTs"])


def test_setup_bar_is_excluded_from_outcome_window():
    features = _features_df(rows=14)
    features.loc[3, "High"] = 1000.0
    features.loc[3, "Low"] = 1.0
    setups = _setups_df()
    setups.loc[0] = ["s-exclude", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    row = outcomes.iloc[0]
    forward = features.iloc[4 : 4 + OUTCOME_HORIZON_BARS]
    assert row["BestHigh"] == forward["High"].max()
    assert row["BestLow"] == forward["Low"].min()
    assert row["BestHigh"] != 1000.0
    assert row["BestLow"] != 1.0


def test_reference_level_zero_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s-zero", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 0.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_reference_level_non_finite_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s-inf", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", float("inf")]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_reference_level_nan_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s-nan", pd.Timestamp("2025-01-01T00:03:00Z"), "SHORT", float("nan")]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_output_preserves_setup_row_order():
    features = _features_df(rows=30)
    setups = _setups_df()
    setups.loc[0] = ["b", pd.Timestamp("2025-01-01T00:10:00Z"), "LONG", 100.0]
    setups.loc[1] = ["a", pd.Timestamp("2025-01-01T00:05:00Z"), "SHORT", 100.0]
    setups.loc[2] = ["c", pd.Timestamp("2025-01-01T00:15:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    assert outcomes["SetupId"].tolist() == ["b", "a", "c"]
