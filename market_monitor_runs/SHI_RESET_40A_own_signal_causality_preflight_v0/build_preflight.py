"""Audit saved 38V/38W1 availability; does not generate signals or run trades."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/full_feed_setup_builder_candidates.csv"
OUTCOMES = ROOT / "market_monitor_runs/SHI_RESET_38W1_fix_chronological_tp1_stop_labels_v0/setup_builder_outcome_replay_results.csv"
ZONES = ROOT / "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/support/selected_zones/selected_zones.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sources = [CANDIDATES, OUTCOMES, ZONES]
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in sources}
    candidates = pd.read_csv(CANDIDATES)
    outcomes = pd.read_csv(OUTCOMES)
    zones = pd.read_csv(ZONES)
    assert len(candidates) == len(outcomes) == 51
    assert candidates.setup_id.is_unique and outcomes.setup_id.is_unique
    assert set(candidates.setup_id) == set(outcomes.setup_id)
    visible = zones[zones.visible_on_snapshot.astype(str).str.lower().eq("true")]
    assert visible.zone_id.is_unique
    visible = visible.set_index("zone_id")
    joined = candidates.drop(columns=["tradable_entry_anchor"]).merge(
        outcomes[["setup_id", "tradable_entry_anchor", "target_zone_lower", "target_zone_upper", "outcome_label"]],
        on="setup_id", validate="one_to_one",
    )
    rows = []
    for row in joined.to_dict("records"):
        formed = pd.Timestamp(row["setup_formed_at"])
        state_end = pd.Timestamp(row["end_timestamp"])
        target_id = row["target_reference_zone"].split(":")[0]
        zone = visible.loc[target_id]
        assert math.isclose(row["target_zone_lower"], zone.price_lower, abs_tol=1e-8, rel_tol=0)
        assert math.isclose(row["target_zone_upper"], zone.price_upper, abs_tol=1e-8, rel_tol=0)
        later_snapshot = pd.Timestamp(zone.source_day, tz="UTC") > formed.normalize()
        entry = float(row["tradable_entry_anchor"])
        directional = (
            row["target_zone_lower"] > entry if row["direction_context"] == "UP"
            else row["target_zone_upper"] < entry
        )
        rows.append({
            "setup_id": row["setup_id"],
            "setup_type": row["setup_type"],
            "recorded_setup_formed_at": formed.isoformat(),
            "consumed_state_end": state_end.isoformat(),
            "state_ends_after_recorded_setup": bool(state_end > formed),
            "state_availability_delay_hours": (state_end - formed).total_seconds() / 3600,
            "target_zone_id": target_id,
            "target_snapshot_source_day": zone.source_day,
            "target_snapshot_later_calendar_day": bool(later_snapshot),
            "target_directionally_valid_at_replay_entry": bool(directional),
            "target_as_of_availability_proven": False,
            "historical_outcome_label": row["outcome_label"],
        })
    checks = pd.DataFrame(rows)
    checks.to_csv(OUT / "candidate_availability_checks.csv", index=False)
    families = pd.crosstab(outcomes.setup_type, outcomes.outcome_label).reindex(
        columns=["STOP_BEFORE_TP1", "TP1_THEN_BE", "TP1_THEN_TARGET", "TP1_ONLY_NO_FOLLOWUP"],
        fill_value=0,
    )
    families.to_csv(OUT / "historical_family_outcome_counts.csv")
    summary = {
        "task_id": "SHI_RESET_40A_OWN_SIGNAL_CAUSALITY_PREFLIGHT",
        "verdict": "SAVED_COHORT_REJECTED_FOR_CAUSAL_FINANCIAL_VALIDATION",
        "research_only": True,
        "candidate_count": len(checks),
        "state_ends_after_recorded_setup": int(checks.state_ends_after_recorded_setup.sum()),
        "max_state_availability_delay_hours": float(checks.state_availability_delay_hours.max()),
        "target_snapshot_later_calendar_day": int(checks.target_snapshot_later_calendar_day.sum()),
        "directionally_invalid_target_at_replay_entry": int((~checks.target_directionally_valid_at_replay_entry).sum()),
        "family_outcomes": families.to_dict(orient="index"),
        "profitability_search_performed": False,
        "financial_backtester_run": False,
        "new_signal_generation": False,
        "raw_feed_read_or_modified": False,
        "source_hashes": hashes,
        "limitations": [
            "source_day identifies the selected snapshot, not the zone's original formation time",
            "a later target snapshot alone does not prove the geometry first appeared in the future",
            "49 backward state timestamps are confirmed by the daily metric computation and builder timestamp assignment",
            "the two remaining rows are not validated: the full-period zone selection has no per-signal availability contract",
            "historical outcome labels are preserved as forensic evidence, not tradable or net-return results",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert hashes == {p.relative_to(ROOT).as_posix(): sha256(p) for p in sources}
    print(json.dumps({k: v for k, v in summary.items() if k not in {"source_hashes", "limitations", "family_outcomes"}}, indent=2))


if __name__ == "__main__":
    main()
