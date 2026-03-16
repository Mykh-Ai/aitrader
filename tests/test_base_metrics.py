from pathlib import Path

import numpy as np
import pandas as pd

from analyzer.base_metrics import add_base_metrics
from analyzer.context import CONTEXT_MODEL_VERSION
from analyzer.loader import load_raw_csv


def test_base_metrics_core_formulas_deterministic():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv")
    out = add_base_metrics(df)

    assert out["Delta"].tolist() == [2.0, 2.0]
    assert out["CVD"].tolist() == [2.0, 4.0]
    assert np.allclose(out["DeltaPct"].tolist(), [0.2, 2.0 / 12.0])

    assert out["BarRange"].tolist() == [2.0, 2.0]
    assert out["BodySize"].tolist() == [0.5, 1.0]
    assert out["UpperWick"].tolist() == [0.5, 0.5]
    assert out["LowerWick"].tolist() == [1.0, 0.5]

    assert np.allclose(out["CloseLocation"].tolist(), [0.75, 0.75])
    assert np.allclose(out["BodyToRange"].tolist(), [0.25, 0.5])
    assert np.allclose(out["UpperWickToRange"].tolist(), [0.25, 0.25])
    assert np.allclose(out["LowerWickToRange"].tolist(), [0.5, 0.25])


def test_zero_volume_delta_pct_is_safe():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_with_synthetic.csv")
    out = add_base_metrics(df)

    assert out["Volume"].iloc[1] == 0
    assert out["DeltaPct"].iloc[1] == 0.0


def test_oi_change_and_liq_total_behavior():
    data = pd.DataFrame(
        {
            "Timestamp": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T00:01:00Z"], utc=True
            ),
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [100.5, 101.5],
            "Volume": [10.0, 10.0],
            "AggTrades": [1.0, 1.0],
            "BuyQty": [5.0, 5.0],
            "SellQty": [4.0, 4.0],
            "VWAP": [100.2, 101.2],
            "OpenInterest": [1000.0, 1004.5],
            "FundingRate": [0.0, 0.0],
            "LiqBuyQty": [1.5, 0.0],
            "LiqSellQty": [0.5, 2.5],
            "IsSynthetic": [0, 0],
        }
    )

    out = add_base_metrics(data)

    assert np.isnan(out["OI_Change"].iloc[0])
    assert out["OI_Change"].iloc[1] == 4.5
    assert out["LiqTotal"].tolist() == [2.0, 2.5]


def test_context_metadata_is_materialized_deterministically():
    data = pd.DataFrame(
        {
            "Timestamp": pd.to_datetime(
                [
                    "2025-01-01T07:59:00Z",
                    "2025-01-01T08:00:00Z",
                    "2025-01-01T13:30:00Z",
                ],
                utc=True,
            ),
            "Open": [100.0, 100.0, 100.0],
            "High": [101.0, 101.0, 101.0],
            "Low": [99.0, 99.0, 99.0],
            "Close": [100.5, 100.5, 100.5],
            "Volume": [10.0, 10.0, 10.0],
            "AggTrades": [1.0, 1.0, 1.0],
            "BuyQty": [5.0, 5.0, 5.0],
            "SellQty": [4.0, 4.0, 4.0],
            "VWAP": [100.2, 100.2, 100.2],
            "OpenInterest": [1000.0, 1000.0, 1000.0],
            "FundingRate": [0.0, 0.0, 0.0],
            "LiqBuyQty": [1.5, 1.5, 1.5],
            "LiqSellQty": [0.5, 0.5, 0.5],
            "IsSynthetic": [0, 0, 0],
        }
    )

    out = add_base_metrics(data)

    assert out["session"].tolist() == ["ASIA", "EU", "US"]
    assert out["minutes_from_eu_open"].tolist() == [-1, 0, 330]
    assert out["minutes_from_us_open"].tolist() == [-331, -330, 0]
    assert set(out["ContextModelVersion"]) == {CONTEXT_MODEL_VERSION}
