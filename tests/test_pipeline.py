from pathlib import Path

import pandas as pd
import pytest

from analyzer.pipeline import run
from analyzer.schema import FEATURE_COLUMNS_IMPLEMENTED, FEATURE_COLUMNS_PLANNED


RANKING_INPUT_COLUMNS = [
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
]


def test_pipeline_fails_loudly_when_report_is_empty(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    with pytest.raises(ValueError, match="non-empty report_df"):
        run(fixture, tmp_path)


def test_pipeline_smoke_writes_outputs_with_valid_report_baseline(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    mock_report = pd.DataFrame(
        [
            {
                "GroupType": "overall",
                "GroupValue": "ALL",
                "SampleCount": 10,
                "Mean_MFE_Pct": 1.0,
                "Mean_MAE_Pct": -1.0,
                "Mean_CloseReturn_Pct": 0.5,
                "PositiveCloseReturnRate": 0.5,
            },
            {
                "GroupType": "SetupType",
                "GroupValue": "ABSORPTION_LONG",
                "SampleCount": 7,
                "Mean_MFE_Pct": 1.2,
                "Mean_MAE_Pct": -0.8,
                "Mean_CloseReturn_Pct": 0.7,
                "PositiveCloseReturnRate": 0.6,
            },
        ]
    )
    mock_context_report = pd.DataFrame(columns=RANKING_INPUT_COLUMNS)

    monkeypatch.setattr("analyzer.pipeline.build_setup_report", lambda setups, outcomes: mock_report)
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_context_report",
        lambda setups, outcomes: mock_context_report,
    )

    result = run(fixture, tmp_path)

    assert result["features"].shape[0] == 2
    assert result["events"].empty
    assert result["setups"].empty
    assert result["outcomes"].empty
    assert not result["report"].empty
    assert result["context_report"].empty
    assert not result["rankings"].empty
    assert not result["selections"].empty
    assert "shortlist" in result
    assert result["features_path"].exists()
    assert result["events_path"].exists()
    assert result["setups_path"].exists()
    assert result["outcomes_path"].exists()
    assert result["report_path"].exists()
    assert result["context_report_path"].exists()
    assert result["rankings_path"].exists()
    assert result["selections_path"].exists()
    assert result["shortlist_path"].exists()
    assert result["setups_path"].name == "analyzer_setups.csv"
    assert result["outcomes_path"].name == "analyzer_setup_outcomes.csv"
    assert result["report_path"].name == "analyzer_setup_report.csv"
    assert result["context_report_path"].name == "analyzer_setup_context_report.csv"
    assert result["rankings_path"].name == "analyzer_setup_rankings.csv"
    assert result["selections_path"].name == "analyzer_setup_selections.csv"
    assert result["shortlist_path"].name == "analyzer_setup_shortlist.csv"


def test_pipeline_output_contains_implemented_feature_columns(tmp_path, monkeypatch):
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
        lambda setups, outcomes: pd.DataFrame(columns=RANKING_INPUT_COLUMNS),
    )

    result = run(fixture, tmp_path)
    features = result["features"]

    for col in FEATURE_COLUMNS_IMPLEMENTED:
        assert col in features.columns


def test_pipeline_output_does_not_claim_planned_columns_as_materialized(tmp_path, monkeypatch):
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
        lambda setups, outcomes: pd.DataFrame(columns=RANKING_INPUT_COLUMNS),
    )

    result = run(fixture, tmp_path)
    features = result["features"]

    for col in FEATURE_COLUMNS_PLANNED:
        assert col not in features.columns


def test_fixture_files_exist_and_loadable():
    fixtures_dir = Path(__file__).parent / "fixtures"
    expected = [
        "sample_raw_minimal.csv",
        "sample_raw_with_synthetic.csv",
        "sample_raw_with_gap.csv",
    ]

    for filename in expected:
        assert (fixtures_dir / filename).exists()


