"""Event table helpers for analyzer."""

from __future__ import annotations

import pandas as pd

from .schema import EVENT_COLUMNS

_TIMEFRAMES = ("H1", "H4")


def _empty_events() -> pd.DataFrame:
    return pd.DataFrame(columns=EVENT_COLUMNS)


def _build_swing_events(df: pd.DataFrame) -> pd.DataFrame:
    events: list[pd.DataFrame] = []

    for tf in _TIMEFRAMES:
        high_price_col = f"SwingHigh_{tf}_Price"
        high_confirmed_col = f"SwingHigh_{tf}_ConfirmedAt"
        low_price_col = f"SwingLow_{tf}_Price"
        low_confirmed_col = f"SwingLow_{tf}_ConfirmedAt"

        required_cols = {high_price_col, high_confirmed_col, low_price_col, low_confirmed_col}
        if not required_cols.issubset(df.columns):
            continue

        high_confirmed = pd.to_datetime(df[high_confirmed_col], utc=True)
        high_is_new = high_confirmed.notna() & (
            high_confirmed != high_confirmed.shift(1)
        )

        high_events = pd.DataFrame(
            {
                "Timestamp": high_confirmed.loc[high_is_new],
                "EventType": "SWING_HIGH",
                "Side": "up",
                "PriceLevel": pd.to_numeric(df.loc[high_is_new, high_price_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": high_confirmed.loc[high_is_new],
                "ReferenceSwingPrice": pd.to_numeric(
                    df.loc[high_is_new, high_price_col], errors="coerce"
                ),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        low_confirmed = pd.to_datetime(df[low_confirmed_col], utc=True)
        low_is_new = low_confirmed.notna() & (
            low_confirmed != low_confirmed.shift(1)
        )

        low_events = pd.DataFrame(
            {
                "Timestamp": low_confirmed.loc[low_is_new],
                "EventType": "SWING_LOW",
                "Side": "down",
                "PriceLevel": pd.to_numeric(df.loc[low_is_new, low_price_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": low_confirmed.loc[low_is_new],
                "ReferenceSwingPrice": pd.to_numeric(
                    df.loc[low_is_new, low_price_col], errors="coerce"
                ),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        events.extend([high_events, low_events])

    if not events:
        return _empty_events()

    out = pd.concat(events, ignore_index=True)
    return out.loc[out["Timestamp"].notna(), EVENT_COLUMNS]


def _build_sweep_events(df: pd.DataFrame) -> pd.DataFrame:
    events: list[pd.DataFrame] = []

    for tf in _TIMEFRAMES:
        up_col = f"Sweep_{tf}_Up"
        down_col = f"Sweep_{tf}_Down"
        level_col = f"Sweep_{tf}_ReferenceLevel"
        ref_ts_col = f"Sweep_{tf}_ReferenceTs"

        required_cols = {"Timestamp", up_col, down_col, level_col, ref_ts_col}
        if not required_cols.issubset(df.columns):
            continue

        up_mask = df[up_col].fillna(False).astype(bool)
        down_mask = df[down_col].fillna(False).astype(bool)

        up_events = pd.DataFrame(
            {
                "Timestamp": pd.to_datetime(df.loc[up_mask, "Timestamp"], utc=True),
                "EventType": "SWEEP_UP",
                "Side": "up",
                "PriceLevel": pd.to_numeric(df.loc[up_mask, level_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": pd.to_datetime(df.loc[up_mask, ref_ts_col], utc=True),
                "ReferenceSwingPrice": pd.to_numeric(df.loc[up_mask, level_col], errors="coerce"),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        down_events = pd.DataFrame(
            {
                "Timestamp": pd.to_datetime(df.loc[down_mask, "Timestamp"], utc=True),
                "EventType": "SWEEP_DOWN",
                "Side": "down",
                "PriceLevel": pd.to_numeric(df.loc[down_mask, level_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": pd.to_datetime(df.loc[down_mask, ref_ts_col], utc=True),
                "ReferenceSwingPrice": pd.to_numeric(df.loc[down_mask, level_col], errors="coerce"),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        events.extend([up_events, down_events])

    if not events:
        return _empty_events()

    return pd.concat(events, ignore_index=True).loc[:, EVENT_COLUMNS]


def _build_failed_break_events(df: pd.DataFrame) -> pd.DataFrame:
    events: list[pd.DataFrame] = []

    for tf in _TIMEFRAMES:
        up_col = f"FailedBreak_{tf}_Up"
        down_col = f"FailedBreak_{tf}_Down"
        level_col = f"FailedBreak_{tf}_ReferenceLevel"
        ref_sweep_ts_col = f"FailedBreak_{tf}_ReferenceSweepTs"
        confirmed_ts_col = f"FailedBreak_{tf}_ConfirmedTs"

        required_cols = {up_col, down_col, level_col, ref_sweep_ts_col, confirmed_ts_col}
        if not required_cols.issubset(df.columns):
            continue

        up_mask = df[up_col].fillna(False).astype(bool)
        down_mask = df[down_col].fillna(False).astype(bool)

        up_events = pd.DataFrame(
            {
                "Timestamp": pd.to_datetime(df.loc[up_mask, confirmed_ts_col], utc=True),
                "EventType": "FAILED_BREAK_UP",
                "Side": "up",
                "PriceLevel": pd.to_numeric(df.loc[up_mask, level_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": pd.to_datetime(df.loc[up_mask, ref_sweep_ts_col], utc=True),
                "ReferenceSwingPrice": pd.to_numeric(df.loc[up_mask, level_col], errors="coerce"),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        down_events = pd.DataFrame(
            {
                "Timestamp": pd.to_datetime(df.loc[down_mask, confirmed_ts_col], utc=True),
                "EventType": "FAILED_BREAK_DOWN",
                "Side": "down",
                "PriceLevel": pd.to_numeric(df.loc[down_mask, level_col], errors="coerce"),
                "SourceTF": tf,
                "ReferenceSwingTs": pd.to_datetime(df.loc[down_mask, ref_sweep_ts_col], utc=True),
                "ReferenceSwingPrice": pd.to_numeric(df.loc[down_mask, level_col], errors="coerce"),
                "Confidence": pd.NA,
                "MetaJson": pd.NA,
            }
        )

        events.extend([up_events, down_events])

    if not events:
        return _empty_events()

    out = pd.concat(events, ignore_index=True)
    return out.loc[out["Timestamp"].notna(), EVENT_COLUMNS]


def build_events(df: pd.DataFrame) -> pd.DataFrame:
    """Build normalized event table from materialized feature columns.

    Mapping implemented:
    - SWING_HIGH / SWING_LOW from confirmed swing columns
    - SWEEP_UP / SWEEP_DOWN from sweep flags
    - FAILED_BREAK_UP / FAILED_BREAK_DOWN from failed-break flags

    Anti-duplication behavior:
    - swings are emitted only when confirmation timestamp changes versus prior row,
      preventing re-emission from persistent "latest confirmed swing" columns.
    - sweeps / failed-breaks emit only rows where corresponding boolean flags are True.

    Output ordering is deterministic: Timestamp, SourceTF, EventType, Side.

    Current phase contract: Confidence and MetaJson remain null/NA for all event rows
    until later lifecycle/scoring phases.
    """
    if df.empty:
        return _empty_events()

    parts = [
        _build_swing_events(df),
        _build_sweep_events(df),
        _build_failed_break_events(df),
    ]
    events = [part for part in parts if not part.empty]
    if not events:
        return _empty_events()

    out = pd.concat(events, ignore_index=True)
    out = out.sort_values(
        by=["Timestamp", "SourceTF", "EventType", "Side"],
        kind="mergesort",
    ).reset_index(drop=True)

    return out.loc[:, EVENT_COLUMNS]
