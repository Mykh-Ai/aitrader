import pandas as pd
import pytest

from analyzer.rankings import MIN_SAMPLE_COUNT, RANKING_COLUMNS, build_setup_rankings
from analyzer.thresholds import MIN_SAMPLE_COUNT as SHARED_MIN_SAMPLE_COUNT


REQUIRED_COLUMNS = [
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
]


def _base_report_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 6,
                "Mean_MFE_Pct": 2.0,
                "Mean_MAE_Pct": -0.5,
                "Mean_CloseReturn_Pct": 1.0,
                "PositiveCloseReturnRate": 0.8,
            },
            {
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SampleCount": 4,
                "Mean_MFE_Pct": 0.5,
                "Mean_MAE_Pct": -2.0,
                "Mean_CloseReturn_Pct": -0.5,
                "PositiveCloseReturnRate": 0.25,
            },
            {
                "GroupType": "LifecycleStatus",
                "GroupValue": "PENDING",
                "SampleCount": 5,
                "Mean_MFE_Pct": 1.5,
                "Mean_MAE_Pct": -1.5,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "OutcomeStatus",
                "GroupValue": "FULL_HORIZON",
                "SampleCount": 5,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": -1.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "ignored_group",
                "GroupValue": "XXX",
                "SampleCount": 99,
                "Mean_MFE_Pct": 9.0,
                "Mean_MAE_Pct": -9.0,
                "Mean_CloseReturn_Pct": 9.0,
                "PositiveCloseReturnRate": 0.9,
            },
        ]
    )


def _base_context_report_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "GroupType": "CtxB",
                "GroupValue": "1",
                "SampleCount": 8,
                "Mean_MFE_Pct": 1.2,
                "Mean_MAE_Pct": -0.8,
                "Mean_CloseReturn_Pct": 0.6,
                "PositiveCloseReturnRate": 0.45,
            },
            {
                "GroupType": "CtxA",
                "GroupValue": "0",
                "SampleCount": 2,
                "Mean_MFE_Pct": 0.2,
                "Mean_MAE_Pct": -0.3,
                "Mean_CloseReturn_Pct": 0.2,
                "PositiveCloseReturnRate": 0.35,
            },
        ]
    )


