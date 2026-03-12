"""Research-only grouped context-bucket reporting for setup outcome statistics."""

from __future__ import annotations

import pandas as pd

CONTEXT_REPORT_COLUMNS = [
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
    "FullHorizonRate",
    "PartialHorizonRate",
    "NoForwardBarsRate",
]

_FLAG_FAMILIES = [
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
]

_NUMERIC_FAMILIES = [
    "AbsorptionScore_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
]

_REQUIRED_SETUP_COLUMNS = {
    "SetupId",
    "SetupType",
    "Direction",
    "AbsorptionScore_v1",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
}

_REQUIRED_OUTCOME_COLUMNS = {
    "SetupId",
    "OutcomeStatus",
    "MFE_Pct",
    "MAE_Pct",
    "CloseReturn_Pct",
}

_BUCKET_LABELS = ["LOW", "MID", "HIGH"]


def _empty_context_report() -> pd.DataFrame:
    return pd.DataFrame(columns=CONTEXT_REPORT_COLUMNS)


def _validate_required_columns(setups_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> None:
    missing_setup = _REQUIRED_SETUP_COLUMNS - set(setups_df.columns)
    if missing_setup:
        raise KeyError(
            "Missing required columns for context report generation in setups_df: "
            f"{sorted(missing_setup)}"
        )

    missing_outcomes = _REQUIRED_OUTCOME_COLUMNS - set(outcomes_df.columns)
    if missing_outcomes:
        raise KeyError(
            "Missing required columns for context report generation in outcomes_df: "
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
    return {
        "GroupType": group_type,
        "GroupValue": group_value,
        "SampleCount": int(len(group_df)),
        "Mean_MFE_Pct": _numeric_mean(group_df["MFE_Pct"]),
        "Median_MFE_Pct": _numeric_median(group_df["MFE_Pct"]),
        "Mean_MAE_Pct": _numeric_mean(group_df["MAE_Pct"]),
        "Median_MAE_Pct": _numeric_median(group_df["MAE_Pct"]),
        "Mean_CloseReturn_Pct": _numeric_mean(group_df["CloseReturn_Pct"]),
        "Median_CloseReturn_Pct": _numeric_median(group_df["CloseReturn_Pct"]),
        "PositiveCloseReturnRate": (group_df["CloseReturn_Pct"] > 0).mean(),
        "FullHorizonRate": (group_df["OutcomeStatus"] == "FULL_HORIZON").mean(),
        "PartialHorizonRate": (group_df["OutcomeStatus"] == "PARTIAL_HORIZON").mean(),
        "NoForwardBarsRate": (group_df["OutcomeStatus"] == "NO_FORWARD_BARS").mean(),
    }


def _normalize_flag_value(value: object) -> str | pd.NA:
    if pd.isna(value):
        return pd.NA

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float)):
        if float(value) == 0.0:
            return "0"
        if float(value) == 1.0:
            return "1"
        raise ValueError(f"Context flag value must be binary 0/1; got: {value}")

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"0", "false"}:
            return "0"
        if normalized in {"1", "true"}:
            return "1"
        raise ValueError(f"Context flag value must be binary 0/1; got: {value}")

    raise ValueError(f"Context flag value must be binary 0/1; got unsupported type: {type(value)}")


def _build_flag_rows(merged: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for flag_column in _FLAG_FAMILIES:
        normalized_flags = merged[flag_column].map(_normalize_flag_value)
        present_values = sorted(normalized_flags.dropna().unique())
        for group_value in present_values:
            subset = merged.loc[normalized_flags == group_value]
            rows.append(_summarize_group(subset, flag_column, group_value))
    return rows


def _build_numeric_bucket_rows(merged: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []

    for numeric_column in _NUMERIC_FAMILIES:
        non_null_mask = merged[numeric_column].notna()
        series = pd.to_numeric(merged.loc[non_null_mask, numeric_column], errors="coerce")

        if series.isna().any():
            raise ValueError(
                f"Numeric context column contains non-numeric values: {numeric_column}"
            )

        if series.nunique() < 3:
            raise ValueError(
                "Expected at least 3 distinct non-null values for numeric context bucket generation; "
                f"column={numeric_column}, unique_values={int(series.nunique())}"
            )

        ranks = series.rank(method="first")
        buckets = pd.qcut(ranks, q=3, labels=_BUCKET_LABELS)

        family_df = merged.loc[non_null_mask].copy()
        family_df["_bucket"] = buckets

        present_buckets = set(family_df["_bucket"].astype(str).unique())
        missing = [label for label in _BUCKET_LABELS if label not in present_buckets]
        if missing:
            raise ValueError(
                "Expected LOW/MID/HIGH numeric buckets to be present for context report generation; "
                f"column={numeric_column}, missing={missing}"
            )

        for bucket_label in _BUCKET_LABELS:
            subset = family_df.loc[family_df["_bucket"].astype(str) == bucket_label]
            rows.append(_summarize_group(subset, numeric_column, bucket_label))

    return rows


def build_setup_context_report(setups_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic grouped context-bucket summary from setup and outcome rows."""
    _validate_required_columns(setups_df, outcomes_df)

    if setups_df.empty and outcomes_df.empty:
        return _empty_context_report()

    if setups_df.empty != outcomes_df.empty:
        raise ValueError(
            "Expected one-to-one setup/outcome mapping by SetupId; one input is empty and the other is not"
        )

    merged = _strict_merge(setups_df, outcomes_df)

    rows = _build_flag_rows(merged)
    rows.extend(_build_numeric_bucket_rows(merged))

    context_report_df = pd.DataFrame(rows)
    return context_report_df.loc[:, CONTEXT_REPORT_COLUMNS]
