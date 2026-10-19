from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


QUALIFIED_H1_SWEEP_RECLAIM_VERSION = "SHI_RESET_38M_QUALIFIED_H1_SWEEP_RECLAIM_V0"

MIN_LEVEL_AGE_H1_BARS = 3
MIN_SWING_CENTER_TO_SWEEP_H1_BARS = 5
REACTION_LEVEL_FRACTION = 0.003
REACTION_ATR_FRACTION = 0.25
PENETRATION_LEVEL_FRACTION = 0.0003
PENETRATION_ATR_FRACTION = 0.05
VOLUME_EXPANSION_RATIO = 1.3
RECLAIM_WINDOW_H1_BARS = 3
STOP_BUFFER_FRACTION = 0.0001

MEANINGFUL_REFERENCE_TYPES = {
    "H1_SWING_HIGH",
    "H1_SWING_LOW",
    "H4_SWING_HIGH",
    "H4_SWING_LOW",
    "ACTIVE_STRUCTURAL_LIQUIDITY_ZONE",
    "STRUCTURAL_SUPPORT_RESISTANCE_FLIP",
}

OUTPUT_COLUMNS = [
    "reference_id",
    "sweep_h1_close_ts",
    "sweep_direction",
    "raw_sweep",
    "sweep_h1_completed",
    "sweep_reference_level",
    "sweep_reference_type",
    "level_age_h1_bars",
    "swing_center_to_sweep_distance_h1_bars",
    "reaction_abs",
    "reaction_rel",
    "atr_h1_14",
    "penetration_abs",
    "penetration_rel",
    "penetration_quality",
    "sweep_wick_present",
    "sweep_body_direction",
    "sweep_h1_total_qty",
    "rolling_h1_volume_median_20",
    "sweep_volume_ratio",
    "volume_expansion_flag",
    "qualified_h1_sweep",
    "qualified_h1_sweep_reject_reason",
    "qualified_h1_failed_reclaim",
    "reclaim_h1_close_ts",
    "reclaim_bar_number_after_sweep",
    "reclaim_close_price",
    "reclaim_direction",
    "entry_candidate_ts",
    "entry_candidate_price",
    "stop_candidate_price",
    "reclaim_reject_reason",
    "evidence_summary",
]


@dataclass(frozen=True)
class QualifiedH1SweepReclaimResult:
    events: pd.DataFrame


def detect_qualified_h1_sweep_reclaims(
    *,
    h1_bars: pd.DataFrame,
    reference_levels: pd.DataFrame,
    reclaim_window_h1_bars: int = RECLAIM_WINDOW_H1_BARS,
) -> pd.DataFrame:
    """Return research-only qualified H1 sweep/reclaim facts.

    The detector consumes completed H1 bars and pre-existing reference levels.
    Raw crossings are recorded, but a crossing becomes qualified only after the
    structural quality contract is satisfied.
    """
    bars = _prepare_h1_bars(h1_bars)
    refs = _prepare_reference_levels(reference_levels)
    if bars.empty or refs.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, object]] = []
    for _, ref in refs.iterrows():
        sweep = _first_raw_sweep(bars, ref)
        if sweep is None:
            continue
        row = _qualified_sweep_row(bars, ref, sweep)
        _attach_failed_reclaim(row, bars, sweep, reclaim_window_h1_bars)
        rows.append(row)
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def raw_m1_sweep_observation(
    *,
    m1_rows: pd.DataFrame,
    reference_level: float,
    direction: str,
) -> bool:
    """Observation-only M1 crossing helper.

    This exists to make the boundary explicit in tests and downstream code:
    an M1 micro-cross may be a raw observation, but it is never a qualified H1
    sweep by itself.
    """
    if m1_rows.empty:
        return False
    frame = m1_rows.copy()
    columns = _lower_columns(frame)
    high = pd.to_numeric(frame[columns["high"]], errors="coerce")
    low = pd.to_numeric(frame[columns["low"]], errors="coerce")
    if direction == "BEARISH":
        return bool((high > reference_level).any())
    if direction == "BULLISH":
        return bool((low < reference_level).any())
    raise ValueError("direction must be BEARISH or BULLISH")



