import pandas as pd
import pytest

import analyzer.selections as selections
from analyzer.selections import SELECTION_COLUMNS, build_setup_selections
from analyzer.thresholds import MIN_SAMPLE_COUNT as SHARED_MIN_SAMPLE_COUNT


REQUIRED_RANKING_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingScore",
    "RankingLabel",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
    "MinSamplePassed",
]


def _base_rankings_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 10,
                "RankingScore": 0.1,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.2,
                "Delta_PositiveCloseReturnRate": 0.1,
                "MinSamplePassed": True,
            }
        ]
    )


def test_empty_rankings_returns_empty_selections_with_exact_schema():
    rankings_df = pd.DataFrame(columns=REQUIRED_RANKING_COLUMNS)

    selections_df = build_setup_selections(rankings_df)

    assert selections_df.empty
    assert list(selections_df.columns) == SELECTION_COLUMNS


def test_missing_required_ranking_column_fails_loudly():
    rankings_df = _base_rankings_df().drop(columns=["RankingLabel"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_selections(rankings_df)


def test_select_classification_works_correctly():
    rankings_df = _base_rankings_df()

    selections_df = build_setup_selections(rankings_df)

    row = selections_df.iloc[0]
    assert row["SelectionDecision"] == "SELECT"
    assert row["SelectionReason"] == "STRONG_POSITIVE_EDGE"


def test_review_classification_works_correctly():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 10,
                "RankingScore": 0.03,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.2,
                "MinSamplePassed": True,
            },
            {
                "SourceReport": "context_report",
                "GroupType": "Ctx",
                "GroupValue": "X",
                "SampleCount": 10,
                "RankingScore": 0.2,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.0,
                "MinSamplePassed": True,
            },
        ]
    )

    selections_df = build_setup_selections(rankings_df)

    assert selections_df.iloc[0]["SelectionDecision"] == "REVIEW"
    assert selections_df.iloc[0]["SelectionReason"] == "POSITIVE_BUT_BORDERLINE"
    assert selections_df.iloc[1]["SelectionDecision"] == "REVIEW"
    assert selections_df.iloc[1]["SelectionReason"] == "POSITIVE_BUT_BORDERLINE"


def test_reject_low_sample_classification_works_correctly():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "OutcomeStatus",
                "GroupValue": "TIMEOUT",
                "SampleCount": 3,
                "RankingScore": 0.4,
                "RankingLabel": "LOW_SAMPLE",
                "Delta_Mean_CloseReturn_Pct": 0.3,
                "Delta_PositiveCloseReturnRate": 0.3,
                "MinSamplePassed": False,
            }
        ]
    )

    selections_df = build_setup_selections(rankings_df)

    row = selections_df.iloc[0]
    assert row["SelectionDecision"] == "REJECT"
    assert row["SelectionReason"] == "LOW_SAMPLE"


def test_reject_non_positive_edge_classification_works_correctly():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "B",
                "SampleCount": 8,
                "RankingScore": 0.0,
                "RankingLabel": "NEUTRAL",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
                "MinSamplePassed": True,
            }
        ]
    )

    selections_df = build_setup_selections(rankings_df)

    row = selections_df.iloc[0]
    assert row["SelectionDecision"] == "REJECT"
    assert row["SelectionReason"] == "NON_POSITIVE_EDGE"


def test_row_order_is_preserved_and_schema_matches_exact_order():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "context_report",
                "GroupType": "Ctx",
                "GroupValue": "2",
                "SampleCount": 10,
                "RankingScore": 0.07,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.2,
                "Delta_PositiveCloseReturnRate": 0.05,
                "MinSamplePassed": True,
            },
            {
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SampleCount": 10,
                "RankingScore": -0.1,
                "RankingLabel": "WEAK",
                "Delta_Mean_CloseReturn_Pct": -0.1,
                "Delta_PositiveCloseReturnRate": -0.02,
                "MinSamplePassed": True,
            },
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 4,
                "RankingScore": 0.2,
                "RankingLabel": "LOW_SAMPLE",
                "Delta_Mean_CloseReturn_Pct": 0.4,
                "Delta_PositiveCloseReturnRate": 0.1,
                "MinSamplePassed": False,
            },
        ]
    )

    selections_df = build_setup_selections(rankings_df)

    assert list(selections_df.columns) == SELECTION_COLUMNS
    assert selections_df[["SourceReport", "GroupType", "GroupValue"]].values.tolist() == [
        ["context_report", "Ctx", "2"],
        ["report", "Direction", "SHORT"],
        ["report", "SetupType", "A"],
    ]


def test_selection_boundary_behavior_for_4_5_6_is_preserved():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "S4",
                "SampleCount": 4,
                "RankingScore": 0.1,
                "RankingLabel": "LOW_SAMPLE",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
                "MinSamplePassed": False,
            },
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "S5",
                "SampleCount": 5,
                "RankingScore": 0.1,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
                "MinSamplePassed": True,
            },
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "S6",
                "SampleCount": 6,
                "RankingScore": 0.1,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
                "MinSamplePassed": True,
            },
        ]
    )

    selections_df = build_setup_selections(rankings_df)
    decisions = dict(zip(selections_df["SampleCount"], selections_df["SelectionDecision"]))

    assert decisions[4] == "REJECT"
    assert decisions[5] == "SELECT"
    assert decisions[6] == "SELECT"


def test_selections_uses_shared_min_sample_threshold():
    assert selections.MIN_SAMPLE_COUNT == SHARED_MIN_SAMPLE_COUNT == 5
