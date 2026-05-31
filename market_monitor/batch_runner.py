from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from market_monitor.feed_adapter import FeedContractError, load_feed
from market_monitor.outputs import write_outputs
from market_monitor.research_summary import (
    ResearchSummaryResult,
    build_post_sweep_research_summary,
)


MANIFEST_COLUMNS = [
    "date",
    "feed_file",
    "status",
    "reason",
    "output_dir",
    "registry_in",
    "registry_out",
    "input_rows",
    "data_quality_summary",
    "structure_levels_count",
    "liquidity_zones_count",
    "registry_zones_count",
    "event_count",
    "unresolved_sweep_count",
    "post_sweep_observation_count",
    "complete_observation_count",
    "incomplete_observation_count",
]

PROCESSED = "PROCESSED"
SKIPPED = "SKIPPED"
FAILED = "FAILED"

BATCH_BOUNDARY_STATEMENT = (
    "This batch research summary is descriptive only. It does not classify "
    "rejected/accepted sweeps, does not generate trading signals, does not "
    "define entries/exits, does not calculate PnL, and does not trigger "
    "Backtester or Executor behavior."
)


class BatchResearchError(RuntimeError):
    """Raised when a batch research run cannot complete as requested."""


@dataclass(frozen=True)
class BatchRunResult:
    output_dir: Path
    manifest_path: Path
    summary_path: Path
    research_summary: ResearchSummaryResult
    daily_output_dirs: tuple[Path, ...]
    processed_days: int
    skipped_days: int
    failed_days: int
    unresolved_sweep_count: int
    post_sweep_observation_count: int


@dataclass(frozen=True)
class _DailyInput:
    day: date
    path: Path | None


def run_batch_research(
    feed_dir,
    output_dir,
    start_date=None,
    end_date=None,
    max_days=None,
    include_degraded=False,
    run_timestamp=None,
    skip_missing=False,
    fail_fast=True,
) -> BatchRunResult:
    feed_root = Path(feed_dir)
    batch_root = Path(output_dir)
    run_ts = run_timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    start = _parse_date(start_date, "start_date") if start_date else None
    end = _parse_date(end_date, "end_date") if end_date else None
    if start and end and start > end:
        raise BatchResearchError("start_date must be <= end_date")
    if max_days is not None and int(max_days) < 1:
        raise BatchResearchError("max_days must be >= 1")

    batch_root.mkdir(parents=True, exist_ok=True)
    daily_root = batch_root / "daily"
    research_dir = batch_root / "research_summary"
    manifest_path = batch_root / "batch_manifest.csv"
    summary_path = batch_root / "batch_summary.md"

    considered = _considered_daily_inputs(
        feed_root=feed_root,
        start=start,
        end=end,
        max_days=max_days,
        skip_missing=skip_missing,
    )
    if not considered:
        _write_empty_artifacts(
            manifest_path=manifest_path,
            summary_path=summary_path,
            research_dir=research_dir,
            run_timestamp=run_ts,
            feed_dir=feed_root,
            output_dir=batch_root,
            start=start,
            end=end,
            max_days=max_days,
            include_degraded=include_degraded,
        )
        raise BatchResearchError("No daily feed CSV files found for batch research")

    manifest_rows: list[dict[str, object]] = []
    processed_dirs: list[Path] = []
    previous_registry_out: Path | None = None
    first_failure: str | None = None

    for item in considered:
        if item.path is None:
            row = _manifest_row(item.day, None, FAILED, "NO_FILE")
            manifest_rows.append(row)
            first_failure = first_failure or f"No feed file found for {item.day.isoformat()}"
            if fail_fast:
                break
            continue

        daily_output = daily_root / item.day.isoformat()
        registry_out = daily_output / "liquidity_zone_registry.csv"
        registry_in = previous_registry_out
        try:
            feed = load_feed(item.path)
            quality_summary = _quality_summary(feed)
            has_degraded = "RECOVERED_DEGRADED" in set(feed["DataQuality"].astype(str))
            if has_degraded and not include_degraded:
                manifest_rows.append(
                    _manifest_row(
                        item.day,
                        item.path,
                        SKIPPED,
                        "DEGRADED_DATA_EXCLUDED",
                        input_rows=len(feed),
                        data_quality_summary=quality_summary,
                    )
                )
                continue

            frames = write_outputs(
                feed,
                daily_output,
                run_timestamp=run_ts,
                input_files=[item.path.name],
                registry_in_path=registry_in,
                registry_out_path=registry_out,
            )
            processed_dirs.append(daily_output)
            previous_registry_out = registry_out
            manifest_rows.append(
                _processed_manifest_row(
                    day=item.day,
                    feed_file=item.path,
                    daily_output=daily_output,
                    registry_in=registry_in,
                    registry_out=registry_out,
                    feed=feed,
                    frames=frames,
                    batch_root=batch_root,
                )
            )
        except (FeedContractError, FileNotFoundError, OSError, ValueError) as exc:
            manifest_rows.append(
                _manifest_row(
                    item.day,
                    item.path,
                    FAILED,
                    "RUN_ERROR",
                    output_dir=_relative_output(daily_output, batch_root),
                    registry_in=_relative_output(registry_in, batch_root),
                    registry_out=_relative_output(registry_out, batch_root),
                )
            )
            first_failure = first_failure or f"Batch day {item.day.isoformat()} failed: {exc}"
            if fail_fast:
                break

    manifest = pd.DataFrame(manifest_rows, columns=MANIFEST_COLUMNS)
    manifest.to_csv(manifest_path, index=False)
    research_result = build_post_sweep_research_summary(
        processed_dirs,
        research_dir,
        run_timestamp=run_ts,
    )
    _write_batch_summary(
        summary_path=summary_path,
        manifest=manifest,
        research_result=research_result,
        run_timestamp=run_ts,
        feed_dir=feed_root,
        output_dir=batch_root,
        start=start,
        end=end,
        max_days=max_days,
        include_degraded=include_degraded,
    )

    result = _result_from_artifacts(
        output_dir=batch_root,
        manifest_path=manifest_path,
        summary_path=summary_path,
        research_summary=research_result,
        daily_output_dirs=processed_dirs,
        manifest=manifest,
    )
    if first_failure and fail_fast:
        raise BatchResearchError(first_failure)
    if result.processed_days == 0:
        raise BatchResearchError("Batch research produced zero processed daily outputs")
    return result


