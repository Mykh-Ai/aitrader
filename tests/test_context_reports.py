import pandas as pd
import pytest

from analyzer.context_reports import CONTEXT_REPORT_COLUMNS, build_setup_context_report


SETUP_COLUMNS = [
    "SetupId",
    "SetupType",
    "Direction",
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
OUTCOME_COLUMNS = ["SetupId", "OutcomeStatus", "MFE_Pct", "MAE_Pct", "CloseReturn_Pct"]


def _base_setups() -> pd.DataFrame:
    rows = []
    for idx in range(1, 7):
        rows.append(
            {
                "SetupId": f"S{idx}",
                "SetupType": "ABSORPTION_LONG" if idx % 2 else "SWEEP_SHORT",
                "Direction": "LONG" if idx % 2 else "SHORT",
                "AbsorptionScore_v1": float(idx),
                "CtxRelVolumeSpike_v1": 1 if idx <= 3 else 0,
                "CtxDeltaSpike_v1": 1 if idx % 2 else 0,
                "CtxOISpike_v1": 1 if idx in {1, 2, 3, 4} else 0,
                "CtxLiqSpike_v1": 1 if idx in {1, 6} else 0,
                "CtxWickReclaim_v1": 1 if idx in {3, 4, 5} else 0,
                "RelVolume_20": float(idx + 10),
                "DeltaAbsRatio_20": float(idx + 20),
                "OIChangeAbsRatio_20": float(idx + 30),
                "LiqTotalRatio_20": float(idx + 40),
            }
        )
    return pd.DataFrame(rows)


def _base_outcomes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "OutcomeStatus": "FULL_HORIZON",
                "MFE_Pct": 1.0,
                "MAE_Pct": -1.0,
                "CloseReturn_Pct": 1.0,
            },
            {
                "SetupId": "S2",
                "OutcomeStatus": "PARTIAL_HORIZON",
                "MFE_Pct": 2.0,
                "MAE_Pct": -2.0,
                "CloseReturn_Pct": -1.0,
            },
            {
                "SetupId": "S3",
                "OutcomeStatus": "NO_FORWARD_BARS",
                "MFE_Pct": 3.0,
                "MAE_Pct": -3.0,
                "CloseReturn_Pct": 0.0,
            },
            {
                "SetupId": "S4",
                "OutcomeStatus": "FULL_HORIZON",
                "MFE_Pct": 4.0,
                "MAE_Pct": -4.0,
                "CloseReturn_Pct": 2.0,
            },
            {
                "SetupId": "S5",
                "OutcomeStatus": "PARTIAL_HORIZON",
                "MFE_Pct": 5.0,
                "MAE_Pct": -5.0,
                "CloseReturn_Pct": -2.0,
            },
            {
                "SetupId": "S6",
                "OutcomeStatus": "NO_FORWARD_BARS",
                "MFE_Pct": 6.0,
                "MAE_Pct": -6.0,
                "CloseReturn_Pct": 0.5,
            },
        ]
    )


def test_empty_inputs_with_required_schema_return_empty_report_schema():
    setups_df = pd.DataFrame(columns=SETUP_COLUMNS)
    outcomes_df = pd.DataFrame(columns=OUTCOME_COLUMNS)

    report = build_setup_context_report(setups_df, outcomes_df)

    assert list(report.columns) == CONTEXT_REPORT_COLUMNS
    assert report.empty


def test_missing_required_setup_column_fails_loudly():
    setups_df = _base_setups().drop(columns=["Direction"])
    outcomes_df = _base_outcomes()

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_context_report(setups_df, outcomes_df)


