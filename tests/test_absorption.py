import pytest
from pathlib import Path

import pandas as pd

from analyzer.absorption import CONTEXT_WINDOW, detect_absorption
from analyzer.base_metrics import add_base_metrics
from analyzer.pipeline import run


def _build_frame(
    volume: list[float],
    delta: list[float],
    open_interest: list[float],
    liq_total: list[float],
) -> pd.DataFrame:
    n = len(volume)
    ts = pd.date_range("2024-01-01", periods=n, freq="min")
    liq_buy = [x * 0.6 for x in liq_total]
    liq_sell = [x * 0.4 for x in liq_total]

    return pd.DataFrame(
        {
            "Timestamp": ts,
            "Open": [10.0] * n,
            "High": [11.0] * n,
            "Low": [9.0] * n,
            "Close": [10.0] * n,
            "Volume": volume,
            "AggTrades": [1.0] * n,
            "BuyQty": delta,
            "SellQty": [0.0] * n,
            "VWAP": [10.0] * n,
            "OpenInterest": open_interest,
            "FundingRate": [0.0] * n,
            "LiqBuyQty": liq_buy,
            "LiqSellQty": liq_sell,
            "IsSynthetic": [False] * n,
        }
    )


def test_relative_volume_ratio_simple_series():
    raw = _build_frame([10.0, 10.0, 30.0], [1.0, 1.0, 1.0], [100.0, 101.0, 102.0], [1.0, 1.0, 1.0])
    features = detect_absorption(add_base_metrics(raw))

    assert CONTEXT_WINDOW == 20
    assert features["RelVolume_20"].tolist() == pytest.approx([1.0, 1.0, 1.8])


def test_delta_oi_and_liq_ratios_simple_series():
    raw = _build_frame([10.0, 10.0, 10.0], [2.0, 2.0, 10.0], [100.0, 102.0, 108.0], [1.0, 1.0, 5.0])
    features = detect_absorption(add_base_metrics(raw))

    assert features["DeltaAbsRatio_20"].tolist() == pytest.approx([1.0, 1.0, 15.0 / 7.0])
    assert features["OIChangeAbsRatio_20"].tolist() == pytest.approx([0.0, 2.0, 2.25])
    assert features["LiqTotalRatio_20"].tolist() == pytest.approx([1.0, 1.0, 15.0 / 7.0])


def test_absorption_score_is_deterministic_sum_of_component_flags():
    raw = _build_frame([10.0, 10.0, 30.0], [2.0, 2.0, 10.0], [100.0, 102.0, 108.0], [1.0, 1.0, 5.0])
    features = detect_absorption(add_base_metrics(raw))

    components = [
        "CtxRelVolumeSpike_v1",
        "CtxDeltaSpike_v1",
        "CtxOISpike_v1",
        "CtxLiqSpike_v1",
        "CtxWickReclaim_v1",
    ]

    assert "AbsorptionScore_v1" in features.columns
    expected = features[components].astype(int).sum(axis=1)
    assert features["AbsorptionScore_v1"].equals(expected)


def test_absorption_features_have_no_lookahead_prefix_stability():
    raw = _build_frame(
        [10.0, 11.0, 9.0, 10.0, 20.0, 12.0],
        [1.0, 2.0, 1.5, 1.0, 6.0, 2.0],
        [100.0, 101.0, 99.0, 102.0, 109.0, 108.0],
        [1.0, 1.5, 1.0, 0.5, 5.0, 1.0],
    )
    full = detect_absorption(add_base_metrics(raw))
    cols = [
        "RelVolume_20",
        "DeltaAbsRatio_20",
        "OIChangeAbsRatio_20",
        "LiqTotalRatio_20",
        "AbsorptionScore_v1",
    ]

    for i in range(2, len(raw) + 1):
        prefix = detect_absorption(add_base_metrics(raw.iloc[:i].copy()))
        for col in cols:
            assert prefix.iloc[-1][col] == full.iloc[i - 1][col]


def test_pipeline_output_contains_absorption_context_columns(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_report",
        lambda setups, outcomes: pd.DataFrame(
            [
                {
                    "GroupType": "overall",
                    "GroupValue": "ALL",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
                {
                    "GroupType": "SetupType",
                    "GroupValue": "X",
                    "SampleCount": 1,
                    "Mean_MFE_Pct": 0.0,
                    "Mean_MAE_Pct": 0.0,
                    "Mean_CloseReturn_Pct": 0.0,
                    "PositiveCloseReturnRate": 0.0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_context_report",
        lambda setups, outcomes: pd.DataFrame(
            columns=[
                "GroupType",
                "GroupValue",
                "SampleCount",
                "Mean_MFE_Pct",
                "Mean_MAE_Pct",
                "Mean_CloseReturn_Pct",
                "PositiveCloseReturnRate",
            ]
        ),
    )

    result = run(fixture, tmp_path)

    for col in [
        "RelVolume_20",
        "DeltaAbsRatio_20",
        "OIChangeAbsRatio_20",
        "LiqTotalRatio_20",
        "AbsorptionScore_v1",
    ]:
        assert col in result["features"].columns
