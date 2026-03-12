from pathlib import Path

import pandas as pd
import pytest

from analyzer.pipeline import run
from analyzer.schema import FEATURE_COLUMNS_IMPLEMENTED, FEATURE_COLUMNS_PLANNED


RANKING_INPUT_COLUMNS = [
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
]


def test_pipeline_fails_loudly_when_report_is_empty(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    with pytest.raises(ValueError, match="non-empty report_df"):
        run(fixture, tmp_path)


def test_pipeline_smoke_writes_outputs_with_valid_report_baseline(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    mock_report = pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "ABSORPTION_LONG",
                "SampleCount": 7,
                "Mean_MFE_Pct": 1.2,
                "Mean_MAE_Pct": -0.8,
                "Mean_CloseReturn_Pct": 0.7,
                "PositiveCloseReturnRate": 0.6,
            },
        ]
    )
    mock_context_report = pd.DataFrame(columns=RANKING_INPUT_COLUMNS)

    monkeypatch.setattr("analyzer.pipeline.build_setup_report", lambda setups, outcomes: mock_report)
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_context_report",
        lambda setups, outcomes: mock_context_report,
    )

    result = run(fixture, tmp_path)

    assert result["features"].shape[0] == 2
    assert result["events"].empty
    assert result["setups"].empty
    assert result["outcomes"].empty
    assert not result["report"].empty
    assert result["context_report"].empty
    assert not result["rankings"].empty
    assert result["features_path"].exists()
    assert result["events_path"].exists()
    assert result["setups_path"].exists()
    assert result["outcomes_path"].exists()
    assert result["report_path"].exists()
    assert result["context_report_path"].exists()
    assert result["rankings_path"].exists()
    assert result["setups_path"].name == "analyzer_setups.csv"
    assert result["outcomes_path"].name == "analyzer_setup_outcomes.csv"
    assert result["report_path"].name == "analyzer_setup_report.csv"
    assert result["context_report_path"].name == "analyzer_setup_context_report.csv"
    assert result["rankings_path"].name == "analyzer_setup_rankings.csv"


def test_pipeline_output_contains_implemented_feature_columns(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_report",
        lambda setups, outcomes: pd.DataFrame(
            [
                {
                    "GroupType": "overall",
                    "GroupValue": "ALL",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
                {
                    "GroupType": "SetupType",
                    "GroupValue": "X",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_context_report",
        lambda setups, outcomes: pd.DataFrame(columns=RANKING_INPUT_COLUMNS),
    )

    result = run(fixture, tmp_path)
    features = result["features"]

    for col in FEATURE_COLUMNS_IMPLEMENTED:
        assert col in features.columns


def test_pipeline_output_does_not_claim_planned_columns_as_materialized(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_report",
        lambda setups, outcomes: pd.DataFrame(
            [
                {
                    "GroupType": "overall",
                    "GroupValue": "ALL",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
                {
                    "GroupType": "SetupType",
                    "GroupValue": "X",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_context_report",
        lambda setups, outcomes: pd.DataFrame(columns=RANKING_INPUT_COLUMNS),
    )

    result = run(fixture, tmp_path)
    features = result["features"]

    for col in FEATURE_COLUMNS_PLANNED:
        assert col not in features.columns


def test_fixture_files_exist_and_loadable():
    fixtures_dir = Path(__file__).parent / "fixtures"
    expected = [
        "sample_raw_minimal.csv",
        "sample_raw_with_synthetic.csv",
        "sample_raw_with_gap.csv",
    ]

    for filename in expected:
        assert (fixtures_dir / filename).exists()
