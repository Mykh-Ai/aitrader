"""H4 active-level reclaim-close diagnostic.

This script intentionally does not use the legacy failed-break/reclaim detector
and does not run the Backtester. It scans UTC H4 candles for 3-candle active
high/low levels, waits for an H4 sweep, then records reclaim closes within the
next three H4 candles.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analyzer.loader import load_raw_csv


VARIANT_ID = "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1"
DEFAULT_START_DATE = "2026-03-30"
DEFAULT_END_DATE = "2026-05-02"
DEFAULT_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_filtered_diagnostic_2026-03-30_to_2026-05-02.csv"
)
DEFAULT_LONG_AUDIT_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_long_active_low_audit_2026-03-30_to_2026-05-02.csv"
)
DEFAULT_FINDING_OUTPUT = (
    "research/findings/"
    "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_FILTERED_DIAGNOSTIC_2026-05-04.md"
)
BUFFER50_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_filtered_diagnostic_buffer50_2026-03-30_to_2026-05-02.csv"
)
BUFFER50_FINDING_OUTPUT = (
    "research/findings/"
    "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_BUFFER50_DIAGNOSTIC_2026-05-04.md"
)
LONG_LOW_SELECTION_AUDIT_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_long_low_selection_audit_2026-03-30_to_2026-05-02.csv"
)
LONG_LOW_SELECTION_FINDING_OUTPUT = (
    "research/findings/"
    "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_LONG_LOW_SELECTION_AUDIT_2026-05-04.md"
)
COMPRESSED_BUFFER350_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_compressed_buffer350_2026-03-30_to_2026-05-02.csv"
)
COMPRESSED_BUFFER350_FINDING_OUTPUT = (
    "research/findings/"
    "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_COMPRESSED_BUFFER350_DIAGNOSTIC_2026-05-04.md"
)
LEVEL_REGISTRY_OUTPUT = (
    "research/results/"
    "h4_active_level_reclaim_close_test_v1_level_registry_2026-03-30_to_2026-05-02.csv"
)
LEVEL_REGISTRY_FINDING_OUTPUT = (
    "research/findings/"
    "H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_LEVEL_REGISTRY_DIAGNOSTIC_2026-05-04.md"
)
LOCAL_H4_VARIANT_ID = "LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1"
LOCAL_H4_BUFFER50_OUTPUT = (
    "research/results/"
    "local_h4_reclaim_sweep_extreme_stop_v1_buffer50_2026-05-05.csv"
)
LOCAL_H4_BUFFER50_FINDING_OUTPUT = (
    "research/findings/"
    "LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md"
)

ACTIVE_LEVEL_TTL_H4_BARS = 30
RECLAIM_WINDOW_H4_BARS = 3
STOP_BUFFER_USD = 350.0
MAX_RISK_USD = 1500.0
PATH_WINDOW_MINUTES = 4 * 24 * 60
FUTURE_WINDOWS = {
    "24h": (24 * 60, "favorable_move_24h_usd", "adverse_move_24h_usd"),
    "48h": (48 * 60, "favorable_move_48h_usd", "adverse_move_48h_usd"),
    "96h": (96 * 60, "favorable_move_96h_usd", "adverse_move_96h_usd"),
}

OUTPUT_COLUMNS = [
    "row_number",
    "candidate_id",
    "direction",
    "active_level_price",
    "active_level_source",
    "promoted_from_pending",
    "pending_queue_size_at_activation",
    "previous_expired_level_price",
    "previous_expired_level_confirmed_ts",
    "active_level_confirmed_ts",
    "active_level_age_h4_bars",
    "ignored_levels_count_before_activation",
    "pending_levels_dropped_swept_count",
    "pending_levels_dropped_expired_count",
    "sweep_h4_open_ts",
    "sweep_h4_close_ts",
    "sweep_extreme_price",
    "reclaim_h4_open_ts",
    "reclaim_h4_close_ts",
    "reclaim_h4_open_price",
    "reclaim_close_price",
    "reclaim_bar_number_after_sweep",
    "entry_ts",
    "entry_price",
    "stop_price",
    "risk_usd",
    "stop_buffer_usd",
    "stop_price_buffer_50",
    "risk_usd_buffer_50",
    "risk_gate_pass",
    "candle_color_gate_pass",
    "diagnostic_trade_allowed",
    "no_trade_reason",
    "diagnostic_trade_allowed_buffer_50",
    "no_trade_reason_buffer_50",
    "diagnostic_trade_allowed_buffer_50_long_with_color_gate",
    "no_trade_reason_buffer_50_long_with_color_gate",
    "diagnostic_trade_allowed_buffer_50_long_without_color_gate",
    "no_trade_reason_buffer_50_long_without_color_gate",
    "favorable_move_24h_usd",
    "adverse_move_24h_usd",
    "favorable_move_48h_usd",
    "adverse_move_48h_usd",
    "favorable_move_96h_usd",
    "adverse_move_96h_usd",
    "hit_1000_favorable_96h",
    "first_stop_touch_ts",
    "first_1R_touch_ts",
    "first_1_5R_touch_ts",
    "first_2R_touch_ts",
    "hit_1R_before_stop",
    "hit_1_5R_before_stop",
    "hit_2R_before_stop",
    "stop_before_1R",
    "stop_before_1_5R",
    "stop_before_2R",
    "same_bar_stop_1R",
    "same_bar_stop_1_5R",
    "same_bar_stop_2R",
    "max_favorable_before_stop",
    "max_adverse_before_1R",
    "max_adverse_before_1_5R",
    "max_adverse_before_2R",
    "notes",
]

INTERNAL_COLUMNS = [
    "_active_level_confirmed_idx",
    "_sweep_h4_idx",
    "_reclaim_h4_idx",
]

LONG_AUDIT_COLUMNS = [
    "candidate_id",
    "active_low_price",
    "active_low_confirmed_ts",
    "active_low_age_h4_bars",
    "sweep_h4_open_ts",
    "sweep_extreme_low",
    "h4_low_broke_active_low",
    "nearest_recent_pivot_low_price",
    "nearest_recent_pivot_low_ts",
    "nearest_recent_pivot_low_age_h4_bars",
    "h4_low_broke_nearest_recent_pivot_low",
    "suspected_issue",
    "note",
]

LONG_LOW_SELECTION_AUDIT_COLUMNS = [
    "row_number",
    "candidate_id",
    "entry_ts",
    "direction",
    "main_active_low_price",
    "main_active_low_confirmed_ts",
    "main_active_low_age_h4_bars_at_sweep",
    "nearest_internal_higher_low_price",
    "nearest_internal_higher_low_ts",
    "nearest_internal_higher_low_age_h4_bars",
    "swept_main_active_low",
    "swept_internal_higher_low",
    "sweep_extreme_low",
    "reclaim_h4_close_ts",
    "reclaim_close_price",
    "low_selection_mode_used_by_script",
    "expected_mode_by_contract",
    "contract_violation",
    "suspected_issue",
    "possible_separate_pattern",
    "note",
]

COMPRESSED_OUTPUT_COLUMNS = [
    "row_number",
    "candidate_id",
    "direction",
    "entry_ts",
    "entry_price",
    "sweep_extreme_price",
    "raw_sweep_risk_usd",
    "desired_stop_price",
    "desired_risk_usd",
    "final_stop_price",
    "final_risk_usd",
    "applied_buffer_usd",
    "buffer_was_compressed",
    "candle_color_gate_pass",
    "diagnostic_trade_allowed",
    "no_trade_reason",
    "first_stop_touch_ts",
    "first_1R_touch_ts",
    "first_1_5R_touch_ts",
    "first_2R_touch_ts",
    "hit_1R_before_stop",
    "hit_1_5R_before_stop",
    "hit_2R_before_stop",
    "stop_before_1R",
    "stop_before_1_5R",
    "stop_before_2R",
    "same_bar_stop_1R",
    "same_bar_stop_1_5R",
    "same_bar_stop_2R",
]

LOCAL_H4_OUTPUT_COLUMNS = [
    "candidate_id",
    "row_number",
    "direction",
    "level_price",
    "level_confirmed_ts",
    "level_family",
    "sweep_h4_open_ts",
    "sweep_extreme_price",
    "reclaim_h4_close_ts",
    "entry_ts",
    "entry_price",
    "stop_price",
    "final_risk_usd",
    "diagnostic_trade_allowed",
    "no_trade_reason",
    "hit_1R_before_stop",
    "hit_1_5R_before_stop",
    "hit_2R_before_stop",
    "first_stop_touch_ts",
    "same_bar_ambiguity",
]


@dataclass(frozen=True)
class ConfirmedLevel:
    side: str
    price: float
    confirmed_ts: pd.Timestamp
    confirmed_idx: int


@dataclass
class ActiveLevel:
    side: str
    price: float
    confirmed_ts: pd.Timestamp
    confirmed_idx: int
    source: str = "direct_new_pivot"
    promoted_from_pending: bool = False
    pending_queue_size_at_activation: int = 0
    previous_expired_level_price: float | None = None
    previous_expired_level_confirmed_ts: pd.Timestamp | None = None
    ignored_levels_count_before_activation: int = 0
    pending_levels_dropped_swept_count: int = 0
    pending_levels_dropped_expired_count: int = 0
    state: str = "ACTIVE"
    sweep_idx: int | None = None
    sweep_open_ts: pd.Timestamp | None = None
    sweep_close_ts: pd.Timestamp | None = None
    sweep_extreme_price: float | None = None


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _iter_feed_paths(feed_dir: Path, start: date, end: date) -> list[Path]:
    paths: list[Path] = []
    cursor = start
    while cursor <= end:
        path = feed_dir / f"{cursor.isoformat()}.csv"
        if path.exists():
            paths.append(path)
        cursor += timedelta(days=1)
    return paths


def load_feed(feed_dir: Path, start: date, end: date) -> pd.DataFrame:
    paths = _iter_feed_paths(feed_dir, start, end)
    if not paths:
        raise FileNotFoundError(f"No feed CSV files found in {feed_dir} for {start}..{end}")

    frames = [load_raw_csv(path) for path in paths]
    raw = pd.concat(frames, ignore_index=True, sort=False)
    raw = raw.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)
    duplicate_ts = raw["Timestamp"].duplicated(keep=False)
    if duplicate_ts.any():
        sample = raw.loc[duplicate_ts, "Timestamp"].head(5).astype(str).tolist()
        raise ValueError(f"Duplicate normalized feed timestamps after concat: {sample}")
    return raw


def build_h4_bars(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"Timestamp", "Open", "High", "Low", "Close"}
    missing = required - set(raw.columns)
    if missing:
        raise KeyError(f"Missing required raw columns for H4 diagnostic: {sorted(missing)}")

    data = raw.loc[:, ["Timestamp", "Open", "High", "Low", "Close"]].copy()
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], utc=True, errors="raise")
    bars = (
        data.set_index("Timestamp")
        .resample("4h", label="left", closed="left")
        .agg(
            Open=("Open", "first"),
            High=("High", "max"),
            Low=("Low", "min"),
            Close=("Close", "last"),
            RowCount=("Close", "count"),
        )
        .dropna(subset=["Open", "High", "Low", "Close"])
        .reset_index()
        .rename(columns={"Timestamp": "h4_open_ts"})
    )
    bars["h4_open_ts"] = pd.to_datetime(bars["h4_open_ts"], utc=True)
    bars["h4_close_ts"] = bars["h4_open_ts"] + pd.Timedelta(hours=4)
    return bars.reset_index(drop=True)


def confirmed_levels(h4: pd.DataFrame) -> dict[int, list[ConfirmedLevel]]:
    by_idx: dict[int, list[ConfirmedLevel]] = {}
    if len(h4.index) < 3:
        return by_idx

    for idx in range(1, len(h4.index) - 1):
        prev_bar = h4.iloc[idx - 1]
        center = h4.iloc[idx]
        next_bar = h4.iloc[idx + 1]
        confirm_idx = idx + 2
        if confirm_idx >= len(h4.index):
            continue

        confirmed_ts = pd.Timestamp(h4.iloc[confirm_idx]["h4_open_ts"])
        if float(center["High"]) > float(prev_bar["High"]) and float(center["High"]) > float(next_bar["High"]):
            by_idx.setdefault(confirm_idx, []).append(
                ConfirmedLevel(
                    side="HIGH",
                    price=float(center["High"]),
                    confirmed_ts=confirmed_ts,
                    confirmed_idx=confirm_idx,
                )
            )
        if float(center["Low"]) < float(prev_bar["Low"]) and float(center["Low"]) < float(next_bar["Low"]):
            by_idx.setdefault(confirm_idx, []).append(
                ConfirmedLevel(
                    side="LOW",
                    price=float(center["Low"]),
                    confirmed_ts=confirmed_ts,
                    confirmed_idx=confirm_idx,
                )
            )
    return by_idx


def _candidate_id(direction: str, active: ActiveLevel, reclaim_close_ts: pd.Timestamp) -> str:
    payload = (
        f"{VARIANT_ID}|{direction}|{active.confirmed_ts.isoformat()}|"
        f"{active.price:.8f}|{reclaim_close_ts.isoformat()}"
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"H4ARCT1_{direction}_{digest}"


def _local_h4_candidate_id(
    direction: str,
    level: ConfirmedLevel,
    reclaim_close_ts: pd.Timestamp,
) -> str:
    payload = (
        f"{LOCAL_H4_VARIANT_ID}|{direction}|{level.confirmed_ts.isoformat()}|"
        f"{level.price:.8f}|{reclaim_close_ts.isoformat()}"
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"LH4RSE1_{direction}_{digest}"


def _level_family(
    *,
    direction: str,
    level: ConfirmedLevel,
    sweep_idx: int,
    levels_by_idx: dict[int, list[ConfirmedLevel]],
    lookback_h4_bars: int = ACTIVE_LEVEL_TTL_H4_BARS,
) -> str:
    side = "HIGH" if direction == "SHORT" else "LOW"
    recent: list[ConfirmedLevel] = []
    for idx, levels in levels_by_idx.items():
        if sweep_idx - lookback_h4_bars <= idx <= sweep_idx:
            recent.extend(item for item in levels if item.side == side)

    if not recent:
        return "LOCAL_LOWER_HIGH_SWEEP" if direction == "SHORT" else "LOCAL_HIGHER_LOW_SWEEP"

    if direction == "SHORT":
        structural = max(recent, key=lambda item: (item.price, item.confirmed_idx))
        if (
            abs(float(level.price) - float(structural.price)) <= 1e-9
            and level.confirmed_idx == structural.confirmed_idx
        ):
            return "MAIN_STRUCTURAL_HIGH_SWEEP"
        return "LOCAL_LOWER_HIGH_SWEEP"

    structural = min(recent, key=lambda item: (item.price, -item.confirmed_idx))
    if (
        abs(float(level.price) - float(structural.price)) <= 1e-9
        and level.confirmed_idx == structural.confirmed_idx
    ):
        return "MAIN_STRUCTURAL_LOW_SWEEP"
    return "LOCAL_HIGHER_LOW_SWEEP"


def _base_candidate_row(
    *,
    direction: str,
    active: ActiveLevel,
    bar: pd.Series,
    reclaim_number: int,
) -> dict[str, object]:
    reclaim_open_ts = pd.Timestamp(bar["h4_open_ts"])
    reclaim_close_ts = pd.Timestamp(bar["h4_close_ts"])
    reclaim_open = float(bar["Open"])
    reclaim_close = float(bar["Close"])
    return {
        "candidate_id": _candidate_id(direction, active, reclaim_close_ts),
        "direction": direction,
        "active_level_price": active.price,
        "active_level_source": active.source,
        "promoted_from_pending": active.promoted_from_pending,
        "pending_queue_size_at_activation": active.pending_queue_size_at_activation,
        "previous_expired_level_price": active.previous_expired_level_price,
        "previous_expired_level_confirmed_ts": active.previous_expired_level_confirmed_ts,
        "active_level_confirmed_ts": active.confirmed_ts,
        "active_level_age_h4_bars": int((active.sweep_idx or 0) - active.confirmed_idx),
        "ignored_levels_count_before_activation": active.ignored_levels_count_before_activation,
        "pending_levels_dropped_swept_count": active.pending_levels_dropped_swept_count,
        "pending_levels_dropped_expired_count": active.pending_levels_dropped_expired_count,
        "sweep_h4_open_ts": active.sweep_open_ts,
        "sweep_h4_close_ts": active.sweep_close_ts,
        "sweep_extreme_price": active.sweep_extreme_price,
        "reclaim_h4_open_ts": reclaim_open_ts,
        "reclaim_h4_close_ts": reclaim_close_ts,
        "reclaim_h4_open_price": reclaim_open,
        "reclaim_close_price": reclaim_close,
        "reclaim_bar_number_after_sweep": reclaim_number,
        "entry_ts": reclaim_close_ts,
        "entry_price": reclaim_close,
        "_active_level_confirmed_idx": active.confirmed_idx,
        "_sweep_h4_idx": active.sweep_idx,
        "_reclaim_h4_idx": int(active.sweep_idx or 0) + reclaim_number,
        "notes": "diagnostic_only;h4_reclaim_close_entry;legacy_failed_break_reclaim_not_used",
    }


def _make_active_level(
    level: ConfirmedLevel,
    *,
    source: str,
    promoted_from_pending: bool,
    pending_queue_size_at_activation: int,
    previous_expired_level: ActiveLevel | None,
    ignored_levels_count_before_activation: int,
    pending_levels_dropped_swept_count: int,
    pending_levels_dropped_expired_count: int,
) -> ActiveLevel:
    return ActiveLevel(
        side=level.side,
        price=level.price,
        confirmed_ts=level.confirmed_ts,
        confirmed_idx=level.confirmed_idx,
        source=source,
        promoted_from_pending=promoted_from_pending,
        pending_queue_size_at_activation=pending_queue_size_at_activation,
        previous_expired_level_price=(
            previous_expired_level.price if previous_expired_level is not None else None
        ),
        previous_expired_level_confirmed_ts=(
            previous_expired_level.confirmed_ts if previous_expired_level is not None else None
        ),
        ignored_levels_count_before_activation=ignored_levels_count_before_activation,
        pending_levels_dropped_swept_count=pending_levels_dropped_swept_count,
        pending_levels_dropped_expired_count=pending_levels_dropped_expired_count,
    )


def _pending_level_was_swept(level: ConfirmedLevel, bar: pd.Series) -> bool:
    if level.side == "HIGH":
        return bool(float(bar["High"]) > level.price)
    if level.side == "LOW":
        return bool(float(bar["Low"]) < level.price)
    raise ValueError(f"Unexpected level side: {level.side}")


def _drop_expired_pending(
    pending: list[ConfirmedLevel],
    *,
    idx: int,
) -> tuple[list[ConfirmedLevel], int]:
    kept: list[ConfirmedLevel] = []
    dropped = 0
    for level in pending:
        if idx - level.confirmed_idx > ACTIVE_LEVEL_TTL_H4_BARS:
            dropped += 1
        else:
            kept.append(level)
    return kept, dropped


def _drop_swept_pending(
    pending: list[ConfirmedLevel],
    *,
    bar: pd.Series,
) -> tuple[list[ConfirmedLevel], int]:
    kept: list[ConfirmedLevel] = []
    dropped = 0
    for level in pending:
        if _pending_level_was_swept(level, bar):
            dropped += 1
        else:
            kept.append(level)
    return kept, dropped


def _promote_latest_pending(
    pending: list[ConfirmedLevel],
    *,
    previous_expired_level: ActiveLevel | None,
    stats: dict[str, int],
) -> tuple[ActiveLevel | None, list[ConfirmedLevel]]:
    if not pending:
        return None, pending

    queue_size = len(pending)
    level = pending[-1]
    remaining = pending[:-1]
    return (
        _make_active_level(
            level,
            source="promoted_from_pending",
            promoted_from_pending=True,
            pending_queue_size_at_activation=queue_size,
            previous_expired_level=previous_expired_level,
            ignored_levels_count_before_activation=stats["ignored"],
            pending_levels_dropped_swept_count=stats["dropped_swept"],
            pending_levels_dropped_expired_count=stats["dropped_expired"],
        ),
        remaining,
    )


def _direct_activate(
    levels: list[ConfirmedLevel],
    *,
    side: str,
    stats: dict[str, int],
) -> ActiveLevel | None:
    matching = [level for level in levels if level.side == side]
    if not matching:
        return None
    return _make_active_level(
        matching[0],
        source="direct_new_pivot",
        promoted_from_pending=False,
        pending_queue_size_at_activation=0,
        previous_expired_level=None,
        ignored_levels_count_before_activation=stats["ignored"],
        pending_levels_dropped_swept_count=stats["dropped_swept"],
        pending_levels_dropped_expired_count=stats["dropped_expired"],
    )


def _store_pending_levels(
    pending: list[ConfirmedLevel],
    levels: list[ConfirmedLevel],
    *,
    side: str,
    stats: dict[str, int],
) -> list[ConfirmedLevel]:
    matching = [level for level in levels if level.side == side]
    if not matching:
        return pending
    stats["ignored"] += len(matching)
    return [*pending, *matching]


def scan_candidates(h4: pd.DataFrame) -> pd.DataFrame:
    levels_by_idx = confirmed_levels(h4)
    active_high: ActiveLevel | None = None
    active_low: ActiveLevel | None = None
    pending_high_levels: list[ConfirmedLevel] = []
    pending_low_levels: list[ConfirmedLevel] = []
    high_stats = {"ignored": 0, "dropped_swept": 0, "dropped_expired": 0}
    low_stats = {"ignored": 0, "dropped_swept": 0, "dropped_expired": 0}
    rows: list[dict[str, object]] = []

    for idx, bar in h4.iterrows():
        idx_int = int(idx)
        levels = levels_by_idx.get(int(idx), [])

        pending_high_levels, dropped = _drop_expired_pending(pending_high_levels, idx=idx_int)
        high_stats["dropped_expired"] += dropped
        pending_low_levels, dropped = _drop_expired_pending(pending_low_levels, idx=idx_int)
        low_stats["dropped_expired"] += dropped

        if active_high is not None and active_high.state == "ACTIVE":
            age = int(idx_int - active_high.confirmed_idx)
            if age > ACTIVE_LEVEL_TTL_H4_BARS:
                expired = active_high
                active_high, pending_high_levels = _promote_latest_pending(
                    pending_high_levels,
                    previous_expired_level=expired,
                    stats=high_stats,
                )

        if active_low is not None and active_low.state == "ACTIVE":
            age = int(idx_int - active_low.confirmed_idx)
            if age > ACTIVE_LEVEL_TTL_H4_BARS:
                expired = active_low
                active_low, pending_low_levels = _promote_latest_pending(
                    pending_low_levels,
                    previous_expired_level=expired,
                    stats=low_stats,
                )

        if active_high is None:
            active_high, pending_high_levels = _promote_latest_pending(
                pending_high_levels,
                previous_expired_level=None,
                stats=high_stats,
            )
        if active_low is None:
            active_low, pending_low_levels = _promote_latest_pending(
                pending_low_levels,
                previous_expired_level=None,
                stats=low_stats,
            )

        if active_high is None:
            active_high = _direct_activate(levels, side="HIGH", stats=high_stats)
        else:
            pending_high_levels = _store_pending_levels(
                pending_high_levels,
                levels,
                side="HIGH",
                stats=high_stats,
            )

        if active_low is None:
            active_low = _direct_activate(levels, side="LOW", stats=low_stats)
        else:
            pending_low_levels = _store_pending_levels(
                pending_low_levels,
                levels,
                side="LOW",
                stats=low_stats,
            )

        if active_high is not None:
            if active_high.state == "ACTIVE" and float(bar["High"]) > active_high.price:
                active_high.state = "SWEPT"
                active_high.sweep_idx = idx_int
                active_high.sweep_open_ts = pd.Timestamp(bar["h4_open_ts"])
                active_high.sweep_close_ts = pd.Timestamp(bar["h4_close_ts"])
                active_high.sweep_extreme_price = float(bar["High"])
            elif active_high.state == "SWEPT" and active_high.sweep_idx is not None:
                reclaim_number = int(idx_int - active_high.sweep_idx)
                if 1 <= reclaim_number <= RECLAIM_WINDOW_H4_BARS:
                    if float(bar["Close"]) < active_high.price:
                        rows.append(
                            _base_candidate_row(
                                direction="SHORT",
                                active=active_high,
                                bar=bar,
                                reclaim_number=reclaim_number,
                            )
                        )
                        active_high = None
                    elif reclaim_number == RECLAIM_WINDOW_H4_BARS:
                        active_high = None
                elif reclaim_number > RECLAIM_WINDOW_H4_BARS:
                    active_high = None

        if active_low is not None:
            if active_low.state == "ACTIVE" and float(bar["Low"]) < active_low.price:
                active_low.state = "SWEPT"
                active_low.sweep_idx = idx_int
                active_low.sweep_open_ts = pd.Timestamp(bar["h4_open_ts"])
                active_low.sweep_close_ts = pd.Timestamp(bar["h4_close_ts"])
                active_low.sweep_extreme_price = float(bar["Low"])
            elif active_low.state == "SWEPT" and active_low.sweep_idx is not None:
                reclaim_number = int(idx_int - active_low.sweep_idx)
                if 1 <= reclaim_number <= RECLAIM_WINDOW_H4_BARS:
                    if float(bar["Close"]) > active_low.price:
                        rows.append(
                            _base_candidate_row(
                                direction="LONG",
                                active=active_low,
                                bar=bar,
                                reclaim_number=reclaim_number,
                            )
                        )
                        active_low = None
                    elif reclaim_number == RECLAIM_WINDOW_H4_BARS:
                        active_low = None
                elif reclaim_number > RECLAIM_WINDOW_H4_BARS:
                    active_low = None

        pending_high_levels, dropped = _drop_swept_pending(pending_high_levels, bar=bar)
        high_stats["dropped_swept"] += dropped
        pending_low_levels, dropped = _drop_swept_pending(pending_low_levels, bar=bar)
        low_stats["dropped_swept"] += dropped

    if not rows:
        return pd.DataFrame(columns=[*OUTPUT_COLUMNS, *INTERNAL_COLUMNS])
    return pd.DataFrame(rows)


def _local_candidate_row(
    *,
    direction: str,
    level: ConfirmedLevel,
    level_family: str,
    sweep_idx: int,
    sweep_bar: pd.Series,
    sweep_extreme_price: float,
    reclaim_bar: pd.Series,
    reclaim_number: int,
) -> dict[str, object]:
    reclaim_close_ts = pd.Timestamp(reclaim_bar["h4_close_ts"])
    reclaim_close = float(reclaim_bar["Close"])
    return {
        "candidate_id": _local_h4_candidate_id(direction, level, reclaim_close_ts),
        "direction": direction,
        "level_price": level.price,
        "level_confirmed_ts": level.confirmed_ts,
        "level_family": level_family,
        "sweep_h4_open_ts": pd.Timestamp(sweep_bar["h4_open_ts"]),
        "sweep_h4_close_ts": pd.Timestamp(sweep_bar["h4_close_ts"]),
        "sweep_extreme_price": sweep_extreme_price,
        "reclaim_h4_open_ts": pd.Timestamp(reclaim_bar["h4_open_ts"]),
        "reclaim_h4_close_ts": reclaim_close_ts,
        "reclaim_close_price": reclaim_close,
        "reclaim_bar_number_after_sweep": reclaim_number,
        "entry_ts": reclaim_close_ts,
        "entry_price": reclaim_close,
        "_level_confirmed_idx": level.confirmed_idx,
        "_sweep_h4_idx": sweep_idx,
        "notes": "diagnostic_only;local_h4_reclaim_close_entry;sweep_extreme_stop_buffer50;legacy_failed_break_reclaim_not_used",
    }


def scan_local_h4_reclaim_candidates(h4: pd.DataFrame) -> pd.DataFrame:
    """Scan latest/local confirmed H4 pivots for sweep then H4 reclaim close.

    This intentionally differs from the active-level registry scanner: same-side
    confirmed pivots replace the selected level while it is not in a swept
    reclaim window. That preserves the old/local H4 swing-selection question
    without reusing the legacy failed-break detector or 1m entry semantics.
    """
    levels_by_idx = confirmed_levels(h4)
    selected_high: ConfirmedLevel | None = None
    selected_low: ConfirmedLevel | None = None
    swept_high: dict[str, object] | None = None
    swept_low: dict[str, object] | None = None
    rows: list[dict[str, object]] = []

    for idx, bar in h4.iterrows():
        idx_int = int(idx)
        levels = levels_by_idx.get(idx_int, [])

        if swept_high is not None:
            sweep_idx = int(swept_high["sweep_idx"])
            reclaim_number = idx_int - sweep_idx
            if 1 <= reclaim_number <= RECLAIM_WINDOW_H4_BARS:
                level = swept_high["level"]
                assert isinstance(level, ConfirmedLevel)
                if float(bar["Close"]) < level.price:
                    rows.append(
                        _local_candidate_row(
                            direction="SHORT",
                            level=level,
                            level_family=str(swept_high["level_family"]),
                            sweep_idx=sweep_idx,
                            sweep_bar=swept_high["sweep_bar"],  # type: ignore[arg-type]
                            sweep_extreme_price=float(swept_high["sweep_extreme_price"]),
                            reclaim_bar=bar,
                            reclaim_number=reclaim_number,
                        )
                    )
                    selected_high = None
                    swept_high = None
                elif reclaim_number == RECLAIM_WINDOW_H4_BARS:
                    selected_high = None
                    swept_high = None
            elif reclaim_number > RECLAIM_WINDOW_H4_BARS:
                selected_high = None
                swept_high = None
        else:
            high_levels = [level for level in levels if level.side == "HIGH"]
            if high_levels:
                selected_high = high_levels[-1]
            if selected_high is not None and float(bar["High"]) > selected_high.price:
                swept_high = {
                    "level": selected_high,
                    "level_family": _level_family(
                        direction="SHORT",
                        level=selected_high,
                        sweep_idx=idx_int,
                        levels_by_idx=levels_by_idx,
                    ),
                    "sweep_idx": idx_int,
                    "sweep_bar": bar,
                    "sweep_extreme_price": float(bar["High"]),
                }

        if swept_low is not None:
            sweep_idx = int(swept_low["sweep_idx"])
            reclaim_number = idx_int - sweep_idx
            if 1 <= reclaim_number <= RECLAIM_WINDOW_H4_BARS:
                level = swept_low["level"]
                assert isinstance(level, ConfirmedLevel)
                if float(bar["Close"]) > level.price:
                    rows.append(
                        _local_candidate_row(
                            direction="LONG",
                            level=level,
                            level_family=str(swept_low["level_family"]),
                            sweep_idx=sweep_idx,
                            sweep_bar=swept_low["sweep_bar"],  # type: ignore[arg-type]
                            sweep_extreme_price=float(swept_low["sweep_extreme_price"]),
                            reclaim_bar=bar,
                            reclaim_number=reclaim_number,
                        )
                    )
                    selected_low = None
                    swept_low = None
                elif reclaim_number == RECLAIM_WINDOW_H4_BARS:
                    selected_low = None
                    swept_low = None
            elif reclaim_number > RECLAIM_WINDOW_H4_BARS:
                selected_low = None
                swept_low = None
        else:
            low_levels = [level for level in levels if level.side == "LOW"]
            if low_levels:
                selected_low = low_levels[-1]
            if selected_low is not None and float(bar["Low"]) < selected_low.price:
                swept_low = {
                    "level": selected_low,
                    "level_family": _level_family(
                        direction="LONG",
                        level=selected_low,
                        sweep_idx=idx_int,
                        levels_by_idx=levels_by_idx,
                    ),
                    "sweep_idx": idx_int,
                    "sweep_bar": bar,
                    "sweep_extreme_price": float(bar["Low"]),
                }

    if not rows:
        return pd.DataFrame(columns=[*LOCAL_H4_OUTPUT_COLUMNS, "_level_confirmed_idx", "_sweep_h4_idx"])
    return pd.DataFrame(rows)


def _local_h4_sweep_extreme_stop_gates(
    row: dict[str, object],
    *,
    stop_buffer_usd: float = 50.0,
    max_risk_usd: float = MAX_RISK_USD,
) -> dict[str, object]:
    direction = str(row["direction"])
    entry_price = float(row["entry_price"])
    sweep_extreme = float(row["sweep_extreme_price"])
    reasons: list[str] = []

    if direction == "SHORT":
        stop_price = sweep_extreme + stop_buffer_usd
        risk_usd = stop_price - entry_price
    else:
        stop_price = sweep_extreme - stop_buffer_usd
        risk_usd = entry_price - stop_price

    if risk_usd <= 0:
        reasons.append("invalid_risk")
    elif risk_usd > max_risk_usd:
        reasons.append("sweep_extreme_risk_too_large")

    allowed = not reasons
    return {
        "stop_price": stop_price,
        "final_risk_usd": risk_usd,
        "risk_usd": risk_usd,
        "diagnostic_trade_allowed": allowed,
        "no_trade_reason": ";".join(reasons),
    }


def add_local_h4_sweep_extreme_stop_gates(
    candidates: pd.DataFrame,
    *,
    stop_buffer_usd: float = 50.0,
    max_risk_usd: float = MAX_RISK_USD,
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()

    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        gates = _local_h4_sweep_extreme_stop_gates(
            row,
            stop_buffer_usd=stop_buffer_usd,
            max_risk_usd=max_risk_usd,
        )
        rows.append({**row, **gates})
    return pd.DataFrame(rows)


def _public_local_h4_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=LOCAL_H4_OUTPUT_COLUMNS)
    out = candidates.copy()
    out["same_bar_ambiguity"] = out[
        ["same_bar_stop_1R", "same_bar_stop_1_5R", "same_bar_stop_2R"]
    ].fillna(False).any(axis=1)
    return out.loc[:, LOCAL_H4_OUTPUT_COLUMNS].copy()


def _diagnostic_trade_gates(
    row: dict[str, object],
    *,
    stop_buffer_usd: float = STOP_BUFFER_USD,
    long_color_gate: bool = True,
) -> dict[str, object]:
    direction = str(row["direction"])
    entry_price = float(row["entry_price"])
    sweep_extreme = float(row["sweep_extreme_price"])
    reclaim_open = float(row["reclaim_h4_open_price"])
    reclaim_close = float(row["reclaim_close_price"])

    reasons: list[str] = []
    if direction == "SHORT":
        stop_price = sweep_extreme + stop_buffer_usd
        risk_usd = stop_price - entry_price
        candle_color_pass = reclaim_close < reclaim_open
        if not candle_color_pass:
            reasons.append("bearish_reclaim_required")
    else:
        stop_price = sweep_extreme - stop_buffer_usd
        risk_usd = entry_price - stop_price
        candle_color_pass = (reclaim_close > reclaim_open) if long_color_gate else True
        if not candle_color_pass:
            reasons.append("bullish_reclaim_required")

    if risk_usd <= 0:
        risk_gate_pass = False
        reasons.insert(0, "invalid_risk")
    elif risk_usd > MAX_RISK_USD:
        risk_gate_pass = False
        reasons.insert(0, "risk_too_large")
    else:
        risk_gate_pass = True

    return {
        "stop_price": stop_price,
        "risk_usd": risk_usd,
        "risk_gate_pass": risk_gate_pass,
        "candle_color_gate_pass": candle_color_pass,
        "diagnostic_trade_allowed": bool(risk_gate_pass and candle_color_pass),
        "no_trade_reason": ";".join(reasons),
    }


def add_trade_gates(candidates: pd.DataFrame, *, stop_buffer_usd: float = STOP_BUFFER_USD) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()

    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        gates = _diagnostic_trade_gates(row, stop_buffer_usd=stop_buffer_usd)
        merged = {**row, **gates, "stop_buffer_usd": stop_buffer_usd}

        if abs(stop_buffer_usd - 50.0) < 1e-9:
            merged["stop_price_buffer_50"] = gates["stop_price"]
            merged["risk_usd_buffer_50"] = gates["risk_usd"]
            merged["diagnostic_trade_allowed_buffer_50"] = gates["diagnostic_trade_allowed"]
            merged["no_trade_reason_buffer_50"] = gates["no_trade_reason"]

            long_with_color = gates
            long_without_color = _diagnostic_trade_gates(
                row,
                stop_buffer_usd=stop_buffer_usd,
                long_color_gate=False,
            )
            if str(row["direction"]) == "LONG":
                merged["diagnostic_trade_allowed_buffer_50_long_with_color_gate"] = long_with_color[
                    "diagnostic_trade_allowed"
                ]
                merged["no_trade_reason_buffer_50_long_with_color_gate"] = long_with_color[
                    "no_trade_reason"
                ]
                merged["diagnostic_trade_allowed_buffer_50_long_without_color_gate"] = long_without_color[
                    "diagnostic_trade_allowed"
                ]
                merged["no_trade_reason_buffer_50_long_without_color_gate"] = long_without_color[
                    "no_trade_reason"
                ]
            else:
                merged["diagnostic_trade_allowed_buffer_50_long_with_color_gate"] = pd.NA
                merged["no_trade_reason_buffer_50_long_with_color_gate"] = pd.NA
                merged["diagnostic_trade_allowed_buffer_50_long_without_color_gate"] = pd.NA
                merged["no_trade_reason_buffer_50_long_without_color_gate"] = pd.NA
        else:
            merged["stop_price_buffer_50"] = pd.NA
            merged["risk_usd_buffer_50"] = pd.NA
            merged["diagnostic_trade_allowed_buffer_50"] = pd.NA
            merged["no_trade_reason_buffer_50"] = pd.NA
            merged["diagnostic_trade_allowed_buffer_50_long_with_color_gate"] = pd.NA
            merged["no_trade_reason_buffer_50_long_with_color_gate"] = pd.NA
            merged["diagnostic_trade_allowed_buffer_50_long_without_color_gate"] = pd.NA
            merged["no_trade_reason_buffer_50_long_without_color_gate"] = pd.NA

        rows.append(merged)
    return pd.DataFrame(rows)


def _compressed_buffer_trade_gates(
    row: dict[str, object],
    *,
    stop_buffer_usd: float = STOP_BUFFER_USD,
    max_risk_usd: float = MAX_RISK_USD,
) -> dict[str, object]:
    direction = str(row["direction"])
    entry_price = float(row["entry_price"])
    sweep_extreme = float(row["sweep_extreme_price"])
    reclaim_open = float(row["reclaim_h4_open_price"])
    reclaim_close = float(row["reclaim_close_price"])
    reasons: list[str] = []

    if direction == "SHORT":
        raw_sweep_risk = sweep_extreme - entry_price
        desired_stop = sweep_extreme + stop_buffer_usd
        desired_risk = desired_stop - entry_price
        max_stop = entry_price + max_risk_usd
        candle_color_pass = reclaim_close < reclaim_open
        if not candle_color_pass:
            reasons.append("bearish_reclaim_required")
        if raw_sweep_risk > max_risk_usd:
            final_stop = pd.NA
            final_risk = pd.NA
            applied_buffer = pd.NA
            buffer_was_compressed = False
            reasons.insert(0, "sweep_extreme_risk_too_large")
        else:
            final_stop = min(desired_stop, max_stop)
            final_risk = final_stop - entry_price
            applied_buffer = final_stop - sweep_extreme
            buffer_was_compressed = bool(applied_buffer < stop_buffer_usd)
    else:
        raw_sweep_risk = entry_price - sweep_extreme
        desired_stop = sweep_extreme - stop_buffer_usd
        desired_risk = entry_price - desired_stop
        max_stop = entry_price - max_risk_usd
        candle_color_pass = reclaim_close > reclaim_open
        if not candle_color_pass:
            reasons.append("bullish_reclaim_required")
        if raw_sweep_risk > max_risk_usd:
            final_stop = pd.NA
            final_risk = pd.NA
            applied_buffer = pd.NA
            buffer_was_compressed = False
            reasons.insert(0, "sweep_extreme_risk_too_large")
        else:
            final_stop = max(desired_stop, max_stop)
            final_risk = entry_price - final_stop
            applied_buffer = sweep_extreme - final_stop
            buffer_was_compressed = bool(applied_buffer < stop_buffer_usd)

    risk_valid = bool(pd.notna(final_risk) and 0 < float(final_risk) <= max_risk_usd)
    if pd.notna(applied_buffer) and float(applied_buffer) < 0:
        risk_valid = False
        reasons.insert(0, "invalid_risk")
    elif pd.notna(final_risk) and float(final_risk) <= 0:
        risk_valid = False
        reasons.insert(0, "invalid_risk")
    elif pd.notna(final_risk) and float(final_risk) > max_risk_usd:
        risk_valid = False
        reasons.insert(0, "risk_too_large")

    return {
        "raw_sweep_risk_usd": raw_sweep_risk,
        "desired_stop_price": desired_stop,
        "desired_risk_usd": desired_risk,
        "final_stop_price": final_stop,
        "final_risk_usd": final_risk,
        "applied_buffer_usd": applied_buffer,
        "buffer_was_compressed": buffer_was_compressed,
        "candle_color_gate_pass": candle_color_pass,
        "diagnostic_trade_allowed": bool(risk_valid and candle_color_pass),
        "no_trade_reason": ";".join(dict.fromkeys(reasons)),
        # Reuse the path-order implementation without changing detector state.
        "stop_price": final_stop,
        "risk_usd": final_risk,
    }


def add_compressed_buffer_gates(
    candidates: pd.DataFrame,
    *,
    stop_buffer_usd: float = STOP_BUFFER_USD,
    max_risk_usd: float = MAX_RISK_USD,
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()

    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        gates = _compressed_buffer_trade_gates(
            row,
            stop_buffer_usd=stop_buffer_usd,
            max_risk_usd=max_risk_usd,
        )
        rows.append({**row, **gates})
    return pd.DataFrame(rows)


def _future_moves(raw: pd.DataFrame, direction: str, entry_ts: pd.Timestamp, entry_price: float) -> tuple[dict[str, object], list[str]]:
    out: dict[str, object] = {}
    notes: list[str] = []
    raw_ts = pd.to_datetime(raw["Timestamp"], utc=True)

    for label, (minutes, favorable_col, adverse_col) in FUTURE_WINDOWS.items():
        end_ts = entry_ts + pd.Timedelta(minutes=minutes)
        window = raw.loc[(raw_ts >= entry_ts) & (raw_ts < end_ts)]
        if window.empty:
            out[favorable_col] = pd.NA
            out[adverse_col] = pd.NA
            notes.append(f"future_{label}_missing")
            continue

        high = float(window["High"].max())
        low = float(window["Low"].min())
        if direction == "LONG":
            favorable = high - entry_price
            adverse = entry_price - low
        else:
            favorable = entry_price - low
            adverse = high - entry_price

        out[favorable_col] = favorable
        out[adverse_col] = adverse
        if len(window.index) < minutes:
            notes.append(f"future_{label}_partial_rows={len(window.index)}/{minutes}")

    favorable_96h = out.get("favorable_move_96h_usd")
    out["hit_1000_favorable_96h"] = (
        bool(pd.notna(favorable_96h) and float(favorable_96h) >= 1000.0)
    )
    return out, notes


def _first_touch_ts(window: pd.DataFrame, mask: pd.Series) -> pd.Timestamp | pd.NaT:
    if mask.any():
        return pd.Timestamp(window.loc[mask, "Timestamp"].iloc[0])
    return pd.NaT


def _movement_extremes(
    window: pd.DataFrame,
    *,
    direction: str,
    entry_price: float,
) -> tuple[float | pd.NA, float | pd.NA]:
    if window.empty:
        return pd.NA, pd.NA
    if direction == "LONG":
        favorable = float(window["High"].max()) - entry_price
        adverse = entry_price - float(window["Low"].min())
    else:
        favorable = entry_price - float(window["Low"].min())
        adverse = float(window["High"].max()) - entry_price
    return favorable, adverse


def _window_before_ts(window: pd.DataFrame, ts: pd.Timestamp | pd.NaT) -> pd.DataFrame:
    if pd.isna(ts):
        return window
    return window.loc[pd.to_datetime(window["Timestamp"], utc=True) < pd.Timestamp(ts)]


def _path_order_diagnostics(raw: pd.DataFrame, row: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    direction = str(row["direction"])
    entry_ts = pd.Timestamp(row["entry_ts"])
    entry_price = float(row["entry_price"])
    stop_price_raw = row.get("stop_price")
    risk_usd_raw = row.get("risk_usd")
    raw_ts = pd.to_datetime(raw["Timestamp"], utc=True)
    end_ts = entry_ts + pd.Timedelta(minutes=PATH_WINDOW_MINUTES)
    window = raw.loc[(raw_ts >= entry_ts) & (raw_ts < end_ts)].copy()

    out: dict[str, object] = {
        "first_stop_touch_ts": pd.NaT,
        "first_1R_touch_ts": pd.NaT,
        "first_1_5R_touch_ts": pd.NaT,
        "first_2R_touch_ts": pd.NaT,
        "hit_1R_before_stop": False,
        "hit_1_5R_before_stop": False,
        "hit_2R_before_stop": False,
        "stop_before_1R": False,
        "stop_before_1_5R": False,
        "stop_before_2R": False,
        "same_bar_stop_1R": False,
        "same_bar_stop_1_5R": False,
        "same_bar_stop_2R": False,
        "max_favorable_before_stop": pd.NA,
        "max_adverse_before_1R": pd.NA,
        "max_adverse_before_1_5R": pd.NA,
        "max_adverse_before_2R": pd.NA,
    }
    notes: list[str] = []
    if window.empty:
        notes.append("path_96h_missing")
        return out, notes
    if len(window.index) < PATH_WINDOW_MINUTES:
        notes.append(f"path_96h_partial_rows={len(window.index)}/{PATH_WINDOW_MINUTES}")
    if pd.isna(stop_price_raw) or pd.isna(risk_usd_raw):
        notes.append("path_order_skipped_missing_final_risk")
        return out, notes
    stop_price = float(stop_price_raw)
    risk_usd = float(risk_usd_raw)
    if risk_usd <= 0:
        notes.append("path_order_skipped_invalid_risk")
        return out, notes

    if direction == "LONG":
        stop_mask = window["Low"] <= stop_price
        target_masks = {
            "1R": window["High"] >= entry_price + (1.0 * risk_usd),
            "1_5R": window["High"] >= entry_price + (1.5 * risk_usd),
            "2R": window["High"] >= entry_price + (2.0 * risk_usd),
        }
    else:
        stop_mask = window["High"] >= stop_price
        target_masks = {
            "1R": window["Low"] <= entry_price - (1.0 * risk_usd),
            "1_5R": window["Low"] <= entry_price - (1.5 * risk_usd),
            "2R": window["Low"] <= entry_price - (2.0 * risk_usd),
        }

    stop_ts = _first_touch_ts(window, stop_mask)
    out["first_stop_touch_ts"] = stop_ts
    before_stop = _window_before_ts(window, stop_ts)
    favorable_before_stop, _ = _movement_extremes(
        before_stop,
        direction=direction,
        entry_price=entry_price,
    )
    out["max_favorable_before_stop"] = favorable_before_stop

    for label, mask in target_masks.items():
        target_ts = _first_touch_ts(window, mask)
        out[f"first_{label}_touch_ts"] = target_ts
        same_bar = bool(pd.notna(stop_ts) and pd.notna(target_ts) and pd.Timestamp(stop_ts) == pd.Timestamp(target_ts))
        out[f"same_bar_stop_{label}"] = same_bar
        out[f"hit_{label}_before_stop"] = bool(
            pd.notna(target_ts) and (pd.isna(stop_ts) or pd.Timestamp(target_ts) < pd.Timestamp(stop_ts))
        )
        out[f"stop_before_{label}"] = bool(
            pd.notna(stop_ts) and (pd.isna(target_ts) or pd.Timestamp(stop_ts) < pd.Timestamp(target_ts))
        )
        before_target = _window_before_ts(window, target_ts)
        _, adverse_before_target = _movement_extremes(
            before_target,
            direction=direction,
            entry_price=entry_price,
        )
        out[f"max_adverse_before_{label}"] = adverse_before_target

    return out, notes


def add_forward_diagnostics(candidates: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        entry_price = float(row["entry_price"])
        moves, notes = _future_moves(raw, str(row["direction"]), entry_ts, entry_price)
        path_order, path_notes = _path_order_diagnostics(raw, row)
        merged = {**row, **moves, **path_order}
        all_notes = [*notes, *path_notes]
        if all_notes:
            merged["notes"] = f"{merged['notes']};" + ";".join(all_notes)
        rows.append(merged)

    columns = list(candidates.columns)
    for column in OUTPUT_COLUMNS:
        if column not in columns:
            columns.append(column)
    return pd.DataFrame(rows, columns=columns)


def filter_output_range(candidates: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    start_ts = pd.Timestamp(start.isoformat(), tz="UTC")
    end_exclusive = pd.Timestamp((end + timedelta(days=1)).isoformat(), tz="UTC")
    entry_ts = pd.to_datetime(candidates["entry_ts"], utc=True)
    return candidates.loc[(entry_ts >= start_ts) & (entry_ts < end_exclusive)].reset_index(drop=True)


def _all_confirmed_lows(h4: pd.DataFrame) -> list[ConfirmedLevel]:
    levels_by_idx = confirmed_levels(h4)
    lows: list[ConfirmedLevel] = []
    for levels in levels_by_idx.values():
        lows.extend(level for level in levels if level.side == "LOW")
    return sorted(lows, key=lambda item: (item.confirmed_idx, item.confirmed_ts))


def build_long_active_low_audit(candidates: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    lows = _all_confirmed_lows(h4)
    rows: list[dict[str, object]] = []
    if candidates.empty:
        return pd.DataFrame(columns=LONG_AUDIT_COLUMNS)

    long_candidates = candidates.loc[candidates["direction"] == "LONG"].copy()
    for row in long_candidates.to_dict("records"):
        sweep_idx = int(row["_sweep_h4_idx"])
        active_low_price = float(row["active_level_price"])
        sweep_extreme_low = float(row["sweep_extreme_price"])
        active_low_confirmed_idx = int(row["_active_level_confirmed_idx"])
        nearest_candidates = [level for level in lows if level.confirmed_idx <= sweep_idx]
        nearest = nearest_candidates[-1] if nearest_candidates else None

        broke_active_low = bool(sweep_extreme_low < active_low_price)
        if nearest is None:
            nearest_price = pd.NA
            nearest_ts = pd.NaT
            nearest_age = pd.NA
            broke_nearest = False
            suspected_issue = ""
            note = "nearest_recent_pivot_low_missing;do_not_label_false_break_reclaim_without_additional_study"
        else:
            nearest_price = nearest.price
            nearest_ts = nearest.confirmed_ts
            nearest_age = int(sweep_idx - nearest.confirmed_idx)
            broke_nearest = bool(sweep_extreme_low < nearest.price)
            suspected_issue = (
                "possible_active_low_selection_issue"
                if broke_active_low and not broke_nearest
                else ""
            )
            note = (
                "active_low_broken_but_nearest_recent_pivot_low_not_broken"
                if suspected_issue
                else "nearest_recent_pivot_low_check_passed"
            )

        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "active_low_price": active_low_price,
                "active_low_confirmed_ts": row["active_level_confirmed_ts"],
                "active_low_age_h4_bars": int(sweep_idx - active_low_confirmed_idx),
                "sweep_h4_open_ts": row["sweep_h4_open_ts"],
                "sweep_extreme_low": sweep_extreme_low,
                "h4_low_broke_active_low": broke_active_low,
                "nearest_recent_pivot_low_price": nearest_price,
                "nearest_recent_pivot_low_ts": nearest_ts,
                "nearest_recent_pivot_low_age_h4_bars": nearest_age,
                "h4_low_broke_nearest_recent_pivot_low": broke_nearest,
                "suspected_issue": suspected_issue,
                "note": note,
            }
        )

    return pd.DataFrame(rows, columns=LONG_AUDIT_COLUMNS)


def _nearest_internal_higher_low(
    *,
    lows: list[ConfirmedLevel],
    main_active_low_price: float,
    main_active_low_confirmed_idx: int,
    sweep_idx: int,
) -> ConfirmedLevel | None:
    candidates = [
        low
        for low in lows
        if main_active_low_confirmed_idx < low.confirmed_idx <= sweep_idx
        and float(low.price) > main_active_low_price
    ]
    if not candidates:
        return None
    return candidates[-1]


def build_long_low_selection_audit(
    candidates: pd.DataFrame,
    h4: pd.DataFrame,
    *,
    row_numbers: tuple[int, ...] = (5, 10, 11),
) -> pd.DataFrame:
    lows = _all_confirmed_lows(h4)
    rows: list[dict[str, object]] = []
    if candidates.empty:
        return pd.DataFrame(columns=LONG_LOW_SELECTION_AUDIT_COLUMNS)

    audited = candidates.loc[
        (candidates["direction"] == "LONG") & (candidates["row_number"].isin(row_numbers))
    ].copy()

    for row in audited.to_dict("records"):
        main_active_low_price = float(row["active_level_price"])
        main_active_low_confirmed_idx = int(row["_active_level_confirmed_idx"])
        sweep_idx = int(row["_sweep_h4_idx"])
        sweep_extreme_low = float(row["sweep_extreme_price"])
        internal_low = _nearest_internal_higher_low(
            lows=lows,
            main_active_low_price=main_active_low_price,
            main_active_low_confirmed_idx=main_active_low_confirmed_idx,
            sweep_idx=sweep_idx,
        )

        swept_main = bool(sweep_extreme_low < main_active_low_price)
        if internal_low is None:
            internal_price = pd.NA
            internal_ts = pd.NaT
            internal_age = pd.NA
            swept_internal = False
        else:
            internal_price = internal_low.price
            internal_ts = internal_low.confirmed_ts
            internal_age = int(sweep_idx - internal_low.confirmed_idx)
            swept_internal = bool(sweep_extreme_low < internal_low.price)

        expected_mode = "MAIN_ACTIVE_LOW_SWEEP"
        if swept_main:
            mode_used = "MAIN_ACTIVE_LOW_SWEEP"
            contract_violation = False
            suspected_issue = ""
            possible_pattern = ""
            note = (
                "script_active_low_was_swept"
                if not swept_internal
                else "script_active_low_was_swept;nearest_internal_higher_low_also_swept"
            )
        elif swept_internal:
            mode_used = "INTERNAL_HIGHER_LOW_SWEEP"
            contract_violation = True
            suspected_issue = "higher_low_replaced_unswept_active_low"
            possible_pattern = "INTERNAL_HIGHER_LOW_SWEEP_RECLAIM"
            note = "internal_higher_low_swept_but_main_active_low_not_swept"
        else:
            mode_used = "NO_VALID_LOW_SWEEP"
            contract_violation = True
            suspected_issue = "no_main_or_internal_low_sweep"
            possible_pattern = ""
            note = "neither_main_active_low_nor_internal_higher_low_was_swept"

        rows.append(
            {
                "row_number": row["row_number"],
                "candidate_id": row["candidate_id"],
                "entry_ts": row["entry_ts"],
                "direction": row["direction"],
                "main_active_low_price": main_active_low_price,
                "main_active_low_confirmed_ts": row["active_level_confirmed_ts"],
                "main_active_low_age_h4_bars_at_sweep": int(sweep_idx - main_active_low_confirmed_idx),
                "nearest_internal_higher_low_price": internal_price,
                "nearest_internal_higher_low_ts": internal_ts,
                "nearest_internal_higher_low_age_h4_bars": internal_age,
                "swept_main_active_low": swept_main,
                "swept_internal_higher_low": swept_internal,
                "sweep_extreme_low": sweep_extreme_low,
                "reclaim_h4_close_ts": row["reclaim_h4_close_ts"],
                "reclaim_close_price": row["reclaim_close_price"],
                "low_selection_mode_used_by_script": mode_used,
                "expected_mode_by_contract": expected_mode,
                "contract_violation": contract_violation,
                "suspected_issue": suspected_issue,
                "possible_separate_pattern": possible_pattern,
                "note": note,
            }
        )

    return pd.DataFrame(rows, columns=LONG_LOW_SELECTION_AUDIT_COLUMNS)


def _count_reason(df: pd.DataFrame, reason: str) -> int:
    if df.empty or "no_trade_reason" not in df.columns:
        return 0
    return int(df["no_trade_reason"].fillna("").astype(str).str.contains(reason, regex=False).sum())


def write_markdown_summary(
    *,
    candidates: pd.DataFrame,
    long_audit: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
    long_audit_csv: Path,
) -> Path:
    total = int(len(candidates.index))
    direction_counts = candidates["direction"].value_counts().to_dict() if not candidates.empty else {}
    allowed = int(candidates.get("diagnostic_trade_allowed", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
    allowed_df = candidates.loc[candidates["diagnostic_trade_allowed"] == True] if not candidates.empty else candidates

    def count_bool(df: pd.DataFrame, column: str) -> int:
        if df.empty or column not in df.columns:
            return 0
        return int(df[column].fillna(False).astype(bool).sum())

    long_total = int(len(long_audit.index))
    long_broke_active = count_bool(long_audit, "h4_low_broke_active_low")
    long_not_broke_nearest = (
        int((~long_audit["h4_low_broke_nearest_recent_pivot_low"].fillna(False).astype(bool)).sum())
        if not long_audit.empty
        else 0
    )
    issue_count = (
        int((long_audit["suspected_issue"] == "possible_active_low_selection_issue").sum())
        if not long_audit.empty
        else 0
    )

    body = "\n".join(
        [
            "# H4 Active-Level Reclaim-Close Test V1 Filtered Diagnostic",
            "",
            "Status: diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.",
            "",
            "This diagnostic does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the legacy failed-break detector, and does not run the Backtester.",
            "",
            "## Outputs",
            "",
            f"- Diagnostic CSV: `{diagnostic_csv}`",
            f"- LONG active-low audit CSV: `{long_audit_csv}`",
            "",
            "## Candidate Counts",
            "",
            f"- Total candidates: {total}",
            f"- SHORT candidates: {int(direction_counts.get('SHORT', 0))}",
            f"- LONG candidates: {int(direction_counts.get('LONG', 0))}",
            f"- `diagnostic_trade_allowed`: {allowed}",
            f"- Rejected with `risk_too_large`: {_count_reason(candidates, 'risk_too_large')}",
            f"- Rejected with `bearish_reclaim_required`: {_count_reason(candidates, 'bearish_reclaim_required')}",
            f"- Rejected with `bullish_reclaim_required`: {_count_reason(candidates, 'bullish_reclaim_required')}",
            "",
            "## Path-Order Diagnostic",
            "",
            "Counts below are on rows where `diagnostic_trade_allowed = true`.",
            "",
            f"- `hit_1R_before_stop`: {count_bool(allowed_df, 'hit_1R_before_stop')}",
            f"- `hit_1_5R_before_stop`: {count_bool(allowed_df, 'hit_1_5R_before_stop')}",
            f"- `hit_2R_before_stop`: {count_bool(allowed_df, 'hit_2R_before_stop')}",
            "",
            "Same-bar stop/target touches are flagged in the CSV and are not counted as clean target-before-stop.",
            "",
            "## LONG Active-Low Audit Summary",
            "",
            f"- LONG candidates: {long_total}",
            f"- Broke active low: {long_broke_active}",
            f"- Did not break nearest recent pivot low: {long_not_broke_nearest}",
            f"- `possible_active_low_selection_issue`: {issue_count}",
            "",
            "If a LONG direction works but did not sweep the nearest recent pivot low, do not label it false-break/reclaim without additional research.",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")
    return output_path


def _format_markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    if df.empty:
        return ["No rows."]
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in df.iterrows():
        values = []
        for column in columns:
            value = row.get(column, "")
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.6g}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return rows


def write_buffer50_markdown_summary(
    *,
    candidates: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
) -> Path:
    total = int(len(candidates.index))
    allowed = int(candidates["diagnostic_trade_allowed_buffer_50"].fillna(False).astype(bool).sum())
    short = candidates.loc[candidates["direction"] == "SHORT"].copy()
    long = candidates.loc[candidates["direction"] == "LONG"].copy()
    short_allowed = short.loc[short["diagnostic_trade_allowed_buffer_50"] == True]
    long_with_color_allowed = long.loc[
        long["diagnostic_trade_allowed_buffer_50_long_with_color_gate"] == True
    ]
    long_without_color_allowed = long.loc[
        long["diagnostic_trade_allowed_buffer_50_long_without_color_gate"] == True
    ]

    def count_bool(df: pd.DataFrame, column: str) -> int:
        if df.empty:
            return 0
        return int(df[column].fillna(False).astype(bool).sum())

    def count_reason(reason: str) -> int:
        return int(candidates["no_trade_reason_buffer_50"].fillna("").astype(str).str.contains(reason, regex=False).sum())

    focus_rows = candidates.loc[candidates["row_number"].isin([7, 8, 13, 5, 10, 11])].copy()
    focus_rows = focus_rows.sort_values("row_number", kind="mergesort")
    focus_columns = [
        "row_number",
        "direction",
        "entry_ts",
        "entry_price",
        "sweep_extreme_price",
        "stop_price_buffer_50",
        "risk_usd_buffer_50",
        "diagnostic_trade_allowed_buffer_50",
        "no_trade_reason_buffer_50",
        "first_stop_touch_ts",
        "first_1R_touch_ts",
        "first_1_5R_touch_ts",
        "first_2R_touch_ts",
        "hit_1R_before_stop",
        "hit_1_5R_before_stop",
        "hit_2R_before_stop",
    ]

    lines = [
        "# H4 Active-Level Reclaim-Close Test V1 Buffer50 Diagnostic",
        "",
        "Status: diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.",
        "",
        "This is a separate diagnostic variant over the same detector candidates. It does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the legacy failed-break detector, and does not run the Backtester.",
        "",
        f"- Diagnostic CSV: `{diagnostic_csv}`",
        "- `stop_buffer_usd`: 50",
        "- `max_risk_usd`: 1500",
        "",
        "## Candidate Counts",
        "",
        f"- Total candidates: {total}",
        f"- Allowed with buffer 50: {allowed}",
        f"- Rejected with `risk_too_large`: {count_reason('risk_too_large')}",
        f"- Rejected with `bearish_reclaim_required`: {count_reason('bearish_reclaim_required')}",
        "",
        "## SHORT Results",
        "",
        "Counts below are SHORT rows where `diagnostic_trade_allowed_buffer_50 = true`.",
        "",
        f"- `hit_1R_before_stop`: {count_bool(short_allowed, 'hit_1R_before_stop')}",
        f"- `hit_1_5R_before_stop`: {count_bool(short_allowed, 'hit_1_5R_before_stop')}",
        f"- `hit_2R_before_stop`: {count_bool(short_allowed, 'hit_2R_before_stop')}",
        "",
        "## LONG Results With Color Gate",
        "",
        f"- Allowed LONG rows: {int(len(long_with_color_allowed.index))}",
        f"- `hit_1R_before_stop`: {count_bool(long_with_color_allowed, 'hit_1R_before_stop')}",
        f"- `hit_1_5R_before_stop`: {count_bool(long_with_color_allowed, 'hit_1_5R_before_stop')}",
        f"- `hit_2R_before_stop`: {count_bool(long_with_color_allowed, 'hit_2R_before_stop')}",
        "",
        "## LONG Results Without Color Gate",
        "",
        f"- Allowed LONG rows: {int(len(long_without_color_allowed.index))}",
        f"- `hit_1R_before_stop`: {count_bool(long_without_color_allowed, 'hit_1R_before_stop')}",
        f"- `hit_1_5R_before_stop`: {count_bool(long_without_color_allowed, 'hit_1_5R_before_stop')}",
        f"- `hit_2R_before_stop`: {count_bool(long_without_color_allowed, 'hit_2R_before_stop')}",
        "",
        "## Manual Review Rows",
        "",
        *_format_markdown_table(focus_rows, focus_columns),
        "",
        "Same-bar stop/target touches are flagged in the CSV and are not counted as clean target-before-stop.",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_long_low_selection_markdown(
    *,
    audit: pd.DataFrame,
    output_path: Path,
    audit_csv: Path,
) -> Path:
    violations = int(audit["contract_violation"].fillna(False).astype(bool).sum()) if not audit.empty else 0
    mode_counts = audit["low_selection_mode_used_by_script"].value_counts().to_dict() if not audit.empty else {}
    internal_pattern_count = (
        int((audit["possible_separate_pattern"] == "INTERNAL_HIGHER_LOW_SWEEP_RECLAIM").sum())
        if not audit.empty
        else 0
    )

    table_columns = [
        "row_number",
        "candidate_id",
        "entry_ts",
        "main_active_low_price",
        "nearest_internal_higher_low_price",
        "swept_main_active_low",
        "swept_internal_higher_low",
        "low_selection_mode_used_by_script",
        "contract_violation",
        "suspected_issue",
        "note",
    ]

    lines = [
        "# H4 Active-Level Reclaim-Close Test V1 LONG Low-Selection Audit",
        "",
        "Status: diagnostic audit only. Not FIELD, not live strategy, not execution-ready evidence.",
        "",
        "This audit does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the legacy failed-break detector, and does not run the Backtester.",
        "",
        f"- Audit CSV: `{audit_csv}`",
        "",
        "## Direct Answers",
        "",
        "- LONG logic currently uses one retained `active_low` slot. A newly confirmed higher low does not replace it while the old `active_low` is still active.",
        "- Higher low can replace the active low only after the old low has been swept/cleared or expired; previously ignored higher lows are not retroactively promoted.",
        f"- Rows 5/10/11 classified as `MAIN_ACTIVE_LOW_SWEEP`: {int(mode_counts.get('MAIN_ACTIVE_LOW_SWEEP', 0))}.",
        f"- Rows 5/10/11 classified as `INTERNAL_HIGHER_LOW_SWEEP`: {int(mode_counts.get('INTERNAL_HIGHER_LOW_SWEEP', 0))}.",
        f"- Active-low lifecycle contract violations found: {violations}.",
        f"- Possible separate internal-higher-low pattern rows: {internal_pattern_count}.",
        "",
        "## Audited Rows",
        "",
        *_format_markdown_table(audit, table_columns),
        "",
        "## Code Path",
        "",
        "- Pivot lows are strict 3-H4-candle lows in `confirmed_levels()`.",
        "- `active_low` is retained by `_maybe_activate()` whenever it is already non-null.",
        "- Expiry clears active lows only when active age exceeds 30 H4 bars.",
        "- LONG sweep requires `bar.Low < active_low.price` in `scan_candidates()`.",
        "- LONG candidate emit requires a reclaim close above that same active low within three H4 bars after the sweep candle.",
        "",
        "## Interpretation Boundary",
        "",
        "If a future row sweeps only an internal higher low while the main active low remains unswept, classify it as `INTERNAL_HIGHER_LOW_SWEEP_RECLAIM` for separate research rather than as the current H4 active-level reclaim contract.",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _public_compressed_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=COMPRESSED_OUTPUT_COLUMNS)
    return candidates.loc[:, COMPRESSED_OUTPUT_COLUMNS].copy()


def write_compressed_buffer_markdown(
    *,
    candidates: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
) -> Path:
    total = int(len(candidates.index))
    direction_counts = candidates["direction"].value_counts().to_dict() if not candidates.empty else {}
    allowed_df = candidates.loc[candidates["diagnostic_trade_allowed"] == True] if not candidates.empty else candidates

    def count_bool(df: pd.DataFrame, column: str) -> int:
        if df.empty:
            return 0
        return int(df[column].fillna(False).astype(bool).sum())

    def count_reason(reason: str) -> int:
        if candidates.empty:
            return 0
        return int(candidates["no_trade_reason"].fillna("").astype(str).str.contains(reason, regex=False).sum())

    focus = candidates.loc[candidates["row_number"].isin([7, 8, 13, 5, 10, 11])].copy()
    focus = focus.sort_values("row_number", kind="mergesort")
    focus_columns = [
        "row_number",
        "direction",
        "entry_ts",
        "entry_price",
        "sweep_extreme_price",
        "raw_sweep_risk_usd",
        "desired_risk_usd",
        "final_risk_usd",
        "applied_buffer_usd",
        "buffer_was_compressed",
        "diagnostic_trade_allowed",
        "no_trade_reason",
        "hit_1R_before_stop",
        "hit_1_5R_before_stop",
        "hit_2R_before_stop",
        "first_stop_touch_ts",
    ]

    lines = [
        "# H4 Active-Level Reclaim-Close Test V1 Compressed Buffer350 Diagnostic",
        "",
        "Status: diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.",
        "",
        "This is a separate diagnostic variant over the same detector candidates. It does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the legacy failed-break detector, and does not run the Backtester.",
        "",
        f"- Diagnostic CSV: `{diagnostic_csv}`",
        "- `stop_buffer_usd`: 350",
        "- `max_risk_usd`: 1500",
        "- `allow_buffer_compression`: true",
        "",
        "## Candidate Counts",
        "",
        f"- Total candidates: {total}",
        f"- SHORT candidates: {int(direction_counts.get('SHORT', 0))}",
        f"- LONG candidates: {int(direction_counts.get('LONG', 0))}",
        f"- `diagnostic_trade_allowed`: {count_bool(candidates, 'diagnostic_trade_allowed')}",
        f"- Rejected with `sweep_extreme_risk_too_large`: {count_reason('sweep_extreme_risk_too_large')}",
        f"- Rejected with `bearish_reclaim_required`: {count_reason('bearish_reclaim_required')}",
        f"- Rejected with `bullish_reclaim_required`: {count_reason('bullish_reclaim_required')}",
        f"- `buffer_was_compressed`: {count_bool(candidates, 'buffer_was_compressed')}",
        "",
        "## Allowed Rows Path-Order",
        "",
        f"- `hit_1R_before_stop`: {count_bool(allowed_df, 'hit_1R_before_stop')}",
        f"- `hit_1_5R_before_stop`: {count_bool(allowed_df, 'hit_1_5R_before_stop')}",
        f"- `hit_2R_before_stop`: {count_bool(allowed_df, 'hit_2R_before_stop')}",
        "",
        "## Special Rows",
        "",
        *_format_markdown_table(focus, focus_columns),
        "",
        "Same-bar stop/target touches are flagged in the CSV and are not counted as clean target-before-stop.",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _load_baseline_candidates(path: Path = Path(DEFAULT_OUTPUT)) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _match_new_by_entry(new_candidates: pd.DataFrame, old_row: dict[str, object]) -> pd.DataFrame:
    if new_candidates.empty:
        return new_candidates
    entry_ts = str(old_row["entry_ts"])
    direction = str(old_row["direction"])
    return new_candidates.loc[
        (new_candidates["direction"].astype(str) == direction)
        & (new_candidates["entry_ts"].astype(str) == entry_ts)
    ].copy()


def _level_registry_focus_rows(
    *,
    baseline: pd.DataFrame,
    candidates: pd.DataFrame,
    row_numbers: list[int],
) -> pd.DataFrame:
    columns = [
        "old_row_number",
        "direction",
        "old_entry_ts",
        "old_active_level_price",
        "new_status",
        "new_row_number",
        "new_active_level_price",
        "new_active_level_source",
        "new_promoted_from_pending",
    ]
    rows: list[dict[str, object]] = []
    if baseline.empty:
        return pd.DataFrame(columns=columns)

    for old in baseline.loc[baseline["row_number"].isin(row_numbers)].to_dict("records"):
        matches = _match_new_by_entry(candidates, old)
        if matches.empty:
            rows.append(
                {
                    "old_row_number": old["row_number"],
                    "direction": old["direction"],
                    "old_entry_ts": old["entry_ts"],
                    "old_active_level_price": old["active_level_price"],
                    "new_status": "missing_after_registry_patch",
                    "new_row_number": pd.NA,
                    "new_active_level_price": pd.NA,
                    "new_active_level_source": pd.NA,
                    "new_promoted_from_pending": pd.NA,
                }
            )
            continue

        for _, new in matches.iterrows():
            changed = float(new["active_level_price"]) != float(old["active_level_price"])
            rows.append(
                {
                    "old_row_number": old["row_number"],
                    "direction": old["direction"],
                    "old_entry_ts": old["entry_ts"],
                    "old_active_level_price": old["active_level_price"],
                    "new_status": "active_level_changed" if changed else "still_present",
                    "new_row_number": new.get("row_number", pd.NA),
                    "new_active_level_price": new["active_level_price"],
                    "new_active_level_source": new.get("active_level_source", pd.NA),
                    "new_promoted_from_pending": new.get("promoted_from_pending", pd.NA),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def write_level_registry_markdown(
    *,
    candidates: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
    baseline_csv: Path = Path(DEFAULT_OUTPUT),
) -> Path:
    baseline = _load_baseline_candidates(baseline_csv)
    before_count = int(len(baseline.index)) if not baseline.empty else 0
    after_count = int(len(candidates.index))
    promoted = candidates.loc[candidates["promoted_from_pending"].fillna(False).astype(bool)].copy()
    long_focus = _level_registry_focus_rows(
        baseline=baseline,
        candidates=candidates,
        row_numbers=[5, 10, 11],
    )
    short_focus = _level_registry_focus_rows(
        baseline=baseline,
        candidates=candidates,
        row_numbers=[7, 8, 13],
    )

    row5_no_local_low = "needs_baseline"
    if not baseline.empty:
        old_row5 = baseline.loc[baseline["row_number"] == 5]
        if old_row5.empty:
            row5_no_local_low = "old_row_5_missing_in_baseline"
        else:
            matches = _match_new_by_entry(candidates, old_row5.iloc[0].to_dict())
            local_low_matches = matches.loc[
                matches["active_level_price"].astype(float).sub(70671.6).abs() < 1e-6
            ]
            row5_no_local_low = "true" if local_low_matches.empty else "false"

    promoted_columns = [
        "row_number",
        "direction",
        "entry_ts",
        "active_level_price",
        "active_level_confirmed_ts",
        "pending_queue_size_at_activation",
        "previous_expired_level_price",
        "previous_expired_level_confirmed_ts",
    ]
    focus_columns = [
        "old_row_number",
        "direction",
        "old_entry_ts",
        "old_active_level_price",
        "new_status",
        "new_row_number",
        "new_active_level_price",
        "new_active_level_source",
        "new_promoted_from_pending",
    ]
    lines = [
        "# H4 Active-Level Reclaim-Close Test V1 Level Registry Diagnostic",
        "",
        "Date: 2026-05-04",
        "",
        "Scope: standalone diagnostic script only. This run does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the Backtester, and does not make FIELD or execution-ready claims.",
        "",
        "## Summary",
        "",
        f"- Baseline candidates before registry patch: {before_count}",
        f"- Candidates after registry patch: {after_count}",
        f"- `promoted_from_pending`: {int(len(promoted.index))}",
        f"- Row 5 no longer opens on local low `70671.6`: {row5_no_local_low}",
        f"- Diagnostic CSV: `{diagnostic_csv.as_posix()}`",
        f"- Baseline CSV used for comparison: `{baseline_csv.as_posix()}`",
        "",
        "## LONG Rows 5/10/11",
        "",
        *_format_markdown_table(long_focus, focus_columns),
        "",
        "## Promoted Pending Levels",
        "",
        *_format_markdown_table(promoted, promoted_columns),
        "",
        "## SHORT Rows 7/8/13",
        "",
        *_format_markdown_table(short_focus, focus_columns),
        "",
        "## Notes",
        "",
        "- `active_level_source=direct_new_pivot` means the active slot was empty and the current confirmed pivot became active directly.",
        "- `active_level_source=promoted_from_pending` means a previously confirmed pending level was retained and later activated.",
        "- Blank `previous_expired_level_*` on a promoted row means the promotion happened after a non-expiry active-slot clear.",
        "- Pending levels are dropped before promotion if they are swept while pending or if their own age exceeds 30 H4 bars.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _public_diagnostic_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return candidates.loc[:, OUTPUT_COLUMNS].copy()


def run_diagnostic(
    feed_dir: Path,
    output_path: Path,
    start: date,
    end: date,
    *,
    stop_buffer_usd: float = STOP_BUFFER_USD,
    long_audit_output_path: Path | None = None,
    long_low_selection_audit_output_path: Path | None = None,
    long_low_selection_finding_output_path: Path | None = None,
    finding_output_path: Path | None = None,
) -> pd.DataFrame:
    raw = load_feed(feed_dir, start - timedelta(days=10), end + timedelta(days=4))
    h4 = build_h4_bars(raw)
    candidates = scan_candidates(h4)
    candidates = filter_output_range(candidates, start, end)
    candidates = add_trade_gates(candidates, stop_buffer_usd=stop_buffer_usd)
    candidates = add_forward_diagnostics(candidates, raw)
    candidates = candidates.sort_values(
        ["entry_ts", "direction", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)
    if not candidates.empty:
        candidates["row_number"] = range(1, len(candidates.index) + 1)

    long_audit = build_long_active_low_audit(candidates, h4)
    long_low_selection_audit = build_long_low_selection_audit(candidates, h4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    public_candidates = _public_diagnostic_frame(candidates)
    public_candidates.to_csv(output_path, index=False, encoding="utf-8")

    if long_audit_output_path is not None:
        long_audit_output_path.parent.mkdir(parents=True, exist_ok=True)
        long_audit.to_csv(long_audit_output_path, index=False, encoding="utf-8")

    if long_low_selection_audit_output_path is not None:
        long_low_selection_audit_output_path.parent.mkdir(parents=True, exist_ok=True)
        long_low_selection_audit.to_csv(
            long_low_selection_audit_output_path,
            index=False,
            encoding="utf-8",
        )

    if long_low_selection_finding_output_path is not None:
        write_long_low_selection_markdown(
            audit=long_low_selection_audit,
            output_path=long_low_selection_finding_output_path,
            audit_csv=long_low_selection_audit_output_path or Path(""),
        )

    if finding_output_path is not None:
        if abs(stop_buffer_usd - 50.0) < 1e-9:
            write_buffer50_markdown_summary(
                candidates=public_candidates,
                output_path=finding_output_path,
                diagnostic_csv=output_path,
            )
        else:
            write_markdown_summary(
                candidates=public_candidates,
                long_audit=long_audit,
                output_path=finding_output_path,
                diagnostic_csv=output_path,
                long_audit_csv=long_audit_output_path or Path(""),
            )

    return public_candidates


def run_level_registry_diagnostic(
    feed_dir: Path,
    output_path: Path,
    start: date,
    end: date,
    *,
    finding_output_path: Path | None = None,
    stop_buffer_usd: float = STOP_BUFFER_USD,
) -> pd.DataFrame:
    raw = load_feed(feed_dir, start - timedelta(days=10), end + timedelta(days=4))
    h4 = build_h4_bars(raw)
    candidates = scan_candidates(h4)
    candidates = filter_output_range(candidates, start, end)
    candidates = add_trade_gates(candidates, stop_buffer_usd=stop_buffer_usd)
    candidates = add_forward_diagnostics(candidates, raw)
    candidates = candidates.sort_values(
        ["entry_ts", "direction", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)
    if not candidates.empty:
        candidates["row_number"] = range(1, len(candidates.index) + 1)

    public = _public_diagnostic_frame(candidates)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    public.to_csv(output_path, index=False, encoding="utf-8")

    if finding_output_path is not None:
        write_level_registry_markdown(
            candidates=public,
            output_path=finding_output_path,
            diagnostic_csv=output_path,
        )

    return public


def run_compressed_buffer_diagnostic(
    feed_dir: Path,
    output_path: Path,
    start: date,
    end: date,
    *,
    finding_output_path: Path | None = None,
    stop_buffer_usd: float = STOP_BUFFER_USD,
    max_risk_usd: float = MAX_RISK_USD,
) -> pd.DataFrame:
    raw = load_feed(feed_dir, start - timedelta(days=10), end + timedelta(days=4))
    h4 = build_h4_bars(raw)
    candidates = scan_candidates(h4)
    candidates = filter_output_range(candidates, start, end)
    candidates = add_compressed_buffer_gates(
        candidates,
        stop_buffer_usd=stop_buffer_usd,
        max_risk_usd=max_risk_usd,
    )
    candidates = add_forward_diagnostics(candidates, raw)
    candidates = candidates.sort_values(
        ["entry_ts", "direction", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)
    if not candidates.empty:
        candidates["row_number"] = range(1, len(candidates.index) + 1)

    public = _public_compressed_frame(candidates)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    public.to_csv(output_path, index=False, encoding="utf-8")

    if finding_output_path is not None:
        write_compressed_buffer_markdown(
            candidates=public,
            output_path=finding_output_path,
            diagnostic_csv=output_path,
        )

    return public


def _add_level_family_to_active_candidates(
    candidates: pd.DataFrame,
    *,
    levels_by_idx: dict[int, list[ConfirmedLevel]],
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        side = "HIGH" if str(row["direction"]) == "SHORT" else "LOW"
        level = ConfirmedLevel(
            side=side,
            price=float(row["active_level_price"]),
            confirmed_ts=pd.Timestamp(row["active_level_confirmed_ts"]),
            confirmed_idx=int(row["_active_level_confirmed_idx"]),
        )
        rows.append(
            {
                **row,
                "level_family": _level_family(
                    direction=str(row["direction"]),
                    level=level,
                    sweep_idx=int(row["_sweep_h4_idx"]),
                    levels_by_idx=levels_by_idx,
                ),
            }
        )
    return pd.DataFrame(rows)


def _family_summary(candidates: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "level_family",
        "candidate_count",
        "direction_count",
        "diagnostic_trade_allowed_count",
        "no_trade_reason_counts",
        "buffer_was_compressed_count",
        "hit_1R_before_stop_count",
        "hit_1_5R_before_stop_count",
        "hit_2R_before_stop_count",
        "same_bar_ambiguity_count",
        "first_stop_touch_count",
    ]
    if candidates.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, object]] = []
    family_order = [
        "MAIN_STRUCTURAL_HIGH_SWEEP",
        "MAIN_STRUCTURAL_LOW_SWEEP",
        "LOCAL_LOWER_HIGH_SWEEP",
        "LOCAL_HIGHER_LOW_SWEEP",
    ]
    for family in family_order:
        group = candidates.loc[candidates["level_family"] == family]
        if group.empty:
            continue
        direction_counts = group["direction"].value_counts().to_dict()
        reason_counts = group["no_trade_reason"].fillna("").replace("", "<allowed>").value_counts().to_dict()
        if "same_bar_ambiguity" in group.columns:
            same_bar = int(group["same_bar_ambiguity"].fillna(False).astype(bool).sum())
        else:
            same_bar = int(
                group[
                    ["same_bar_stop_1R", "same_bar_stop_1_5R", "same_bar_stop_2R"]
                ].fillna(False).any(axis=1).sum()
            )
        first_stop = (
            int(group["first_stop_touch_ts"].notna().sum())
            if "first_stop_touch_ts" in group.columns
            else 0
        )
        rows.append(
            {
                "level_family": family,
                "candidate_count": int(len(group.index)),
                "direction_count": ", ".join(
                    f"{key}={int(value)}" for key, value in sorted(direction_counts.items())
                ),
                "diagnostic_trade_allowed_count": int(
                    group["diagnostic_trade_allowed"].fillna(False).astype(bool).sum()
                ),
                "no_trade_reason_counts": "; ".join(
                    f"{key}={int(value)}" for key, value in reason_counts.items()
                ),
                "buffer_was_compressed_count": int(
                    group.get("buffer_was_compressed", pd.Series(False, index=group.index))
                    .fillna(False)
                    .astype(bool)
                    .sum()
                ),
                "hit_1R_before_stop_count": int(group["hit_1R_before_stop"].fillna(False).astype(bool).sum()),
                "hit_1_5R_before_stop_count": int(group["hit_1_5R_before_stop"].fillna(False).astype(bool).sum()),
                "hit_2R_before_stop_count": int(group["hit_2R_before_stop"].fillna(False).astype(bool).sum()),
                "same_bar_ambiguity_count": same_bar,
                "first_stop_touch_count": first_stop,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _overlap_rows(local: pd.DataFrame, active: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "direction",
        "level_price",
        "sweep_h4_open_ts",
        "entry_ts",
        "local_row_number",
        "local_level_family",
        "active_row_number",
        "active_level_family",
    ]
    if local.empty or active.empty:
        return pd.DataFrame(columns=columns)
    local_key = local.copy()
    active_key = active.copy()
    local_key["level_key"] = local_key["level_price"].astype(float).round(8)
    active_key["level_key"] = active_key["active_level_price"].astype(float).round(8)
    for col in ["sweep_h4_open_ts", "entry_ts"]:
        local_key[col] = pd.to_datetime(local_key[col], utc=True).astype(str)
        active_key[col] = pd.to_datetime(active_key[col], utc=True).astype(str)
    merged = local_key.merge(
        active_key,
        on=["direction", "level_key", "sweep_h4_open_ts", "entry_ts"],
        how="inner",
        suffixes=("_local", "_active"),
    )
    if merged.empty:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        {
            "direction": merged["direction"],
            "level_price": merged["level_key"],
            "sweep_h4_open_ts": merged["sweep_h4_open_ts"],
            "entry_ts": merged["entry_ts"],
            "local_row_number": merged["row_number_local"],
            "local_level_family": merged["level_family_local"],
            "active_row_number": merged["row_number_active"],
            "active_level_family": merged["level_family_active"],
        },
        columns=columns,
    )


def write_local_h4_markdown(
    *,
    local_candidates: pd.DataFrame,
    active_candidates: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
) -> Path:
    local_summary = _family_summary(local_candidates)
    active_summary = _family_summary(active_candidates)
    overlap = _overlap_rows(local_candidates, active_candidates)
    focus_columns = [
        "row_number",
        "direction",
        "entry_ts",
        "level_family",
        "level_price",
        "sweep_extreme_price",
        "entry_price",
        "stop_price",
        "final_risk_usd",
        "diagnostic_trade_allowed",
        "no_trade_reason",
        "hit_1R_before_stop",
        "hit_1_5R_before_stop",
        "hit_2R_before_stop",
        "first_stop_touch_ts",
        "same_bar_ambiguity",
    ]
    overlap_columns = [
        "direction",
        "level_price",
        "sweep_h4_open_ts",
        "entry_ts",
        "local_row_number",
        "local_level_family",
        "active_row_number",
        "active_level_family",
    ]
    lines = [
        "# LOCAL H4 Reclaim Sweep-Extreme Stop V1 Buffer50 Diagnostic",
        "",
        "Date: 2026-05-05",
        "",
        "Status: standalone diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.",
        "",
        "This diagnostic uses latest/local confirmed H4 swing high/low selection, H4 reclaim-close entry, and sweep-extreme stop with fixed `buffer_usd=50`. It does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not use 1m entry, does not use reference-level stops, and does not run the Backtester.",
        "",
        "## Local Diagnostic Summary By Level Family",
        "",
        *_format_markdown_table(local_summary, list(local_summary.columns)),
        "",
        "## Current Active-Level Registry Comparison",
        "",
        *_format_markdown_table(active_summary, list(active_summary.columns)),
        "",
        "## Overlap By Direction, Level, Sweep Time, Entry Time",
        "",
        f"- Overlap rows: {int(len(overlap.index))}",
        "",
        *_format_markdown_table(overlap, overlap_columns),
        "",
        "## Local Candidate Rows",
        "",
        *_format_markdown_table(local_candidates, focus_columns),
        "",
        "## Files",
        "",
        f"- Diagnostic CSV: `{diagnostic_csv.as_posix()}`",
        f"- Report: `{output_path.as_posix()}`",
        "",
        "## Interpretation Boundary",
        "",
        "- This answers whether local H4 swing selection looks different once entry and stop are cleaned up.",
        "- MAIN and LOCAL buckets are separate setup families and must not be pooled as one H4 false-break/reclaim edge.",
        "- Any positive path-order rows remain diagnostic only until a separate research decision defines a formal contract and holdout path.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_local_h4_reclaim_sweep_extreme_stop_diagnostic(
    feed_dir: Path,
    output_path: Path,
    start: date,
    end: date,
    *,
    finding_output_path: Path | None = None,
) -> pd.DataFrame:
    raw = load_feed(feed_dir, start - timedelta(days=10), end + timedelta(days=4))
    h4 = build_h4_bars(raw)
    levels_by_idx = confirmed_levels(h4)

    local = scan_local_h4_reclaim_candidates(h4)
    local = filter_output_range(local, start, end)
    local = add_local_h4_sweep_extreme_stop_gates(local, stop_buffer_usd=50.0, max_risk_usd=MAX_RISK_USD)
    local = add_forward_diagnostics(local, raw)
    local = local.sort_values(["entry_ts", "direction", "candidate_id"], kind="mergesort").reset_index(drop=True)
    if not local.empty:
        local["row_number"] = range(1, len(local.index) + 1)
    public_local = _public_local_h4_frame(local)

    active = scan_candidates(h4)
    active = filter_output_range(active, start, end)
    active = _add_level_family_to_active_candidates(active, levels_by_idx=levels_by_idx)
    active = add_compressed_buffer_gates(active, stop_buffer_usd=STOP_BUFFER_USD, max_risk_usd=MAX_RISK_USD)
    active = add_forward_diagnostics(active, raw)
    active = active.sort_values(["entry_ts", "direction", "candidate_id"], kind="mergesort").reset_index(drop=True)
    if not active.empty:
        active["row_number"] = range(1, len(active.index) + 1)
        active["same_bar_ambiguity"] = active[
            ["same_bar_stop_1R", "same_bar_stop_1_5R", "same_bar_stop_2R"]
        ].fillna(False).any(axis=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    public_local.to_csv(output_path, index=False, encoding="utf-8")

    if finding_output_path is not None:
        write_local_h4_markdown(
            local_candidates=public_local,
            active_candidates=active,
            output_path=finding_output_path,
            diagnostic_csv=output_path,
        )

    return public_local


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-dir", default="feed", type=Path)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--long-audit-output", default=DEFAULT_LONG_AUDIT_OUTPUT, type=Path)
    parser.add_argument("--long-low-selection-audit-output", default=LONG_LOW_SELECTION_AUDIT_OUTPUT, type=Path)
    parser.add_argument("--long-low-selection-finding-output", default=LONG_LOW_SELECTION_FINDING_OUTPUT, type=Path)
    parser.add_argument("--finding-output", default=DEFAULT_FINDING_OUTPUT, type=Path)
    parser.add_argument("--stop-buffer-usd", default=STOP_BUFFER_USD, type=float)
    parser.add_argument("--compressed-buffer350", action="store_true")
    parser.add_argument("--level-registry", action="store_true")
    parser.add_argument("--local-h4-buffer50", action="store_true")
    args = parser.parse_args()

    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)
    if end < start:
        raise ValueError("end-date must be >= start-date")

    if args.local_h4_buffer50:
        output = args.output if args.output != Path(DEFAULT_OUTPUT) else Path(LOCAL_H4_BUFFER50_OUTPUT)
        finding = (
            args.finding_output
            if args.finding_output != Path(DEFAULT_FINDING_OUTPUT)
            else Path(LOCAL_H4_BUFFER50_FINDING_OUTPUT)
        )
        candidates = run_local_h4_reclaim_sweep_extreme_stop_diagnostic(
            args.feed_dir,
            output,
            start,
            end,
            finding_output_path=finding,
        )
        print(f"wrote {len(candidates)} local H4 buffer50 candidates to {output}")
        print(f"wrote local H4 buffer50 finding to {finding}")
    elif args.level_registry:
        output = args.output if args.output != Path(DEFAULT_OUTPUT) else Path(LEVEL_REGISTRY_OUTPUT)
        finding = (
            args.finding_output
            if args.finding_output != Path(DEFAULT_FINDING_OUTPUT)
            else Path(LEVEL_REGISTRY_FINDING_OUTPUT)
        )
        candidates = run_level_registry_diagnostic(
            args.feed_dir,
            output,
            start,
            end,
            finding_output_path=finding,
            stop_buffer_usd=args.stop_buffer_usd,
        )
        print(f"wrote {len(candidates)} level-registry candidates to {output}")
        print(f"wrote level-registry finding to {finding}")
    elif args.compressed_buffer350:
        output = args.output if args.output != Path(DEFAULT_OUTPUT) else Path(COMPRESSED_BUFFER350_OUTPUT)
        finding = (
            args.finding_output
            if args.finding_output != Path(DEFAULT_FINDING_OUTPUT)
            else Path(COMPRESSED_BUFFER350_FINDING_OUTPUT)
        )
        candidates = run_compressed_buffer_diagnostic(
            args.feed_dir,
            output,
            start,
            end,
            finding_output_path=finding,
            stop_buffer_usd=STOP_BUFFER_USD,
            max_risk_usd=MAX_RISK_USD,
        )
        print(f"wrote {len(candidates)} compressed candidates to {output}")
        print(f"wrote compressed finding to {finding}")
    else:
        candidates = run_diagnostic(
            args.feed_dir,
            args.output,
            start,
            end,
            stop_buffer_usd=args.stop_buffer_usd,
            long_audit_output_path=args.long_audit_output,
            long_low_selection_audit_output_path=args.long_low_selection_audit_output,
            long_low_selection_finding_output_path=args.long_low_selection_finding_output,
            finding_output_path=args.finding_output,
        )
        print(f"wrote {len(candidates)} candidates to {args.output}")
        print(f"wrote LONG audit to {args.long_audit_output}")
        print(f"wrote LONG low-selection audit to {args.long_low_selection_audit_output}")
        print(f"wrote LONG low-selection finding to {args.long_low_selection_finding_output}")
        print(f"wrote finding to {args.finding_output}")


if __name__ == "__main__":
    main()
