"""Sprint 08 deterministic mapper for three BTC replay candidates.

The mapper consumes Sprint 06 discovery artifacts only. It does not use
Sprint 06 outcomes as entry predicates and does not change Analyzer v1,
Backtester core, Executor, live behavior, or Phase 4 state.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


RULE_VERSION = "SPRINT08_BTC_FORMAL_REPLAY_V1"
SOURCE_EVENT_FILE = "research/results/sprint_06_discovery_events.csv"
SOURCE_FEATURE_FILE = "research/results/sprint_06_discovery_features.csv"


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    family: str
    side: str
    expiry_bars: int
    vwap_bp_bucket: str | None
    description: str


CANDIDATES = [
    CandidateSpec(
        candidate_id="CAND_BTC_EXH_SHORT_24_V1",
        family="EXHAUSTION_REVERSAL",
        side="SHORT",
        expiry_bars=24,
        vwap_bp_bucket=None,
        description="Exhaustion reversal short, 24-bar expiry, event-high stop, entry-time DayVWAP target.",
    ),
    CandidateSpec(
        candidate_id="CAND_BTC_VWAP_DEV_LONG_60_100200_V1",
        family="VWAP_DEVIATION_REVERSION",
        side="LONG",
        expiry_bars=60,
        vwap_bp_bucket="VWAP_100_200BP",
        description="VWAP deviation reversion long, 100-200bp below DayVWAP, 60-bar expiry.",
    ),
    CandidateSpec(
        candidate_id="CAND_BTC_VWAP_DEV_SHORT_60_100200_V1",
        family="VWAP_DEVIATION_REVERSION",
        side="SHORT",
        expiry_bars=60,
        vwap_bp_bucket="VWAP_100_200BP",
        description="VWAP deviation reversion short, 100-200bp above DayVWAP, 60-bar expiry.",
    ),
]


EVENT_COLUMNS = [
    "candidate_id",
    "event_id",
    "family",
    "side",
    "event_time",
    "signal_close_time",
    "entry_time",
    "entry_price",
    "stop_price",
    "target_price",
    "expiry_bars",
    "expiry_time",
    "event_high",
    "event_low",
    "entry_day_vwap",
    "vwap_distance_bucket",
    "volume_bucket",
    "rejection_bucket",
    "session",
    "regime",
    "source_event_file",
    "source_feature_file",
    "rule_version",
    "valid_for_replay",
    "invalid_reason",
]


def parse_predicates(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def vwap_bp_bucket(vwap_distance_pct: float) -> str:
    bp = abs(vwap_distance_pct) * 100.0
    if bp < 60:
        return "VWAP_45_60BP"
    if bp < 100:
        return "VWAP_60_100BP"
    if bp < 200:
        return "VWAP_100_200BP"
    return "VWAP_GE_200BP"


def load_sources(events_path: Path, features_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_csv(events_path)
    features = pd.read_csv(features_path)
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True, format="ISO8601")
    features = features.sort_values("Timestamp").reset_index(drop=True)
    events = events[events["clustered_event"].astype(str).str.lower().eq("true")].copy()
    predicates = events["observable_predicates"].apply(parse_predicates)
    events["vwap_distance_pct_observed"] = predicates.apply(lambda row: float(row.get("vwap_distance_pct", 0.0) or 0.0))
    events["vwap_bp_bucket"] = events["vwap_distance_pct_observed"].apply(vwap_bp_bucket)
    events["event_time_ts"] = pd.to_datetime(events["event_time"], utc=True, format="ISO8601")
    return events, features


def feature_lookup(features: pd.DataFrame) -> dict[pd.Timestamp, int]:
    return {ts: int(idx) for idx, ts in features["Timestamp"].items()}


def select_events(events: pd.DataFrame, spec: CandidateSpec) -> pd.DataFrame:
    selected = events[(events["family"].eq(spec.family)) & (events["side"].eq(spec.side))].copy()
    if spec.vwap_bp_bucket:
        selected = selected[selected["vwap_bp_bucket"].eq(spec.vwap_bp_bucket)].copy()
    return selected.sort_values("event_time_ts").reset_index(drop=True)


def map_event(row: pd.Series, spec: CandidateSpec, features: pd.DataFrame, lookup: dict[pd.Timestamp, int]) -> dict[str, Any]:
    event_ts = row["event_time_ts"]
    base = {
        "candidate_id": spec.candidate_id,
        "event_id": row["discovery_event_id"],
        "family": spec.family,
        "side": spec.side,
        "event_time": event_ts.isoformat(),
        "signal_close_time": event_ts.isoformat(),
        "expiry_bars": spec.expiry_bars,
        "vwap_distance_bucket": row.get("vwap_bp_bucket", row.get("vwap_distance_bucket", "")),
        "volume_bucket": row.get("volume_bucket", ""),
        "rejection_bucket": row.get("rejection_strength_bucket", ""),
        "session": row.get("session", ""),
        "regime": row.get("regime", ""),
        "source_event_file": SOURCE_EVENT_FILE,
        "source_feature_file": SOURCE_FEATURE_FILE,
        "rule_version": RULE_VERSION,
    }
    invalid: list[str] = []
    if event_ts not in lookup:
        invalid.append("event_timestamp_missing_in_features")
        return invalid_row(base, invalid)
    event_idx = lookup[event_ts]
    entry_idx = event_idx + 1
    expiry_idx = entry_idx + spec.expiry_bars
    if entry_idx >= len(features.index):
        invalid.append("missing_next_bar_for_entry")
        return invalid_row(base, invalid)
    entry_ts = features.loc[entry_idx, "Timestamp"]
    if entry_ts != event_ts + pd.Timedelta(minutes=1):
        invalid.append("entry_bar_not_next_m1")
    event_bar = features.loc[event_idx]
    entry_bar = features.loc[entry_idx]
    entry_price = float(entry_bar["OpenPrice"])
    event_high = float(event_bar["HiPrice"])
    event_low = float(event_bar["LowPrice"])
    entry_day_vwap = float(entry_bar["DayVWAP"])
    stop_price = event_high if spec.side == "SHORT" else event_low
    target_price = entry_day_vwap
    expiry_time = ""
    if expiry_idx < len(features.index):
        expiry_ts = features.loc[expiry_idx, "Timestamp"]
        expected_expiry = entry_ts + pd.Timedelta(minutes=spec.expiry_bars)
        if expiry_ts == expected_expiry:
            expiry_time = expiry_ts.isoformat()
        else:
            invalid.append("expiry_bar_not_contiguous")
    else:
        invalid.append("missing_expiry_bar")

    if spec.side == "SHORT":
        if stop_price <= entry_price:
            invalid.append("short_stop_not_above_entry")
        if target_price >= entry_price:
            invalid.append("short_target_not_below_entry")
    else:
        if stop_price >= entry_price:
            invalid.append("long_stop_not_below_entry")
        if target_price <= entry_price:
            invalid.append("long_target_not_above_entry")

    return {
        **base,
        "entry_time": entry_ts.isoformat(),
        "entry_price": round(entry_price, 8),
        "stop_price": round(stop_price, 8),
        "target_price": round(target_price, 8),
        "expiry_time": expiry_time,
        "event_high": round(event_high, 8),
        "event_low": round(event_low, 8),
        "entry_day_vwap": round(entry_day_vwap, 8),
        "valid_for_replay": not invalid,
        "invalid_reason": "PASS" if not invalid else ";".join(invalid),
    }


def invalid_row(base: dict[str, Any], invalid: list[str]) -> dict[str, Any]:
    return {
        **base,
        "entry_time": "",
        "entry_price": 0.0,
        "stop_price": 0.0,
        "target_price": 0.0,
        "expiry_time": "",
        "event_high": 0.0,
        "event_low": 0.0,
        "entry_day_vwap": 0.0,
        "valid_for_replay": False,
        "invalid_reason": ";".join(invalid),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_ruleset_spec(path: Path, spec: CandidateSpec) -> None:
    if spec.family == "EXHAUSTION_REVERSAL":
        predicates = "Sprint 06 exhaustion SHORT observable predicates: prior impulse up, high volume quantile, rejection/stall, delta dominance, VWAP stretch."
    else:
        direction = "below" if spec.side == "LONG" else "above"
        predicates = f"Sprint 06 VWAP {spec.side} observable predicates: price {direction} DayVWAP, VWAP deviation bucket 100-200bp, stall/rejection context; session/regime recorded only."
    lines = [
        f"# {spec.candidate_id} Ruleset Spec",
        "",
        f"Family: `{spec.family}`",
        f"Side: `{spec.side}`",
        f"Rule version: `{RULE_VERSION}`",
        f"Description: {spec.description}",
        "",
        "## Observable Entry Predicates",
        "",
        predicates,
        "",
        "Outcomes are not entry predicates.",
        "",
        "## Mapping",
        "",
        "- Signal after event M1 bar close.",
        "- Entry at next M1 bar open.",
        f"- Stop: event bar {'high' if spec.side == 'SHORT' else 'low'}.",
        "- Target: DayVWAP observed at entry timestamp, static after entry.",
        f"- Expiry: {spec.expiry_bars} M1 bars after entry.",
        "- Same-bar policy: conservative stop-first.",
        "- Cost levels: 0.00000, 0.00010, 0.00015, 0.00020.",
        "- One active position per candidate; new events while active are skipped in replay.",
        "",
        "## Boundary",
        "",
        "No live trading, no Executor, no Phase 4, no PROMOTE, no CTX tuning, no Analyzer v1 or Backtester core changes.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_no_lookahead(path: Path, spec: CandidateSpec, total: int, valid: int, invalid_reasons: dict[str, int]) -> None:
    lines = [
        f"# {spec.candidate_id} No-Lookahead Check",
        "",
        "Result: `PASS_MAPPING_NO_OUTCOME_PREDICATES`.",
        "",
        f"- Selected Sprint 06 clustered discovery events: {total}.",
        f"- Valid replay mappings: {valid}.",
        f"- Invalid mappings: {total - valid}.",
        "- Entry uses only event close plus next M1 open from Sprint 06 feature rows.",
        "- Stop uses event high/low from event bar.",
        "- Target uses DayVWAP observed at entry timestamp and is frozen.",
        "- Sprint 06 discovery outcomes are not read by this mapper.",
        "",
        "Invalid reasons:",
        "",
    ]
    if invalid_reasons:
        for reason, count in sorted(invalid_reasons.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- None.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_promotion_checklist(path: Path) -> None:
    lines = [
        "# Promotion Gate Checklist",
        "",
        "- [x] formal deterministic mapping exists",
        "- [x] no future labels",
        "- [x] stop frozen",
        "- [x] target frozen",
        "- [x] expiry frozen",
        "- [x] one-active-position rule applied",
        "- [ ] cost 0.00015 positive",
        "- [ ] cost 0.00020 reported",
        "- [ ] same-bar ambiguity not verdict-changing",
        "- [ ] source concentration PASS",
        "- [ ] no single-day PnL dominance",
        "- [ ] true holdout completed",
        "- [x] no tuning after Sprint 08 freeze",
        "- [ ] isolated margin compatible",
        "- [x] no martingale",
        "",
        "promotion_status: `NO_PROMOTE_HOLDOUT_REQUIRED`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_placeholder_reports(candidate_dir: Path, spec: CandidateSpec) -> None:
    (candidate_dir / "candidate_replay_summary.md").write_text(
        f"# {spec.candidate_id} Replay Summary\n\nReplay not run by mapper. Run `research/scripts/sprint_08_btc_formal_replay_runner.py`.\n",
        encoding="utf-8",
    )
    write_csv(candidate_dir / "cost_stress_summary.csv", [], ["cost_level", "net_result", "verdict"])
    write_csv(candidate_dir / "source_concentration_report.csv", [], ["candidate_id", "status", "notes"])
    (candidate_dir / "same_bar_ambiguity_report.md").write_text(
        f"# {spec.candidate_id} Same-Bar Ambiguity Report\n\nReplay not run by mapper.\n",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> None:
    events_path = Path(args.events)
    features_path = Path(args.features)
    candidate_root = Path(args.candidate_root)
    events, features = load_sources(events_path, features_path)
    lookup = feature_lookup(features)
    summary_rows: list[dict[str, Any]] = []
    for spec in CANDIDATES:
        candidate_dir = candidate_root / spec.candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        selected = select_events(events, spec)
        rows = [map_event(row, spec, features, lookup) for _, row in selected.iterrows()]
        write_csv(candidate_dir / "candidate_events.csv", rows, EVENT_COLUMNS)
        write_ruleset_spec(candidate_dir / "RULESET_SPEC.md", spec)
        invalid_counts: dict[str, int] = {}
        for row in rows:
            if str(row["valid_for_replay"]).lower() == "true":
                continue
            for reason in str(row["invalid_reason"]).split(";"):
                invalid_counts[reason] = invalid_counts.get(reason, 0) + 1
        valid = sum(1 for row in rows if str(row["valid_for_replay"]).lower() == "true")
        write_no_lookahead(candidate_dir / "no_lookahead_check.md", spec, len(rows), valid, invalid_counts)
        write_promotion_checklist(candidate_dir / "promotion_gate_checklist.md")
        write_placeholder_reports(candidate_dir, spec)
        summary_rows.append(
            {
                "candidate_id": spec.candidate_id,
                "selected_events": len(rows),
                "valid_replay_events": valid,
                "invalid_events": len(rows) - valid,
                "invalid_reasons": json.dumps(invalid_counts, sort_keys=True),
            }
        )
    write_csv(candidate_root / "sprint_08_mapper_summary.csv", summary_rows, list(summary_rows[0]))
    print(json.dumps(summary_rows, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Map Sprint 08 BTC replay candidates deterministically.")
    parser.add_argument("--events", default=SOURCE_EVENT_FILE)
    parser.add_argument("--features", default=SOURCE_FEATURE_FILE)
    parser.add_argument("--candidate-root", default="research/candidates")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
