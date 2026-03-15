import pandas as pd
import pytest

from analyzer.research_summary import RESEARCH_SUMMARY_COLUMNS, build_research_summary


SHORTLIST_REQUIRED_COLUMNS = [
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

SHORTLIST_EXPLANATIONS_REQUIRED_COLUMNS = [
    "ShortlistRank",
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SelectionDecision",
    "SelectionReason",
    "RankingLabel",
    "ScoreBand",
    "SampleBand",
    "DeltaDirection",
    "PositiveRateDirection",
    "ExplanationCode",
]


def _shortlist_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ShortlistRank": 2,
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SampleCount": 20,
                "RankingScore": 0.33,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.12,
                "Delta_PositiveCloseReturnRate": 0.2,
                "SelectionDecision": "SELECT",
                "SelectionReason": "STRONG_POSITIVE_EDGE",
            },
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 11,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.02,
                "Delta_PositiveCloseReturnRate": 0.01,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            },
        ]
    )




def _setups_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"SetupType": "FAILED_BREAK_RECLAIM_LONG", "Direction": "LONG"},
            {"SetupType": "FAILED_BREAK_RECLAIM_SHORT", "Direction": "SHORT"},
        ]
    )


def _shortlist_explanations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ShortlistRank": 2,
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "SelectionReason": "STRONG_POSITIVE_EDGE",
                "RankingLabel": "TOP",
                "ScoreBand": "STRONG",
                "SampleBand": "LARGE",
                "DeltaDirection": "UP",
                "PositiveRateDirection": "UP",
                "ExplanationCode": "SELECT|STRONG_POSITIVE_EDGE|TOP|STRONG|LARGE|UP|UP",
            },
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
                "RankingLabel": "TOP",
                "ScoreBand": "MODERATE",
                "SampleBand": "MEDIUM",
                "DeltaDirection": "UP",
                "PositiveRateDirection": "UP",
                "ExplanationCode": "REVIEW|POSITIVE_BUT_BORDERLINE|TOP|MODERATE|MEDIUM|UP|UP",
            },
        ]
    )


def test_both_empty_inputs_return_empty_summary_with_exact_schema():
    shortlist_df = pd.DataFrame(columns=SHORTLIST_REQUIRED_COLUMNS)
    shortlist_explanations_df = pd.DataFrame(columns=SHORTLIST_EXPLANATIONS_REQUIRED_COLUMNS)

    research_summary_df = build_research_summary(shortlist_df, shortlist_explanations_df, _setups_df())

    assert research_summary_df.empty
    assert list(research_summary_df.columns) == RESEARCH_SUMMARY_COLUMNS


