from pathlib import Path

import pandas as pd
import pytest

from analyzer.loader import load_raw_csv
from analyzer.schema import SchemaValidationError


FIXTURES = Path(__file__).parent / "fixtures"


def test_loader_parses_timestamp_and_sorts(tmp_path):
    src = tmp_path / "unsorted.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic\n"
        "2025-01-01T00:01:00Z,1,1,1,1,1,1,1,0,1,1,0,0,0,0\n"
        "2025-01-01T00:00:00Z,1,1,1,1,1,1,1,0,1,1,0,0,0,0\n",
        encoding="utf-8",
    )

    df = load_raw_csv(src)

    assert pd.api.types.is_datetime64tz_dtype(df["Timestamp"])
    assert df["Timestamp"].iloc[0] < df["Timestamp"].iloc[1]


def test_loader_preserves_is_synthetic_values():
    df = load_raw_csv(FIXTURES / "sample_raw_with_synthetic.csv")
    assert df["IsSynthetic"].tolist() == [0, 1]


def test_loader_missing_column_fails_clearly(tmp_path):
    src = tmp_path / "missing.csv"
    src.write_text(
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty\n"
        "2025-01-01T00:00:00Z,1,1,1,1,1,1,1,0,1,1,0,0,0\n",
        encoding="utf-8",
    )

    with pytest.raises(SchemaValidationError, match="Missing required raw columns: IsSynthetic"):
        load_raw_csv(src)
