import pandas as pd

from market_monitor.structure import build_structure_levels


def test_h1_swing_created_at_uses_confirming_bar_timestamp():
    highs = [101, 102, 110, 103, 102]
    lows = [99, 98, 97, 98, 99]
    feed = _hourly_feed(highs, lows)

    levels = build_structure_levels(feed)
    swing = levels[levels["level_type"] == "H1_SWING_HIGH"].iloc[0]

    assert swing["level_timestamp"] == "2026-05-07T02:00:00Z"
    assert swing["created_at"] == "2026-05-07T04:00:00Z"
    assert pd.Timestamp(swing["created_at"]) >= pd.Timestamp(swing["level_timestamp"])
    assert "future_return" not in levels.columns
    assert "outcome_12_bar" not in levels.columns
    assert "signal" not in levels.columns
    assert "order" not in levels.columns
    assert "position" not in levels.columns


def test_h4_swing_created_at_uses_right_bar_timestamp():
    highs = [101, 120, 102]
    lows = [99, 98, 100]
    feed = _four_hour_feed(highs, lows)

    levels = build_structure_levels(feed)
    swing = levels[levels["level_type"] == "H4_SWING_HIGH"].iloc[0]

    assert swing["level_timestamp"] == "2026-05-07T04:00:00Z"
    assert swing["created_at"] == "2026-05-07T08:00:00Z"


def _hourly_feed(highs, lows):
    rows = []
    for hour, (high, low) in enumerate(zip(highs, lows)):
        rows.append(_row(f"2026-05-07T{hour:02d}:00:00Z", high, low))
    return pd.DataFrame(rows)


def _four_hour_feed(highs, lows):
    rows = []
    for index, (high, low) in enumerate(zip(highs, lows)):
        rows.append(_row(f"2026-05-07T{index * 4:02d}:00:00Z", high, low))
    return pd.DataFrame(rows)


def _row(ts, high, low):
    return {
        "Timestamp": pd.Timestamp(ts),
        "OpenPrice": 100,
        "HiPrice": high,
        "LowPrice": low,
        "ClosePrice": 100,
        "TotalQty": 10,
        "Trades": 1,
        "BuyQty": 5,
        "SellQty": 5,
        "OpenInterest": 1000,
        "FundingRate": 0.0001,
        "DataQuality": "RAW",
        "SourceFile": "synthetic.csv",
    }
