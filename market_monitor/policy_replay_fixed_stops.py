from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd


POLICY_REPLAY_FIXED_STOPS_VERSION = "SHI_RESET_38I_POLICY_REPLAY_WITH_FIXED_ANCHORS_AND_STRUCTURAL_STOPS_V0"

POLICY_REPLAY_FIXED_RESULTS_CSV = "policy_replay_fixed_stop_results.csv"
POLICY_REPLAY_FIXED_SUMMARY_MD = "policy_replay_fixed_stop_summary.md"
POLICY_REPLAY_FIXED_MANIFEST_JSON = "policy_replay_fixed_stop_manifest.json"

SELECTED_STOP_TARGET_POLICY = "SELECTED_STOP_TARGET_POLICY"
TP1_BE_WITH_SELECTED_STOP_POLICY = "TP1_BE_WITH_SELECTED_STOP_POLICY"

RESULT_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "sequence_role",
    "research_action",
    "policy_name",
    "tradable_entry_anchor",
    "setup_reference_level",
    "setup_reference_used_as_entry",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "stop_distance_usd",
    "target_reference",
    "target_zone_lower",
    "target_zone_upper",
    "target_distance_usd",
    "potential_r_to_target",
    "tp1_r",
    "tp1_price",
    "target_touched",
    "target_touched_at",
    "selected_stop_touched",
    "selected_stop_touched_at",
    "tp1_touched",
    "tp1_touched_at",
    "be_hit_after_tp1",
    "first_event",
    "policy_outcome_label",
    "max_favorable_excursion_usd",
    "max_adverse_excursion_usd",
    "max_favorable_excursion_r",
    "max_adverse_excursion_r",
    "evidence_summary",
]


class PolicyReplayFixedStopsError(RuntimeError):
    """Raised when fixed-anchor structural-stop policy replay cannot complete."""


@dataclass(frozen=True)
class PolicyReplayFixedStopsResult:
    output_dir: Path
    results_path: Path
    summary_path: Path
    manifest_path: Path
    row_count: int


