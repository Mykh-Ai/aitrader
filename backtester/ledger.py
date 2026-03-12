"""Trade ledger materialization for Backtester Phase 3 Step 2B."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

LEDGER_COLUMNS = [
    "trade_id",
    "ruleset_id",
    "source_setup_id",
    "direction",
    "entry_signal_ts",
    "entry_activation_ts",
    "entry_price_raw",
    "entry_price_effective",
    "initial_stop_price",
    "initial_target_price",
    "expiry_ts",
    "exit_ts",
    "exit_price_raw",
    "exit_price_effective",
    "exit_reason",
    "exit_reason_category",
    "holding_bars",
    "cost_model_id",
    "same_bar_policy_id",
    "replay_semantics_version",
    "notes",
]

REQUIRED_EVENT_COLUMNS = (
    "event_id",
    "ruleset_id",
    "event_type",
    "timestamp",
    "source_setup_id",
    "direction",
    "state_after",
    "price_raw",
    "price_effective",
    "same_bar_policy_id",
    "same_bar_outcome",
    "cost_model_id",
    "replay_semantics_version",
    "notes",
)

RESOLVED_EXIT_CATEGORIES = {"STOP", "TARGET", "EXPIRY", "INVALIDATION", "RULE_CLOSE", "OTHER"}
UNRESOLVED_EXIT_REASONS = {
    "UNRESOLVED",
    "DEFERRED",
    "NO_EXIT_RESOLVED_YET",
}


class LedgerContractError(ValueError):
    """Raised when event-to-ledger materialization contract is violated."""


@dataclass(frozen=True)
class TradeLedgerRow:
    """Immutable trade ledger row schema for one simulated trade."""

    trade_id: str
    ruleset_id: str
    source_setup_id: str
    direction: str
    entry_signal_ts: pd.Timestamp | None
    entry_activation_ts: pd.Timestamp
    entry_price_raw: float | None
    entry_price_effective: float | None
    initial_stop_price: float | None
    initial_target_price: float | None
    expiry_ts: pd.Timestamp | None
    exit_ts: pd.Timestamp | None
    exit_price_raw: float | None
    exit_price_effective: float | None
    exit_reason: str
    exit_reason_category: str
    holding_bars: int | None
    cost_model_id: str
    same_bar_policy_id: str
    replay_semantics_version: str
    notes: str


def _require_event_columns(events_df: pd.DataFrame) -> None:
    missing = sorted(set(REQUIRED_EVENT_COLUMNS) - set(events_df.columns))
    if missing:
        raise LedgerContractError(f"Missing required replay event columns: {missing}")


def _normalize_events(events_df: pd.DataFrame) -> pd.DataFrame:
    out = events_df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    if "bar_timestamp" in out.columns:
        out["bar_timestamp"] = pd.to_datetime(out["bar_timestamp"], utc=True, errors="raise")
    else:
        out["bar_timestamp"] = out["timestamp"]

    sort_columns = ["timestamp", "bar_timestamp", "ruleset_id", "source_setup_id", "event_id"]
    return out.sort_values(sort_columns, kind="mergesort").reset_index(drop=True)


def _derive_exit(close_event: pd.Series | None, expiry_event: pd.Series | None) -> tuple[str, str, pd.Timestamp | None, float | None, float | None, str]:
    if close_event is None:
        if expiry_event is not None and "EXPIR" in str(expiry_event.get("state_after", "")).upper():
            return (
                "EXPIRY_CLOSE",
                "EXPIRY",
                expiry_event["timestamp"],
                expiry_event.get("price_raw"),
                expiry_event.get("price_effective"),
                "derived_from_expiry_state_after",
            )
        return "NO_EXIT_RESOLVED_YET", "UNRESOLVED", None, None, None, ""

    same_bar_outcome = str(close_event.get("same_bar_outcome", "NONE")).strip().upper()
    close_notes = str(close_event.get("notes", ""))

    if same_bar_outcome == "STOP_WINS":
        return (
            "SAME_BAR_STOP_WINS_POLICY",
            "STOP",
            close_event["timestamp"],
            close_event.get("price_raw"),
            close_event.get("price_effective"),
            "",
        )
    if same_bar_outcome == "TARGET_WINS":
        return (
            "SAME_BAR_TARGET_WINS_POLICY",
            "TARGET",
            close_event["timestamp"],
            close_event.get("price_raw"),
            close_event.get("price_effective"),
            "",
        )
    if same_bar_outcome in {"UNRESOLVED", "DEFERRED"}:
        return same_bar_outcome, "UNRESOLVED", None, None, None, ""

    if "not_resolved" in close_notes:
        return "UNRESOLVED", "UNRESOLVED", None, None, None, ""

    state_after = str(close_event.get("state_after", "")).upper()
    if "EXPIR" in state_after:
        return (
            "EXPIRY_CLOSE",
            "EXPIRY",
            close_event["timestamp"],
            close_event.get("price_raw"),
            close_event.get("price_effective"),
            "",
        )

    return (
        "RULE_CLOSE",
        "RULE_CLOSE",
        close_event["timestamp"],
        close_event.get("price_raw"),
        close_event.get("price_effective"),
        "",
    )


def _parse_numeric(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _materialize_trade_rows(events_df: pd.DataFrame) -> list[TradeLedgerRow]:
    rows: list[TradeLedgerRow] = []

    grouped = events_df.groupby(["ruleset_id", "source_setup_id"], sort=False)
    for (ruleset_id, setup_id), group in grouped:
        group = group.reset_index(drop=True)
        activation_indexes = group.index[group["event_type"] == "ENTRY_ACTIVATED"].tolist()
        if not activation_indexes:
            continue

        for ordinal, activation_idx in enumerate(activation_indexes, start=1):
            next_activation_idx = (
                activation_indexes[ordinal] if ordinal < len(activation_indexes) else len(group)
            )
            window = group.iloc[activation_idx:next_activation_idx].reset_index(drop=True)
            activation = window.iloc[0]

            signal_events = group.iloc[: activation_idx + 1]
            signal_subset = signal_events[signal_events["event_type"] == "SIGNAL_ACTIONABLE"]
            signal_ts = signal_subset.iloc[-1]["timestamp"] if not signal_subset.empty else pd.NaT

            stop_eval = window[window["event_type"] == "STOP_EVALUATED"]
            target_eval = window[window["event_type"] == "TARGET_EVALUATED"]
            close_eval = window[window["event_type"] == "CLOSE_RESOLVED"]
            expiry_eval = window[window["event_type"] == "EXPIRY_EVALUATED"]

            close_event = close_eval.iloc[-1] if not close_eval.empty else None
            expiry_event = expiry_eval.iloc[-1] if not expiry_eval.empty else None
            exit_reason, exit_category, exit_ts, exit_raw, exit_effective, extra_note = _derive_exit(
                close_event,
                expiry_event,
            )

            entry_ts = activation["timestamp"]
            if pd.isna(entry_ts):
                raise LedgerContractError(
                    "ENTRY_ACTIVATED event missing timestamp; cannot materialize honest trade row"
                )

            if pd.notna(signal_ts) and entry_ts < signal_ts:
                raise LedgerContractError(
                    f"entry_activation_ts earlier than entry_signal_ts for ruleset={ruleset_id}, setup={setup_id}"
                )

            if exit_ts is not None:
                holding_bars = int((events_df["timestamp"].drop_duplicates().sort_values().tolist().index(exit_ts)) - (events_df["timestamp"].drop_duplicates().sort_values().tolist().index(entry_ts)))
            else:
                holding_bars = None

            if holding_bars is not None and holding_bars < 0:
                raise LedgerContractError(
                    f"Negative holding_bars for ruleset={ruleset_id}, setup={setup_id}"
                )

            notes = ""
            window_notes = [str(n) for n in window["notes"].dropna().tolist() if str(n).strip()]
            if window_notes:
                notes = " | ".join(window_notes)
            if extra_note:
                notes = f"{notes} | {extra_note}" if notes else extra_note

            trade_id = f"TRADE_{ruleset_id}_{setup_id}" if len(activation_indexes) == 1 else f"TRADE_{ruleset_id}_{setup_id}_{ordinal}"

            row = TradeLedgerRow(
                trade_id=trade_id,
                ruleset_id=str(ruleset_id),
                source_setup_id=str(setup_id),
                direction=str(activation["direction"]),
                entry_signal_ts=(None if pd.isna(signal_ts) else signal_ts),
                entry_activation_ts=entry_ts,
                entry_price_raw=_parse_numeric(activation.get("price_raw")),
                entry_price_effective=_parse_numeric(activation.get("price_effective")),
                initial_stop_price=_parse_numeric(stop_eval.iloc[-1]["price_raw"]) if not stop_eval.empty else None,
                initial_target_price=_parse_numeric(target_eval.iloc[-1]["price_raw"]) if not target_eval.empty else None,
                expiry_ts=(None if expiry_event is None else expiry_event["timestamp"]),
                exit_ts=exit_ts,
                exit_price_raw=_parse_numeric(exit_raw),
                exit_price_effective=_parse_numeric(exit_effective),
                exit_reason=exit_reason,
                exit_reason_category=exit_category,
                holding_bars=holding_bars,
                cost_model_id=str(activation["cost_model_id"]),
                same_bar_policy_id=str(activation["same_bar_policy_id"]),
                replay_semantics_version=str(activation["replay_semantics_version"]),
                notes=notes,
            )
            rows.append(row)

    return rows


def validate_trade_ledger(ledger_df: pd.DataFrame) -> None:
    missing_fields = sorted(set(LEDGER_COLUMNS) - set(ledger_df.columns))
    if missing_fields:
        raise LedgerContractError(f"Trade ledger missing required fields: {missing_fields}")

    dupes = ledger_df[ledger_df["trade_id"].duplicated()]["trade_id"].tolist()
    if dupes:
        raise LedgerContractError(f"Duplicate trade_id values found: {dupes}")

    if ledger_df["ruleset_id"].isna().any() or (ledger_df["ruleset_id"].astype(str).str.strip() == "").any():
        raise LedgerContractError("Each trade row must have exactly one non-empty ruleset_id")

    if ledger_df["source_setup_id"].isna().any() or (
        ledger_df["source_setup_id"].astype(str).str.strip() == ""
    ).any():
        raise LedgerContractError("Each trade row must have exactly one non-empty source_setup_id")

    if ledger_df["entry_activation_ts"].isna().any():
        raise LedgerContractError("entry_activation_ts is required for every trade row")

    for row in ledger_df.itertuples(index=False):
        if row.entry_signal_ts is not pd.NaT and row.entry_signal_ts is not None and row.entry_activation_ts < row.entry_signal_ts:
            raise LedgerContractError(
                f"entry_activation_ts < entry_signal_ts for trade_id={row.trade_id}"
            )
        if row.holding_bars is not None and row.holding_bars < 0:
            raise LedgerContractError(f"holding_bars < 0 for trade_id={row.trade_id}")
        if pd.notna(row.exit_price_raw) and (row.exit_reason is None or str(row.exit_reason).strip() == ""):
            raise LedgerContractError(
                f"exit_price_raw present but exit_reason missing for trade_id={row.trade_id}"
            )
        if row.exit_reason_category in RESOLVED_EXIT_CATEGORIES and pd.isna(row.exit_ts):
            raise LedgerContractError(
                f"Resolved exit category requires exit_ts for trade_id={row.trade_id}"
            )
        if row.exit_reason_category == "UNRESOLVED" and row.exit_reason not in UNRESOLVED_EXIT_REASONS:
            raise LedgerContractError(
                f"Unresolved trade must use explicit unresolved reason for trade_id={row.trade_id}"
            )


def build_trade_ledger(
    engine_events_df: pd.DataFrame,
    *,
    rulesets_df: pd.DataFrame | None = None,
    setup_lineage_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Materialize immutable trade rows from deterministic replay events only."""
    del rulesets_df, setup_lineage_df

    _require_event_columns(engine_events_df)
    events = _normalize_events(engine_events_df)

    rows = _materialize_trade_rows(events)
    ledger_df = pd.DataFrame([asdict(row) for row in rows], columns=LEDGER_COLUMNS)

    for ts_col in ["entry_signal_ts", "entry_activation_ts", "expiry_ts", "exit_ts"]:
        if ts_col in ledger_df.columns:
            ledger_df[ts_col] = pd.to_datetime(ledger_df[ts_col], utc=True, errors="coerce")

    ledger_df = ledger_df.sort_values(["entry_activation_ts", "trade_id"], kind="mergesort").reset_index(drop=True)
    validate_trade_ledger(ledger_df)
    return ledger_df


def write_trade_ledger_csv(
    *,
    ledger_df: pd.DataFrame,
    output_dir: str | Path,
) -> Path:
    """Persist backtest trade ledger artifact as backtest_trades.csv."""
    validate_trade_ledger(ledger_df)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    trades_path = output_path / "backtest_trades.csv"
    ledger_df.to_csv(trades_path, index=False)
    return trades_path
