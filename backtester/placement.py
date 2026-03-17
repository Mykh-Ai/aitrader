"""Deterministic pre-engine SL/TP placement materialization for Backtester Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PLACEMENT_STATUS_PLACED = "PLACED"
PLACEMENT_STATUS_UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"
PLACEMENT_STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
PLACEMENT_STATUS_INVALID_RISK = "INVALID_RISK"

PLACEMENT_STATUSES = {
    PLACEMENT_STATUS_PLACED,
    PLACEMENT_STATUS_UNSUPPORTED_MODEL,
    PLACEMENT_STATUS_INSUFFICIENT_DATA,
    PLACEMENT_STATUS_INVALID_RISK,
}

REQUIRED_RULESET_COLUMNS = (
    "ruleset_id",
    "entry_price_convention",
    "stop_model",
    "take_profit_model",
)

REQUIRED_SETUP_COLUMNS = (
    "SetupId",
    "SetupBarTs",
    "Direction",
    "ReferenceLevel",
)

REQUIRED_RAW_COLUMNS = (
    "Timestamp",
    "Open",
)

PLACEMENT_COLUMNS = (
    "initial_stop_price",
    "initial_target_price",
    "stop_model_applied",
    "take_profit_model_applied",
    "placement_computed_at_ts",
    "placement_basis_ts",
    "placement_status",
    "placement_notes",
    "risk_distance",
)


class PlacementContractError(ValueError):
    """Raised when deterministic SL/TP placement assumptions are violated."""


@dataclass(frozen=True)
class PlacementResult:
    initial_stop_price: float | None
    initial_target_price: float | None
    stop_model_applied: str
    take_profit_model_applied: str
    placement_computed_at_ts: pd.Timestamp | None
    placement_basis_ts: pd.Timestamp | None
    placement_status: str
    placement_notes: str
    risk_distance: float | None


def _require_columns(df: pd.DataFrame, required_columns: tuple[str, ...], label: str) -> None:
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise PlacementContractError(f"Missing required columns in {label}: {missing}")


def _parse_fixed_r_multiple(model: str) -> float | None:
    token = str(model).strip()
    prefix = "FIXED_R_MULTIPLE:"
    if not token.upper().startswith(prefix):
        return None
    value = token[len(prefix) :].strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _resolve_activation_ts(*, setup_bar_ts: pd.Timestamp, raw_timestamps: list[pd.Timestamp]) -> pd.Timestamp | None:
    for ts in raw_timestamps:
        if ts > setup_bar_ts:
            return ts
    return None


def _materialize_one(
    *,
    setup_row: pd.Series,
    ruleset_row: pd.Series,
    raw_open_by_ts: dict[pd.Timestamp, float],
    raw_timestamps: list[pd.Timestamp],
) -> PlacementResult:
    stop_model = str(ruleset_row["stop_model"]).strip()
    tp_model = str(ruleset_row["take_profit_model"]).strip()

    direction = str(setup_row["Direction"]).strip().upper()
    if direction not in {"LONG", "SHORT"}:
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_UNSUPPORTED_MODEL,
            placement_notes="unsupported_direction",
            risk_distance=None,
        )

    if stop_model != "REFERENCE_LEVEL_HARD_STOP":
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_UNSUPPORTED_MODEL,
            placement_notes="unsupported_stop_model",
            risk_distance=None,
        )

    r_multiple = _parse_fixed_r_multiple(tp_model)
    if r_multiple is None or r_multiple != 1.5:
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_UNSUPPORTED_MODEL,
            placement_notes="unsupported_take_profit_model",
            risk_distance=None,
        )

    entry_convention = str(ruleset_row["entry_price_convention"]).strip().upper()
    if entry_convention != "NEXT_BAR_OPEN":
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_UNSUPPORTED_MODEL,
            placement_notes="unsupported_entry_price_convention",
            risk_distance=None,
        )

    setup_bar_ts = pd.to_datetime(setup_row["SetupBarTs"], utc=True)
    activation_ts = _resolve_activation_ts(setup_bar_ts=setup_bar_ts, raw_timestamps=raw_timestamps)
    if activation_ts is None:
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_INSUFFICIENT_DATA,
            placement_notes="missing_activation_bar",
            risk_distance=None,
        )

    reference_level_raw = setup_row.get("ReferenceLevel")
    if pd.isna(reference_level_raw):
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=activation_ts,
            placement_basis_ts=activation_ts,
            placement_status=PLACEMENT_STATUS_INSUFFICIENT_DATA,
            placement_notes="missing_reference_level",
            risk_distance=None,
        )

    stop_price = float(reference_level_raw)
    if activation_ts not in raw_open_by_ts:
        return PlacementResult(
            initial_stop_price=None,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=None,
            placement_basis_ts=None,
            placement_status=PLACEMENT_STATUS_INSUFFICIENT_DATA,
            placement_notes="missing_activation_open",
            risk_distance=None,
        )

    entry_proxy = float(raw_open_by_ts[activation_ts])
    risk_distance = abs(entry_proxy - stop_price)
    if risk_distance <= 0:
        return PlacementResult(
            initial_stop_price=stop_price,
            initial_target_price=None,
            stop_model_applied=stop_model,
            take_profit_model_applied=tp_model,
            placement_computed_at_ts=activation_ts,
            placement_basis_ts=activation_ts,
            placement_status=PLACEMENT_STATUS_INVALID_RISK,
            placement_notes="risk_distance_non_positive",
            risk_distance=risk_distance,
        )

    if direction == "LONG":
        target_price = entry_proxy + (r_multiple * risk_distance)
    else:
        target_price = entry_proxy - (r_multiple * risk_distance)

    return PlacementResult(
        initial_stop_price=stop_price,
        initial_target_price=float(target_price),
        stop_model_applied=stop_model,
        take_profit_model_applied=tp_model,
        placement_computed_at_ts=activation_ts,
        placement_basis_ts=activation_ts,
        placement_status=PLACEMENT_STATUS_PLACED,
        placement_notes="placement_v1_ok",
        risk_distance=float(risk_distance),
    )


def materialize_stop_target_levels(
    *,
    rulesets_df: pd.DataFrame,
    setups_df: pd.DataFrame,
    raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """Materialize canonical initial SL/TP levels before replay engine execution."""
    _require_columns(rulesets_df, REQUIRED_RULESET_COLUMNS, "rulesets_df")
    _require_columns(setups_df, REQUIRED_SETUP_COLUMNS, "setups_df")
    _require_columns(raw_df, REQUIRED_RAW_COLUMNS, "raw_df")

    if len(rulesets_df.index) != 1:
        raise PlacementContractError(
            "v1 placement contract requires exactly one ruleset row per replay run, "
            f"got {len(rulesets_df.index)}"
        )

    ruleset = rulesets_df.iloc[0]

    raw = raw_df.copy()
    raw["Timestamp"] = pd.to_datetime(raw["Timestamp"], utc=True, errors="raise")
    raw = raw.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)
    raw_open_by_ts = {pd.Timestamp(ts): float(op) for ts, op in zip(raw["Timestamp"], raw["Open"], strict=False)}
    raw_timestamps = [pd.Timestamp(ts) for ts in raw["Timestamp"].tolist()]

    out = setups_df.copy()
    out["SetupBarTs"] = pd.to_datetime(out["SetupBarTs"], utc=True, errors="raise")

    materialized: list[PlacementResult] = []
    for _, setup in out.iterrows():
        result = _materialize_one(
            setup_row=setup,
            ruleset_row=ruleset,
            raw_open_by_ts=raw_open_by_ts,
            raw_timestamps=raw_timestamps,
        )
        materialized.append(result)

    for column in PLACEMENT_COLUMNS:
        out[column] = [getattr(item, column) for item in materialized]

    invalid_statuses = sorted(set(out["placement_status"].astype(str)) - PLACEMENT_STATUSES)
    if invalid_statuses:
        raise PlacementContractError(f"Unexpected placement_status values produced: {invalid_statuses}")

    return out
