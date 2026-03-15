"""Тести для analyzer.run_daily — щоденний запуск Analyzer pipeline."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from analyzer.run_daily import (
    EXPECTED_ARTIFACTS,
    REQUIRED_ARTIFACT_COLUMNS,
    _allocate_run_dir,
    _extract_date_from_filename,
    _is_partial_day,
    _next_run_seq,
    run_daily,
    validate_input,
    verify_artifacts,
)


def test_validate_input_missing_file(tmp_path):
    missing = tmp_path / "2026-03-13.csv"
    with pytest.raises(FileNotFoundError, match="не знайдено"):
        validate_input(missing)


def test_validate_input_not_a_file(tmp_path):
    with pytest.raises(ValueError, match="не є файлом"):
        validate_input(tmp_path)


def test_validate_input_not_csv(tmp_path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("data")
    with pytest.raises(ValueError, match="не є CSV"):
        validate_input(txt_file)


def test_validate_input_valid_csv(tmp_path):
    csv_file = tmp_path / "2026-03-13.csv"
    csv_file.write_text("col1,col2\n1,2\n")
    validate_input(csv_file)


def test_extract_date_valid():
    assert _extract_date_from_filename(Path("2026-03-13.csv")) == "2026-03-13"


def test_extract_date_invalid_format():
    with pytest.raises(ValueError, match="не відповідає"):
        _extract_date_from_filename(Path("not-a-date.csv"))


def test_extract_date_invalid_date():
    with pytest.raises(ValueError):
        _extract_date_from_filename(Path("2026-13-45.csv"))


def test_is_partial_day_today():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert _is_partial_day(today) is True


def test_is_partial_day_past():
    assert _is_partial_day("2020-01-01") is False


def test_next_run_seq_empty_dir(tmp_path):
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 1


def test_next_run_seq_nonexistent_dir(tmp_path):
    assert _next_run_seq(tmp_path / "missing", "2026-03-13_to_2026-03-13") == 1


def test_next_run_seq_increments(tmp_path):
    (tmp_path / "2026-03-13_to_2026-03-13_run_001").mkdir()
    (tmp_path / "2026-03-13_to_2026-03-13_run_002").mkdir()
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 3


def test_next_run_seq_ignores_other_dates(tmp_path):
    (tmp_path / "2026-03-12_to_2026-03-12_run_005").mkdir()
    (tmp_path / "2026-03-13_to_2026-03-13_run_001").mkdir()
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 2


def test_allocate_run_dir_creates_directory(tmp_path):
    run_dir = _allocate_run_dir(tmp_path, "2026-03-13")
    assert run_dir.exists()
    assert run_dir.is_dir()
    assert run_dir.name == "2026-03-13_to_2026-03-13_run_001"


def test_allocate_run_dir_increments(tmp_path):
    d1 = _allocate_run_dir(tmp_path, "2026-03-13")
    d2 = _allocate_run_dir(tmp_path, "2026-03-13")
    assert d1.name == "2026-03-13_to_2026-03-13_run_001"
    assert d2.name == "2026-03-13_to_2026-03-13_run_002"


def test_verify_artifacts_all_present(tmp_path):
    for name in EXPECTED_ARTIFACTS:
        (tmp_path / name).write_text("header\n")
    assert verify_artifacts(tmp_path) == []


def test_verify_artifacts_missing(tmp_path):
    missing = verify_artifacts(tmp_path)
    assert set(missing) == set(EXPECTED_ARTIFACTS)


def _make_feed_file(feed_dir: Path, date_str: str) -> Path:
    src = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"
    dst = feed_dir / f"{date_str}.csv"
    shutil.copy(src, dst)
    return dst


def _value_for_col(col: str, idx: int):
    if "Timestamp" in col or col.endswith("At") or col.endswith("Ts"):
        return f"2025-01-01T00:0{idx}:00Z"
    if col in {"Direction", "SelectionDecision"}:
        return "LONG"
    if col == "SelectionReason":
        return "reason"
    if col == "SourceReport":
        return "setup_report"
    if col == "GroupType":
        return "Direction"
    if col == "GroupValue":
        return "LONG"
    if col in {"EventType", "ReferenceEventType", "EligibleEventTypes"}:
        return "FAILED_BREAK_DOWN"
    if col == "SourceTF":
        return "H1"
    if col in {"SetupType", "Status", "LifecycleStatus", "OutcomeStatus", "RankingLabel", "ResearchPriority"}:
        return "TEST"
    if col in {"FormalizationEligible", "CtxRelVolumeSpike_v1", "CtxDeltaSpike_v1", "CtxOISpike_v1", "CtxLiqSpike_v1", "CtxWickReclaim_v1"}:
        return True
    if col == "MetaJson":
        return "{}"
    if col == "SetupId":
        return f"setup-{idx}"
    if col == "ShortlistRank":
        return idx + 1
    return 1.0


def _artifact_df(artifact_name: str, rows: int = 2) -> pd.DataFrame:
    cols = REQUIRED_ARTIFACT_COLUMNS[artifact_name]
    values = [{col: _value_for_col(col, i) for col in cols} for i in range(rows)]
    return pd.DataFrame(values, columns=cols)


def _mock_pipeline_run(input_path, output_dir):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_ARTIFACTS:
        _artifact_df(name, rows=2).to_csv(out_dir / name, index=False)
    return {"features": pd.DataFrame({"col": range(100)})}


def _mock_pipeline_run_empty_day(input_path, output_dir):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_ARTIFACTS:
        _artifact_df(name, rows=0).to_csv(out_dir / name, index=False)
    return {"features": pd.DataFrame(columns=["col"]) }


def test_run_daily_success(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        result = run_daily(feed_file, runs_root)

    with open(result["manifest_path"], encoding="utf-8") as f:
        manifest = json.load(f)

    assert result["status"] == "SUCCESS"
    assert manifest["status"] == "SUCCESS"
    assert manifest["run_date"] == "2025-01-01"
    assert manifest["date_range"] == {"from": "2025-01-01", "to": "2025-01-01"}
    assert manifest["artifact_count"] == len(EXPECTED_ARTIFACTS)
    assert manifest["row_counts"]["analyzer_features.csv"] == 2
    assert set(manifest["artifact_paths"]) == set(EXPECTED_ARTIFACTS)
    assert set(manifest["artifact_hashes"]) == set(EXPECTED_ARTIFACTS)
    assert "input_feed_checksums" in manifest
    assert "artifact_contract_version" in manifest
    assert "analyzer_schema_version" in manifest


def test_run_daily_success_with_empty_day_artifacts(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run_empty_day):
        result = run_daily(feed_file, runs_root)

    with open(result["manifest_path"], encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["status"] == "SUCCESS"
    assert set(manifest["row_counts"].values()) == {0}


def test_run_daily_missing_artifacts_marks_non_canonical(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    def _incomplete_pipeline(input_path, output_dir):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        _artifact_df("analyzer_features.csv", rows=1).to_csv(out / "analyzer_features.csv", index=False)
        _artifact_df("analyzer_events.csv", rows=1).to_csv(out / "analyzer_events.csv", index=False)
        return {"features": pd.DataFrame({"c": range(10)})}

    with patch("analyzer.run_daily.pipeline.run", side_effect=_incomplete_pipeline):
        with pytest.raises(ValueError, match="Відсутній required артефакт"):
            run_daily(feed_file, runs_root)

    manifest_path = next(runs_root.iterdir()) / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "NON_CANONICAL"


def test_run_daily_schema_mismatch_marks_non_canonical(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    def _schema_drift_pipeline(input_path, output_dir):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name in EXPECTED_ARTIFACTS:
            df = _artifact_df(name, rows=1)
            if name == "analyzer_setup_rankings.csv":
                df = df.rename(columns={df.columns[-1]: "UnexpectedColumn"})
            df.to_csv(out / name, index=False)
        return {"features": pd.DataFrame({"c": range(10)})}

    with patch("analyzer.run_daily.pipeline.run", side_effect=_schema_drift_pipeline):
        with pytest.raises(ValueError, match="Schema mismatch"):
            run_daily(feed_file, runs_root)

    manifest_path = next(runs_root.iterdir()) / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "NON_CANONICAL"


def test_run_daily_pipeline_failure_writes_failed_manifest(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    def _failing_pipeline(input_path, output_dir):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        raise RuntimeError("Pipeline exploded")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_failing_pipeline):
        with pytest.raises(RuntimeError, match="Pipeline exploded"):
            run_daily(feed_file, runs_root)

    manifest_path = next(runs_root.iterdir()) / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"


def test_run_daily_partial_day_flag(tmp_path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    feed_file = _make_feed_file(feed_dir, today_str)

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        result = run_daily(feed_file, runs_root)

    manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
    assert manifest["input_includes_partial_day"] is True
