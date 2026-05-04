from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from analyzer import pipeline as analyzer_pipeline
from backtester.engine import ReplayContractError, ZeroCostSkeletonModel
from backtester.orchestrator import ORCHESTRATION_MANIFEST_NAME, result_as_dict, run_backtester


def _write_analyzer_artifacts(
    artifact_dir: Path,
    *,
    raw_output_path: Path | None = None,
    shortlist_rows: list[dict[str, object]] | None = None,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.DataFrame(
        [
            {
                "Timestamp": "2024-01-01T00:00:00Z",
                "Open": 100.0,
                "High": 101.0,
                "Low": 99.0,
                "Close": 100.5,
                "IsSynthetic": 0,
            },
            {
                "Timestamp": "2024-01-01T00:01:00Z",
                "Open": 101.0,
                "High": 102.0,
                "Low": 100.0,
                "Close": 101.5,
                "IsSynthetic": 0,
            },
            {
                "Timestamp": "2024-01-01T00:02:00Z",
                "Open": 102.0,
                "High": 103.0,
                "Low": 101.0,
                "Close": 102.5,
                "IsSynthetic": 0,
            },
        ]
    )
    features = pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "DummyFeature": 1.0},
            {"Timestamp": "2024-01-01T00:01:00Z", "DummyFeature": 1.1},
            {"Timestamp": "2024-01-01T00:02:00Z", "DummyFeature": 1.2},
        ]
    )
    setups = pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "FAILED_BREAK_RECLAIM",
                "Direction": "LONG",
                "DetectedAt": "2024-01-01T00:00:00Z",
                "SetupBarTs": "2024-01-01T00:00:00Z",
                "ReferenceEventType": "FAILED_BREAK_DOWN",
                "ReferenceLevel": 99.0,
            }
        ]
    )
    shortlist = pd.DataFrame(
        shortlist_rows
        or [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "SELECT",
            }
        ]
    )
    research_summary = shortlist.copy()

    if raw_output_path is None:
        raw_output_path = artifact_dir / "raw.csv"
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(raw_output_path, index=False)
    features.to_csv(artifact_dir / "analyzer_features.csv", index=False)
    setups.to_csv(artifact_dir / "analyzer_setups.csv", index=False)
    shortlist.to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    research_summary.to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)


def _run(artifact_dir: Path, output_dir: Path, *, expiry_model: str = "BARS_AFTER_ACTIVATION:12"):
    return run_backtester(
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        ruleset_source_formalization_mode="SHORTLIST_FIRST",
        variant_names=("BASE",),
        cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
        same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
        replay_semantics_version="REPLAY_V0_1",
        expiry_model=expiry_model,
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
    )


