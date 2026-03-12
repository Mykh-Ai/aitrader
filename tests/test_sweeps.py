from __future__ import annotations

import pandas as pd

from analyzer.sweeps import SWEEP_FEATURE_COLUMNS, detect_sweeps
from analyzer.swings import annotate_swings


def _hourly_df(highs: list[float], lows: list[float], start: str = "2025-01-01") -> pd.DataFrame:
    ts = pd.date_range(start=start, periods=len(highs), freq="1h", tz="UTC")
    return pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})


def test_upward_sweep_over_confirmed_h1_swing_high():
    # H1 swing high at 01:00 (14) is confirmed at 03:00; only then sweeps can trigger.
    df = _hourly_df(highs=[10, 14, 11, 13, 15], lows=[5, 6, 6, 6, 7])

    out = detect_sweeps(annotate_swings(df))

    assert not out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T03:00:00Z"), "Sweep_H1_Up"].iloc[0]
    row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T04:00:00Z")].iloc[0]
    assert row["Sweep_H1_Up"]
    assert not row["Sweep_H1_Down"]
    assert row["Sweep_H1_Direction"] == "up"
    assert row["Sweep_H1_ReferenceLevel"] == 14
    assert row["Sweep_H1_ReferenceTs"] == pd.Timestamp("2025-01-01T03:00:00Z")


def test_downward_sweep_below_confirmed_h1_swing_low():
    # H1 swing low at 01:00 (4) is confirmed at 03:00; downward sweep at 04:00.
    df = _hourly_df(highs=[9, 10, 11, 10, 9], lows=[7, 4, 6, 5, 3])

    out = detect_sweeps(annotate_swings(df))

    row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T04:00:00Z")].iloc[0]
    assert row["Sweep_H1_Down"]
    assert not row["Sweep_H1_Up"]
    assert row["Sweep_H1_Direction"] == "down"
    assert row["Sweep_H1_ReferenceLevel"] == 4
    assert row["Sweep_H1_ReferenceTs"] == pd.Timestamp("2025-01-01T03:00:00Z")


def test_no_sweep_before_confirmation_exists():
    # Bar at 02:00 trades above eventual swing high (14), but confirmation appears only at 03:00.
    df = _hourly_df(highs=[10, 14, 15, 10], lows=[5, 6, 7, 6])

    out = detect_sweeps(annotate_swings(df))

    row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T02:00:00Z")].iloc[0]
    assert pd.isna(row["SwingHigh_H1_Price"])
    assert not row["Sweep_H1_Up"]


def test_equal_touch_is_not_sweep_with_strict_rule():
    # Strict inequality: equal touch to level should not count as sweep.
    df = _hourly_df(highs=[10, 14, 11, 14], lows=[5, 6, 6, 6])

    out = detect_sweeps(annotate_swings(df))

    row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T03:00:00Z")].iloc[0]
    assert row["SwingHigh_H1_Price"] == 14
    assert not row["Sweep_H1_Up"]


def test_synthetic_rows_fixture_stable_and_explicit_columns():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=5, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "High": [10, 14, 11, 13, 15],
            "Low": [5, 6, 6, 6, 7],
            "IsSynthetic": [False, False, True, False, False],
        }
    )

    out = detect_sweeps(annotate_swings(df))

    assert len(out) == len(df)
    for col in SWEEP_FEATURE_COLUMNS:
        assert col in out.columns