def evaluate_qualified_h1_sweep_reclaim_at(
    *,
    h1_bars: pd.DataFrame,
    reference_level: float,
    reference_type: str,
    direction: str,
    confirmed_at: str,
    sweep_h1_close_ts: str,
    reference_id: str = "reference",
    swing_center_timestamp: str = "",
    reclaim_window_h1_bars: int = RECLAIM_WINDOW_H1_BARS,
) -> dict[str, object]:
    """Evaluate one explicit H1 close timestamp against the qualified contract."""
    bars = _prepare_h1_bars(h1_bars)
    if bars.empty:
        return _empty_explicit_row(
            reference_id=reference_id,
            sweep_h1_close_ts=sweep_h1_close_ts,
            direction=direction,
            reference_level=reference_level,
            reference_type=reference_type,
            reject_reason="missing_h1_bars",
        )
    sweep_ts = pd.Timestamp(sweep_h1_close_ts)
    if sweep_ts.tzinfo is None:
        sweep_ts = sweep_ts.tz_localize("UTC")
    matches = bars[bars["timestamp"] == sweep_ts]
    if matches.empty:
        return _empty_explicit_row(
            reference_id=reference_id,
            sweep_h1_close_ts=sweep_h1_close_ts,
            direction=direction,
            reference_level=reference_level,
            reference_type=reference_type,
            reject_reason="h1_bar_not_found_at_setup_timestamp",
        )
    sweep = matches.iloc[0]
    raw_cross = (
        float(sweep["high"]) > float(reference_level)
        if direction == "BEARISH"
        else float(sweep["low"]) < float(reference_level)
        if direction == "BULLISH"
        else False
    )
    if not raw_cross:
        return _empty_explicit_row(
            reference_id=reference_id,
            sweep_h1_close_ts=sweep_h1_close_ts,
            direction=direction,
            reference_level=reference_level,
            reference_type=reference_type,
            reject_reason="no_raw_sweep_at_h1_close",
        )
    ref = pd.Series(
        {
            "reference_id": reference_id,
            "reference_level": reference_level,
            "reference_type": reference_type,
            "direction": direction,
            "confirmed_at": pd.Timestamp(confirmed_at),
            "swing_center_timestamp": pd.Timestamp(swing_center_timestamp)
            if swing_center_timestamp
            else pd.Timestamp(confirmed_at),
        }
    )
    row = _qualified_sweep_row(bars, ref, sweep)
    _attach_failed_reclaim(row, bars, sweep, reclaim_window_h1_bars)
    return row


def _empty_explicit_row(
    *,
    reference_id: str,
    sweep_h1_close_ts: str,
    direction: str,
    reference_level: float,
    reference_type: str,
    reject_reason: str,
) -> dict[str, object]:
    row = {column: "" for column in OUTPUT_COLUMNS}
    row.update(
        {
            "reference_id": reference_id,
            "sweep_h1_close_ts": sweep_h1_close_ts,
            "sweep_direction": direction,
            "raw_sweep": "false",
            "sweep_h1_completed": "false" if reject_reason == "h1_bar_not_found_at_setup_timestamp" else "",
            "sweep_reference_level": _round(reference_level),
            "sweep_reference_type": reference_type,
            "qualified_h1_sweep": "false",
            "qualified_h1_sweep_reject_reason": reject_reason,
            "qualified_h1_failed_reclaim": "false",
            "reclaim_reject_reason": "qualified_h1_sweep_required",
            "evidence_summary": "explicit H1 evaluation; raw_sweep_observation=false; raw_sweep_alone_is_not_entry_trigger",
        }
    )
    return row
