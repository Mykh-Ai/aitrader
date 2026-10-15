from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RUN_VERSION = "SHI_RESET_38W1_FIX_CHRONOLOGICAL_TP1_STOP_LABELS_V0"
OUT = Path("market_monitor_runs/SHI_RESET_38W1_fix_chronological_tp1_stop_labels_v0")
SOURCE_CANDIDATES = Path(
    "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/"
    "full_feed_setup_builder_candidates.csv"
)
SOURCE_SELECTED_FEED = Path(
    "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/"
    "support/selected_feed"
)
SOURCE_SELECTED_ZONES = Path(
    "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/"
    "support/selected_zones/selected_zones.csv"
)
SOURCE_38V_MANIFEST = Path(
    "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/38v_manifest.json"
)
END_TS = pd.Timestamp("2026-06-28T23:59:00Z")
SPECIMEN_SETUP_FORMED_AT = "2026-05-26T16:59:00Z"

OUTCOME_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "trigger_status",
    "candidate_strength",
    "armed_high_bucket",
    "actual_setup_price",
    "tradable_entry_anchor",
    "setup_reference_level",
    "setup_reference_used_as_entry",
    "target_reference",
    "target_zone_lower",
    "target_zone_upper",
    "selected_research_stop_reference",
    "selected_research_stop_type",
    "stop_distance_usd",
    "target_distance_usd",
    "potential_r_to_target",
    "tp1_price",
    "target_touched",
    "target_touched_at",
    "selected_stop_touched",
    "selected_stop_touched_at",
    "tp1_touched",
    "tp1_touched_at",
    "be_hit_after_tp1",
    "be_hit_after_tp1_at",
    "first_event",
    "outcome_label",
    "max_favorable_excursion_usd",
    "max_adverse_excursion_usd",
    "max_favorable_excursion_r",
    "max_adverse_excursion_r",
    "quality_mfe_before_stop_usd",
    "quality_mfe_before_stop_r",
    "valid_tp1_before_stop",
    "selected_stop_before_or_at_tp1",
    "manual_monitor_verdict",
    "evidence_summary",
]

