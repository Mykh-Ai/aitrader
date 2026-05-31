import pandas as pd

from market_monitor.structure import build_structure_levels


def test_finalized_sessions_emit_one_high_and_one_low_per_session():
    feed = pd.DataFrame(
        [
            _row("2026-05-07T00:00:00Z", 101, 99),
            _row("2026-05-07T07:59:00Z", 110, 98),
            _row("2026-05-07T08:00:00Z", 105, 97),
            _row("2026-05-07T15:59:00Z", 115, 100),
            _row("2026-05-07T16:00:00Z", 104, 96),
            _row("2026-05-07T23:59:00Z", 116, 95),
        ]
    )

    levels = build_structure_levels(feed)
    session = levels[levels["timeframe"] == "SESSION"]

    assert session["level_type"].tolist() == [
        "ASIA_HIGH",
        "ASIA_LOW",
        "EUROPE_LOW",
        "EUROPE_HIGH",
        "US_HIGH",
        "US_LOW",
    ]
    asia_high = session[session["level_type"] == "ASIA_HIGH"].iloc[0]
    assert asia_high["created_at"] == "2026-05-07T08:00:00Z"
    assert asia_high["level_timestamp"] == "2026-05-07T07:59:00Z"


def test_pdh_pdl_use_previous_day_once_and_no_first_day_fake_levels():
    feed = pd.DataFrame(
        [
            _row("2026-05-07T00:00:00Z", 100, 90),
            _row("2026-05-07T23:59:00Z", 110, 89),
            _row("2026-05-08T00:00:00Z", 105, 95),
            _row("2026-05-08T23:59:00Z", 106, 94),
        ]
    )

    levels = build_structure_levels(feed)
    pdh = levels[levels["level_type"] == "PDH"]
    pdl = levels[levels["level_type"] == "PDL"]

    assert len(pdh) == 1
    assert len(pdl) == 1
    assert pdh.iloc[0]["created_at"] == "2026-05-08T00:00:00Z"
    assert pdh.iloc[0]["price"] == 110
    assert pdl.iloc[0]["price"] == 89
    assert pdh.iloc[0]["source_start"] == "2026-05-07T00:00:00Z"
    assert pdh.iloc[0]["source_end"] == "2026-05-07T23:59:00Z"


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
