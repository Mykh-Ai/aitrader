"""Phase 3 orchestration layer for deterministic end-to-end backtesting runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
from typing import Any, Mapping

import pandas as pd

from .engine import (
    CostModelHook,
    ReplayContractError,
    SameBarPolicyHook,
    load_replay_inputs,
    run_replay_engine,
    write_engine_outputs,
)
from .ledger import build_trade_ledger, write_trade_ledger_csv
from .metrics import build_trade_metrics_artifacts, write_trade_metrics_csvs
from .promotion import build_promotion_artifacts, write_promotion_csvs
from .robustness import build_robustness_artifacts, write_robustness_csvs
from .rulesets import build_backtest_rulesets, validate_rulesets, write_backtest_rulesets_csv
from .validation import build_validation_artifacts, write_validation_csvs

REQUIRED_ANALYZER_ARTIFACTS = {
    "raw": "raw.csv",
    "features": "analyzer_features.csv",
    "setups": "analyzer_setups.csv",
    "shortlist": "analyzer_setup_shortlist.csv",
    "research_summary": "analyzer_research_summary.csv",
}

OPTIONAL_ANALYZER_ARTIFACTS = {
    "events": "analyzer_events.csv",
    "lineage": "analyzer_setup_shortlist_explanations.csv",
}

ORCHESTRATION_MANIFEST_NAME = "backtest_orchestration_manifest.json"

_BOUNDARY_NOTES = [
    "historical backtest orchestration only",
    "consumes pre-generated Analyzer artifacts only",
    "does not call analyzer.pipeline.run()",
    "does not mutate Analyzer artifacts",
    "promotion decisions are for execution-design progression only",
    "promotion decisions are not live-trading authorization",
]


@dataclass(frozen=True)
class OrchestrationResult:
    """Structured result of one orchestration run with written artifact paths."""

    rulesets_path: Path
    engine_events_path: Path
    engine_manifest_path: Path
    ledger_path: Path
    metrics_paths: dict[str, Path]
    validation_paths: dict[str, Path]
    robustness_paths: dict[str, Path]
    promotion_paths: dict[str, Path]
    orchestration_manifest_path: Path


def _git_commit_or_unknown() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _load_csv(path: Path, *, label: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise ReplayContractError(f"Failed loading {label} artifact at {path}: {exc}") from exc


def _resolve_artifact_paths(
    *,
    artifact_dir: Path,
    raw_artifact_filename: str,
    events_artifact_filename: str | None,
    lineage_artifact_filename: str | None,
) -> tuple[dict[str, Path], dict[str, Path]]:
    required_filenames = {
        **REQUIRED_ANALYZER_ARTIFACTS,
        "raw": raw_artifact_filename,
    }

    required_paths = {key: artifact_dir / filename for key, filename in required_filenames.items()}
    missing_required = [f"{key}={path}" for key, path in required_paths.items() if not path.exists()]
    if missing_required:
        raise ReplayContractError(
            "Missing required Analyzer artifacts for Phase 3 orchestration: " + ", ".join(missing_required)
        )

    optional_paths: dict[str, Path] = {}
    events_name = events_artifact_filename or OPTIONAL_ANALYZER_ARTIFACTS["events"]
    lineage_name = lineage_artifact_filename or OPTIONAL_ANALYZER_ARTIFACTS["lineage"]

    events_path = artifact_dir / events_name
    if events_path.exists():
        optional_paths["events"] = events_path

    lineage_path = artifact_dir / lineage_name
    if lineage_path.exists():
        optional_paths["lineage"] = lineage_path

    return required_paths, optional_paths


def run_backtester(
    *,
    artifact_dir: str | Path,
    output_dir: str | Path,
    ruleset_source_formalization_mode: str,
    variant_names: tuple[str, ...],
    cost_model_id: str,
    same_bar_policy_id: str,
    replay_semantics_version: str,
    generation_timestamp: str | None = None,
    raw_artifact_filename: str = "raw.csv",
    events_artifact_filename: str | None = None,
    lineage_artifact_filename: str | None = None,
    cost_models: Mapping[str, CostModelHook] | None = None,
    same_bar_policies: Mapping[str, SameBarPolicyHook] | None = None,
) -> OrchestrationResult:
    """Run deterministic Phase 3 backtester orchestration over pre-generated Analyzer artifacts."""
    resolved_generation_timestamp = generation_timestamp or datetime.now(timezone.utc).isoformat()

    artifact_root = Path(artifact_dir)
    if not artifact_root.exists() or not artifact_root.is_dir():
        raise ReplayContractError(f"artifact_dir must exist and be a directory: {artifact_root}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    required_paths, optional_paths = _resolve_artifact_paths(
        artifact_dir=artifact_root,
        raw_artifact_filename=raw_artifact_filename,
        events_artifact_filename=events_artifact_filename,
        lineage_artifact_filename=lineage_artifact_filename,
    )

    shortlist_df = _load_csv(required_paths["shortlist"], label="shortlist")
    research_summary_df = _load_csv(required_paths["research_summary"], label="research_summary")

    rulesets_df, mapping_warnings = build_backtest_rulesets(
        shortlist_df=shortlist_df,
        research_summary_df=research_summary_df,
        variant_names=variant_names,
        source_formalization_mode=ruleset_source_formalization_mode,
        cost_model_id=cost_model_id,
        same_bar_policy_id=same_bar_policy_id,
        replay_semantics_version=replay_semantics_version,
    )
    validate_rulesets(rulesets_df)

    rulesets_path = write_backtest_rulesets_csv(rulesets_df, out_dir / "backtest_rulesets.csv")

    replay_artifact_paths: dict[str, str | Path] = {
        "raw": required_paths["raw"],
        "features": required_paths["features"],
        "setups": required_paths["setups"],
    }
    replay_artifact_paths.update(optional_paths)

    replay_inputs = load_replay_inputs(artifact_paths=replay_artifact_paths, rulesets=rulesets_path)
    engine_events_df, engine_manifest = run_replay_engine(
        replay_inputs,
        cost_models=cost_models,
        same_bar_policies=same_bar_policies,
        generation_timestamp=resolved_generation_timestamp,
    )
    engine_events_path, engine_manifest_path = write_engine_outputs(
        events_df=engine_events_df,
        manifest=engine_manifest,
        output_dir=out_dir,
    )

    trade_ledger_df = build_trade_ledger(engine_events_df, rulesets_df=rulesets_df)
    ledger_path = write_trade_ledger_csv(ledger_df=trade_ledger_df, output_dir=out_dir)

    metrics_artifacts = build_trade_metrics_artifacts(trade_ledger_df, rulesets_df=rulesets_df)
    metrics_paths = dict(write_trade_metrics_csvs(artifacts=metrics_artifacts, output_dir=out_dir))

    validation_artifacts = build_validation_artifacts(
        trade_ledger_df=trade_ledger_df,
        trade_metrics_df=metrics_artifacts.trade_metrics,
        drawdown_df=metrics_artifacts.drawdown,
        rulesets_df=rulesets_df,
    )
    validation_paths = dict(write_validation_csvs(artifacts=validation_artifacts, output_dir=out_dir))

    robustness_artifacts = build_robustness_artifacts(
        trade_ledger_df=trade_ledger_df,
        trade_metrics_df=metrics_artifacts.trade_metrics,
        validation_df=validation_artifacts.summary,
        rulesets_df=rulesets_df,
    )
    robustness_paths = dict(write_robustness_csvs(artifacts=robustness_artifacts, output_dir=out_dir))

    promotion_artifacts = build_promotion_artifacts(
        validation_summary_df=validation_artifacts.summary,
        robustness_summary_df=robustness_artifacts.summary,
    )
    promotion_paths = dict(write_promotion_csvs(artifacts=promotion_artifacts, output_dir=out_dir))

    orchestration_manifest = {
        "artifact_dir": str(artifact_root),
        "output_dir": str(out_dir),
        "ruleset_source_mode": ruleset_source_formalization_mode,
        "variant_names": [str(v) for v in variant_names],
        "cost_model_id": cost_model_id,
        "same_bar_policy_id": same_bar_policy_id,
        "replay_semantics_version": replay_semantics_version,
        "ruleset_count": int(len(rulesets_df)),
        "mapping_warnings": list(mapping_warnings),
        "engine_event_count": int(len(engine_events_df)),
        "trade_count": int(len(trade_ledger_df)),
        "validation_scopes": validation_artifacts.summary["scope"].astype(str).tolist(),
        "robustness_scopes": robustness_artifacts.summary["scope"].astype(str).tolist(),
        "promotion_scopes": promotion_artifacts.decisions["scope"].astype(str).tolist(),
        "generation_timestamp": resolved_generation_timestamp,
        "git_commit": _git_commit_or_unknown(),
        "notes": _BOUNDARY_NOTES,
    }

    orchestration_manifest_path = out_dir / ORCHESTRATION_MANIFEST_NAME
    with orchestration_manifest_path.open("w", encoding="utf-8") as fp:
        json.dump(orchestration_manifest, fp, ensure_ascii=False, indent=2)

    return OrchestrationResult(
        rulesets_path=rulesets_path,
        engine_events_path=engine_events_path,
        engine_manifest_path=engine_manifest_path,
        ledger_path=ledger_path,
        metrics_paths=metrics_paths,
        validation_paths=validation_paths,
        robustness_paths=robustness_paths,
        promotion_paths=promotion_paths,
        orchestration_manifest_path=orchestration_manifest_path,
    )


def orchestrate_backtest(**kwargs: Any) -> OrchestrationResult:
    """Alias for run_backtester for explicit orchestration naming."""
    return run_backtester(**kwargs)


def result_as_dict(result: OrchestrationResult) -> dict[str, Any]:
    """Utility serializer for stable path-oriented return contract."""
    payload = asdict(result)
    for key, value in list(payload.items()):
        if isinstance(value, Path):
            payload[key] = str(value)
        elif isinstance(value, dict):
            payload[key] = {name: str(path) for name, path in value.items()}
    return payload
