from __future__ import annotations

import pandas as pd

from analyzer.failed_breaks import FAILED_BREAK_FEATURE_COLUMNS, detect_failed_breaks


def _empty_sweeps_df(periods: int = 6) -> pd.DataFrame:
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=periods, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "High": [10.0] * periods,
            "Low": [9.0] * periods,
            "Close": [9.5] * periods,
        }
    )

    for tf in ("H1", "H4"):
        df[f"Sweep_{tf}_Up"] = False
        df[f"Sweep_{tf}_Down"] = False
        df[f"Sweep_{tf}_Direction"] = pd.Series(pd.NA, index=df.index, dtype="object")
        df[f"Sweep_{tf}_ReferenceLevel"] = pd.Series(pd.NA, index=df.index, dtype="Float64")
        df[f"Sweep_{tf}_ReferenceTs"] = pd.Series(pd.NaT, index=df.index, dtype="object")

    return df


def test_upward_sweep_then_close_below_confirms_failed_up_break():
    df = _empty_sweeps_df(5)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]

    df.loc[1, "Close"] = 101.0
    df.loc[2, "Close"] = 100.5
    df.loc[3, "Close"] = 99.0

    out = detect_failed_breaks(df)

    assert not out.loc[1, "FailedBreak_H1_Up"]
    assert not out.loc[2, "FailedBreak_H1_Up"]
    assert out.loc[3, "FailedBreak_H1_Up"]
    assert out.loc[3, "FailedBreak_H1_Direction"] == "up"
    assert out.loc[3, "FailedBreak_H1_ReferenceLevel"] == 100.0
    assert out.loc[3, "FailedBreak_H1_ReferenceSweepTs"] == df.loc[1, "Timestamp"]
    assert out.loc[3, "FailedBreak_H1_ConfirmedTs"] == df.loc[3, "Timestamp"]


def test_downward_sweep_then_close_above_confirms_failed_down_break():
    df = _empty_sweeps_df(5)
    df.loc[1, "Sweep_H1_Down"] = True
    df.loc[1, "Sweep_H1_Direction"] = "down"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 90.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]

    df.loc[1, "Close"] = 89.0
    df.loc[2, "Close"] = 89.5
    df.loc[3, "Close"] = 91.0

    out = detect_failed_breaks(df)

    assert not out.loc[1, "FailedBreak_H1_Down"]
    assert not out.loc[2, "FailedBreak_H1_Down"]
    assert out.loc[3, "FailedBreak_H1_Down"]
    assert out.loc[3, "FailedBreak_H1_Direction"] == "down"
    assert out.loc[3, "FailedBreak_H1_ReferenceLevel"] == 90.0
    assert out.loc[3, "FailedBreak_H1_ReferenceSweepTs"] == df.loc[1, "Timestamp"]
    assert out.loc[3, "FailedBreak_H1_ConfirmedTs"] == df.loc[3, "Timestamp"]


def test_no_failed_break_before_any_sweep_exists():
    df = _empty_sweeps_df(6)
    df["Close"] = [99, 98, 97, 96, 101, 102]

    out = detect_failed_breaks(df)

    assert not out["FailedBreak_H1_Up"].any()
    assert not out["FailedBreak_H1_Down"].any()


def test_no_failed_break_when_continuation_persists_without_reclaim():
    df = _empty_sweeps_df(6)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 102.0, 103.0, 104.0, 105.0]

    out = detect_failed_breaks(df)

    assert not out["FailedBreak_H1_Up"].any()
    assert not out["FailedBreak_H1_Down"].any()


def test_no_lookahead_leakage_prefix_result_is_stable():
    df = _empty_sweeps_df(6)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 102.0, 100.2, 99.8, 99.7]

    out_full = detect_failed_breaks(df)
    out_prefix = detect_failed_breaks(df.iloc[:4].copy())

    compare_cols = [
        "FailedBreak_H1_Up",
        "FailedBreak_H1_Down",
        "FailedBreak_H1_Direction",
        "FailedBreak_H1_ReferenceLevel",
        "FailedBreak_H1_ReferenceSweepTs",
        "FailedBreak_H1_ConfirmedTs",
    ]
    for col in compare_cols:
        assert out_full.loc[:3, col].reset_index(drop=True).equals(out_prefix[col].reset_index(drop=True))


