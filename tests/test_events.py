from __future__ import annotations

import pandas as pd

from analyzer.events import build_events
from analyzer.schema import EVENT_COLUMNS


def _base_df(periods: int = 6) -> pd.DataFrame:
    ts = pd.date_range("2025-01-01T00:00:00Z", periods=periods, freq="1h", tz="UTC")
    return pd.DataFrame({"Timestamp": ts})


def test_swing_event_emitted_once_on_confirmation_not_repeated_by_persistence():
    df = _base_df(6)
    # Swing high persists after confirmation on rows 3,4,5; event must be emitted once.
    df["SwingHigh_H1_Price"] = [pd.NA, pd.NA, pd.NA, 14.0, 14.0, 14.0]
    df["SwingHigh_H1_ConfirmedAt"] = [pd.NaT, pd.NaT, pd.NaT, df.loc[3, "Timestamp"], df.loc[3, "Timestamp"], df.loc[3, "Timestamp"]]
    df["SwingLow_H1_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingLow_H1_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    df["SwingHigh_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingHigh_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    df["SwingLow_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingLow_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")

    events = build_events(df)

    swing_high = events[events["EventType"] == "SWING_HIGH"]
    assert len(swing_high) == 1
    row = swing_high.iloc[0]
    assert row["Timestamp"] == df.loc[3, "Timestamp"]
    assert row["SourceTF"] == "H1"
    assert row["Side"] == "up"
    assert row["PriceLevel"] == 14.0
    assert row["ReferenceSwingTs"] == df.loc[3, "Timestamp"]


def test_sweep_event_emitted_with_correct_mapping_fields():
    df = _base_df(4)
    df["Sweep_H4_Up"] = [False, True, False, False]
    df["Sweep_H4_Down"] = [False, False, False, False]
    df["Sweep_H4_ReferenceLevel"] = [pd.NA, 123.5, pd.NA, pd.NA]
    df["Sweep_H4_ReferenceTs"] = [pd.NaT, df.loc[0, "Timestamp"], pd.NaT, pd.NaT]

    events = build_events(df)

    sweep = events[events["EventType"] == "SWEEP_UP"]
    assert len(sweep) == 1
    row = sweep.iloc[0]
    assert row["SourceTF"] == "H4"
    assert row["Timestamp"] == df.loc[1, "Timestamp"]
    assert row["ReferenceSwingTs"] == df.loc[0, "Timestamp"]
    assert row["PriceLevel"] == 123.5
    assert row["ReferenceSwingPrice"] == 123.5


def test_failed_break_event_emitted_with_confirmed_timestamp_and_references():
    df = _base_df(5)
    df["FailedBreak_H1_Up"] = [False, False, True, False, False]
    df["FailedBreak_H1_Down"] = [False, False, False, False, False]
    df["FailedBreak_H1_ReferenceLevel"] = [pd.NA, pd.NA, 100.0, pd.NA, pd.NA]
    df["FailedBreak_H1_ReferenceSweepTs"] = [pd.NaT, pd.NaT, df.loc[1, "Timestamp"], pd.NaT, pd.NaT]
    df["FailedBreak_H1_ConfirmedTs"] = [pd.NaT, pd.NaT, df.loc[3, "Timestamp"], pd.NaT, pd.NaT]

    events = build_events(df)

    fb = events[events["EventType"] == "FAILED_BREAK_UP"]
    assert len(fb) == 1
    row = fb.iloc[0]
    assert row["SourceTF"] == "H1"
    assert row["Timestamp"] == df.loc[3, "Timestamp"]
    assert row["ReferenceSwingTs"] == df.loc[1, "Timestamp"]
    assert row["PriceLevel"] == 100.0


def test_mixed_events_are_sorted_by_timestamp_then_tf_then_event_type():
    df = _base_df(6)

    df["SwingHigh_H1_Price"] = [pd.NA, pd.NA, 14.0, 14.0, 14.0, 14.0]
    df["SwingHigh_H1_ConfirmedAt"] = [pd.NaT, pd.NaT, df.loc[2, "Timestamp"], df.loc[2, "Timestamp"], df.loc[2, "Timestamp"], df.loc[2, "Timestamp"]]
    df["SwingLow_H1_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingLow_H1_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    df["SwingHigh_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingHigh_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    df["SwingLow_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    df["SwingLow_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")

    df["Sweep_H4_Down"] = [False, False, True, False, False, False]
    df["Sweep_H4_Up"] = [False, False, False, False, False, False]
    df["Sweep_H4_ReferenceLevel"] = [pd.NA, pd.NA, 90.0, pd.NA, pd.NA, pd.NA]
    df["Sweep_H4_ReferenceTs"] = [pd.NaT, pd.NaT, df.loc[1, "Timestamp"], pd.NaT, pd.NaT, pd.NaT]

    df["FailedBreak_H1_Down"] = [False, False, True, False, False, False]
    df["FailedBreak_H1_Up"] = [False, False, False, False, False, False]
    df["FailedBreak_H1_ReferenceLevel"] = [pd.NA, pd.NA, 90.0, pd.NA, pd.NA, pd.NA]
    df["FailedBreak_H1_ReferenceSweepTs"] = [pd.NaT, pd.NaT, df.loc[1, "Timestamp"], pd.NaT, pd.NaT, pd.NaT]
    df["FailedBreak_H1_ConfirmedTs"] = [pd.NaT, pd.NaT, df.loc[2, "Timestamp"], pd.NaT, pd.NaT, pd.NaT]

    events = build_events(df)

    assert events["Timestamp"].tolist() == sorted(events["Timestamp"].tolist())
    same_ts = events[events["Timestamp"] == df.loc[2, "Timestamp"]][["SourceTF", "EventType", "Side"]]
    assert same_ts.to_records(index=False).tolist() == [
        ("H1", "FAILED_BREAK_DOWN", "down"),
        ("H1", "SWING_HIGH", "up"),
        ("H4", "SWEEP_DOWN", "down"),
    ]


def test_h1_h4_normalization_works_independently_for_same_event_type():
    df = _base_df(4)
    df["Sweep_H1_Up"] = [False, True, False, False]
    df["Sweep_H1_Down"] = [False, False, False, False]
    df["Sweep_H1_ReferenceLevel"] = [pd.NA, 10.0, pd.NA, pd.NA]
    df["Sweep_H1_ReferenceTs"] = [pd.NaT, df.loc[0, "Timestamp"], pd.NaT, pd.NaT]

    df["Sweep_H4_Up"] = [False, False, True, False]
    df["Sweep_H4_Down"] = [False, False, False, False]
    df["Sweep_H4_ReferenceLevel"] = [pd.NA, pd.NA, 20.0, pd.NA]
    df["Sweep_H4_ReferenceTs"] = [pd.NaT, pd.NaT, df.loc[1, "Timestamp"], pd.NaT]

    events = build_events(df)

    sweep_up = events[events["EventType"] == "SWEEP_UP"]
    assert len(sweep_up) == 2
    assert set(sweep_up["SourceTF"].tolist()) == {"H1", "H4"}


def test_empty_or_no_event_frame_returns_empty_with_contract_columns():
    empty_df = pd.DataFrame(columns=["Timestamp"])
    empty_events = build_events(empty_df)
    assert empty_events.empty
    assert empty_events.columns.tolist() == EVENT_COLUMNS

    no_event_df = _base_df(3)
    no_event = build_events(no_event_df)
    assert no_event.empty
    assert no_event.columns.tolist() == EVENT_COLUMNS



def test_swing_anti_dup_with_non_default_index_after_sort_reset_scenario():
    base = _base_df(6)
    base["SwingHigh_H1_Price"] = [pd.NA, pd.NA, pd.NA, 15.0, 15.0, 15.0]
    base["SwingHigh_H1_ConfirmedAt"] = [
        pd.NaT,
        pd.NaT,
        pd.NaT,
        base.loc[3, "Timestamp"],
        base.loc[3, "Timestamp"],
        base.loc[3, "Timestamp"],
    ]
    base["SwingLow_H1_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    base["SwingLow_H1_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    base["SwingHigh_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    base["SwingHigh_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")
    base["SwingLow_H4_Price"] = pd.Series([pd.NA] * 6, dtype="Float64")
    base["SwingLow_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 6, dtype="object")

    # Simulate ingest pipeline style reorder+sort with non-default index retained.
    reordered = base.iloc[[2, 0, 1, 5, 4, 3]].copy()
    reordered.index = [100, 101, 102, 103, 104, 105]
    df = reordered.sort_values("Timestamp", kind="mergesort")

    events = build_events(df)
    swing_high = events[(events["EventType"] == "SWING_HIGH") & (events["SourceTF"] == "H1")]

    assert len(swing_high) == 1
    assert swing_high.iloc[0]["Timestamp"] == base.loc[3, "Timestamp"]


def test_timestamp_reference_contracts_and_metajson_nulls_for_all_event_types():
    df = _base_df(8)

    # SWING_HIGH at t2, SWING_LOW at t3
    df["SwingHigh_H1_Price"] = [pd.NA, pd.NA, 14.0, 14.0, 14.0, 14.0, 14.0, 14.0]
    df["SwingHigh_H1_ConfirmedAt"] = [
        pd.NaT,
        pd.NaT,
        df.loc[2, "Timestamp"],
        df.loc[2, "Timestamp"],
        df.loc[2, "Timestamp"],
        df.loc[2, "Timestamp"],
        df.loc[2, "Timestamp"],
        df.loc[2, "Timestamp"],
    ]
    df["SwingLow_H1_Price"] = [pd.NA, pd.NA, pd.NA, 6.0, 6.0, 6.0, 6.0, 6.0]
    df["SwingLow_H1_ConfirmedAt"] = [
        pd.NaT,
        pd.NaT,
        pd.NaT,
        df.loc[3, "Timestamp"],
        df.loc[3, "Timestamp"],
        df.loc[3, "Timestamp"],
        df.loc[3, "Timestamp"],
        df.loc[3, "Timestamp"],
    ]
    df["SwingHigh_H4_Price"] = pd.Series([pd.NA] * 8, dtype="Float64")
    df["SwingHigh_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 8, dtype="object")
    df["SwingLow_H4_Price"] = pd.Series([pd.NA] * 8, dtype="Float64")
    df["SwingLow_H4_ConfirmedAt"] = pd.Series([pd.NaT] * 8, dtype="object")

    # SWEEP_UP at t4, SWEEP_DOWN at t5
    df["Sweep_H1_Up"] = [False, False, False, False, True, False, False, False]
    df["Sweep_H1_Down"] = [False, False, False, False, False, True, False, False]
    df["Sweep_H1_ReferenceLevel"] = [pd.NA, pd.NA, pd.NA, pd.NA, 14.0, 6.0, pd.NA, pd.NA]
    df["Sweep_H1_ReferenceTs"] = [
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        df.loc[2, "Timestamp"],
        df.loc[3, "Timestamp"],
        pd.NaT,
        pd.NaT,
    ]

    # FAILED_BREAK_UP at t6 confirmed from sweep t4; FAILED_BREAK_DOWN at t7 from sweep t5
    df["FailedBreak_H1_Up"] = [False, False, False, False, False, False, True, False]
    df["FailedBreak_H1_Down"] = [False, False, False, False, False, False, False, True]
    df["FailedBreak_H1_ReferenceLevel"] = [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 14.0, 6.0]
    df["FailedBreak_H1_ReferenceSweepTs"] = [
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        df.loc[4, "Timestamp"],
        df.loc[5, "Timestamp"],
    ]
    df["FailedBreak_H1_ConfirmedTs"] = [
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        pd.NaT,
        df.loc[6, "Timestamp"],
        df.loc[7, "Timestamp"],
    ]

    events = build_events(df)

    swings = events[events["EventType"].isin(["SWING_HIGH", "SWING_LOW"])]
    assert (swings["Timestamp"] == swings["ReferenceSwingTs"]).all()
    assert (swings["PriceLevel"] == swings["ReferenceSwingPrice"]).all()

    sweep_up = events[events["EventType"] == "SWEEP_UP"].iloc[0]
    assert sweep_up["Timestamp"] == df.loc[4, "Timestamp"]
    assert sweep_up["ReferenceSwingTs"] == df.loc[2, "Timestamp"]
    assert sweep_up["PriceLevel"] == sweep_up["ReferenceSwingPrice"]

    sweep_down = events[events["EventType"] == "SWEEP_DOWN"].iloc[0]
    assert sweep_down["Timestamp"] == df.loc[5, "Timestamp"]
    assert sweep_down["ReferenceSwingTs"] == df.loc[3, "Timestamp"]
    assert sweep_down["PriceLevel"] == sweep_down["ReferenceSwingPrice"]

    fb_up = events[events["EventType"] == "FAILED_BREAK_UP"].iloc[0]
    assert fb_up["Timestamp"] == df.loc[6, "Timestamp"]
    assert fb_up["ReferenceSwingTs"] == df.loc[4, "Timestamp"]
    assert fb_up["PriceLevel"] == fb_up["ReferenceSwingPrice"]

    fb_down = events[events["EventType"] == "FAILED_BREAK_DOWN"].iloc[0]
    assert fb_down["Timestamp"] == df.loc[7, "Timestamp"]
    assert fb_down["ReferenceSwingTs"] == df.loc[5, "Timestamp"]
    assert fb_down["PriceLevel"] == fb_down["ReferenceSwingPrice"]

    assert events["MetaJson"].isna().all()