POLICY_COLUMNS = [
    "setup_id",
    "setup_formed_at",
    "setup_type",
    "direction_context",
    "trigger_status",
    "candidate_strength",
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
    "be_hit_after_tp1_at",
    "first_event",
    "policy_outcome_label",
    "max_favorable_excursion_usd",
    "max_adverse_excursion_usd",
    "max_favorable_excursion_r",
    "max_adverse_excursion_r",
    "quality_mfe_before_stop_usd",
    "quality_mfe_before_stop_r",
    "valid_tp1_before_stop",
    "selected_stop_before_or_at_tp1",
    "evidence_summary",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = _read_csv(SOURCE_CANDIDATES)
    if len(candidates) != 51:
        raise RuntimeError(f"expected 51 canonical setup_builder candidates from 38V, found {len(candidates)}")
    zones = _read_csv(SOURCE_SELECTED_ZONES)
    feed = _load_feed(SOURCE_SELECTED_FEED)

    outcome_rows: list[dict[str, object]] = []
    policy_rows: list[dict[str, object]] = []
    for _, setup in candidates.iterrows():
        enriched = _enrich_setup(setup, feed, zones)
        path = _evaluate_path(enriched, feed)
        outcome_rows.append(_outcome_row(enriched, path))
        policy_rows.extend(_policy_rows(enriched, path))

    outcomes = pd.DataFrame(outcome_rows, columns=OUTCOME_COLUMNS)
    policies = pd.DataFrame(policy_rows, columns=POLICY_COLUMNS)
    shortlist = outcomes[outcomes["manual_monitor_verdict"].isin({"MANUAL_REVIEW_PRIMARY", "MANUAL_REVIEW_SECONDARY"})].copy()
    rejects = outcomes[~outcomes["manual_monitor_verdict"].isin({"MANUAL_REVIEW_PRIMARY", "MANUAL_REVIEW_SECONDARY"})].copy()

    outcomes.to_csv(OUT / "setup_builder_outcome_replay_results.csv", index=False)
    policies.to_csv(OUT / "setup_builder_policy_replay_results.csv", index=False)
    shortlist.to_csv(OUT / "manual_monitor_shortlist.csv", index=False)
    rejects.to_csv(OUT / "manual_monitor_rejects.csv", index=False)

    summary = _summary_text(outcomes, policies, shortlist, rejects)
    (OUT / "setup_builder_replay_summary.md").write_text(summary, encoding="utf-8")
    manifest = {
        "run_version": RUN_VERSION,
        "research_only": True,
        "source_candidates_are_38v_canonical_setup_builder_only": True,
        "uses_38s_rows_as_source_candidates": False,
        "uses_old_analyzer": False,
        "uses_old_backtester": False,
        "uses_executor": False,
        "uses_orders": False,
        "uses_live_trading": False,
        "uses_pnl": False,
        "uses_position_sizing": False,
        "uses_live_readiness": False,
        "uses_strategy_promotion": False,
        "setup_reference_level_used_as_entry": False,
        "forward_data_used_for_outcome_evaluation_only": True,
        "source_candidates_csv": str(SOURCE_CANDIDATES),
        "selected_feed_dir": str(SOURCE_SELECTED_FEED),
        "selected_zones_csv": str(SOURCE_SELECTED_ZONES),
        "source_38v_manifest": str(SOURCE_38V_MANIFEST),
        "candidate_count": int(len(candidates)),
        "outcome_count": int(len(outcomes)),
        "policy_result_count": int(len(policies)),
        "outputs": {
            "setup_builder_outcome_replay_results_csv": str(OUT / "setup_builder_outcome_replay_results.csv"),
            "setup_builder_policy_replay_results_csv": str(OUT / "setup_builder_policy_replay_results.csv"),
            "setup_builder_replay_summary_md": str(OUT / "setup_builder_replay_summary.md"),
            "setup_builder_replay_manifest_json": str(OUT / "setup_builder_replay_manifest.json"),
            "manual_monitor_shortlist_csv": str(OUT / "manual_monitor_shortlist.csv"),
            "manual_monitor_rejects_csv": str(OUT / "manual_monitor_rejects.csv"),
        },
        "counts": {
            "valid_tp1_before_stop": int((outcomes["valid_tp1_before_stop"].astype(str).str.lower() == "true").sum()),
            "target_before_stop": int((outcomes["first_event"] == "TARGET").sum()),
            "tp1_then_target": int((outcomes["outcome_label"] == "TP1_THEN_TARGET").sum()),
            "stop_before_or_at_tp1": int((outcomes["selected_stop_before_or_at_tp1"].astype(str).str.lower() == "true").sum()),
            "stop_before_tp1_label": int((outcomes["outcome_label"] == "STOP_BEFORE_TP1").sum()),
            "unresolved": int(outcomes["outcome_label"].isin({"UNRESOLVED_REFERENCE", "INSUFFICIENT_FORWARD_DATA"}).sum()),
        },
        "repo_commit": _repo_commit(),
        "generation_timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (OUT / "setup_builder_replay_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _enrich_setup(setup: pd.Series, feed: pd.DataFrame, zones: pd.DataFrame) -> dict[str, object]:
    row = setup.to_dict()
    formed_at = _parse_ts(row.get("setup_formed_at"))
    actual_bar = _first_bar_at_or_after(feed, formed_at)
    entry_bar = _first_bar_after(feed, formed_at)
    actual = _float(actual_bar.get("close")) if actual_bar is not None else float("nan")
    entry = _float(entry_bar.get("open"), _float(entry_bar.get("close"))) if entry_bar is not None else float("nan")
    row["actual_setup_price"] = actual
    row["tradable_entry_anchor"] = entry
    row["setup_reference_used_as_entry"] = "false"
    row["setup_reference_level"] = _float(row.get("setup_reference_level"), _float(row.get("entry_reference_level")))
    row["target_reference"] = _target_reference_text(row)
    row["target"] = _parse_target_zone(row.get("target_reference"))
    row["source_window"] = _source_window(feed, row)
    row["local_swing"] = _local_swing(feed, formed_at)
    stop = _stop_candidates(row, zones)
    row.update(stop)
    return row


def _evaluate_path(setup: dict[str, object], feed: pd.DataFrame) -> dict[str, object]:
    formed_at = _parse_ts(setup.get("setup_formed_at"))
    forward = feed[(feed["timestamp"] > formed_at) & (feed["timestamp"] <= END_TS)].copy()
    direction = _cell(setup.get("direction_context")).upper()
    entry = _float(setup.get("tradable_entry_anchor"))
    selected_stop = _float(setup.get("selected_research_stop_reference"))
    stop_distance = abs(selected_stop - entry) if not pd.isna(selected_stop) and not pd.isna(entry) else float("nan")
    target = setup.get("target")
    tp1 = _tp1_price(direction, entry, stop_distance)
    path = {
        "forward_rows": int(len(forward)),
        "target_touched": False,
        "target_touched_at": pd.NaT,
        "stop_touched": False,
        "stop_touched_at": pd.NaT,
        "tp1_touched": False,
        "tp1_touched_at": pd.NaT,
        "valid_tp1_before_stop": False,
        "selected_stop_before_or_at_tp1": False,
        "be_hit_after_tp1": False,
        "be_hit_after_tp1_at": pd.NaT,
        "mfe_usd": float("nan"),
        "mae_usd": float("nan"),
        "mfe_r": float("nan"),
        "mae_r": float("nan"),
        "quality_mfe_before_stop_usd": float("nan"),
        "quality_mfe_before_stop_r": float("nan"),
        "selected_stop_first_event": "",
        "tp1_policy_first_event": "",
        "outcome_label": "INSUFFICIENT_FORWARD_DATA" if forward.empty else "UNRESOLVED_REFERENCE",
        "tp1_price": tp1,
    }
    if forward.empty or pd.isna(entry) or direction not in {"UP", "DOWN"}:
        return path

    high = pd.to_numeric(forward["high"], errors="coerce")
    low = pd.to_numeric(forward["low"], errors="coerce")
    if direction == "DOWN":
        path["mfe_usd"] = max(0.0, entry - float(low.min()))
        path["mae_usd"] = min(0.0, entry - float(high.max()))
        stop_mask = high >= selected_stop if not pd.isna(selected_stop) else pd.Series(False, index=forward.index)
        tp1_mask = low <= tp1 if not pd.isna(tp1) else pd.Series(False, index=forward.index)
    else:
        path["mfe_usd"] = max(0.0, float(high.max()) - entry)
        path["mae_usd"] = min(0.0, float(low.min()) - entry)
        stop_mask = low <= selected_stop if not pd.isna(selected_stop) else pd.Series(False, index=forward.index)
        tp1_mask = high >= tp1 if not pd.isna(tp1) else pd.Series(False, index=forward.index)
    if _positive(stop_distance):
        path["mfe_r"] = path["mfe_usd"] / stop_distance
        path["mae_r"] = path["mae_usd"] / stop_distance

    target_mask = _target_touch_mask(forward, target)
    if bool(target_mask.any()):
        path["target_touched"] = True
        path["target_touched_at"] = forward.loc[target_mask, "timestamp"].iloc[0]
    if bool(stop_mask.any()):
        path["stop_touched"] = True
        path["stop_touched_at"] = forward.loc[stop_mask, "timestamp"].iloc[0]
    if bool(tp1_mask.any()):
        path["tp1_touched"] = True
        path["tp1_touched_at"] = forward.loc[tp1_mask, "timestamp"].iloc[0]

    tp1_at = _parse_ts(path["tp1_touched_at"])
    stop_at = _parse_ts(path["stop_touched_at"])
    target_at = _parse_ts(path["target_touched_at"])
    path["selected_stop_first_event"] = _first_event(
        [("TARGET", path["target_touched_at"]), ("SELECTED_STOP", path["stop_touched_at"])]
    )
    path["selected_stop_before_or_at_tp1"] = bool(
        path["stop_touched"] and (pd.isna(tp1_at) or stop_at <= tp1_at)
    )
    path["valid_tp1_before_stop"] = bool(path["tp1_touched"] and (pd.isna(stop_at) or tp1_at < stop_at))

    quality_end = stop_at if not pd.isna(stop_at) else forward["timestamp"].max()
    quality_forward = forward[forward["timestamp"] <= quality_end].copy()
    if not quality_forward.empty:
        q_high = pd.to_numeric(quality_forward["high"], errors="coerce")
        q_low = pd.to_numeric(quality_forward["low"], errors="coerce")
        if direction == "DOWN":
            path["quality_mfe_before_stop_usd"] = max(0.0, entry - float(q_low.min()))
        else:
            path["quality_mfe_before_stop_usd"] = max(0.0, float(q_high.max()) - entry)
        if _positive(stop_distance):
            path["quality_mfe_before_stop_r"] = path["quality_mfe_before_stop_usd"] / stop_distance

    if path["valid_tp1_before_stop"]:
        after_tp1 = forward[forward["timestamp"] > tp1_at].copy()
        if not after_tp1.empty:
            if direction == "DOWN":
                be_mask = pd.to_numeric(after_tp1["high"], errors="coerce") >= entry
            else:
                be_mask = pd.to_numeric(after_tp1["low"], errors="coerce") <= entry
            if bool(be_mask.any()):
                path["be_hit_after_tp1"] = True
                path["be_hit_after_tp1_at"] = after_tp1.loc[be_mask, "timestamp"].iloc[0]
        path["tp1_policy_first_event"] = _first_event(
            [
                ("TARGET", target_at if (not pd.isna(target_at) and target_at >= tp1_at) else pd.NaT),
                ("BE", path["be_hit_after_tp1_at"]),
            ]
        )
    elif path["selected_stop_before_or_at_tp1"]:
        path["tp1_policy_first_event"] = "SELECTED_STOP"

    unresolved = _unresolved(direction, entry, selected_stop, target)
    path["outcome_label"] = _combined_outcome(path, unresolved=unresolved, insufficient=forward.empty)
    return path

def _outcome_row(setup: dict[str, object], path: dict[str, object]) -> dict[str, object]:
    target = setup.get("target")
    direction = _cell(setup.get("direction_context")).upper()
    entry = _float(setup.get("tradable_entry_anchor"))
    stop = _float(setup.get("selected_research_stop_reference"))
    stop_distance = abs(stop - entry) if not pd.isna(stop) and not pd.isna(entry) else float("nan")
    target_distance = _target_distance(direction, entry, target)
    potential_r = target_distance / stop_distance if _positive(stop_distance) and not pd.isna(target_distance) else float("nan")
    verdict = _manual_monitor_verdict(setup, path)
    return {
        "setup_id": _cell(setup.get("setup_id")),
        "setup_formed_at": _iso(setup.get("setup_formed_at")),
        "setup_type": _cell(setup.get("setup_type")),
        "direction_context": direction,
        "trigger_status": _cell(setup.get("trigger_status")),
        "candidate_strength": _cell(setup.get("candidate_strength")),
        "armed_high_bucket": str(_armed_high(setup)).lower(),
        "actual_setup_price": _round(setup.get("actual_setup_price")),
        "tradable_entry_anchor": _round(entry),
        "setup_reference_level": _round(setup.get("setup_reference_level")),
        "setup_reference_used_as_entry": "false",
        "target_reference": _cell(setup.get("target_reference")),
        "target_zone_lower": _round(target["lower"]) if target else "",
        "target_zone_upper": _round(target["upper"]) if target else "",
        "selected_research_stop_reference": _round(stop),
        "selected_research_stop_type": _cell(setup.get("selected_research_stop_type")),
        "stop_distance_usd": _round(stop_distance),
        "target_distance_usd": _round(target_distance),
        "potential_r_to_target": _round(potential_r),
        "tp1_price": _round(path.get("tp1_price")),
        "target_touched": str(path["target_touched"]).lower(),
        "target_touched_at": _iso(path["target_touched_at"]),
        "selected_stop_touched": str(path["stop_touched"]).lower(),
        "selected_stop_touched_at": _iso(path["stop_touched_at"]),
        "tp1_touched": str(path["tp1_touched"]).lower(),
        "tp1_touched_at": _iso(path["tp1_touched_at"]),
        "be_hit_after_tp1": str(path["be_hit_after_tp1"]).lower(),
        "be_hit_after_tp1_at": _iso(path["be_hit_after_tp1_at"]),
        "first_event": path["selected_stop_first_event"],
        "outcome_label": path["outcome_label"],
        "max_favorable_excursion_usd": _round(path["mfe_usd"]),
        "max_adverse_excursion_usd": _round(path["mae_usd"]),
        "max_favorable_excursion_r": _round(path["mfe_r"]),
        "max_adverse_excursion_r": _round(path["mae_r"]),
        "quality_mfe_before_stop_usd": _round(path["quality_mfe_before_stop_usd"]),
        "quality_mfe_before_stop_r": _round(path["quality_mfe_before_stop_r"]),
        "valid_tp1_before_stop": str(path["valid_tp1_before_stop"]).lower(),
        "selected_stop_before_or_at_tp1": str(path["selected_stop_before_or_at_tp1"]).lower(),
        "manual_monitor_verdict": verdict,
        "evidence_summary": _evidence(setup, path, verdict),
    }


def _policy_rows(setup: dict[str, object], path: dict[str, object]) -> list[dict[str, object]]:
    base = _outcome_row(setup, path)
    selected_outcome = _selected_stop_outcome(path, _unresolved(base["direction_context"], _float(base["tradable_entry_anchor"]), _float(base["selected_research_stop_reference"]), setup.get("target")), path["forward_rows"] == 0)
    tp1_outcome = _tp1_outcome(path, _unresolved(base["direction_context"], _float(base["tradable_entry_anchor"]), _float(base["selected_research_stop_reference"]), setup.get("target")), path["forward_rows"] == 0)
    rows = []
    for policy, outcome, first_event in [
        ("SELECTED_STOP_TARGET_POLICY", selected_outcome, path["selected_stop_first_event"]),
        ("TP1_BE_WITH_SELECTED_STOP_POLICY", tp1_outcome, path["tp1_policy_first_event"]),
    ]:
        rows.append(
            {
                **{column: base.get(column, "") for column in POLICY_COLUMNS if column in base},
                "policy_name": policy,
                "tp1_r": 1.0,
                "first_event": first_event,
                "policy_outcome_label": outcome,
                "evidence_summary": f"policy={policy}; canonical_setup_builder_source=38V; setup_reference_used_as_entry=false; forward_rows_after_setup={path['forward_rows']}; no_38s_source_candidates=true",
            }
        )
    return rows


def _combined_outcome(path: dict[str, object], *, unresolved: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_FORWARD_DATA"
    if unresolved:
        return "UNRESOLVED_REFERENCE"
    if path["selected_stop_before_or_at_tp1"]:
        return "STOP_BEFORE_TP1"
    if path["tp1_policy_first_event"] == "TARGET":
        return "TP1_THEN_TARGET"
    if path["tp1_policy_first_event"] == "BE":
        return "TP1_THEN_BE"
    if path["valid_tp1_before_stop"]:
        return "TP1_ONLY_NO_FOLLOWUP"
    if path["selected_stop_first_event"] == "TARGET":
        return "TARGET_BEFORE_SELECTED_STOP"
    return "NO_DECISIVE_OUTCOME"


def _selected_stop_outcome(path: dict[str, object], unresolved: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_FORWARD_DATA"
    if unresolved:
        return "UNRESOLVED_REFERENCE"
    if path["selected_stop_first_event"] == "TARGET":
        return "TARGET_BEFORE_SELECTED_STOP"
    if path["selected_stop_first_event"] == "SELECTED_STOP":
        return "SELECTED_STOP_BEFORE_TARGET"
    return "NO_DECISIVE_OUTCOME"


def _tp1_outcome(path: dict[str, object], unresolved: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_FORWARD_DATA"
    if unresolved:
        return "UNRESOLVED_REFERENCE"
    if path["selected_stop_before_or_at_tp1"]:
        return "STOP_BEFORE_TP1"
    if not path["valid_tp1_before_stop"]:
        return "NO_DECISIVE_OUTCOME"
    if path["tp1_policy_first_event"] == "TARGET":
        return "TP1_THEN_TARGET"
    if path["tp1_policy_first_event"] == "BE":
        return "TP1_THEN_BE"
    return "TP1_ONLY_NO_FOLLOWUP"


def _manual_monitor_verdict(setup: dict[str, object], path: dict[str, object]) -> str:
    formed_at = _parse_ts(setup.get("setup_formed_at"))
    if pd.Timestamp("2026-04-23T17:05:00Z") <= formed_at <= pd.Timestamp("2026-05-06T22:51:00Z"):
        return "DATA_COVERAGE_REVIEW"
    if path["outcome_label"] in {"UNRESOLVED_REFERENCE", "INSUFFICIENT_FORWARD_DATA"}:
        return "REFERENCE_UNRESOLVED_REVIEW"
    if path["selected_stop_before_or_at_tp1"]:
        return "WEAK_REACTION_REJECT"
    if _armed_high(setup) and path["outcome_label"] in {"TARGET_BEFORE_SELECTED_STOP", "TP1_THEN_TARGET", "TP1_THEN_BE", "TP1_ONLY_NO_FOLLOWUP"}:
        return "MANUAL_REVIEW_PRIMARY"
    if path["valid_tp1_before_stop"] and path["quality_mfe_before_stop_r"] >= 1.0:
        return "MANUAL_REVIEW_SECONDARY"
    return "WEAK_REACTION_REJECT"


def _summary_text(outcomes: pd.DataFrame, policies: pd.DataFrame, shortlist: pd.DataFrame, rejects: pd.DataFrame) -> str:
    valid_tp1 = int((outcomes["valid_tp1_before_stop"].astype(str).str.lower() == "true").sum())
    target_before_stop = int((outcomes["first_event"] == "TARGET").sum())
    tp1_then_target = int((outcomes["outcome_label"] == "TP1_THEN_TARGET").sum())
    stop_before_or_at_tp1 = int((outcomes["selected_stop_before_or_at_tp1"].astype(str).str.lower() == "true").sum())
    unresolved = int(outcomes["outcome_label"].isin({"UNRESOLVED_REFERENCE", "INSUFFICIENT_FORWARD_DATA"}).sum())
    specimen = outcomes[outcomes["setup_formed_at"].astype(str).str.startswith(SPECIMEN_SETUP_FORMED_AT[:16])]
    specimen_strong = bool(
        not specimen.empty
        and specimen.iloc[0]["manual_monitor_verdict"] in {"MANUAL_REVIEW_PRIMARY", "MANUAL_REVIEW_SECONDARY"}
        and specimen.iloc[0]["outcome_label"] in {"TARGET_BEFORE_SELECTED_STOP", "TP1_THEN_TARGET", "TP1_THEN_BE", "TP1_ONLY_NO_FOLLOWUP"}
    )
    armed_high = outcomes[outcomes["armed_high_bucket"].astype(str) == "true"]
    armed_high_valid = armed_high[armed_high["manual_monitor_verdict"].isin({"MANUAL_REVIEW_PRIMARY", "MANUAL_REVIEW_SECONDARY"})]
    non_specimen_armed_high = armed_high[
        ~armed_high["setup_formed_at"].astype(str).str.startswith(SPECIMEN_SETUP_FORMED_AT[:16])
    ]
    non_specimen_usable = non_specimen_armed_high[
        non_specimen_armed_high["manual_monitor_verdict"].isin({"MANUAL_REVIEW_PRIMARY", "MANUAL_REVIEW_SECONDARY"})
    ]
    lines = [
        "# SHI RESET 38W1 Chronological TP1/Stop Label Fix",
        "",
        "Research-only correction of 38W outcome labels on canonical 38V setup_builder candidates only.",
        "",
        "## Governance",
        "",
        "- This is not live trading.",
        "- This does not prove edge.",
        "- This does not use old Analyzer v1.",
        "- This does not use old Backtester.",
        "- This evaluates canonical setup_builder candidates only.",
        "- 38S rows remain rejected as source candidates.",
        "- No Executor, orders, PnL, position sizing, live-readiness, or strategy promotion.",
        "- MFE/R after selected stop is not counted as trade-quality evidence.",
        "- Manual shortlist excludes rows where selected_stop_touched_at <= tp1_touched_at.",
        "",
        "## Corrected Counts",
        "",
        f"- Canonical setup_builder candidates replayed: {len(outcomes)}",
        f"- Valid TP1-before-stop reactions: {valid_tp1}",
        f"- Target-before-stop / full target continuation: {target_before_stop}",
        f"- TP1 then target: {tp1_then_target}",
        f"- STOP_BEFORE_TP1 rows: {stop_before_or_at_tp1}",
        f"- Unresolved / insufficient: {unresolved}",
        f"- Manual monitor shortlist rows: {len(shortlist)}",
        f"- Manual monitor reject rows: {len(rejects)}",
        f"- ARMED/HIGH valid reaction: {len(armed_high_valid)} of {len(armed_high)}",
        f"- Non-specimen ARMED/HIGH valid reaction: {len(non_specimen_usable)} of {len(non_specimen_armed_high)}",
        f"- 2026-05-26 specimen remains strong: {str(specimen_strong).lower()}",
        "",
        "## Splits",
        "",
        f"- By setup_type: {_counts_json(outcomes, 'setup_type')}",
        f"- By direction_context: {_counts_json(outcomes, 'direction_context')}",
        f"- By trigger_status: {_counts_json(outcomes, 'trigger_status')}",
        f"- By candidate_strength: {_counts_json(outcomes, 'candidate_strength')}",
        f"- By ARMED/HIGH bucket: {_counts_json(outcomes, 'armed_high_bucket')}",
        f"- By outcome_label: {_counts_json(outcomes, 'outcome_label')}",
        f"- By manual_monitor_verdict: {_counts_json(outcomes, 'manual_monitor_verdict')}",
        f"- Policy outcomes: {_nested_counts_json(policies, 'policy_name', 'policy_outcome_label')}",
        "",
        "## Verdict",
        "",
        "38W was positive as proof that the monitor sees reactions, but 38W1 rejects the earlier 51/51 quality reading. The corrected valid reaction set is based on chronological TP1-before-stop only, with full target continuation remaining limited to the target-before-stop rows.",
        "",
        "## Manual Monitor Shortlist",
        "",
    ]
    if shortlist.empty:
        lines.append("- none")
    else:
        for _, row in shortlist.iterrows():
            lines.append(
                "- "
                f"{row['setup_id']} {row['setup_formed_at']} {row['direction_context']} "
                f"{row['setup_type']} {row['outcome_label']} "
                f"quality_mfe_before_stop_r={row['quality_mfe_before_stop_r']} "
                f"verdict={row['manual_monitor_verdict']}"
            )
    lines.append("")
    return "\n".join(lines)

def _stop_candidates(row: dict[str, object], zones: pd.DataFrame) -> dict[str, object]:
    direction = _cell(row.get("direction_context")).upper()
    entry = _float(row.get("tradable_entry_anchor"))
    source = row.get("source_window")
    source_high = float(source["high"].max()) if isinstance(source, pd.DataFrame) and not source.empty else float("nan")
    source_low = float(source["low"].min()) if isinstance(source, pd.DataFrame) and not source.empty else float("nan")
    local = row.get("local_swing", {})
    local_high = _float(local.get("high"))
    local_low = _float(local.get("low"))
    original = _float(row.get("stop_reference"), _float(row.get("invalidation_level")))
    structural = _structural_zone_stop(row, zones)
    source_stop = source_high if direction == "DOWN" else source_low
    local_stop = local_high if direction == "DOWN" else local_low
    selected, selected_type, reason = _select_stop(
        direction=direction,
        entry=entry,
        structural_stop=structural["stop"],
        structural_stop_type=structural["type"],
        local_stop=local_stop,
        source_stop=source_stop,
        original_stop=original,
    )
    return {
        "source_window_high": source_high,
        "source_window_low": source_low,
        "local_swing_high_candidate": local_high,
        "local_swing_low_candidate": local_low,
        "structural_zone_stop_reference": structural["stop"],
        "structural_zone_stop_type": structural["type"],
        "original_invalidation_stop": original,
        "selected_research_stop_reference": selected,
        "selected_research_stop_type": selected_type,
        "stop_selection_reason": reason,
    }


def _select_stop(*, direction: str, entry: float, structural_stop: float, structural_stop_type: str, local_stop: float, source_stop: float, original_stop: float) -> tuple[float, str, str]:
    if structural_stop_type == "structural_zone_stop" and _valid_stop(direction, entry, structural_stop):
        return structural_stop, "structural_zone_stop", "selected structural zone stop"
    if _valid_stop(direction, entry, local_stop):
        return local_stop, "local_swing_stop", "selected local swing stop"
    if _valid_stop(direction, entry, source_stop):
        return source_stop, "source_window_stop", "selected source-window stop because no structural/local stop resolved"
    if _valid_stop(direction, entry, original_stop):
        return original_stop, "original_invalidation_stop", "selected setup invalidation because no better structural/local stop resolved"
    return float("nan"), "unresolved", "no valid stop candidate resolved"


def _structural_zone_stop(row: dict[str, object], zones: pd.DataFrame) -> dict[str, object]:
    fallback = _float(row.get("stop_reference"), _float(row.get("invalidation_level")))
    if zones.empty:
        return {"stop": fallback, "type": "original_invalidation_stop"}
    direction = _cell(row.get("direction_context")).upper()
    side = "BUY_SIDE" if direction == "DOWN" else "SELL_SIDE"
    frame = zones[zones.get("side", pd.Series(dtype=str)).astype(str) == side].copy()
    if frame.empty:
        return {"stop": fallback, "type": "original_invalidation_stop"}
    frame["_lower"] = pd.to_numeric(frame.get("price_lower"), errors="coerce")
    frame["_upper"] = pd.to_numeric(frame.get("price_upper"), errors="coerce")
    entry = _float(row.get("tradable_entry_anchor"))
    if direction == "DOWN":
        candidates = frame[frame["_lower"] >= entry]
        if candidates.empty:
            return {"stop": fallback, "type": "original_invalidation_stop"}
        selected = candidates.sort_values("_lower", kind="mergesort").iloc[0]
        return {"stop": float(selected["_upper"]), "type": "structural_zone_stop"}
    if direction == "UP":
        candidates = frame[frame["_upper"] <= entry]
        if candidates.empty:
            return {"stop": fallback, "type": "original_invalidation_stop"}
        selected = candidates.sort_values("_upper", ascending=False, kind="mergesort").iloc[0]
        return {"stop": float(selected["_lower"]), "type": "structural_zone_stop"}
    return {"stop": fallback, "type": "original_invalidation_stop"}


def _load_feed(feed_dir: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(feed_dir.glob("*.csv")):
        frame = pd.read_csv(path)
        columns = {str(column).lower(): column for column in frame.columns}
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(frame[columns["timestamp"]], errors="coerce", utc=True),
                    "open": pd.to_numeric(frame[columns["open"]], errors="coerce"),
                    "high": pd.to_numeric(frame[columns["high"]], errors="coerce"),
                    "low": pd.to_numeric(frame[columns["low"]], errors="coerce"),
                    "close": pd.to_numeric(frame[columns["close"]], errors="coerce"),
                    "source_file": path.name,
                    "is_synthetic": pd.to_numeric(frame[columns.get("issynthetic", "IsSynthetic")], errors="coerce").fillna(0)
                    if "issynthetic" in columns or "IsSynthetic" in frame.columns
                    else 0,
                }
            )
        )
    return pd.concat(frames, ignore_index=True, sort=False).dropna(subset=["timestamp", "close"]).sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _first_bar_at_or_after(feed: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    frame = feed[feed["timestamp"] >= ts]
    return None if frame.empty else frame.iloc[0]


def _first_bar_after(feed: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    frame = feed[feed["timestamp"] > ts]
    return None if frame.empty else frame.iloc[0]


def _source_window(feed: pd.DataFrame, row: dict[str, object]) -> pd.DataFrame:
    start = _parse_ts(row.get("source_window_start"))
    end = _parse_ts(row.get("source_window_end"))
    if pd.isna(start) or pd.isna(end):
        return pd.DataFrame()
    return feed[(feed["timestamp"] >= start) & (feed["timestamp"] <= end)].copy()


def _local_swing(feed: pd.DataFrame, formed_at: pd.Timestamp, minutes: int = 180) -> dict[str, float]:
    window = feed[(feed["timestamp"] >= formed_at - pd.Timedelta(minutes=minutes)) & (feed["timestamp"] <= formed_at)]
    if window.empty:
        return {"high": float("nan"), "low": float("nan")}
    return {"high": float(window["high"].max()), "low": float(window["low"].min())}


def _target_reference_text(row: dict[str, object]) -> str:
    value = _cell(row.get("target_reference"))
    if value:
        return value
    return _cell(row.get("target_reference_zone"))


def _parse_target_zone(value: object) -> dict[str, float] | None:
    text = _cell(value)
    match = re.search(r":(BUY_SIDE|SELL_SIDE):([0-9.]+)-([0-9.]+)", text)
    if not match:
        return None
    lower = _float(match.group(2))
    upper = _float(match.group(3))
    if pd.isna(lower) or pd.isna(upper):
        return None
    return {"lower": min(lower, upper), "upper": max(lower, upper)}


def _target_touch_mask(feed: pd.DataFrame, target: dict[str, float] | None) -> pd.Series:
    if target is None:
        return pd.Series(False, index=feed.index)
    high = pd.to_numeric(feed["high"], errors="coerce")
    low = pd.to_numeric(feed["low"], errors="coerce")
    return (high >= target["lower"]) & (low <= target["upper"])


def _target_distance(direction: str, entry: float, target: dict[str, float] | None) -> float:
    if target is None or pd.isna(entry):
        return float("nan")
    if direction == "DOWN":
        return entry - target["upper"] if target["upper"] <= entry else target["lower"] - entry
    if direction == "UP":
        return target["lower"] - entry if target["lower"] >= entry else entry - target["upper"]
    return float("nan")


def _tp1_price(direction: str, entry: float, stop_distance: float) -> float:
    if pd.isna(entry) or not _positive(stop_distance):
        return float("nan")
    return entry - stop_distance if direction == "DOWN" else entry + stop_distance if direction == "UP" else float("nan")


def _first_event(events: list[tuple[str, object]]) -> str:
    valid = [(name, _parse_ts(ts)) for name, ts in events if not pd.isna(_parse_ts(ts))]
    if not valid:
        return ""
    order = {"TARGET": 0, "TP1": 1, "BE": 2, "SELECTED_STOP": 3}
    valid.sort(key=lambda item: (item[1], order.get(item[0], 99)))
    return valid[0][0]


def _after(value: object, threshold: object) -> bool:
    ts = _parse_ts(value)
    cutoff = _parse_ts(threshold)
    return not pd.isna(ts) and not pd.isna(cutoff) and ts > cutoff


def _unresolved(direction: str, entry: float, selected_stop: float, target: dict[str, float] | None) -> bool:
    return direction not in {"UP", "DOWN"} or pd.isna(entry) or pd.isna(selected_stop) or target is None


def _valid_stop(direction: str, entry: float, stop: float) -> bool:
    if pd.isna(entry) or pd.isna(stop):
        return False
    return stop > entry if direction == "DOWN" else stop < entry if direction == "UP" else False


def _armed_high(setup: dict[str, object] | pd.Series) -> bool:
    return _cell(setup.get("trigger_status")).upper() == "ARMED" and _cell(setup.get("candidate_strength")).upper() == "HIGH"


def _evidence(setup: dict[str, object], path: dict[str, object], verdict: str) -> str:
    return (
        f"canonical_setup_builder_source=38V; no_38s_source_candidates=true; "
        f"setup_reference_used_as_entry=false; stop_type={_cell(setup.get('selected_research_stop_type'))}; "
        f"forward_rows_after_setup={path['forward_rows']}; manual_monitor_verdict={verdict}"
    )


def _counts_json(frame: pd.DataFrame, column: str) -> str:
    return json.dumps(dict(Counter(frame[column].astype(str))), sort_keys=True)


def _nested_counts_json(frame: pd.DataFrame, outer: str, inner: str) -> str:
    data: dict[str, dict[str, int]] = {}
    for outer_value, group in frame.groupby(outer, dropna=False):
        data[str(outer_value)] = dict(Counter(group[inner].astype(str)))
    return json.dumps(data, sort_keys=True)


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _parse_ts(value: object) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce", utc=True)


def _iso(value: object) -> str:
    ts = _parse_ts(value)
    if pd.isna(ts):
        return ""
    return ts.isoformat().replace("+00:00", "Z")


def _float(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if pd.notna(number) else default


def _round(value: object) -> object:
    number = _float(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _positive(value: float) -> bool:
    return not pd.isna(value) and value > 0


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


if __name__ == "__main__":
    main()
