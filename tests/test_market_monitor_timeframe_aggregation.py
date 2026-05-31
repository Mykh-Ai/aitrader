import pandas as pd

from market_monitor.structure import aggregate_timeframe


def test_h1_aggregation_is_deterministic_and_conservative_quality():
    feed = _feed(
        [
            ("2026-05-07T00:00:00Z", 100, 102, 99, 101, 10, "RAW"),
            ("2026-05-07T00:01:00Z", 101, 104, 100, 103, 11, "RECOVERED_DEGRADED"),
            ("2026-05-07T01:00:00Z", 103, 105, 102, 104, 12, "RAW"),
        ]
    )

    first = aggregate_timeframe(feed, "H1")
    second = aggregate_timeframe(feed, "H1")

    assert first.equals(second)
    assert first.loc[0, "Timestamp"] == pd.Timestamp("2026-05-07T00:00:00Z")
    assert first.loc[0, "OpenPrice"] == 100
    assert first.loc[0, "HiPrice"] == 104
    assert first.loc[0, "LowPrice"] == 99
    assert first.loc[0, "ClosePrice"] == 103
    assert first.loc[0, "TotalQty"] == 21
    assert first.loc[0, "DataQuality"] == "RECOVERED_DEGRADED"


def test_h4_aggregation_aligns_to_utc_four_hour_boundaries():
    feed = _feed(
        [
            ("2026-05-07T03:59:00Z", 100, 101, 99, 100, 10, "RAW"),
            ("2026-05-07T04:00:00Z", 100, 102, 99, 101, 11, "RAW"),
            ("2026-05-07T07:59:00Z", 101, 103, 100, 102, 12, "RAW"),
            ("2026-05-07T08:00:00Z", 102, 104, 101, 103, 13, "RAW"),
        ]
    )

    bars = aggregate_timeframe(feed, "H4")

    assert bars["Timestamp"].tolist() == [
        pd.Timestamp("2026-05-07T00:00:00Z"),
        pd.Timestamp("2026-05-07T04:00:00Z"),
        pd.Timestamp("2026-05-07T08:00:00Z"),
    ]
    assert all(ts.hour in {0, 4, 8, 12, 16, 20} for ts in bars["Timestamp"])


def _feed(rows):
    records = []
    for index, (ts, open_, high, low, close, qty, quality) in enumerate(rows):
        records.append(
            {
                "Timestamp": pd.Timestamp(ts),
                "OpenPrice": open_,
                "HiPrice": high,
                "LowPrice": low,
                "ClosePrice": close,
                "TotalQty": qty,
                "Trades": index + 1,
                "BuyQty": qty / 2,
                "SellQty": qty / 2,
                "OpenInterest": 1000 + index,
                "FundingRate": 0.0001,
                "DataQuality": quality,
                "SourceFile": "synthetic.csv",
            }
        )
    return pd.DataFrame(records)
