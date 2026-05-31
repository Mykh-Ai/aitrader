from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROW_SUMMARY_COLUMNS = [
    "source_run_dir",
    "observation_id",
    "source_event_id",
    "source_event_timestamp",
    "zone_id",
    "side",
    "zone_type",
    "zone_price_lower",
    "zone_price_upper",
    "zone_price_mid",
    "observation_bars_expected",
    "observation_bars_available",
    "observation_complete",
    "max_high_after_event",
    "min_low_after_event",
    "close_at_window_end",
    "max_excursion_beyond_zone",
    "max_return_inside_zone",
    "bars_inside_zone",
    "bars_above_zone",
    "bars_below_zone",
    "first_return_inside_at",
    "first_close_inside_at",
    "first_close_beyond_at",
    "net_close_change_abs",
    "net_close_change_pct",
    "post_volume_sum",
    "post_buy_qty_sum",
    "post_sell_qty_sum",
    "post_delta_sum",
    "post_delta_pct",
    "post_trades_sum",
    "post_oi_change",
    "post_max_volume_zscore",
    "post_max_abs_delta_zscore",
    "data_quality",
]

GROUP_SUMMARY_COLUMNS = [
    "group_type",
    "group_value",
    "observation_count",
    "complete_count",
    "incomplete_count",
    "avg_max_excursion_beyond_zone",
    "median_max_excursion_beyond_zone",
    "avg_max_return_inside_zone",
    "median_max_return_inside_zone",
    "avg_bars_inside_zone",
    "avg_bars_above_zone",
    "avg_bars_below_zone",
    "avg_net_close_change_pct",
    "avg_post_delta_pct",
    "avg_post_oi_change",
    "avg_post_max_volume_zscore",
    "avg_post_max_abs_delta_zscore",
]

BOUNDARY_STATEMENT = (
    "This research summary is descriptive only. It does not classify rejected/accepted "
    "sweeps, does not generate trading signals, does not define entries/exits, "
    "does not calculate PnL, and does not trigger Backtester or Executor behavior."
)


@dataclass(frozen=True)
class ResearchSummaryResult:
    markdown_path: Path
    row_summary_path: Path
    group_summary_path: Path
    observation_count: int
    complete_count: int
    incomplete_count: int
    event_counts_by_type: dict[str, int]
    warnings: tuple[str, ...]


def build_post_sweep_research_summary(
    input_dirs,
    output_dir,
    run_timestamp: str | None = None,
) -> ResearchSummaryResult:
    input_paths = _input_paths(input_dirs)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    loaded = [_load_run_dir(path) for path in input_paths]
    observations = _combined_observations(loaded)
    event_counts = _combined_event_counts(loaded)
    group_summary = _group_summary(observations)
    warnings = tuple(warning for item in loaded for warning in item["warnings"])

    row_summary = observations[ROW_SUMMARY_COLUMNS]
    row_path = output_path / "post_sweep_research_summary.csv"
    group_path = output_path / "post_sweep_group_summary.csv"
    markdown_path = output_path / "post_sweep_research_summary.md"
    row_summary.to_csv(row_path, index=False)
    group_summary.to_csv(group_path, index=False)
    markdown_path.write_text(
        _markdown_summary(
            input_paths=input_paths,
            observations=observations,
            group_summary=group_summary,
            event_counts=event_counts,
            warnings=warnings,
            run_timestamp=run_timestamp or "",
        ),
        encoding="utf-8",
    )

    complete = _complete_mask(observations)
    return ResearchSummaryResult(
        markdown_path=markdown_path,
        row_summary_path=row_path,
        group_summary_path=group_path,
        observation_count=len(observations),
        complete_count=int(complete.sum()),
        incomplete_count=int((~complete).sum()) if len(observations) else 0,
        event_counts_by_type=event_counts,
        warnings=warnings,
    )


def _input_paths(input_dirs) -> list[Path]:
    paths = [Path(path) for path in input_dirs]
    return sorted(paths, key=lambda path: str(path))


def _load_run_dir(path: Path) -> dict[str, object]:
    warnings: list[str] = []
    observation_path = path / "post_sweep_observation.csv"
    if observation_path.exists():
        observations = pd.read_csv(observation_path)
    else:
        observations = pd.DataFrame(columns=ROW_SUMMARY_COLUMNS)
        warnings.append(f"Missing post_sweep_observation.csv in {path}")

    if not observations.empty:
        observations = observations.copy()
        observations["source_run_dir"] = str(path)
        observations = _enrich_from_event_log(observations, path / "event_log.csv")
        observations = _normalize_observations(observations)
    else:
        observations = pd.DataFrame(columns=ROW_SUMMARY_COLUMNS + ["confidence_tier", "source_timeframes"])

    event_counts = _event_counts(path / "event_log.csv")
    return {
        "observations": observations,
        "event_counts": event_counts,
        "warnings": warnings,
    }


