from pathlib import Path

from analyzer.pipeline import run


def test_pipeline_smoke_writes_outputs(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)

    assert result["features"].shape[0] == 2
    assert result["events"].empty
    assert result["features_path"].exists()
    assert result["events_path"].exists()


def test_fixture_files_exist_and_loadable():
    fixtures_dir = Path(__file__).parent / "fixtures"
    expected = [
        "sample_raw_minimal.csv",
        "sample_raw_with_synthetic.csv",
        "sample_raw_with_gap.csv",
    ]

    for filename in expected:
        assert (fixtures_dir / filename).exists()
