"""Promotion decision layer for Backtester Phase 3 Step 6."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from .robustness import FINAL_STATUSES as FINAL_ROBUSTNESS_STATUSES
from .validation import FINAL_VALIDATION_STATUSES

PROMOTION_COLUMNS = [
    "scope",
    "promotion_decision",
    "validation_status",
    "robustness_status",
    "decision_reason",
    "requires_manual_review",
    "notes",
]

PROMOTION_DETAIL_COLUMNS = [
    "scope",
    "validation_status",
    "robustness_status",
    "matrix_rule",
    "decision",
    "notes",
]

PROMOTION_DECISIONS = ("PROMOTE", "REVIEW", "REJECT")

REQUIRED_VALIDATION_COLUMNS = {"scope", "validation_status"}
REQUIRED_ROBUSTNESS_COLUMNS = {"scope", "robustness_status"}

LIVE_AUTH_DISCLAIMER = "promotion is for execution-design progression only; not approved for live trading"


class PromotionContractError(ValueError):
    """Raised when promotion input/output contract checks fail."""


@dataclass(frozen=True)
class PromotionDecisionRow:
    scope: str
    promotion_decision: str
    validation_status: str
    robustness_status: str
    decision_reason: str
    requires_manual_review: bool
    notes: str


@dataclass(frozen=True)
class PromotionDetailRow:
    scope: str
    validation_status: str
    robustness_status: str
    matrix_rule: str
    decision: str
    notes: str


@dataclass(frozen=True)
class PromotionArtifacts:
    decisions: pd.DataFrame
    details: pd.DataFrame


def _validate_artifact_schema(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise PromotionContractError(f"{name} missing required fields: {missing}")

    if df["scope"].isna().any() or (df["scope"].astype(str).str.strip() == "").any():
        raise PromotionContractError(f"{name} has empty scope values")

    duplicated = df["scope"].astype(str).duplicated(keep=False)
    if duplicated.any():
        dupes = sorted(df.loc[duplicated, "scope"].astype(str).unique().tolist())
        raise PromotionContractError(f"{name} has duplicate scopes: {dupes}")


def _validate_controlled_enums(validation_df: pd.DataFrame, robustness_df: pd.DataFrame) -> None:
    validation_bad = sorted(
        set(validation_df["validation_status"].astype(str).tolist()) - set(FINAL_VALIDATION_STATUSES)
    )
    if validation_bad:
        raise PromotionContractError(
            f"validation_status contains unsupported values: {validation_bad}; expected one of {FINAL_VALIDATION_STATUSES}"
        )

    robustness_bad = sorted(
        set(robustness_df["robustness_status"].astype(str).tolist()) - set(FINAL_ROBUSTNESS_STATUSES)
    )
    if robustness_bad:
        raise PromotionContractError(
            f"robustness_status contains unsupported values: {robustness_bad}; expected one of {FINAL_ROBUSTNESS_STATUSES}"
        )


def _ordered_scopes(validation_df: pd.DataFrame, robustness_df: pd.DataFrame) -> list[str]:
    scopes: list[str] = []
    preferred = ["ALL_TRADES", "RESOLVED_ONLY"]

    v_scopes = validation_df["scope"].astype(str).tolist()
    r_scopes = robustness_df["scope"].astype(str).tolist()

    for scope in preferred:
        if scope in v_scopes and scope not in scopes:
            scopes.append(scope)

    for scope in v_scopes:
        if scope not in scopes:
            scopes.append(scope)

    for scope in r_scopes:
        if scope not in scopes:
            scopes.append(scope)

    return scopes


def _decision_matrix(validation_status: str, robustness_status: str) -> tuple[str, str]:
    if validation_status == "FAIL":
        return "REJECT", "matrix: validation_status == FAIL => REJECT"
    if robustness_status == "FRAGILE":
        return "REJECT", "matrix: robustness_status == FRAGILE => REJECT"
    if validation_status == "PASS" and robustness_status == "ROBUST":
        return "PROMOTE", "matrix: validation_status == PASS and robustness_status == ROBUST => PROMOTE"
    return "REVIEW", "matrix: fallback => REVIEW"


def build_promotion_artifacts(
    *,
    validation_summary_df: pd.DataFrame,
    robustness_summary_df: pd.DataFrame,
    trade_metrics_df: pd.DataFrame | None = None,
    rulesets_df: pd.DataFrame | None = None,
    trade_ledger_df: pd.DataFrame | None = None,
) -> PromotionArtifacts:
    """Build deterministic promotion decisions from validation and robustness artifacts."""
    del trade_metrics_df, rulesets_df, trade_ledger_df

    _validate_artifact_schema(validation_summary_df, REQUIRED_VALIDATION_COLUMNS, "validation artifact")
    _validate_artifact_schema(robustness_summary_df, REQUIRED_ROBUSTNESS_COLUMNS, "robustness artifact")
    _validate_controlled_enums(validation_summary_df, robustness_summary_df)

    validation_lookup = validation_summary_df.copy().set_index(validation_summary_df["scope"].astype(str), drop=False)
    robustness_lookup = robustness_summary_df.copy().set_index(robustness_summary_df["scope"].astype(str), drop=False)

    scopes = _ordered_scopes(validation_summary_df, robustness_summary_df)

    rows: list[PromotionDecisionRow] = []
    details: list[PromotionDetailRow] = []

    for scope in scopes:
        if scope not in validation_lookup.index:
            raise PromotionContractError(
                f"scope '{scope}' exists in robustness artifact but not in validation artifact; refusing promotion decision"
            )

        validation_status = str(validation_lookup.loc[scope, "validation_status"])

        if scope not in robustness_lookup.index:
            decision = "REVIEW"
            matrix_rule = "missing robustness scope => REVIEW"
            robustness_status = "MISSING"
            reason = "robustness scope missing; deterministic non-promote review required"
        else:
            robustness_status = str(robustness_lookup.loc[scope, "robustness_status"])
            decision, matrix_rule = _decision_matrix(validation_status, robustness_status)
            reason = matrix_rule.replace("matrix: ", "")

        requires_manual_review = decision == "REVIEW"
        notes = (
            f"{LIVE_AUTH_DISCLAIMER}; uses only validation+robustness summaries; "
            f"decision surface is deterministic and explicit"
        )

        rows.append(
            PromotionDecisionRow(
                scope=scope,
                promotion_decision=decision,
                validation_status=validation_status,
                robustness_status=robustness_status,
                decision_reason=reason,
                requires_manual_review=requires_manual_review,
                notes=notes,
            )
        )
        details.append(
            PromotionDetailRow(
                scope=scope,
                validation_status=validation_status,
                robustness_status=robustness_status,
                matrix_rule=matrix_rule,
                decision=decision,
                notes=notes,
            )
        )

    decisions_df = pd.DataFrame([asdict(r) for r in rows], columns=PROMOTION_COLUMNS)
    details_df = pd.DataFrame([asdict(r) for r in details], columns=PROMOTION_DETAIL_COLUMNS)

    if not decisions_df["promotion_decision"].isin(PROMOTION_DECISIONS).all():
        raise PromotionContractError("Invalid final promotion_decision values")

    return PromotionArtifacts(decisions=decisions_df, details=details_df)


def write_promotion_csvs(*, artifacts: PromotionArtifacts, output_dir: str | Path) -> Mapping[str, Path]:
    """Persist promotion artifacts to deterministic CSV outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    decisions_path = output_path / "backtest_promotion_decisions.csv"
    details_path = output_path / "backtest_promotion_details.csv"

    artifacts.decisions.to_csv(decisions_path, index=False)
    artifacts.details.to_csv(details_path, index=False)

    return {
        "backtest_promotion_decisions.csv": decisions_path,
        "backtest_promotion_details.csv": details_path,
    }
