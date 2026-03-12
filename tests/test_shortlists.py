import pandas as pd
import pytest

from analyzer.shortlists import SHORTLIST_COLUMNS, build_setup_shortlist


RANKING_REQUIRED_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingScore",
    "RankingLabel",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
]

SELECTION_REQUIRED_COLUMNS = [
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


def _rankings_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 8,
                "RankingScore": 0.20,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.30,
                "Delta_PositiveCloseReturnRate": 0.10,
            },
            {
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 12,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.20,
                "Delta_PositiveCloseReturnRate": 0.08,
            },
            {
                "SourceReport": "context_report",
                "GroupType": "HourBucket",
                "GroupValue": "13",
                "SampleCount": 20,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.10,
                "Delta_PositiveCloseReturnRate": 0.05,
            },
        ]
    )


def _selections_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "A",
                "SampleCount": 8,
                "RankingScore": 0.20,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.30,
                "Delta_PositiveCloseReturnRate": 0.10,
                "SelectionDecision": "SELECT",
                "SelectionReason": "STRONG_POSITIVE_EDGE",
            },
            {
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 12,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.20,
                "Delta_PositiveCloseReturnRate": 0.08,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            },
            {
                "SourceReport": "context_report",
                "GroupType": "HourBucket",
                "GroupValue": "13",
                "SampleCount": 20,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.10,
                "Delta_PositiveCloseReturnRate": 0.05,
                "SelectionDecision": "REJECT",
                "SelectionReason": "NON_POSITIVE_EDGE",
            },
        ]
    )


def test_empty_selections_returns_empty_shortlist_with_exact_schema():
    shortlist_df = build_setup_shortlist(
        _rankings_df(),
        pd.DataFrame(columns=SELECTION_REQUIRED_COLUMNS),
    )

    assert shortlist_df.empty
    assert list(shortlist_df.columns) == SHORTLIST_COLUMNS


def test_missing_required_ranking_column_fails_loudly():
    rankings_df = _rankings_df().drop(columns=["RankingLabel"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_shortlist(rankings_df, _selections_df())


def test_missing_required_selection_column_fails_loudly():
    selections_df = _selections_df().drop(columns=["SelectionReason"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_setup_shortlist(_rankings_df(), selections_df)


def test_duplicate_natural_key_in_rankings_fails_loudly():
    rankings_df = pd.concat([_rankings_df(), _rankings_df().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate natural key rows"):
        build_setup_shortlist(rankings_df, _selections_df())


def test_duplicate_natural_key_in_selections_fails_loudly():
    selections_df = pd.concat([_selections_df(), _selections_df().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate natural key rows"):
        build_setup_shortlist(_rankings_df(), selections_df)


def test_shortlist_includes_only_select_and_review_rows_and_excludes_reject():
    shortlist_df = build_setup_shortlist(_rankings_df(), _selections_df())

    assert set(shortlist_df["SelectionDecision"]) == {"SELECT", "REVIEW"}
    assert "REJECT" not in set(shortlist_df["SelectionDecision"])


def test_strict_join_fails_loudly_when_shortlistable_selection_has_no_ranking_match():
    selections_df = pd.concat(
        [
            _selections_df(),
            pd.DataFrame(
                [
                    {
                        "SourceReport": "report",
                        "GroupType": "SetupType",
                        "GroupValue": "MISSING",
                        "SampleCount": 9,
                        "RankingScore": 0.3,
                        "RankingLabel": "TOP",
                        "Delta_Mean_CloseReturn_Pct": 0.2,
                        "Delta_PositiveCloseReturnRate": 0.2,
                        "SelectionDecision": "SELECT",
                        "SelectionReason": "STRONG_POSITIVE_EDGE",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="missing ranking match"):
        build_setup_shortlist(_rankings_df(), selections_df)


def test_ordering_contract_and_shortlist_rank_are_deterministic():
    rankings_df = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "G",
                "GroupValue": "a",
                "SampleCount": 5,
                "RankingScore": 0.4,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
            },
            {
                "SourceReport": "context_report",
                "GroupType": "G",
                "GroupValue": "b",
                "SampleCount": 7,
                "RankingScore": 0.3,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
            },
            {
                "SourceReport": "report",
                "GroupType": "G",
                "GroupValue": "c",
                "SampleCount": 9,
                "RankingScore": 0.3,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
            },
            {
                "SourceReport": "context_report",
                "GroupType": "A",
                "GroupValue": "z",
                "SampleCount": 9,
                "RankingScore": 0.3,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
            },
            {
                "SourceReport": "report",
                "GroupType": "G",
                "GroupValue": "d",
                "SampleCount": 10,
                "RankingScore": 0.5,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.1,
                "Delta_PositiveCloseReturnRate": 0.1,
            },
        ]
    )

    selections_df = pd.DataFrame(
        [
            {
                **row,
                "SelectionDecision": "SELECT" if row["GroupValue"] != "d" else "REVIEW",
                "SelectionReason": "R",
            }
            for row in rankings_df.to_dict("records")
        ]
    )

    shortlist_df = build_setup_shortlist(rankings_df, selections_df)

    assert shortlist_df[["SelectionDecision", "GroupValue"]].values.tolist() == [
        ["SELECT", "a"],
        ["SELECT", "z"],
        ["SELECT", "c"],
        ["SELECT", "b"],
        ["REVIEW", "d"],
    ]
    assert shortlist_df["ShortlistRank"].tolist() == [1, 2, 3, 4, 5]


def test_output_columns_match_exact_schema_order():
    shortlist_df = build_setup_shortlist(_rankings_df(), _selections_df())

    assert list(shortlist_df.columns) == SHORTLIST_COLUMNS


def test_empty_after_filter_returns_empty_shortlist_schema():
    selections_df = _selections_df()
    selections_df["SelectionDecision"] = "REJECT"

    shortlist_df = build_setup_shortlist(_rankings_df(), selections_df)

    assert shortlist_df.empty
    assert list(shortlist_df.columns) == SHORTLIST_COLUMNS


def test_empty_rankings_with_shortlistable_selection_fails_loudly():
    rankings_df = pd.DataFrame(columns=RANKING_REQUIRED_COLUMNS)
    selections_df = _selections_df().iloc[[0]].copy()

    with pytest.raises(ValueError, match="must be non-empty"):
        build_setup_shortlist(rankings_df, selections_df)