def _combined_observations(loaded: list[dict[str, object]]) -> pd.DataFrame:
    frames = [item["observations"] for item in loaded if not item["observations"].empty]
    if not frames:
        return pd.DataFrame(columns=ROW_SUMMARY_COLUMNS + ["confidence_tier", "source_timeframes"])
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(
        ["source_run_dir", "source_event_timestamp", "zone_id", "observation_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    return out


def _combined_event_counts(loaded: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in loaded:
        for event_type, count in item["event_counts"].items():
            counts[event_type] = counts.get(event_type, 0) + int(count)
    return dict(sorted(counts.items()))


def _normalize_observations(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in ROW_SUMMARY_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    for column in _numeric_columns():
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if "confidence_tier" not in out.columns:
        out["confidence_tier"] = ""
    if "source_timeframes" not in out.columns:
        out["source_timeframes"] = ""
    return out[ROW_SUMMARY_COLUMNS + ["confidence_tier", "source_timeframes"]]


def _enrich_from_event_log(observations: pd.DataFrame, event_log_path: Path) -> pd.DataFrame:
    observations = observations.copy()
    observations["confidence_tier"] = ""
    observations["source_timeframes"] = ""
    if not event_log_path.exists():
        return observations
    event_log = pd.read_csv(event_log_path)
    if event_log.empty or "event_id" not in event_log.columns:
        return observations
    evidence_by_event = {}
    for _, row in event_log.iterrows():
        try:
            evidence = json.loads(str(row.get("evidence_json", "{}")))
        except json.JSONDecodeError:
            evidence = {}
        evidence_by_event[str(row["event_id"])] = evidence
    observations["confidence_tier"] = observations["source_event_id"].map(
        lambda event_id: str(evidence_by_event.get(str(event_id), {}).get("confidence_tier", ""))
    )
    observations["source_timeframes"] = observations["source_event_id"].map(
        lambda event_id: str(evidence_by_event.get(str(event_id), {}).get("source_timeframes", ""))
    )
    return observations


def _event_counts(event_log_path: Path) -> dict[str, int]:
    if not event_log_path.exists():
        return {}
    event_log = pd.read_csv(event_log_path)
    if event_log.empty or "event_type" not in event_log.columns:
        return {}
    counts = event_log["event_type"].value_counts().sort_index()
    return {str(name): int(count) for name, count in counts.items()}


def _group_summary(observations: pd.DataFrame) -> pd.DataFrame:
    rows = [_group_row("ALL", "ALL", observations)]
    if not observations.empty:
        for column, group_type in [
            ("side", "side"),
            ("data_quality", "data_quality"),
            ("observation_complete", "observation_complete"),
            ("zone_type", "zone_type"),
            ("confidence_tier", "confidence_tier"),
            ("source_timeframes", "source_timeframes"),
        ]:
            if column in observations.columns:
                for value, group in observations.groupby(column, sort=True, dropna=False):
                    if str(value):
                        rows.append(_group_row(group_type, str(value), group))
    return pd.DataFrame(rows, columns=GROUP_SUMMARY_COLUMNS)


def _group_row(group_type: str, group_value: str, group: pd.DataFrame) -> dict[str, object]:
    complete = _complete_mask(group)
    return {
        "group_type": group_type,
        "group_value": group_value,
        "observation_count": len(group),
        "complete_count": int(complete.sum()) if len(group) else 0,
        "incomplete_count": int((~complete).sum()) if len(group) else 0,
        "avg_max_excursion_beyond_zone": _mean(group, "max_excursion_beyond_zone"),
        "median_max_excursion_beyond_zone": _median(group, "max_excursion_beyond_zone"),
        "avg_max_return_inside_zone": _mean(group, "max_return_inside_zone"),
        "median_max_return_inside_zone": _median(group, "max_return_inside_zone"),
        "avg_bars_inside_zone": _mean(group, "bars_inside_zone"),
        "avg_bars_above_zone": _mean(group, "bars_above_zone"),
        "avg_bars_below_zone": _mean(group, "bars_below_zone"),
        "avg_net_close_change_pct": _mean(group, "net_close_change_pct"),
        "avg_post_delta_pct": _mean(group, "post_delta_pct"),
        "avg_post_oi_change": _mean(group, "post_oi_change"),
        "avg_post_max_volume_zscore": _mean(group, "post_max_volume_zscore"),
        "avg_post_max_abs_delta_zscore": _mean(group, "post_max_abs_delta_zscore"),
    }


def _markdown_summary(
    *,
    input_paths: list[Path],
    observations: pd.DataFrame,
    group_summary: pd.DataFrame,
    event_counts: dict[str, int],
    warnings: tuple[str, ...],
    run_timestamp: str,
) -> str:
    complete = _complete_mask(observations)
    observation_count = len(observations)
    lines = [
        "# Post-Sweep Observation Research Summary",
        "",
        "## Run Metadata",
        "",
        f"- Run timestamp: {run_timestamp}",
        f"- Input directories: {', '.join(str(path) for path in input_paths)}",
        f"- Observation rows loaded: {observation_count}",
        f"- Complete observations: {int(complete.sum()) if observation_count else 0}",
        f"- Incomplete observations: {int((~complete).sum()) if observation_count else 0}",
        "",
        "## Event Context",
        "",
        f"- Event counts by type: {_format_counts(event_counts)}",
        f"- Unresolved sweep count: {event_counts.get('LIQUIDITY_SWEEP_UNRESOLVED', 0)}",
        "",
        "## Observation Overview",
        "",
        f"- observation_count: {observation_count}",
        f"- by side: {_counts_for(observations, 'side')}",
        f"- by data_quality: {_counts_for(observations, 'data_quality')}",
        f"- by observation_complete: {_counts_for(observations, 'observation_complete')}",
        f"- by zone_type: {_counts_for(observations, 'zone_type')}",
        f"- by confidence_tier: {_counts_for(observations, 'confidence_tier')}",
        "",
        "## Descriptive Metrics",
        "",
        f"- average max_excursion_beyond_zone: {_fmt(_mean(observations, 'max_excursion_beyond_zone'))}",
        f"- median max_excursion_beyond_zone: {_fmt(_median(observations, 'max_excursion_beyond_zone'))}",
        f"- average max_return_inside_zone: {_fmt(_mean(observations, 'max_return_inside_zone'))}",
        f"- median max_return_inside_zone: {_fmt(_median(observations, 'max_return_inside_zone'))}",
        f"- average bars_inside_zone: {_fmt(_mean(observations, 'bars_inside_zone'))}",
        f"- average bars_above_zone: {_fmt(_mean(observations, 'bars_above_zone'))}",
        f"- average bars_below_zone: {_fmt(_mean(observations, 'bars_below_zone'))}",
        f"- average net_close_change_pct: {_fmt(_mean(observations, 'net_close_change_pct'))}",
        f"- average post_delta_pct: {_fmt(_mean(observations, 'post_delta_pct'))}",
        f"- average post_oi_change: {_fmt(_mean(observations, 'post_oi_change'))}",
        "",
        "## Data Quality Caveats",
        "",
        f"- Degraded rows present: {'yes' if _has_degraded(observations) else 'no'}",
    ]
    if observation_count < 30:
        lines.append("- Sample size is below 30 observations. This summary is insufficient for strategy rules or validation.")
    if observation_count < 100:
        lines.append("- Sample size is below 100 observations. Treat descriptive metrics as preliminary.")
    for warning in warnings:
        lines.append(f"- {warning}")
    lines.extend(
        [
            "",
            "## Boundary Statement",
            "",
            BOUNDARY_STATEMENT,
            "",
        ]
    )
    return "\n".join(lines)


def _complete_mask(frame: pd.DataFrame) -> pd.Series:
    if frame.empty or "observation_complete" not in frame.columns:
        return pd.Series(dtype=bool)
    return frame["observation_complete"].astype(str).str.lower() == "true"


def _numeric_columns() -> list[str]:
    return [
        "zone_price_lower",
        "zone_price_upper",
        "zone_price_mid",
        "observation_bars_expected",
        "observation_bars_available",
        "max_high_after_event",
        "min_low_after_event",
        "close_at_window_end",
        "max_excursion_beyond_zone",
        "max_return_inside_zone",
        "bars_inside_zone",
        "bars_above_zone",
        "bars_below_zone",
        "net_close_change_abs",
        "net_close_change_pct",
        "post_volume_sum",
        "post_buy_qty_sum",
        "post_sell_qty_sum",
        "post_delta_sum",
        "post_delta_pct",
        "post_trades_sum",
        "post_oi_change",
        "post_max_volume_zscore",
        "post_max_abs_delta_zscore",
    ]


def _mean(frame: pd.DataFrame, column: str):
    if frame.empty or column not in frame.columns:
        return ""
    value = pd.to_numeric(frame[column], errors="coerce").mean()
    return "" if pd.isna(value) else float(value)


def _median(frame: pd.DataFrame, column: str):
    if frame.empty or column not in frame.columns:
        return ""
    value = pd.to_numeric(frame[column], errors="coerce").median()
    return "" if pd.isna(value) else float(value)


def _counts_for(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "none"
    counts = frame[column].astype(str).value_counts().sort_index()
    counts = counts[counts.index != ""]
    if counts.empty:
        return "none"
    return ", ".join(f"{name}={int(count)}" for name, count in counts.items())


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


def _has_degraded(frame: pd.DataFrame) -> bool:
    return not frame.empty and bool((frame["data_quality"] == "RECOVERED_DEGRADED").any())


def _fmt(value) -> str:
    if value == "":
        return ""
    return f"{float(value):.8g}"
