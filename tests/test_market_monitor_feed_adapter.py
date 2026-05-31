from pathlib import Path

from market_monitor.feed_adapter import load_feed


def test_load_feed_maps_historical_schema_without_mutating_source(tmp_path: Path):
    source = tmp_path / "historical.csv"
    original = "\n".join(
        [
            "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,IsSynthetic",
            "2025-01-01T00:01:00Z,101,103,100,102,12,7,8,4,101.5,1002,0.0001,0",
            "2025-01-01T00:00:00Z,100,102,99,101,10,5,6,4,100.5,1000,0.0001,0",
        ]
    )
    source.write_text(original, encoding="utf-8")

    feed = load_feed(source)

    assert source.read_text(encoding="utf-8") == original
    assert feed.columns.tolist() == [
        "Timestamp",
        "OpenPrice",
        "HiPrice",
        "LowPrice",
        "ClosePrice",
        "TotalQty",
        "Trades",
        "BuyQty",
        "SellQty",
        "OpenInterest",
        "FundingRate",
        "DataQuality",
        "SourceFile",
    ]
    assert feed["Timestamp"].is_monotonic_increasing
    assert feed.loc[0, "OpenPrice"] == 100
    assert feed.loc[0, "HiPrice"] == 102
    assert feed.loc[0, "LowPrice"] == 99
    assert feed.loc[0, "ClosePrice"] == 101
    assert feed.loc[0, "TotalQty"] == 10
    assert feed.loc[0, "Trades"] == 5
    assert feed["DataQuality"].tolist() == ["RAW", "RAW"]


def test_load_feed_marks_synthetic_rows_degraded(tmp_path: Path):
    source = tmp_path / "synthetic.csv"
    source.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate,IsSynthetic",
                "2025-01-01T00:00:00Z,100,101,99,100,10,5,6,4,1000,0.0001,1",
            ]
        ),
        encoding="utf-8",
    )

    feed = load_feed(source)

    assert feed.loc[0, "DataQuality"] == "RECOVERED_DEGRADED"