def test_missing_required_report_column_fails_loudly():
    report_df = _base_report_df().drop(columns=["Mean_MAE_Pct"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_rankings(report_df, _base_context_report_df())


def test_missing_required_context_report_column_fails_loudly():
    context_report_df = _base_context_report_df().drop(columns=["Mean_MAE_Pct"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_rankings(_base_report_df(), context_report_df)


def test_missing_baseline_row_fails_loudly():
    report_df = _base_report_df().loc[lambda df: df["GroupType"] != "overall"]

    with pytest.raises(ValueError, match="baseline row"):
        build_setup_rankings(report_df, _base_context_report_df())


def test_duplicate_baseline_row_fails_loudly():
    report_df = pd.concat([_base_report_df(), _base_report_df().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="found duplicates"):
        build_setup_rankings(report_df, _base_context_report_df())


def test_report_candidates_are_included_and_baseline_excluded():
    rankings = build_setup_rankings(_base_report_df(), _base_context_report_df())

    report_rows = rankings.loc[rankings["SourceReport"] == "report"]
    assert not ((report_rows["GroupType"] == "overall") & (report_rows["GroupValue"] == "ALL")).any()
    assert set(report_rows["GroupType"].unique()) == {
        "SetupType",
        "Direction",
        "LifecycleStatus",
        "OutcomeStatus",
    }
    assert "ignored_group" not in report_rows["GroupType"].tolist()


def test_context_report_candidates_are_included_correctly():
    rankings = build_setup_rankings(_base_report_df(), _base_context_report_df())

    context_rows = rankings.loc[rankings["SourceReport"] == "context_report"]
    assert context_rows[["GroupType", "GroupValue"]].values.tolist() == [["CtxB", "1"], ["CtxA", "0"]]


def test_delta_fields_are_computed_correctly():
    rankings = build_setup_rankings(_base_report_df(), _base_context_report_df())
    row = rankings.loc[(rankings["SourceReport"] == "report") & (rankings["GroupType"] == "SetupType")].iloc[0]

    assert row["Baseline_Mean_CloseReturn_Pct"] == pytest.approx(0.5)
    assert row["Baseline_PositiveCloseReturnRate"] == pytest.approx(0.4)
    assert row["Delta_Mean_CloseReturn_Pct"] == pytest.approx(0.5)
    assert row["Delta_PositiveCloseReturnRate"] == pytest.approx(0.4)


def test_min_sample_passed_is_computed_correctly():
    rankings = build_setup_rankings(_base_report_df(), _base_context_report_df())

    low_sample = rankings.loc[
        (rankings["SourceReport"] == "report") & (rankings["GroupType"] == "Direction")
    ].iloc[0]
    high_sample = rankings.loc[
        (rankings["SourceReport"] == "report") & (rankings["GroupType"] == "SetupType")
    ].iloc[0]

    assert low_sample["SampleCount"] < MIN_SAMPLE_COUNT
    assert low_sample["MinSamplePassed"] == False
    assert high_sample["SampleCount"] >= MIN_SAMPLE_COUNT
    assert high_sample["MinSamplePassed"] == True


def test_ranking_score_uses_exact_formula():
    rankings = build_setup_rankings(_base_report_df(), _base_context_report_df())
    row = rankings.loc[(rankings["SourceReport"] == "report") & (rankings["GroupType"] == "SetupType")].iloc[0]

    expected = 0.4 + 0.1 * 0.5 + 0.02 * 2.0 + 0.02 * -0.5
    assert row["RankingScore"] == pytest.approx(expected)


def test_ranking_label_logic_works_for_all_outcomes():
    report_df = pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 1.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "low",
                "SampleCount": 4,
                "Mean_MFE_Pct": 10.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 2.0,
                "PositiveCloseReturnRate": 0.6,
            },
            {
                "GroupType": "Direction",
                "GroupValue": "top",
                "SampleCount": 5,
                "Mean_MFE_Pct": 10.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 1.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "LifecycleStatus",
                "GroupValue": "neutral",
                "SampleCount": 5,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 1.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "OutcomeStatus",
                "GroupValue": "weak",
                "SampleCount": 5,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.4,
            },
        ]
    )
    context_report_df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    rankings = build_setup_rankings(report_df, context_report_df)

    labels = dict(zip(rankings["GroupValue"], rankings["RankingLabel"]))
    assert labels["low"] == "LOW_SAMPLE"
    assert labels["top"] == "TOP"
    assert labels["neutral"] == "NEUTRAL"
    assert labels["weak"] == "WEAK"


def test_row_ordering_matches_contract():
    report_df = pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "B",
                "SampleCount": 6,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.7,
                "PositiveCloseReturnRate": 0.45,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 7,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.9,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SampleCount": 6,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.4,
                "PositiveCloseReturnRate": 0.3,
            },
            {
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 6,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.6,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "LifecycleStatus",
                "GroupValue": "PENDING",
                "SampleCount": 5,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "OutcomeStatus",
                "GroupValue": "FULL_HORIZON",
                "SampleCount": 5,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
        ]
    )

    context_report_df = pd.DataFrame(
        [
            {
                "GroupType": "Ctx2",
                "GroupValue": "x",
                "SampleCount": 6,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
            {
                "GroupType": "Ctx1",
                "GroupValue": "y",
                "SampleCount": 6,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.4,
            },
        ]
    )

    rankings = build_setup_rankings(report_df, context_report_df)

    assert list(rankings.columns) == RANKING_COLUMNS
    assert rankings[["SourceReport", "GroupType", "GroupValue"]].values.tolist() == [
        ["report", "SetupType", "A"],
        ["report", "SetupType", "B"],
        ["report", "Direction", "LONG"],
        ["report", "Direction", "SHORT"],
        ["report", "LifecycleStatus", "PENDING"],
        ["report", "OutcomeStatus", "FULL_HORIZON"],
        ["context_report", "Ctx2", "x"],
        ["context_report", "Ctx1", "y"],
    ]


def test_context_report_empty_is_allowed_if_report_has_baseline_and_candidates():
    rankings = build_setup_rankings(_base_report_df(), pd.DataFrame(columns=REQUIRED_COLUMNS))

    assert not rankings.empty
    assert set(rankings["SourceReport"]) == {"report"}


def test_both_inputs_empty_return_empty_rankings_with_exact_schema():
    rankings = build_setup_rankings(
        pd.DataFrame(columns=REQUIRED_COLUMNS),
        pd.DataFrame(columns=REQUIRED_COLUMNS),
    )

    assert list(rankings.columns) == RANKING_COLUMNS
    assert rankings.empty


def test_min_sample_boundary_behavior_for_4_5_6_is_preserved():
    report_df = pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "S4",
                "SampleCount": 4,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "Direction",
                "GroupValue": "S5",
                "SampleCount": 5,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "LifecycleStatus",
                "GroupValue": "S6",
                "SampleCount": 6,
                "Mean_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.5,
            },
        ]
    )

    rankings = build_setup_rankings(report_df, pd.DataFrame(columns=REQUIRED_COLUMNS))
    passed = dict(zip(rankings["SampleCount"], rankings["MinSamplePassed"]))

    assert passed[4] is False
    assert passed[5] is True
    assert passed[6] is True


def test_rankings_uses_shared_min_sample_threshold():
    assert MIN_SAMPLE_COUNT == SHARED_MIN_SAMPLE_COUNT == 5