def _qualified_sweep_row(bars: pd.DataFrame, ref: pd.Series, sweep: pd.Series) -> dict[str, object]:
    direction = str(ref["direction"])
    level = float(ref["reference_level"])
    sweep_ts = pd.Timestamp(sweep["timestamp"])
    reference_ts = pd.Timestamp(ref["confirmed_at"])
    center_ts = pd.Timestamp(ref["swing_center_timestamp"]) if pd.notna(ref["swing_center_timestamp"]) else pd.NaT

    prior = bars[(bars["timestamp"] > reference_ts) & (bars["timestamp"] < sweep_ts)].copy()
    level_age = int(len(bars[(bars["timestamp"] > reference_ts) & (bars["timestamp"] <= sweep_ts)]))
    center_distance = _h1_bar_distance(center_ts, sweep_ts)
    reaction_abs = _reaction_abs(prior, direction, level)
    reaction_rel = reaction_abs / abs(level) if level else float("nan")
    atr = _atr_at(bars, sweep_ts)
    penetration_abs = _penetration_abs(sweep, direction, level)
    penetration_rel = penetration_abs / abs(level) if level else float("nan")
    penetration_threshold, penetration_reason = _penetration_threshold(level, atr)
    reaction_threshold, reaction_reason = _reaction_threshold(level, atr)
    wick_present = _wick_present(sweep, direction, level)
    body_direction = _body_direction(sweep)
    volume = float(sweep["volume"])
    median_volume = _rolling_volume_median_at(bars, sweep_ts)
    volume_ratio = volume / median_volume if median_volume and pd.notna(median_volume) else float("nan")

    reject_reasons = []
    if not bool(sweep["completed"]):
        reject_reasons.append("h1_bar_incomplete")
    if str(ref["reference_type"]) not in MEANINGFUL_REFERENCE_TYPES:
        reject_reasons.append("reference_type_not_meaningful")
    if level_age < MIN_LEVEL_AGE_H1_BARS and (
        pd.isna(center_distance) or center_distance < MIN_SWING_CENTER_TO_SWEEP_H1_BARS
    ):
        reject_reasons.append("level_too_young")
    if pd.isna(atr):
        reject_reasons.append("insufficient_reaction_data")
    elif reaction_abs < reaction_threshold:
        reject_reasons.append("insufficient_prior_reaction")
    if penetration_abs < penetration_threshold:
        reject_reasons.append("insufficient_penetration")
    if not wick_present:
        reject_reasons.append("missing_sweep_wick")
    if _strongly_holds_beyond_level(sweep, direction, level):
        reject_reasons.append("close_strongly_held_beyond_level")

    qualified = not reject_reasons
    reject_reason = "|".join(reject_reasons)
    penetration_quality = (
        "INSUFFICIENT"
        if penetration_abs < penetration_threshold
        else "ATR_CONFIRMED"
        if not pd.isna(atr)
        else f"FALLBACK_REL_{penetration_reason}"
    )
    evidence = [
        "raw_sweep_observation=true",
        f"qualified_h1_sweep={str(qualified).lower()}",
        f"penetration_rule={penetration_reason}",
        f"reaction_rule={reaction_reason}",
        "raw_sweep_alone_is_not_entry_trigger",
    ]
    return {
        "reference_id": str(ref["reference_id"]),
        "sweep_h1_close_ts": _format_ts(sweep_ts),
        "sweep_direction": direction,
        "raw_sweep": "true",
        "sweep_h1_completed": str(bool(sweep["completed"])).lower(),
        "sweep_reference_level": _round(level),
        "sweep_reference_type": str(ref["reference_type"]),
        "level_age_h1_bars": level_age,
        "swing_center_to_sweep_distance_h1_bars": "" if pd.isna(center_distance) else int(center_distance),
        "reaction_abs": _round(reaction_abs),
        "reaction_rel": _round(reaction_rel),
        "atr_h1_14": _round(atr),
        "penetration_abs": _round(penetration_abs),
        "penetration_rel": _round(penetration_rel),
        "penetration_quality": penetration_quality,
        "sweep_wick_present": str(wick_present).lower(),
        "sweep_body_direction": body_direction,
        "sweep_h1_total_qty": _round(volume),
        "rolling_h1_volume_median_20": _round(median_volume),
        "sweep_volume_ratio": _round(volume_ratio),
        "volume_expansion_flag": str(not pd.isna(volume_ratio) and volume_ratio >= VOLUME_EXPANSION_RATIO).lower(),
        "qualified_h1_sweep": str(qualified).lower(),
        "qualified_h1_sweep_reject_reason": reject_reason,
        "qualified_h1_failed_reclaim": "false",
        "reclaim_h1_close_ts": "",
        "reclaim_bar_number_after_sweep": "",
        "reclaim_close_price": "",
        "reclaim_direction": "",
        "entry_candidate_ts": "",
        "entry_candidate_price": "",
        "stop_candidate_price": "",
        "reclaim_reject_reason": "",
        "evidence_summary": "; ".join(evidence),
    }


