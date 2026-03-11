from __future__ import annotations

from pathlib import Path

import pandas as pd

from analyzer.loader import load_raw_csv
from analyzer.swings import SWING_FEATURE_COLUMNS, annotate_swings


def _hourly_df(highs: list[float], lows: list[float], start: str = "2025-01-01") -> pd.DataFrame:
    ts = pd.date_range(start=start, periods=len(highs), freq="1h", tz="UTC")
    return pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})


def test_confirmed_h1_swing_high_delayed_marking():
    df = _hourly_df(highs=[10, 14, 11, 10, 9], lows=[5, 6, 6, 5, 5])

    out = annotate_swings(df)

    confirm_ts = pd.Timestamp("2025-01-01T03:00:00Z")
    assert pd.isna(out.loc[out["Timestamp"] < confirm_ts, "SwingHigh_H1_Price"]).all()
    row = out.loc[out["Timestamp"] == confirm_ts].iloc[0]
    assert row["SwingHigh_H1_Price"] == 14
    assert row["SwingHigh_H1_ConfirmedAt"] == confirm_ts


def test_confirmed_h1_swing_low_delayed_marking():
    df = _hourly_df(highs=[10, 11, 11, 10, 10], lows=[7, 4, 6, 7, 7])

    out = annotate_swings(df)

    confirm_ts = pd.Timestamp("2025-01-01T03:00:00Z")
    assert pd.isna(out.loc[out["Timestamp"] < confirm_ts, "SwingLow_H1_Price"]).all()
    row = out.loc[out["Timestamp"] == confirm_ts].iloc[0]
    assert row["SwingLow_H1_Price"] == 4
    assert row["SwingLow_H1_ConfirmedAt"] == confirm_ts


def test_flat_ambiguous_structure_does_not_create_swing():
    df = _hourly_df(highs=[10, 12, 12, 11], lows=[5, 5, 6, 6])

    out = annotate_swings(df)

    assert pd.isna(out["SwingHigh_H1_Price"]).all()
    assert pd.isna(out["SwingLow_H1_Price"]).all()


def test_synthetic_rows_fixture_stays_stable_and_outputs_columns():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_with_synthetic.csv")

    out = annotate_swings(df)

    assert len(out) == len(df)
    for col in SWING_FEATURE_COLUMNS:
        assert col in out.columns


def test_h1_h4_plumbing_and_delayed_confirmation():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=16, freq="1h", tz="UTC")
    # 4H bar highs become: [10, 20, 15, 14] -> H4 swing high at 04:00 confirmed at 12:00.
    highs = [8, 10, 9, 7, 16, 20, 18, 17, 14, 15, 13, 12, 13, 14, 12, 11]
    lows = [5, 6, 5, 4, 8, 9, 8, 7, 6, 7, 6, 5, 6, 7, 6, 5]
    df = pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})

    out = annotate_swings(df)

    h4_confirm_ts = pd.Timestamp("2025-01-01T12:00:00Z")
    assert pd.isna(out.loc[out["Timestamp"] < h4_confirm_ts, "SwingHigh_H4_Price"]).all()

    row = out.loc[out["Timestamp"] == h4_confirm_ts].iloc[0]
    assert row["SwingHigh_H4_Price"] == 20
    assert row["SwingHigh_H4_ConfirmedAt"] == h4_confirm_ts

    assert out["SwingHigh_H1_ConfirmedAt"].notna().any()