def test_missing_required_shortlist_column_fails_loudly():
    shortlist_df = _shortlist_df().drop(columns=["RankingScore"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_research_summary(shortlist_df, _shortlist_explanations_df(), _setups_df())


def test_missing_required_shortlist_explanation_column_fails_loudly():
    shortlist_explanations_df = _shortlist_explanations_df().drop(columns=["ExplanationCode"])

    with pytest.raises(KeyError, match="Missing required columns"):
        build_research_summary(_shortlist_df(), shortlist_explanations_df, _setups_df())


def test_one_empty_and_one_non_empty_input_fails_loudly():
    with pytest.raises(ValueError, match="must both be empty or both be non-empty"):
        build_research_summary(_shortlist_df(), pd.DataFrame(columns=SHORTLIST_EXPLANATIONS_REQUIRED_COLUMNS))


def test_duplicate_natural_key_in_shortlist_fails_loudly():
    shortlist_df = pd.concat([_shortlist_df(), _shortlist_df().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate natural key rows"):
        build_research_summary(shortlist_df, _shortlist_explanations_df(), _setups_df())


def test_duplicate_natural_key_in_shortlist_explanations_fails_loudly():
    shortlist_explanations_df = pd.concat(
        [_shortlist_explanations_df(), _shortlist_explanations_df().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate natural key rows"):
        build_research_summary(_shortlist_df(), shortlist_explanations_df, _setups_df())


def test_strict_join_fails_loudly_when_shortlist_row_has_no_explanation_match():
    shortlist_explanations_df = _shortlist_explanations_df().iloc[[0]].reset_index(drop=True)

    with pytest.raises(ValueError, match="Shortlist rows missing explanation match"):
        build_research_summary(_shortlist_df(), shortlist_explanations_df, _setups_df())


def test_strict_join_fails_loudly_when_explanation_row_has_no_shortlist_match():
    extra = {
        "ShortlistRank": 99,
        "SourceReport": "report",
        "GroupType": "HourBucket",
        "GroupValue": "13",
        "SelectionDecision": "SELECT",
        "SelectionReason": "STRONG_POSITIVE_EDGE",
        "RankingLabel": "TOP",
        "ScoreBand": "STRONG",
        "SampleBand": "SMALL",
        "DeltaDirection": "UP",
        "PositiveRateDirection": "UP",
        "ExplanationCode": "SELECT|STRONG_POSITIVE_EDGE|TOP|STRONG|SMALL|UP|UP",
    }
    shortlist_explanations_df = pd.concat(
        [_shortlist_explanations_df(), pd.DataFrame([extra])],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Shortlist explanation rows missing shortlist match"):
        build_research_summary(_shortlist_df(), shortlist_explanations_df, _setups_df())


def test_research_priority_is_derived_correctly_for_select_and_review():
    research_summary_df = build_research_summary(_shortlist_df(), _shortlist_explanations_df(), _setups_df())

    assert research_summary_df["ResearchPriority"].tolist() == ["P1", "P2"]


def test_outcome_semantics_is_materialized_as_fixed_horizon_research_proxy():
    research_summary_df = build_research_summary(_shortlist_df(), _shortlist_explanations_df(), _setups_df())

    assert set(research_summary_df["OutcomeSemantics"]) == {"RESEARCH_PROXY_FIXED_HORIZON"}


def test_unexpected_selection_decision_fails_loudly():
    shortlist_df = _shortlist_df()
    shortlist_df.loc[0, "SelectionDecision"] = "REJECT"

    shortlist_explanations_df = _shortlist_explanations_df()
    shortlist_explanations_df.loc[0, "SelectionDecision"] = "REJECT"

    with pytest.raises(ValueError, match="Unsupported SelectionDecision"):
        build_research_summary(shortlist_df, shortlist_explanations_df, _setups_df())


def test_row_ordering_is_preserved_exactly_from_shortlist_input():
    shortlist_df = _shortlist_df()

    research_summary_df = build_research_summary(shortlist_df, _shortlist_explanations_df(), _setups_df())

    assert research_summary_df["ShortlistRank"].tolist() == shortlist_df["ShortlistRank"].tolist()
    assert research_summary_df[["SourceReport", "GroupType", "GroupValue"]].values.tolist() == (
        shortlist_df[["SourceReport", "GroupType", "GroupValue"]].values.tolist()
    )


def test_output_columns_match_exact_schema_order():
    research_summary_df = build_research_summary(_shortlist_df(), _shortlist_explanations_df(), _setups_df())

    assert list(research_summary_df.columns) == RESEARCH_SUMMARY_COLUMNS


def test_context_rows_are_marked_non_formalizable_and_have_null_semantics():
    shortlist_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SampleCount": 11,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.02,
                "Delta_PositiveCloseReturnRate": 0.01,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            }
        ]
    )
    shortlist_explanations_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
                "RankingLabel": "TOP",
                "ScoreBand": "MODERATE",
                "SampleBand": "MEDIUM",
                "DeltaDirection": "UP",
                "PositiveRateDirection": "UP",
                "ExplanationCode": "REVIEW|POSITIVE_BUT_BORDERLINE|TOP|MODERATE|MEDIUM|UP|UP",
            }
        ]
    )
    research_summary_df = build_research_summary(shortlist_df, shortlist_explanations_df, _setups_df())

    assert bool(research_summary_df.loc[0, "FormalizationEligible"]) is False
    assert pd.isna(research_summary_df.loc[0, "Direction"])
    assert pd.isna(research_summary_df.loc[0, "SetupType"])
    assert pd.isna(research_summary_df.loc[0, "EligibleEventTypes"])


def test_context_rows_without_setups_stay_non_formalizable():
    shortlist_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SampleCount": 11,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.02,
                "Delta_PositiveCloseReturnRate": 0.01,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            }
        ]
    )
    shortlist_explanations_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
                "RankingLabel": "TOP",
                "ScoreBand": "MODERATE",
                "SampleBand": "MEDIUM",
                "DeltaDirection": "UP",
                "PositiveRateDirection": "UP",
                "ExplanationCode": "REVIEW|POSITIVE_BUT_BORDERLINE|TOP|MODERATE|MEDIUM|UP|UP",
            }
        ]
    )

    research_summary_df = build_research_summary(shortlist_df, shortlist_explanations_df)

    assert bool(research_summary_df.loc[0, "FormalizationEligible"]) is False
    assert pd.isna(research_summary_df.loc[0, "Direction"])
    assert pd.isna(research_summary_df.loc[0, "SetupType"])
    assert pd.isna(research_summary_df.loc[0, "EligibleEventTypes"])


def test_replay_semantics_enrichment_fails_loudly_on_ambiguous_setup_families():
    setups_df = pd.DataFrame(
        [
            {"SetupType": "FAILED_BREAK_RECLAIM_LONG", "Direction": "LONG"},
            {"SetupType": "ANOTHER_SETUP_SHORT", "Direction": "SHORT"},
        ]
    )

    with pytest.raises(ValueError, match="Cannot derive unique replay setup family"):
        build_research_summary(_shortlist_df(), _shortlist_explanations_df(), setups_df)


def test_formalizable_setup_type_row_gets_full_semantics_and_eligible_true():
    shortlist_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SampleCount": 11,
                "RankingScore": 0.15,
                "RankingLabel": "TOP",
                "Delta_Mean_CloseReturn_Pct": 0.02,
                "Delta_PositiveCloseReturnRate": 0.01,
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
            }
        ]
    )
    shortlist_explanations_df = pd.DataFrame(
        [
            {
                "ShortlistRank": 1,
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "REVIEW",
                "SelectionReason": "POSITIVE_BUT_BORDERLINE",
                "RankingLabel": "TOP",
                "ScoreBand": "MODERATE",
                "SampleBand": "MEDIUM",
                "DeltaDirection": "UP",
                "PositiveRateDirection": "UP",
                "ExplanationCode": "REVIEW|POSITIVE_BUT_BORDERLINE|TOP|MODERATE|MEDIUM|UP|UP",
            }
        ]
    )

    research_summary_df = build_research_summary(shortlist_df, shortlist_explanations_df, _setups_df())

    assert bool(research_summary_df.loc[0, "FormalizationEligible"]) is True
    assert research_summary_df.loc[0, "Direction"] == "LONG"
    assert research_summary_df.loc[0, "SetupType"] == "FAILED_BREAK_RECLAIM_LONG"
    assert research_summary_df.loc[0, "EligibleEventTypes"] == "FAILED_BREAK_DOWN"


def test_formalizable_rows_without_setups_fail_loudly():
    with pytest.raises(ValueError, match="Cannot enrich Direction research summary rows without non-empty setups_df"):
        build_research_summary(_shortlist_df(), _shortlist_explanations_df())