def test_h1_h4_failed_break_plumbing_are_independent():
    df = _empty_sweeps_df(6)

    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]

    df.loc[2, "Sweep_H4_Down"] = True
    df.loc[2, "Sweep_H4_Direction"] = "down"
    df.loc[2, "Sweep_H4_ReferenceLevel"] = 90.0
    df.loc[2, "Sweep_H4_ReferenceTs"] = df.loc[2, "Timestamp"]

    df["Close"] = [99.0, 101.0, 95.0, 99.0, 91.0, 91.5]

    out = detect_failed_breaks(df)

    assert out.loc[2, "FailedBreak_H1_Up"]
    assert not out.loc[2, "FailedBreak_H4_Down"]
    assert out.loc[3, "FailedBreak_H4_Down"]
    assert not out.loc[3, "FailedBreak_H1_Up"]

    for col in FAILED_BREAK_FEATURE_COLUMNS:
        assert col in out.columns


def test_synthetic_row_cannot_confirm_failed_break():
    df = _empty_sweeps_df(5)
    df["IsSynthetic"] = [0, 0, 1, 0, 0]
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 99.0, 99.0, 99.0]

    out = detect_failed_breaks(df)

    assert not out.loc[2, "FailedBreak_H1_Up"]
    assert out.loc[3, "FailedBreak_H1_Up"]


def test_failed_break_pending_state_resets_after_large_timestamp_gap():
    df = _empty_sweeps_df(5)
    df["Timestamp"] = pd.to_datetime(
        [
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:01:00Z",
            "2025-01-01T00:02:00Z",
            "2025-01-01T00:10:00Z",
            "2025-01-01T00:11:00Z",
        ],
        utc=True,
    )

    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 101.0, 99.0, 98.0]

    out = detect_failed_breaks(df)

    assert not out["FailedBreak_H1_Up"].any()


def test_failed_break_confirmation_must_happen_inside_timeout_window():
    df = _empty_sweeps_df(7)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 102.0, 102.0, 102.0, 102.0, 99.0]

    out = detect_failed_breaks(df, confirmation_bars=3)

    assert not out["FailedBreak_H1_Up"].any()


def test_failed_break_can_still_confirm_on_last_in_window_bar():
    df = _empty_sweeps_df(6)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = [99.0, 101.0, 102.0, 102.0, 99.0, 98.0]

    out = detect_failed_breaks(df, confirmation_bars=3)

    assert out.loc[4, "FailedBreak_H1_Up"]
    assert not out.loc[5, "FailedBreak_H1_Up"]


def test_failed_break_extended_confirmation_can_confirm_on_sixtieth_bar():
    df = _empty_sweeps_df(62)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = 101.0
    df.loc[61, "Close"] = 99.0

    out = detect_failed_breaks(df, confirmation_bars=60)

    assert out.loc[61, "FailedBreak_H1_Up"]
    assert out["FailedBreak_H1_Up"].sum() == 1


def test_failed_break_extended_confirmation_expires_after_sixtieth_bar():
    df = _empty_sweeps_df(63)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]
    df["Close"] = 101.0
    df.loc[62, "Close"] = 99.0

    out = detect_failed_breaks(df, confirmation_bars=60)

    assert not out["FailedBreak_H1_Up"].any()


def test_new_sweep_after_timeout_can_create_fresh_failed_break_opportunity():
    df = _empty_sweeps_df(8)
    df.loc[1, "Sweep_H1_Up"] = True
    df.loc[1, "Sweep_H1_Direction"] = "up"
    df.loc[1, "Sweep_H1_ReferenceLevel"] = 100.0
    df.loc[1, "Sweep_H1_ReferenceTs"] = df.loc[1, "Timestamp"]

    df.loc[6, "Sweep_H1_Up"] = True
    df.loc[6, "Sweep_H1_Direction"] = "up"
    df.loc[6, "Sweep_H1_ReferenceLevel"] = 110.0
    df.loc[6, "Sweep_H1_ReferenceTs"] = df.loc[6, "Timestamp"]

    df["Close"] = [99.0, 101.0, 102.0, 102.0, 102.0, 102.0, 111.0, 109.0]

    out = detect_failed_breaks(df, confirmation_bars=3)

    assert out["FailedBreak_H1_Up"].sum() == 1
    assert out.loc[7, "FailedBreak_H1_Up"]
    assert out.loc[7, "FailedBreak_H1_ReferenceLevel"] == 110.0


def test_confirmation_bars_must_be_positive():
    df = _empty_sweeps_df(3)

    try:
        detect_failed_breaks(df, confirmation_bars=0)
    except ValueError as exc:
        assert "confirmation_bars" in str(exc)
    else:
        raise AssertionError("Expected ValueError for confirmation_bars=0")
