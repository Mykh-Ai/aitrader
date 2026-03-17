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
from .validation import (
    VALIDATION_COLUMNS,
    VALIDATION_DETAIL_COLUMNS,
    ValidationArtifacts,
    ValidationContractError,
    build_validation_artifacts,
    write_validation_csvs,
)
from .robustness import (
    ROBUSTNESS_COLUMNS,
    ROBUSTNESS_DETAIL_COLUMNS,
    RobustnessArtifacts,
    RobustnessContractError,
    build_robustness_artifacts,
    write_robustness_csvs,
)

from .orchestrator import (
    ORCHESTRATION_MANIFEST_NAME,
    OrchestrationResult,
    orchestrate_backtest,
    result_as_dict,
    run_backtester,
)


from .experiment_registry import (
    REGISTRY_COLUMNS,
    REGISTRY_FILENAME,
    append_registry_row,
    build_registry_row_for_completed_run,
)

from .campaign import (
    CAMPAIGN_MANIFEST_FILENAME,
    CAMPAIGN_RUN_INDEX_FILENAME,
    CAMPAIGN_SUMMARY_FILENAME,
    CampaignResult,
    run_backtest_campaign,
)
from .promotion import (
    PROMOTION_COLUMNS,
    PROMOTION_DETAIL_COLUMNS,
    PromotionArtifacts,
    PromotionContractError,
    build_promotion_artifacts,
    write_promotion_csvs,
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
    "VALIDATION_COLUMNS",
    "VALIDATION_DETAIL_COLUMNS",
    "ValidationArtifacts",
    "ValidationContractError",
    "build_validation_artifacts",
    "write_validation_csvs",
    "ROBUSTNESS_COLUMNS",
    "ROBUSTNESS_DETAIL_COLUMNS",
    "RobustnessArtifacts",
    "RobustnessContractError",
    "build_robustness_artifacts",
    "write_robustness_csvs",
    "PROMOTION_COLUMNS",
    "PROMOTION_DETAIL_COLUMNS",
    "PromotionArtifacts",
    "PromotionContractError",
    "build_promotion_artifacts",
    "write_promotion_csvs",
    "ORCHESTRATION_MANIFEST_NAME",
    "OrchestrationResult",
    "run_backtester",
    "orchestrate_backtest",
    "result_as_dict",

    "REGISTRY_COLUMNS",
    "REGISTRY_FILENAME",
    "build_registry_row_for_completed_run",
    "append_registry_row",
    "CAMPAIGN_MANIFEST_FILENAME",
    "CAMPAIGN_RUN_INDEX_FILENAME",
    "CAMPAIGN_SUMMARY_FILENAME",
    "CampaignResult",
    "run_backtest_campaign",
]