def test_pipeline_end_to_end_contract_consistency_non_mocked(tmp_path):
    rows = []
    start = pd.Timestamp("2025-01-01T00:00:00Z")

    special = {
        "2025-01-01T03:04:00+00:00": (121, 118, 121, 200, 150, 50, 1040, 4, 1),
        "2025-01-01T03:06:00+00:00": (119, 117, 119, 80, 30, 50, 1035, 1, 3),
        "2025-01-01T03:08:00+00:00": (122, 118, 122, 300, 250, 50, 1050, 5, 0),
        "2025-01-01T03:10:00+00:00": (119, 116, 118, 90, 20, 70, 1040, 1, 4),
        "2025-01-01T03:12:00+00:00": (123, 117, 123, 400, 350, 50, 1060, 6, 0),
        "2025-01-01T03:14:00+00:00": (119, 115, 117, 70, 10, 60, 1055, 1, 5),
        "2025-01-01T03:16:00+00:00": (124, 120, 124, 180, 120, 60, 1065, 2, 1),
        "2025-01-01T03:18:00+00:00": (119, 119, 119, 100, 50, 50, 1065, 1, 1),
    }

    for i in range(131):
        ts = start + pd.Timedelta(minutes=2 * i)
        hour = ts.hour

        high = 105
        low = 95
        close = 100
        open_ = 100
        volume = 100 + i
        buy_qty = 60 + (i % 10)
        sell_qty = 40 + (i % 7)
        open_interest = 1000 + i * 0.5
        liq_buy_qty = 1 + (i % 3)
        liq_sell_qty = 1 + (i % 4)

        if hour == 0:
            high = 100 - (i % 3)
            low = 90 + (i % 2)
            close = 95 + (i % 2)
        elif hour == 1:
            high = 110
            low = 85
            close = 100
            if ts.minute == 20:
                high = 120
                low = 80
                close = 110
        elif hour == 2:
            high = 110 - (i % 2)
            low = 85 + (i % 3)
            close = 100 - (i % 2)
        elif hour >= 3:
            high = 111
            low = 96
            close = 100

        key = ts.isoformat()
        if key in special:
            (
                high,
                low,
                close,
                volume,
                buy_qty,
                sell_qty,
                open_interest,
                liq_buy_qty,
                liq_sell_qty,
            ) = special[key]
            open_ = close

        rows.append(
            {
                "Timestamp": ts.isoformat().replace("+00:00", "Z"),
                "Open": open_,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": volume,
                "AggTrades": 10,
                "BuyQty": buy_qty,
                "SellQty": sell_qty,
                "VWAP": (high + low + close) / 3,
                "OpenInterest": open_interest,
                "FundingRate": 0.0001,
                "LiqBuyQty": liq_buy_qty,
                "LiqSellQty": liq_sell_qty,
                "IsSynthetic": 0,
            }
        )

    fixture_path = tmp_path / "contract_non_mocked_raw.csv"
    pd.DataFrame(rows).to_csv(fixture_path, index=False)

    result = run(fixture_path, tmp_path)

    assert not result["setups"].empty
    assert not result["outcomes"].empty
    assert not result["report"].empty

    assert len(result["setups"]) == len(result["outcomes"])
    assert set(result["setups"]["SetupId"]) == set(result["outcomes"]["SetupId"])

    baseline = result["report"].loc[
        (result["report"]["GroupType"] == "overall")
        & (result["report"]["GroupValue"] == "ALL")
    ]
    assert len(baseline) == 1

    assert not (
        (result["rankings"]["GroupType"] == "overall")
        & (result["rankings"]["GroupValue"] == "ALL")
    ).any()

    for name in [
        "analyzer_setups.csv",
        "analyzer_setup_outcomes.csv",
        "analyzer_setup_report.csv",
        "analyzer_setup_context_report.csv",
        "analyzer_setup_rankings.csv",
        "analyzer_setup_selections.csv",
        "analyzer_setup_shortlist.csv",
    ]:
        assert (tmp_path / name).exists()

    assert not result["rankings"].empty
    assert not result["selections"].empty
    assert "shortlist" in result
    assert set(result["rankings"]["SourceReport"].unique()) <= {"report", "context_report"}
    assert len(result["selections"]) == len(result["rankings"])
