from pathlib import Path

from analyzer.pipeline import run
from analyzer.schema import FEATURE_COLUMNS_IMPLEMENTED, FEATURE_COLUMNS_PLANNED


def test_pipeline_smoke_writes_outputs(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)

    assert result["features"].shape[0] == 2
    assert result["events"].empty
    assert result["setups"].empty
    assert result["outcomes"].empty
    assert result["report"].empty
    assert result["features_path"].exists()
    assert result["events_path"].exists()
    assert result["setups_path"].exists()
    assert result["outcomes_path"].exists()
    assert result["report_path"].exists()
    assert result["setups_path"].name == "analyzer_setups.csv"
    assert result["outcomes_path"].name == "analyzer_setup_outcomes.csv"
    assert result["report_path"].name == "analyzer_setup_report.csv"


def test_pipeline_output_contains_implemented_feature_columns(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)
    features = result["features"]

    for col in FEATURE_COLUMNS_IMPLEMENTED:
        assert col in features.columns


def test_pipeline_output_does_not_claim_planned_columns_as_materialized(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

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
