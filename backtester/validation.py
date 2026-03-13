"""Statistical acceptance validation for Backtester Phase 3 Step 4."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from .ledger import RESOLVED_EXIT_CATEGORIES, validate_trade_ledger

VALIDATION_COLUMNS = [
    "scope",
    "validation_status",
    "sample_sufficiency_status",
    "expectancy_status",
    "drawdown_status",
    "outlier_dependence_status",
    "long_short_asymmetry_status",
    "source_concentration_status",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "notes",
]

VALIDATION_DETAIL_COLUMNS = ["scope", "check", "status", "value", "threshold", "notes"]

VALID_STATUSES = ("PASS", "REVIEW", "FAIL", "NOT_EVALUATED")
FINAL_VALIDATION_STATUSES = ("PASS", "REVIEW", "FAIL")

REQUIRED_METRICS_COLUMNS = {
    "scope",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "long_trade_count",
    "short_trade_count",
    "expectancy",
    "notes",
}

RETURN_COLUMNS_PRIORITY = ("trade_return_pct", "trade_pnl", "trade_return_r")
SOURCE_GROUP_COLUMNS_PRIORITY = (
    "source_report",
    "source_family",
    "source_candidate_group",
    "source_lineage_artifact",
)
RULESET_SOURCE_COLUMNS_PRIORITY = ("source_candidate_group", "source_lineage_artifact")
NON_ECONOMIC_DRAWDOWN_BASES = {"RESOLVED_TRADE_COUNT"}
MAX_PASS_NOT_EVALUATED_CRITICAL = 1


class ValidationContractError(ValueError):
    """Raised when validation input/output contract checks fail."""


@dataclass(frozen=True)
class ValidationSummaryRow:
    scope: str
    validation_status: str
    sample_sufficiency_status: str
    expectancy_status: str
    drawdown_status: str
    outlier_dependence_status: str
    long_short_asymmetry_status: str
    source_concentration_status: str
    trade_count: int
    resolved_trade_count: int
    unresolved_trade_count: int
    notes: str


@dataclass(frozen=True)
class ValidationDetailRow:
    scope: str
    check: str
    status: str
    value: str
    threshold: str
    notes: str


@dataclass(frozen=True)
class ValidationArtifacts:
    summary: pd.DataFrame
    details: pd.DataFrame


def _require_status(value: str) -> None:
    if value not in VALID_STATUSES:
        raise ValidationContractError(f"Invalid status value: {value}")


def _status_from_resolved_count(resolved_trade_count: int) -> str:
    if resolved_trade_count >= 20:
        return "PASS"
    if resolved_trade_count >= 5:
        return "REVIEW"
    return "FAIL"


def _extract_expectancy_basis(metrics_row: pd.Series) -> str | None:
    for column in ("expectancy_basis", "return_metric_basis", "economic_return_basis"):
        if column not in metrics_row.index:
            continue
        value = str(metrics_row.get(column, "")).strip()
        if value and value.upper() not in NON_ECONOMIC_DRAWDOWN_BASES:
            return value
    return None


def _expectancy_status(metrics_row: pd.Series) -> tuple[str, str]:
    expectancy = pd.to_numeric(pd.Series([metrics_row.get("expectancy")]), errors="coerce").iloc[0]
    if pd.isna(expectancy):
        return "NOT_EVALUATED", "expectancy not evaluated: no explicit trustworthy expectancy metric in artifact"
    expectancy_basis = _extract_expectancy_basis(metrics_row)
    if expectancy_basis is None:
        return "NOT_EVALUATED", "expectancy not evaluated: no explicit economic expectancy basis"

    if float(expectancy) > 0:
        return "PASS", f"expectancy={float(expectancy):.8f} (>0), basis={expectancy_basis}"
    if float(expectancy) < 0:
        return "FAIL", f"expectancy={float(expectancy):.8f} (<0), basis={expectancy_basis}"
    return "REVIEW", f"expectancy=0, basis={expectancy_basis}"


def _drawdown_status(drawdown_df: pd.DataFrame | None) -> tuple[str, str]:
    if drawdown_df is None or drawdown_df.empty:
        return "NOT_EVALUATED", "drawdown not evaluated: drawdown artifact unavailable"
    if "drawdown_basis" not in drawdown_df.columns:
        return "NOT_EVALUATED", "drawdown not evaluated: drawdown_basis missing"

    bases = sorted({str(v) for v in drawdown_df["drawdown_basis"].dropna().tolist()})
    if not bases:
        return "NOT_EVALUATED", "drawdown not evaluated: empty drawdown basis"

    if any(base in NON_ECONOMIC_DRAWDOWN_BASES for base in bases):
        return "NOT_EVALUATED", f"drawdown not evaluated: non-economic basis present={bases}"

    max_drawdown = pd.to_numeric(drawdown_df.get("drawdown_value"), errors="coerce").dropna().max()
    if pd.isna(max_drawdown):
        return "NOT_EVALUATED", "drawdown not evaluated: drawdown_value unavailable"
    if float(max_drawdown) <= 0.08:
        return "PASS", f"max_drawdown={float(max_drawdown):.6f} <= 0.08 on economic basis={bases}"
    if float(max_drawdown) <= 0.15:
        return "REVIEW", f"max_drawdown={float(max_drawdown):.6f} in (0.08, 0.15] on economic basis={bases}"
    return "FAIL", f"max_drawdown={float(max_drawdown):.6f} > 0.15 on economic basis={bases}"


def _find_return_column(ledger_df: pd.DataFrame) -> str | None:
    for col in RETURN_COLUMNS_PRIORITY:
        if col not in ledger_df.columns:
            continue
        series = pd.to_numeric(ledger_df[col], errors="coerce")
        if series.notna().any():
            return col
    return None


def _outlier_dependence_status(scope_ledger_df: pd.DataFrame) -> tuple[str, str]:
    return_column = _find_return_column(scope_ledger_df)
    if return_column is None:
        return "NOT_EVALUATED", "outlier dependence not evaluated: no explicit return field"

    returns = pd.to_numeric(scope_ledger_df[return_column], errors="coerce").dropna()
    positive = returns[returns > 0]
    if positive.empty:
        return "NOT_EVALUATED", "outlier dependence not evaluated: no positive return contributions"

    total_positive = float(positive.sum())
    if total_positive <= 0:
        return "NOT_EVALUATED", "outlier dependence not evaluated: non-positive total positive contribution"

    sorted_positive = positive.sort_values(ascending=False)
    top1_share = float(sorted_positive.iloc[:1].sum() / total_positive)
    top2_share = float(sorted_positive.iloc[:2].sum() / total_positive)

    if top1_share > 0.80 or top2_share > 0.95:
        return "FAIL", f"provisional outlier concentration top1={top1_share:.4f}, top2={top2_share:.4f}"
    if top1_share > 0.60 or top2_share > 0.85:
        return "REVIEW", f"provisional outlier concentration top1={top1_share:.4f}, top2={top2_share:.4f}"
    return "PASS", f"provisional outlier concentration top1={top1_share:.4f}, top2={top2_share:.4f}"


def _worst_evaluated_status(*statuses: str) -> str:
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    return max(statuses, key=lambda status: order[status])


def _long_short_asymmetry_status(metrics_row: pd.Series, scope_ledger_df: pd.DataFrame) -> tuple[str, str]:
    long_count = int(metrics_row["long_trade_count"])
    short_count = int(metrics_row["short_trade_count"])
    if long_count == 0 or short_count == 0:
        return "NOT_EVALUATED", "long/short asymmetry not evaluated: one side has zero observations"

    ratio = max(long_count, short_count) / min(long_count, short_count)
    count_status: str
    if ratio > 4.0:
        count_status = "FAIL"
    elif ratio > 2.0:
        count_status = "REVIEW"
    else:
        count_status = "PASS"

    return_column = _find_return_column(scope_ledger_df)
    if return_column is None:
        return count_status, f"count asymmetry ratio={ratio:.4f}; side expectancy not evaluated: no explicit return field"

    side_df = scope_ledger_df.copy()
    side_df["_return"] = pd.to_numeric(side_df[return_column], errors="coerce")
    side_df["_direction"] = side_df["direction"].astype(str).str.upper()
    side_df = side_df[side_df["_direction"].isin(["LONG", "SHORT"]) & side_df["_return"].notna()]

    if side_df.empty:
        return count_status, f"count asymmetry ratio={ratio:.4f}; side expectancy not evaluated: no numeric side returns"

    mean_long = side_df.loc[side_df["_direction"] == "LONG", "_return"].mean()
    mean_short = side_df.loc[side_df["_direction"] == "SHORT", "_return"].mean()
    if pd.isna(mean_long) or pd.isna(mean_short):
        return count_status, f"count asymmetry ratio={ratio:.4f}; side expectancy not evaluated: one side lacks numeric returns"

    if float(mean_long) * float(mean_short) < 0:
        side_status = "FAIL"
    else:
        abs_long = abs(float(mean_long))
        abs_short = abs(float(mean_short))
        if abs_long == 0 or abs_short == 0:
            side_status = "REVIEW" if abs_long != abs_short else "PASS"
        else:
            mean_ratio = max(abs_long, abs_short) / min(abs_long, abs_short)
            if mean_ratio > 4.0:
                side_status = "FAIL"
            elif mean_ratio > 2.0:
                side_status = "REVIEW"
            else:
                side_status = "PASS"

    combined = _worst_evaluated_status(count_status, side_status)
    return combined, (
        f"count asymmetry ratio={ratio:.4f}; side_mean_long={float(mean_long):.8f}; "
        f"side_mean_short={float(mean_short):.8f}; combined={combined}"
    )


def _best_source_group_series(scope_ledger_df: pd.DataFrame, rulesets_df: pd.DataFrame | None) -> tuple[pd.Series | None, str]:
    for column in SOURCE_GROUP_COLUMNS_PRIORITY:
        if column not in scope_ledger_df.columns:
            continue
        values = scope_ledger_df[column].astype(str).replace("", pd.NA).dropna()
        if not values.empty:
            return values, column

    if rulesets_df is not None and not rulesets_df.empty:
        if "ruleset_id" in rulesets_df.columns and "ruleset_id" in scope_ledger_df.columns:
            for column in RULESET_SOURCE_COLUMNS_PRIORITY:
                if column not in rulesets_df.columns:
                    continue
                mapping = rulesets_df[["ruleset_id", column]].copy()
                mapping["ruleset_id"] = mapping["ruleset_id"].astype(str)
                mapped = scope_ledger_df["ruleset_id"].astype(str).map(mapping.set_index("ruleset_id")[column])
                values = mapped.astype(str).replace("", pd.NA).dropna()
                if not values.empty:
                    return values, f"rulesets_df.{column}"

    if "source_setup_id" in scope_ledger_df.columns:
        values = scope_ledger_df["source_setup_id"].astype(str).replace("", pd.NA).dropna()
        if not values.empty:
            return values, "source_setup_id"

    return None, ""


def _source_concentration_status(scope_ledger_df: pd.DataFrame, rulesets_df: pd.DataFrame | None) -> tuple[str, str]:
    source_values, source_surface = _best_source_group_series(scope_ledger_df, rulesets_df)
    if source_values is None:
        return "NOT_EVALUATED", "source concentration not evaluated: no explicit source grouping values available"

    source_counts = source_values.value_counts(sort=True)
    if source_counts.empty:
        return "NOT_EVALUATED", "source concentration not evaluated: explicit source grouping unavailable"

    max_share = float(source_counts.iloc[0] / source_counts.sum())
    if max_share > 0.80:
        return "FAIL", f"source concentration max_share={max_share:.4f} (>0.80), source_surface={source_surface}"
    if max_share > 0.60:
        return "REVIEW", f"source concentration max_share={max_share:.4f} (>0.60), source_surface={source_surface}"
    return "PASS", f"source concentration max_share={max_share:.4f}, source_surface={source_surface}"


def _combine_final_status(sub_statuses: list[str], critical_sub_statuses: list[str]) -> str:
    for status in sub_statuses:
        _require_status(status)
    for status in critical_sub_statuses:
        _require_status(status)

    if any(status == "FAIL" for status in sub_statuses):
        return "FAIL"
    if any(status == "REVIEW" for status in sub_statuses):
        return "REVIEW"
    critical_not_evaluated_count = sum(status == "NOT_EVALUATED" for status in critical_sub_statuses)
    if critical_not_evaluated_count > MAX_PASS_NOT_EVALUATED_CRITICAL:
        return "REVIEW"
    return "PASS"


def _validate_inputs(trade_ledger_df: pd.DataFrame, trade_metrics_df: pd.DataFrame) -> None:
    validate_trade_ledger(trade_ledger_df)
    missing = sorted(REQUIRED_METRICS_COLUMNS - set(trade_metrics_df.columns))
    if missing:
        raise ValidationContractError(f"Trade metrics artifact missing required fields: {missing}")


def _build_scope_ledger(ordered_ledger: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "ALL_TRADES":
        return ordered_ledger
    if scope == "RESOLVED_ONLY":
        return ordered_ledger[ordered_ledger["exit_reason_category"].isin(RESOLVED_EXIT_CATEGORIES)].copy()
    return ordered_ledger[ordered_ledger["ruleset_id"].astype(str) == scope].copy()


def build_validation_artifacts(
    *,
    trade_ledger_df: pd.DataFrame,
    trade_metrics_df: pd.DataFrame,
    drawdown_df: pd.DataFrame | None = None,
    rulesets_df: pd.DataFrame | None = None,
) -> ValidationArtifacts:
    """Build deterministic statistical acceptance validation artifacts."""
    _validate_inputs(trade_ledger_df, trade_metrics_df)
    ordered_ledger = trade_ledger_df.sort_values(["entry_activation_ts", "trade_id"], kind="mergesort").reset_index(drop=True)
    ordered_metrics = trade_metrics_df.sort_values(["scope"], kind="mergesort").reset_index(drop=True)

    preferred_scope_order = ["ALL_TRADES", "RESOLVED_ONLY"]
    scopes = [s for s in preferred_scope_order if s in set(ordered_metrics["scope"]) ]
    for scope in ordered_metrics["scope"].astype(str).tolist():
        if scope not in scopes:
            scopes.append(scope)

    summary_rows: list[ValidationSummaryRow] = []
    detail_rows: list[ValidationDetailRow] = []

    for scope in scopes:
        metrics_row = ordered_metrics.loc[ordered_metrics["scope"] == scope].iloc[0]
        scope_ledger = _build_scope_ledger(ordered_ledger, scope)

        trade_count = int(metrics_row["trade_count"])
        resolved_trade_count = int(metrics_row["resolved_trade_count"])
        unresolved_trade_count = int(metrics_row["unresolved_trade_count"])

        sample_status = _status_from_resolved_count(resolved_trade_count)
        expectancy_status, expectancy_note = _expectancy_status(metrics_row)
        drawdown_status, drawdown_note = _drawdown_status(drawdown_df)
        outlier_status, outlier_note = _outlier_dependence_status(scope_ledger)
        asymmetry_status, asymmetry_note = _long_short_asymmetry_status(metrics_row, scope_ledger)
        source_status, source_note = _source_concentration_status(scope_ledger, rulesets_df)

        validation_status = _combine_final_status(
            [sample_status, expectancy_status, drawdown_status, outlier_status, asymmetry_status, source_status],
            [expectancy_status, drawdown_status, outlier_status, asymmetry_status, source_status],
        )
        if validation_status not in FINAL_VALIDATION_STATUSES:
            raise ValidationContractError(f"Invalid final validation_status: {validation_status}")

        notes = (
            "provisional thresholds used for sample/asymmetry/source/outlier; "
            f"unresolved trades explicit={unresolved_trade_count}; "
            f"{expectancy_note}; {drawdown_note}; {outlier_note}; {asymmetry_note}; {source_note}"
        )

        summary_rows.append(
            ValidationSummaryRow(
                scope=str(scope),
                validation_status=validation_status,
                sample_sufficiency_status=sample_status,
                expectancy_status=expectancy_status,
                drawdown_status=drawdown_status,
                outlier_dependence_status=outlier_status,
                long_short_asymmetry_status=asymmetry_status,
                source_concentration_status=source_status,
                trade_count=trade_count,
                resolved_trade_count=resolved_trade_count,
                unresolved_trade_count=unresolved_trade_count,
                notes=notes,
            )
        )

        detail_rows.extend(
            [
                ValidationDetailRow(str(scope), "sample_sufficiency", sample_status, str(resolved_trade_count), ">=20 PASS, >=5 REVIEW", "provisional"),
                ValidationDetailRow(str(scope), "expectancy", expectancy_status, str(metrics_row.get("expectancy")), ">0 PASS, =0 REVIEW, <0 FAIL", expectancy_note),
                ValidationDetailRow(str(scope), "drawdown", drawdown_status, "", "economic basis required", drawdown_note),
                ValidationDetailRow(str(scope), "outlier_dependence", outlier_status, "", "top1/top2 positive contribution concentration", outlier_note),
                ValidationDetailRow(str(scope), "long_short_asymmetry", asymmetry_status, f"L={int(metrics_row['long_trade_count'])},S={int(metrics_row['short_trade_count'])}", "ratio>4 FAIL, >2 REVIEW", asymmetry_note),
                ValidationDetailRow(str(scope), "source_concentration", source_status, "", "max source share >0.80 FAIL, >0.60 REVIEW", source_note),
            ]
        )

    summary_df = pd.DataFrame([asdict(r) for r in summary_rows], columns=VALIDATION_COLUMNS)
    details_df = pd.DataFrame([asdict(r) for r in detail_rows], columns=VALIDATION_DETAIL_COLUMNS)

    if summary_df["scope"].isna().any() or (summary_df["scope"].astype(str).str.strip() == "").any():
        raise ValidationContractError("Validation summary has empty scope values")

    for col in [
        "sample_sufficiency_status",
        "expectancy_status",
        "drawdown_status",
        "outlier_dependence_status",
        "long_short_asymmetry_status",
        "source_concentration_status",
    ]:
        if not summary_df[col].isin(VALID_STATUSES).all():
            raise ValidationContractError(f"Validation summary has invalid controlled values in {col}")

    if not summary_df["validation_status"].isin(FINAL_VALIDATION_STATUSES).all():
        raise ValidationContractError("Validation summary has invalid validation_status values")

    return ValidationArtifacts(summary=summary_df, details=details_df)


def write_validation_csvs(*, artifacts: ValidationArtifacts, output_dir: str | Path) -> Mapping[str, Path]:
    """Persist validation artifacts to deterministic CSV outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "backtest_validation_summary.csv"
    details_path = output_path / "backtest_validation_details.csv"

    artifacts.summary.to_csv(summary_path, index=False)
    artifacts.details.to_csv(details_path, index=False)

    return {
        "backtest_validation_summary.csv": summary_path,
        "backtest_validation_details.csv": details_path,
    }
