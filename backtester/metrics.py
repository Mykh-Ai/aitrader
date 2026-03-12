"""Trade-level metrics aggregation for Backtester Phase 3 Step 3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from .ledger import RESOLVED_EXIT_CATEGORIES, validate_trade_ledger

TRADE_METRICS_COLUMNS = [
    "scope",
    "trade_count",
    "resolved_trade_count",
    "unresolved_trade_count",
    "long_trade_count",
    "short_trade_count",
    "average_holding_bars",
    "median_holding_bars",
    "win_rate",
    "average_win",
    "average_loss",
    "payoff_ratio",
    "expectancy",
    "notes",
]

EQUITY_CURVE_COLUMNS = [
    "sequence",
    "trade_id",
    "ruleset_id",
    "exit_ts",
    "equity_step_value",
    "equity_basis",
    "notes",
]

DRAWDOWN_COLUMNS = [
    "sequence",
    "trade_id",
    "ruleset_id",
    "exit_ts",
    "equity_step_value",
    "peak_equity_value",
    "drawdown_value",
    "drawdown_basis",
    "notes",
]

EXIT_REASON_SUMMARY_COLUMNS = [
    "exit_reason",
    "exit_reason_category",
    "trade_count",
    "scope",
]

REQUIRED_LEDGER_COLUMNS = {
    "trade_id",
    "ruleset_id",
    "direction",
    "exit_ts",
    "exit_reason",
    "exit_reason_category",
    "holding_bars",
}

RETURN_COLUMNS_PRIORITY = ("trade_return_pct", "trade_return_r", "trade_pnl")


class MetricsContractError(ValueError):
    """Raised when metrics input/output contract checks fail."""


@dataclass(frozen=True)
class TradeMetricsRow:
    scope: str
    trade_count: int
    resolved_trade_count: int
    unresolved_trade_count: int
    long_trade_count: int
    short_trade_count: int
    average_holding_bars: float | None
    median_holding_bars: float | None
    win_rate: float | None
    average_win: float | None
    average_loss: float | None
    payoff_ratio: float | None
    expectancy: float | None
    notes: str


@dataclass(frozen=True)
class EquityCurveRow:
    sequence: int
    trade_id: str
    ruleset_id: str
    exit_ts: pd.Timestamp
    equity_step_value: float
    equity_basis: str
    notes: str


@dataclass(frozen=True)
class DrawdownRow:
    sequence: int
    trade_id: str
    ruleset_id: str
    exit_ts: pd.Timestamp
    equity_step_value: float
    peak_equity_value: float
    drawdown_value: float
    drawdown_basis: str
    notes: str


@dataclass(frozen=True)
class ExitReasonSummaryRow:
    exit_reason: str
    exit_reason_category: str
    trade_count: int
    scope: str


@dataclass(frozen=True)
class MetricsArtifacts:
    trade_metrics: pd.DataFrame
    equity_curve: pd.DataFrame
    drawdown: pd.DataFrame
    exit_reason_summary: pd.DataFrame


def _validate_metrics_input(ledger_df: pd.DataFrame) -> None:
    validate_trade_ledger(ledger_df)
    missing = sorted(REQUIRED_LEDGER_COLUMNS - set(ledger_df.columns))
    if missing:
        raise MetricsContractError(f"Trade ledger missing required metrics fields: {missing}")


def _resolved_mask(ledger_df: pd.DataFrame) -> pd.Series:
    return ledger_df["exit_reason_category"].isin(RESOLVED_EXIT_CATEGORIES)


def _safe_holding_stats(ledger_df: pd.DataFrame) -> tuple[float | None, float | None]:
    holding = ledger_df["holding_bars"].dropna()
    if holding.empty:
        return None, None
    return float(holding.mean()), float(holding.median())


def _find_return_column(ledger_df: pd.DataFrame) -> str | None:
    for column in RETURN_COLUMNS_PRIORITY:
        if column in ledger_df.columns:
            return column
    return None


def _return_metrics(ledger_df: pd.DataFrame, return_column: str | None) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    if return_column is None:
        return None, None, None, None, None

    series = pd.to_numeric(ledger_df[return_column], errors="coerce").dropna()
    if series.empty:
        return None, None, None, None, None

    wins = series[series > 0]
    losses = series[series < 0]
    win_rate = float((series > 0).mean())
    average_win = float(wins.mean()) if not wins.empty else None
    average_loss = float(losses.mean()) if not losses.empty else None

    if average_win is None or average_loss is None or average_loss == 0:
        payoff_ratio = None
    else:
        payoff_ratio = float(abs(average_win / average_loss))

    expectancy = float(series.mean())
    return win_rate, average_win, average_loss, payoff_ratio, expectancy


def _build_trade_metrics_summary(ledger_df: pd.DataFrame) -> pd.DataFrame:
    resolved_df = ledger_df[_resolved_mask(ledger_df)].copy()

    return_column = _find_return_column(resolved_df)
    missing_return_note = (
        "return metrics omitted: ledger has no explicit return/PnL contract field"
        if return_column is None
        else f"return metrics computed from explicit {return_column}"
    )

    rows: list[TradeMetricsRow] = []
    scopes = (("ALL_TRADES", ledger_df), ("RESOLVED_ONLY", resolved_df))
    for scope_name, scope_df in scopes:
        avg_holding, med_holding = _safe_holding_stats(scope_df)
        win_rate, average_win, average_loss, payoff_ratio, expectancy = _return_metrics(
            scope_df,
            return_column,
        )

        row = TradeMetricsRow(
            scope=scope_name,
            trade_count=int(len(scope_df)),
            resolved_trade_count=int(_resolved_mask(scope_df).sum()),
            unresolved_trade_count=int((~_resolved_mask(scope_df)).sum()),
            long_trade_count=int((scope_df["direction"].astype(str).str.upper() == "LONG").sum()),
            short_trade_count=int((scope_df["direction"].astype(str).str.upper() == "SHORT").sum()),
            average_holding_bars=avg_holding,
            median_holding_bars=med_holding,
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            payoff_ratio=payoff_ratio,
            expectancy=expectancy,
            notes=(
                f"scope={scope_name}; includes unresolved counts explicitly; {missing_return_note}"
                if scope_name == "ALL_TRADES"
                else f"scope={scope_name}; resolved subset only; {missing_return_note}"
            ),
        )
        rows.append(row)

    return pd.DataFrame([asdict(r) for r in rows], columns=TRADE_METRICS_COLUMNS)


def _build_exit_reason_summary(ledger_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        ledger_df.groupby(["exit_reason", "exit_reason_category"], dropna=False, sort=True)
        .size()
        .reset_index(name="trade_count")
        .sort_values(["exit_reason_category", "exit_reason"], kind="mergesort")
        .reset_index(drop=True)
    )
    grouped["scope"] = "ALL_TRADES"
    return grouped[EXIT_REASON_SUMMARY_COLUMNS]


def _build_equity_curve(ledger_df: pd.DataFrame) -> pd.DataFrame:
    resolved = ledger_df[_resolved_mask(ledger_df)].copy()
    if resolved.empty:
        return pd.DataFrame(columns=EQUITY_CURVE_COLUMNS)

    resolved = resolved.sort_values(["exit_ts", "trade_id"], kind="mergesort").reset_index(drop=True)
    if resolved["exit_ts"].isna().any():
        raise MetricsContractError("Resolved trades must have non-null exit_ts for equity curve")

    rows: list[EquityCurveRow] = []
    for idx, row in enumerate(resolved.itertuples(index=False), start=1):
        rows.append(
            EquityCurveRow(
                sequence=idx,
                trade_id=str(row.trade_id),
                ruleset_id=str(row.ruleset_id),
                exit_ts=row.exit_ts,
                equity_step_value=float(idx),
                equity_basis="RESOLVED_TRADE_COUNT",
                notes="not monetary equity; cumulative resolved trade count",
            )
        )

    equity_df = pd.DataFrame([asdict(r) for r in rows], columns=EQUITY_CURVE_COLUMNS)
    if equity_df["sequence"].duplicated().any():
        raise MetricsContractError("Duplicate sequence values in equity curve")
    return equity_df


def _build_drawdown(equity_df: pd.DataFrame) -> pd.DataFrame:
    if equity_df.empty:
        return pd.DataFrame(columns=DRAWDOWN_COLUMNS)

    peak = equity_df["equity_step_value"].cummax()
    drawdown = peak - equity_df["equity_step_value"]

    rows: list[DrawdownRow] = []
    for row, peak_value, drawdown_value in zip(equity_df.itertuples(index=False), peak, drawdown):
        rows.append(
            DrawdownRow(
                sequence=int(row.sequence),
                trade_id=str(row.trade_id),
                ruleset_id=str(row.ruleset_id),
                exit_ts=row.exit_ts,
                equity_step_value=float(row.equity_step_value),
                peak_equity_value=float(peak_value),
                drawdown_value=float(drawdown_value),
                drawdown_basis=str(row.equity_basis),
                notes="drawdown computed on declared equity basis",
            )
        )

    drawdown_df = pd.DataFrame([asdict(r) for r in rows], columns=DRAWDOWN_COLUMNS)
    if drawdown_df["sequence"].duplicated().any():
        raise MetricsContractError("Duplicate sequence values in drawdown artifact")
    if (drawdown_df["drawdown_value"] < 0).any():
        raise MetricsContractError("Negative drawdown_value detected")
    return drawdown_df


def build_trade_metrics_artifacts(
    ledger_df: pd.DataFrame,
    *,
    rulesets_df: pd.DataFrame | None = None,
) -> MetricsArtifacts:
    """Build deterministic metric artifacts from trade ledger ground truth."""
    del rulesets_df

    _validate_metrics_input(ledger_df)
    ordered_ledger = ledger_df.sort_values(["entry_activation_ts", "trade_id"], kind="mergesort").reset_index(drop=True)

    trade_metrics_df = _build_trade_metrics_summary(ordered_ledger)
    exit_reason_df = _build_exit_reason_summary(ordered_ledger)
    equity_df = _build_equity_curve(ordered_ledger)
    drawdown_df = _build_drawdown(equity_df)

    return MetricsArtifacts(
        trade_metrics=trade_metrics_df,
        equity_curve=equity_df,
        drawdown=drawdown_df,
        exit_reason_summary=exit_reason_df,
    )


def write_trade_metrics_csvs(*, artifacts: MetricsArtifacts, output_dir: str | Path) -> Mapping[str, Path]:
    """Persist metrics artifacts to deterministic CSV outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trade_metrics_path = output_path / "backtest_trade_metrics.csv"
    equity_curve_path = output_path / "backtest_equity_curve.csv"
    drawdown_path = output_path / "backtest_drawdown.csv"
    exit_reason_path = output_path / "backtest_exit_reason_summary.csv"

    artifacts.trade_metrics.to_csv(trade_metrics_path, index=False)
    artifacts.equity_curve.to_csv(equity_curve_path, index=False)
    artifacts.drawdown.to_csv(drawdown_path, index=False)
    artifacts.exit_reason_summary.to_csv(exit_reason_path, index=False)

    return {
        "backtest_trade_metrics.csv": trade_metrics_path,
        "backtest_equity_curve.csv": equity_curve_path,
        "backtest_drawdown.csv": drawdown_path,
        "backtest_exit_reason_summary.csv": exit_reason_path,
    }
