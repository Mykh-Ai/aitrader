"""Raw feed timestamp contract and normalization helpers."""

from __future__ import annotations

import pandas as pd

FEED_TIMEZONE = "UTC"
FEED_TIMESTAMP_LABEL = "CLOSE"
FEED_INTERVAL = pd.Timedelta(minutes=1)
FEED_RAW_TIMESTAMP_COLUMN = "Timestamp"
FEED_TIMESTAMP_UTC_COLUMN = "FeedTimestampUTC"
CANDLE_OPEN_TIMESTAMP_COLUMN = "CandleOpenTsUTC"


def normalize_feed_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize current aggregator close-labeled feed rows to UTC candle opens.

    ``binance_aggregator_shi.py`` writes the wall-clock UTC minute at flush time.
    The buffered OHLCV data covers the preceding one-minute interval, so the raw
    feed ``Timestamp`` is a close label. Analyzer internals use ``Timestamp`` as
    the canonical candle-open timestamp, while preserving the raw label in
    ``FeedTimestampUTC`` for auditability.
    """
    out = df.copy()
    raw_ts = pd.to_datetime(
        out[FEED_RAW_TIMESTAMP_COLUMN],
        utc=True,
        errors="raise",
    )
    out[FEED_TIMESTAMP_UTC_COLUMN] = raw_ts

    if FEED_TIMESTAMP_LABEL == "CLOSE":
        candle_open = raw_ts - FEED_INTERVAL
    elif FEED_TIMESTAMP_LABEL == "OPEN":
        candle_open = raw_ts
    else:
        raise ValueError(f"Unsupported FEED_TIMESTAMP_LABEL: {FEED_TIMESTAMP_LABEL}")

    out[CANDLE_OPEN_TIMESTAMP_COLUMN] = candle_open
    out[FEED_RAW_TIMESTAMP_COLUMN] = candle_open
    return out
