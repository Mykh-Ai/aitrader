"""Phase 3 orchestration layer for deterministic end-to-end backtesting runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import subprocess
from typing import Any, Mapping

import pandas as pd

from .engine import (
    CostModelHook,
    ReplayContractError,
    ReplayInputs,
    SameBarPolicyHook,
    load_replay_inputs,
    run_replay_engine,
    write_engine_outputs,
)
from .ledger import build_trade_ledger, write_trade_ledger_csv
from .metrics import build_trade_metrics_artifacts, write_trade_metrics_csvs
from .placement import PlacementContractError, materialize_stop_target_levels
from .promotion import build_promotion_artifacts, write_promotion_csvs
from .robustness import build_robustness_artifacts, write_robustness_csvs
from .rulesets import build_backtest_rulesets, validate_rulesets, write_backtest_rulesets_csv
from .ruleset_validation import validate_phase3_ruleset_mapping, write_ruleset_validation_csvs
from .validation import build_validation_artifacts, write_validation_csvs

REQUIRED_ANALYZER_ARTIFACTS = {
    "features": "analyzer_features.csv",
    "setups": "analyzer_setups.csv",
    "shortlist": "analyzer_setup_shortlist.csv",
    "research_summary": "analyzer_research_summary.csv",
}

OPTIONAL_ANALYZER_ARTIFACTS = {
    "events": "analyzer_events.csv",
    "lineage": "analyzer_setup_shortlist_explanations.csv",
    "ruleset_mapping": "phase3_ruleset_mapping.csv",
    "ruleset_contract": "phase3_ruleset_contract.csv",
    "ruleset_draft": "phase3_ruleset_draft.csv",
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
    engine_events_path: Path | None
    engine_manifest_path: Path | None
    ledger_path: Path | None
    metrics_paths: dict[str, Path] = field(default_factory=dict)
    validation_paths: dict[str, Path] = field(default_factory=dict)
    robustness_paths: dict[str, Path] = field(default_factory=dict)
    promotion_paths: dict[str, Path] = field(default_factory=dict)
    orchestration_manifest_path: Path | None = None
    derived_run_dirs: list[Path] = field(default_factory=list)


class FanoutReplayError(ReplayContractError):
    """Raised when a multi-ruleset fan-out run partially completes before a child fails."""

    def __init__(
        self,
        message: str,
        *,
        completed_derived_run_dirs: list[Path],
        failed_derived_run_dir: Path,
        failed_ruleset_id: str,
    ) -> None:
        super().__init__(message)
        self.completed_derived_run_dirs = list(completed_derived_run_dirs)
        self.failed_derived_run_dir = failed_derived_run_dir
        self.failed_ruleset_id = failed_ruleset_id




def _sanitize_ruleset_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").lower()
    return token[:48] if token else "ruleset"


def _write_orchestration_manifest(*, output_path: Path, payload: Mapping[str, Any]) -> Path:
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(dict(payload), fp, ensure_ascii=False, indent=2)
    return output_path


def _run_single_backtester(
    *,
    artifact_root: Path,
    out_dir: Path,
    required_paths: Mapping[str, Path],
    optional_paths: Mapping[str, Path],
    rulesets_df: pd.DataFrame,
    ruleset_source_formalization_mode: str,
    variant_names: tuple[str, ...],
    cost_model_id: str,
    same_bar_policy_id: str,
    replay_semantics_version: str,
    stop_model: str,
    expiry_model: str,
    resolved_generation_timestamp: str,
    mapping_warnings: list[str],
    phase4_validation_paths: Mapping[str, str],
    cost_models: Mapping[str, CostModelHook] | None = None,
    same_bar_policies: Mapping[str, SameBarPolicyHook] | None = None,
) -> OrchestrationResult:
    validate_rulesets(rulesets_df)
    rulesets_path = write_backtest_rulesets_csv(rulesets_df, out_dir / "backtest_rulesets.csv")

    replay_artifact_paths: dict[str, str | Path] = {
        "raw": required_paths["raw"],
        "features": required_paths["features"],
        "setups": required_paths["setups"],
    }
    replay_artifact_paths.update(optional_paths)

    replay_inputs = load_replay_inputs(artifact_paths=replay_artifact_paths, rulesets=rulesets_path)

    try:
        setups_with_placement = materialize_stop_target_levels(
            rulesets_df=rulesets_df,
            setups_df=replay_inputs.setups_df,
            raw_df=replay_inputs.raw_df,
        )
    except PlacementContractError as exc:
        raise ReplayContractError(f"SL/TP placement materialization failed: {exc}") from exc

    non_placed = setups_with_placement[setups_with_placement["placement_status"] != "PLACED"]
    if not non_placed.empty:
        details = [
            f"setup_id={row.SetupId}:status={row.placement_status}:notes={row.placement_notes}"
            for row in non_placed.itertuples(index=False)
        ]
        raise ReplayContractError(
            "SL/TP placement materialization produced non-placed setups: " + "; ".join(details)
        )

    replay_inputs = ReplayInputs(
        raw_df=replay_inputs.raw_df,
        features_df=replay_inputs.features_df,
        setups_df=setups_with_placement,
        rulesets_df=replay_inputs.rulesets_df,
        events_df=replay_inputs.events_df,
        lineage_df=replay_inputs.lineage_df,
        artifact_paths=replay_inputs.artifact_paths,
    )

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
        "run_type": "SINGLE_REPLAY_RUN",
        "completion_state": "COMPLETED",
        "ruleset_source_mode": ruleset_source_formalization_mode,
        "variant_names": [str(v) for v in variant_names],
        "cost_model_id": cost_model_id,
        "same_bar_policy_id": same_bar_policy_id,
        "replay_semantics_version": replay_semantics_version,
        "stop_model": stop_model,
        "expiry_model": expiry_model,
        "ruleset_count": int(len(rulesets_df)),
        "ruleset_ids": rulesets_df["ruleset_id"].astype(str).tolist(),
        "mapping_warnings": list(mapping_warnings),
        "phase4_validation_paths": dict(phase4_validation_paths),
        "derived_run_count": 0,
        "derived_run_dirs": [],
        "engine_event_count": int(len(engine_events_df)),
        "trade_count": int(len(trade_ledger_df)),
        "validation_scopes": validation_artifacts.summary["scope"].astype(str).tolist(),
        "robustness_scopes": robustness_artifacts.summary["scope"].astype(str).tolist(),
        "promotion_scopes": promotion_artifacts.decisions["scope"].astype(str).tolist(),
        "generation_timestamp": resolved_generation_timestamp,
        "git_commit": _git_commit_or_unknown(),
        "notes": _BOUNDARY_NOTES,
    }

    orchestration_manifest_path = _write_orchestration_manifest(
        output_path=out_dir / ORCHESTRATION_MANIFEST_NAME,
        payload=orchestration_manifest,
    )

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
    events_artifact_filename: str | None,
    lineage_artifact_filename: str | None,
) -> tuple[dict[str, Path], dict[str, Path]]:
    required_paths = {key: artifact_dir / filename for key, filename in REQUIRED_ANALYZER_ARTIFACTS.items()}
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


def resolve_raw_feed_path(
    *,
    artifact_dir: Path,
    raw_path: str | Path | None,
    raw_artifact_filename: str,
    run_manifest_filename: str = "run_manifest.json",
) -> Path:
    if raw_path is not None:
        explicit_raw_path = Path(raw_path)
        if explicit_raw_path.exists() and explicit_raw_path.is_file():
            return explicit_raw_path
        raise ReplayContractError(f"Explicit raw_path does not exist or is not a file: {explicit_raw_path}")

    manifest_path = artifact_dir / run_manifest_filename
    manifest_candidates: list[Path] = []
    if manifest_path.exists() and manifest_path.is_file():
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ReplayContractError(f"Failed parsing run manifest at {manifest_path}: {exc}") from exc

        input_feed_paths = manifest_payload.get("input_feed_paths")
        if input_feed_paths is not None and not isinstance(input_feed_paths, list):
            raise ReplayContractError(
                f"run manifest field input_feed_paths must be a list when present: {manifest_path}"
            )

        if isinstance(input_feed_paths, list):
            for candidate in input_feed_paths:
                if not isinstance(candidate, str) or not candidate.strip():
                    continue
                candidate_path = Path(candidate)
                if not candidate_path.is_absolute():
                    candidate_path = manifest_path.parent / candidate_path
                manifest_candidates.append(candidate_path)
                if candidate_path.exists() and candidate_path.is_file():
                    return candidate_path

    fallback_raw_path = artifact_dir / raw_artifact_filename
    if fallback_raw_path.exists() and fallback_raw_path.is_file():
        return fallback_raw_path

    manifest_candidates_str = ", ".join(str(path) for path in manifest_candidates) or "<none>"
    raise ReplayContractError(
        "Raw feed not found for Phase 3 orchestration. Checked explicit raw_path, "
        f"manifest input_feed_paths ({manifest_candidates_str}), and fallback {fallback_raw_path}."
    )


def run_backtester(
    *,
    artifact_dir: str | Path,
    output_dir: str | Path,
    ruleset_source_formalization_mode: str,
    variant_names: tuple[str, ...],
    cost_model_id: str,
    same_bar_policy_id: str,
    replay_semantics_version: str,
    stop_model: str = "REFERENCE_LEVEL_HARD_STOP",
    expiry_model: str = "BARS_AFTER_ACTIVATION:12",
    generation_timestamp: str | None = None,
    raw_path: str | Path | None = None,
    raw_artifact_filename: str = "raw.csv",
    events_artifact_filename: str | None = None,
    lineage_artifact_filename: str | None = None,
    ruleset_mapping_artifact_filename: str | None = None,
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
        events_artifact_filename=events_artifact_filename,
        lineage_artifact_filename=lineage_artifact_filename,
    )
    required_paths["raw"] = resolve_raw_feed_path(
        artifact_dir=artifact_root,
        raw_path=raw_path,
        raw_artifact_filename=raw_artifact_filename,
    )

    shortlist_df = _load_csv(required_paths["shortlist"], label="shortlist")
    research_summary_df = _load_csv(required_paths["research_summary"], label="research_summary")
    ruleset_mapping_df = None
    phase4_validation_paths: dict[str, str] = {}

    if ruleset_source_formalization_mode == "PHASE3_MAPPING_ONLY":
        mapping_name = ruleset_mapping_artifact_filename or OPTIONAL_ANALYZER_ARTIFACTS["ruleset_mapping"]
        mapping_path = artifact_root / mapping_name
        if not mapping_path.exists() or not mapping_path.is_file():
            raise ReplayContractError(
                "PHASE3_MAPPING_ONLY requires phase3 ruleset mapping artifact: "
                f"ruleset_mapping={mapping_path}"
            )
        ruleset_mapping_df = _load_csv(mapping_path, label="phase3_ruleset_mapping")

        contract_path = artifact_root / OPTIONAL_ANALYZER_ARTIFACTS["ruleset_contract"]
        draft_path = artifact_root / OPTIONAL_ANALYZER_ARTIFACTS["ruleset_draft"]
        contract_df = _load_csv(contract_path, label="phase3_ruleset_contract") if contract_path.exists() else None
        draft_df = _load_csv(draft_path, label="phase3_ruleset_draft") if draft_path.exists() else None

        phase4_artifacts = validate_phase3_ruleset_mapping(
            mapping_df=ruleset_mapping_df,
            contract_df=contract_df,
            draft_df=draft_df,
        )
        summary_path, details_path = write_ruleset_validation_csvs(artifacts=phase4_artifacts, output_dir=out_dir)
        phase4_validation_paths = {"summary": str(summary_path), "details": str(details_path)}

        replay_eligible = phase4_artifacts.summary[
            phase4_artifacts.summary["IsReplayEligible"] == True
        ].reset_index(drop=True)
        if replay_eligible.empty:
            raise ReplayContractError(
                "Phase 4 ruleset validation gate blocked replay: no replay-eligible mapping rows. "
                f"See {summary_path} and {details_path}."
            )
        if len(replay_eligible.index) > 1:
            raise ReplayContractError(
                "Phase 4 ruleset validation gate blocked replay: mapping-only mode requires exactly one "
                f"replay-eligible row, got {len(replay_eligible.index)}. See {summary_path}."
            )

        ruleset_id = str(replay_eligible.iloc[0]["RulesetId"])
        ruleset_mapping_df = ruleset_mapping_df[
            ruleset_mapping_df["RulesetId"].astype(str) == ruleset_id
        ].reset_index(drop=True)

    rulesets_df, mapping_warnings = build_backtest_rulesets(
        shortlist_df=shortlist_df,
        research_summary_df=research_summary_df,
        ruleset_mapping_df=ruleset_mapping_df,
        variant_names=variant_names,
        source_formalization_mode=ruleset_source_formalization_mode,
        cost_model_id=cost_model_id,
        same_bar_policy_id=same_bar_policy_id,
        replay_semantics_version=replay_semantics_version,
        stop_model=stop_model,
        expiry_model=expiry_model,
    )
    validate_rulesets(rulesets_df)

    rulesets_path = write_backtest_rulesets_csv(rulesets_df, out_dir / "backtest_rulesets.csv")

    if len(rulesets_df.index) == 0:
        raise ReplayContractError(
            "No replayable canonical rulesets materialized; replay skipped before placement. "
            f"See {rulesets_path}."
        )

    if len(rulesets_df.index) <= 1:
        result = _run_single_backtester(
            artifact_root=artifact_root,
            out_dir=out_dir,
            required_paths=required_paths,
            optional_paths=optional_paths,
            rulesets_df=rulesets_df,
            ruleset_source_formalization_mode=ruleset_source_formalization_mode,
            variant_names=variant_names,
            cost_model_id=cost_model_id,
            same_bar_policy_id=same_bar_policy_id,
            replay_semantics_version=replay_semantics_version,
            stop_model=stop_model,
            expiry_model=expiry_model,
            resolved_generation_timestamp=resolved_generation_timestamp,
            mapping_warnings=mapping_warnings,
            phase4_validation_paths=phase4_validation_paths,
            cost_models=cost_models,
            same_bar_policies=same_bar_policies,
        )
        if result.rulesets_path != rulesets_path:
            write_backtest_rulesets_csv(rulesets_df, rulesets_path)
        return result

    derived_run_dirs: list[Path] = []
    planned_derived_run_dirs = [
        out_dir / f"derived_run_{index:04d}_{_sanitize_ruleset_token(ruleset_row['ruleset_id'])}"
        for index, (_, ruleset_row) in enumerate(rulesets_df.iterrows(), start=1)
    ]
    for index, ((_, ruleset_row), child_dir) in enumerate(
        zip(rulesets_df.iterrows(), planned_derived_run_dirs, strict=True),
        start=1,
    ):
        child_rulesets_df = pd.DataFrame([ruleset_row.to_dict()], columns=rulesets_df.columns).reset_index(drop=True)
        try:
            _run_single_backtester(
                artifact_root=artifact_root,
                out_dir=child_dir,
                required_paths=required_paths,
                optional_paths=optional_paths,
                rulesets_df=child_rulesets_df,
                ruleset_source_formalization_mode=ruleset_source_formalization_mode,
                variant_names=variant_names,
                cost_model_id=cost_model_id,
                same_bar_policy_id=same_bar_policy_id,
                replay_semantics_version=replay_semantics_version,
                stop_model=stop_model,
                expiry_model=expiry_model,
                resolved_generation_timestamp=resolved_generation_timestamp,
                mapping_warnings=mapping_warnings,
                phase4_validation_paths=phase4_validation_paths,
                cost_models=cost_models,
                same_bar_policies=same_bar_policies,
            )
        except Exception as exc:
            failed_ruleset_id = str(ruleset_row["ruleset_id"])
            orchestration_manifest = {
                "artifact_dir": str(artifact_root),
                "output_dir": str(out_dir),
                "run_type": "FANOUT_PARENT_LINEAGE_ONLY",
                "completion_state": "PARTIAL_FAILURE",
                "ruleset_source_mode": ruleset_source_formalization_mode,
                "variant_names": [str(v) for v in variant_names],
                "cost_model_id": cost_model_id,
                "same_bar_policy_id": same_bar_policy_id,
                "replay_semantics_version": replay_semantics_version,
                "stop_model": stop_model,
                "expiry_model": expiry_model,
                "ruleset_count": int(len(rulesets_df)),
                "ruleset_ids": rulesets_df["ruleset_id"].astype(str).tolist(),
                "mapping_warnings": list(mapping_warnings),
                "phase4_validation_paths": phase4_validation_paths,
                "derived_run_count": len(derived_run_dirs),
                "derived_run_dirs": [str(path) for path in derived_run_dirs],
                "planned_derived_run_dirs": [str(path) for path in planned_derived_run_dirs],
                "failed_derived_run_dir": str(child_dir),
                "failed_ruleset_id": failed_ruleset_id,
                "engine_event_count": None,
                "trade_count": None,
                "validation_scopes": [],
                "robustness_scopes": [],
                "promotion_scopes": [],
                "generation_timestamp": resolved_generation_timestamp,
                "git_commit": _git_commit_or_unknown(),
                "notes": _BOUNDARY_NOTES + ["fan-out replay: one isolated child run per canonical ruleset"],
            }
            _write_orchestration_manifest(
                output_path=out_dir / ORCHESTRATION_MANIFEST_NAME,
                payload=orchestration_manifest,
            )
            raise FanoutReplayError(
                "Multi-ruleset fan-out replay partially completed before child failure: "
                f"failed_ruleset_id={failed_ruleset_id}; completed_children={len(derived_run_dirs)}; "
                f"failed_child_dir={child_dir}; cause={exc}",
                completed_derived_run_dirs=derived_run_dirs,
                failed_derived_run_dir=child_dir,
                failed_ruleset_id=failed_ruleset_id,
            ) from exc
        derived_run_dirs.append(child_dir)

    orchestration_manifest = {
        "artifact_dir": str(artifact_root),
        "output_dir": str(out_dir),
        "run_type": "FANOUT_PARENT_LINEAGE_ONLY",
        "completion_state": "COMPLETED",
        "ruleset_source_mode": ruleset_source_formalization_mode,
        "variant_names": [str(v) for v in variant_names],
        "cost_model_id": cost_model_id,
        "same_bar_policy_id": same_bar_policy_id,
        "replay_semantics_version": replay_semantics_version,
        "stop_model": stop_model,
        "expiry_model": expiry_model,
        "ruleset_count": int(len(rulesets_df)),
        "ruleset_ids": rulesets_df["ruleset_id"].astype(str).tolist(),
        "mapping_warnings": list(mapping_warnings),
        "phase4_validation_paths": phase4_validation_paths,
        "derived_run_count": len(derived_run_dirs),
        "derived_run_dirs": [str(path) for path in derived_run_dirs],
        "planned_derived_run_dirs": [str(path) for path in planned_derived_run_dirs],
        "engine_event_count": None,
        "trade_count": None,
        "validation_scopes": [],
        "robustness_scopes": [],
        "promotion_scopes": [],
        "generation_timestamp": resolved_generation_timestamp,
        "git_commit": _git_commit_or_unknown(),
        "notes": _BOUNDARY_NOTES + ["fan-out replay: one isolated child run per canonical ruleset"],
    }
    orchestration_manifest_path = _write_orchestration_manifest(
        output_path=out_dir / ORCHESTRATION_MANIFEST_NAME,
        payload=orchestration_manifest,
    )

    return OrchestrationResult(
        rulesets_path=rulesets_path,
        engine_events_path=None,
        engine_manifest_path=None,
        ledger_path=None,
        metrics_paths={},
        validation_paths=phase4_validation_paths,
        robustness_paths={},
        promotion_paths={},
        orchestration_manifest_path=orchestration_manifest_path,
        derived_run_dirs=derived_run_dirs,
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
        elif value is None:
            payload[key] = None
        elif isinstance(value, dict):
            payload[key] = {name: str(path) for name, path in value.items()}
        elif isinstance(value, list):
            payload[key] = [str(item) if isinstance(item, Path) else item for item in value]
    return payload
