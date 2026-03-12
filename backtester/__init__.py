"""Backtester package for Strategy Shi Phase 3."""

from .rulesets import (
    RULESET_COLUMNS,
    RulesetRow,
    build_backtest_rulesets,
    validate_rulesets,
    write_backtest_rulesets_csv,
)
from .engine import (
    ReplayContractError,
    ReplayInputs,
    load_replay_inputs,
    run_replay_engine,
    write_engine_outputs,
)
from .ledger import (
    LEDGER_COLUMNS,
    LedgerContractError,
    TradeLedgerRow,
    build_trade_ledger,
    validate_trade_ledger,
    write_trade_ledger_csv,
)
from .metrics import (
    DRAWDOWN_COLUMNS,
    EQUITY_CURVE_COLUMNS,
    EXIT_REASON_SUMMARY_COLUMNS,
    TRADE_METRICS_COLUMNS,
    MetricsArtifacts,
    MetricsContractError,
    build_trade_metrics_artifacts,
    write_trade_metrics_csvs,
)


__all__ = [
    "RULESET_COLUMNS",
    "RulesetRow",
    "build_backtest_rulesets",
    "validate_rulesets",
    "write_backtest_rulesets_csv",
    "ReplayContractError",
    "ReplayInputs",
    "load_replay_inputs",
    "run_replay_engine",
    "write_engine_outputs",
    "LEDGER_COLUMNS",
    "TradeLedgerRow",
    "LedgerContractError",
    "build_trade_ledger",
    "validate_trade_ledger",
    "write_trade_ledger_csv",
    "TRADE_METRICS_COLUMNS",
    "EQUITY_CURVE_COLUMNS",
    "DRAWDOWN_COLUMNS",
    "EXIT_REASON_SUMMARY_COLUMNS",
    "MetricsArtifacts",
    "MetricsContractError",
    "build_trade_metrics_artifacts",
    "write_trade_metrics_csvs",
]
