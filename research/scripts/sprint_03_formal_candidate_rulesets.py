"""Sprint 03 formal candidate mapper and pooled replay runner.

This script turns two frozen short-side research surfaces into deterministic
candidate_events.csv files and Backtester-compatible Phase 3 mapping artifacts.
It does not tune thresholds, does not use future labels, and does not modify
Analyzer or Backtester core code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backtester.engine import ConservativeSameBarPolicy
from backtester.orchestrator import run_backtester


COST_LEVELS = (0.0, 0.00010, 0.00015, 0.00020)
HARD_GATE_COST = 0.00015
WARNING_GATE_COST = 0.00020
TAKE_PROFIT_R = 1.5
EXPIRY_BARS = 12
SYMBOL = "BTCUSDT"
REPLAY_SEMANTICS_VERSION = "REPLAY_V0_1"
STOP_MODEL = "REFERENCE_LEVEL_HARD_STOP"
SAME_BAR_CONSERVATIVE = "SAME_BAR_CONSERVATIVE_V0_1"
SAME_BAR_PESSIMISTIC = "SAME_BAR_PESSIMISTIC_STOP_WINS_V0_1"
SAME_BAR_OPTIMISTIC = "SAME_BAR_OPTIMISTIC_TARGET_WINS_V0_1"
GAP_START = date(2026, 4, 23)
GAP_END = date(2026, 5, 6)
FORBIDDEN_LOOKAHEAD_TOKENS = (
    "H2_Post",
    "Post12",
    "FullFade",
    "NoFade",
    "TradeReturn",
    "TradePnl",
    "ExitTs",
    "ExitReason",
    "ExitReasonCategory",
    "Win",
)
CANDIDATE_EVENT_COLUMNS = [
    "candidate_event_id",
    "candidate_id",
    "symbol",
    "timeframe",
    "side",
    "setup_timestamp",
    "entry_timestamp",
    "entry_price",
    "stop_price",
    "exit_rule_id",
    "source_analyzer_run",
    "source_sidecar_file",
    "rule_version",
    "feature_snapshot_hash",
    "eligible_reason",
    "source_setup_id",
    "original_setup_timestamp",
    "reference_event_timestamp",
    "reference_level",
    "target_price",
    "risk_distance",
    "take_profit_r",
    "expiry_bars",
]


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    rule_version: str
    setup_type: str
    timeframe: str
    source_sidecar_file: str
    eligible_event_types: str
    source_report: str
    group_type: str
    group_value: str
    ruleset_id: str


CTX_SPEC = CandidateSpec(
    candidate_id="CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1",
    rule_version="SPRINT03_CTX_GE2_ENTRY_DELAY_1_V1",
    setup_type="SPRINT03_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1",
    timeframe="H1_H2_CONTEXT_M1_REPLAY",
    source_sidecar_file="research/results/short_reclaim_timing_survival_diagnostic_trades_2026-05-03.csv",
    eligible_event_types="FAILED_BREAK_UP|IMPULSE_UP",
    source_report="sprint_03_formal_ruleset",
    group_type="CandidateId",
    group_value="CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1",
    ruleset_id="RULESET_SPRINT03_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1_BASE",
)

DEEP_SPEC = CandidateSpec(
    candidate_id="CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6",
    rule_version="SPRINT03_SHORT_DEEP_RECLAIM_GT_0_6_V1",
    setup_type="SPRINT03_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6",
    timeframe="H2_M1_REPLAY",
    source_sidecar_file="research/results/impulse_fade_short_deep_reclaim_cluster_detail_2026-03-17_to_2026-05-12.csv",
    eligible_event_types="IMPULSE_UP",
    source_report="sprint_03_formal_ruleset",
    group_type="CandidateId",
    group_value="CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6",
    ruleset_id="RULESET_SPRINT03_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6_BASE",
)


class FixedRoundTripCostModel:
    """Apply a deterministic round-trip return penalty as half-spread per side."""

    def __init__(self, cost_level: float) -> None:
        self.cost_level = float(cost_level)
        self.half = self.cost_level / 2.0

    def apply(
        self,
        *,
        ruleset_row: pd.Series,
        event_type: str,
        timestamp: pd.Timestamp,
        price_raw: float | None,
        direction: str,
    ) -> dict[str, Any]:
        if price_raw is None:
            return {
                "price_effective": None,
                "cost_amount": 0.0,
                "notes": f"cost_model_hook=ROUND_TRIP_BPS:{self.cost_level:.5f}",
            }
        side = str(direction).upper()
        px = float(price_raw)
        if event_type == "ENTRY_ACTIVATED":
            if side == "SHORT":
                effective = px * (1.0 - self.half)
            else:
                effective = px * (1.0 + self.half)
        elif event_type == "CLOSE_RESOLVED":
            if side == "SHORT":
                effective = px * (1.0 + self.half)
            else:
                effective = px * (1.0 - self.half)
        else:
            effective = px
        return {
            "price_effective": effective,
            "cost_amount": abs(effective - px),
            "notes": f"cost_model_hook=ROUND_TRIP_BPS:{self.cost_level:.5f}",
        }


class StopWinsSameBarPolicy:
    def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
        return "STOP_WINS"


class TargetWinsSameBarPolicy:
    def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
        return "TARGET_WINS"


def cost_model_id(cost_level: float) -> str:
    return f"COST_ROUND_TRIP_{str(f'{cost_level:.5f}').replace('.', '_')}"


def cost_token(cost_level: float) -> str:
    return str(f"{cost_level:.5f}").replace(".", "_")


def parse_run_date(path: Path) -> date | None:
    try:
        return date.fromisoformat(path.name[:10])
    except ValueError:
        return None


def iter_dates(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def load_source_analyzer_dirs(analyzer_runs_root: Path, recovered_gap_root: Path) -> list[Path]:
    by_day: dict[date, Path] = {}
    if analyzer_runs_root.exists():
        for path in sorted(analyzer_runs_root.iterdir()):
            if not path.is_dir() or not (path / "analyzer_setups.csv").exists():
                continue
            day = parse_run_date(path)
            if day is None or GAP_START <= day <= GAP_END:
                continue
            by_day.setdefault(day, path)
    if recovered_gap_root.exists():
        for path in sorted(recovered_gap_root.iterdir()):
            if not path.is_dir() or not (path / "analyzer_setups.csv").exists():
                continue
            day = parse_run_date(path)
            if day is not None:
                by_day[day] = path
    return [by_day[day] for day in sorted(by_day)]


def raw_path_for_day(day: date, feed_root: Path, recovered_root: Path) -> Path:
    recovered = recovered_root / f"{day.isoformat()}.csv"
    primary = feed_root / f"{day.isoformat()}.csv"
    if GAP_START <= day <= GAP_END and recovered.exists():
        return recovered
    return primary


def load_raw_window(days: list[date], feed_root: Path, recovered_root: Path) -> pd.DataFrame:
    if not days:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for day in iter_dates(min(days), max(days)):
        path = raw_path_for_day(day, feed_root, recovered_root)
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True, errors="raise")
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True, sort=False)
    raw = raw.sort_values("Timestamp", kind="mergesort").drop_duplicates("Timestamp").reset_index(drop=True)
    return raw


def bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def numeric(value: object) -> float | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def ctx_spike_count(row: pd.Series) -> int:
    fields = (
        "CtxRelVolumeSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxOISpike_v1",
        "CtxLiqSpike_v1",
        "CtxWickReclaim_v1",
    )
    return sum(1 for field in fields if bool_value(row.get(field)))


def next_timestamp(raw: pd.DataFrame, ts: pd.Timestamp, offset: int = 1) -> pd.Timestamp | None:
    idx = raw.index[raw["Timestamp"] == ts]
    if len(idx) != 1:
        return None
    target = int(idx[0]) + offset
    if target < 0 or target >= len(raw.index):
        return None
    return pd.Timestamp(raw.loc[target, "Timestamp"])


def raw_row_at(raw_by_ts: dict[pd.Timestamp, pd.Series], ts: pd.Timestamp) -> pd.Series | None:
    return raw_by_ts.get(pd.Timestamp(ts))


def feature_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_analyzer_frame(path: Path, filename: str) -> pd.DataFrame:
    file_path = path / filename
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


def build_common_event(
    *,
    spec: CandidateSpec,
    source_dir: Path,
    source_setup_id: str,
    setup_timestamp: pd.Timestamp,
    original_setup_timestamp: pd.Timestamp,
    reference_event_ts: pd.Timestamp | None,
    reference_level: float,
    raw: pd.DataFrame,
    raw_by_ts: dict[pd.Timestamp, pd.Series],
    eligible_reason: str,
    feature_payload: dict[str, Any],
) -> dict[str, Any] | None:
    entry_timestamp = next_timestamp(raw, setup_timestamp, 1)
    if entry_timestamp is None:
        return None
    entry_bar = raw_row_at(raw_by_ts, entry_timestamp)
    if entry_bar is None:
        return None
    entry_price = numeric(entry_bar.get("Open"))
    if entry_price is None:
        return None
    stop_price = float(reference_level)
    risk_distance = stop_price - entry_price
    if risk_distance <= 0:
        return None
    target_price = entry_price - (TAKE_PROFIT_R * risk_distance)
    event_id = f"{spec.candidate_id}::{source_dir.name}::{source_setup_id}::{setup_timestamp.isoformat()}"
    return {
        "candidate_event_id": hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:24],
        "candidate_id": spec.candidate_id,
        "symbol": SYMBOL,
        "timeframe": spec.timeframe,
        "side": "SHORT",
        "setup_timestamp": setup_timestamp.isoformat(),
        "entry_timestamp": entry_timestamp.isoformat(),
        "entry_price": round(float(entry_price), 8),
        "stop_price": round(float(stop_price), 8),
        "exit_rule_id": f"FIXED_R_MULTIPLE_{TAKE_PROFIT_R}_OR_EXPIRY_{EXPIRY_BARS}_BARS",
        "source_analyzer_run": source_dir.name,
        "source_sidecar_file": spec.source_sidecar_file,
        "rule_version": spec.rule_version,
        "feature_snapshot_hash": feature_hash(feature_payload),
        "eligible_reason": eligible_reason,
        "source_setup_id": source_setup_id,
        "original_setup_timestamp": original_setup_timestamp.isoformat(),
        "reference_event_timestamp": "" if reference_event_ts is None else reference_event_ts.isoformat(),
        "reference_level": round(float(reference_level), 8),
        "target_price": round(float(target_price), 8),
        "risk_distance": round(float(risk_distance), 8),
        "take_profit_r": TAKE_PROFIT_R,
        "expiry_bars": EXPIRY_BARS,
    }


def build_ctx_candidate_events(source_dirs: list[Path], raw: pd.DataFrame) -> pd.DataFrame:
    raw_by_ts = {pd.Timestamp(row.Timestamp): pd.Series(row._asdict()) for row in raw.itertuples(index=False)}
    rows: list[dict[str, Any]] = []
    for source_dir in source_dirs:
        setups = load_analyzer_frame(source_dir, "analyzer_setups.csv")
        if setups.empty:
            continue
        setups["SetupBarTs"] = pd.to_datetime(setups["SetupBarTs"], utc=True, errors="coerce")
        mask = (
            setups["Direction"].astype(str).str.upper().eq("SHORT")
            & setups["SetupType"].astype(str).str.contains("RECLAIM", na=False)
        )
        selected = setups.loc[mask].copy()
        selected["_ctx_spike_count"] = selected.apply(ctx_spike_count, axis=1)
        selected = selected.loc[selected["_ctx_spike_count"] >= 2].copy()
        for _, setup in selected.iterrows():
            original_ts = pd.Timestamp(setup["SetupBarTs"])
            shifted_ts = next_timestamp(raw, original_ts, 1)
            if shifted_ts is None:
                continue
            reference_level = numeric(setup.get("ReferenceLevel"))
            if reference_level is None:
                continue
            feature_payload = {
                "candidate_id": CTX_SPEC.candidate_id,
                "source_setup_id": str(setup.get("SetupId")),
                "original_setup_timestamp": original_ts.isoformat(),
                "setup_timestamp": shifted_ts.isoformat(),
                "reference_level": reference_level,
                "ctx_spike_count": int(setup["_ctx_spike_count"]),
                "CtxRelVolumeSpike_v1": bool_value(setup.get("CtxRelVolumeSpike_v1")),
                "CtxDeltaSpike_v1": bool_value(setup.get("CtxDeltaSpike_v1")),
                "CtxOISpike_v1": bool_value(setup.get("CtxOISpike_v1")),
                "CtxLiqSpike_v1": bool_value(setup.get("CtxLiqSpike_v1")),
                "CtxWickReclaim_v1": bool_value(setup.get("CtxWickReclaim_v1")),
                "entry_delay_bars": 1,
            }
            row = build_common_event(
                spec=CTX_SPEC,
                source_dir=source_dir,
                source_setup_id=str(setup.get("SetupId")),
                setup_timestamp=shifted_ts,
                original_setup_timestamp=original_ts,
                reference_event_ts=pd.to_datetime(setup.get("ReferenceEventTs"), utc=True, errors="coerce"),
                reference_level=float(reference_level),
                raw=raw,
                raw_by_ts=raw_by_ts,
                eligible_reason="ctx_spike_count>=2;entry_delay_1;no_future_labels",
                feature_payload=feature_payload,
            )
            if row is not None:
                rows.append(row)
    if not rows:
        return pd.DataFrame(columns=CANDIDATE_EVENT_COLUMNS)
    return pd.DataFrame(rows).sort_values(["setup_timestamp", "candidate_event_id"], kind="mergesort").reset_index(drop=True)


def build_deep_candidate_events(source_dirs: list[Path], raw: pd.DataFrame) -> pd.DataFrame:
    raw_by_ts = {pd.Timestamp(row.Timestamp): pd.Series(row._asdict()) for row in raw.itertuples(index=False)}
    rows: list[dict[str, Any]] = []
    for source_dir in source_dirs:
        setups = load_analyzer_frame(source_dir, "analyzer_setups.csv")
        if setups.empty:
            continue
        setups["SetupBarTs"] = pd.to_datetime(setups["SetupBarTs"], utc=True, errors="coerce")
        if "ReferenceEventTs" in setups.columns:
            setups["ReferenceEventTs"] = pd.to_datetime(setups["ReferenceEventTs"], utc=True, errors="coerce")
        mask = (
            setups["Direction"].astype(str).str.upper().eq("SHORT")
            & setups["SetupType"].astype(str).eq("IMPULSE_FADE_RECLAIM_SHORT_V1")
        )
        selected = setups.loc[mask].copy()
        for _, setup in selected.iterrows():
            setup_ts = pd.Timestamp(setup["SetupBarTs"])
            ref_ts_raw = setup.get("ReferenceEventTs")
            if pd.isna(ref_ts_raw):
                continue
            ref_ts = pd.Timestamp(ref_ts_raw)
            setup_bar = raw_row_at(raw_by_ts, setup_ts)
            impulse_bar = raw_row_at(raw_by_ts, ref_ts)
            reference_level = numeric(setup.get("ReferenceLevel"))
            if setup_bar is None or impulse_bar is None or reference_level is None:
                continue
            setup_close = numeric(setup_bar.get("Close"))
            setup_high = numeric(setup_bar.get("High"))
            setup_low = numeric(setup_bar.get("Low"))
            impulse_high = numeric(impulse_bar.get("High"))
            impulse_low = numeric(impulse_bar.get("Low"))
            if None in {setup_close, setup_high, setup_low, impulse_high, impulse_low}:
                continue
            impulse_range = float(impulse_high) - float(impulse_low)
            setup_range = float(setup_high) - float(setup_low)
            if impulse_range <= 0 or setup_range <= 0:
                continue
            reclaim_depth_usd = float(reference_level) - float(setup_close)
            reclaim_depth_to_impulse = reclaim_depth_usd / impulse_range
            reclaim_depth_to_setup = reclaim_depth_usd / setup_range
            setup_location_in_impulse = (float(setup_close) - float(impulse_low)) / impulse_range
            if not reclaim_depth_to_impulse > 0.6:
                continue
            feature_payload = {
                "candidate_id": DEEP_SPEC.candidate_id,
                "source_setup_id": str(setup.get("SetupId")),
                "setup_timestamp": setup_ts.isoformat(),
                "reference_event_timestamp": ref_ts.isoformat(),
                "reference_level": float(reference_level),
                "setup_close": float(setup_close),
                "impulse_high": float(impulse_high),
                "impulse_low": float(impulse_low),
                "reclaim_depth_to_impulse": reclaim_depth_to_impulse,
                "threshold": 0.6,
            }
            row = build_common_event(
                spec=DEEP_SPEC,
                source_dir=source_dir,
                source_setup_id=str(setup.get("SetupId")),
                setup_timestamp=setup_ts,
                original_setup_timestamp=setup_ts,
                reference_event_ts=ref_ts,
                reference_level=float(reference_level),
                raw=raw,
                raw_by_ts=raw_by_ts,
                eligible_reason="ReclaimDepthToImpulseRange>0.6;no_future_labels",
                feature_payload=feature_payload,
            )
            if row is not None:
                row["ReclaimDepthUsd"] = round(reclaim_depth_usd, 8)
                row["ReclaimDepthToImpulseRange"] = round(reclaim_depth_to_impulse, 10)
                row["ReclaimDepthToSetupRange"] = round(reclaim_depth_to_setup, 10)
                row["SetupCloseLocationInImpulseRange"] = round(setup_location_in_impulse, 10)
                rows.append(row)
    if not rows:
        return pd.DataFrame(columns=CANDIDATE_EVENT_COLUMNS)
    return pd.DataFrame(rows).sort_values(["setup_timestamp", "candidate_event_id"], kind="mergesort").reset_index(drop=True)


def write_candidate_events(candidate_dir: Path, events: pd.DataFrame) -> Path:
    path = candidate_dir / "candidate_events.csv"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(path, index=False)
    return path


def no_lookahead_check(events: pd.DataFrame, candidate_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    joined_columns = " ".join(events.columns.astype(str).tolist())
    for token in FORBIDDEN_LOOKAHEAD_TOKENS:
        if token in joined_columns:
            issues.append(f"forbidden token in candidate_events columns: {token}")
    for column in ("eligible_reason", "rule_version"):
        if column in events.columns:
            values = " ".join(events[column].astype(str).tolist())
            for token in FORBIDDEN_LOOKAHEAD_TOKENS:
                if token in values:
                    issues.append(f"forbidden token in {column}: {token}")
    if events.empty:
        issues.append("candidate_events is empty")
    result = {
        "status": "PASS" if not issues else "FAIL",
        "events": int(len(events.index)),
        "issues": issues,
    }
    lines = [
        "# No-Lookahead Check",
        "",
        f"Status: `{result['status']}`",
        f"Candidate events: {result['events']}",
        "",
        "## Checks",
        "",
        "- Entry predicates use only setup-time/context/depth fields.",
        "- Future/outcome fields such as `H2_Post*`, `TradeReturn*`, `TradePnl`, `ExitTs`, `ExitReason`, `Win*`, `FullFade`, and `NoFade` are forbidden from candidate_events.",
        "- `feature_snapshot_hash` is built from observable feature payload only.",
        "",
        "## Issues",
        "",
    ]
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- none")
    (candidate_dir / "no_lookahead_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def write_artifact_bundle(
    *,
    artifact_dir: Path,
    spec: CandidateSpec,
    events: pd.DataFrame,
    raw: pd.DataFrame,
    candidate_events_path: Path,
    freeze_timestamp: str,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    raw.to_csv(artifact_dir / "raw.csv", index=False)
    pd.DataFrame({"Timestamp": raw["Timestamp"]}).to_csv(artifact_dir / "analyzer_features.csv", index=False)
    setups = pd.DataFrame(
        [
            {
                "SetupId": row.candidate_event_id,
                "SetupType": spec.setup_type,
                "Direction": "SHORT",
                "DetectedAt": row.setup_timestamp,
                "SetupBarTs": row.setup_timestamp,
                "ReferenceEventType": "SPRINT03_FORMAL_CANDIDATE_EVENT",
                "ReferenceLevel": row.reference_level,
                "ReferenceEventTs": row.reference_event_timestamp,
                "StopPrice": row.stop_price,
                "TargetPrice": row.target_price,
                "SourceCandidateId": spec.candidate_id,
                "SourceSetupId": row.source_setup_id,
                "FeatureSnapshotHash": row.feature_snapshot_hash,
            }
            for row in events.itertuples(index=False)
        ]
    )
    setups.to_csv(artifact_dir / "analyzer_setups.csv", index=False)
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": spec.source_report,
                "GroupType": spec.group_type,
                "GroupValue": spec.group_value,
                "SelectionDecision": "SELECT",
                "FormalizationEligible": True,
                "Direction": "SHORT",
                "SetupType": spec.setup_type,
                "EligibleEventTypes": spec.eligible_event_types,
            }
        ]
    )
    shortlist.to_csv(artifact_dir / "analyzer_setup_shortlist.csv", index=False)
    shortlist.to_csv(artifact_dir / "analyzer_research_summary.csv", index=False)
    pd.DataFrame(columns=["Timestamp", "EventType", "Direction"]).to_csv(artifact_dir / "analyzer_events.csv", index=False)
    mapping = pd.DataFrame(
        [
            {
                "SourceReport": spec.source_report,
                "GroupType": spec.group_type,
                "GroupValue": spec.group_value,
                "RulesetId": spec.ruleset_id,
                "RulesetContractVersion": spec.rule_version,
                "MappingStatus": "READY",
                "ReplaySemanticsVersion": REPLAY_SEMANTICS_VERSION,
                "SetupFamily": spec.setup_type,
                "Direction": "SHORT",
                "EligibleEventTypes": spec.eligible_event_types,
                "ReplayIntegrationStatus": "READY_FOR_BINDING",
                "EntryTriggerMapping": "CANDIDATE_EVENTS_CSV_FILTERED_AT_FREEZE",
                "EntryBoundaryMapping": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "ExitBoundaryMapping": f"BARS_AFTER_ACTIVATION:{EXPIRY_BARS}",
                "RiskMapping": f"{STOP_MODEL}|FIXED_R_MULTIPLE:{TAKE_PROFIT_R}",
            }
        ]
    )
    mapping.to_csv(artifact_dir / "phase3_ruleset_mapping.csv", index=False)
    manifest = {
        "candidate_id": spec.candidate_id,
        "rule_version": spec.rule_version,
        "freeze_timestamp": freeze_timestamp,
        "candidate_events_path": str(candidate_events_path),
        "event_count": int(len(events.index)),
        "notes": [
            "Sprint 03 formal mapper artifact.",
            "No future labels are used in candidate_events.",
            "Stop=ReferenceLevel hard stop; target=1.5R; expiry=12 bars after activation.",
        ],
    }
    (artifact_dir / "mapper_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_candidate_replays(
    *,
    artifact_dir: Path,
    spec: CandidateSpec,
    output_root: Path,
) -> dict[str, Path]:
    output_dirs: dict[str, Path] = {}
    policies = {
        SAME_BAR_CONSERVATIVE: ConservativeSameBarPolicy(),
        SAME_BAR_PESSIMISTIC: StopWinsSameBarPolicy(),
        SAME_BAR_OPTIMISTIC: TargetWinsSameBarPolicy(),
    }
    for cost in COST_LEVELS:
        cid = cost_model_id(cost)
        for policy_id in [SAME_BAR_CONSERVATIVE]:
            out_dir = output_root / spec.candidate_id / f"cost_{cost_token(cost)}" / "conservative"
            run_backtester(
                artifact_dir=artifact_dir,
                output_dir=out_dir,
                ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
                variant_names=("BASE",),
                cost_model_id=cid,
                same_bar_policy_id=policy_id,
                replay_semantics_version=REPLAY_SEMANTICS_VERSION,
                stop_model=STOP_MODEL,
                expiry_model=f"BARS_AFTER_ACTIVATION:{EXPIRY_BARS}",
                generation_timestamp="2026-05-17T00:00:00+00:00",
                cost_models={cid: FixedRoundTripCostModel(cost)},
                same_bar_policies={policy_id: policies[policy_id]},
            )
            output_dirs[f"cost_{cost_token(cost)}_conservative"] = out_dir
    for policy_id, token in [
        (SAME_BAR_PESSIMISTIC, "pessimistic"),
        (SAME_BAR_OPTIMISTIC, "optimistic"),
    ]:
        cid = cost_model_id(HARD_GATE_COST)
        out_dir = output_root / spec.candidate_id / f"cost_{cost_token(HARD_GATE_COST)}" / token
        run_backtester(
            artifact_dir=artifact_dir,
            output_dir=out_dir,
            ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
            variant_names=("BASE",),
            cost_model_id=cid,
            same_bar_policy_id=policy_id,
            replay_semantics_version=REPLAY_SEMANTICS_VERSION,
            stop_model=STOP_MODEL,
            expiry_model=f"BARS_AFTER_ACTIVATION:{EXPIRY_BARS}",
            generation_timestamp="2026-05-17T00:00:00+00:00",
            cost_models={cid: FixedRoundTripCostModel(HARD_GATE_COST)},
            same_bar_policies={policy_id: policies[policy_id]},
        )
        output_dirs[f"cost_{cost_token(HARD_GATE_COST)}_{token}"] = out_dir
    return output_dirs


def read_trades(run_dir: Path) -> pd.DataFrame:
    path = run_dir / "backtest_trades.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def read_events(run_dir: Path) -> pd.DataFrame:
    path = run_dir / "backtest_engine_events.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def max_drawdown(values: pd.Series) -> float:
    series = pd.to_numeric(values, errors="coerce").fillna(0.0)
    curve = series.cumsum()
    if curve.empty:
        return 0.0
    return float((curve - curve.cummax()).min())


def profit_factor(values: pd.Series) -> float | str:
    series = pd.to_numeric(values, errors="coerce").dropna()
    gains = float(series[series > 0].sum())
    losses = float(series[series < 0].sum())
    if losses == 0:
        return "inf" if gains > 0 else 0.0
    return float(gains / abs(losses))


def build_cost_report(spec: CandidateSpec, output_dirs: dict[str, Path], candidate_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for cost in COST_LEVELS:
        key = f"cost_{cost_token(cost)}_conservative"
        trades = read_trades(output_dirs[key])
        returns = pd.to_numeric(trades.get("trade_return_pct", pd.Series(dtype=float)), errors="coerce").dropna()
        pf = profit_factor(returns)
        rows.append(
            {
                "candidate_id": spec.candidate_id,
                "cost_level": f"{cost:.5f}",
                "trades": int(len(trades.index)),
                "gross_result": "",
                "net_result": round(float(returns.sum()), 10) if not returns.empty else 0.0,
                "winrate": round(float((returns > 0).mean()), 6) if not returns.empty else 0.0,
                "max_drawdown": round(max_drawdown(returns), 10),
                "profit_factor": pf if isinstance(pf, str) else round(pf, 6),
                "pass_fail": "PASS" if float(returns.sum()) > 0 else "FAIL",
                "notes": "formal Sprint 03 replay; conservative same-bar policy; cost model applied inside Backtester",
            }
        )
    report = pd.DataFrame(rows)
    report.to_csv(candidate_dir / "cost_stress_summary.csv", index=False)
    return report


def build_source_concentration_report(spec: CandidateSpec, output_dirs: dict[str, Path], candidate_dir: Path) -> pd.DataFrame:
    trades = read_trades(output_dirs[f"cost_{cost_token(HARD_GATE_COST)}_conservative"])
    if trades.empty:
        summary = pd.DataFrame(
            [
                {
                    "candidate_id": spec.candidate_id,
                    "total_trades": 0,
                    "resolved_return_trades": 0,
                    "independent_trade_days": 0,
                    "net_result": 0.0,
                    "largest_day": "",
                    "largest_day_trades": 0,
                    "largest_day_result": 0.0,
                    "largest_day_abs_result_share": 0.0,
                    "top3_day_abs_result_share": 0.0,
                    "pass_fail": "FAIL",
                    "notes": "no trades",
                }
            ]
        )
        summary.to_csv(candidate_dir / "source_concentration_report.csv", index=False)
        return summary
    trades["_day"] = pd.to_datetime(trades["entry_signal_ts"], utc=True, errors="coerce").dt.date.astype(str)
    trades["_return"] = pd.to_numeric(trades["trade_return_pct"], errors="coerce")
    by_day = trades.groupby("_day", dropna=False)["_return"].agg(["count", "sum"]).reset_index()
    total_abs = float(by_day["sum"].abs().sum())
    idx = by_day["sum"].abs().idxmax()
    largest = by_day.loc[idx]
    largest_abs_share = abs(float(largest["sum"])) / total_abs if total_abs else 0.0
    top3_abs_share = float(by_day["sum"].abs().sort_values(ascending=False).head(3).sum()) / total_abs if total_abs else 0.0
    status = "PASS"
    if len(by_day.index) < 10 or largest_abs_share > 0.33 or top3_abs_share > 0.60:
        status = "FAIL"
    summary = pd.DataFrame(
        [
            {
                "candidate_id": spec.candidate_id,
                "total_trades": int(len(trades.index)),
                "resolved_return_trades": int(trades["_return"].notna().sum()),
                "independent_trade_days": int(len(by_day.index)),
                "net_result": round(float(trades["_return"].sum()), 10),
                "largest_day": str(largest["_day"]),
                "largest_day_trades": int(largest["count"]),
                "largest_day_result": round(float(largest["sum"]), 10),
                "largest_day_abs_result_share": round(largest_abs_share, 6),
                "top3_day_abs_result_share": round(top3_abs_share, 6),
                "pass_fail": status,
                "notes": "PASS requires >=10 trade-days, largest abs day <=33%, top3 abs days <=60%; cost level 0.00015 conservative replay",
            }
        ]
    )
    detail = by_day.rename(columns={"_day": "source_day", "count": "trades", "sum": "day_result"}).sort_values(
        "day_result", key=lambda s: s.abs(), ascending=False
    )
    with (candidate_dir / "source_concentration_report.csv").open("w", encoding="utf-8", newline="") as fp:
        summary.to_csv(fp, index=False)
        fp.write("\n")
        detail.to_csv(fp, index=False)
    return summary


def same_bar_result(output_dir: Path) -> dict[str, Any]:
    trades = read_trades(output_dir)
    events = read_events(output_dir)
    returns = pd.to_numeric(trades.get("trade_return_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    ambiguous = 0
    if not events.empty and "same_bar_outcome" in events.columns:
        close = events[events["event_type"].astype(str).eq("CLOSE_RESOLVED")].copy()
        ambiguous = int(close["same_bar_outcome"].astype(str).ne("NONE").sum())
    return {
        "total_trades": int(len(trades.index)),
        "ambiguous_trades": ambiguous,
        "net_result": round(float(returns.sum()), 10) if not returns.empty else 0.0,
    }


def write_same_bar_report(spec: CandidateSpec, output_dirs: dict[str, Path], candidate_dir: Path) -> dict[str, Any]:
    conservative = same_bar_result(output_dirs[f"cost_{cost_token(HARD_GATE_COST)}_conservative"])
    pessimistic = same_bar_result(output_dirs[f"cost_{cost_token(HARD_GATE_COST)}_pessimistic"])
    optimistic = same_bar_result(output_dirs[f"cost_{cost_token(HARD_GATE_COST)}_optimistic"])
    total = conservative["total_trades"]
    ambiguous = conservative["ambiguous_trades"]
    pct = (100.0 * ambiguous / total) if total else 0.0
    spread = abs(float(optimistic["net_result"]) - float(pessimistic["net_result"]))
    verdict = "PASS"
    if ambiguous and spread > abs(float(conservative["net_result"])) * 0.25:
        verdict = "WAIT"
    if (float(pessimistic["net_result"]) <= 0 < float(optimistic["net_result"])) or (
        float(conservative["net_result"]) > 0 and float(pessimistic["net_result"]) <= 0
    ):
        verdict = "WAIT"
    lines = [
        "# Same-Bar Ambiguity Report",
        "",
        f"Candidate: `{spec.candidate_id}`",
        f"Cost basis: `{HARD_GATE_COST:.5f}`",
        "",
        f"- total trades: {total}",
        f"- same-bar ambiguous trades: {ambiguous}",
        f"- same-bar percentage: {pct:.2f}%",
        f"- pessimistic result: {pessimistic['net_result']}",
        f"- optimistic result: {optimistic['net_result']}",
        f"- conservative result: {conservative['net_result']}",
        f"- verdict: `{verdict}`",
        "",
        "If same-bar ambiguity materially changes the economic verdict, this candidate cannot be promoted.",
        "",
    ]
    (candidate_dir / "same_bar_ambiguity_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "verdict": verdict,
        "total_trades": total,
        "ambiguous_trades": ambiguous,
        "same_bar_pct": pct,
        "pessimistic_result": pessimistic["net_result"],
        "optimistic_result": optimistic["net_result"],
        "conservative_result": conservative["net_result"],
    }


def write_replay_summary(
    *,
    spec: CandidateSpec,
    candidate_dir: Path,
    events: pd.DataFrame,
    cost_report: pd.DataFrame,
    source_report: pd.DataFrame,
    same_bar: dict[str, Any],
    no_lookahead: dict[str, Any],
    verdict: str,
) -> None:
    lines = [
        "# Candidate Replay Summary",
        "",
        f"Candidate: `{spec.candidate_id}`",
        f"Rule version: `{spec.rule_version}`",
        "",
        "## Formal Mapping",
        "",
        f"- candidate events: {len(events.index)}",
        f"- no-lookahead status: `{no_lookahead['status']}`",
        f"- stop model: `{STOP_MODEL}`",
        f"- exit model: `FIXED_R_MULTIPLE:{TAKE_PROFIT_R}` plus `BARS_AFTER_ACTIVATION:{EXPIRY_BARS}` expiry",
        f"- hard cost gate: `{HARD_GATE_COST:.5f}`",
        f"- warning cost gate: `{WARNING_GATE_COST:.5f}`",
        "",
        "## Cost Stress",
        "",
    ]
    for row in cost_report.to_dict("records"):
        lines.append(
            f"- cost `{row['cost_level']}`: trades={row['trades']}, net={row['net_result']}, "
            f"winrate={row['winrate']}, pass_fail={row['pass_fail']}"
        )
    source_row = source_report.iloc[0].to_dict() if not source_report.empty else {}
    lines.extend(
        [
            "",
            "## Source Concentration",
            "",
            f"- pass_fail: `{source_row.get('pass_fail', '')}`",
            f"- independent trade days: {source_row.get('independent_trade_days', '')}",
            f"- largest day abs result share: {source_row.get('largest_day_abs_result_share', '')}",
            f"- top3 day abs result share: {source_row.get('top3_day_abs_result_share', '')}",
            "",
            "## Same-Bar",
            "",
            f"- verdict: `{same_bar['verdict']}`",
            f"- ambiguous trades: {same_bar['ambiguous_trades']} / {same_bar['total_trades']}",
            f"- conservative result: {same_bar['conservative_result']}",
            "",
            "## Verdict",
            "",
            f"`{verdict}`",
            "",
        ]
    )
    (candidate_dir / "candidate_replay_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_promotion_checklist(
    *,
    spec: CandidateSpec,
    candidate_dir: Path,
    events: pd.DataFrame,
    cost_report: pd.DataFrame,
    source_report: pd.DataFrame,
    same_bar: dict[str, Any],
    no_lookahead: dict[str, Any],
    verdict: str,
) -> None:
    cost_015 = cost_report.loc[cost_report["cost_level"].astype(str).eq(f"{HARD_GATE_COST:.5f}")].iloc[0]
    source = source_report.iloc[0].to_dict() if not source_report.empty else {}
    checks = [
        ("formal deterministic mapping exists", len(events.index) > 0),
        ("no future labels", no_lookahead["status"] == "PASS"),
        ("stop frozen", True),
        ("exit frozen", True),
        ("same-bar ambiguity cleared", same_bar["verdict"] == "PASS"),
        ("cost 0.00015 positive", float(cost_015["net_result"]) > 0),
        ("source concentration PASS", source.get("pass_fail") == "PASS"),
        ("no single-day PnL dominance", source.get("pass_fail") == "PASS"),
        (">= 25 post-holdout trades", False),
        (">= 10 independent post-holdout days", False),
        ("true holdout completed", False),
        ("no tuning after freeze", True),
    ]
    lines = ["# Promotion Gate Checklist", "", f"Candidate: `{spec.candidate_id}`", ""]
    for label, ok in checks:
        marker = "PASS" if ok else "FAIL"
        lines.append(f"- [{marker}] {label}")
    lines.extend(["", f"Overall: `{verdict}`", ""])
    (candidate_dir / "promotion_gate_checklist.md").write_text("\n".join(lines), encoding="utf-8")


def compute_verdict(
    *,
    cost_report: pd.DataFrame,
    source_report: pd.DataFrame,
    same_bar: dict[str, Any],
    no_lookahead: dict[str, Any],
) -> str:
    if no_lookahead["status"] != "PASS":
        return "BLOCKED"
    cost_015 = cost_report.loc[cost_report["cost_level"].astype(str).eq(f"{HARD_GATE_COST:.5f}")].iloc[0]
    if float(cost_015["net_result"]) <= 0:
        return "REJECT"
    source = source_report.iloc[0].to_dict() if not source_report.empty else {}
    if source.get("pass_fail") != "PASS":
        return "WAIT"
    if same_bar["verdict"] != "PASS":
        return "WAIT"
    return "WAIT"


def write_ruleset_spec(path: Path, spec: CandidateSpec, candidate_events_path: Path) -> None:
    if spec.candidate_id == CTX_SPEC.candidate_id:
        entry_rule = "SHORT reclaim setup with ctx_spike_count >= 2, then apply entry_delay_1."
        required = "`CtxRelVolumeSpike_v1`, `CtxDeltaSpike_v1`, `CtxOISpike_v1`, `CtxLiqSpike_v1`, `CtxWickReclaim_v1`."
    else:
        entry_rule = "SHORT H2 impulse fade/reclaim setup with ReclaimDepthToImpulseRange > 0.6."
        required = "`ReferenceLevel`, setup close, reference impulse high/low/range, `ReclaimDepthToImpulseRange`."
    lines = [
        f"# RULESET_SPEC - {spec.candidate_id}",
        "",
        "## 1. Candidate Identity",
        "",
        f"- candidate_id: `{spec.candidate_id}`",
        f"- side: `SHORT`",
        f"- timeframe: `{spec.timeframe}`",
        f"- rule_version: `{spec.rule_version}`",
        "",
        "## 2. Input Files",
        "",
        f"- candidate_events: `{candidate_events_path.as_posix()}`",
        f"- source_sidecar_file: `{spec.source_sidecar_file}`",
        "- analyzer source: canonical already-seen Analyzer artifacts plus recovered gap Analyzer artifacts.",
        "",
        "## 3. Required Features",
        "",
        f"- {required}",
        "- No `H2_Post*`, `TradeReturn*`, `TradePnl`, `Exit*`, `Win*`, `FullFade`, or `NoFade` fields are allowed as entry predicates.",
        "",
        "## 4. Entry Rule",
        "",
        f"- {entry_rule}",
        "",
        "## 5. Entry Timing",
        "",
        "- `SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN`.",
        "- Entry price is next raw bar open after `setup_timestamp`.",
        "",
        "## 6. Stop Rule",
        "",
        "- Primary stop model: `REFERENCE_LEVEL_HARD_STOP`.",
        "- For SHORT, `stop_price = ReferenceLevel`; invalid when `stop_price <= entry_price`.",
        "",
        "## 7. Exit Rule",
        "",
        f"- Primary target: `FIXED_R_MULTIPLE:{TAKE_PROFIT_R}`.",
        f"- Expiry: `BARS_AFTER_ACTIVATION:{EXPIRY_BARS}`.",
        "- No target optimization in Sprint 03.",
        "",
        "## 8. Same-Bar Policy",
        "",
        "- Primary replay: `SAME_BAR_CONSERVATIVE_V0_1`.",
        "- Audit variants: pessimistic stop-wins and optimistic target-wins at cost 0.00015.",
        "",
        "## 9. Cost Model",
        "",
        "- Cost is applied inside Backtester via round-trip price adjustment.",
        "- Levels: `0.00000`, `0.00010`, `0.00015`, `0.00020`.",
        "- `0.00015` is the hard gate; `0.00020` is the warning stress gate.",
        "",
        "## 10. Invalid Conditions",
        "",
        "- Missing raw entry bar.",
        "- Missing `ReferenceLevel`.",
        "- Non-positive short risk distance.",
        "- Any future/outcome label in entry predicate.",
        "",
        "## 11. No-Tuning Declaration",
        "",
        "- No thresholds, stop model, target model, expiry, or entry timing may be changed after inspecting Sprint 03 replay outputs.",
        "- This ruleset is not live and not Phase 4 approved.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_holdout_protocol(path: Path, freeze_timestamp: str) -> None:
    lines = [
        "# HOLDOUT_PROTOCOL",
        "",
        f"Contract freeze timestamp: `{freeze_timestamp}`",
        "",
        "## Candidate IDs",
        "",
        f"- `{CTX_SPEC.candidate_id}`",
        f"- `{DEEP_SPEC.candidate_id}`",
        "",
        "## Already-Seen Data",
        "",
        "- All data, Analyzer artifacts, Backtester outputs, sidecar diagnostics, and recovered-gap reruns inspected before the freeze timestamp.",
        "- This includes primary/recovered data through the current local project state on 2026-05-17.",
        "- Recovered gap data is valid for data repair and pooled replay, but it is not true holdout.",
        "",
        "## True Holdout",
        "",
        "- True holdout starts only after the Sprint 03 freeze timestamp.",
        "- Any day analyzed, used in candidate_events, or discussed before freeze is not holdout.",
        "- Holdout data must come from clean feed or explicitly accepted recovered source with degraded fields documented.",
        "",
        "## Minimum Evidence",
        "",
        "- >= 25 post-holdout trades.",
        "- >= 10 independent post-holdout trade-days.",
        "- Positive net after cost stress 0.00015.",
        "- 0.00020 stress failure is allowed only as WAIT_FOR_EXECUTION_COST_REVIEW, never PROMOTE.",
        "- Source concentration PASS.",
        "- Same-bar ambiguity cleared.",
        "",
        "## No-Tuning Rule",
        "",
        "- No threshold, entry delay, stop, target, expiry, feature definition, or filter may be changed after freeze based on holdout results.",
        "- A changed rule becomes a new candidate and restarts the holdout clock.",
        "",
        "## Verdict Rules",
        "",
        "- `PROMOTE`: all gates pass, including true holdout.",
        "- `WAIT`: formal mapping exists but holdout/cost/source/same-bar gates are incomplete or mixed.",
        "- `REJECT`: hard cost gate fails or evidence is negative under frozen rule.",
        "- `BLOCKED`: mapping, stop/exit, no-lookahead, or replay contract is invalid.",
        "",
        "Phase 4 Bridge remains closed until this protocol passes. Executor/live remain prohibited.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_all(args: argparse.Namespace) -> dict[str, Any]:
    freeze_timestamp = datetime.now(timezone.utc).isoformat()
    analyzer_root = Path(args.analyzer_runs_root)
    recovered_gap_root = Path(args.recovered_gap_analyzer_root)
    feed_root = Path(args.feed_root)
    recovered_root = Path(args.feed_recovered_root)
    candidates_root = Path(args.candidates_root)
    output_root = Path(args.backtest_output_root)
    artifacts_root = output_root / "artifacts"

    source_dirs = load_source_analyzer_dirs(analyzer_root, recovered_gap_root)
    source_days = [parse_run_date(path) for path in source_dirs]
    days = [day for day in source_days if day is not None]
    raw = load_raw_window(days, feed_root, recovered_root)
    if raw.empty:
        raise SystemExit("No raw data loaded for Sprint 03 replay.")

    candidate_builders = {
        CTX_SPEC.candidate_id: (CTX_SPEC, build_ctx_candidate_events),
        DEEP_SPEC.candidate_id: (DEEP_SPEC, build_deep_candidate_events),
    }
    results: dict[str, Any] = {
        "freeze_timestamp": freeze_timestamp,
        "source_analyzer_dirs": len(source_dirs),
        "candidates": {},
    }
    write_holdout_protocol(Path(args.holdout_protocol_path), freeze_timestamp)

    for candidate_id, (spec, builder) in candidate_builders.items():
        candidate_dir = candidates_root / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        events = builder(source_dirs, raw)
        events_path = write_candidate_events(candidate_dir, events)
        write_ruleset_spec(candidate_dir / "RULESET_SPEC.md", spec, events_path)
        no_lookahead = no_lookahead_check(events, candidate_dir)
        artifact_dir = artifacts_root / candidate_id
        write_artifact_bundle(
            artifact_dir=artifact_dir,
            spec=spec,
            events=events,
            raw=raw,
            candidate_events_path=events_path,
            freeze_timestamp=freeze_timestamp,
        )
        output_dirs = run_candidate_replays(artifact_dir=artifact_dir, spec=spec, output_root=output_root)
        cost_report = build_cost_report(spec, output_dirs, candidate_dir)
        source_report = build_source_concentration_report(spec, output_dirs, candidate_dir)
        same_bar = write_same_bar_report(spec, output_dirs, candidate_dir)
        verdict = compute_verdict(
            cost_report=cost_report,
            source_report=source_report,
            same_bar=same_bar,
            no_lookahead=no_lookahead,
        )
        write_promotion_checklist(
            spec=spec,
            candidate_dir=candidate_dir,
            events=events,
            cost_report=cost_report,
            source_report=source_report,
            same_bar=same_bar,
            no_lookahead=no_lookahead,
            verdict=verdict,
        )
        write_replay_summary(
            spec=spec,
            candidate_dir=candidate_dir,
            events=events,
            cost_report=cost_report,
            source_report=source_report,
            same_bar=same_bar,
            no_lookahead=no_lookahead,
            verdict=verdict,
        )
        results["candidates"][candidate_id] = {
            "candidate_events": str(events_path),
            "event_count": int(len(events.index)),
            "artifact_dir": str(artifact_dir),
            "verdict": verdict,
            "no_lookahead": no_lookahead,
            "same_bar": same_bar,
        }

    summary_path = output_root / "sprint_03_pooled_replay_summary.json"
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 03 formal candidate ruleset mapper and replay runner.")
    parser.add_argument("--analyzer-runs-root", default="analyzer_runs")
    parser.add_argument(
        "--recovered-gap-analyzer-root",
        default="analyzer_runs/recovered_gap_2026-04-23_2026-05-06",
    )
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--feed-recovered-root", default="feed_recovered")
    parser.add_argument("--candidates-root", default="research/candidates")
    parser.add_argument("--backtest-output-root", default="backtest_runs/sprint_03_candidate_rulesets")
    parser.add_argument("--holdout-protocol-path", default="research/canonical/HOLDOUT_PROTOCOL.md")
    args = parser.parse_args()
    run_all(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
