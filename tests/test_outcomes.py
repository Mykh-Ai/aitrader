from __future__ import annotations

import pandas as pd

from analyzer.outcomes import (
    MULTI_HORIZON_OUTCOME_COLUMNS,
    OUTCOME_COLUMNS,
    OUTCOME_HORIZON_BARS,
    build_setup_outcomes_by_horizon,
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
        columns=["SetupId", "SetupType", "SetupBarTs", "Direction", "ReferenceLevel"]
    )


def test_empty_setups_returns_empty_with_exact_schema():
    outcomes = build_setup_outcomes(_features_df(), _setups_df())

    assert outcomes.empty
    assert outcomes.columns.tolist() == OUTCOME_COLUMNS


def test_missing_required_df_column_fails_loudly():
    features = _features_df().drop(columns=["High"])
    setups = _setups_df()
    setups.loc[0] = ["s1", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:01:00Z"), "LONG", 100.0]

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
    setups.loc[0] = ["s1", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T23:59:00Z"), "LONG", 100.0]

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
    setups.loc[0] = ["s1", "FAILED_BREAK_RECLAIM_LONG", duplicate_ts, "LONG", 100.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Expected exactly one feature row per setup SetupBarTs" in str(exc)


def test_long_full_horizon_outcome_computes_correct_values():
    features = _features_df()
    setup_ts = pd.Timestamp("2025-01-01T00:03:00Z")
    setups = _setups_df()
    setups.loc[0] = ["s-long", "FAILED_BREAK_RECLAIM_LONG", setup_ts, "LONG", 100.0]

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
    setups.loc[0] = ["s-short", "FAILED_BREAK_RECLAIM_SHORT", setup_ts, "SHORT", 120.0]

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
    setups.loc[0] = ["s-partial", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    assert outcomes.iloc[0]["OutcomeStatus"] == "PARTIAL_HORIZON"
    assert outcomes.iloc[0]["OutcomeBarsObserved"] == 4


def test_no_forward_bars_outcome_works_correctly():
    features = _features_df(rows=1)
    setups = _setups_df()
    setups.loc[0] = ["s-none", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:00:00Z"), "LONG", 100.0]

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
    setups.loc[0] = ["s-exclude", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 100.0]

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
    setups.loc[0] = ["s-zero", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 0.0]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_reference_level_non_finite_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s-inf", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", float("inf")]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_reference_level_nan_fails_loudly():
    features = _features_df()
    setups = _setups_df()
    setups.loc[0] = ["s-nan", "FAILED_BREAK_RECLAIM_SHORT", pd.Timestamp("2025-01-01T00:03:00Z"), "SHORT", float("nan")]

    try:
        build_setup_outcomes(features, setups)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid ReferenceLevel" in str(exc)


def test_output_preserves_setup_row_order():
    features = _features_df(rows=30)
    setups = _setups_df()
    setups.loc[0] = ["b", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:10:00Z"), "LONG", 100.0]
    setups.loc[1] = ["a", "FAILED_BREAK_RECLAIM_SHORT", pd.Timestamp("2025-01-01T00:05:00Z"), "SHORT", 100.0]
    setups.loc[2] = ["c", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:15:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    assert outcomes["SetupId"].tolist() == ["b", "a", "c"]



def test_h1_outcomes_regression_remains_unchanged_with_additive_h2_columns():
    features = _features_df(rows=20)
    setups = _setups_df()
    setup_ts = pd.Timestamp("2025-01-01T00:03:00Z")
    setups.loc[0] = ["h1", "FAILED_BREAK_RECLAIM_LONG", setup_ts, "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)
    forward = features.iloc[4 : 4 + OUTCOME_HORIZON_BARS]
    row = outcomes.iloc[0]

    assert row["MFE_Pct"] == ((forward["High"].max() - 100.0) / 100.0) * 100
    assert row["MAE_Pct"] == ((forward["Low"].min() - 100.0) / 100.0) * 100
    assert row["CloseReturn_Pct"] == ((forward["Close"].iloc[-1] - 100.0) / 100.0) * 100
    assert pd.isna(row["H2_Post3Label_v1"])
    assert pd.isna(row["H2_Post6Label_v1"])
    assert pd.isna(row["H2_Post12Label_v1"])


def test_h2_long_observational_labels_basic_path():
    features = _features_df(rows=20)
    setup_idx = 3
    features.loc[setup_idx, "Close"] = 100.0
    features.loc[4:15, ["High", "Low", "Close"]] = [
        [100.8, 100.2, 100.4],
        [101.0, 100.3, 100.6],
        [101.1, 100.4, 100.7],
        [101.2, 100.5, 100.8],
        [101.3, 100.6, 100.9],
        [101.4, 100.7, 101.0],
        [101.5, 100.8, 101.1],
        [101.6, 100.9, 101.2],
        [101.7, 101.0, 101.3],
        [101.8, 101.1, 101.4],
        [101.9, 101.2, 101.5],
        [102.0, 101.3, 101.6],
    ]

    setups = _setups_df()
    setups.loc[0] = [
        "h2-long",
        "IMPULSE_FADE_RECLAIM_LONG_V1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        "LONG",
        100.0,
    ]

    row = build_setup_outcomes(features, setups).iloc[0]
    assert row["H2_Post3Label_v1"] == "EARLY_CONTINUATION"
    assert row["H2_Post6Label_v1"] == "RECLAIM_HELD"
    assert row["H2_Post12Label_v1"] == "FULL_FADE"


def test_h2_short_observational_labels_basic_path():
    features = _features_df(rows=20)
    setup_idx = 3
    features.loc[setup_idx, "Close"] = 100.0
    features.loc[4:15, ["High", "Low", "Close"]] = [
        [99.8, 99.2, 99.6],
        [99.7, 99.0, 99.4],
        [99.6, 98.9, 99.3],
        [99.5, 98.8, 99.2],
        [99.4, 98.7, 99.1],
        [99.3, 98.6, 99.0],
        [99.2, 98.5, 98.9],
        [99.1, 98.4, 98.8],
        [99.0, 98.3, 98.7],
        [98.9, 98.2, 98.6],
        [98.8, 98.1, 98.5],
        [98.7, 98.0, 98.4],
    ]

    setups = _setups_df()
    setups.loc[0] = [
        "h2-short",
        "IMPULSE_FADE_RECLAIM_SHORT_V1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        "SHORT",
        100.0,
    ]

    row = build_setup_outcomes(features, setups).iloc[0]
    assert row["H2_Post3Label_v1"] == "EARLY_CONTINUATION"
    assert row["H2_Post6Label_v1"] == "RECLAIM_HELD"
    assert row["H2_Post12Label_v1"] == "FULL_FADE"


def test_h2_reclaim_failure_in_first_6_bars_is_labeled_failed():
    features = _features_df(rows=20)
    features.loc[3, "Close"] = 100.0
    features.loc[4:15, ["High", "Low", "Close"]] = [
        [100.8, 100.2, 100.4],
        [101.0, 100.3, 100.6],
        [101.1, 100.4, 99.8],
        [101.2, 100.5, 100.8],
        [101.3, 100.6, 100.9],
        [101.4, 100.7, 101.0],
        [101.5, 100.8, 101.1],
        [101.6, 100.9, 101.2],
        [101.7, 101.0, 101.3],
        [101.8, 101.1, 101.4],
        [101.9, 101.2, 101.5],
        [102.0, 101.3, 101.6],
    ]

    setups = _setups_df()
    setups.loc[0] = [
        "h2-fail",
        "IMPULSE_FADE_RECLAIM_LONG_V1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        "LONG",
        100.0,
    ]

    row = build_setup_outcomes(features, setups).iloc[0]
    assert row["H2_Post6Label_v1"] == "RECLAIM_FAILED"


def test_h2_labels_are_deterministic_for_same_input():
    features = _features_df(rows=20)
    features.loc[3, "Close"] = 100.0
    setups = _setups_df()
    setups.loc[0] = [
        "h2-det",
        "IMPULSE_FADE_RECLAIM_LONG_V1",
        pd.Timestamp("2025-01-01T00:03:00Z"),
        "LONG",
        100.0,
    ]

    first = build_setup_outcomes(features, setups)
    second = build_setup_outcomes(features, setups)

    assert first.equals(second)


def test_outcome_pipeline_surface_materializes_h2_columns_while_h1_rows_stay_unchanged():
    features = _features_df(rows=20)
    features.loc[3, "Close"] = 100.0

    setups = _setups_df()
    setups.loc[0] = ["h1", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:03:00Z"), "LONG", 100.0]
    setups.loc[1] = ["h2", "IMPULSE_FADE_RECLAIM_LONG_V1", pd.Timestamp("2025-01-01T00:04:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes(features, setups)

    assert {"H2_Post3Label_v1", "H2_Post6Label_v1", "H2_Post12Label_v1"}.issubset(outcomes.columns)

    h1_row = outcomes.loc[outcomes["SetupId"] == "h1"].iloc[0]
    assert pd.isna(h1_row["H2_Post3Label_v1"])
    assert pd.isna(h1_row["H2_Post6Label_v1"])
    assert pd.isna(h1_row["H2_Post12Label_v1"])

    h2_row = outcomes.loc[outcomes["SetupId"] == "h2"].iloc[0]
    assert h2_row["H2_Post3Label_v1"] in {"EARLY_CONTINUATION", "NO_EARLY_CONTINUATION"}


def test_multi_horizon_output_has_one_row_per_setup_and_horizon():
    features = _features_df(rows=10)
    setups = _setups_df()
    setups.loc[0] = ["s1", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:01:00Z"), "LONG", 100.0]
    setups.loc[1] = ["s2", "FAILED_BREAK_RECLAIM_SHORT", pd.Timestamp("2025-01-01T00:02:00Z"), "SHORT", 120.0]

    outcomes = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="FAILED_BREAK_RECLAIM_EXTENDED_V1",
        outcome_horizons=(2, 4, 6),
    )

    assert list(outcomes.columns) == MULTI_HORIZON_OUTCOME_COLUMNS
    assert len(outcomes) == 6
    assert outcomes.groupby("SetupId")["OutcomeHorizonBars"].apply(list).to_dict() == {
        "s1": [2, 4, 6],
        "s2": [2, 4, 6],
    }
    assert set(outcomes["VariantId"]) == {"FAILED_BREAK_RECLAIM_EXTENDED_V1"}


def test_multi_horizon_setup_bar_is_excluded_from_outcome_window():
    features = _features_df(rows=6)
    features.loc[1, "High"] = 1000.0
    features.loc[1, "Low"] = 1.0
    setups = _setups_df()
    setups.loc[0] = ["s-exclude", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:01:00Z"), "LONG", 100.0]

    row = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="V",
        outcome_horizons=(3,),
    ).iloc[0]

    forward = features.iloc[2:5]
    assert row["MFE_Pct"] == ((forward["High"].max() - 100.0) / 100.0) * 100
    assert row["MAE_Pct"] == ((forward["Low"].min() - 100.0) / 100.0) * 100
    assert row["MFE_Pct"] != ((1000.0 - 100.0) / 100.0) * 100


def test_multi_horizon_long_short_outcomes_are_deterministic():
    features = pd.DataFrame(
        {
            "Timestamp": pd.date_range("2025-01-01T00:00:00Z", periods=5, freq="1min", tz="UTC"),
            "High": [100.0, 103.0, 105.0, 104.0, 102.0],
            "Low": [100.0, 99.0, 98.0, 96.0, 97.0],
            "Close": [100.0, 102.0, 104.0, 97.0, 101.0],
        }
    )
    setups = _setups_df()
    setups.loc[0] = ["long", "FAILED_BREAK_RECLAIM_LONG", features.loc[0, "Timestamp"], "LONG", 100.0]
    setups.loc[1] = ["short", "FAILED_BREAK_RECLAIM_SHORT", features.loc[0, "Timestamp"], "SHORT", 100.0]

    outcomes = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="V",
        outcome_horizons=(4,),
    ).set_index("SetupId")

    assert outcomes.loc["long", "MFE_Pct"] == 5.0
    assert outcomes.loc["long", "MAE_Pct"] == -4.0
    assert outcomes.loc["long", "CloseReturn_Pct"] == 1.0
    assert outcomes.loc["short", "MFE_Pct"] == 4.0
    assert outcomes.loc["short", "MAE_Pct"] == -5.0
    assert outcomes.loc["short", "CloseReturn_Pct"] == -1.0


def test_multi_horizon_time_to_extremes_uses_first_tie_deterministically():
    features = pd.DataFrame(
        {
            "Timestamp": pd.date_range("2025-01-01T00:00:00Z", periods=5, freq="1min", tz="UTC"),
            "High": [100.0, 101.0, 105.0, 105.0, 104.0],
            "Low": [100.0, 95.0, 95.0, 97.0, 96.0],
            "Close": [100.0, 101.0, 102.0, 103.0, 104.0],
        }
    )
    setups = _setups_df()
    setups.loc[0] = ["s-tie", "FAILED_BREAK_RECLAIM_LONG", features.loc[0, "Timestamp"], "LONG", 100.0]

    row = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="V",
        outcome_horizons=(4,),
    ).iloc[0]

    assert row["TimeToMFE_Bars"] == 2
    assert row["TimeToMFE_Ts"] == features.loc[2, "Timestamp"]
    assert row["TimeToMAE_Bars"] == 1
    assert row["TimeToMAE_Ts"] == features.loc[1, "Timestamp"]


def test_multi_horizon_partial_and_no_forward_statuses_work():
    features = _features_df(rows=3)
    setups = _setups_df()
    setups.loc[0] = ["partial", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:01:00Z"), "LONG", 100.0]
    setups.loc[1] = ["none", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:02:00Z"), "LONG", 100.0]

    outcomes = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="V",
        outcome_horizons=(2,),
    ).set_index("SetupId")

    assert outcomes.loc["partial", "OutcomeStatus"] == "PARTIAL_HORIZON"
    assert outcomes.loc["partial", "OutcomeBarsObserved"] == 1
    assert outcomes.loc["none", "OutcomeStatus"] == "NO_FORWARD_BARS"
    assert outcomes.loc["none", "OutcomeBarsObserved"] == 0
    assert pd.isna(outcomes.loc["none", "MFE_Pct"])


def test_multi_horizon_gap_metadata_flags_missing_minutes():
    features = _features_df(rows=4)
    features.loc[2, "Timestamp"] = pd.Timestamp("2025-01-01T00:05:00Z")
    features.loc[3, "Timestamp"] = pd.Timestamp("2025-01-01T00:06:00Z")
    setups = _setups_df()
    setups.loc[0] = ["gap", "FAILED_BREAK_RECLAIM_LONG", pd.Timestamp("2025-01-01T00:00:00Z"), "LONG", 100.0]

    row = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id="V",
        outcome_horizons=(3,),
    ).iloc[0]

    assert row["MaxGapMinutesObserved"] == 4.0
    assert bool(row["HasLargeGap"]) is True
