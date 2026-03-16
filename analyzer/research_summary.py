"""Research-only deterministic final summary export layer for Phase 2 shortlist outputs."""

from __future__ import annotations

import pandas as pd

from .context import CONTEXT_MODEL_VERSION

RESEARCH_SUMMARY_COLUMNS = [
    "ShortlistRank",
    "ResearchPriority",
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingMethod",
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
    "OutcomeSemantics",
    "ConfidenceModelStatus",
    "AcceptedBreakSemanticsStatus",
    "ContextFormalizationStatus",
    "ExecutableEntrySemanticsStatus",
    "FormalizationEligible",
    "Direction",
    "SetupType",
    "EligibleEventTypes",
    "ContextModelVersion",
]

_NATURAL_KEY = ["ShortlistRank", "SourceReport", "GroupType", "GroupValue"]
_RESEARCH_PRIORITY_MAP = {"SELECT": "P1", "REVIEW": "P2"}
_OUTCOME_SEMANTICS_RESEARCH_PROXY = "RESEARCH_PROXY_FIXED_HORIZON"
_CONFIDENCE_MODEL_STATUS = "PROXY_RANKING_HEURISTIC"
_ACCEPTED_BREAK_SEMANTICS_STATUS = "NOT_IMPLEMENTED"
_CONTEXT_FORMALIZATION_STATUS = "DESCRIPTIVE_ONLY_UNLESS_EXPLICIT_SEMANTICS"
_EXECUTABLE_ENTRY_SEMANTICS_STATUS = "IMPLEMENTED_IN_BACKTEST_RULESET_V1"