def test_end_to_end_smoke_produces_full_phase3_artifact_set(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(artifact_dir)

    result = _run(artifact_dir, output_dir)

    expected = {
        "backtest_rulesets.csv",
        "backtest_engine_events.csv",
        "backtest_run_manifest.json",
        "backtest_trades.csv",
        "backtest_trade_metrics.csv",
        "backtest_equity_curve.csv",
        "backtest_drawdown.csv",
        "backtest_exit_reason_summary.csv",
        "backtest_validation_summary.csv",
        "backtest_validation_details.csv",
        "backtest_robustness_summary.csv",
        "backtest_robustness_details.csv",
        "backtest_promotion_decisions.csv",
        "backtest_promotion_details.csv",
        ORCHESTRATION_MANIFEST_NAME,
    }
    assert expected.issubset({p.name for p in output_dir.iterdir() if p.is_file()})

    as_dict = result_as_dict(result)
    assert as_dict["rulesets_path"].endswith("backtest_rulesets.csv")
    assert as_dict["engine_events_path"].endswith("backtest_engine_events.csv")

    trades = pd.read_csv(output_dir / "backtest_trades.csv")
    assert trades.iloc[0]["initial_stop_price"] == pytest.approx(99.0)
    assert trades.iloc[0]["initial_target_price"] == pytest.approx(104.0)


def test_run_backtester_threads_explicit_expiry_model_to_rulesets_and_manifests(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(artifact_dir)

    _run(artifact_dir, output_dir, expiry_model="BARS_AFTER_ACTIVATION:60")

    rulesets = pd.read_csv(output_dir / "backtest_rulesets.csv")
    assert rulesets["expiry_model"].tolist() == ["BARS_AFTER_ACTIVATION:60"]

    engine_manifest = json.loads((output_dir / "backtest_run_manifest.json").read_text(encoding="utf-8"))
    assert engine_manifest["expiry_models"] == ["BARS_AFTER_ACTIVATION:60"]

    orchestration_manifest = json.loads((output_dir / ORCHESTRATION_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert orchestration_manifest["expiry_model"] == "BARS_AFTER_ACTIVATION:60"


def test_deterministic_runs_same_input_same_artifacts_with_fixed_timestamp(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    first = tmp_path / "out_first"
    second = tmp_path / "out_second"

    _run(artifact_dir, first)
    _run(artifact_dir, second)

    files = [
        "backtest_rulesets.csv",
        "backtest_engine_events.csv",
        "backtest_trades.csv",
        "backtest_trade_metrics.csv",
        "backtest_equity_curve.csv",
        "backtest_drawdown.csv",
        "backtest_exit_reason_summary.csv",
        "backtest_validation_summary.csv",
        "backtest_validation_details.csv",
        "backtest_robustness_summary.csv",
        "backtest_robustness_details.csv",
        "backtest_promotion_decisions.csv",
        "backtest_promotion_details.csv",
        "backtest_run_manifest.json",
        ORCHESTRATION_MANIFEST_NAME,
    ]

    for name in files:
        first_text = (first / name).read_text(encoding="utf-8")
        second_text = (second / name).read_text(encoding="utf-8")
        if name == ORCHESTRATION_MANIFEST_NAME:
            first_manifest = json.loads(first_text)
            second_manifest = json.loads(second_text)
            first_manifest.pop("output_dir", None)
            second_manifest.pop("output_dir", None)
            assert first_manifest == second_manifest
        else:
            assert first_text == second_text


def test_missing_required_analyzer_artifact_fails_loudly(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)
    (artifact_dir / "analyzer_setup_shortlist.csv").unlink()

    with pytest.raises(ReplayContractError, match="Missing required Analyzer artifacts"):
        _run(artifact_dir, tmp_path / "out")


def test_raw_feed_resolution_prefers_explicit_raw_path(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    external_raw_path = tmp_path / "feeds" / "explicit_raw.csv"
    _write_analyzer_artifacts(artifact_dir, raw_output_path=external_raw_path)

    result = run_backtester(
        artifact_dir=artifact_dir,
        output_dir=tmp_path / "out",
        ruleset_source_formalization_mode="SHORTLIST_FIRST",
        variant_names=("BASE",),
        cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
        same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
        replay_semantics_version="REPLAY_V0_1",
        generation_timestamp="2024-01-01T00:00:00+00:00",
        raw_path=external_raw_path,
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
    )

    assert result.engine_events_path.exists()


def test_raw_feed_resolution_uses_manifest_input_feed_paths(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    manifest_raw_path = tmp_path / "feeds" / "manifest_raw.csv"
    _write_analyzer_artifacts(artifact_dir, raw_output_path=manifest_raw_path)

    manifest_payload = {
        "status": "SUCCESS",
        "input_feed_paths": [str(manifest_raw_path)],
    }
    (artifact_dir / "run_manifest.json").write_text(json.dumps(manifest_payload), encoding="utf-8")

    result = _run(artifact_dir, tmp_path / "out")

    assert result.engine_events_path.exists()


def test_raw_feed_resolution_falls_back_to_artifact_dir_raw_csv(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    result = _run(artifact_dir, tmp_path / "out")

    assert result.engine_events_path.exists()


def test_boundary_preservation_orchestrator_does_not_call_analyzer_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    def _boom(*args, **kwargs):
        raise AssertionError("analyzer.pipeline.run must not be called by backtester orchestrator")

    monkeypatch.setattr(analyzer_pipeline, "run", _boom)

    _run(artifact_dir, tmp_path / "out")


def test_backtester_ignores_research_variant_sidecar_by_default(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "out"
    _write_analyzer_artifacts(artifact_dir)

    sidecar_dir = artifact_dir / "research_variants" / "FAILED_BREAK_RECLAIM_EXTENDED_V1"
    sidecar_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "VariantId": "FAILED_BREAK_RECLAIM_EXTENDED_V1",
                "SetupId": "SIDE",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "SetupBarTs": "2024-01-01T00:00:00Z",
                "ReferenceLevel": 100.0,
                "OutcomeHorizonBars": 10080,
                "OutcomeBarsObserved": 10080,
                "OutcomeStatus": "FULL_HORIZON",
                "OutcomeEndTs": "2024-01-08T00:00:00Z",
                "MFE_Pct": 999.0,
                "MAE_Pct": 0.0,
                "CloseReturn_Pct": 999.0,
                "TimeToMFE_Bars": 1,
                "TimeToMFE_Ts": "2024-01-01T00:01:00Z",
                "TimeToMAE_Bars": 1,
                "TimeToMAE_Ts": "2024-01-01T00:01:00Z",
            }
        ]
    ).to_csv(sidecar_dir / "analyzer_setup_outcomes_by_horizon.csv", index=False)

    result = _run(artifact_dir, output_dir)

    assert result.engine_events_path.exists()
    manifest = json.loads((output_dir / "backtest_run_manifest.json").read_text(encoding="utf-8"))
    artifact_paths = manifest["artifact_paths"]
    assert "research_variants" not in json.dumps(artifact_paths)
    assert set(artifact_paths) <= {"raw", "features", "setups"}


def test_manifest_honesty_contains_phase_boundary_and_non_live_disclaimers(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "out"
    _write_analyzer_artifacts(artifact_dir)

    _run(artifact_dir, output_dir)

    manifest = json.loads((output_dir / ORCHESTRATION_MANIFEST_NAME).read_text(encoding="utf-8"))
    notes = " ".join(manifest["notes"])
    assert "pre-generated Analyzer artifacts only" in notes
    assert "does not call analyzer.pipeline.run()" in notes
    assert "not live-trading authorization" in notes


def test_no_event_path_writes_valid_engine_csv_and_manifest_and_does_not_break_ledger(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "out"
    _write_analyzer_artifacts(artifact_dir)

    pd.DataFrame(
        [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SelectionDecision": "SELECT",
            }
        ]
    ).to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    pd.DataFrame(
        [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SelectionDecision": "SELECT",
            }
        ]
    ).to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)

    result = _run(artifact_dir, output_dir)

    engine_events = pd.read_csv(result.engine_events_path)
    assert engine_events.empty
    assert "event_id" in engine_events.columns

    ledger = pd.read_csv(result.ledger_path)
    assert ledger.empty

    orchestration_manifest = json.loads(result.orchestration_manifest_path.read_text(encoding="utf-8"))
    assert orchestration_manifest["engine_event_count"] == 0
    assert orchestration_manifest["trade_count"] == 0


def test_phase3_mapping_only_mode_requires_mapping_artifact(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    with pytest.raises(ReplayContractError, match="PHASE3_MAPPING_ONLY requires phase3 ruleset mapping artifact"):
        run_backtester(
            artifact_dir=artifact_dir,
            output_dir=tmp_path / "out",
            ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
            variant_names=("BASE",),
            cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
            same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
            replay_semantics_version="REPLAY_V0_1",
            generation_timestamp="2024-01-01T00:00:00+00:00",
            cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
        )




def test_phase3_mapping_only_phase4_gate_happy_path_writes_artifacts_and_runs(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "out"
    _write_analyzer_artifacts(artifact_dir)

    pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "RulesetId": "RULESET_1",
                "RulesetContractVersion": "CONTRACT_V1",
                "MappingVersion": "MAPPING_V1",
                "MappingStatus": "READY",
                "ReplaySemanticsVersion": "REPLAY_V0_1",
                "SetupFamily": "FAILED_BREAK_RECLAIM_SHORT",
                "Direction": "SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP",
                "EntryTriggerMapping": "EXPLICIT_TRIGGER",
                "EntryBoundaryMapping": "EXPLICIT_ENTRY_BOUNDARY",
                "ExitBoundaryMapping": "EXPLICIT_EXIT_BOUNDARY",
                "RiskMapping": "EXPLICIT_RISK",
                "ReplayIntegrationStatus": "READY_FOR_BINDING",
                "KnownUnresolvedMappings": "",
                "NextAction": "",
            }
        ]
    ).to_csv(artifact_dir / "phase3_ruleset_mapping.csv", index=False)

    result = run_backtester(
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
        variant_names=("BASE",),
        cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
        same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
        replay_semantics_version="REPLAY_V0_1",
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
    )

    assert result.rulesets_path.exists()
    assert (output_dir / "backtest_rulesets.csv").exists()
    assert (output_dir / "phase4_ruleset_validation_summary.csv").exists()
    assert (output_dir / "phase4_ruleset_validation_details.csv").exists()

    orchestration_manifest = json.loads(result.orchestration_manifest_path.read_text(encoding="utf-8"))
    assert orchestration_manifest["phase4_validation_paths"]["summary"]
    assert orchestration_manifest["phase4_validation_paths"]["details"]

def test_phase3_mapping_only_phase4_gate_blocks_when_no_replay_eligible_ruleset(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "RulesetId": "RULESET_1",
                "RulesetContractVersion": "CONTRACT_V1",
                "MappingVersion": "MAPPING_V1",
                "MappingStatus": "PARTIAL",
                "ReplaySemanticsVersion": "REPLAY_V0_1",
                "SetupFamily": "FAILED_BREAK_RECLAIM_SHORT",
                "Direction": "SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP",
                "EntryTriggerMapping": "MANUAL_MAPPING_REQUIRED",
                "EntryBoundaryMapping": "MANUAL_MAPPING_REQUIRED",
                "ExitBoundaryMapping": "MANUAL_MAPPING_REQUIRED",
                "RiskMapping": "MANUAL_MAPPING_REQUIRED",
                "ReplayIntegrationStatus": "NOT_INTEGRATED",
                "KnownUnresolvedMappings": "ENTRY_EXIT_RISK_REPLAY_MAPPING_UNRESOLVED",
                "NextAction": "MANUAL_RULESET_TO_REPLAY_BINDING",
            }
        ]
    ).to_csv(artifact_dir / "phase3_ruleset_mapping.csv", index=False)

    with pytest.raises(ReplayContractError, match="Phase 4 ruleset validation gate blocked replay"):
        run_backtester(
            artifact_dir=artifact_dir,
            output_dir=tmp_path / "out",
            ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
            variant_names=("BASE",),
            cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
            same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
            replay_semantics_version="REPLAY_V0_1",
            generation_timestamp="2024-01-01T00:00:00+00:00",
            cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
        )


def test_zero_ruleset_path_fails_loudly_before_placement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(artifact_dir)

    empty_shortlist = pd.DataFrame(columns=["SourceReport", "GroupType", "GroupValue", "SelectionDecision"])
    empty_shortlist.to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    empty_shortlist.to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)

    def _placement_must_not_run(*args, **kwargs):
        raise AssertionError("placement must not run when no replayable rulesets materialize")

    monkeypatch.setattr("backtester.orchestrator.materialize_stop_target_levels", _placement_must_not_run)

    with pytest.raises(ReplayContractError, match="No replayable canonical rulesets materialized"):
        _run(artifact_dir, output_dir)

    saved_rulesets = pd.read_csv(output_dir / "backtest_rulesets.csv")
    assert saved_rulesets.empty



def test_multi_ruleset_fanout_creates_one_row_child_runs_without_parent_collapse(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(
        artifact_dir,
        shortlist_rows=[
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "SELECT",
            },
            {
                "SourceReport": "REPORT_B",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SelectionDecision": "SELECT",
            },
        ],
    )

    result = _run(artifact_dir, output_dir)

    parent_rulesets = pd.read_csv(output_dir / "backtest_rulesets.csv")
    assert parent_rulesets["ruleset_id"].tolist() == [
        "RULESET_REPORT_A_DIRECTION_LONG_V1_LONG_BASE",
        "RULESET_REPORT_B_DIRECTION_SHORT_V1_SHORT_BASE",
    ]

    derived_names = [path.name for path in result.derived_run_dirs]
    assert derived_names[0].startswith("derived_run_0001_")
    assert derived_names[1].startswith("derived_run_0002_")
    assert derived_names == sorted(derived_names)

    child_ruleset_ids: list[str] = []
    for child_dir in result.derived_run_dirs:
        child_rulesets = pd.read_csv(child_dir / "backtest_rulesets.csv")
        assert len(child_rulesets.index) == 1
        child_ruleset_ids.append(str(child_rulesets.iloc[0]["ruleset_id"]))

        child_manifest = json.loads((child_dir / ORCHESTRATION_MANIFEST_NAME).read_text(encoding="utf-8"))
        assert child_manifest["run_type"] == "SINGLE_REPLAY_RUN"
        assert child_manifest["completion_state"] == "COMPLETED"
        assert child_manifest["ruleset_count"] == 1
        assert child_manifest["derived_run_count"] == 0

    assert child_ruleset_ids == parent_rulesets["ruleset_id"].tolist()

    parent_manifest = json.loads((output_dir / ORCHESTRATION_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert parent_manifest["run_type"] == "FANOUT_PARENT_LINEAGE_ONLY"
    assert parent_manifest["completion_state"] == "COMPLETED"
    assert parent_manifest["derived_run_count"] == 2
    assert parent_manifest["derived_run_dirs"] == [str(path) for path in result.derived_run_dirs]
    assert parent_manifest["planned_derived_run_dirs"] == [str(path) for path in result.derived_run_dirs]
    assert parent_manifest["engine_event_count"] is None
    assert parent_manifest["trade_count"] is None


def test_multi_ruleset_fanout_preserves_placement_single_ruleset_contract(tmp_path: Path):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(
        artifact_dir,
        shortlist_rows=[
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "SELECT",
            },
            {
                "SourceReport": "REPORT_B",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SelectionDecision": "SELECT",
            },
        ],
    )

    result = _run(artifact_dir, output_dir)

    assert len(result.derived_run_dirs) == 2
    for child_dir in result.derived_run_dirs:
        assert (child_dir / "backtest_run_manifest.json").exists()
        child_rulesets = pd.read_csv(child_dir / "backtest_rulesets.csv")
        assert len(child_rulesets.index) == 1


def test_multi_ruleset_fanout_partial_failure_writes_parent_lineage_manifest_with_completed_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    artifact_dir = tmp_path / "analyzer_run"
    output_dir = tmp_path / "backtest_run"
    _write_analyzer_artifacts(
        artifact_dir,
        shortlist_rows=[
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "SELECT",
            },
            {
                "SourceReport": "REPORT_B",
                "GroupType": "Direction",
                "GroupValue": "SHORT",
                "SelectionDecision": "SELECT",
            },
        ],
    )

    original = run_backtester.__globals__["_run_single_backtester"]

    def _fail_second_child(*args, **kwargs):
        out_dir = kwargs["out_dir"]
        if out_dir.name.startswith("derived_run_0002_"):
            raise ReplayContractError("simulated child failure")
        return original(*args, **kwargs)

    monkeypatch.setitem(run_backtester.__globals__, "_run_single_backtester", _fail_second_child)

    with pytest.raises(ReplayContractError, match="failed_ruleset_id="):
        _run(artifact_dir, output_dir)

    first_child = next(output_dir.glob("derived_run_0001_*"))
    assert (first_child / "backtest_run_manifest.json").exists()

    parent_manifest = json.loads((output_dir / ORCHESTRATION_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert parent_manifest["run_type"] == "FANOUT_PARENT_LINEAGE_ONLY"
    assert parent_manifest["completion_state"] == "PARTIAL_FAILURE"
    assert parent_manifest["derived_run_count"] == 1
    assert len(parent_manifest["derived_run_dirs"]) == 1
    assert len(parent_manifest["planned_derived_run_dirs"]) == 2
    assert parent_manifest["failed_ruleset_id"] == "RULESET_REPORT_B_DIRECTION_SHORT_V1_SHORT_BASE"
