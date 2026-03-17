"""Phase 5 append-only experiment registry for completed backtester runs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Mapping

import pandas as pd

REGISTRY_FILENAME = "phase5_experiment_registry.csv"
REGISTRY_COLUMNS = [
    "ExperimentId",
    "ExperimentLabel",
    "RunTimestamp",
    "DateRangeStart",
    "DateRangeEnd",
    "RulesetId",
    "RulesetContractVersion",
    "ReplaySemanticsVersion",
    "MappingVersion",
    "ValidationStatus",
    "CostModelId",
    "SameBarPolicyId",
    "InputArtifactDir",
    "BacktestRunDir",
    "GitCommit",
    "DurationSeconds",
    "TradeCount",
    "ResolvedTradeCount",
    "ValidationSummaryStatus",
    "PromotionSummaryStatus",
    "NetResult",
    "Notes",
]


class ExperimentRegistryError(ValueError):
    """Raised when completed-run facts cannot be extracted for registry writing."""


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.exists() or not path.is_file():
        raise ExperimentRegistryError(f"Required registry source JSON is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ExperimentRegistryError(f"Failed parsing registry source JSON at {path}: {exc}") from exc


def _load_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def _pick_scope_value(df: pd.DataFrame, *, value_column: str, default: str = "") -> str:
    if df.empty or value_column not in df.columns:
        return default
    if "scope" in df.columns:
        scopes = df["scope"].astype(str)
        for preferred_scope in ("ALL_TRADES", "RESOLVED_ONLY"):
            mask = scopes == preferred_scope
            if mask.any():
                return str(df.loc[mask].iloc[0][value_column])
    return str(df.iloc[0][value_column])


def _safe_date_range_from_raw(raw_path: Path) -> tuple[str, str]:
    if not raw_path.exists() or not raw_path.is_file():
        return "", ""
    raw_df = pd.read_csv(raw_path)
    if "Timestamp" not in raw_df.columns or raw_df.empty:
        return "", ""
    ts = pd.to_datetime(raw_df["Timestamp"], utc=True, errors="coerce").dropna()
    if ts.empty:
        return "", ""
    return ts.min().isoformat(), ts.max().isoformat()


def build_registry_row_for_completed_run(
    *,
    run_dir: str | Path,
    input_artifact_dir: str | Path,
    experiment_id: str,
    experiment_label: str,
    duration_seconds: float,
    run_timestamp: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Build one registry row from existing per-run outputs without recomputing replay logic."""
    out_dir = Path(run_dir)
    artifact_dir = Path(input_artifact_dir)

    orchestration_manifest = _load_json(out_dir / "backtest_orchestration_manifest.json")
    run_manifest = _load_json(out_dir / "backtest_run_manifest.json")

    rulesets_df = _load_csv_or_empty(out_dir / "backtest_rulesets.csv")
    validation_df = _load_csv_or_empty(out_dir / "backtest_validation_summary.csv")
    promotion_df = _load_csv_or_empty(out_dir / "backtest_promotion_decisions.csv")

    ruleset_id = ""
    ruleset_contract_version = ""
    replay_semantics_version = ""
    mapping_version = ""
    if not rulesets_df.empty:
        ruleset_id = str(rulesets_df.iloc[0].get("ruleset_id", ""))
        ruleset_contract_version = str(rulesets_df.iloc[0].get("ruleset_version", ""))
        replay_semantics_version = str(rulesets_df.iloc[0].get("replay_semantics_version", ""))
        for mapping_col in ("mapping_version", "MappingVersion", "source_lineage_artifact"):
            value = str(rulesets_df.iloc[0].get(mapping_col, "")).strip()
            if value:
                mapping_version = value
                break

    validation_summary_status = _pick_scope_value(validation_df, value_column="validation_status", default="")
    promotion_summary_status = _pick_scope_value(promotion_df, value_column="promotion_decision", default="")
    resolved_trade_count_value = _pick_scope_value(validation_df, value_column="resolved_trade_count", default="")

    trade_count = int(orchestration_manifest.get("trade_count", 0))
    try:
        resolved_trade_count = int(float(resolved_trade_count_value)) if resolved_trade_count_value != "" else 0
    except ValueError:
        resolved_trade_count = 0

    raw_path = Path(str(run_manifest.get("artifact_paths", {}).get("raw", "")))
    date_start, date_end = _safe_date_range_from_raw(raw_path)

    registry_run_timestamp = run_timestamp or datetime.now(timezone.utc).isoformat()
    row = {
        "ExperimentId": experiment_id,
        "ExperimentLabel": experiment_label,
        "RunTimestamp": registry_run_timestamp,
        "DateRangeStart": date_start,
        "DateRangeEnd": date_end,
        "RulesetId": ruleset_id,
        "RulesetContractVersion": ruleset_contract_version,
        "ReplaySemanticsVersion": replay_semantics_version,
        "MappingVersion": mapping_version,
        "ValidationStatus": validation_summary_status,
        "CostModelId": str(orchestration_manifest.get("cost_model_id", "")),
        "SameBarPolicyId": str(orchestration_manifest.get("same_bar_policy_id", "")),
        "InputArtifactDir": str(artifact_dir),
        "BacktestRunDir": str(out_dir),
        "GitCommit": str(orchestration_manifest.get("git_commit", "unknown")),
        "DurationSeconds": round(float(duration_seconds), 6),
        "TradeCount": trade_count,
        "ResolvedTradeCount": resolved_trade_count,
        "ValidationSummaryStatus": validation_summary_status,
        "PromotionSummaryStatus": promotion_summary_status,
        "NetResult": "",
        "Notes": notes,
    }
    return {column: row.get(column, "") for column in REGISTRY_COLUMNS}


def append_registry_row(*, registry_path: str | Path, row: Mapping[str, Any]) -> Path:
    """Append one completed-run row to registry CSV without mutating prior rows."""
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    row_df = pd.DataFrame([{column: row.get(column, "") for column in REGISTRY_COLUMNS}], columns=REGISTRY_COLUMNS)
    if not path.exists():
        row_df.to_csv(path, index=False)
        return path

    existing = pd.read_csv(path)
    existing = existing.reindex(columns=REGISTRY_COLUMNS)
    combined = pd.concat([existing, row_df], ignore_index=True)
    combined.to_csv(path, index=False)
    return path