def _considered_daily_inputs(
    *,
    feed_root: Path,
    start: date | None,
    end: date | None,
    max_days,
    skip_missing: bool,
) -> list[_DailyInput]:
    files = _discover_daily_files(feed_root)
    if start or end:
        lower = start or min(files) if files else start
        upper = end or max(files) if files else end
        if lower is None or upper is None:
            considered: list[_DailyInput] = []
        elif skip_missing:
            considered = [
                _DailyInput(day, files[day])
                for day in sorted(files)
                if lower <= day <= upper
            ]
        else:
            considered = [
                _DailyInput(day, files.get(day))
                for day in _date_range(lower, upper)
            ]
    else:
        considered = [_DailyInput(day, files[day]) for day in sorted(files)]
    if max_days is not None:
        considered = considered[: int(max_days)]
    return considered


def _discover_daily_files(feed_root: Path) -> dict[date, Path]:
    if not feed_root.exists():
        return {}
    files: dict[date, Path] = {}
    for path in feed_root.iterdir():
        if not path.is_file() or path.suffix.lower() != ".csv":
            continue
        parsed = _date_from_filename(path)
        if parsed is not None:
            files[parsed] = path
    return dict(sorted(files.items()))


def _date_from_filename(path: Path) -> date | None:
    try:
        return datetime.strptime(path.stem, "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_range(start: date, end: date) -> list[date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _parse_date(value, name: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise BatchResearchError(f"{name} must be YYYY-MM-DD") from exc


def _processed_manifest_row(
    *,
    day: date,
    feed_file: Path,
    daily_output: Path,
    registry_in: Path | None,
    registry_out: Path,
    feed: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    batch_root: Path,
) -> dict[str, object]:
    event_log = frames["event_log.csv"]
    observations = frames["post_sweep_observation.csv"]
    complete = _complete_observation_count(observations)
    return _manifest_row(
        day,
        feed_file,
        PROCESSED,
        "OK",
        output_dir=_relative_output(daily_output, batch_root),
        registry_in=_relative_output(registry_in, batch_root),
        registry_out=_relative_output(registry_out, batch_root),
        input_rows=len(feed),
        data_quality_summary=_quality_summary(feed),
        structure_levels_count=len(frames["structure_levels.csv"]),
        liquidity_zones_count=len(frames["liquidity_map.csv"]),
        registry_zones_count=len(frames["liquidity_zone_registry.csv"]),
        event_count=len(event_log),
        unresolved_sweep_count=int(
            (event_log["event_type"] == "LIQUIDITY_SWEEP_UNRESOLVED").sum()
        )
        if not event_log.empty
        else 0,
        post_sweep_observation_count=len(observations),
        complete_observation_count=complete,
        incomplete_observation_count=len(observations) - complete,
    )


def _manifest_row(
    day: date,
    feed_file: Path | None,
    status: str,
    reason: str,
    *,
    output_dir: str = "",
    registry_in: str = "",
    registry_out: str = "",
    input_rows: int | str = "",
    data_quality_summary: str = "",
    structure_levels_count: int | str = "",
    liquidity_zones_count: int | str = "",
    registry_zones_count: int | str = "",
    event_count: int | str = "",
    unresolved_sweep_count: int | str = "",
    post_sweep_observation_count: int | str = "",
    complete_observation_count: int | str = "",
    incomplete_observation_count: int | str = "",
) -> dict[str, object]:
    return {
        "date": day.isoformat(),
        "feed_file": _relative_path(feed_file),
        "status": status,
        "reason": reason,
        "output_dir": output_dir,
        "registry_in": registry_in,
        "registry_out": registry_out,
        "input_rows": input_rows,
        "data_quality_summary": data_quality_summary,
        "structure_levels_count": structure_levels_count,
        "liquidity_zones_count": liquidity_zones_count,
        "registry_zones_count": registry_zones_count,
        "event_count": event_count,
        "unresolved_sweep_count": unresolved_sweep_count,
        "post_sweep_observation_count": post_sweep_observation_count,
        "complete_observation_count": complete_observation_count,
        "incomplete_observation_count": incomplete_observation_count,
    }


def _write_empty_artifacts(
    *,
    manifest_path: Path,
    summary_path: Path,
    research_dir: Path,
    run_timestamp: str,
    feed_dir: Path,
    output_dir: Path,
    start: date | None,
    end: date | None,
    max_days,
    include_degraded: bool,
) -> None:
    manifest = pd.DataFrame(columns=MANIFEST_COLUMNS)
    manifest.to_csv(manifest_path, index=False)
    research_result = build_post_sweep_research_summary(
        [],
        research_dir,
        run_timestamp=run_timestamp,
    )
    _write_batch_summary(
        summary_path=summary_path,
        manifest=manifest,
        research_result=research_result,
        run_timestamp=run_timestamp,
        feed_dir=feed_dir,
        output_dir=output_dir,
        start=start,
        end=end,
        max_days=max_days,
        include_degraded=include_degraded,
    )


def _write_batch_summary(
    *,
    summary_path: Path,
    manifest: pd.DataFrame,
    research_result: ResearchSummaryResult,
    run_timestamp: str,
    feed_dir: Path,
    output_dir: Path,
    start: date | None,
    end: date | None,
    max_days,
    include_degraded: bool,
) -> None:
    processed = _status_count(manifest, PROCESSED)
    skipped = _status_count(manifest, SKIPPED)
    failed = _status_count(manifest, FAILED)
    processed_rows = manifest[manifest["status"] == PROCESSED].copy()
    degraded_processed = int(
        processed_rows["data_quality_summary"].astype(str).str.contains("RECOVERED_DEGRADED").sum()
    )
    degraded_skipped = int((manifest["reason"] == "DEGRADED_DATA_EXCLUDED").sum())
    rows_processed = _sum_column(processed_rows, "input_rows")
    final_registry_zones = _last_numeric(processed_rows, "registry_zones_count")
    score_instrumentation = _score_instrumentation_available(research_result)
    lines = [
        "# Market Monitor Batch Research Summary",
        "",
        "## Run Metadata",
        "",
        f"- Run timestamp: {run_timestamp}",
        f"- Feed dir: {_relative_path(feed_dir)}",
        f"- Output dir: {_relative_path(output_dir)}",
        f"- Start date: {start.isoformat() if start else ''}",
        f"- End date: {end.isoformat() if end else ''}",
        f"- Max days: {max_days if max_days is not None else ''}",
        f"- Include degraded: {str(bool(include_degraded)).lower()}",
        f"- Score instrumentation available: {score_instrumentation}",
        f"- Processed days: {processed}",
        f"- Skipped days: {skipped}",
        f"- Failed days: {failed}",
        "",
        "## Data Quality",
        "",
        f"- RAW days: {int(processed_rows['data_quality_summary'].astype(str).str.startswith('RAW').sum()) if not processed_rows.empty else 0}",
        f"- Degraded days processed: {degraded_processed}",
        f"- Degraded days skipped: {degraded_skipped}",
        f"- Rows processed: {rows_processed}",
        "",
        "## Daily Output Counts",
        "",
        f"- Total structure levels: {_sum_column(processed_rows, 'structure_levels_count')}",
        f"- Total liquidity zones: {_sum_column(processed_rows, 'liquidity_zones_count')}",
        f"- Final registry zones: {final_registry_zones}",
        f"- Total lifecycle events: {_sum_column(processed_rows, 'event_count')}",
        f"- Unresolved sweep candidates: {_sum_column(processed_rows, 'unresolved_sweep_count')}",
        f"- Post-sweep observations: {_sum_column(processed_rows, 'post_sweep_observation_count')}",
        f"- Complete observations: {_sum_column(processed_rows, 'complete_observation_count')}",
        f"- Incomplete observations: {_sum_column(processed_rows, 'incomplete_observation_count')}",
        "",
        "## Research Summary Link",
        "",
        f"- {(_relative_output(research_result.markdown_path, output_dir))}",
        "",
        "## Boundary Statement",
        "",
        BATCH_BOUNDARY_STATEMENT,
        "",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def _result_from_artifacts(
    *,
    output_dir: Path,
    manifest_path: Path,
    summary_path: Path,
    research_summary: ResearchSummaryResult,
    daily_output_dirs: list[Path],
    manifest: pd.DataFrame,
) -> BatchRunResult:
    return BatchRunResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        summary_path=summary_path,
        research_summary=research_summary,
        daily_output_dirs=tuple(daily_output_dirs),
        processed_days=_status_count(manifest, PROCESSED),
        skipped_days=_status_count(manifest, SKIPPED),
        failed_days=_status_count(manifest, FAILED),
        unresolved_sweep_count=_sum_column(manifest, "unresolved_sweep_count"),
        post_sweep_observation_count=_sum_column(manifest, "post_sweep_observation_count"),
    )


def _quality_summary(feed: pd.DataFrame) -> str:
    if feed.empty:
        return "none"
    counts = feed["DataQuality"].value_counts().sort_index()
    return ", ".join(f"{name}={int(count)}" for name, count in counts.items())


def _complete_observation_count(observations: pd.DataFrame) -> int:
    if observations.empty or "observation_complete" not in observations.columns:
        return 0
    return int(observations["observation_complete"].astype(str).str.lower().eq("true").sum())


def _status_count(manifest: pd.DataFrame, status: str) -> int:
    if manifest.empty:
        return 0
    return int((manifest["status"] == status).sum())


def _sum_column(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def _last_numeric(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return 0
    return int(values.iloc[-1])


def _score_instrumentation_available(research_result: ResearchSummaryResult) -> str:
    try:
        columns = pd.read_csv(research_result.row_summary_path, nrows=0).columns
    except OSError:
        return "no"
    return "yes" if "score_components_json" in columns else "no"


def _relative_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = Path(path)
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _relative_output(path: Path | None, batch_root: Path) -> str:
    if path is None:
        return ""
    try:
        return Path(path).relative_to(batch_root).as_posix()
    except ValueError:
        return _relative_path(Path(path))
