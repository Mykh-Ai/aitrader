import pandas as pd
import pytest

from analyzer.reports import REPORT_COLUMNS, build_setup_report


SETUP_COLUMNS = ["SetupId", "SetupType", "Direction", "LifecycleStatus"]
OUTCOME_COLUMNS = ["SetupId", "OutcomeStatus", "MFE_Pct", "MAE_Pct", "CloseReturn_Pct"]


def _base_setups() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "ABSORPTION_LONG",
                "Direction": "LONG",
                "LifecycleStatus": "PENDING",
            },
            {
                "SetupId": "S2",
                "SetupType": "SWEEP_SHORT",
                "Direction": "SHORT",
                "LifecycleStatus": "INVALIDATED",
            },
            {
                "SetupId": "S3",
                "SetupType": "SWEEP_SHORT",
                "Direction": "SHORT",
                "LifecycleStatus": "EXPIRED",
            },
            {
                "SetupId": "S4",
                "SetupType": "ABSORPTION_LONG",
                "Direction": "LONG",
                "LifecycleStatus": "PENDING",
            },
        ]
    )


def _base_outcomes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "OutcomeStatus": "FULL_HORIZON",
                "MFE_Pct": 1.0,
                "MAE_Pct": -1.0,
                "CloseReturn_Pct": 0.5,
            },
            {
                "SetupId": "S2",
                "OutcomeStatus": "PARTIAL_HORIZON",
                "MFE_Pct": 2.0,
                "MAE_Pct": -2.0,
                "CloseReturn_Pct": -0.5,
            },
            {
                "SetupId": "S3",
                "OutcomeStatus": "NO_FORWARD_BARS",
                "MFE_Pct": pd.NA,
                "MAE_Pct": pd.NA,
                "CloseReturn_Pct": pd.NA,
            },
            {
                "SetupId": "S4",
                "OutcomeStatus": "FULL_HORIZON",
                "MFE_Pct": 3.0,
                "MAE_Pct": -0.5,
                "CloseReturn_Pct": 1.0,
            },
        ]
    )


def test_empty_inputs_with_required_schema_return_empty_report_schema():
    setups_df = pd.DataFrame(columns=SETUP_COLUMNS)
    outcomes_df = pd.DataFrame(columns=OUTCOME_COLUMNS)

    report = build_setup_report(setups_df, outcomes_df)

    assert list(report.columns) == REPORT_COLUMNS
    assert report.empty


def test_missing_required_setup_column_fails_loudly():
    setups_df = _base_setups().drop(columns=["Direction"])
    outcomes_df = _base_outcomes()

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_report(setups_df, outcomes_df)


def test_missing_required_outcome_column_fails_loudly():
    setups_df = _base_setups()
    outcomes_df = _base_outcomes().drop(columns=["OutcomeStatus"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_report(setups_df, outcomes_df)


def test_missing_outcome_match_for_setup_fails_loudly():
    setups_df = _base_setups()
    outcomes_df = _base_outcomes().loc[lambda df: df["SetupId"] != "S4"]

    with pytest.raises(ValueError, match="missing match"):
        build_setup_report(setups_df, outcomes_df)


def test_duplicate_setup_id_breaking_one_to_one_fails_loudly():
    setups_df = pd.concat([_base_setups(), _base_setups().iloc[[0]]], ignore_index=True)
    outcomes_df = _base_outcomes()

    with pytest.raises(ValueError, match="duplicate SetupId"):
        build_setup_report(setups_df, outcomes_df)


def test_overall_row_computes_expected_metrics():
    report = build_setup_report(_base_setups(), _base_outcomes())
    overall = report.iloc[0]

    assert overall["GroupType"] == "overall"
    assert overall["GroupValue"] == "ALL"
    assert overall["SampleCount"] == 4
    assert overall["Mean_MFE_Pct"] == pytest.approx(2.0)
    assert overall["Median_MFE_Pct"] == pytest.approx(2.0)
    assert overall["Mean_MAE_Pct"] == pytest.approx(-1.1666666667)
    assert overall["Median_MAE_Pct"] == pytest.approx(-1.0)
    assert overall["Mean_CloseReturn_Pct"] == pytest.approx(1 / 3)
    assert overall["Median_CloseReturn_Pct"] == pytest.approx(0.5)
    assert overall["PositiveCloseReturnRate"] == pytest.approx(0.5)
    assert overall["InvalidatedRate"] == pytest.approx(0.25)
    assert overall["ExpiredRate"] == pytest.approx(0.25)
    assert overall["PendingRate"] == pytest.approx(0.5)
    assert overall["FullHorizonRate"] == pytest.approx(0.5)
    assert overall["PartialHorizonRate"] == pytest.approx(0.25)
    assert overall["NoForwardBarsRate"] == pytest.approx(0.25)


def test_group_rows_generated_for_all_required_families():
    report = build_setup_report(_base_setups(), _base_outcomes())

    setup_type_values = report.loc[report["GroupType"] == "SetupType", "GroupValue"].tolist()
    direction_values = report.loc[report["GroupType"] == "Direction", "GroupValue"].tolist()
    lifecycle_values = report.loc[
        report["GroupType"] == "LifecycleStatus", "GroupValue"
    ].tolist()
    outcome_values = report.loc[report["GroupType"] == "OutcomeStatus", "GroupValue"].tolist()

    assert setup_type_values == ["ABSORPTION_LONG", "SWEEP_SHORT"]
    assert direction_values == ["LONG", "SHORT"]
    assert lifecycle_values == ["EXPIRED", "INVALIDATED", "PENDING"]
    assert outcome_values == ["FULL_HORIZON", "NO_FORWARD_BARS", "PARTIAL_HORIZON"]


def test_report_row_ordering_matches_contract():
    report = build_setup_report(_base_setups(), _base_outcomes())

    assert report["GroupType"].tolist() == [
        "overall",
        "SetupType",
        "SetupType",
        "Direction",
        "Direction",
        "LifecycleStatus",
        "LifecycleStatus",
        "LifecycleStatus",
        "OutcomeStatus",
        "OutcomeStatus",
        "OutcomeStatus",
    ]
