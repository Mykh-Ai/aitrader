from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


STRUCTURAL_STOP_RESOLVER_VERSION = "SHI_RESET_38H_STRUCTURAL_SWING_STOP_RESOLVER_V0"

STRUCTURAL_STOP_CANDIDATES_CSV = "structural_stop_reference_candidates.csv"
STRUCTURAL_STOP_SUMMARY_MD = "structural_stop_resolver_summary.md"
STRUCTURAL_STOP_MANIFEST_JSON = "structural_stop_resolver_manifest.json"

STRUCTURAL_STOP_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "sequence_role",
    "actual_setup_price",
    "tradable_entry_anchor",
    "setup_reference_level",
    "target_reference",
    "original_stop_reference",
    "source_window_high",
    "source_window_low",
    "source_window_stop_reference",
    "local_swing_high_candidate",
    "local_swing_low_candidate",
    "local_swing_stop_reference",
    "structural_zone_lower",
    "structural_zone_upper",
    "structural_zone_role",
    "structural_zone_stop_reference",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "stop_distance_usd",
    "target_distance_usd",
    "potential_r_from_selected_stop",
    "stop_selection_reason",
    "evidence_summary",
]


class StructuralStopResolverError(RuntimeError):
    """Raised when structural stop reference resolution cannot complete."""


@dataclass(frozen=True)
class StructuralStopResolverResult:
    output_dir: Path
    candidates_path: Path
    summary_path: Path
    manifest_path: Path
    row_count: int


