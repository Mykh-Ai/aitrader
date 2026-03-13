"""Щоденний запуск Analyzer pipeline з frozen artifact directory.

Створює один run directory під analyzer_runs/ з усіма артефактами
та run_manifest.json. Не перезаписує попередні runs.
"""

from __future__ import annotations

import json
import platform
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import pipeline

# Канонічний список артефактів, які повинен створити pipeline
EXPECTED_ARTIFACTS = [
    "analyzer_features.csv",
    "analyzer_events.csv",
    "analyzer_setups.csv",
    "analyzer_setup_outcomes.csv",
    "analyzer_setup_report.csv",
    "analyzer_setup_context_report.csv",
    "analyzer_setup_rankings.csv",
    "analyzer_setup_selections.csv",
    "analyzer_setup_shortlist.csv",
    "analyzer_setup_shortlist_explanations.csv",
    "analyzer_research_summary.csv",
]

PIPELINE_STAGE_COUNT = 16

# Дефолтний кореневий каталог для run output
DEFAULT_RUNS_ROOT = Path("/opt/aitrader/analyzer_runs")


def _extract_date_from_filename(file_path: Path) -> str:
    """Витягує дату YYYY-MM-DD з імені файлу feed CSV.

    Raises ValueError якщо формат не відповідає.
    """
    match = re.match(r"^(\d{4}-\d{2}-\d{2})\.csv$", file_path.name)
    if not match:
        raise ValueError(
            f"Ім'я файлу не відповідає формату YYYY-MM-DD.csv: {file_path.name}"
        )
    date_str = match.group(1)
    # Перевіряємо що дата валідна
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def _is_partial_day(date_str: str) -> bool:
    """Визначає чи є вхідний файл partial (поточний UTC день)."""
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return date_str == today_utc


def _next_run_seq(runs_root: Path, date_prefix: str) -> int:
    """Знаходить наступний вільний sequence number для даного date prefix.

    Сканує існуючі директорії в runs_root з відповідним префіксом.
    """
    pattern = re.compile(re.escape(date_prefix) + r"_run_(\d{3})$")
    max_seq = 0
    if runs_root.exists():
        for entry in runs_root.iterdir():
            if entry.is_dir():
                m = pattern.match(entry.name)
                if m:
                    seq = int(m.group(1))
                    if seq > max_seq:
                        max_seq = seq
    return max_seq + 1


def _allocate_run_dir(runs_root: Path, date_str: str) -> Path:
    """Створює та повертає шлях до нової run directory.

    Формат: {date}_to_{date}_run_{NNN}
    """
    date_prefix = f"{date_str}_to_{date_str}"
    seq = _next_run_seq(runs_root, date_prefix)
    run_id = f"{date_prefix}_run_{seq:03d}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _get_git_info() -> tuple[str, str]:
    """Повертає (git_commit, git_branch). Fallback до 'unknown'."""
    commit = "unknown"
    branch = "unknown"
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode().strip()
    except Exception:
        pass
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode().strip()
    except Exception:
        pass
    return commit, branch


