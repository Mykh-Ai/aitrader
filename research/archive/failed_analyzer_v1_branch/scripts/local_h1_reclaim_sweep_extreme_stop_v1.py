"""LOCAL H1 higher-low reclaim diagnostic with sweep-extreme buffer50 stop.

Standalone research diagnostic only. This script does not use the legacy
failed-break/reclaim detector, does not run the Backtester, and does not change
the frozen H4 diagnostic contract.
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

from analyzer.feed_contract import normalize_feed_timestamps
from analyzer.loader import load_raw_csv
from analyzer.schema import SchemaValidationError


VARIANT_ID = "LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50"
DEFAULT_START_DATE = "2026-03-12"
DEFAULT_END_DATE = "2026-05-04"
DEFAULT_OUTPUT = (
    "research/results/"
    "local_h1_reclaim_sweep_extreme_stop_v1_buffer50_2026-03-12_to_2026-05-04.csv"
)
DEFAULT_FINDING_OUTPUT = (
    "research/findings/"
    "LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md"
)

LOOKBACK_H1_BARS = 120
RECLAIM_WINDOW_H1_BARS = 12
CLUSTER_WINDOW_HOURS = 48
STOP_BUFFER_USD = 50.0
MAX_RISK_USD = 1500.0
PATH_WINDOW_MINUTES = 4 * 24 * 60
FEE_ROUNDTRIP_RATE = 0.002

OUTPUT_COLUMNS = [
    "candidate_id",
    "row_number",
    "cluster_id",
    "keep_or_duplicate",
    "duplicate_count_in_cluster",
    "direction",
    "level_family",
    "level_price",
    "level_confirmed_ts",
    "level_age_h1_bars",
    "prior_major_low_120h1",
    "prior_major_low_confirmed_ts",
    "relation_to_major_low",
    "sweep_h1_open_ts",
    "sweep_h1_close_ts",
    "sweep_extreme_price",
    "sweep_depth",
    "sweep_h1_row_count",
    "sweep_h1_incomplete",
    "reclaim_h1_open_ts",
    "reclaim_h1_close_ts",
    "reclaim_number",
    "reclaim_open_price",
    "reclaim_close_price",
    "reclaim_distance",
    "reclaim_body_direction",
    "reclaim_body_pct",
    "reclaim_h1_row_count",
    "reclaim_h1_incomplete",
    "entry_ts",
    "entry_price",
    "stop_price",
    "final_risk_usd",
    "diagnostic_trade_allowed",
    "no_trade_reason",
    "MFE_R",
    "MFE_usd",
    "fee_as_R",
    "net_MFE_R",
    "net_MFE_usd",
    "hit_1_5R",
    "hit_2R",
    "hit_3R",
    "hit_5R",
    "hit_10R",
    "first_stop_touch_ts",
    "time_to_1_5R",
    "time_to_2R",
    "time_to_3R",
    "time_to_5R",
    "time_to_10R",
    "incomplete_forward_window",
    "favorable_move_24h_usd",
    "adverse_move_24h_usd",
    "favorable_move_48h_usd",
    "adverse_move_48h_usd",
    "favorable_move_96h_usd",
    "adverse_move_96h_usd",
    "notes",
]


@dataclass(frozen=True)
class ConfirmedLow:
    price: float
    confirmed_ts: pd.Timestamp
    confirmed_idx: int


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


def _load_ohlc_csv(path: Path) -> pd.DataFrame:
    try:
        return load_raw_csv(path)
    except SchemaValidationError as exc:
        if "Missing required raw columns" not in str(exc):
            raise

    df = pd.read_csv(path, encoding="utf-8")
    required = {"Timestamp", "Open", "High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise SchemaValidationError(f"Missing required OHLC columns for H1 diagnostic: {sorted(missing)}")

    df = normalize_feed_timestamps(df)
    for column in ["Open", "High", "Low", "Close"]:
        df[column] = pd.to_numeric(df[column], errors="raise")
    df = df.sort_values("Timestamp", ascending=True, kind="mergesort").reset_index(drop=True)
    duplicate_mask = df["Timestamp"].duplicated(keep=False)
    if duplicate_mask.any():
        sample = df.loc[duplicate_mask, "Timestamp"].head(5).astype(str).tolist()
        raise SchemaValidationError(f"Duplicate Timestamp values found: {sample}")
    return df


def load_feed(feed_dir: Path, start: date, end: date) -> pd.DataFrame:
    paths = _iter_feed_paths(feed_dir, start, end)
    if not paths:
        raise FileNotFoundError(f"No feed CSV files found in {feed_dir} for {start}..{end}")

    frames = [_load_ohlc_csv(path) for path in paths]
    raw = pd.concat(frames, ignore_index=True, sort=False)
    raw = raw.sort_values("Timestamp", kind="mergesort").reset_index(drop=True)
    duplicate_ts = raw["Timestamp"].duplicated(keep=False)
    if duplicate_ts.any():
        sample = raw.loc[duplicate_ts, "Timestamp"].head(5).astype(str).tolist()
        raise ValueError(f"Duplicate normalized feed timestamps after concat: {sample}")
    return raw


def build_h1_bars(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"Timestamp", "Open", "High", "Low", "Close"}
    missing = required - set(raw.columns)
    if missing:
        raise KeyError(f"Missing required raw columns for H1 diagnostic: {sorted(missing)}")

    data = raw.loc[:, ["Timestamp", "Open", "High", "Low", "Close"]].copy()
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], utc=True, errors="raise")
    bars = (
        data.set_index("Timestamp")
        .resample("1h", label="left", closed="left")
        .agg(
            Open=("Open", "first"),
            High=("High", "max"),
            Low=("Low", "min"),
            Close=("Close", "last"),
            RowCount=("Close", "count"),
        )
        .dropna(subset=["Open", "High", "Low", "Close"])
        .reset_index()
        .rename(columns={"Timestamp": "h1_open_ts"})
    )
    bars["h1_open_ts"] = pd.to_datetime(bars["h1_open_ts"], utc=True)
    bars["h1_close_ts"] = bars["h1_open_ts"] + pd.Timedelta(hours=1)
    bars["h1_incomplete"] = bars["RowCount"].astype(int) < 60
    return bars.reset_index(drop=True)


def confirmed_lows(h1: pd.DataFrame) -> dict[int, list[ConfirmedLow]]:
    by_idx: dict[int, list[ConfirmedLow]] = {}
    if len(h1.index) < 3:
        return by_idx

    for idx in range(1, len(h1.index) - 1):
        prev_bar = h1.iloc[idx - 1]
        center = h1.iloc[idx]
        next_bar = h1.iloc[idx + 1]
        confirm_idx = idx + 2
        if confirm_idx >= len(h1.index):
            continue
        confirm_bar = h1.iloc[confirm_idx]
        if any(
            bool(bar.get("h1_incomplete", False))
            for bar in (prev_bar, center, next_bar, confirm_bar)
        ):
            continue

        if float(center["Low"]) < float(prev_bar["Low"]) and float(center["Low"]) < float(next_bar["Low"]):
            by_idx.setdefault(confirm_idx, []).append(
                ConfirmedLow(
                    price=float(center["Low"]),
                    confirmed_ts=pd.Timestamp(confirm_bar["h1_open_ts"]),
                    confirmed_idx=confirm_idx,
                )
            )
    return by_idx


def _candidate_id(level: ConfirmedLow, reclaim_close_ts: pd.Timestamp) -> str:
    payload = (
        f"{VARIANT_ID}|LONG|{level.confirmed_ts.isoformat()}|"
        f"{level.price:.8f}|{reclaim_close_ts.isoformat()}"
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"LH1RSE1_LONG_{digest}"


def _all_lows_before(
    levels_by_idx: dict[int, list[ConfirmedLow]],
    *,
    sweep_idx: int,
) -> list[ConfirmedLow]:
    lows: list[ConfirmedLow] = []
    for idx, levels in levels_by_idx.items():
        if sweep_idx - LOOKBACK_H1_BARS <= idx <= sweep_idx:
            lows.extend(levels)
    return sorted(lows, key=lambda item: (item.confirmed_idx, item.confirmed_ts))


def _prior_major_low(
    levels_by_idx: dict[int, list[ConfirmedLow]],
    *,
    selected: ConfirmedLow,
    sweep_idx: int,
) -> ConfirmedLow | None:
    lows = [
        low
        for low in _all_lows_before(levels_by_idx, sweep_idx=sweep_idx)
        if low.confirmed_idx != selected.confirmed_idx
    ]
    below_selected = [low for low in lows if float(low.price) < float(selected.price)]
    if not below_selected:
        return None
    return min(below_selected, key=lambda item: (item.price, -item.confirmed_idx))


def _reclaim_body_pct(open_price: float, high: float, low: float, close: float) -> float:
    candle_range = high - low
    if candle_range <= 0:
        return 0.0
    return abs(close - open_price) / candle_range


def _candidate_row(
    *,
    level: ConfirmedLow,
    prior_major: ConfirmedLow,
    sweep_idx: int,
    sweep_bar: pd.Series,
    reclaim_bar: pd.Series,
    reclaim_number: int,
) -> dict[str, object]:
    reclaim_close_ts = pd.Timestamp(reclaim_bar["h1_close_ts"])
    entry_price = float(reclaim_bar["Close"])
    sweep_extreme = float(sweep_bar["Low"])
    stop_price = sweep_extreme - STOP_BUFFER_USD
    risk = entry_price - stop_price
    reasons: list[str] = []
    if risk <= 0:
        reasons.append("invalid_risk")
    elif risk > MAX_RISK_USD:
        reasons.append("sweep_extreme_risk_too_large")

    reclaim_open = float(reclaim_bar["Open"])
    reclaim_high = float(reclaim_bar["High"])
    reclaim_low = float(reclaim_bar["Low"])
    reclaim_close = float(reclaim_bar["Close"])
    allowed = not reasons
    return {
        "candidate_id": _candidate_id(level, reclaim_close_ts),
        "direction": "LONG",
        "level_family": "LOCAL_HIGHER_LOW_SWEEP",
        "level_price": level.price,
        "level_confirmed_ts": level.confirmed_ts,
        "level_age_h1_bars": int(sweep_idx - level.confirmed_idx),
        "prior_major_low_120h1": prior_major.price,
        "prior_major_low_confirmed_ts": prior_major.confirmed_ts,
        "relation_to_major_low": "above_unswept_prior_major_low",
        "sweep_h1_open_ts": pd.Timestamp(sweep_bar["h1_open_ts"]),
        "sweep_h1_close_ts": pd.Timestamp(sweep_bar["h1_close_ts"]),
        "sweep_extreme_price": sweep_extreme,
        "sweep_depth": level.price - sweep_extreme,
        "sweep_h1_row_count": int(sweep_bar["RowCount"]),
        "sweep_h1_incomplete": bool(sweep_bar["h1_incomplete"]),
        "reclaim_h1_open_ts": pd.Timestamp(reclaim_bar["h1_open_ts"]),
        "reclaim_h1_close_ts": reclaim_close_ts,
        "reclaim_number": reclaim_number,
        "reclaim_open_price": reclaim_open,
        "reclaim_close_price": reclaim_close,
        "reclaim_distance": reclaim_close - level.price,
        "reclaim_body_direction": "bullish" if reclaim_close > reclaim_open else "bearish_or_flat",
        "reclaim_body_pct": _reclaim_body_pct(reclaim_open, reclaim_high, reclaim_low, reclaim_close),
        "reclaim_h1_row_count": int(reclaim_bar["RowCount"]),
        "reclaim_h1_incomplete": bool(reclaim_bar["h1_incomplete"]),
        "entry_ts": reclaim_close_ts,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "final_risk_usd": risk,
        "risk_usd": risk,
        "diagnostic_trade_allowed": allowed,
        "no_trade_reason": ";".join(reasons),
        "notes": "diagnostic_only;local_h1_higher_low_reclaim_close_entry;sweep_extreme_stop_buffer50;legacy_failed_break_reclaim_not_used;backtester_not_used",
    }


def scan_local_h1_higher_low_reclaim_candidates(h1: pd.DataFrame) -> pd.DataFrame:
    levels_by_idx = confirmed_lows(h1)
    selected_low: ConfirmedLow | None = None
    swept_low: dict[str, object] | None = None
    rows: list[dict[str, object]] = []

    for idx, bar in h1.iterrows():
        idx_int = int(idx)
        levels = levels_by_idx.get(idx_int, [])

        if swept_low is not None:
            sweep_idx = int(swept_low["sweep_idx"])
            reclaim_number = idx_int - sweep_idx
            if 1 <= reclaim_number <= RECLAIM_WINDOW_H1_BARS:
                level = swept_low["level"]
                prior_major = swept_low["prior_major"]
                assert isinstance(level, ConfirmedLow)
                assert isinstance(prior_major, ConfirmedLow)
                if float(bar["Close"]) > level.price:
                    rows.append(
                        _candidate_row(
                            level=level,
                            prior_major=prior_major,
                            sweep_idx=sweep_idx,
                            sweep_bar=swept_low["sweep_bar"],  # type: ignore[arg-type]
                            reclaim_bar=bar,
                            reclaim_number=reclaim_number,
                        )
                    )
                    selected_low = None
                    swept_low = None
                elif reclaim_number == RECLAIM_WINDOW_H1_BARS:
                    selected_low = None
                    swept_low = None
            elif reclaim_number > RECLAIM_WINDOW_H1_BARS:
                selected_low = None
                swept_low = None
        else:
            low_levels = levels
            if low_levels:
                selected_low = low_levels[-1]
            if selected_low is not None and float(bar["Low"]) < selected_low.price:
                prior_major = _prior_major_low(
                    levels_by_idx,
                    selected=selected_low,
                    sweep_idx=idx_int,
                )
                if prior_major is not None and selected_low.price > prior_major.price and float(bar["Low"]) > prior_major.price:
                    swept_low = {
                        "level": selected_low,
                        "prior_major": prior_major,
                        "sweep_idx": idx_int,
                        "sweep_bar": bar,
                    }
                else:
                    selected_low = None

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame(rows)


def _first_touch_ts(window: pd.DataFrame, mask: pd.Series) -> pd.Timestamp | pd.NaT:
    if mask.any():
        return pd.Timestamp(window.loc[mask, "Timestamp"].iloc[0])
    return pd.NaT


def _window_before_ts(window: pd.DataFrame, ts: pd.Timestamp | pd.NaT) -> pd.DataFrame:
    if pd.isna(ts):
        return window
    return window.loc[pd.to_datetime(window["Timestamp"], utc=True) < pd.Timestamp(ts)]


def _duration_minutes(start_ts: pd.Timestamp, end_ts: pd.Timestamp | pd.NaT) -> float | pd.NA:
    if pd.isna(end_ts):
        return pd.NA
    return (pd.Timestamp(end_ts) - pd.Timestamp(start_ts)).total_seconds() / 60.0


def _future_window_moves(
    raw: pd.DataFrame,
    *,
    entry_ts: pd.Timestamp,
    entry_price: float,
) -> tuple[dict[str, object], list[str]]:
    raw_ts = pd.to_datetime(raw["Timestamp"], utc=True)
    out: dict[str, object] = {}
    notes: list[str] = []
    for label, minutes in [("24h", 24 * 60), ("48h", 48 * 60), ("96h", 96 * 60)]:
        end_ts = entry_ts + pd.Timedelta(minutes=minutes)
        window = raw.loc[(raw_ts >= entry_ts) & (raw_ts < end_ts)]
        if window.empty:
            out[f"favorable_move_{label}_usd"] = pd.NA
            out[f"adverse_move_{label}_usd"] = pd.NA
            notes.append(f"future_{label}_missing")
            continue
        out[f"favorable_move_{label}_usd"] = float(window["High"].max()) - entry_price
        out[f"adverse_move_{label}_usd"] = entry_price - float(window["Low"].min())
        if len(window.index) < minutes:
            notes.append(f"future_{label}_partial_rows={len(window.index)}/{minutes}")
    return out, notes


def _path_diagnostics(raw: pd.DataFrame, row: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    entry_ts = pd.Timestamp(row["entry_ts"])
    entry_price = float(row["entry_price"])
    risk = float(row["final_risk_usd"])
    stop_price = float(row["stop_price"])
    raw_ts = pd.to_datetime(raw["Timestamp"], utc=True)
    end_ts = entry_ts + pd.Timedelta(minutes=PATH_WINDOW_MINUTES)
    window = raw.loc[(raw_ts >= entry_ts) & (raw_ts < end_ts)].copy()

    out: dict[str, object] = {
        "MFE_R": pd.NA,
        "MFE_usd": pd.NA,
        "fee_as_R": pd.NA,
        "net_MFE_R": pd.NA,
        "net_MFE_usd": pd.NA,
        "first_stop_touch_ts": pd.NaT,
        "incomplete_forward_window": True,
    }
    for multiple in ("1_5", "2", "3", "5", "10"):
        out[f"hit_{multiple}R"] = False
        out[f"time_to_{multiple}R"] = pd.NA

    notes: list[str] = []
    if window.empty:
        notes.append("path_96h_missing")
        return out, notes
    out["incomplete_forward_window"] = len(window.index) < PATH_WINDOW_MINUTES
    if bool(out["incomplete_forward_window"]):
        notes.append(f"path_96h_partial_rows={len(window.index)}/{PATH_WINDOW_MINUTES}")
    if risk <= 0:
        notes.append("path_order_skipped_invalid_risk")
        return out, notes

    stop_mask = window["Low"] <= stop_price
    stop_ts = _first_touch_ts(window, stop_mask)
    out["first_stop_touch_ts"] = stop_ts
    before_stop = _window_before_ts(window, stop_ts)
    if not before_stop.empty:
        mfe_usd = float(before_stop["High"].max()) - entry_price
        out["MFE_usd"] = mfe_usd
        out["MFE_R"] = mfe_usd / risk
        fee_usd = entry_price * FEE_ROUNDTRIP_RATE
        out["fee_as_R"] = fee_usd / risk
        out["net_MFE_R"] = float(out["MFE_R"]) - float(out["fee_as_R"])
        out["net_MFE_usd"] = mfe_usd - fee_usd

    for multiple, label in [(1.5, "1_5"), (2.0, "2"), (3.0, "3"), (5.0, "5"), (10.0, "10")]:
        target_ts = _first_touch_ts(window, window["High"] >= entry_price + (multiple * risk))
        hit = bool(pd.notna(target_ts) and (pd.isna(stop_ts) or pd.Timestamp(target_ts) < pd.Timestamp(stop_ts)))
        out[f"hit_{label}R"] = hit
        if hit:
            out[f"time_to_{label}R"] = _duration_minutes(entry_ts, target_ts)

    return out, notes


def add_forward_diagnostics(candidates: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, object]] = []
    for row in candidates.to_dict("records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        entry_price = float(row["entry_price"])
        moves, move_notes = _future_window_moves(raw, entry_ts=entry_ts, entry_price=entry_price)
        if bool(row["diagnostic_trade_allowed"]):
            path, path_notes = _path_diagnostics(raw, row)
        else:
            path = {
                "MFE_R": pd.NA,
                "MFE_usd": pd.NA,
                "fee_as_R": pd.NA,
                "net_MFE_R": pd.NA,
                "net_MFE_usd": pd.NA,
                "hit_1_5R": False,
                "hit_2R": False,
                "hit_3R": False,
                "hit_5R": False,
                "hit_10R": False,
                "first_stop_touch_ts": pd.NaT,
                "time_to_1_5R": pd.NA,
                "time_to_2R": pd.NA,
                "time_to_3R": pd.NA,
                "time_to_5R": pd.NA,
                "time_to_10R": pd.NA,
                "incomplete_forward_window": pd.NA,
            }
            path_notes = ["path_order_skipped_no_trade"]
        merged = {**row, **moves, **path}
        notes = [*move_notes, *path_notes]
        if notes:
            merged["notes"] = f"{merged['notes']};" + ";".join(notes)
        rows.append(merged)

    return pd.DataFrame(rows)


def filter_output_range(candidates: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    start_ts = pd.Timestamp(start.isoformat(), tz="UTC")
    end_exclusive = pd.Timestamp((end + timedelta(days=1)).isoformat(), tz="UTC")
    entry_ts = pd.to_datetime(candidates["entry_ts"], utc=True)
    return candidates.loc[(entry_ts >= start_ts) & (entry_ts < end_exclusive)].reset_index(drop=True)


def apply_cluster_first_rule(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()

    out = candidates.sort_values(["entry_ts", "candidate_id"], kind="mergesort").reset_index(drop=True).copy()
    out["cluster_id"] = pd.NA
    out["keep_or_duplicate"] = "no_trade"
    out["duplicate_count_in_cluster"] = 0

    allowed_idx = out.index[out["diagnostic_trade_allowed"].fillna(False).astype(bool)].tolist()
    cluster_id = 0
    last_allowed_entry_ts: pd.Timestamp | None = None
    cluster_members: dict[int, list[int]] = {}
    for idx in allowed_idx:
        entry_ts = pd.Timestamp(out.at[idx, "entry_ts"])
        if last_allowed_entry_ts is None or entry_ts - last_allowed_entry_ts > pd.Timedelta(hours=CLUSTER_WINDOW_HOURS):
            cluster_id += 1
            cluster_members[cluster_id] = []
        cluster_members[cluster_id].append(int(idx))
        out.at[idx, "cluster_id"] = f"LH1_LONG_CLUSTER_{cluster_id:03d}"
        last_allowed_entry_ts = entry_ts

    for members in cluster_members.values():
        duplicate_count = max(len(members) - 1, 0)
        for position, idx in enumerate(members):
            out.at[idx, "duplicate_count_in_cluster"] = duplicate_count
            out.at[idx, "keep_or_duplicate"] = "cluster_first" if position == 0 else "duplicate_same_move"

    out["row_number"] = range(1, len(out.index) + 1)
    return out


def _count_bool(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].fillna(False).astype(bool).sum())


def _median(df: pd.DataFrame, column: str) -> str:
    if df.empty or column not in df.columns:
        return "n/a"
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.empty:
        return "n/a"
    return f"{float(values.median()):.4f}"


def _format_markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    if df.empty:
        return ["_No rows._"]
    view = df.loc[:, [column for column in columns if column in df.columns]].copy()
    for column in view.columns:
        view[column] = view[column].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in view.astype(str).values.tolist()]
    return [header, separator, *rows]


def _summary_rows(candidates: pd.DataFrame) -> pd.DataFrame:
    retained = candidates.loc[candidates["keep_or_duplicate"] == "cluster_first"] if not candidates.empty else candidates
    rows: list[dict[str, object]] = []
    periods = [
        ("2026-03-12_to_2026-03-29", pd.Timestamp("2026-03-12T00:00:00Z"), pd.Timestamp("2026-03-30T00:00:00Z")),
        ("2026-03-30_to_2026-05-02", pd.Timestamp("2026-03-30T00:00:00Z"), pd.Timestamp("2026-05-03T00:00:00Z")),
        ("2026-05-03_to_2026-05-04", pd.Timestamp("2026-05-03T00:00:00Z"), pd.Timestamp("2026-05-05T00:00:00Z")),
    ]
    for label, start_ts, end_ts in periods:
        if retained.empty:
            period = retained
        else:
            entry_ts = pd.to_datetime(retained["entry_ts"], utc=True)
            period = retained.loc[(entry_ts >= start_ts) & (entry_ts < end_ts)]
        rows.append(
            {
                "period": label,
                "retained": len(period.index),
                "median_risk": _median(period, "final_risk_usd"),
                "median_MFE_R": _median(period, "MFE_R"),
                "median_net_MFE_R": _median(period, "net_MFE_R"),
                "hit_1_5R": _count_bool(period, "hit_1_5R"),
                "hit_2R": _count_bool(period, "hit_2R"),
                "hit_3R": _count_bool(period, "hit_3R"),
                "hit_5R": _count_bool(period, "hit_5R"),
                "hit_10R": _count_bool(period, "hit_10R"),
            }
        )
    return pd.DataFrame(rows)


def write_markdown_report(
    *,
    candidates: pd.DataFrame,
    h1: pd.DataFrame,
    output_path: Path,
    diagnostic_csv: Path,
    start: date,
    end: date,
) -> Path:
    raw_candidates = int(len(candidates.index))
    allowed = candidates.loc[candidates["diagnostic_trade_allowed"] == True] if not candidates.empty else candidates
    retained = candidates.loc[candidates["keep_or_duplicate"] == "cluster_first"] if not candidates.empty else candidates
    duplicate_rows = candidates.loc[candidates["keep_or_duplicate"] == "duplicate_same_move"] if not candidates.empty else candidates
    unique_clusters = int(retained["cluster_id"].nunique(dropna=True)) if not retained.empty else 0
    incomplete_h1_bars = int(h1["h1_incomplete"].fillna(False).astype(bool).sum()) if not h1.empty else 0

    summary = pd.DataFrame(
        [
            {
                "metric": "raw_candidates",
                "value": raw_candidates,
            },
            {
                "metric": "allowed_candidates",
                "value": int(len(allowed.index)),
            },
            {
                "metric": "unique_clusters",
                "value": unique_clusters,
            },
            {
                "metric": "retained_cluster_first_rows",
                "value": int(len(retained.index)),
            },
            {
                "metric": "duplicate_rows_removed",
                "value": int(len(duplicate_rows.index)),
            },
            {
                "metric": "incomplete_h1_bar_count",
                "value": incomplete_h1_bars,
            },
            {
                "metric": "incomplete_forward_window_rows",
                "value": _count_bool(retained, "incomplete_forward_window"),
            },
            {
                "metric": "median_risk",
                "value": _median(retained, "final_risk_usd"),
            },
            {
                "metric": "median_MFE_R",
                "value": _median(retained, "MFE_R"),
            },
            {
                "metric": "median_MFE_usd",
                "value": _median(retained, "MFE_usd"),
            },
            {
                "metric": "median_net_MFE_R",
                "value": _median(retained, "net_MFE_R"),
            },
            {
                "metric": "hit_1_5R",
                "value": f"{_count_bool(retained, 'hit_1_5R')}/{len(retained.index)}",
            },
            {
                "metric": "hit_2R",
                "value": f"{_count_bool(retained, 'hit_2R')}/{len(retained.index)}",
            },
            {
                "metric": "hit_3R",
                "value": f"{_count_bool(retained, 'hit_3R')}/{len(retained.index)}",
            },
            {
                "metric": "hit_5R",
                "value": f"{_count_bool(retained, 'hit_5R')}/{len(retained.index)}",
            },
            {
                "metric": "hit_10R",
                "value": f"{_count_bool(retained, 'hit_10R')}/{len(retained.index)}",
            },
        ]
    )
    period_summary = _summary_rows(candidates)

    h4_compare = pd.DataFrame(
        [
            {
                "surface": "H4 LOCAL_HIGHER_LOW full-range status",
                "retained": 7,
                "median_MFE_R": "2.2077",
                "median_net_MFE_R": "1.6898",
                "hit_1_5R": "5/7",
                "hit_2R": "4/7",
                "hit_3R": "3/7",
                "hit_5R": "1/7",
                "hit_10R": "1/7",
            },
            {
                "surface": "H1 LOCAL_HIGHER_LOW buffer50 diagnostic",
                "retained": int(len(retained.index)),
                "median_MFE_R": _median(retained, "MFE_R"),
                "median_net_MFE_R": _median(retained, "net_MFE_R"),
                "hit_1_5R": f"{_count_bool(retained, 'hit_1_5R')}/{len(retained.index)}",
                "hit_2R": f"{_count_bool(retained, 'hit_2R')}/{len(retained.index)}",
                "hit_3R": f"{_count_bool(retained, 'hit_3R')}/{len(retained.index)}",
                "hit_5R": f"{_count_bool(retained, 'hit_5R')}/{len(retained.index)}",
                "hit_10R": f"{_count_bool(retained, 'hit_10R')}/{len(retained.index)}",
            },
        ]
    )

    if len(retained.index) > 7 and _count_bool(retained, "hit_3R") >= 3:
        density_read = "H1 increases row density, but cluster-level quality still needs manual review before any ruleset discussion."
    elif len(retained.index) > 7:
        density_read = "H1 increases row density, but expansion quality does not clearly improve versus the H4 status benchmark."
    else:
        density_read = "H1 does not clearly increase useful cluster-first signal density versus the H4 status benchmark."

    lines = [
        "# LOCAL H1 Reclaim Sweep-Extreme Stop V1 Buffer50 Diagnostic",
        "",
        "Date: 2026-05-05",
        "",
        "Status: standalone diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.",
        "",
        "This diagnostic is separate from the frozen H4 contract. It does not use the legacy failed-break/reclaim detector and does not run the Backtester.",
        "",
        "## Contract",
        "",
        "- Direction: LONG only.",
        "- Level family: `LOCAL_HIGHER_LOW_SWEEP` only.",
        "- H1 bars: normalized UTC 1m feed resampled with `1h`, `label=left`, `closed=left`; incomplete H1 bars are marked when `RowCount < 60`.",
        "- Level selection: latest strict 3-candle H1 pivot low, confirmed at `idx + 2` using the confirmation bar `h1_open_ts`; incomplete H1 bars cannot form confirmed pivot lows.",
        "- Prior major low context: lowest confirmed pivot low over prior 120 H1 bars; selected local low must be above it, and the sweep candle must not break it.",
        "- Sweep/reclaim: H1 low sweeps selected local higher-low, sweep candle excluded, reclaim close above level within max 12 H1 bars.",
        "- Entry: reclaim H1 close timestamp and close price.",
        "- Stop: sweep extreme low minus fixed 50 USD; max risk 1500 USD; no compression.",
        "- Cluster: first allowed candidate per 48h same-direction cluster is retained; later allowed rows are `duplicate_same_move`.",
        "- Forward diagnostics: normalized 1m path over 24h / 48h / 96h, with incomplete forward windows marked.",
        "",
        "## Run",
        "",
        f"- Window: `{start.isoformat()}` to `{end.isoformat()}`.",
        f"- Diagnostic CSV: `{diagnostic_csv.as_posix()}`",
        "",
        "## Summary",
        "",
        *_format_markdown_table(summary, ["metric", "value"]),
        "",
        "## Subperiod Split",
        "",
        *_format_markdown_table(period_summary, list(period_summary.columns)),
        "",
        "## H4 Status Comparison",
        "",
        *_format_markdown_table(h4_compare, list(h4_compare.columns)),
        "",
        "## Verdict",
        "",
        "- H1 result is diagnostic only.",
        "- No ruleset promotion.",
        f"- Density read: {density_read}",
        "- Any apparent improvement must be audited for duplicated/choppy H1 clustering before it can be treated as evidence.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_diagnostic(
    feed_dir: Path,
    output_path: Path,
    start: date,
    end: date,
    *,
    finding_output_path: Path | None = None,
) -> pd.DataFrame:
    raw = load_feed(feed_dir, start - timedelta(days=5), end + timedelta(days=4))
    h1 = build_h1_bars(raw)
    candidates = scan_local_h1_higher_low_reclaim_candidates(h1)
    candidates = filter_output_range(candidates, start, end)
    candidates = add_forward_diagnostics(candidates, raw)
    candidates = apply_cluster_first_rule(candidates)
    if not candidates.empty:
        candidates = candidates.loc[:, [column for column in OUTPUT_COLUMNS if column in candidates.columns]].copy()
    else:
        candidates = pd.DataFrame(columns=OUTPUT_COLUMNS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output_path, index=False, encoding="utf-8")

    if finding_output_path is not None:
        write_markdown_report(
            candidates=candidates,
            h1=h1,
            output_path=finding_output_path,
            diagnostic_csv=output_path,
            start=start,
            end=end,
        )

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-dir", default="feed", type=Path)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--finding-output", default=DEFAULT_FINDING_OUTPUT, type=Path)
    args = parser.parse_args()

    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)
    if end < start:
        raise ValueError("end-date must be >= start-date")

    candidates = run_diagnostic(
        args.feed_dir,
        args.output,
        start,
        end,
        finding_output_path=args.finding_output,
    )
    print(f"wrote {len(candidates)} local H1 buffer50 candidates to {args.output}")
    print(f"wrote local H1 buffer50 finding to {args.finding_output}")


if __name__ == "__main__":
    main()