def run_structural_stop_resolver(
    *,
    live_like_replay_path: str | Path,
    focus_alignment_path: str | Path,
    manual_verdicts_path: str | Path,
    output_dir: str | Path,
) -> StructuralStopResolverResult:
    replay = _read_csv(Path(live_like_replay_path))
    focus = _read_csv(Path(focus_alignment_path))
    verdicts = _read_csv(Path(manual_verdicts_path))
    if replay.empty:
        raise StructuralStopResolverError("live-like replay rows are required")
    if focus.empty:
        raise StructuralStopResolverError("focus alignment rows are required")
    if verdicts.empty:
        raise StructuralStopResolverError("38C manual verdict rows are required")

    rows = [_resolve_focus_setup(focus_row=row, replay=replay, verdicts=verdicts) for _, row in focus.iterrows()]
    candidates = pd.DataFrame(rows, columns=STRUCTURAL_STOP_COLUMNS)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    candidates_path = output_root / STRUCTURAL_STOP_CANDIDATES_CSV
    summary_path = output_root / STRUCTURAL_STOP_SUMMARY_MD
    manifest_path = output_root / STRUCTURAL_STOP_MANIFEST_JSON

    candidates.to_csv(candidates_path, index=False)
    summary_path.write_text(_summary_text(candidates), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "structural_stop_resolver_version": STRUCTURAL_STOP_RESOLVER_VERSION,
                "research_only": True,
                "sample_expanded": False,
                "uses_existing_38g_focus_setups_only": True,
                "changes_setup_detection_logic": False,
                "changes_setup_builder": False,
                "uses_backtester": False,
                "uses_executor": False,
                "uses_orders": False,
                "uses_entries_exits": False,
                "uses_pnl": False,
                "uses_position_sizing": False,
                "live_readiness_claim": False,
                "strategy_promotion": False,
                "live_like_replay_path": str(live_like_replay_path),
                "focus_alignment_path": str(focus_alignment_path),
                "manual_verdicts_path": str(manual_verdicts_path),
                "output_dir": str(output_root),
                "row_count": int(len(candidates)),
                "outputs": {
                    "structural_stop_reference_candidates_csv": str(candidates_path),
                    "summary_md": str(summary_path),
                    "manifest_json": str(manifest_path),
                },
                "repo_commit": _repo_commit(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return StructuralStopResolverResult(output_root, candidates_path, summary_path, manifest_path, int(len(candidates)))


def _resolve_focus_setup(*, focus_row: pd.Series, replay: pd.DataFrame, verdicts: pd.DataFrame) -> dict[str, object]:
    formed_at = _cell(focus_row.get("focus_timestamp"))
    setup_type = _cell(focus_row.get("expected_setup_type"))
    live = replay[(replay["replay_timestamp"].astype(str) == formed_at) & (replay["setup_type"].astype(str) == setup_type)]
    if live.empty:
        raise StructuralStopResolverError(f"missing live-like row for {formed_at} {setup_type}")
    live_row = live.iloc[0]

    verdict = verdicts[(verdicts["setup_formed_at"].astype(str) == formed_at) & (verdicts["setup_type"].astype(str) == setup_type)]
    verdict_row = verdict.iloc[0] if not verdict.empty else pd.Series(dtype=object)
    direction = _cell(verdict_row.get("direction_context")).upper()
    if not direction:
        direction = "DOWN" if "_DOWN_" in setup_type else "UP" if "_UP_" in setup_type else ""

    entry = _float_value(live_row.get("tradable_entry_anchor"))
    target_reference = _cell(live_row.get("target_reference"))
    original_stop = _float_value(live_row.get("stop_reference"))
    source_high = _float_value(live_row.get("source_window_high"))
    source_low = _float_value(live_row.get("source_window_low"))
    local_high = _float_value(live_row.get("local_swing_high_candidate"))
    local_low = _float_value(live_row.get("local_swing_low_candidate"))

    source_stop = _directional_stop(direction=direction, high=source_high, low=source_low)
    local_stop = _directional_stop(direction=direction, high=local_high, low=local_low)
    structural = _manual_structural_zone(formed_at=formed_at, direction=direction, entry=entry)
    selected_stop, selected_type, reason = _select_research_stop(
        direction=direction,
        entry=entry,
        original_stop=original_stop,
        source_stop=source_stop,
        local_stop=local_stop,
        structural_stop=structural["stop"],
        structural_role=structural["role"],
    )
    stop_distance = abs(selected_stop - entry) if not pd.isna(selected_stop) and not pd.isna(entry) else float("nan")
    target_distance = _target_distance(direction=direction, entry=entry, target_reference=target_reference)
    potential_r = target_distance / stop_distance if stop_distance and not pd.isna(stop_distance) and not pd.isna(target_distance) else float("nan")

    return {
        "setup_id": _cell(verdict_row.get("setup_id")),
        "setup_formed_at": formed_at,
        "setup_type": setup_type,
        "direction_context": direction,
        "sequence_role": _cell(verdict_row.get("sequence_role")),
        "actual_setup_price": _round(live_row.get("actual_setup_price")),
        "tradable_entry_anchor": _round(entry),
        "setup_reference_level": _round(live_row.get("setup_reference_level")),
        "target_reference": target_reference,
        "original_stop_reference": _round(original_stop),
        "source_window_high": _round(source_high),
        "source_window_low": _round(source_low),
        "source_window_stop_reference": _round(source_stop),
        "local_swing_high_candidate": _round(local_high),
        "local_swing_low_candidate": _round(local_low),
        "local_swing_stop_reference": _round(local_stop),
        "structural_zone_lower": _round(structural["lower"]),
        "structural_zone_upper": _round(structural["upper"]),
        "structural_zone_role": structural["role"],
        "structural_zone_stop_reference": _round(structural["stop"]),
        "selected_research_stop_reference": _round(selected_stop),
        "selected_research_stop_type": selected_type,
        "stop_distance_usd": _round(stop_distance),
        "target_distance_usd": _round(target_distance),
        "potential_r_from_selected_stop": _round(potential_r),
        "stop_selection_reason": reason,
        "evidence_summary": _evidence_summary(
            formed_at=formed_at,
            setup_type=setup_type,
            entry=entry,
            setup_reference=_float_value(live_row.get("setup_reference_level")),
            source_stop=source_stop,
            local_stop=local_stop,
            structural=structural,
        ),
    }


def _select_research_stop(
    *,
    direction: str,
    entry: float,
    original_stop: float,
    source_stop: float,
    local_stop: float,
    structural_stop: float,
    structural_role: str,
) -> tuple[float, str, str]:
    valid = {
        "original_invalidation_stop": _valid_stop(direction, entry, original_stop),
        "source_window_stop": _valid_stop(direction, entry, source_stop),
        "local_swing_stop": _valid_stop(direction, entry, local_stop),
        "structural_zone_stop": _valid_stop(direction, entry, structural_stop),
    }
    if structural_role and valid["structural_zone_stop"]:
        return (
            structural_stop,
            "structural_zone_stop",
            "selected manual structural support-resistance flip review zone; source-window high is context only",
        )
    if valid["local_swing_stop"]:
        return local_stop, "local_swing_stop", "selected broader local swing candidate over source-window high/low"
    if valid["source_window_stop"]:
        return source_stop, "source_window_stop", "selected source-window stop only because no broader structural/local candidate resolved"
    if valid["original_invalidation_stop"]:
        return original_stop, "original_invalidation_stop", "selected original invalidation because no other valid stop resolved"
    return float("nan"), "unresolved", "no valid stop candidate resolved"


def _manual_structural_zone(*, formed_at: str, direction: str, entry: float) -> dict[str, object]:
    if formed_at.startswith("2026-06-25T") and direction == "DOWN" and not pd.isna(entry) and entry < 62000:
        return {
            "lower": 62000.0,
            "upper": 62200.0,
            "role": "support_resistance_flip_review_zone",
            "stop": 62200.0,
        }
    return {"lower": float("nan"), "upper": float("nan"), "role": "", "stop": float("nan")}


def _directional_stop(*, direction: str, high: float, low: float) -> float:
    if direction == "DOWN":
        return high
    if direction == "UP":
        return low
    return float("nan")


def _valid_stop(direction: str, entry: float, stop: float) -> bool:
    if pd.isna(entry) or pd.isna(stop):
        return False
    if direction == "DOWN":
        return stop > entry
    if direction == "UP":
        return stop < entry
    return False


def _target_distance(*, direction: str, entry: float, target_reference: str) -> float:
    target = _parse_target_zone(target_reference)
    if target is None or pd.isna(entry):
        return float("nan")
    if direction == "DOWN":
        if target["upper"] <= entry:
            return entry - target["upper"]
        return target["lower"] - entry
    if direction == "UP":
        if target["lower"] >= entry:
            return target["lower"] - entry
        return entry - target["upper"]
    return float("nan")


def _parse_target_zone(value: str) -> dict[str, float] | None:
    parts = _cell(value).split(":")
    if len(parts) != 3 or "-" not in parts[2]:
        return None
    lower_text, upper_text = parts[2].split("-", 1)
    lower = _float_value(lower_text)
    upper = _float_value(upper_text)
    if pd.isna(lower) or pd.isna(upper):
        return None
    return {"lower": min(lower, upper), "upper": max(lower, upper)}


def _evidence_summary(
    *,
    formed_at: str,
    setup_type: str,
    entry: float,
    setup_reference: float,
    source_stop: float,
    local_stop: float,
    structural: dict[str, object],
) -> str:
    return (
        f"setup_formed_at={formed_at}; setup_type={setup_type}; actual_entry_anchor={_round(entry)}; "
        f"setup_reference_level={_round(setup_reference)}; setup_reference_is_not_entry=true; "
        f"source_window_stop={_round(source_stop)}; local_swing_stop={_round(local_stop)}; "
        f"structural_zone_role={structural['role']}; structural_zone_stop={_round(structural['stop'])}; "
        "research_only_stop_comparison=true"
    )


def _summary_text(candidates: pd.DataFrame) -> str:
    lines = [
        "# SHI RESET 38H Structural Swing Stop Resolver Summary",
        "",
        "Research-only stop reference comparison for existing 38G focus setups.",
        "",
        f"- Focus setup rows: {len(candidates)}",
        f"- Rows by selected_research_stop_type: {_counts_json(candidates, 'selected_research_stop_type')}",
        f"- Rows by setup_type: {_counts_json(candidates, 'setup_type')}",
        f"- Rows by sequence_role: {_counts_json(candidates, 'sequence_role')}",
        "",
        "## Required Conclusions",
        "",
        "- Setup detection was not changed.",
        "- Setup Builder rules were not changed.",
        "- Stop references are classified and compared only; no entries/exits, orders, PnL, position sizing, Backtester, Executor, live-readiness, or strategy promotion are introduced.",
        "- `setup_reference_level` remains a structural/reference level and is not treated as a tradable entry.",
        "- Source-window high/low are context candidates and are not automatically selected as structural swing stops.",
        "- For `2026-06-25T11:59:00Z`, the resolver compares original stop `61286.628`, source-window high `61395.3`, broader local swing high `61897.6`, and the manual `62000-62200` support-resistance flip review zone.",
        "",
    ]
    focus = candidates[candidates["setup_formed_at"] == "2026-06-25T11:59:00Z"]
    if not focus.empty:
        row = focus.iloc[0]
        lines.extend(
            [
                "## 2026-06-25T11:59Z Check",
                "",
                f"- actual_setup_price: {row['actual_setup_price']}",
                f"- tradable_entry_anchor: {row['tradable_entry_anchor']}",
                f"- setup_reference_level: {row['setup_reference_level']}",
                f"- source_window_high: {row['source_window_high']}",
                f"- local_swing_high_candidate: {row['local_swing_high_candidate']}",
                f"- structural_zone: {row['structural_zone_lower']} -> {row['structural_zone_upper']} `{row['structural_zone_role']}`",
                f"- selected_research_stop_reference: {row['selected_research_stop_reference']} `{row['selected_research_stop_type']}`",
                f"- potential_r_from_selected_stop: {row['potential_r_from_selected_stop']}",
                "",
            ]
        )
    return "\n".join(lines)


def _counts_json(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "{}"
    return json.dumps(frame[column].fillna("").astype(str).value_counts().to_dict(), sort_keys=True)


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _float_value(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if pd.notna(number) else default


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""