def _attach_failed_reclaim(
    row: dict[str, object],
    bars: pd.DataFrame,
    sweep: pd.Series,
    reclaim_window_h1_bars: int,
) -> None:
    if row["qualified_h1_sweep"] != "true":
        row["reclaim_reject_reason"] = "qualified_h1_sweep_required"
        return

    sweep_ts = pd.Timestamp(sweep["timestamp"])
    level = float(row["sweep_reference_level"])
    direction = str(row["sweep_direction"])
    after = bars[bars["timestamp"] > sweep_ts].head(reclaim_window_h1_bars).copy()
    if after.empty:
        row["reclaim_reject_reason"] = "no_completed_h1_bar_after_sweep"
        return

    for idx, (_, bar) in enumerate(after.iterrows(), start=1):
        if not bool(bar["completed"]) or pd.Timestamp(bar["timestamp"]) != sweep_ts + pd.Timedelta(hours=idx):
            row["reclaim_reject_reason"] = "incomplete_or_missing_confirmation_bar"
            return
        close = float(bar["close"])
        if direction == "BEARISH" and close < level:
            _mark_reclaim(row, bar, idx, direction, stop_price=float(sweep["high"]) * (1 + STOP_BUFFER_FRACTION))
            return
        if direction == "BULLISH" and close > level:
            _mark_reclaim(row, bar, idx, direction, stop_price=float(sweep["low"]) * (1 - STOP_BUFFER_FRACTION))
            return
    row["reclaim_reject_reason"] = "no_close_back_through_level_within_window"


def _mark_reclaim(
    row: dict[str, object],
    bar: pd.Series,
    bar_number: int,
    direction: str,
    stop_price: float,
) -> None:
    ts = pd.Timestamp(bar["timestamp"])
    row["qualified_h1_failed_reclaim"] = "true"
    row["reclaim_h1_close_ts"] = _format_ts(ts)
    row["reclaim_bar_number_after_sweep"] = bar_number
    row["reclaim_close_price"] = _round(float(bar["close"]))
    row["reclaim_direction"] = direction
    row["entry_candidate_ts"] = _format_ts(ts)
    row["entry_candidate_price"] = _round(float(bar["close"]))
    row["stop_candidate_price"] = _round(stop_price)
    row["reclaim_reject_reason"] = ""
    row["evidence_summary"] += "; qualified_h1_failed_reclaim=true; entry_candidate_ts=reclaim_close_ts"


