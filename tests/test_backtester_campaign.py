from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import pytest

from backtester.campaign import run_backtest_campaign
from backtester.engine import ReplayContractError, ZeroCostSkeletonModel


def _write_analyzer_artifacts(artifact_dir: Path, *, shortlist_direction: str = "LONG") -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "IsSynthetic": 0},
            {"Timestamp": "2024-01-01T00:01:00Z", "Open": 101.0, "High": 102.0, "Low": 100.0, "Close": 101.5, "IsSynthetic": 0},
            {"Timestamp": "2024-01-01T00:02:00Z", "Open": 102.0, "High": 103.0, "Low": 101.0, "Close": 102.5, "IsSynthetic": 0},
        ]
    ).to_csv(artifact_dir / "raw.csv", index=False)
    pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "DummyFeature": 1.0},
            {"Timestamp": "2024-01-01T00:01:00Z", "DummyFeature": 1.1},
            {"Timestamp": "2024-01-01T00:02:00Z", "DummyFeature": 1.2},
        ]
    ).to_csv(artifact_dir / "analyzer_features.csv", index=False)
    pd.DataFrame(
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
    ).to_csv(artifact_dir / "analyzer_setups.csv", index=False)
    pd.DataFrame(
        [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": shortlist_direction,
                "SelectionDecision": "SELECT",
            }
        ]
    ).to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    pd.DataFrame(
        [
            {
                "SourceReport": "REPORT_A",
                "GroupType": "Direction",
                "GroupValue": shortlist_direction,
                "SelectionDecision": "SELECT",
            }
        ]
    ).to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)


def _campaign_kwargs() -> dict:
    return {
        "campaign_label": "baseline",
        "ruleset_source_formalization_mode": "SHORTLIST_FIRST",
        "variant_names": ("BASE",),
        "cost_model_id": "COST_MODEL_ZERO_SKELETON_ONLY",
        "same_bar_policy_id": "SAME_BAR_CONSERVATIVE_V0_1",
        "replay_semantics_version": "REPLAY_V0_1",
        "generation_timestamp": "2024-01-01T00:00:00+00:00",
        "backtester_kwargs": {"cost_models": {"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()}},
    }


def test_campaign_happy_path_writes_manifest_summary_index_and_registry(tmp_path: Path):
    a1 = tmp_path / "a1"
    a2 = tmp_path / "a2"
    _write_analyzer_artifacts(a1)
    _write_analyzer_artifacts(a2)

    result = run_backtest_campaign(
        artifact_dirs=[a1, a2],
        output_dir=tmp_path / "campaign",
        **_campaign_kwargs(),
    )

    assert result.campaign_manifest_path.exists()
    assert result.campaign_summary_path.exists()
    assert result.campaign_run_index_path.exists()
    registry = pd.read_csv(result.registry_path)
    assert len(registry.index) == 2


def test_campaign_stop_on_error_writes_completed_only_registry(tmp_path: Path):
    ok = tmp_path / "ok"
    bad = tmp_path / "bad"
    _write_analyzer_artifacts(ok)
    bad.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ReplayContractError):
        run_backtest_campaign(
            artifact_dirs=[ok, bad],
            output_dir=tmp_path / "campaign",
            **_campaign_kwargs(),
        )

    registry = pd.read_csv(tmp_path / "campaign" / "phase5_experiment_registry.csv")
    assert len(registry.index) == 1


def test_campaign_zero_trade_run_is_completed_and_registered(tmp_path: Path):
    no_trades = tmp_path / "no_trades"
    _write_analyzer_artifacts(no_trades, shortlist_direction="SHORT")

    result = run_backtest_campaign(
        artifact_dirs=[no_trades],
        output_dir=tmp_path / "campaign",
        **_campaign_kwargs(),
    )

    registry = pd.read_csv(result.registry_path)
    assert len(registry.index) == 1
    assert int(registry.iloc[0]["TradeCount"]) == 0
    summary = pd.read_csv(result.campaign_summary_path)
    assert int(summary.iloc[0]["RunCountCompleted"]) == 1
    assert int(summary.iloc[0]["RunCountFailed"]) == 0


def test_campaign_ids_are_deterministic_across_different_run_timestamps(tmp_path: Path):
    a1 = tmp_path / "a1"
    a2 = tmp_path / "a2"
    _write_analyzer_artifacts(a1)
    _write_analyzer_artifacts(a2)

    kwargs = _campaign_kwargs()
    kwargs["generation_timestamp"] = "2024-01-01T00:00:00+00:00"
    first = run_backtest_campaign(
        artifact_dirs=[a1, a2],
        output_dir=tmp_path / "campaign_first",
        **kwargs,
    )

    kwargs = _campaign_kwargs()
    kwargs["generation_timestamp"] = "2024-01-02T00:00:00+00:00"
    second = run_backtest_campaign(
        artifact_dirs=[a1, a2],
        output_dir=tmp_path / "campaign_second",
        **kwargs,
    )

    first_manifest = json.loads(first.campaign_manifest_path.read_text(encoding="utf-8"))
    second_manifest = json.loads(second.campaign_manifest_path.read_text(encoding="utf-8"))
    assert first_manifest["CampaignId"] == second_manifest["CampaignId"]

    first_index = pd.read_csv(first.campaign_run_index_path)
    second_index = pd.read_csv(second.campaign_run_index_path)
    assert first_index["ExperimentId"].tolist() == second_index["ExperimentId"].tolist()


def test_campaign_continue_on_error_keeps_later_runs(tmp_path: Path):
    ok1 = tmp_path / "ok1"
    bad = tmp_path / "bad"
    ok2 = tmp_path / "ok2"
    _write_analyzer_artifacts(ok1)
    bad.mkdir(parents=True, exist_ok=True)
    _write_analyzer_artifacts(ok2)

    result = run_backtest_campaign(
        artifact_dirs=[ok1, bad, ok2],
        output_dir=tmp_path / "campaign",
        continue_on_error=True,
        **_campaign_kwargs(),
    )

    registry = pd.read_csv(result.registry_path)
    assert len(registry.index) == 2

    run_index = pd.read_csv(result.campaign_run_index_path)
    assert run_index["CompletionState"].tolist() == ["COMPLETED", "FAILED", "COMPLETED"]

    summary = pd.read_csv(result.campaign_summary_path)
    assert int(summary.iloc[0]["RunCountCompleted"]) == 2
    assert int(summary.iloc[0]["RunCountFailed"]) == 1
