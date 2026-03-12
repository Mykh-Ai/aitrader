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


def _minute_df(highs: list[float], lows: list[float], start: str = "2025-01-01") -> pd.DataFrame:
    ts = pd.date_range(start=start, periods=len(highs), freq="1min", tz="UTC")
    return pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})


def test_incomplete_h1_bucket_is_excluded_from_swing_structure():
    chunks: list[pd.DataFrame] = []
    # Bucket 00:00 complete (60 rows), high 100
    chunks.append(_minute_df(highs=[100.0] * 60, lows=[10.0] * 60, start="2025-01-01T00:00:00Z"))
    # Bucket 01:00 incomplete (44 rows < 45), would be a swing center if included
    chunks.append(_minute_df(highs=[200.0] * 44, lows=[20.0] * 44, start="2025-01-01T01:00:00Z"))
    # Bucket 02:00 complete (60 rows), high 90
    chunks.append(_minute_df(highs=[90.0] * 60, lows=[10.0] * 60, start="2025-01-01T02:00:00Z"))
    # Bucket 03:00 complete to allow confirmation row to exist
    chunks.append(_minute_df(highs=[80.0] * 60, lows=[10.0] * 60, start="2025-01-01T03:00:00Z"))

    out = annotate_swings(pd.concat(chunks, ignore_index=True))

    assert pd.isna(out["SwingHigh_H1_Price"]).all()
    assert pd.isna(out["SwingHigh_H1_ConfirmedAt"]).all()


def test_incomplete_h4_bucket_is_excluded_from_swing_structure():
    chunks: list[pd.DataFrame] = []
    # 00:00-03:59 complete 4H bucket (240 rows), high 100
    chunks.append(_minute_df(highs=[100.0] * 240, lows=[10.0] * 240, start="2025-01-01T00:00:00Z"))
    # 04:00-07:59 incomplete 4H bucket (179 rows < 180), would be swing center if included
    chunks.append(_minute_df(highs=[200.0] * 179, lows=[20.0] * 179, start="2025-01-01T04:00:00Z"))
    # 08:00-11:59 complete 4H bucket (240 rows), high 90
    chunks.append(_minute_df(highs=[90.0] * 240, lows=[10.0] * 240, start="2025-01-01T08:00:00Z"))
    # 12:00-15:59 complete bucket to carry confirmation region
    chunks.append(_minute_df(highs=[80.0] * 240, lows=[10.0] * 240, start="2025-01-01T12:00:00Z"))

    out = annotate_swings(pd.concat(chunks, ignore_index=True))

    assert pd.isna(out["SwingHigh_H4_Price"]).all()
    assert pd.isna(out["SwingHigh_H4_ConfirmedAt"]).all()


def test_dense_real_minute_data_still_confirms_expected_h1_swing():
    chunks: list[pd.DataFrame] = []
    chunks.append(_minute_df(highs=[100.0] * 60, lows=[10.0] * 60, start="2025-01-01T00:00:00Z"))
    chunks.append(_minute_df(highs=[120.0] * 60, lows=[10.0] * 60, start="2025-01-01T01:00:00Z"))
    chunks.append(_minute_df(highs=[90.0] * 60, lows=[10.0] * 60, start="2025-01-01T02:00:00Z"))
    chunks.append(_minute_df(highs=[80.0] * 60, lows=[10.0] * 60, start="2025-01-01T03:00:00Z"))

    out = annotate_swings(pd.concat(chunks, ignore_index=True))

    confirm_ts = pd.Timestamp("2025-01-01T03:00:00Z")
    row = out.loc[out["Timestamp"] == confirm_ts].iloc[0]
    assert row["SwingHigh_H1_Price"] == 120.0
    assert row["SwingHigh_H1_ConfirmedAt"] == confirm_ts


def test_synthetic_bar_cannot_be_swing_center_for_structure():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=5, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "High": [10.0, 20.0, 11.0, 10.0, 9.0],
            "Low": [5.0, 6.0, 6.0, 5.0, 5.0],
            "IsSynthetic": [0, 1, 0, 0, 0],
        }
    )

    out = annotate_swings(df)

    synthetic_confirm_ts = pd.Timestamp("2025-01-01T03:00:00Z")
    synthetic_confirm_row = out.loc[out["Timestamp"] == synthetic_confirm_ts].iloc[0]
    assert pd.isna(synthetic_confirm_row["SwingHigh_H1_Price"])
    assert pd.isna(synthetic_confirm_row["SwingHigh_H1_ConfirmedAt"])
    assert not (out["SwingHigh_H1_Price"] == 20.0).any()


def test_confirmed_swing_first_materializes_on_first_real_row_when_confirm_ts_is_synthetic():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=6, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "High": [10.0, 14.0, 11.0, 13.0, 15.0, 12.0],
            "Low": [5.0, 6.0, 6.0, 6.0, 7.0, 6.0],
            "IsSynthetic": [0, 0, 0, 1, 1, 0],
        }
    )

    out = annotate_swings(df)

    confirm_ts = pd.Timestamp("2025-01-01T03:00:00Z")
    first_real_anchor_ts = pd.Timestamp("2025-01-01T05:00:00Z")

    at_confirm = out.loc[out["Timestamp"] == confirm_ts].iloc[0]
    assert pd.isna(at_confirm["SwingHigh_H1_Price"])
    assert pd.isna(at_confirm["SwingHigh_H1_ConfirmedAt"])

    at_first_real = out.loc[out["Timestamp"] == first_real_anchor_ts].iloc[0]
    assert at_first_real["SwingHigh_H1_Price"] == 14.0
    assert at_first_real["SwingHigh_H1_ConfirmedAt"] == confirm_ts
