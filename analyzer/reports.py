"""Research-only grouped reporting for setup outcome statistics."""

from __future__ import annotations

import pandas as pd

REPORT_COLUMNS = [
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Median_MFE_Pct",
    "Mean_MAE_Pct",
    "Median_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "Median_CloseReturn_Pct",
    "PositiveCloseReturnRate",
    "InvalidatedRate",
    "ExpiredRate",
    "PendingRate",
    "FullHorizonRate",
    "PartialHorizonRate",
    "NoForwardBarsRate",
]

_REQUIRED_SETUP_COLUMNS = {"SetupId", "SetupType", "Direction", "LifecycleStatus"}
_REQUIRED_OUTCOME_COLUMNS = {
    "SetupId",
    "OutcomeStatus",
    "MFE_Pct",
    "MAE_Pct",
    "CloseReturn_Pct",
}


def _empty_report() -> pd.DataFrame:
    return pd.DataFrame(columns=REPORT_COLUMNS)


def _validate_required_columns(setups_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> None:
    missing_setup = _REQUIRED_SETUP_COLUMNS - set(setups_df.columns)
    if missing_setup:
        raise KeyError(
            "Missing required columns for setup report generation in setups_df: "
            f"{sorted(missing_setup)}"
        )

    missing_outcomes = _REQUIRED_OUTCOME_COLUMNS - set(outcomes_df.columns)
    if missing_outcomes:
        raise KeyError(
            "Missing required columns for setup report generation in outcomes_df: "
            f"{sorted(missing_outcomes)}"
        )


def _strict_merge(setups_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> pd.DataFrame:
    if setups_df["SetupId"].duplicated().any():
        dup_ids = setups_df.loc[setups_df["SetupId"].duplicated(), "SetupId"].tolist()
        raise ValueError(
            "Expected one-to-one setup/outcome mapping by SetupId; duplicate SetupId in setups_df: "
            f"{sorted(set(dup_ids))}"
        )

    if outcomes_df["SetupId"].duplicated().any():
        dup_ids = outcomes_df.loc[outcomes_df["SetupId"].duplicated(), "SetupId"].tolist()
        raise ValueError(
            "Expected one-to-one setup/outcome mapping by SetupId; duplicate SetupId in outcomes_df: "
            f"{sorted(set(dup_ids))}"
        )

    merged = setups_df.loc[:, sorted(_REQUIRED_SETUP_COLUMNS)].merge(
        outcomes_df.loc[:, sorted(_REQUIRED_OUTCOME_COLUMNS)],
        on="SetupId",
        how="outer",
        indicator=True,
    )

    if (merged["_merge"] != "both").any():
        bad_ids = merged.loc[merged["_merge"] != "both", "SetupId"].tolist()
        raise ValueError(
            "Expected one-to-one setup/outcome mapping by SetupId; missing match for SetupId values: "
            f"{sorted(bad_ids)}"
        )

    return merged.drop(columns=["_merge"])



def _numeric_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.mean())


def _numeric_median(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.median())

def _summarize_group(group_df: pd.DataFrame, group_type: str, group_value: str) -> dict:
    sample_count = int(len(group_df))
    return {
        "GroupType": group_type,
        "GroupValue": group_value,
        "SampleCount": sample_count,
        "Mean_MFE_Pct": _numeric_mean(group_df["MFE_Pct"]),
        "Median_MFE_Pct": _numeric_median(group_df["MFE_Pct"]),
        "Mean_MAE_Pct": _numeric_mean(group_df["MAE_Pct"]),
        "Median_MAE_Pct": _numeric_median(group_df["MAE_Pct"]),
        "Mean_CloseReturn_Pct": _numeric_mean(group_df["CloseReturn_Pct"]),
        "Median_CloseReturn_Pct": _numeric_median(group_df["CloseReturn_Pct"]),
        "PositiveCloseReturnRate": (group_df["CloseReturn_Pct"] > 0).mean(),
        "InvalidatedRate": (group_df["LifecycleStatus"] == "INVALIDATED").mean(),
        "ExpiredRate": (group_df["LifecycleStatus"] == "EXPIRED").mean(),
        "PendingRate": (group_df["LifecycleStatus"] == "PENDING").mean(),
        "FullHorizonRate": (group_df["OutcomeStatus"] == "FULL_HORIZON").mean(),
        "PartialHorizonRate": (group_df["OutcomeStatus"] == "PARTIAL_HORIZON").mean(),
        "NoForwardBarsRate": (group_df["OutcomeStatus"] == "NO_FORWARD_BARS").mean(),
    }


def _append_grouped_rows(rows: list[dict], merged: pd.DataFrame, group_type: str, column: str) -> None:
    for group_value in sorted(merged[column].dropna().unique()):
        group = merged.loc[merged[column] == group_value]
        rows.append(_summarize_group(group, group_type, str(group_value)))


def build_setup_report(setups_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic grouped research summary from setup and outcome rows."""
    _validate_required_columns(setups_df, outcomes_df)

    if setups_df.empty and outcomes_df.empty:
        return _empty_report()

    if setups_df.empty != outcomes_df.empty:
        raise ValueError(
            "Expected one-to-one setup/outcome mapping by SetupId; one input is empty and the other is not"
        )

    merged = _strict_merge(setups_df, outcomes_df)

    rows: list[dict] = []
    rows.append(_summarize_group(merged, "overall", "ALL"))
    _append_grouped_rows(rows, merged, "SetupType", "SetupType")
    _append_grouped_rows(rows, merged, "Direction", "Direction")
    _append_grouped_rows(rows, merged, "LifecycleStatus", "LifecycleStatus")
    _append_grouped_rows(rows, merged, "OutcomeStatus", "OutcomeStatus")

    report_df = pd.DataFrame(rows)
    return report_df.loc[:, REPORT_COLUMNS]