def _prepare_h1_bars(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "completed"])
    columns = _lower_columns(frame)
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[columns["timestamp"]], utc=True, errors="coerce"),
            "open": pd.to_numeric(frame[columns["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[columns["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[columns["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[columns["close"]], errors="coerce"),
            "volume": pd.to_numeric(frame[columns.get("volume", columns.get("qty", "volume"))], errors="coerce")
            if "volume" in columns or "qty" in columns
            else 0.0,
            "completed": frame[columns["completed"]].astype(str).str.lower().isin({"true", "1", "1.0"}) if "completed" in columns else True,
        }
    )
    if out["timestamp"].duplicated().any():
        raise ValueError("duplicate H1 confirmation observations")
    return out.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp", kind="mergesort")


def _prepare_reference_levels(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    columns = _lower_columns(frame)
    out = pd.DataFrame(
        {
            "reference_id": frame[columns.get("reference_id", columns.get("level_id", "reference_id"))]
            if "reference_id" in columns or "level_id" in columns
            else [f"reference_{idx + 1:06d}" for idx in range(len(frame))],
            "reference_level": pd.to_numeric(frame[columns["reference_level"]], errors="coerce"),
            "reference_type": frame[columns["reference_type"]].astype(str),
            "direction": frame[columns["direction"]].astype(str),
            "confirmed_at": pd.to_datetime(frame[columns["confirmed_at"]], utc=True, errors="coerce"),
            "swing_center_timestamp": pd.to_datetime(
                frame[columns["swing_center_timestamp"]], utc=True, errors="coerce"
            )
            if "swing_center_timestamp" in columns
            else pd.NaT,
        }
    )
    return out.dropna(subset=["reference_level", "confirmed_at"]).copy()


def _first_raw_sweep(bars: pd.DataFrame, ref: pd.Series) -> pd.Series | None:
    level = float(ref["reference_level"])
    confirmed_at = pd.Timestamp(ref["confirmed_at"])
    frame = bars[(bars["timestamp"] > confirmed_at) & bars["completed"]].copy()
    if frame.empty:
        return None
    direction = str(ref["direction"])
    if direction == "BEARISH":
        hits = frame[frame["high"] > level]
    elif direction == "BULLISH":
        hits = frame[frame["low"] < level]
    else:
        raise ValueError("reference direction must be BEARISH or BULLISH")
    if hits.empty:
        return None
    return hits.iloc[0]


def _reaction_abs(prior: pd.DataFrame, direction: str, level: float) -> float:
    if prior.empty:
        return 0.0
    if direction == "BEARISH":
        return max(0.0, level - float(prior["low"].min()))
    return max(0.0, float(prior["high"].max()) - level)


def _penetration_abs(sweep: pd.Series, direction: str, level: float) -> float:
    if direction == "BEARISH":
        return max(0.0, float(sweep["high"]) - level)
    return max(0.0, level - float(sweep["low"]))


def _atr_at(bars: pd.DataFrame, timestamp: pd.Timestamp, period: int = 14) -> float:
    frame = bars[bars["timestamp"] <= timestamp].copy()
    if len(frame) < period + 1:
        return float("nan")
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    value = true_range.rolling(period).mean().iloc[-1]
    return float(value) if pd.notna(value) else float("nan")


def _reaction_threshold(level: float, atr: float) -> tuple[float, str]:
    if pd.isna(atr):
        return max(REACTION_LEVEL_FRACTION * level, float("inf")), "ATR_UNAVAILABLE"
    return max(REACTION_LEVEL_FRACTION * level, REACTION_ATR_FRACTION * atr), "ATR_CONFIRMED"


def _penetration_threshold(level: float, atr: float) -> tuple[float, str]:
    if pd.isna(atr):
        return PENETRATION_LEVEL_FRACTION * level, "ATR_UNAVAILABLE_REL_FALLBACK"
    return max(PENETRATION_LEVEL_FRACTION * level, PENETRATION_ATR_FRACTION * atr), "ATR_CONFIRMED"


def _wick_present(sweep: pd.Series, direction: str, level: float) -> bool:
    open_price = float(sweep["open"])
    close_price = float(sweep["close"])
    if direction == "BEARISH":
        body_top = max(open_price, close_price)
        return float(sweep["high"]) > max(level, body_top)
    body_bottom = min(open_price, close_price)
    return float(sweep["low"]) < min(level, body_bottom)


def _body_direction(sweep: pd.Series) -> str:
    open_price = float(sweep["open"])
    close_price = float(sweep["close"])
    if close_price < open_price:
        return "BEARISH"
    if close_price > open_price:
        return "BULLISH"
    return "DOJI"


def _strongly_holds_beyond_level(sweep: pd.Series, direction: str, level: float) -> bool:
    if direction == "BEARISH":
        return float(sweep["close"]) > level
    return float(sweep["close"]) < level


def _rolling_volume_median_at(bars: pd.DataFrame, timestamp: pd.Timestamp, period: int = 20) -> float:
    frame = bars[bars["timestamp"] <= timestamp]
    if frame.empty:
        return float("nan")
    value = frame["volume"].rolling(period, min_periods=1).median().iloc[-1]
    return float(value) if pd.notna(value) else float("nan")


def _h1_bar_distance(start: pd.Timestamp, end: pd.Timestamp) -> float:
    if pd.isna(start) or pd.isna(end):
        return float("nan")
    return float((end - start).total_seconds() / 3600.0)


def _lower_columns(frame: pd.DataFrame) -> dict[str, str]:
    return {str(column).lower(): column for column in frame.columns}


def _format_ts(value: object) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.isoformat().replace("+00:00", "Z")


def _round(value: object) -> object:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(number):
        return ""
    return round(number, 6)
