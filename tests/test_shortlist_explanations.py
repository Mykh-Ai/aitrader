import pandas as pd
import pytest

from analyzer.shortlist_explanations import (
    SHORTLIST_EXPLANATION_COLUMNS,
    build_setup_shortlist_explanations,
)


REQUIRED_SHORTLIST_COLUMNS = [
    "ShortlistRank",
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingScore",
    "RankingLabel",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
    "SelectionDecision",
    "SelectionReason",
]


def _shortlist_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ShortlistRank": 2,
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 20,
                "RankingScore": 0.30,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.10,
                "Delta_PositiveCloseReturnRate": 0.15,
                "SelectionDecision": "SELECT",
                "SelectionReason": "STRONG_POSITIVE_EDGE",
            },
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 15,
                "RankingScore": 0.10,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            },
            {
                "ShortlistRank": 3,
                "SourceReport": "report",
                "GroupType": "HourBucket",
                "GroupValue": "13",
                "SampleCount": 5,
                "RankingScore": 0.05,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": -0.01,
                "Delta_PositiveCloseReturnRate": -0.10,
                "SelectionDecision": "REJECT",
                "SelectionReason": "NON_POSITIVE_EDGE",
            },
            {
                "ShortlistRank": 4,
                "SourceReport": "report",
                "GroupType": "VolatilityRegime",
                "GroupValue": "HIGH",
                "SampleCount": 9,
                "RankingScore": 0.0,
                "RankingLabel": "BOTTOM",
                "Delta_Mean_CloseReturn_Pct": -0.2,
                "Delta_PositiveCloseReturnRate": 0.2,
                "SelectionDecision": "REJECT",
                "SelectionReason": "NON_POSITIVE_EDGE",
            },
        ]
    )


def test_empty_shortlist_returns_empty_explanations_with_exact_schema():
    shortlist_df = pd.DataFrame(columns=REQUIRED_SHORTLIST_COLUMNS)

    shortlist_explanations_df = build_setup_shortlist_explanations(shortlist_df)

    assert shortlist_explanations_df.empty
    assert list(shortlist_explanations_df.columns) == SHORTLIST_EXPLANATION_COLUMNS


def test_missing_required_shortlist_column_fails_loudly():
    shortlist_df = _shortlist_df().drop(columns=["RankingScore"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_shortlist_explanations(shortlist_df)


def test_score_band_classification_works_correctly():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert shortlist_explanations_df["ScoreBand"].tolist() == [
        "STRONG",
        "MODERATE",
        "WEAK_POSITIVE",
        "NON_POSITIVE",
    ]


def test_sample_band_classification_works_correctly():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert shortlist_explanations_df["SampleBand"].tolist() == ["LARGE", "MEDIUM", "SMALL", "SMALL"]


def test_delta_direction_classification_works_correctly():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert shortlist_explanations_df["DeltaDirection"].tolist() == ["UP", "FLAT", "DOWN", "DOWN"]


def test_positive_rate_direction_classification_works_correctly():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert shortlist_explanations_df["PositiveRateDirection"].tolist() == ["UP", "FLAT", "DOWN", "UP"]


def test_explanation_code_is_built_in_required_order_exactly():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert shortlist_explanations_df.loc[0, "ExplanationCode"] == (
        "SELECT|STRONG_POSITIVE_EDGE|TOP|STRONG|LARGE|UP|UP"
    )


def test_row_ordering_is_preserved_exactly_from_shortlist_input():
    shortlist_df = _shortlist_df()

    shortlist_explanations_df = build_setup_shortlist_explanations(shortlist_df)

    assert shortlist_explanations_df["ShortlistRank"].tolist() == shortlist_df["ShortlistRank"].tolist()
    assert shortlist_explanations_df[["SourceReport", "GroupType", "GroupValue"]].values.tolist() == (
        shortlist_df[["SourceReport", "GroupType", "GroupValue"]].values.tolist()
    )


def test_output_columns_match_exact_schema_order():
    shortlist_explanations_df = build_setup_shortlist_explanations(_shortlist_df())

    assert list(shortlist_explanations_df.columns) == SHORTLIST_EXPLANATION_COLUMNS
