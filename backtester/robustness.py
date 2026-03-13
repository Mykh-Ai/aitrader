"""Generalization/fragility robustness checks for Backtester Phase 3 Step 5."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from .ledger import RESOLVED_EXIT_CATEGORIES, validate_trade_ledger

ROBUSTNESS_COLUMNS = [
    "scope",
    "robustness_status",
    "oos_status",
    "walkforward_status",
    "regime_status",
    "perturbation_status",
    "trade_count",
    "resolved_trade_count",
    "notes",
]

ROBUSTNESS_DETAIL_COLUMNS = ["scope", "check", "status", "value", "threshold", "notes"]

SUB_STATUSES = ("ROBUST", "UNSTABLE", "FRAGILE", "NOT_EVALUATED")
FINAL_STATUSES = ("ROBUST", "UNSTABLE", "FRAGILE")
RETURN_COLUMNS_PRIORITY = ("trade_return_pct", "trade_return_r", "trade_pnl")
REGIME_COLUMNS_PRIORITY = ("regime", "volatility_regime", "session")

MIN_RESOLVED_FOR_OOS = 6
MIN_RESOLVED_FOR_WALKFORWARD = 9
WALKFORWARD_WINDOWS = 3
MIN_OOS_SEGMENT_OBS = 2
MIN_REGIME_OBS_PER_LABEL = 3

CRITICAL_CHECKS = ("oos", "walkforward", "regime")
MAX_CRITICAL_NOT_EVALUATED_FOR_ROBUST = 1


class RobustnessContractError(ValueError):
    """Raised when robustness input/output contract checks fail."""


@dataclass(frozen=True)
class RobustnessSummaryRow:
    scope: str
    robustness_status: str
    oos_status: str
    walkforward_status: str
    regime_status: str
    perturbation_status: str
    trade_count: int
    resolved_trade_count: int
    notes: str


@dataclass(frozen=True)
class RobustnessDetailRow:
    scope: str
    check: str
    status: str
    value: str
    threshold: str
    notes: str


@dataclass(frozen=True)
class RobustnessArtifacts:
    summary: pd.DataFrame
    details: pd.DataFrame


def _find_return_column(df: pd.DataFrame) -> str | None:
    for col in RETURN_COLUMNS_PRIORITY:
        if col in df.columns:
            return col
    return None


def _require_sub_status(value: str) -> None:
    if value not in SUB_STATUSES:
        raise RobustnessContractError(f"Invalid robustness sub-status: {value}")


def _prepare_scope_ledger(ordered_ledger: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "ALL_TRADES":
        return ordered_ledger.copy()
    if scope == "RESOLVED_ONLY":
        return ordered_ledger[ordered_ledger["exit_reason_category"].isin(RESOLVED_EXIT_CATEGORIES)].copy()
    return ordered_ledger[ordered_ledger["ruleset_id"].astype(str) == scope].copy()


def _resolved_return_subset(scope_ledger_df: pd.DataFrame, return_column: str | None) -> pd.DataFrame:
    if return_column is None:
        return pd.DataFrame(columns=list(scope_ledger_df.columns) + ["_return_value"])

    resolved = scope_ledger_df[scope_ledger_df["exit_reason_category"].isin(RESOLVED_EXIT_CATEGORIES)].copy()
    resolved["_return_value"] = pd.to_numeric(resolved[return_column], errors="coerce")
    resolved = resolved.dropna(subset=["_return_value", "exit_ts"]) \
        .sort_values(["exit_ts", "trade_id"], kind="mergesort") \
        .reset_index(drop=True)
    return resolved


def _evaluate_oos(resolved_returns_df: pd.DataFrame) -> tuple[str, str, str, str]:
    if len(resolved_returns_df) < MIN_RESOLVED_FOR_OOS:
        return "NOT_EVALUATED", "", f">={MIN_RESOLVED_FOR_OOS} resolved observations", "oos not evaluated: insufficient resolved chronological observations"

    split_idx = int(len(resolved_returns_df) * 0.7)
    split_idx = max(1, min(split_idx, len(resolved_returns_df) - 1))
    is_slice = resolved_returns_df.iloc[:split_idx]
    oos_slice = resolved_returns_df.iloc[split_idx:]
    if len(is_slice) < MIN_OOS_SEGMENT_OBS or len(oos_slice) < MIN_OOS_SEGMENT_OBS:
        return (
            "NOT_EVALUATED",
            "",
            f"IS/OOS slices each require >={MIN_OOS_SEGMENT_OBS} observations",
            "oos not evaluated: deterministic split produced under-supported IS/OOS slices",
        )

    is_mean = float(is_slice["_return_value"].mean())
    oos_mean = float(oos_slice["_return_value"].mean())
    is_pos_rate = float((is_slice["_return_value"] > 0).mean())
    oos_pos_rate = float((oos_slice["_return_value"] > 0).mean())

    degradation_ratio = np.nan
    if is_mean > 0:
        degradation_ratio = oos_mean / is_mean

    if is_mean > 0:
        if oos_mean <= 0 or oos_pos_rate < 0.40:
            status = "FRAGILE"
        elif degradation_ratio >= 0.60 and oos_pos_rate >= 0.50:
            status = "ROBUST"
        else:
            status = "UNSTABLE"
    else:
        status = "UNSTABLE"

    ratio_repr = "nan" if np.isnan(degradation_ratio) else f"{degradation_ratio:.8f}"
    value = (
        f"is_mean={is_mean:.8f};oos_mean={oos_mean:.8f};"
        f"is_pos_rate={is_pos_rate:.4f};oos_pos_rate={oos_pos_rate:.4f};"
        f"degradation_ratio={ratio_repr};split=70/30"
    )
    note = f"oos evaluated from chronological resolved trades; {value}"
    return status, value, "sign, degradation, and minimum-sample consistency", note


def _evaluate_walkforward(resolved_returns_df: pd.DataFrame) -> tuple[str, str, str, str]:
    if len(resolved_returns_df) < MIN_RESOLVED_FOR_WALKFORWARD:
        return "NOT_EVALUATED", "", f">={MIN_RESOLVED_FOR_WALKFORWARD} resolved observations", "walk-forward not evaluated: insufficient resolved chronological observations"

    windows = [list(chunk) for chunk in np.array_split(range(len(resolved_returns_df)), WALKFORWARD_WINDOWS)]
    if not windows or any(len(w) < 2 for w in windows):
        return "NOT_EVALUATED", "", f"{WALKFORWARD_WINDOWS} chronological windows with >=2 obs/window", "walk-forward not evaluated: insufficient window support"

    means: list[float] = []
    for indexes in windows:
        means.append(float(resolved_returns_df.iloc[list(indexes)]["_return_value"].mean()))

    positive = sum(m > 0 for m in means)
    non_positive = sum(m <= 0 for m in means)

    if positive == len(means) and means[-1] >= 0.5 * means[0]:
        status = "ROBUST"
    elif means[0] > 0 and all(m <= 0 for m in means[1:]) and float(np.mean(means[1:])) < 0:
        status = "FRAGILE"
    else:
        status = "UNSTABLE"

    value = "window_means=" + "|".join(f"{m:.8f}" for m in means)
    note = f"walk-forward evaluated with deterministic {WALKFORWARD_WINDOWS} chronological windows; {value}"
    return status, value, "window stability with local-pocket collapse detection", note


def _attach_regime_labels(scope_ledger_df: pd.DataFrame, rulesets_df: pd.DataFrame | None) -> tuple[pd.DataFrame, str | None]:
    for col in REGIME_COLUMNS_PRIORITY:
        if col in scope_ledger_df.columns:
            return scope_ledger_df.copy(), col

    if rulesets_df is not None and "ruleset_id" in rulesets_df.columns:
        for col in REGIME_COLUMNS_PRIORITY:
            if col in rulesets_df.columns:
                enriched = scope_ledger_df.merge(
                    rulesets_df[["ruleset_id", col]].copy(),
                    on="ruleset_id",
                    how="left",
                    sort=False,
                )
                return enriched, col
    return scope_ledger_df.copy(), None


def _evaluate_regime(resolved_returns_df: pd.DataFrame, regime_col: str | None) -> tuple[str, str, str, str]:
    if regime_col is None:
        return "NOT_EVALUATED", "", "explicit regime label required", "regime not evaluated: explicit regime label unavailable"

    work = resolved_returns_df.copy()
    work[regime_col] = work[regime_col].astype(str).replace("", pd.NA)
    work = work.dropna(subset=[regime_col])
    if work.empty:
        return "NOT_EVALUATED", "", ">=2 regimes with resolved returns", "regime not evaluated: no resolved rows with explicit regime labels"

    grouped = work.groupby(regime_col, sort=True)["_return_value"].agg(["count", "mean"]).reset_index()
    grouped = grouped[grouped["count"] >= MIN_REGIME_OBS_PER_LABEL].reset_index(drop=True)
    if len(grouped) < 2:
        return (
            "NOT_EVALUATED",
            "",
            f">=2 regimes with >={MIN_REGIME_OBS_PER_LABEL} observations each",
            "regime not evaluated: insufficient regime coverage",
        )

    means = grouped["mean"].tolist()
    pos = sum(m > 0 for m in means)
    non_pos = sum(m <= 0 for m in means)
    max_count = int(grouped["count"].max())
    total_count = int(grouped["count"].sum())
    concentration = max_count / total_count if total_count else 1.0

    if pos == len(means) and concentration <= 0.75:
        status = "ROBUST"
    elif pos >= 1 and non_pos >= 1 and concentration > 0.70:
        status = "FRAGILE"
    elif pos == 0:
        status = "FRAGILE"
    else:
        status = "UNSTABLE"

    value = ";".join(
        f"{row[regime_col]}:n={int(row['count'])},mean={float(row['mean']):.8f}"
        for _, row in grouped.iterrows()
    )
    note = f"regime evaluated using explicit {regime_col}; {value}"
    return status, value, "cross-regime sign/consistency", note


def _evaluate_perturbation(perturbation_df: pd.DataFrame | None, scope: str) -> tuple[str, str, str, str]:
    if perturbation_df is None or perturbation_df.empty:
        return "NOT_EVALUATED", "", "explicit deterministic perturbation surface", "perturbation not evaluated: no explicit perturbation artifact surface provided"

    if "scope" not in perturbation_df.columns or "status" not in perturbation_df.columns:
        return "NOT_EVALUATED", "", "columns: scope,status", "perturbation not evaluated: required perturbation columns missing"

    scoped = perturbation_df[perturbation_df["scope"].astype(str) == scope]
    if scoped.empty:
        return "NOT_EVALUATED", "", "scope coverage in perturbation artifact", "perturbation not evaluated: no rows for scope"

    statuses = [str(v) for v in scoped["status"].dropna().tolist()]
    if not statuses:
        return "NOT_EVALUATED", "", "non-empty status rows", "perturbation not evaluated: scope has no usable status rows"
    if any(s not in SUB_STATUSES for s in statuses):
        return "NOT_EVALUATED", "", f"status in {SUB_STATUSES}", "perturbation not evaluated: artifact has unsupported status values"

    fragile_count = sum(s == "FRAGILE" for s in statuses)
    robust_count = sum(s == "ROBUST" for s in statuses)
    unstable_count = sum(s == "UNSTABLE" for s in statuses)

    if fragile_count > 0:
        status = "FRAGILE"
    elif robust_count == len(statuses):
        status = "ROBUST"
    else:
        status = "UNSTABLE"

    value = (
        f"rows={len(statuses)};robust={robust_count};"
        f"unstable={unstable_count};fragile={fragile_count}"
    )
    return status, value, "descriptive only (no search/tuning)", "perturbation status consumed from explicit artifact only"


def _combine_final_status(status_by_check: Mapping[str, str]) -> str:
    for status in status_by_check.values():
        _require_sub_status(status)

    critical_not_evaluated = sum(status_by_check.get(check) == "NOT_EVALUATED" for check in CRITICAL_CHECKS)
    evaluated = [s for s in status_by_check.values() if s != "NOT_EVALUATED"]
    if not evaluated:
        return "UNSTABLE"
    if any(s == "FRAGILE" for s in evaluated):
        return "FRAGILE"
    if any(s == "UNSTABLE" for s in evaluated):
        return "UNSTABLE"
    if critical_not_evaluated > MAX_CRITICAL_NOT_EVALUATED_FOR_ROBUST:
        return "UNSTABLE"
    return "ROBUST"


def build_robustness_artifacts(
    *,
    trade_ledger_df: pd.DataFrame,
    trade_metrics_df: pd.DataFrame | None = None,
    validation_df: pd.DataFrame | None = None,
    rulesets_df: pd.DataFrame | None = None,
    perturbation_df: pd.DataFrame | None = None,
) -> RobustnessArtifacts:
    """Build deterministic robustness artifacts from existing backtester artifacts only."""
    del trade_metrics_df, validation_df

    validate_trade_ledger(trade_ledger_df)
    ordered_ledger = trade_ledger_df.sort_values(["entry_activation_ts", "trade_id"], kind="mergesort").reset_index(drop=True)

    scopes = ["ALL_TRADES", "RESOLVED_ONLY"]
    for ruleset_id in ordered_ledger["ruleset_id"].astype(str).drop_duplicates().tolist():
        if ruleset_id not in scopes:
            scopes.append(ruleset_id)

    summary_rows: list[RobustnessSummaryRow] = []
    detail_rows: list[RobustnessDetailRow] = []

    for scope in scopes:
        scope_ledger = _prepare_scope_ledger(ordered_ledger, scope)
        trade_count = int(len(scope_ledger))
        resolved_trade_count = int(scope_ledger["exit_reason_category"].isin(RESOLVED_EXIT_CATEGORIES).sum())

        return_column = _find_return_column(scope_ledger)
        resolved_returns = _resolved_return_subset(scope_ledger, return_column)

        if return_column is None:
            oos_status, oos_value, oos_threshold, oos_note = (
                "NOT_EVALUATED",
                "",
                "explicit return-like field required",
                "oos not evaluated: no explicit trustworthy return-like field in ledger",
            )
            walk_status, walk_value, walk_threshold, walk_note = (
                "NOT_EVALUATED",
                "",
                "explicit return-like field required",
                "walk-forward not evaluated: no explicit trustworthy return-like field in ledger",
            )
        else:
            oos_status, oos_value, oos_threshold, oos_note = _evaluate_oos(resolved_returns)
            walk_status, walk_value, walk_threshold, walk_note = _evaluate_walkforward(resolved_returns)

        regime_input, regime_col = _attach_regime_labels(scope_ledger, rulesets_df)
        regime_resolved = _resolved_return_subset(regime_input, return_column)
        regime_status, regime_value, regime_threshold, regime_note = _evaluate_regime(regime_resolved, regime_col)

        perturb_status, perturb_value, perturb_threshold, perturb_note = _evaluate_perturbation(perturbation_df, scope)

        final_status = _combine_final_status(
            {
                "oos": oos_status,
                "walkforward": walk_status,
                "regime": regime_status,
                "perturbation": perturb_status,
            }
        )

        notes = (
            f"return_basis={'none' if return_column is None else return_column}; "
            f"unresolved trades excluded from return-based checks={trade_count - resolved_trade_count}; "
            f"{oos_note}; {walk_note}; {regime_note}; {perturb_note}"
        )

        summary_rows.append(
            RobustnessSummaryRow(
                scope=str(scope),
                robustness_status=final_status,
                oos_status=oos_status,
                walkforward_status=walk_status,
                regime_status=regime_status,
                perturbation_status=perturb_status,
                trade_count=trade_count,
                resolved_trade_count=resolved_trade_count,
                notes=notes,
            )
        )

        detail_rows.extend(
            [
                RobustnessDetailRow(str(scope), "oos", oos_status, oos_value, oos_threshold, oos_note),
                RobustnessDetailRow(str(scope), "walkforward", walk_status, walk_value, walk_threshold, walk_note),
                RobustnessDetailRow(str(scope), "regime", regime_status, regime_value, regime_threshold, regime_note),
                RobustnessDetailRow(str(scope), "perturbation", perturb_status, perturb_value, perturb_threshold, perturb_note),
            ]
        )

    summary_df = pd.DataFrame([asdict(r) for r in summary_rows], columns=ROBUSTNESS_COLUMNS)
    details_df = pd.DataFrame([asdict(r) for r in detail_rows], columns=ROBUSTNESS_DETAIL_COLUMNS)

    for col in ["oos_status", "walkforward_status", "regime_status", "perturbation_status"]:
        if not summary_df[col].isin(SUB_STATUSES).all():
            raise RobustnessContractError(f"Invalid controlled values in {col}")
    if not summary_df["robustness_status"].isin(FINAL_STATUSES).all():
        raise RobustnessContractError("Invalid final robustness_status values")

    return RobustnessArtifacts(summary=summary_df, details=details_df)


def write_robustness_csvs(*, artifacts: RobustnessArtifacts, output_dir: str | Path) -> Mapping[str, Path]:
    """Persist robustness artifacts to deterministic CSV outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "backtest_robustness_summary.csv"
    details_path = output_path / "backtest_robustness_details.csv"

    artifacts.summary.to_csv(summary_path, index=False)
    artifacts.details.to_csv(details_path, index=False)

    return {
        "backtest_robustness_summary.csv": summary_path,
        "backtest_robustness_details.csv": details_path,
    }