_REQUIRED_SHORTLIST_COLUMNS = {
    "ShortlistRank",
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingMethod",
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

_REQUIRED_SETUPS_COLUMNS = {"SetupType", "Direction"}
def _eligible_events_for_direction(direction: str) -> str:
    if direction == "LONG":
        return "FAILED_BREAK_DOWN"
    if direction == "SHORT":
        return "FAILED_BREAK_UP"
    if direction == "BOTH":
        return "FAILED_BREAK_DOWN|FAILED_BREAK_UP"
    raise ValueError(f"Unsupported direction for research summary replay semantics: {direction}")


def _derive_setup_family(setup_types: pd.Series) -> str:
    families = set()
    for setup_type in setup_types.dropna().astype(str):
        upper = setup_type.upper()
        if upper.endswith("_LONG"):
            families.add(setup_type[: -len("_LONG")])
        elif upper.endswith("_SHORT"):
            families.add(setup_type[: -len("_SHORT")])
        else:
            families.add(setup_type)

    if not families:
        raise ValueError("Cannot derive replay setup family from empty setups_df")
    if len(families) != 1:
        raise ValueError(
            "Cannot derive unique replay setup family for research summary semantics from setups_df: "
            f"{sorted(families)}"
        )
    return next(iter(families))


def _enrich_replay_semantics(merged_df: pd.DataFrame, setups_df: pd.DataFrame) -> pd.DataFrame:
    missing = _REQUIRED_SETUPS_COLUMNS - set(setups_df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for research summary replay semantics enrichment in "
            f"setups_df: {sorted(missing)}"
        )

    setup_family = _derive_setup_family(setups_df["SetupType"])
    formalization_eligible_values: list[bool] = []
    direction_values: list[str] = []
    setup_type_values: list[str] = []
    event_values: list[str] = []

    for row in merged_df.itertuples(index=False):
        group_type = str(row.GroupType)
        group_value = str(row.GroupValue)
        upper_group_value = group_value.upper()

        if group_type == "Direction":
            if upper_group_value not in {"LONG", "SHORT"}:
                raise ValueError(
                    "Unsupported Direction GroupValue for research summary replay semantics enrichment: "
                    f"{group_value}"
                )
            formalization_eligible_values.append(True)
            direction = upper_group_value
            setup_type = setup_family
        elif group_type == "SetupType":
            formalization_eligible_values.append(True)
            setup_type = group_value
            if upper_group_value.endswith("_LONG"):
                direction = "LONG"
            elif upper_group_value.endswith("_SHORT"):
                direction = "SHORT"
            else:
                raise ValueError(
                    "Cannot derive replay direction from SetupType group without explicit _LONG/_SHORT suffix: "
                    f"{group_value}"
                )
        else:
            formalization_eligible_values.append(False)
            direction = pd.NA
            setup_type = pd.NA

        if not formalization_eligible_values[-1]:
            event_values.append(pd.NA)
            direction_values.append(direction)
            setup_type_values.append(setup_type)
            continue

        direction_values.append(direction)
        setup_type_values.append(setup_type)
        event_values.append(_eligible_events_for_direction(direction))

    enriched = merged_df.copy()
    enriched["FormalizationEligible"] = formalization_eligible_values
    enriched["Direction"] = direction_values
    enriched["SetupType"] = setup_type_values
    enriched["EligibleEventTypes"] = event_values
    enriched["ContextModelVersion"] = CONTEXT_MODEL_VERSION
    return enriched


def _enrich_without_setups_fail_loud_direction_rows(merged_df: pd.DataFrame) -> pd.DataFrame:
    formalization_eligible_values: list[bool] = []
    direction_values: list[str] = []
    setup_type_values: list[str] = []
    event_values: list[str] = []

    for row in merged_df.itertuples(index=False):
        group_type = str(row.GroupType)
        group_value = str(row.GroupValue)
        upper_group_value = group_value.upper()

        if group_type == "Direction":
            raise ValueError(
                "Cannot enrich Direction research summary rows without non-empty setups_df "
                "because SetupType lineage is unavailable"
            )

        if group_type == "SetupType":
            if upper_group_value.endswith("_LONG"):
                direction = "LONG"
            elif upper_group_value.endswith("_SHORT"):
                direction = "SHORT"
            else:
                raise ValueError(
                    "Cannot derive replay direction from SetupType group without explicit _LONG/_SHORT suffix: "
                    f"{group_value}"
                )
            formalization_eligible_values.append(True)
            direction_values.append(direction)
            setup_type_values.append(group_value)
            event_values.append(_eligible_events_for_direction(direction))
            continue

        formalization_eligible_values.append(False)
        direction_values.append(pd.NA)
        setup_type_values.append(pd.NA)
        event_values.append(pd.NA)

    enriched = merged_df.copy()
    enriched["FormalizationEligible"] = formalization_eligible_values
    enriched["Direction"] = direction_values
    enriched["SetupType"] = setup_type_values
    enriched["EligibleEventTypes"] = event_values
    enriched["ContextModelVersion"] = CONTEXT_MODEL_VERSION
    return enriched


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
    shortlist_df: pd.DataFrame,
    shortlist_explanations_df: pd.DataFrame,
    setups_df: pd.DataFrame | None = None,
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
    merged_df["OutcomeSemantics"] = _OUTCOME_SEMANTICS_RESEARCH_PROXY
    merged_df["ConfidenceModelStatus"] = _CONFIDENCE_MODEL_STATUS
    merged_df["AcceptedBreakSemanticsStatus"] = _ACCEPTED_BREAK_SEMANTICS_STATUS
    merged_df["ContextFormalizationStatus"] = _CONTEXT_FORMALIZATION_STATUS
    merged_df["ExecutableEntrySemanticsStatus"] = _EXECUTABLE_ENTRY_SEMANTICS_STATUS

    if setups_df is None or setups_df.empty:
        merged_df = _enrich_without_setups_fail_loud_direction_rows(merged_df)
    else:
        merged_df = _enrich_replay_semantics(merged_df, setups_df)

    return merged_df.loc[:, RESEARCH_SUMMARY_COLUMNS]
