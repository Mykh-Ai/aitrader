"""Research-only deterministic shortlist export layer for setup selections."""

from __future__ import annotations

import pandas as pd

SHORTLIST_COLUMNS = [
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

_NATURAL_KEY = ["SourceReport", "GroupType", "GroupValue"]
_SELECTION_PRIORITY = {"SELECT": 0, "REVIEW": 1}

_REQUIRED_RANKING_COLUMNS = {
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingScore",
    "RankingLabel",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
}

_REQUIRED_SELECTION_COLUMNS = {
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


def _empty_shortlist() -> pd.DataFrame:
    return pd.DataFrame(columns=SHORTLIST_COLUMNS)


def _validate_required_columns(df: pd.DataFrame, required_columns: set[str], df_name: str) -> None:
    missing = required_columns - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for setup shortlist generation in "
            f"{df_name}: {sorted(missing)}"
        )


def _validate_unique_natural_key(df: pd.DataFrame, df_name: str) -> None:
    duplicates = df.duplicated(subset=_NATURAL_KEY, keep=False)
    if duplicates.any():
        duplicate_keys = df.loc[duplicates, _NATURAL_KEY].drop_duplicates().to_dict("records")
        raise ValueError(
            "Duplicate natural key rows found for setup shortlist generation in "
            f"{df_name}: {duplicate_keys}"
        )


def _strict_shortlist_join(rankings_df: pd.DataFrame, shortlistable_selections: pd.DataFrame) -> pd.DataFrame:
    merged = shortlistable_selections.merge(
        rankings_df[_NATURAL_KEY],
        on=_NATURAL_KEY,
        how="left",
        indicator=True,
        validate="one_to_one",
    )

    unmatched = merged[merged["_merge"] != "both"]
    if not unmatched.empty:
        unmatched_keys = unmatched[_NATURAL_KEY].drop_duplicates().to_dict("records")
        raise ValueError(
            "Shortlistable selection rows missing ranking match for setup shortlist generation: "
            f"{unmatched_keys}"
        )

    return shortlistable_selections.copy()


def build_setup_shortlist(rankings_df: pd.DataFrame, selections_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic shortlist rows for research review/export only."""
    _validate_required_columns(rankings_df, _REQUIRED_RANKING_COLUMNS, "rankings_df")
    _validate_required_columns(selections_df, _REQUIRED_SELECTION_COLUMNS, "selections_df")

    if selections_df.empty:
        return _empty_shortlist()

    _validate_unique_natural_key(rankings_df, "rankings_df")
    _validate_unique_natural_key(selections_df, "selections_df")

    shortlistable = selections_df[selections_df["SelectionDecision"].isin(_SELECTION_PRIORITY)].copy()
    if shortlistable.empty:
        return _empty_shortlist()

    if rankings_df.empty:
        raise ValueError(
            "Rankings dataframe must be non-empty when shortlistable selection rows exist "
            "for setup shortlist generation"
        )

    shortlist_df = _strict_shortlist_join(rankings_df, shortlistable)

    shortlist_df["_SelectionPriority"] = shortlist_df["SelectionDecision"].map(_SELECTION_PRIORITY)
    shortlist_df = shortlist_df.sort_values(
        by=[
            "_SelectionPriority",
            "RankingScore",
            "SampleCount",
            "SourceReport",
            "GroupType",
            "GroupValue",
        ],
        ascending=[True, False, False, True, True, True],
        kind="mergesort",
    )

    shortlist_df = shortlist_df.drop(columns=["_SelectionPriority"])
    shortlist_df.insert(0, "ShortlistRank", range(1, len(shortlist_df) + 1))
    return shortlist_df.loc[:, SHORTLIST_COLUMNS]
