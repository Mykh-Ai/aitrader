"""Research-only deterministic explanation view layer for setup shortlist rows."""

from __future__ import annotations

import pandas as pd

SHORTLIST_EXPLANATION_COLUMNS = [
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

_REQUIRED_SHORTLIST_COLUMNS = {
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
}


def _empty_shortlist_explanations() -> pd.DataFrame:
    return pd.DataFrame(columns=SHORTLIST_EXPLANATION_COLUMNS)


def _validate_required_columns(shortlist_df: pd.DataFrame) -> None:
    missing = _REQUIRED_SHORTLIST_COLUMNS - set(shortlist_df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for setup shortlist explanations generation in "
            f"shortlist_df: {sorted(missing)}"
        )


def _score_band(ranking_score: float) -> str:
    if ranking_score >= 0.25:
        return "STRONG"
    if ranking_score >= 0.10:
        return "MODERATE"
    if ranking_score > 0:
        return "WEAK_POSITIVE"
    return "NON_POSITIVE"


def _sample_band(sample_count: int) -> str:
    if sample_count >= 20:
        return "LARGE"
    if sample_count >= 10:
        return "MEDIUM"
    return "SMALL"


def _direction_label(value: float) -> str:
    if value > 0:
        return "UP"
    if value == 0:
        return "FLAT"
    return "DOWN"


def build_setup_shortlist_explanations(shortlist_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic shortlist explanation rows for research review only."""
    _validate_required_columns(shortlist_df)

    if shortlist_df.empty:
        return _empty_shortlist_explanations()

    shortlist_explanations_df = pd.DataFrame(index=shortlist_df.index)
    shortlist_explanations_df["ShortlistRank"] = shortlist_df["ShortlistRank"]
    shortlist_explanations_df["SourceReport"] = shortlist_df["SourceReport"]
    shortlist_explanations_df["GroupType"] = shortlist_df["GroupType"]
    shortlist_explanations_df["GroupValue"] = shortlist_df["GroupValue"]
    shortlist_explanations_df["SelectionDecision"] = shortlist_df["SelectionDecision"]
    shortlist_explanations_df["SelectionReason"] = shortlist_df["SelectionReason"]
    shortlist_explanations_df["RankingLabel"] = shortlist_df["RankingLabel"]
    shortlist_explanations_df["ScoreBand"] = shortlist_df["RankingScore"].map(_score_band)
    shortlist_explanations_df["SampleBand"] = shortlist_df["SampleCount"].map(_sample_band)
    shortlist_explanations_df["DeltaDirection"] = shortlist_df["Delta_Mean_CloseReturn_Pct"].map(
        _direction_label
    )
    shortlist_explanations_df["PositiveRateDirection"] = shortlist_df[
        "Delta_PositiveCloseReturnRate"
    ].map(_direction_label)

    shortlist_explanations_df["ExplanationCode"] = shortlist_explanations_df[
        [
            "SelectionDecision",
            "SelectionReason",
            "RankingLabel",
            "ScoreBand",
            "SampleBand",
            "DeltaDirection",
            "PositiveRateDirection",
        ]
    ].agg("|".join, axis=1)

    return shortlist_explanations_df.loc[:, SHORTLIST_EXPLANATION_COLUMNS]
