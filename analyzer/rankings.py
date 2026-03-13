"""Research-only ranking/comparison layer for setup reports."""

from __future__ import annotations

import pandas as pd

RANKING_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Baseline_Mean_CloseReturn_Pct",
    "Baseline_PositiveCloseReturnRate",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
    "MinSamplePassed",
    "RankingScore",
    "RankingLabel",
]

MIN_SAMPLE_COUNT = 5

_REQUIRED_INPUT_COLUMNS = {
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
}

_REPORT_GROUP_ORDER = ["SetupType", "Direction", "LifecycleStatus", "OutcomeStatus"]


def _empty_rankings() -> pd.DataFrame:
    return pd.DataFrame(columns=RANKING_COLUMNS)


def _validate_required_columns(df: pd.DataFrame, df_name: str) -> None:
    missing = _REQUIRED_INPUT_COLUMNS - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for setup ranking generation in "
            f"{df_name}: {sorted(missing)}"
        )


def _extract_baseline_row(report_df: pd.DataFrame) -> pd.Series:
    baseline_rows = report_df.loc[
        (report_df["GroupType"] == "overall") & (report_df["GroupValue"] == "ALL")
    ]
    if baseline_rows.empty:
        raise ValueError(
            "Expected exactly one baseline row in report_df where GroupType='overall' and "
            "GroupValue='ALL'; found none"
        )
    if len(baseline_rows) > 1:
        raise ValueError(
            "Expected exactly one baseline row in report_df where GroupType='overall' and "
            f"GroupValue='ALL'; found duplicates: {len(baseline_rows)}"
        )
    return baseline_rows.iloc[0]


def _score_row(candidate_row: pd.Series, baseline_row: pd.Series) -> dict:
    delta_close_return = (
        candidate_row["Mean_CloseReturn_Pct"] - baseline_row["Mean_CloseReturn_Pct"]
    )
    delta_positive_rate = (
        candidate_row["PositiveCloseReturnRate"] - baseline_row["PositiveCloseReturnRate"]
    )
    min_sample_passed = bool(candidate_row["SampleCount"] >= MIN_SAMPLE_COUNT)

    ranking_score = (
        delta_positive_rate
        + 0.1 * delta_close_return
        + 0.02 * candidate_row["Mean_MFE_Pct"]
        + 0.02 * candidate_row["Mean_MAE_Pct"]
    )

    if not min_sample_passed:
        ranking_label = "LOW_SAMPLE"
    elif ranking_score > 0:
        ranking_label = "TOP"
    elif ranking_score == 0:
        ranking_label = "NEUTRAL"
    else:
        ranking_label = "WEAK"

    return {
        "SampleCount": candidate_row["SampleCount"],
        "Mean_CloseReturn_Pct": candidate_row["Mean_CloseReturn_Pct"],
        "PositiveCloseReturnRate": candidate_row["PositiveCloseReturnRate"],
        "Mean_MFE_Pct": candidate_row["Mean_MFE_Pct"],
        "Mean_MAE_Pct": candidate_row["Mean_MAE_Pct"],
        "Baseline_Mean_CloseReturn_Pct": baseline_row["Mean_CloseReturn_Pct"],
        "Baseline_PositiveCloseReturnRate": baseline_row["PositiveCloseReturnRate"],
        "Delta_Mean_CloseReturn_Pct": delta_close_return,
        "Delta_PositiveCloseReturnRate": delta_positive_rate,
        "MinSamplePassed": min_sample_passed,
        "RankingScore": ranking_score,
        "RankingLabel": ranking_label,
    }


def _build_report_rows(report_df: pd.DataFrame, baseline_row: pd.Series) -> list[dict]:
    rows: list[dict] = []
    candidates = report_df.loc[
        report_df["GroupType"].isin(_REPORT_GROUP_ORDER)
        & ~((report_df["GroupType"] == "overall") & (report_df["GroupValue"] == "ALL"))
    ]

    for group_type in _REPORT_GROUP_ORDER:
        family = candidates.loc[candidates["GroupType"] == group_type]
        family = family.sort_values(by=["GroupValue"], kind="stable")
        for _, candidate_row in family.iterrows():
            scored = _score_row(candidate_row, baseline_row)
            rows.append(
                {
                    "SourceReport": "report",
                    "GroupType": candidate_row["GroupType"],
                    "GroupValue": candidate_row["GroupValue"],
                    **scored,
                }
            )

    return rows


def _build_context_rows(context_report_df: pd.DataFrame, baseline_row: pd.Series) -> list[dict]:
    rows: list[dict] = []
    for _, candidate_row in context_report_df.iterrows():
        scored = _score_row(candidate_row, baseline_row)
        rows.append(
            {
                "SourceReport": "context_report",
                "GroupType": candidate_row["GroupType"],
                "GroupValue": candidate_row["GroupValue"],
                **scored,
            }
        )
    return rows


def build_setup_rankings(report_df: pd.DataFrame, context_report_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic ranking rows relative to report overall baseline."""
    _validate_required_columns(report_df, "report_df")
    _validate_required_columns(context_report_df, "context_report_df")

    if report_df.empty:
        if context_report_df.empty:
            return _empty_rankings()
        raise ValueError("Expected non-empty report_df with an overall baseline row for ranking")

    baseline_row = _extract_baseline_row(report_df)

    ranking_rows = _build_report_rows(report_df, baseline_row)
    ranking_rows.extend(_build_context_rows(context_report_df, baseline_row))

    rankings_df = pd.DataFrame(ranking_rows)
    if rankings_df.empty:
        return _empty_rankings()
    return rankings_df.loc[:, RANKING_COLUMNS]