def test_missing_required_outcome_column_fails_loudly():
    setups_df = _base_setups()
    outcomes_df = _base_outcomes().drop(columns=["OutcomeStatus"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_context_report(setups_df, outcomes_df)


def test_missing_outcome_match_for_setup_fails_loudly():
    setups_df = _base_setups()
    outcomes_df = _base_outcomes().loc[lambda df: df["SetupId"] != "S6"]

    with pytest.raises(ValueError, match="missing match"):
        build_setup_context_report(setups_df, outcomes_df)


def test_duplicate_setup_id_breaking_one_to_one_fails_loudly():
    setups_df = pd.concat([_base_setups(), _base_setups().iloc[[0]]], ignore_index=True)
    outcomes_df = _base_outcomes()

    with pytest.raises(ValueError, match="duplicate SetupId"):
        build_setup_context_report(setups_df, outcomes_df)


def test_flag_family_grouping_rows_generated_correctly():
    report = build_setup_context_report(_base_setups(), _base_outcomes())

    flags = report.loc[report["GroupType"] == "CtxRelVolumeSpike_v1"]
    assert flags["GroupValue"].tolist() == ["0", "1"]

    row_1 = flags.loc[flags["GroupValue"] == "1"].iloc[0]
    assert row_1["SampleCount"] == 3
    assert row_1["Mean_MFE_Pct"] == pytest.approx(2.0)
    assert row_1["Median_MAE_Pct"] == pytest.approx(-2.0)
    assert row_1["PositiveCloseReturnRate"] == pytest.approx(1 / 3)
    assert row_1["FullHorizonRate"] == pytest.approx(1 / 3)
    assert row_1["PartialHorizonRate"] == pytest.approx(1 / 3)
    assert row_1["NoForwardBarsRate"] == pytest.approx(1 / 3)


def test_flag_values_are_normalized_to_binary_group_values():
    setups_df = _base_setups()
    setups_df["CtxRelVolumeSpike_v1"] = [True, False, "1", "0", 1.0, 0.0]

    report = build_setup_context_report(setups_df, _base_outcomes())

    flags = report.loc[report["GroupType"] == "CtxRelVolumeSpike_v1", "GroupValue"].tolist()
    assert flags == ["0", "1"]


def test_non_binary_flag_values_fail_loudly():
    setups_df = _base_setups()
    setups_df["CtxRelVolumeSpike_v1"] = [0, 1, 2, 0, 1, 0]

    with pytest.raises(ValueError, match="binary 0/1"):
        build_setup_context_report(setups_df, _base_outcomes())


def test_numeric_bucket_families_generate_low_mid_high_rows_correctly():
    report = build_setup_context_report(_base_setups(), _base_outcomes())

    numeric_rows = report.loc[report["GroupType"] == "AbsorptionScore_v1"]
    assert numeric_rows["GroupValue"].tolist() == ["LOW", "MID", "HIGH"]
    assert numeric_rows["SampleCount"].tolist() == [2, 2, 2]


def test_numeric_bucket_family_fails_when_too_few_unique_values_exist():
    setups_df = _base_setups()
    setups_df["RelVolume_20"] = 99.0

    with pytest.raises(ValueError, match="at least 3 distinct"):
        build_setup_context_report(setups_df, _base_outcomes())


def test_context_report_row_ordering_matches_contract():
    report = build_setup_context_report(_base_setups(), _base_outcomes())

    expected_prefix = [
        "CtxRelVolumeSpike_v1",
        "CtxRelVolumeSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxOISpike_v1",
        "CtxOISpike_v1",
        "CtxLiqSpike_v1",
        "CtxLiqSpike_v1",
        "CtxWickReclaim_v1",
        "CtxWickReclaim_v1",
    ]
    assert report["GroupType"].tolist()[:10] == expected_prefix

    rel_volume_rows = report.loc[report["GroupType"] == "RelVolume_20"]
    assert rel_volume_rows["GroupValue"].tolist() == ["LOW", "MID", "HIGH"]


def test_rates_are_decimal_fractions_not_percent_units():
    report = build_setup_context_report(_base_setups(), _base_outcomes())

    row = report.loc[
        (report["GroupType"] == "CtxDeltaSpike_v1") & (report["GroupValue"] == "1")
    ].iloc[0]
    assert row["PositiveCloseReturnRate"] == pytest.approx(1 / 3)
    assert row["FullHorizonRate"] == pytest.approx(1 / 3)
    assert row["PartialHorizonRate"] == pytest.approx(1 / 3)
    assert row["NoForwardBarsRate"] == pytest.approx(1 / 3)