def run_policy_replay_fixed_stops(
    *,
    focus_alignment_path: str | Path,
    structural_stops_path: str | Path,
    manual_verdicts_path: str | Path,
    feed_dir: str | Path,
    output_dir: str | Path,
) -> PolicyReplayFixedStopsResult:
    focus = _read_csv(Path(focus_alignment_path))
    stops = _read_csv(Path(structural_stops_path))
    verdicts = _read_csv(Path(manual_verdicts_path))
    if focus.empty:
        raise PolicyReplayFixedStopsError("38G focus alignment rows are required")
    if stops.empty:
        raise PolicyReplayFixedStopsError("38H structural stop candidates are required")
    if verdicts.empty:
        raise PolicyReplayFixedStopsError("38C manual verdict rows are required")

    focus = focus[focus.get("alignment_verdict", "").astype(str) == "MATCH"].copy()
    if focus.empty:
        raise PolicyReplayFixedStopsError("no matched focus setup rows found")

    merged = _merge_focus_rows(focus=focus, stops=stops, verdicts=verdicts)
    rows: list[dict[str, object]] = []
    feed_root = Path(feed_dir)
    for _, setup in merged.iterrows():
        rows.extend(_replay_setup(setup=setup, feed_root=feed_root))

    results = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    if not results.empty and set(results["setup_reference_used_as_entry"].astype(str).str.lower()) != {"false"}:
        raise PolicyReplayFixedStopsError("setup_reference_level was used as entry in at least one row")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / POLICY_REPLAY_FIXED_RESULTS_CSV
    summary_path = out_dir / POLICY_REPLAY_FIXED_SUMMARY_MD
    manifest_path = out_dir / POLICY_REPLAY_FIXED_MANIFEST_JSON

    results.to_csv(results_path, index=False)
    summary_path.write_text(_summary_text(results, merged), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "policy_replay_fixed_stops_version": POLICY_REPLAY_FIXED_STOPS_VERSION,
                "research_only": True,
                "sample_expanded": False,
                "focus_setup_rows_only": True,
                "watch_rows_evaluated": False,
                "changes_setup_detection_logic": False,
                "changes_setup_builder": False,
                "setup_reference_level_used_as_entry": False,
                "uses_tradable_entry_anchor": True,
                "uses_selected_research_stop_reference": True,
                "uses_backtester": False,
                "uses_executor": False,
                "uses_orders": False,
                "uses_entries_exits": False,
                "uses_pnl": False,
                "uses_position_sizing": False,
                "live_readiness_claim": False,
                "strategy_promotion": False,
                "focus_alignment_path": str(focus_alignment_path),
                "structural_stops_path": str(structural_stops_path),
                "manual_verdicts_path": str(manual_verdicts_path),
                "feed_dir": str(feed_root),
                "output_dir": str(out_dir),
                "focus_setup_count": int(len(merged)),
                "result_row_count": int(len(results)),
                "outputs": {
                    "policy_replay_fixed_stop_results_csv": str(results_path),
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
    return PolicyReplayFixedStopsResult(out_dir, results_path, summary_path, manifest_path, int(len(results)))


def _merge_focus_rows(*, focus: pd.DataFrame, stops: pd.DataFrame, verdicts: pd.DataFrame) -> pd.DataFrame:
    focus_keys = focus.rename(columns={"focus_timestamp": "setup_formed_at", "expected_setup_type": "setup_type"})[
        ["setup_formed_at", "setup_type"]
    ].copy()
    merged = focus_keys.merge(stops, on=["setup_formed_at", "setup_type"], how="left", suffixes=("", "_stop"))
    merged = merged.merge(
        verdicts[
            [
                "setup_id",
                "interval_id",
                "setup_formed_at",
                "setup_type",
                "direction_context",
                "sequence_role",
                "research_action",
            ]
        ],
        on=["setup_formed_at", "setup_type"],
        how="left",
        suffixes=("", "_verdict"),
    )
    if merged["selected_research_stop_reference"].isna().any():
        raise PolicyReplayFixedStopsError("missing selected research stop for at least one focus setup")
    if merged["setup_id_verdict"].notna().any():
        merged["setup_id"] = merged["setup_id_verdict"].fillna(merged["setup_id"])
    if merged["direction_context_verdict"].notna().any():
        merged["direction_context"] = merged["direction_context_verdict"].fillna(merged["direction_context"])
    return merged.drop(columns=[column for column in ["setup_id_verdict", "direction_context_verdict"] if column in merged.columns])


def _replay_setup(*, setup: pd.Series, feed_root: Path) -> list[dict[str, object]]:
    formed_at = _parse_ts(setup.get("setup_formed_at"))
    end_ts = _interval_end(setup.get("interval_id"))
    if pd.isna(end_ts) or end_ts <= formed_at:
        end_ts = formed_at + pd.Timedelta(hours=48)
    forward = _load_feed_range(feed_root=feed_root, start_ts=formed_at + pd.Timedelta(minutes=1), end_ts=end_ts)

    direction = _cell(setup.get("direction_context")).upper()
    entry = _float_value(setup.get("tradable_entry_anchor"))
    setup_reference = _float_value(setup.get("setup_reference_level"))
    selected_stop = _float_value(setup.get("selected_research_stop_reference"))
    target_reference = _cell(setup.get("target_reference"))
    target = _parse_target_zone(target_reference)
    stop_distance = abs(selected_stop - entry) if not pd.isna(selected_stop) and not pd.isna(entry) else float("nan")
    target_distance = _target_distance(direction=direction, entry=entry, target=target)
    potential_r = target_distance / stop_distance if _positive(stop_distance) and not pd.isna(target_distance) else float("nan")
    tp1_price = _tp1_price(direction=direction, entry=entry, stop_distance=stop_distance)

    path = _evaluate_forward_path(
        forward=forward,
        direction=direction,
        entry=entry,
        selected_stop=selected_stop,
        target=target,
        stop_distance=stop_distance,
        tp1_price=tp1_price,
    )
    base = {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_formed_at": _iso_z(formed_at),
        "setup_type": _cell(setup.get("setup_type")),
        "direction_context": direction,
        "sequence_role": _cell(setup.get("sequence_role")),
        "research_action": _cell(setup.get("research_action")),
        "tradable_entry_anchor": _round(entry),
        "setup_reference_level": _round(setup_reference),
        "setup_reference_used_as_entry": "false",
        "selected_research_stop_reference": _round(selected_stop),
        "selected_research_stop_type": _cell(setup.get("selected_research_stop_type")),
        "stop_distance_usd": _round(stop_distance),
        "target_reference": target_reference,
        "target_zone_lower": _round(target["lower"]) if target else "",
        "target_zone_upper": _round(target["upper"]) if target else "",
        "target_distance_usd": _round(target_distance),
        "potential_r_to_target": _round(potential_r),
        "tp1_r": 1.0,
        "tp1_price": _round(tp1_price),
        "target_touched": str(path["target_touched"]).lower(),
        "target_touched_at": _iso_z(path["target_touched_at"]),
        "selected_stop_touched": str(path["stop_touched"]).lower(),
        "selected_stop_touched_at": _iso_z(path["stop_touched_at"]),
        "tp1_touched": str(path["tp1_touched"]).lower(),
        "tp1_touched_at": _iso_z(path["tp1_touched_at"]),
        "be_hit_after_tp1": str(path["be_hit_after_tp1"]).lower(),
        "max_favorable_excursion_usd": _round(path["mfe_usd"]),
        "max_adverse_excursion_usd": _round(path["mae_usd"]),
        "max_favorable_excursion_r": _round(path["mfe_r"]),
        "max_adverse_excursion_r": _round(path["mae_r"]),
    }
    return [
        {
            **base,
            "policy_name": SELECTED_STOP_TARGET_POLICY,
            "first_event": path["selected_stop_first_event"],
            "policy_outcome_label": _selected_stop_outcome(path=path, unresolved=_unresolved(direction, entry, selected_stop, target), insufficient=forward.empty),
            "evidence_summary": _evidence_summary(setup=setup, forward_rows=len(forward), policy=SELECTED_STOP_TARGET_POLICY, path=path),
        },
        {
            **base,
            "policy_name": TP1_BE_WITH_SELECTED_STOP_POLICY,
            "first_event": path["tp1_policy_first_event"],
            "policy_outcome_label": _tp1_outcome(path=path, unresolved=_unresolved(direction, entry, selected_stop, target), insufficient=forward.empty),
            "evidence_summary": _evidence_summary(setup=setup, forward_rows=len(forward), policy=TP1_BE_WITH_SELECTED_STOP_POLICY, path=path),
        },
    ]


def _evaluate_forward_path(
    *,
    forward: pd.DataFrame,
    direction: str,
    entry: float,
    selected_stop: float,
    target: dict[str, float] | None,
    stop_distance: float,
    tp1_price: float,
) -> dict[str, object]:
    path = {
        "target_touched": False,
        "target_touched_at": pd.NaT,
        "stop_touched": False,
        "stop_touched_at": pd.NaT,
        "tp1_touched": False,
        "tp1_touched_at": pd.NaT,
        "be_hit_after_tp1": False,
        "be_hit_after_tp1_at": pd.NaT,
        "tp1_effective": False,
        "tp1_same_bar_as_stop": False,
        "tp1_be_same_bar": False,
        "mfe_usd": float("nan"),
        "mae_usd": float("nan"),
        "mfe_r": float("nan"),
        "mae_r": float("nan"),
        "selected_stop_first_event": "",
        "tp1_policy_first_event": "",
    }
    if forward.empty or pd.isna(entry) or direction not in {"UP", "DOWN"}:
        return path

    high = pd.to_numeric(forward["High"], errors="coerce")
    low = pd.to_numeric(forward["Low"], errors="coerce")
    if direction == "DOWN":
        path["mfe_usd"] = max(0.0, entry - float(low.min()))
        path["mae_usd"] = min(0.0, entry - float(high.max()))
        stop_mask = high >= selected_stop if not pd.isna(selected_stop) else pd.Series(False, index=forward.index)
        tp1_mask = low <= tp1_price if not pd.isna(tp1_price) else pd.Series(False, index=forward.index)
    else:
        path["mfe_usd"] = max(0.0, float(high.max()) - entry)
        path["mae_usd"] = min(0.0, float(low.min()) - entry)
        stop_mask = low <= selected_stop if not pd.isna(selected_stop) else pd.Series(False, index=forward.index)
        tp1_mask = high >= tp1_price if not pd.isna(tp1_price) else pd.Series(False, index=forward.index)
    if _positive(stop_distance):
        path["mfe_r"] = path["mfe_usd"] / stop_distance
        path["mae_r"] = path["mae_usd"] / stop_distance

    target_mask = _target_touch_mask(forward, target) if target else pd.Series(False, index=forward.index)
    if bool(target_mask.any()):
        path["target_touched"] = True
        path["target_touched_at"] = forward.loc[target_mask, "_ts"].iloc[0]
    if bool(stop_mask.any()):
        path["stop_touched"] = True
        path["stop_touched_at"] = forward.loc[stop_mask, "_ts"].iloc[0]
    if bool(tp1_mask.any()):
        path["tp1_touched"] = True
        path["tp1_touched_at"] = forward.loc[tp1_mask, "_ts"].iloc[0]

    path["selected_stop_first_event"] = _first_event(
        [("TARGET", path["target_touched_at"]), ("SELECTED_STOP", path["stop_touched_at"])]
    )
    tp1_at = _parse_ts(path["tp1_touched_at"])
    stop_at = _parse_ts(path["stop_touched_at"])
    if not pd.isna(stop_at) and not pd.isna(tp1_at) and stop_at < tp1_at:
        path["tp1_policy_first_event"] = "SELECTED_STOP"
    elif not pd.isna(stop_at) and not pd.isna(tp1_at) and stop_at == tp1_at:
        path["tp1_same_bar_as_stop"] = True
        path["tp1_policy_first_event"] = "AMBIGUOUS_SAME_BAR"
    elif not pd.isna(tp1_at):
        path["tp1_effective"] = True
        same_bar = forward[forward["_ts"] == tp1_at]
        if not same_bar.empty:
            if direction == "DOWN":
                same_bar_be_mask = pd.to_numeric(same_bar["High"], errors="coerce") >= entry
            else:
                same_bar_be_mask = pd.to_numeric(same_bar["Low"], errors="coerce") <= entry
            if bool(same_bar_be_mask.any()):
                path["tp1_be_same_bar"] = True
                path["be_hit_after_tp1"] = True
                path["be_hit_after_tp1_at"] = tp1_at
                path["tp1_policy_first_event"] = "AMBIGUOUS_SAME_BAR"
                return path
        after_tp1 = forward[forward["_ts"] > tp1_at]
        if not after_tp1.empty:
            if direction == "DOWN":
                be_mask = pd.to_numeric(after_tp1["High"], errors="coerce") >= entry
            else:
                be_mask = pd.to_numeric(after_tp1["Low"], errors="coerce") <= entry
            if bool(be_mask.any()):
                path["be_hit_after_tp1"] = True
                path["be_hit_after_tp1_at"] = after_tp1.loc[be_mask, "_ts"].iloc[0]
        path["tp1_policy_first_event"] = _first_event(
            [
                ("TARGET", path["target_touched_at"] if _at_or_after(path["target_touched_at"], tp1_at) else pd.NaT),
                ("BE", path["be_hit_after_tp1_at"]),
                ("SELECTED_STOP", path["stop_touched_at"] if _at_or_after(path["stop_touched_at"], tp1_at) else pd.NaT),
            ]
        )
    else:
        path["tp1_policy_first_event"] = path["selected_stop_first_event"]
    return path


def _selected_stop_outcome(*, path: dict[str, object], unresolved: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_FORWARD_DATA"
    if unresolved:
        return "TARGET_OR_STOP_UNRESOLVED"
    first = path["selected_stop_first_event"]
    if first == "TARGET":
        return "TARGET_BEFORE_SELECTED_STOP"
    if first == "SELECTED_STOP":
        return "SELECTED_STOP_BEFORE_TARGET"
    return "NO_DECISIVE_OUTCOME"


def _tp1_outcome(*, path: dict[str, object], unresolved: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_FORWARD_DATA"
    if unresolved:
        return "NO_DECISIVE_OUTCOME"
    if path["tp1_policy_first_event"] == "AMBIGUOUS_SAME_BAR":
        return "AMBIGUOUS_SAME_BAR"
    if path["tp1_policy_first_event"] == "SELECTED_STOP":
        return "NO_TP1_SELECTED_STOP"
    if not path["tp1_touched"]:
        return "NO_TP1_SELECTED_STOP" if path["stop_touched"] else "NO_DECISIVE_OUTCOME"
    first = path["tp1_policy_first_event"]
    if first == "TARGET":
        return "TP1_THEN_TARGET"
    if first == "BE":
        return "TP1_THEN_BE"
    if first == "SELECTED_STOP":
        return "TP1_THEN_SELECTED_STOP"
    return "NO_DECISIVE_OUTCOME"


def _first_event(events: list[tuple[str, object]]) -> str:
    valid = [(name, _parse_ts(ts)) for name, ts in events if not pd.isna(_parse_ts(ts))]
    if not valid:
        return ""
    valid.sort(key=lambda item: (item[1], ["TARGET", "TP1", "BE", "SELECTED_STOP"].index(item[0]) if item[0] in {"TARGET", "TP1", "BE", "SELECTED_STOP"} else 99))
    return valid[0][0]


def _after(value: object, threshold: object) -> bool:
    ts = _parse_ts(value)
    cutoff = _parse_ts(threshold)
    return not pd.isna(ts) and not pd.isna(cutoff) and ts > cutoff


def _at_or_after(value: object, threshold: object) -> bool:
    ts = _parse_ts(value)
    cutoff = _parse_ts(threshold)
    return not pd.isna(ts) and not pd.isna(cutoff) and ts >= cutoff


def _load_feed_range(*, feed_root: Path, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> pd.DataFrame:
    frames = []
    day = start_ts.date()
    while day <= end_ts.date():
        path = feed_root / f"{day.isoformat()}.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["_ts"] = pd.to_datetime(frame.get("Timestamp"), errors="coerce", utc=True)
            frames.append(frame)
        day = day + timedelta(days=1)
    if not frames:
        return pd.DataFrame(columns=["_ts", "Open", "High", "Low", "Close"])
    feed = pd.concat(frames, ignore_index=True, sort=False)
    feed = feed[(feed["_ts"] >= start_ts) & (feed["_ts"] <= end_ts)].copy()
    return feed.sort_values("_ts", kind="mergesort").reset_index(drop=True)


def _interval_end(value: object) -> pd.Timestamp:
    text = _cell(value)
    match = re.match(r"interval_\d{4}_\d{2}_\d{2}_to_(\d{4})_(\d{2})_(\d{2})", text)
    if not match:
        return pd.NaT
    year, month, day = match.groups()
    return pd.Timestamp(f"{year}-{month}-{day}T23:59:00Z")


def _parse_target_zone(value: object) -> dict[str, float] | None:
    parts = _cell(value).split(":")
    if len(parts) != 3 or "-" not in parts[2]:
        return None
    lower_text, upper_text = parts[2].split("-", 1)
    lower = _float_value(lower_text)
    upper = _float_value(upper_text)
    if pd.isna(lower) or pd.isna(upper):
        return None
    return {"lower": min(lower, upper), "upper": max(lower, upper)}


def _target_touch_mask(feed: pd.DataFrame, target: dict[str, float] | None) -> pd.Series:
    if target is None:
        return pd.Series(False, index=feed.index)
    high = pd.to_numeric(feed["High"], errors="coerce")
    low = pd.to_numeric(feed["Low"], errors="coerce")
    return (high >= target["lower"]) & (low <= target["upper"])


def _target_distance(*, direction: str, entry: float, target: dict[str, float] | None) -> float:
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


def _tp1_price(*, direction: str, entry: float, stop_distance: float) -> float:
    if pd.isna(entry) or not _positive(stop_distance):
        return float("nan")
    if direction == "DOWN":
        return entry - stop_distance
    if direction == "UP":
        return entry + stop_distance
    return float("nan")


def _unresolved(direction: str, entry: float, selected_stop: float, target: dict[str, float] | None) -> bool:
    return direction not in {"UP", "DOWN"} or pd.isna(entry) or pd.isna(selected_stop) or target is None


def _positive(value: float) -> bool:
    return not pd.isna(value) and value > 0


def _evidence_summary(*, setup: pd.Series, forward_rows: int, policy: str, path: dict[str, object]) -> str:
    ordering = ""
    stop_at = _iso_z(path.get("stop_touched_at"))
    tp1_at = _iso_z(path.get("tp1_touched_at"))
    if stop_at and tp1_at and _parse_ts(stop_at) < _parse_ts(tp1_at):
        ordering = f"; selected_stop_touched_at={stop_at} occurred before tp1_touched_at={tp1_at}"
    elif stop_at and tp1_at and _parse_ts(stop_at) == _parse_ts(tp1_at):
        ordering = f"; selected_stop_touched_at={stop_at} and tp1_touched_at={tp1_at} occurred in same bar"
    return (
        f"policy={policy}; forward_rows_after_setup={forward_rows}; setup_reference_used_as_entry=false; "
        f"entry_anchor=tradable_entry_anchor:{_round(setup.get('tradable_entry_anchor'))}; "
        f"selected_stop={_round(setup.get('selected_research_stop_reference'))}:{_cell(setup.get('selected_research_stop_type'))}; "
        f"target_reference={_cell(setup.get('target_reference'))}; no_new_setup_detection=true{ordering}"
    )

def _summary_text(results: pd.DataFrame, focus_rows: pd.DataFrame) -> str:
    positive = results[
        results["policy_outcome_label"].isin({"TARGET_BEFORE_SELECTED_STOP", "TP1_THEN_TARGET", "TP1_THEN_BE"})
    ]
    weak = results[
        results["policy_outcome_label"].isin(
            {"SELECTED_STOP_BEFORE_TARGET", "NO_TP1_SELECTED_STOP", "NO_DECISIVE_OUTCOME", "TARGET_OR_STOP_UNRESOLVED", "INSUFFICIENT_FORWARD_DATA"}
        )
    ]
    lines = [
        "# SHI RESET 38I Policy Replay Fixed Anchors Structural Stops Summary",
        "",
        "Research-only policy replay on the five existing 38G focus setup rows using 38F fixed entry anchors and 38H selected research stops.",
        "",
        f"- Total focus setup rows: {len(focus_rows)}",
        f"- Result rows: {len(results)}",
        f"- Rows by setup_type: {_counts_json(focus_rows, 'setup_type')}",
        f"- Rows by sequence_role: {_counts_json(focus_rows, 'sequence_role')}",
        f"- Rows by selected_research_stop_type: {_counts_json(focus_rows, 'selected_research_stop_type')}",
        f"- Outcomes by policy_name: {_nested_counts_json(results, 'policy_name', 'policy_outcome_label')}",
        f"- Target-before-stop count: {int((results['policy_outcome_label'] == 'TARGET_BEFORE_SELECTED_STOP').sum()) if not results.empty else 0}",
        f"- Stop-before-target count: {int((results['policy_outcome_label'] == 'SELECTED_STOP_BEFORE_TARGET').sum()) if not results.empty else 0}",
        f"- TP1 touched count: {int((results['tp1_touched'].astype(str).str.lower() == 'true').sum()) if not results.empty else 0}",
        f"- TP1 then target count: {int((results['policy_outcome_label'] == 'TP1_THEN_TARGET').sum()) if not results.empty else 0}",
        f"- TP1 then BE count: {int((results['policy_outcome_label'] == 'TP1_THEN_BE').sum()) if not results.empty else 0}",
        f"- Rejected/unresolved count: {len(weak)}",
        "",
        "## Policy-Positive Setups",
        "",
    ]
    lines.extend(_setup_list(positive))
    lines.extend(["", "## Setups That Remain Weak After Fixed-Anchor / Structural-Stop Replay", ""])
    lines.extend(_setup_list(weak))
    lines.extend(
        [
            "",
            "## Governance",
            "",
            "- `setup_reference_level` was not used as entry.",
            "- No setup rows were created.",
            "- WATCH rows were not evaluated.",
            "- Forward data was used only after `setup_formed_at` for outcome evaluation.",
            "- No Backtester, Executor, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def _setup_list(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["- None"]
    rows = []
    for _, row in frame.sort_values(["setup_formed_at", "policy_name"], kind="mergesort").iterrows():
        rows.append(
            f"- `{row['setup_formed_at']}` `{row['setup_type']}` `{row['policy_name']}` -> `{row['policy_outcome_label']}`"
        )
    return rows


def _counts_json(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "{}"
    return json.dumps(frame[column].fillna("").astype(str).value_counts().to_dict(), sort_keys=True)


def _nested_counts_json(frame: pd.DataFrame, outer: str, inner: str) -> str:
    if frame.empty:
        return "{}"
    output = {}
    for name, group in frame.groupby(outer):
        output[str(name)] = group[inner].astype(str).value_counts().to_dict()
    return json.dumps(output, sort_keys=True)


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _parse_ts(value: object) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce", utc=True)


def _iso_z(value: object) -> str:
    ts = _parse_ts(value)
    if pd.isna(ts):
        return ""
    return ts.isoformat().replace("+00:00", "Z")


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
