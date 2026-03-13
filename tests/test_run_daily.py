"""Тести для analyzer.run_daily — щоденний запуск Analyzer pipeline."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from analyzer.run_daily import (
    EXPECTED_ARTIFACTS,
    _extract_date_from_filename,
    _is_partial_day,
    _next_run_seq,
    _allocate_run_dir,
    run_daily,
    validate_input,
    verify_artifacts,
)


# --- validate_input ---


def test_validate_input_missing_file(tmp_path):
    """Відсутній файл → FileNotFoundError."""
    missing = tmp_path / "2026-03-13.csv"
    with pytest.raises(FileNotFoundError, match="не знайдено"):
        validate_input(missing)


def test_validate_input_not_a_file(tmp_path):
    """Шлях до директорії → ValueError."""
    with pytest.raises(ValueError, match="не є файлом"):
        validate_input(tmp_path)


def test_validate_input_not_csv(tmp_path):
    """Файл без .csv розширення → ValueError."""
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("data")
    with pytest.raises(ValueError, match="не є CSV"):
        validate_input(txt_file)


def test_validate_input_valid_csv(tmp_path):
    """Валідний CSV файл проходить перевірку."""
    csv_file = tmp_path / "2026-03-13.csv"
    csv_file.write_text("col1,col2\n1,2\n")
    validate_input(csv_file)  # не кидає


# --- _extract_date_from_filename ---


def test_extract_date_valid():
    assert _extract_date_from_filename(Path("2026-03-13.csv")) == "2026-03-13"


def test_extract_date_invalid_format():
    with pytest.raises(ValueError, match="не відповідає"):
        _extract_date_from_filename(Path("not-a-date.csv"))


def test_extract_date_invalid_date():
    with pytest.raises(ValueError):
        _extract_date_from_filename(Path("2026-13-45.csv"))


# --- _is_partial_day ---


def test_is_partial_day_today():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert _is_partial_day(today) is True


def test_is_partial_day_past():
    assert _is_partial_day("2020-01-01") is False


# --- _next_run_seq ---


def test_next_run_seq_empty_dir(tmp_path):
    """Порожня директорія → seq = 1."""
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 1


def test_next_run_seq_nonexistent_dir(tmp_path):
    """Неіснуюча директорія → seq = 1."""
    assert _next_run_seq(tmp_path / "missing", "2026-03-13_to_2026-03-13") == 1


def test_next_run_seq_increments(tmp_path):
    """Існуючі runs → наступний seq."""
    (tmp_path / "2026-03-13_to_2026-03-13_run_001").mkdir()
    (tmp_path / "2026-03-13_to_2026-03-13_run_002").mkdir()
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 3


def test_next_run_seq_ignores_other_dates(tmp_path):
    """Директорії з іншими датами не впливають на seq."""
    (tmp_path / "2026-03-12_to_2026-03-12_run_005").mkdir()
    (tmp_path / "2026-03-13_to_2026-03-13_run_001").mkdir()
    assert _next_run_seq(tmp_path, "2026-03-13_to_2026-03-13") == 2


# --- _allocate_run_dir ---


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


# --- verify_artifacts ---


def test_verify_artifacts_all_present(tmp_path):
    for name in EXPECTED_ARTIFACTS:
        (tmp_path / name).write_text("header\n")
    assert verify_artifacts(tmp_path) == []


def test_verify_artifacts_missing(tmp_path):
    missing = verify_artifacts(tmp_path)
    assert set(missing) == set(EXPECTED_ARTIFACTS)


def test_verify_artifacts_partial(tmp_path):
    (tmp_path / "analyzer_features.csv").write_text("header\n")
    missing = verify_artifacts(tmp_path)
    assert "analyzer_features.csv" not in missing
    assert len(missing) == len(EXPECTED_ARTIFACTS) - 1


# --- run_daily (інтеграційні тести з mock pipeline) ---


def _make_feed_file(feed_dir: Path, date_str: str) -> Path:
    """Створює мінімальний feed CSV для тестів."""
    src = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"
    dst = feed_dir / f"{date_str}.csv"
    shutil.copy(src, dst)
    return dst


def _mock_pipeline_run(input_path, output_dir):
    """Mock pipeline.run що створює всі артефакти як порожні CSV."""
    import pandas as pd

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_ARTIFACTS:
        pd.DataFrame({"col": [1, 2]}).to_csv(out_dir / name, index=False)
    return {"features": pd.DataFrame({"col": range(100)})}


def test_run_daily_success(tmp_path):
    """Успішний run створює директорію, артефакти та manifest."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        result = run_daily(feed_file, runs_root)

    assert result["status"] == "SUCCESS"
    assert result["run_id"] == "2025-01-01_to_2025-01-01_run_001"
    assert result["run_dir"].exists()
    assert result["manifest_path"].exists()

    # Перевірка manifest
    with open(result["manifest_path"], encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["run_id"] == "2025-01-01_to_2025-01-01_run_001"
    assert manifest["status"] == "SUCCESS"
    assert manifest["input_date_range"] == {"from": "2025-01-01", "to": "2025-01-01"}
    assert manifest["input_includes_partial_day"] is False
    assert manifest["artifact_count"] == 11
    assert manifest["pipeline_stage_count"] == 16
    assert manifest["notes"] is None
    assert len(manifest["artifact_list"]) == 11
    assert len(manifest["input_feed_paths"]) == 1
    assert "generated_at_utc" in manifest
    assert "git_commit" in manifest
    assert "git_branch" in manifest
    assert "hostname" in manifest
    assert "python_version" in manifest
    assert "input_bar_count" in manifest
    assert manifest["input_bar_count"] == 100
    assert "artifact_row_counts" in manifest




def _mock_pipeline_run_empty_day(input_path, output_dir):
    """Mock pipeline.run для валідного empty-day SUCCESS."""
    import pandas as pd

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_ARTIFACTS:
        pd.DataFrame(columns=["col"]).to_csv(out_dir / name, index=False)
    return {"features": pd.DataFrame(columns=["col"]) }


def test_run_daily_success_with_empty_day_artifacts(tmp_path):
    """Empty day з валідними порожніми артефактами завершується SUCCESS."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run_empty_day):
        result = run_daily(feed_file, runs_root)

    assert result["status"] == "SUCCESS"
    with open(result["manifest_path"], encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["status"] == "SUCCESS"
    assert manifest["input_bar_count"] == 0
    assert set(manifest["artifact_row_counts"]) == set(EXPECTED_ARTIFACTS)
    assert set(manifest["artifact_row_counts"].values()) == {0}

def test_run_daily_repeated_runs_increment(tmp_path):
    """Повторні runs для тієї ж дати інкрементують seq."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        r1 = run_daily(feed_file, runs_root)
        r2 = run_daily(feed_file, runs_root)
        r3 = run_daily(feed_file, runs_root)

    assert r1["run_id"].endswith("_run_001")
    assert r2["run_id"].endswith("_run_002")
    assert r3["run_id"].endswith("_run_003")


def test_run_daily_missing_input(tmp_path):
    """Відсутній вхідний файл → FileNotFoundError."""
    runs_root = tmp_path / "analyzer_runs"
    missing = tmp_path / "feed" / "2025-01-01.csv"

    with pytest.raises(FileNotFoundError):
        run_daily(missing, runs_root)


def test_run_daily_pipeline_failure_writes_failed_manifest(tmp_path):
    """Pipeline failure → re-raise, але manifest з FAILED."""
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

    # Manifest повинен існувати з FAILED
    run_dirs = list(runs_root.iterdir())
    assert len(run_dirs) == 1
    manifest_path = run_dirs[0] / "run_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["status"] == "FAILED"
    assert "Pipeline exploded" in manifest["notes"]


def test_run_daily_missing_artifacts_raises(tmp_path):
    """Pipeline що не створила всі артефакти → ValueError."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    import pandas as pd

    def _incomplete_pipeline(input_path, output_dir):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        # Створюємо тільки 2 з 11 артефактів
        pd.DataFrame({"c": [1]}).to_csv(out / "analyzer_features.csv", index=False)
        pd.DataFrame({"c": [1]}).to_csv(out / "analyzer_events.csv", index=False)
        return {"features": pd.DataFrame({"c": range(10)})}

    with patch("analyzer.run_daily.pipeline.run", side_effect=_incomplete_pipeline):
        with pytest.raises(ValueError, match="Відсутні артефакти"):
            run_daily(feed_file, runs_root)

    # Manifest з FAILED повинен існувати
    run_dirs = list(runs_root.iterdir())
    manifest_path = run_dirs[0] / "run_manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["status"] == "FAILED"


def test_run_daily_partial_day_flag(tmp_path):
    """Файл з поточною UTC датою → partial_day = True."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    feed_file = _make_feed_file(feed_dir, today_str)

    # Фікстура має дату 2025-01-01 в Timestamp, але partial detection
    # базується тільки на імені файлу, не на вмісті
    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        result = run_daily(feed_file, runs_root)

    with open(result["manifest_path"], encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["input_includes_partial_day"] is True


def test_run_daily_does_not_overwrite_existing(tmp_path):
    """Повторний run не перезаписує попередній."""
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    runs_root = tmp_path / "analyzer_runs"

    feed_file = _make_feed_file(feed_dir, "2025-01-01")

    with patch("analyzer.run_daily.pipeline.run", side_effect=_mock_pipeline_run):
        r1 = run_daily(feed_file, runs_root)
        # Записуємо маркер у першу run directory
        marker = r1["run_dir"] / "marker.txt"
        marker.write_text("original")

        r2 = run_daily(feed_file, runs_root)

    # Перший run залишився недоторканим
    assert marker.read_text() == "original"
    assert r1["run_dir"] != r2["run_dir"]
