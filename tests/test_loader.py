from pathlib import Path

import pandas as pd
import pytest

from analyzer.loader import load_raw_csv
from analyzer.feed_contract import FEED_TIMESTAMP_LABEL, FEED_TIMEZONE
from analyzer.schema import SchemaValidationError


FIXTURES = Path(__file__).parent / "fixtures"


def test_loader_parses_timestamp_and_sorts():
    df = load_raw_csv(FIXTURES / "sample_raw_minimal.csv")

    assert isinstance(df["Timestamp"].dtype, pd.DatetimeTZDtype)
    assert str(df["Timestamp"].dtype.tz) == "UTC"
    assert df["Timestamp"].is_monotonic_increasing


def test_datetime_utcnow_feed_rows_parse_as_utc(tmp_path):
    src = tmp_path / "utcnow_style.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2026-03-12 12:01:00,1,2,0,1,1,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    df = load_raw_csv(src)

    assert FEED_TIMEZONE == "UTC"
    assert str(df["FeedTimestampUTC"].dtype.tz) == "UTC"
    assert df.loc[0, "FeedTimestampUTC"] == pd.Timestamp("2026-03-12T12:01:00Z")


def test_close_labeled_feed_row_normalizes_to_candle_open(tmp_path):
    src = tmp_path / "close_labeled.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2026-03-12 12:01:00,1,2,0,1,1,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    df = load_raw_csv(src)

    assert FEED_TIMESTAMP_LABEL == "CLOSE"
    assert df.loc[0, "FeedTimestampUTC"] == pd.Timestamp("2026-03-12T12:01:00Z")
    assert df.loc[0, "CandleOpenTsUTC"] == pd.Timestamp("2026-03-12T12:00:00Z")
    assert df.loc[0, "Timestamp"] == pd.Timestamp("2026-03-12T12:00:00Z")


def test_loader_preserves_is_synthetic_values():
    df = load_raw_csv(FIXTURES / "sample_raw_with_synthetic.csv")
    assert df["IsSynthetic"].tolist() == [0, 1]


def test_loader_normalizes_bool_like_is_synthetic_values(tmp_path):
    src = tmp_path / "bool_like_synth.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,true\n"
        "2025-01-01T00:01:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,false\n",
        encoding="utf-8",
    )

    df = load_raw_csv(src)
    assert df["IsSynthetic"].tolist() == [1, 0]


def test_loader_missing_column_fails_clearly(tmp_path):
    src = tmp_path / "missing.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty\n"
        "2025-01-01T00:00:00Z,1,1,1,1,1,1,1,0,1,1,0,0,0\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Missing required raw columns: IsSynthetic"):
        load_raw_csv(src)


def test_loader_duplicate_timestamps_fail_clearly(tmp_path):
    src = tmp_path / "dupe_ts.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,0\n"
        "2025-01-01T00:00:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Duplicate Timestamp values found"):
        load_raw_csv(src)


def test_loader_invalid_is_synthetic_values_fail_clearly(tmp_path):
    src = tmp_path / "bad_synth.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,2\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Invalid IsSynthetic values"):
        load_raw_csv(src)


def test_loader_bad_numeric_values_fail_clearly(tmp_path):
    src = tmp_path / "bad_numeric.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,abc,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Invalid numeric raw values in column 'Volume'"):
        load_raw_csv(src)


def test_loader_empty_required_numeric_values_fail_clearly(tmp_path):
    src = tmp_path / "empty_numeric.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Invalid numeric raw values in column 'Volume'"):
        load_raw_csv(src)


def test_loader_reads_utf8_csv_explicitly(tmp_path):
    src = tmp_path / "utf8.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:00:00Z,1,2,0,1,1,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    df = load_raw_csv(src)
    assert len(df) == 1
    assert df.iloc[0]["Close"] == 1
