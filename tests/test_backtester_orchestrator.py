from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from analyzer import pipeline as analyzer_pipeline
from backtester.engine import ReplayContractError, ZeroCostSkeletonModel
from backtester.orchestrator import ORCHESTRATION_MANIFEST_NAME, result_as_dict, run_backtester


def _write_analyzer_artifacts(artifact_dir: Path) -> None:
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
            }
        ]
    )
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "SELECT",
            }
        ]
    )
    research_summary = shortlist.copy()

    raw.to_csv(artifact_dir / "raw.csv", index=False)
    features.to_csv(artifact_dir / "analyzer_features.csv", index=False)
    setups.to_csv(artifact_dir / "analyzer_setups.csv", index=False)
    shortlist.to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    research_summary.to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)


def _run(artifact_dir: Path, output_dir: Path):
    return run_backtester(
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        ruleset_source_formalization_mode="SHORTLIST_FIRST",
        variant_names=("BASE",),
        cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
        same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
        replay_semantics_version="REPLAY_V0_1",
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


def test_boundary_preservation_orchestrator_does_not_call_analyzer_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artifact_dir = tmp_path / "analyzer_run"
    _write_analyzer_artifacts(artifact_dir)

    def _boom(*args, **kwargs):
        raise AssertionError("analyzer.pipeline.run must not be called by backtester orchestrator")

    monkeypatch.setattr(analyzer_pipeline, "run", _boom)

    _run(artifact_dir, tmp_path / "out")


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
