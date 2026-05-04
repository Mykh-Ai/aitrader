"""Deterministic replay engine skeleton for Backtester Phase 3 Step 2A."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
from typing import Any, Mapping, Protocol

import pandas as pd

from .rulesets import parse_expiry_model_bars

REQUIRED_ARTIFACT_KEYS = ("raw", "features", "setups")
OPTIONAL_ARTIFACT_KEYS = ("events", "lineage")

REQUIRED_RAW_COLUMNS = ("Timestamp", "Open", "High", "Low", "Close", "IsSynthetic")
REQUIRED_FEATURE_COLUMNS = ("Timestamp",)
REQUIRED_SETUP_COLUMNS = (
    "SetupId",
    "SetupType",
    "Direction",
    "DetectedAt",
    "SetupBarTs",
    "ReferenceEventType",
)
REQUIRED_RULESET_REPLAY_FIELDS = (
    "ruleset_id",
    "entry_timing",
    "entry_price_convention",
    "same_bar_policy_id",
    "expiry_model",
    "expiry_start_semantics",
    "stop_model",
    "take_profit_model",
    "cost_model_id",
    "replay_semantics_version",
)
SAME_BAR_OUTCOMES = ("STOP_WINS", "TARGET_WINS", "UNRESOLVED", "DEFERRED", "NONE")
CLOSE_REASON_CATEGORIES = ("STOP", "TARGET", "EXPIRY", "UNRESOLVED")
REPLAY_EVENT_COLUMNS = (
    "event_id",
    "ruleset_id",
    "event_type",
    "timestamp",
    "bar_timestamp",
    "source_setup_id",
    "direction",
    "state_before",
    "state_after",
    "price_raw",
    "price_effective",
    "same_bar_policy_id",
    "same_bar_outcome",
    "cost_model_id",
    "replay_semantics_version",
    "close_reason",
    "close_reason_category",
    "close_resolved",
    "close_price_raw",
    "close_price_effective",
    "notes",
)

ENTRY_TIMING_BASELINE = "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN"
ENTRY_PRICE_BASELINE = "NEXT_BAR_OPEN"
STOP_PRICE_KEYS = ("initial_stop_price", "InitialStopPrice", "StopPrice", "stop_price")
TARGET_PRICE_KEYS = (
    "initial_target_price",
    "InitialTargetPrice",
    "TargetPrice",
    "target_price",
    "TakeProfitPrice",
    "take_profit_price",
)


class ReplayContractError(ValueError):
    """Raised when replay contract assumptions are violated."""


def _parse_expiry_bars(ruleset: pd.Series) -> int:
    """Parse replay expiry semantics after replay contract validation."""
    try:
        return parse_expiry_model_bars(str(ruleset.get("expiry_model", "")))
    except ValueError as exc:
        ruleset_id = str(ruleset.get("ruleset_id", "<unknown>"))
        raise ReplayContractError(f"Invalid expiry_model for ruleset={ruleset_id}: {exc}") from exc


class CostModelHook(Protocol):
    """Explicit interface for deterministic replay cost application."""

    def apply(
        self,
        *,
        ruleset_row: pd.Series,
        event_type: str,
        timestamp: pd.Timestamp,
        price_raw: float | None,
        direction: str,
    ) -> dict[str, Any]: ...


class SameBarPolicyHook(Protocol):
    """Explicit interface for same-bar stop/target collision resolution."""

    def resolve(
        self,
        *,
        ruleset_row: pd.Series,
        setup_row: pd.Series,
        bar_row: pd.Series,
    ) -> str: ...


@dataclass(frozen=True)
class ReplayInputs:
    raw_df: pd.DataFrame
    features_df: pd.DataFrame
    setups_df: pd.DataFrame
    rulesets_df: pd.DataFrame
    events_df: pd.DataFrame | None = None
    lineage_df: pd.DataFrame | None = None
    artifact_paths: dict[str, str] | None = None


class ZeroCostSkeletonModel:
    """Explicitly non-production zero-cost model for skeleton-only replay."""

    def apply(
        self,
        *,
        ruleset_row: pd.Series,
        event_type: str,
        timestamp: pd.Timestamp,
        price_raw: float | None,
        direction: str,
    ) -> dict[str, Any]:
        return {
            "price_effective": price_raw,
            "cost_amount": 0.0,
            "notes": "cost_model_hook=COST_MODEL_ZERO_SKELETON_ONLY",
        }


class ConservativeSameBarPolicy:
    """Baseline explicit same-bar collision resolver."""

    def resolve(
        self,
        *,
        ruleset_row: pd.Series,
        setup_row: pd.Series,
        bar_row: pd.Series,
    ) -> str:
        return "UNRESOLVED"


def _require_columns(df: pd.DataFrame, required_columns: tuple[str, ...], label: str) -> None:
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ReplayContractError(f"Missing required columns in {label}: {missing}")


def _normalize_timestamp_column(df: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
    if column not in df.columns:
        raise ReplayContractError(f"Missing timestamp column '{column}' in {label}")
    out = df.copy()
    out[column] = pd.to_datetime(out[column], utc=True, errors="raise")
    out = out.sort_values(column, kind="mergesort").reset_index(drop=True)
    return out


def _validate_rulesets_replay_contract(rulesets_df: pd.DataFrame) -> None:
    _require_columns(rulesets_df, REQUIRED_RULESET_REPLAY_FIELDS, "rulesets_df")
    for field in REQUIRED_RULESET_REPLAY_FIELDS:
        bad = rulesets_df[field].isna() | (rulesets_df[field].astype(str).str.strip() == "")
        if bad.any():
            bad_ids = rulesets_df.loc[bad, "ruleset_id"].astype(str).tolist()
            raise ReplayContractError(
                f"Ruleset replay-critical field '{field}' is missing/blank for rulesets: {bad_ids}"
            )
    for _, row in rulesets_df.iterrows():
        try:
            parse_expiry_model_bars(str(row["expiry_model"]))
        except ValueError as exc:
            raise ReplayContractError(
                f"Invalid expiry_model for ruleset={row['ruleset_id']}: {exc}"
            ) from exc


def validate_replay_inputs(inputs: ReplayInputs) -> None:
    """Fail-loud schema + contract validation before replay starts."""
    _require_columns(inputs.raw_df, REQUIRED_RAW_COLUMNS, "raw_df")
    _require_columns(inputs.features_df, REQUIRED_FEATURE_COLUMNS, "features_df")
    _require_columns(inputs.setups_df, REQUIRED_SETUP_COLUMNS, "setups_df")
    _validate_rulesets_replay_contract(inputs.rulesets_df)


def load_replay_inputs(
    *,
    artifact_paths: Mapping[str, str | Path],
    rulesets: pd.DataFrame | str | Path,
) -> ReplayInputs:
    """Load pre-generated Analyzer artifacts for deterministic replay."""
    missing_artifacts = [key for key in REQUIRED_ARTIFACT_KEYS if key not in artifact_paths]
    if missing_artifacts:
        raise ReplayContractError(f"Missing required artifact path keys: {missing_artifacts}")

    dataframes: dict[str, pd.DataFrame | None] = {}
    normalized_paths: dict[str, str] = {}
    for key in [*REQUIRED_ARTIFACT_KEYS, *OPTIONAL_ARTIFACT_KEYS]:
        if key not in artifact_paths:
            dataframes[key] = None
            continue
        path = Path(artifact_paths[key])
        if not path.exists():
            raise ReplayContractError(f"Required artifact does not exist: key={key}, path={path}")
        normalized_paths[key] = str(path)
        dataframes[key] = pd.read_csv(path)

    rulesets_df = pd.read_csv(rulesets) if isinstance(rulesets, (str, Path)) else rulesets.copy()

    loaded = ReplayInputs(
        raw_df=_normalize_timestamp_column(dataframes["raw"], "Timestamp", "raw_df"),
        features_df=_normalize_timestamp_column(dataframes["features"], "Timestamp", "features_df"),
        setups_df=_normalize_timestamp_column(dataframes["setups"], "SetupBarTs", "setups_df"),
        rulesets_df=rulesets_df.reset_index(drop=True),
        events_df=(
            _normalize_timestamp_column(dataframes["events"], "Timestamp", "events_df")
            if dataframes["events"] is not None
            else None
        ),
        lineage_df=dataframes["lineage"],
        artifact_paths=normalized_paths,
    )
    validate_replay_inputs(loaded)
    return loaded


def _git_commit_or_unknown() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _build_event(
    *,
    event_id: str,
    ruleset_id: str,
    event_type: str,
    timestamp: pd.Timestamp,
    bar_timestamp: pd.Timestamp,
    setup_id: str,
    direction: str,
    state_before: str,
    state_after: str,
    price_raw: float | None,
    price_effective: float | None,
    same_bar_policy_id: str,
    same_bar_outcome: str,
    cost_model_id: str,
    replay_semantics_version: str,
    close_reason: str | None,
    close_reason_category: str | None,
    close_resolved: bool,
    close_price_raw: float | None,
    close_price_effective: float | None,
    notes: str,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "ruleset_id": ruleset_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "bar_timestamp": bar_timestamp,
        "source_setup_id": setup_id,
        "direction": direction,
        "state_before": state_before,
        "state_after": state_after,
        "price_raw": price_raw,
        "price_effective": price_effective,
        "same_bar_policy_id": same_bar_policy_id,
        "same_bar_outcome": same_bar_outcome,
        "cost_model_id": cost_model_id,
        "replay_semantics_version": replay_semantics_version,
        "close_reason": close_reason,
        "close_reason_category": close_reason_category,
        "close_resolved": close_resolved,
        "close_price_raw": close_price_raw,
        "close_price_effective": close_price_effective,
        "notes": notes,
    }


def _validate_same_bar_outcome(outcome: str, ruleset_id: str, setup_id: str) -> str:
    normalized = str(outcome).strip().upper()
    if normalized not in SAME_BAR_OUTCOMES:
        raise ReplayContractError(
            f"Invalid same-bar outcome '{outcome}' for ruleset={ruleset_id}, setup={setup_id}. "
            f"Allowed values: {SAME_BAR_OUTCOMES}"
        )
    return normalized


def _validate_close_reason_category(category: str, ruleset_id: str, setup_id: str) -> str:
    normalized = str(category).strip().upper()
    if normalized not in CLOSE_REASON_CATEGORIES:
        raise ReplayContractError(
            f"Invalid close_reason_category '{category}' for ruleset={ruleset_id}, setup={setup_id}. "
            f"Allowed values: {CLOSE_REASON_CATEGORIES}"
        )
    return normalized


def _first_numeric(row: pd.Series, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in row and pd.notna(row[key]):
            return float(row[key])
    return None


def _hit_flags(*, direction: str, low: float, high: float, stop_price: float | None, target_price: float | None) -> tuple[bool, bool]:
    side = direction.upper()
    if side == "LONG":
        stop_hit = stop_price is not None and low <= stop_price
        target_hit = target_price is not None and high >= target_price
        return stop_hit, target_hit
    if side == "SHORT":
        stop_hit = stop_price is not None and high >= stop_price
        target_hit = target_price is not None and low <= target_price
        return stop_hit, target_hit
    return False, False


def run_replay_engine(
    inputs: ReplayInputs,
    *,
    cost_models: Mapping[str, CostModelHook] | None = None,
    same_bar_policies: Mapping[str, SameBarPolicyHook] | None = None,
    generation_timestamp: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute deterministic replay skeleton with explicit contract hooks."""
    validate_replay_inputs(inputs)

    raw = _normalize_timestamp_column(inputs.raw_df, "Timestamp", "raw_df")
    setups = _normalize_timestamp_column(inputs.setups_df, "SetupBarTs", "setups_df")
    rulesets = inputs.rulesets_df.sort_values("ruleset_id", kind="mergesort").reset_index(drop=True)

    cost_models = cost_models or {"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()}
    same_bar_policies = same_bar_policies or {"SAME_BAR_CONSERVATIVE_V0_1": ConservativeSameBarPolicy()}

    raw_timestamps = list(raw["Timestamp"])
    timestamp_index = {ts: idx for idx, ts in enumerate(raw_timestamps)}

    setups_by_ts: dict[pd.Timestamp, pd.DataFrame] = {
        ts: grp.sort_values(["SetupId"], kind="mergesort").reset_index(drop=True)
        for ts, grp in setups.groupby("SetupBarTs", sort=False)
    }

    pending_by_ts: dict[pd.Timestamp, list[dict[str, Any]]] = {}
    active_positions: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    event_counter = 1

    def emit_event(**kwargs: Any) -> None:
        nonlocal event_counter
        kwargs["event_id"] = f"EV_{event_counter:08d}"
        events.append(_build_event(**kwargs))
        event_counter += 1

    for bar_ts in raw_timestamps:
        bar_row = raw.loc[timestamp_index[bar_ts]]

        actionable = setups_by_ts.get(bar_ts)
        if actionable is not None and not actionable.empty:
            for _, ruleset in rulesets.iterrows():
                if ruleset["entry_timing"] != ENTRY_TIMING_BASELINE:
                    raise ReplayContractError(
                        f"Unsupported entry_timing for Step 2A: {ruleset['entry_timing']}"
                    )
                if ruleset["entry_price_convention"] != ENTRY_PRICE_BASELINE:
                    raise ReplayContractError(
                        f"Unsupported entry_price_convention for Step 2A: {ruleset['entry_price_convention']}"
                    )

                cost_model_id = str(ruleset["cost_model_id"])
                same_bar_policy_id = str(ruleset["same_bar_policy_id"])
                if cost_model_id not in cost_models:
                    raise ReplayContractError(f"No cost model hook registered for id={cost_model_id}")
                if same_bar_policy_id not in same_bar_policies:
                    raise ReplayContractError(f"No same-bar policy hook registered for id={same_bar_policy_id}")

                eligible = actionable
                if "direction" in ruleset and str(ruleset["direction"]).upper() in {"LONG", "SHORT"}:
                    eligible = eligible[eligible["Direction"] == str(ruleset["direction"]).upper()]
                if "setup_type" in ruleset and str(ruleset["setup_type"]).strip():
                    eligible = eligible[eligible["SetupType"] == str(ruleset["setup_type"])]
                if eligible.empty:
                    continue

                for _, setup in eligible.iterrows():
                    direction = str(setup["Direction"])
                    cost_model = cost_models[cost_model_id]
                    cost_signal = cost_model.apply(
                        ruleset_row=ruleset,
                        event_type="SIGNAL_ACTIONABLE",
                        timestamp=bar_ts,
                        price_raw=None,
                        direction=direction,
                    )
                    emit_event(
                        ruleset_id=str(ruleset["ruleset_id"]),
                        event_type="SIGNAL_ACTIONABLE",
                        timestamp=bar_ts,
                        bar_timestamp=bar_ts,
                        setup_id=str(setup["SetupId"]),
                        direction=direction,
                        state_before="IDLE",
                        state_after="SIGNAL_ACTIONABLE",
                        price_raw=None,
                        price_effective=cost_signal["price_effective"],
                        same_bar_policy_id=same_bar_policy_id,
                        same_bar_outcome="NONE",
                        cost_model_id=cost_model_id,
                        replay_semantics_version=str(ruleset["replay_semantics_version"]),
                        close_reason=None,
                        close_reason_category=None,
                        close_resolved=False,
                        close_price_raw=None,
                        close_price_effective=None,
                        notes="observability=signal_bar_close_only",
                    )
                    emit_event(
                        ruleset_id=str(ruleset["ruleset_id"]),
                        event_type="ENTRY_PENDING",
                        timestamp=bar_ts,
                        bar_timestamp=bar_ts,
                        setup_id=str(setup["SetupId"]),
                        direction=direction,
                        state_before="SIGNAL_ACTIONABLE",
                        state_after="ENTRY_PENDING",
                        price_raw=None,
                        price_effective=None,
                        same_bar_policy_id=same_bar_policy_id,
                        same_bar_outcome="NONE",
                        cost_model_id=cost_model_id,
                        replay_semantics_version=str(ruleset["replay_semantics_version"]),
                        close_reason=None,
                        close_reason_category=None,
                        close_resolved=False,
                        close_price_raw=None,
                        close_price_effective=None,
                        notes="entry_timing=next_bar_open",
                    )

                    next_idx = timestamp_index[bar_ts] + 1
                    if next_idx >= len(raw_timestamps):
                        emit_event(
                            ruleset_id=str(ruleset["ruleset_id"]),
                            event_type="EXPIRY_EVALUATED",
                            timestamp=bar_ts,
                            bar_timestamp=bar_ts,
                            setup_id=str(setup["SetupId"]),
                            direction=direction,
                            state_before="ENTRY_PENDING",
                            state_after="EXPIRED",
                            price_raw=None,
                            price_effective=None,
                            same_bar_policy_id=same_bar_policy_id,
                            same_bar_outcome="NONE",
                            cost_model_id=cost_model_id,
                            replay_semantics_version=str(ruleset["replay_semantics_version"]),
                            close_reason="ENTRY_EXPIRED_NO_NEXT_BAR",
                            close_reason_category="EXPIRY",
                            close_resolved=True,
                            close_price_raw=None,
                            close_price_effective=None,
                            notes="no_next_bar_available",
                        )
                        continue

                    activation_ts = raw_timestamps[next_idx]
                    pending_by_ts.setdefault(activation_ts, []).append(
                        {
                            "ruleset": ruleset,
                            "setup": setup,
                            "same_bar_policy_id": same_bar_policy_id,
                            "cost_model_id": cost_model_id,
                        }
                    )

        activated_records = pending_by_ts.pop(bar_ts, [])
        for record in activated_records:
            ruleset = record["ruleset"]
            setup = record["setup"]
            direction = str(setup["Direction"])
            cost_model_id = record["cost_model_id"]
            same_bar_policy_id = record["same_bar_policy_id"]
            cost_model = cost_models[cost_model_id]

            entry_price_raw = float(bar_row["Open"])
            cost_entry = cost_model.apply(
                ruleset_row=ruleset,
                event_type="ENTRY_ACTIVATED",
                timestamp=bar_ts,
                price_raw=entry_price_raw,
                direction=direction,
            )
            emit_event(
                ruleset_id=str(ruleset["ruleset_id"]),
                event_type="ENTRY_ACTIVATED",
                timestamp=bar_ts,
                bar_timestamp=bar_ts,
                setup_id=str(setup["SetupId"]),
                direction=direction,
                state_before="ENTRY_PENDING",
                state_after="ENTRY_ACTIVE",
                price_raw=entry_price_raw,
                price_effective=cost_entry["price_effective"],
                same_bar_policy_id=same_bar_policy_id,
                same_bar_outcome="NONE",
                cost_model_id=cost_model_id,
                replay_semantics_version=str(ruleset["replay_semantics_version"]),
                close_reason=None,
                close_reason_category=None,
                close_resolved=False,
                close_price_raw=None,
                close_price_effective=None,
                notes="entry_price_convention=next_bar_open",
            )

            active_positions.append(
                {
                    "ruleset": ruleset,
                    "setup": setup,
                    "direction": direction,
                    "cost_model_id": cost_model_id,
                    "same_bar_policy_id": same_bar_policy_id,
                    "stop_price": _first_numeric(setup, STOP_PRICE_KEYS),
                    "target_price": _first_numeric(setup, TARGET_PRICE_KEYS),
                    "activation_ts": bar_ts,
                    "activation_idx": timestamp_index[bar_ts],
                    "expiry_bars": _parse_expiry_bars(ruleset),
                    "force_expiry_close": bool(setup.get("ForceExpiryClose", False)),
                    "force_collision": bool(setup.get("ForceSameBarCollision", False)),
                }
            )

        next_active_positions: list[dict[str, Any]] = []
        for position in active_positions:
            ruleset = position["ruleset"]
            setup = position["setup"]
            direction = str(position["direction"])
            cost_model_id = str(position["cost_model_id"])
            same_bar_policy_id = str(position["same_bar_policy_id"])
            cost_model = cost_models[cost_model_id]

            stop_price = position["stop_price"]
            target_price = position["target_price"]
            bar_low = float(bar_row["Low"])
            bar_high = float(bar_row["High"])
            stop_hit, target_hit = _hit_flags(
                direction=direction,
                low=bar_low,
                high=bar_high,
                stop_price=stop_price,
                target_price=target_price,
            )

            emit_event(
                ruleset_id=str(ruleset["ruleset_id"]),
                event_type="STOP_EVALUATED",
                timestamp=bar_ts,
                bar_timestamp=bar_ts,
                setup_id=str(setup["SetupId"]),
                direction=direction,
                state_before="ENTRY_ACTIVE",
                state_after="ENTRY_ACTIVE",
                price_raw=stop_price,
                price_effective=None,
                same_bar_policy_id=same_bar_policy_id,
                same_bar_outcome="NONE",
                cost_model_id=cost_model_id,
                replay_semantics_version=str(ruleset["replay_semantics_version"]),
                close_reason=None,
                close_reason_category=None,
                close_resolved=False,
                close_price_raw=None,
                close_price_effective=None,
                notes=(
                    "stop_level_missing"
                    if stop_price is None
                    else ("stop_hit" if stop_hit else "stop_not_hit")
                ),
            )
            emit_event(
                ruleset_id=str(ruleset["ruleset_id"]),
                event_type="TARGET_EVALUATED",
                timestamp=bar_ts,
                bar_timestamp=bar_ts,
                setup_id=str(setup["SetupId"]),
                direction=direction,
                state_before="ENTRY_ACTIVE",
                state_after="ENTRY_ACTIVE",
                price_raw=target_price,
                price_effective=None,
                same_bar_policy_id=same_bar_policy_id,
                same_bar_outcome="NONE",
                cost_model_id=cost_model_id,
                replay_semantics_version=str(ruleset["replay_semantics_version"]),
                close_reason=None,
                close_reason_category=None,
                close_resolved=False,
                close_price_raw=None,
                close_price_effective=None,
                notes=(
                    "target_level_missing"
                    if target_price is None
                    else ("target_hit" if target_hit else "target_not_hit")
                ),
            )

            force_collision = bool(position["force_collision"])
            force_expiry_close = bool(position["force_expiry_close"])
            expiry_bars = position["expiry_bars"]
            bars_since_activation = timestamp_index[bar_ts] - int(position["activation_idx"])
            expiry_due = bool(expiry_bars is not None and bars_since_activation >= expiry_bars)

            close_state = "ENTRY_ACTIVE"
            same_bar_outcome = "NONE"
            close_notes = "close_not_resolved_step2a"
            close_reason = "NO_EXIT_RESOLVED_YET"
            close_reason_category = "UNRESOLVED"
            close_resolved = False
            close_price_raw = None
            collision_forced = force_collision
            if collision_forced or (stop_hit and target_hit):
                policy = same_bar_policies[same_bar_policy_id]
                outcome = _validate_same_bar_outcome(
                    policy.resolve(ruleset_row=ruleset, setup_row=setup, bar_row=bar_row),
                    str(ruleset["ruleset_id"]),
                    str(setup["SetupId"]),
                )
                same_bar_outcome = outcome
                close_state = "CLOSE_POLICY_ROUTED"
                close_notes = "same_bar_collision_routed_to_policy"
                if outcome == "STOP_WINS":
                    close_reason = "STOP_LOSS"
                    close_reason_category = "STOP"
                    close_resolved = True
                    close_price_raw = stop_price
                elif outcome == "TARGET_WINS":
                    close_reason = "TAKE_PROFIT"
                    close_reason_category = "TARGET"
                    close_resolved = True
                    close_price_raw = target_price
                elif outcome in {"UNRESOLVED", "DEFERRED"}:
                    close_reason = f"SAME_BAR_{outcome}"
                    close_reason_category = "UNRESOLVED"
                    close_resolved = False

            elif stop_hit:
                close_state = "CLOSED_STOP"
                close_notes = "stop_hit_resolved"
                close_reason = "STOP_LOSS"
                close_reason_category = "STOP"
                close_resolved = True
                close_price_raw = stop_price
            elif target_hit:
                close_state = "CLOSED_TARGET"
                close_notes = "target_hit_resolved"
                close_reason = "TAKE_PROFIT"
                close_reason_category = "TARGET"
                close_resolved = True
                close_price_raw = target_price

            if (force_expiry_close or expiry_due) and not close_resolved:
                close_state = "CLOSED_EXPIRY"
                close_notes = (
                    "expiry_close_forced"
                    if force_expiry_close
                    else f"expiry_hit_bars_after_activation={expiry_bars}"
                )
                close_reason = "EXPIRY"
                close_reason_category = "EXPIRY"
                close_resolved = True
                close_price_raw = float(bar_row["Close"])

            close_reason_category = _validate_close_reason_category(
                close_reason_category,
                str(ruleset["ruleset_id"]),
                str(setup["SetupId"]),
            )

            cost_close = cost_model.apply(
                ruleset_row=ruleset,
                event_type="CLOSE_RESOLVED",
                timestamp=bar_ts,
                price_raw=close_price_raw,
                direction=direction,
            )
            close_price_effective = cost_close["price_effective"] if close_price_raw is not None else None
            emit_event(
                ruleset_id=str(ruleset["ruleset_id"]),
                event_type="CLOSE_RESOLVED",
                timestamp=bar_ts,
                bar_timestamp=bar_ts,
                setup_id=str(setup["SetupId"]),
                direction=direction,
                state_before="ENTRY_ACTIVE",
                state_after=close_state,
                price_raw=close_price_raw,
                price_effective=close_price_effective,
                same_bar_policy_id=same_bar_policy_id,
                same_bar_outcome=same_bar_outcome,
                cost_model_id=cost_model_id,
                replay_semantics_version=str(ruleset["replay_semantics_version"]),
                close_reason=close_reason,
                close_reason_category=close_reason_category,
                close_resolved=close_resolved,
                close_price_raw=close_price_raw,
                close_price_effective=close_price_effective,
                notes=close_notes,
            )
            emit_event(
                ruleset_id=str(ruleset["ruleset_id"]),
                event_type="EXPIRY_EVALUATED",
                timestamp=bar_ts,
                bar_timestamp=bar_ts,
                setup_id=str(setup["SetupId"]),
                direction=direction,
                state_before=close_state,
                state_after=close_state,
                price_raw=None,
                price_effective=None,
                same_bar_policy_id=same_bar_policy_id,
                same_bar_outcome=same_bar_outcome,
                cost_model_id=cost_model_id,
                replay_semantics_version=str(ruleset["replay_semantics_version"]),
                close_reason=None,
                close_reason_category=None,
                close_resolved=False,
                close_price_raw=None,
                close_price_effective=None,
                notes=(
                    f"expiry_start_semantics={ruleset['expiry_start_semantics']}; "
                    f"expiry_model={ruleset.get('expiry_model', '')}; "
                    f"bars_since_activation={bars_since_activation}; "
                    f"expiry_due={expiry_due}"
                ),
            )

            position["force_collision"] = False

            if not close_resolved:
                next_active_positions.append(position)

        active_positions = next_active_positions

    events_df = pd.DataFrame(events, columns=REPLAY_EVENT_COLUMNS)
    manifest = {
        "artifact_paths": inputs.artifact_paths or {},
        "ruleset_ids": rulesets["ruleset_id"].astype(str).tolist(),
        "replay_semantics_version": sorted(set(rulesets["replay_semantics_version"].astype(str))),
        "cost_model_ids": sorted(set(rulesets["cost_model_id"].astype(str))),
        "expiry_models": sorted(set(rulesets["expiry_model"].astype(str))),
        "generated_at_utc": generation_timestamp or datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit_or_unknown(),
    }
    return events_df, manifest


def write_engine_outputs(
    *,
    events_df: pd.DataFrame,
    manifest: Mapping[str, Any],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Persist deterministic Step 2A replay outputs."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    events_path = output / "backtest_engine_events.csv"
    manifest_path = output / "backtest_run_manifest.json"

    events_out = events_df.reindex(columns=REPLAY_EVENT_COLUMNS)
    events_out.to_csv(events_path, index=False)
    with manifest_path.open("w", encoding="utf-8") as fp:
        json.dump(dict(manifest), fp, ensure_ascii=False, indent=2)
    return events_path, manifest_path