def _count_rows(run_dir: Path, artifacts: list[str]) -> dict[str, int]:
    """Рахує кількість рядків у кожному артефакті (без header)."""
    counts: dict[str, int] = {}
    for name in artifacts:
        path = run_dir / name
        if path.exists():
            # Рахуємо рядки мінус header
            with open(path, "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
            counts[name] = max(0, line_count - 1)
    return counts


def _write_manifest(
    run_dir: Path,
    *,
    input_path: Path,
    date_str: str,
    partial_day: bool,
    input_bar_count: int,
    status: str,
    error_message: str | None = None,
) -> Path:
    """Записує run_manifest.json у run directory."""
    run_id = run_dir.name
    git_commit, git_branch = _get_git_info()

    artifact_row_counts = {}
    if status == "SUCCESS":
        artifact_row_counts = _count_rows(run_dir, EXPECTED_ARTIFACTS)

    manifest = {
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "input_feed_paths": [str(input_path)],
        "input_date_range": {"from": date_str, "to": date_str},
        "input_bar_count": input_bar_count,
        "input_includes_partial_day": partial_day,
        "output_dir": str(run_dir),
        "artifact_list": list(EXPECTED_ARTIFACTS),
        "artifact_count": len(EXPECTED_ARTIFACTS),
        "artifact_row_counts": artifact_row_counts,
        "pipeline_stage_count": PIPELINE_STAGE_COUNT,
        "analyzer_version": git_commit,
        "git_commit": git_commit,
        "git_branch": git_branch,
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
        "status": status,
        "notes": error_message,
    }

    manifest_path = run_dir / "run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest_path


def validate_input(input_path: Path) -> None:
    """Перевіряє що вхідний файл існує, читабельний та має формат .csv.

    Raises FileNotFoundError або ValueError при порушенні.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Вхідний файл не знайдено: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Шлях не є файлом: {input_path}")
    if input_path.suffix.lower() != ".csv":
        raise ValueError(f"Файл не є CSV: {input_path}")


def verify_artifacts(run_dir: Path) -> list[str]:
    """Перевіряє наявність усіх очікуваних артефактів.

    Повертає список відсутніх файлів. Порожній список = все ОК.
    """
    missing = []
    for name in EXPECTED_ARTIFACTS:
        if not (run_dir / name).exists():
            missing.append(name)
    return missing


def run_daily(
    input_path: str | Path,
    runs_root: str | Path | None = None,
) -> dict:
    """Запускає щоденний Analyzer run.

    Args:
        input_path: шлях до raw feed CSV (YYYY-MM-DD.csv).
        runs_root: кореневий каталог для run directories.
                   Дефолт: /opt/aitrader/analyzer_runs.

    Returns:
        dict з run_id, run_dir, manifest_path, status.

    Raises:
        FileNotFoundError: вхідний файл не знайдено.
        ValueError: невалідний вхідний файл або відсутні артефакти.
    """
    input_path = Path(input_path)
    if runs_root is None:
        runs_root = DEFAULT_RUNS_ROOT
    runs_root = Path(runs_root)

    # 1. Валідація вхідного файлу
    validate_input(input_path)

    # 2. Витягуємо дату з імені файлу
    date_str = _extract_date_from_filename(input_path)

    # 3. Partial-day detection
    partial_day = _is_partial_day(date_str)

    # 4. Алокація run directory
    run_dir = _allocate_run_dir(runs_root, date_str)
    run_id = run_dir.name

    # 5. Запуск pipeline
    status = "SUCCESS"
    error_message = None
    input_bar_count = 0
    try:
        result = pipeline.run(input_path, run_dir)
        input_bar_count = len(result["features"])
    except Exception as exc:
        status = "FAILED"
        error_message = str(exc)
        # Пишемо manifest з FAILED статусом
        _write_manifest(
            run_dir,
            input_path=input_path,
            date_str=date_str,
            partial_day=partial_day,
            input_bar_count=0,
            status="FAILED",
            error_message=error_message,
        )
        raise

    # 6. Верифікація артефактів
    missing = verify_artifacts(run_dir)
    if missing:
        error_message = f"Відсутні артефакти: {', '.join(missing)}"
        _write_manifest(
            run_dir,
            input_path=input_path,
            date_str=date_str,
            partial_day=partial_day,
            input_bar_count=input_bar_count,
            status="FAILED",
            error_message=error_message,
        )
        raise ValueError(error_message)

    # 7. Запис manifest
    manifest_path = _write_manifest(
        run_dir,
        input_path=input_path,
        date_str=date_str,
        partial_day=partial_day,
        input_bar_count=input_bar_count,
        status="SUCCESS",
    )

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "manifest_path": manifest_path,
        "status": status,
    }


def main() -> None:
    """CLI entrypoint для щоденного Analyzer run."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Запуск Analyzer pipeline на одному daily feed CSV."
    )
    parser.add_argument(
        "input_path",
        help="Шлях до raw feed CSV файлу (YYYY-MM-DD.csv)",
    )
    parser.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help=f"Кореневий каталог для run directories (дефолт: {DEFAULT_RUNS_ROOT})",
    )
    args = parser.parse_args()

    try:
        result = run_daily(args.input_path, args.runs_root)
        print(f"✅ Run completed: {result['run_id']}")
        print(f"   Directory: {result['run_dir']}")
        print(f"   Manifest: {result['manifest_path']}")
        print(f"   Status: {result['status']}")
    except Exception as exc:
        print(f"❌ Run failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
