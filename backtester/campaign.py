"""Batch campaign runner for Phase 5 observational orchestration outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time
from typing import Any, Mapping, Sequence

import pandas as pd

from .experiment_registry import (
    REGISTRY_FILENAME,
    append_registry_row,
    build_registry_row_for_completed_run,
)
from .orchestrator import run_backtester

CAMPAIGN_MANIFEST_FILENAME = "backtest_campaign_manifest.json"
CAMPAIGN_SUMMARY_FILENAME = "backtest_campaign_summary.csv"
CAMPAIGN_RUN_INDEX_FILENAME = "backtest_campaign_run_index.csv"


@dataclass(frozen=True)
class CampaignResult:
    campaign_manifest_path: Path
    campaign_summary_path: Path
    campaign_run_index_path: Path
    registry_path: Path
    run_dirs: list[Path]


def _build_deterministic_campaign_id(
    *,
    campaign_label: str,
    artifact_dirs: Sequence[Path],
    ruleset_source_formalization_mode: str,
    variant_names: tuple[str, ...],
    cost_model_id: str,
    same_bar_policy_id: str,
    replay_semantics_version: str,
    ruleset_mapping_artifact_filename: str | None,
) -> str:
    payload = {
        "campaign_label": campaign_label,
        "artifact_dirs": [str(path.resolve()) for path in artifact_dirs],
        "ruleset_source_formalization_mode": ruleset_source_formalization_mode,
        "variant_names": [str(name) for name in variant_names],
        "cost_model_id": cost_model_id,
        "same_bar_policy_id": same_bar_policy_id,
        "replay_semantics_version": replay_semantics_version,
        "ruleset_mapping_artifact_filename": ruleset_mapping_artifact_filename or "",
    }
    payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return f"campaign_{hashlib.sha256(payload_bytes).hexdigest()[:12]}"


def _write_campaign_outputs(
    *,
    output_dir: Path,
    manifest: Mapping[str, Any],
    run_index_rows: list[dict[str, Any]],
) -> tuple[Path, Path, Path]:
    manifest_path = output_dir / CAMPAIGN_MANIFEST_FILENAME
    summary_path = output_dir / CAMPAIGN_SUMMARY_FILENAME
    run_index_path = output_dir / CAMPAIGN_RUN_INDEX_FILENAME

    with manifest_path.open("w", encoding="utf-8") as fp:
        json.dump(dict(manifest), fp, ensure_ascii=False, indent=2)

    run_index_df = pd.DataFrame(run_index_rows)
    run_index_df.to_csv(run_index_path, index=False)

    completed_df = run_index_df[run_index_df["CompletionState"] == "COMPLETED"].copy()
    failed_df = run_index_df[run_index_df["CompletionState"] == "FAILED"].copy()

    summary_row: dict[str, Any] = {
        "CampaignId": manifest["CampaignId"],
        "RunCountPlanned": int(manifest["RunCountPlanned"]),
        "RunCountCompleted": int(len(completed_df)),
        "RunCountFailed": int(len(failed_df)),
        "TotalTradeCount": int(pd.to_numeric(completed_df.get("TradeCount"), errors="coerce").fillna(0).sum()),
        "TotalResolvedTradeCount": int(
            pd.to_numeric(completed_df.get("ResolvedTradeCount"), errors="coerce").fillna(0).sum()
        ),
        "ValidationStatusCounts": json.dumps(completed_df.get("ValidationSummaryStatus", pd.Series(dtype=str)).value_counts().to_dict()),
        "PromotionStatusCounts": json.dumps(completed_df.get("PromotionSummaryStatus", pd.Series(dtype=str)).value_counts().to_dict()),
        "Notes": "observational summary only; no ranking/selection/auto-promotion",
    }
    pd.DataFrame([summary_row]).to_csv(summary_path, index=False)
    return manifest_path, summary_path, run_index_path


def run_backtest_campaign(
    *,
    artifact_dirs: Sequence[str | Path],
    output_dir: str | Path,
    campaign_label: str,
    ruleset_source_formalization_mode: str,
    variant_names: tuple[str, ...],
    cost_model_id: str,
    same_bar_policy_id: str,
    replay_semantics_version: str,
    ruleset_mapping_artifact_filename: str | None = None,
    generation_timestamp: str | None = None,
    continue_on_error: bool = False,
    notes: str = "",
    registry_path: str | Path | None = None,
    backtester_kwargs: Mapping[str, Any] | None = None,
) -> CampaignResult:
    """Execute deterministic multi-run campaign over analyzer artifact directories."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_timestamp = generation_timestamp or datetime.now(timezone.utc).isoformat()
    artifact_dir_list = [Path(path) for path in artifact_dirs]
    campaign_id = _build_deterministic_campaign_id(
        campaign_label=campaign_label,
        artifact_dirs=artifact_dir_list,
        ruleset_source_formalization_mode=ruleset_source_formalization_mode,
        variant_names=variant_names,
        cost_model_id=cost_model_id,
        same_bar_policy_id=same_bar_policy_id,
        replay_semantics_version=replay_semantics_version,
        ruleset_mapping_artifact_filename=ruleset_mapping_artifact_filename,
    )
    resolved_registry_path = Path(registry_path) if registry_path is not None else out_dir / REGISTRY_FILENAME

    run_index_rows: list[dict[str, Any]] = []
    run_dirs: list[Path] = []

    shared_kwargs = dict(backtester_kwargs or {})

    for run_idx, artifact_dir in enumerate(artifact_dir_list, start=1):
        run_dir = out_dir / f"run_{run_idx:04d}"
        run_dirs.append(run_dir)
        experiment_id = f"{campaign_id}_run_{run_idx:04d}"
        experiment_label = f"{campaign_label}_run_{run_idx:04d}"

        started = time.monotonic()
        try:
            run_result = run_backtester(
                artifact_dir=artifact_dir,
                output_dir=run_dir,
                ruleset_source_formalization_mode=ruleset_source_formalization_mode,
                variant_names=variant_names,
                cost_model_id=cost_model_id,
                same_bar_policy_id=same_bar_policy_id,
                replay_semantics_version=replay_semantics_version,
                generation_timestamp=run_timestamp,
                ruleset_mapping_artifact_filename=ruleset_mapping_artifact_filename,
                **shared_kwargs,
            )
            duration_seconds = time.monotonic() - started
            completed_run_dirs = list(run_result.derived_run_dirs) or [run_dir]

            for derived_idx, completed_run_dir in enumerate(completed_run_dirs, start=1):
                derived_experiment_id = experiment_id
                derived_experiment_label = experiment_label
                derived_notes = "campaign completed run"
                if len(completed_run_dirs) > 1:
                    derived_suffix = f"derived_{derived_idx:04d}"
                    derived_experiment_id = f"{experiment_id}__{derived_suffix}"
                    derived_experiment_label = f"{experiment_label}__{derived_suffix}"
                    derived_notes = "campaign completed derived replay run"

                registry_row = build_registry_row_for_completed_run(
                    run_dir=completed_run_dir,
                    input_artifact_dir=artifact_dir,
                    experiment_id=derived_experiment_id,
                    experiment_label=derived_experiment_label,
                    duration_seconds=duration_seconds,
                    run_timestamp=run_timestamp,
                    notes=derived_notes,
                )
                append_registry_row(registry_path=resolved_registry_path, row=registry_row)

                run_index_rows.append(
                    {
                        "RunId": run_idx,
                        "ExperimentId": derived_experiment_id,
                        "ArtifactDir": str(artifact_dir),
                        "RunDir": str(completed_run_dir),
                        "RulesetId": registry_row["RulesetId"],
                        "ValidationSummaryStatus": registry_row["ValidationSummaryStatus"],
                        "PromotionSummaryStatus": registry_row["PromotionSummaryStatus"],
                        "TradeCount": registry_row["TradeCount"],
                        "ResolvedTradeCount": registry_row["ResolvedTradeCount"],
                        "DurationSeconds": registry_row["DurationSeconds"],
                        "GitCommit": registry_row["GitCommit"],
                        "CompletionState": "COMPLETED",
                        "Error": "",
                    }
                )
        except Exception as exc:
            run_index_rows.append(
                {
                    "RunId": run_idx,
                    "ExperimentId": experiment_id,
                    "ArtifactDir": str(artifact_dir),
                    "RunDir": str(run_dir),
                    "RulesetId": "",
                    "ValidationSummaryStatus": "",
                    "PromotionSummaryStatus": "",
                    "TradeCount": "",
                    "ResolvedTradeCount": "",
                    "DurationSeconds": round(time.monotonic() - started, 6),
                    "GitCommit": "",
                    "CompletionState": "FAILED",
                    "Error": str(exc),
                }
            )
            if not continue_on_error:
                manifest = {
                    "CampaignId": campaign_id,
                    "CampaignLabel": campaign_label,
                    "RunTimestamp": run_timestamp,
                    "ArtifactDirs": [str(path) for path in artifact_dir_list],
                    "RunCountPlanned": len(artifact_dir_list),
                    "RunCountCompleted": sum(1 for row in run_index_rows if row["CompletionState"] == "COMPLETED"),
                    "RulesetSourceMode": ruleset_source_formalization_mode,
                    "CostModelId": cost_model_id,
                    "SameBarPolicyId": same_bar_policy_id,
                    "ReplaySemanticsVersion": replay_semantics_version,
                    "RulesetId": "",
                    "GitCommit": next((row.get("GitCommit", "") for row in run_index_rows if row.get("GitCommit")), ""),
                    "Notes": notes,
                    "RegistryPath": str(resolved_registry_path),
                    "CampaignSummaryPath": str(out_dir / CAMPAIGN_SUMMARY_FILENAME),
                    "CampaignRunIndexPath": str(out_dir / CAMPAIGN_RUN_INDEX_FILENAME),
                }
                _write_campaign_outputs(output_dir=out_dir, manifest=manifest, run_index_rows=run_index_rows)
                raise

    completed_rows = [row for row in run_index_rows if row["CompletionState"] == "COMPLETED"]
    manifest = {
        "CampaignId": campaign_id,
        "CampaignLabel": campaign_label,
        "RunTimestamp": run_timestamp,
        "ArtifactDirs": [str(path) for path in artifact_dir_list],
        "RunCountPlanned": len(artifact_dir_list),
        "RunCountCompleted": len(completed_rows),
        "RulesetSourceMode": ruleset_source_formalization_mode,
        "CostModelId": cost_model_id,
        "SameBarPolicyId": same_bar_policy_id,
        "ReplaySemanticsVersion": replay_semantics_version,
        "RulesetId": completed_rows[0]["RulesetId"] if len({r["RulesetId"] for r in completed_rows if r["RulesetId"]}) == 1 and completed_rows else "",
        "GitCommit": completed_rows[0]["GitCommit"] if len({r["GitCommit"] for r in completed_rows if r.get("GitCommit")}) == 1 and completed_rows else "",
        "Notes": notes,
        "RegistryPath": str(resolved_registry_path),
        "CampaignSummaryPath": str(out_dir / CAMPAIGN_SUMMARY_FILENAME),
        "CampaignRunIndexPath": str(out_dir / CAMPAIGN_RUN_INDEX_FILENAME),
    }
    manifest_path, summary_path, run_index_path = _write_campaign_outputs(
        output_dir=out_dir,
        manifest=manifest,
        run_index_rows=run_index_rows,
    )
    return CampaignResult(
        campaign_manifest_path=manifest_path,
        campaign_summary_path=summary_path,
        campaign_run_index_path=run_index_path,
        registry_path=resolved_registry_path,
        run_dirs=run_dirs,
    )
