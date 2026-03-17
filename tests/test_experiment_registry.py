from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtester.experiment_registry import (
    REGISTRY_COLUMNS,
    append_registry_row,
    build_registry_row_for_completed_run,
)


def test_registry_append_only_preserves_existing_rows_and_order(tmp_path: Path):
    registry_path = tmp_path / "phase5_experiment_registry.csv"
    first = {column: f"v1_{column}" for column in REGISTRY_COLUMNS}
    second = {column: f"v2_{column}" for column in REGISTRY_COLUMNS}

    append_registry_row(registry_path=registry_path, row=first)
    append_registry_row(registry_path=registry_path, row=second)

    out = pd.read_csv(registry_path)
    assert list(out.columns) == REGISTRY_COLUMNS
    assert out.iloc[0]["ExperimentId"] == "v1_ExperimentId"
    assert out.iloc[1]["ExperimentId"] == "v2_ExperimentId"


def test_registry_row_extracts_completed_run_facts(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    raw_path = tmp_path / "raw.csv"

    pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "Open": 1, "High": 1, "Low": 1, "Close": 1, "IsSynthetic": 0},
            {"Timestamp": "2024-01-02T00:00:00Z", "Open": 1, "High": 1, "Low": 1, "Close": 1, "IsSynthetic": 0},
        ]
    ).to_csv(raw_path, index=False)

    (run_dir / "backtest_orchestration_manifest.json").write_text(
        json.dumps(
            {
                "cost_model_id": "COST_MODEL_ZERO_SKELETON_ONLY",
                "same_bar_policy_id": "SAME_BAR_CONSERVATIVE_V0_1",
                "trade_count": 3,
                "git_commit": "abc123",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "backtest_run_manifest.json").write_text(
        json.dumps({"artifact_paths": {"raw": str(raw_path)}}),
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            {
                "ruleset_id": "R1",
                "ruleset_version": "v0.1",
                "replay_semantics_version": "REPLAY_V0_1",
                "source_lineage_artifact": "phase3_ruleset_mapping.csv",
            }
        ]
    ).to_csv(run_dir / "backtest_rulesets.csv", index=False)
    pd.DataFrame(
        [{"scope": "ALL_TRADES", "validation_status": "PASS", "resolved_trade_count": 2}]
    ).to_csv(run_dir / "backtest_validation_summary.csv", index=False)
    pd.DataFrame([{"scope": "ALL_TRADES", "promotion_decision": "REVIEW"}]).to_csv(
        run_dir / "backtest_promotion_decisions.csv", index=False
    )

    row = build_registry_row_for_completed_run(
        run_dir=run_dir,
        input_artifact_dir=tmp_path / "artifact",
        experiment_id="exp-1",
        experiment_label="baseline",
        duration_seconds=1.5,
        run_timestamp="2024-01-03T00:00:00+00:00",
    )

    assert row["ExperimentId"] == "exp-1"
    assert row["RulesetId"] == "R1"
    assert row["ValidationSummaryStatus"] == "PASS"
    assert row["PromotionSummaryStatus"] == "REVIEW"
    assert row["TradeCount"] == 3
    assert row["ResolvedTradeCount"] == 2
    assert row["DateRangeStart"].startswith("2024-01-01")
    assert row["DateRangeEnd"].startswith("2024-01-02")