def test_h1_h4_plumbing_sweeps_work_independently():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=16, freq="1h", tz="UTC")
    # 4H highs per bar: [10, 20, 15, 14] -> H4 swing-high=20 confirmed at 12:00.
    highs = [8, 10, 9, 7, 16, 20, 18, 17, 14, 15, 13, 12, 13, 21, 12, 11]
    lows = [5, 6, 5, 4, 8, 9, 8, 7, 6, 7, 6, 5, 6, 7, 6, 5]
    df = pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})

    out = detect_sweeps(annotate_swings(df))

    pre_h4_confirm = out.loc[out["Timestamp"] < pd.Timestamp("2025-01-01T12:00:00Z")]
    assert not pre_h4_confirm["Sweep_H4_Up"].any()

    h4_sweep_row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T13:00:00Z")].iloc[0]
    assert h4_sweep_row["Sweep_H4_Up"]
    assert h4_sweep_row["Sweep_H4_Direction"] == "up"
    assert h4_sweep_row["Sweep_H4_ReferenceLevel"] == 20
    assert h4_sweep_row["Sweep_H4_ReferenceTs"] == pd.Timestamp("2025-01-01T12:00:00Z")

    assert out["Sweep_H1_Up"].dtype == bool
    assert out["Sweep_H4_Down"].dtype == bool


def test_sweep_flags_are_mutually_exclusive_per_timeframe():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=16, freq="1h", tz="UTC")
    highs = [8, 10, 9, 7, 16, 20, 18, 17, 14, 15, 13, 12, 13, 21, 12, 11]
    lows = [5, 6, 5, 4, 8, 9, 8, 7, 6, 7, 6, 5, 6, 7, 6, 5]
    df = pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})

    out = detect_sweeps(annotate_swings(df))

    for tf_label in ("H1", "H4"):
        both = out[f"Sweep_{tf_label}_Up"] & out[f"Sweep_{tf_label}_Down"]
        assert not both.any(), f"{tf_label} has rows with both up and down sweeps"


def test_sweep_fields_remain_consistent_with_flags_and_references():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=16, freq="1h", tz="UTC")
    highs = [8, 10, 9, 7, 16, 20, 18, 17, 14, 15, 13, 12, 13, 21, 12, 11]
    lows = [5, 6, 5, 4, 8, 9, 8, 7, 6, 7, 6, 5, 6, 7, 6, 5]
    df = pd.DataFrame({"Timestamp": ts, "High": highs, "Low": lows})

    out = detect_sweeps(annotate_swings(df))

    for tf_label in ("H1", "H4"):
        up_col = f"Sweep_{tf_label}_Up"
        down_col = f"Sweep_{tf_label}_Down"
        direction_col = f"Sweep_{tf_label}_Direction"
        ref_level_col = f"Sweep_{tf_label}_ReferenceLevel"
        ref_ts_col = f"Sweep_{tf_label}_ReferenceTs"
        high_level_col = f"SwingHigh_{tf_label}_Price"
        low_level_col = f"SwingLow_{tf_label}_Price"
        high_ts_col = f"SwingHigh_{tf_label}_ConfirmedAt"
        low_ts_col = f"SwingLow_{tf_label}_ConfirmedAt"

        for _, row in out.iterrows():
            if row[up_col]:
                assert not row[down_col]
                assert row[direction_col] == "up"
                assert row[ref_level_col] == row[high_level_col]
                assert row[ref_ts_col] == row[high_ts_col]
            elif row[down_col]:
                assert not row[up_col]
                assert row[direction_col] == "down"
                assert row[ref_level_col] == row[low_level_col]
                assert row[ref_ts_col] == row[low_ts_col]
            else:
                assert pd.isna(row[direction_col])
                assert pd.isna(row[ref_level_col])
                assert pd.isna(row[ref_ts_col])


def test_synthetic_row_cannot_trigger_sweep_even_if_price_crosses_level():
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=5, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "High": [10.0, 14.0, 11.0, 16.0, 15.0],
            "Low": [5.0, 6.0, 6.0, 6.0, 7.0],
            "IsSynthetic": [0, 0, 0, 1, 0],
        }
    )

    out = detect_sweeps(annotate_swings(df))

    synth_row = out.loc[out["Timestamp"] == pd.Timestamp("2025-01-01T03:00:00Z")].iloc[0]
    assert not synth_row["Sweep_H1_Up"]
    assert not synth_row["Sweep_H1_Down"]
    assert pd.isna(synth_row["Sweep_H1_Direction"])
    assert pd.isna(synth_row["Sweep_H1_ReferenceLevel"])
    assert pd.isna(synth_row["Sweep_H1_ReferenceTs"])
