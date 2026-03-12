"""Research-only deterministic final summary export layer for Phase 2 shortlist outputs."""

from __future__ import annotations

import pandas as pd

RESEARCH_SUMMARY_COLUMNS = [
    "ShortlistRank",
    "ResearchPriority",
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
    "ScoreBand",
    "SampleBand",
    "DeltaDirection",
    "PositiveRateDirection",
    "ExplanationCode",
]

_NATURAL_KEY = ["ShortlistRank", "SourceReport", "GroupType", "GroupValue"]
_RESEARCH_PRIORITY_MAP = {"SELECT": "P1", "REVIEW": "P2"}

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

_REQUIRED_SHORTLIST_EXPLANATION_COLUMNS = {
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
}


def _empty_research_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=RESEARCH_SUMMARY_COLUMNS)


def _validate_required_columns(df: pd.DataFrame, required_columns: set[str], df_name: str) -> None:
    missing = required_columns - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for research summary generation in "
            f"{df_name}: {sorted(missing)}"
        )


def _validate_unique_natural_key(df: pd.DataFrame, df_name: str) -> None:
    duplicates = df.duplicated(subset=_NATURAL_KEY, keep=False)
    if duplicates.any():
        duplicate_keys = df.loc[duplicates, _NATURAL_KEY].drop_duplicates().to_dict("records")
        raise ValueError(
            "Duplicate natural key rows found for research summary generation in "
            f"{df_name}: {duplicate_keys}"
        )


def _strict_one_to_one_merge(
    shortlist_df: pd.DataFrame, shortlist_explanations_df: pd.DataFrame
) -> pd.DataFrame:
    shortlist_with_order = shortlist_df.assign(_ShortlistInputOrder=range(len(shortlist_df)))

    merged = shortlist_with_order.merge(
        shortlist_explanations_df,
        on=_NATURAL_KEY,
        how="outer",
        suffixes=("", "_explanation"),
        indicator=True,
        validate="one_to_one",
        sort=False,
    )

    missing_explanations = merged[merged["_merge"] == "left_only"]
    if not missing_explanations.empty:
        missing_keys = missing_explanations[_NATURAL_KEY].drop_duplicates().to_dict("records")
        raise ValueError(
            "Shortlist rows missing explanation match for research summary generation: "
            f"{missing_keys}"
        )

    missing_shortlist = merged[merged["_merge"] == "right_only"]
    if not missing_shortlist.empty:
        missing_keys = missing_shortlist[_NATURAL_KEY].drop_duplicates().to_dict("records")
        raise ValueError(
            "Shortlist explanation rows missing shortlist match for research summary generation: "
            f"{missing_keys}"
        )

    merged = merged.sort_values(by="_ShortlistInputOrder", kind="mergesort")
    return merged.drop(columns=["_merge", "_ShortlistInputOrder"])


def _derive_research_priority(selection_decision: pd.Series) -> pd.Series:
    invalid = sorted(set(selection_decision.dropna()) - set(_RESEARCH_PRIORITY_MAP))
    if invalid:
        raise ValueError(
            "Unsupported SelectionDecision values for research summary generation: "
            f"{invalid}. Allowed values: {sorted(_RESEARCH_PRIORITY_MAP)}"
        )

    if selection_decision.isna().any():
        raise ValueError(
            "SelectionDecision contains null values for research summary generation; "
            f"allowed values: {sorted(_RESEARCH_PRIORITY_MAP)}"
        )

    return selection_decision.map(_RESEARCH_PRIORITY_MAP)


def build_research_summary(
    shortlist_df: pd.DataFrame, shortlist_explanations_df: pd.DataFrame
) -> pd.DataFrame:
    """Build deterministic final research summary rows for Phase 2 outputs."""
    _validate_required_columns(shortlist_df, _REQUIRED_SHORTLIST_COLUMNS, "shortlist_df")
    _validate_required_columns(
        shortlist_explanations_df,
        _REQUIRED_SHORTLIST_EXPLANATION_COLUMNS,
        "shortlist_explanations_df",
    )

    if shortlist_df.empty and shortlist_explanations_df.empty:
        return _empty_research_summary()

    if shortlist_df.empty != shortlist_explanations_df.empty:
        raise ValueError(
            "shortlist_df and shortlist_explanations_df must both be empty or both be non-empty "
            "for research summary generation"
        )

    _validate_unique_natural_key(shortlist_df, "shortlist_df")
    _validate_unique_natural_key(shortlist_explanations_df, "shortlist_explanations_df")

    merged_df = _strict_one_to_one_merge(shortlist_df, shortlist_explanations_df)

    mismatch_columns = ["SelectionDecision", "SelectionReason", "RankingLabel"]
    for column in mismatch_columns:
        explanation_column = f"{column}_explanation"
        mismatched = merged_df[merged_df[column] != merged_df[explanation_column]]
        if not mismatched.empty:
            mismatch_keys = mismatched[_NATURAL_KEY].drop_duplicates().to_dict("records")
            raise ValueError(
                f"Mismatched {column} values between shortlist and shortlist explanations "
                "for research summary generation: "
                f"{mismatch_keys}"
            )

    merged_df["ResearchPriority"] = _derive_research_priority(merged_df["SelectionDecision"])

    return merged_df.loc[:, RESEARCH_SUMMARY_COLUMNS]
