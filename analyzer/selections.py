"""Research-only deterministic selection layer for setup rankings."""

from __future__ import annotations

import pandas as pd

from analyzer.thresholds import MIN_SAMPLE_COUNT

SELECTION_COLUMNS = [
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

MIN_SELECTION_SCORE = 0.05
MIN_POSITIVE_RATE_DELTA = 0.0

_REQUIRED_RANKING_COLUMNS = {
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SampleCount",
    "RankingScore",
    "RankingLabel",
    "Delta_Mean_CloseReturn_Pct",
    "Delta_PositiveCloseReturnRate",
    "MinSamplePassed",
}


def _empty_selections() -> pd.DataFrame:
    return pd.DataFrame(columns=SELECTION_COLUMNS)


def _validate_required_columns(rankings_df: pd.DataFrame) -> None:
    missing = _REQUIRED_RANKING_COLUMNS - set(rankings_df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for setup selection generation in "
            f"rankings_df: {sorted(missing)}"
        )


def _classify_row(ranking_row: pd.Series) -> tuple[str, str]:
    min_sample_passed = bool(ranking_row["MinSamplePassed"])
    has_min_sample_count = bool(ranking_row["SampleCount"] >= MIN_SAMPLE_COUNT)
    has_positive_delta = bool(ranking_row["Delta_PositiveCloseReturnRate"] > MIN_POSITIVE_RATE_DELTA)
    score = ranking_row["RankingScore"]

    if min_sample_passed and has_min_sample_count and score >= MIN_SELECTION_SCORE and has_positive_delta:
        return "SELECT", "STRONG_POSITIVE_EDGE"

    if min_sample_passed and has_min_sample_count and score > 0:
        return "REVIEW", "POSITIVE_BUT_BORDERLINE"

    if (not min_sample_passed) or (not has_min_sample_count):
        return "REJECT", "LOW_SAMPLE"

    return "REJECT", "NON_POSITIVE_EDGE"


def build_setup_selections(rankings_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic research-only selection decisions from ranking rows."""
    _validate_required_columns(rankings_df)

    if rankings_df.empty:
        return _empty_selections()

    selection_rows: list[dict] = []
    for _, ranking_row in rankings_df.iterrows():
        decision, reason = _classify_row(ranking_row)
        selection_rows.append(
            {
                "SourceReport": ranking_row["SourceReport"],
                "GroupType": ranking_row["GroupType"],
                "GroupValue": ranking_row["GroupValue"],
                "SampleCount": ranking_row["SampleCount"],
                "RankingScore": ranking_row["RankingScore"],
                "RankingLabel": ranking_row["RankingLabel"],
                "Delta_Mean_CloseReturn_Pct": ranking_row["Delta_Mean_CloseReturn_Pct"],
                "Delta_PositiveCloseReturnRate": ranking_row["Delta_PositiveCloseReturnRate"],
                "SelectionDecision": decision,
                "SelectionReason": reason,
            }
        )

    selections_df = pd.DataFrame(selection_rows)
    return selections_df.loc[:, SELECTION_COLUMNS]
