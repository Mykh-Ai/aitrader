"""Structural swing detection with delayed confirmation (Phase 1B)."""

from __future__ import annotations

import pandas as pd
from pandas.tseries.frequencies import to_offset

SWING_FEATURE_COLUMNS = [
    "SwingHigh_H1_Price",
    "SwingHigh_H1_ConfirmedAt",
    "SwingLow_H1_Price",
    "SwingLow_H1_ConfirmedAt",
    "SwingHigh_H4_Price",
    "SwingHigh_H4_ConfirmedAt",
    "SwingLow_H4_Price",
    "SwingLow_H4_ConfirmedAt",
]

MIN_REAL_BARS_H1 = 45
MIN_REAL_BARS_H4 = 180


def _infer_base_seconds(df: pd.DataFrame) -> float | None:
    ts = pd.Series(pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")).dropna()
    if len(ts) < 2:
        return None
    deltas = ts.sort_values().diff().dropna().dt.total_seconds()
    if deltas.empty:
        return None
    positive = deltas[deltas > 0]
    if positive.empty:
        return None
    return float(positive.median())


def _min_real_rows_for_freq(freq: str, base_seconds: float | None) -> int:
    if base_seconds is None:
        return 0

    tf_seconds = float(to_offset(freq).nanos / 1_000_000_000)
    if base_seconds > 60:
        return 0

    expected_rows = tf_seconds / base_seconds
    min_rows_by_freq = {"1h": MIN_REAL_BARS_H1, "4h": MIN_REAL_BARS_H4}
    configured_for_1m = min_rows_by_freq[freq]
    completeness_ratio = configured_for_1m / (tf_seconds / 60.0)
    return int(max(1, expected_rows * completeness_ratio))


def _build_tf_bars(df: pd.DataFrame, freq: str, min_real_rows: int = 0) -> pd.DataFrame:
    bars = (
        df.set_index("Timestamp")
        .resample(freq, label="left", closed="left")
        .agg(High=("High", "max"), Low=("Low", "min"), RealRows=("High", "count"))
        .dropna(subset=["High", "Low"])
        .reset_index()
    )
    eligible = bars["RealRows"] >= min_real_rows
    return bars.loc[eligible, ["Timestamp", "High", "Low", "RealRows"]].reset_index(drop=True)


def _confirmed_swings(bars: pd.DataFrame, swing_kind: str, freq: str) -> pd.DataFrame:
    if len(bars) < 3:
        return pd.DataFrame(columns=["ConfirmedAt", "Price"])

    if swing_kind == "high":
        is_swing = (bars["High"] > bars["High"].shift(1)) & (
            bars["High"] > bars["High"].shift(-1)
        )
        price = bars["High"]
    else:
        is_swing = (bars["Low"] < bars["Low"].shift(1)) & (
            bars["Low"] < bars["Low"].shift(-1)
        )
        price = bars["Low"]

    center_idx = bars.index[is_swing.fillna(False)]
    center_idx = center_idx[(center_idx > 0) & (center_idx < len(bars) - 1)]
    if len(center_idx) == 0:
        return pd.DataFrame(columns=["ConfirmedAt", "Price"])

    tf_offset = to_offset(freq)
    confirmed = pd.DataFrame(
        {
            "ConfirmedAt": (bars.loc[center_idx, "Timestamp"] + (2 * tf_offset)).to_numpy(),
            "Price": price.loc[center_idx].to_numpy(),
        }
    )
    return confirmed.sort_values("ConfirmedAt", kind="mergesort").reset_index(drop=True)


def _attach_latest_confirmed(
    df: pd.DataFrame, confirmed: pd.DataFrame, price_col: str, confirmed_col: str
) -> pd.DataFrame:
    out = df.copy()
    if confirmed.empty:
        out[price_col] = pd.NA
        out[confirmed_col] = pd.NaT
        return out

    joined = pd.merge_asof(
        out[["Timestamp"]],
        confirmed,
        left_on="Timestamp",
        right_on="ConfirmedAt",
        direction="backward",
    )
    out[price_col] = joined["Price"]
    out[confirmed_col] = joined["ConfirmedAt"]
    return out


def annotate_swings(df: pd.DataFrame) -> pd.DataFrame:
    """Annotate rows with latest confirmed H1/H4 structural swings.

    Swing definition: strict 3-bar local extremum on timeframe bars.
    - Swing high at bar i: High[i] > High[i-1] and High[i] > High[i+1]
    - Swing low  at bar i: Low[i] < Low[i-1] and Low[i] < Low[i+1]

    Delayed confirmation: a swing at i becomes known only after bar i+1 fully closes,
    therefore confirmation timestamp is timestamp of i+2 bar start.
    """
    out = df.copy()

    structure_df = out
    if "IsSynthetic" in out.columns:
        is_synth = pd.to_numeric(out["IsSynthetic"], errors="coerce").fillna(0).astype(int)
        structure_df = out.loc[is_synth == 0]

    base_seconds = _infer_base_seconds(structure_df)

    tf_specs = [("1h", "H1"), ("4h", "H4")]
    for freq, tf_label in tf_specs:
        min_real_rows = _min_real_rows_for_freq(freq, base_seconds)
        bars = _build_tf_bars(structure_df, freq, min_real_rows=min_real_rows)
        high_confirmed = _confirmed_swings(bars, "high", freq)
        low_confirmed = _confirmed_swings(bars, "low", freq)

        out = _attach_latest_confirmed(
            out,
            high_confirmed,
            price_col=f"SwingHigh_{tf_label}_Price",
            confirmed_col=f"SwingHigh_{tf_label}_ConfirmedAt",
        )
        out = _attach_latest_confirmed(
            out,
            low_confirmed,
            price_col=f"SwingLow_{tf_label}_Price",
            confirmed_col=f"SwingLow_{tf_label}_ConfirmedAt",
        )

    return out
