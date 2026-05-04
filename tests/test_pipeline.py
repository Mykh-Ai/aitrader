from pathlib import Path

import pandas as pd
import pytest

from analyzer.pipeline import run
from analyzer.rankings import RANKING_COLUMNS
from analyzer.research_variants import FAILED_BREAK_RECLAIM_EXTENDED_V1, run_research_variants
from analyzer.schema import FEATURE_COLUMNS_IMPLEMENTED
from analyzer.selections import SELECTION_COLUMNS
from analyzer.shortlist_explanations import SHORTLIST_EXPLANATION_COLUMNS
from analyzer.shortlists import SHORTLIST_COLUMNS
from analyzer.research_summary import RESEARCH_SUMMARY_COLUMNS
from analyzer.day_regime_report import DAY_REGIME_REPORT_COLUMNS
from analyzer.outcomes import build_setup_outcomes_by_horizon


RANKING_INPUT_COLUMNS = [
    "GroupType",
    "GroupValue",
    "SampleCount",
    "Mean_MFE_Pct",
    "Mean_MAE_Pct",
    "Mean_CloseReturn_Pct",
    "PositiveCloseReturnRate",
]


def test_pipeline_succeeds_with_valid_empty_day_outputs(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)

    assert result["setups"].empty
    assert result["outcomes"].empty
    assert result["report"].empty
    assert result["context_report"].empty

    assert list(result["rankings"].columns) == RANKING_COLUMNS
    assert result["rankings"].empty

    assert list(result["selections"].columns) == SELECTION_COLUMNS
    assert result["selections"].empty

    assert list(result["shortlist"].columns) == SHORTLIST_COLUMNS
    assert result["shortlist"].empty

    assert list(result["shortlist_explanations"].columns) == SHORTLIST_EXPLANATION_COLUMNS
    assert result["shortlist_explanations"].empty

    assert list(result["research_summary"].columns) == RESEARCH_SUMMARY_COLUMNS
    assert result["research_summary"].empty

    assert list(result["day_regime_report"].columns) == DAY_REGIME_REPORT_COLUMNS
    assert not result["day_regime_report"].empty


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
    assert "shortlist_explanations" in result
    assert "research_summary" in result
    assert result["features_path"].exists()
    assert result["events_path"].exists()
    assert result["setups_path"].exists()
    assert result["outcomes_path"].exists()
    assert result["report_path"].exists()
    assert result["context_report_path"].exists()
    assert result["rankings_path"].exists()
    assert result["selections_path"].exists()
    assert result["shortlist_path"].exists()
    assert result["shortlist_explanations_path"].exists()
    assert result["research_summary_path"].exists()
    assert result["day_regime_report_path"].exists()
    assert result["setups_path"].name == "analyzer_setups.csv"
    assert result["outcomes_path"].name == "analyzer_setup_outcomes.csv"
    assert result["report_path"].name == "analyzer_setup_report.csv"
    assert result["context_report_path"].name == "analyzer_setup_context_report.csv"
    assert result["rankings_path"].name == "analyzer_setup_rankings.csv"
    assert result["selections_path"].name == "analyzer_setup_selections.csv"
    assert result["shortlist_path"].name == "analyzer_setup_shortlist.csv"
    assert result["shortlist_explanations_path"].name == "analyzer_setup_shortlist_explanations.csv"
    assert result["research_summary_path"].name == "analyzer_research_summary.csv"
    assert result["day_regime_report_path"].name == "analyzer_day_regime_report.csv"


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


def test_pipeline_output_contains_context_feature_columns(tmp_path, monkeypatch):
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

    for col in ["session", "minutes_from_eu_open", "minutes_from_us_open", "ContextModelVersion"]:
        assert col in features.columns


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
        "analyzer_setup_shortlist_explanations.csv",
        "analyzer_research_summary.csv",
    ]:
        assert (tmp_path / name).exists()

    assert not result["rankings"].empty
    assert not result["selections"].empty
    assert "shortlist" in result
    assert "shortlist_explanations" in result
    assert "research_summary" in result
    assert set(result["rankings"]["SourceReport"].unique()) <= {"report", "context_report"}
    assert len(result["selections"]) == len(result["rankings"])


def test_pipeline_succeeds_on_small_sample_when_numeric_context_buckets_are_not_possible(
    tmp_path, monkeypatch
):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    small_setups = pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "ABSORPTION_LONG",
                "Direction": "LONG",
                "LifecycleStatus": "PENDING",
                "AbsorptionScore_v1": 1.0,
                "CtxRelVolumeSpike_v1": 1,
                "CtxDeltaSpike_v1": 0,
                "CtxOISpike_v1": 1,
                "CtxLiqSpike_v1": 0,
                "CtxWickReclaim_v1": 1,
                "RelVolume_20": 10.0,
                "DeltaAbsRatio_20": 20.0,
                "OIChangeAbsRatio_20": 30.0,
                "LiqTotalRatio_20": 40.0,
            },
            {
                "SetupId": "S2",
                "SetupType": "SWEEP_SHORT",
                "Direction": "SHORT",
                "LifecycleStatus": "PENDING",
                "AbsorptionScore_v1": 2.0,
                "CtxRelVolumeSpike_v1": 0,
                "CtxDeltaSpike_v1": 1,
                "CtxOISpike_v1": 0,
                "CtxLiqSpike_v1": 1,
                "CtxWickReclaim_v1": 0,
                "RelVolume_20": 10.0,
                "DeltaAbsRatio_20": 20.0,
                "OIChangeAbsRatio_20": 30.0,
                "LiqTotalRatio_20": 40.0,
            },
        ]
    )
    small_outcomes = pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "OutcomeStatus": "FULL_HORIZON",
                "MFE_Pct": 1.0,
                "MAE_Pct": -1.0,
                "CloseReturn_Pct": 1.0,
            },
            {
                "SetupId": "S2",
                "OutcomeStatus": "PARTIAL_HORIZON",
                "MFE_Pct": 2.0,
                "MAE_Pct": -2.0,
                "CloseReturn_Pct": -1.0,
            },
        ]
    )

    monkeypatch.setattr("analyzer.pipeline.extract_setup_candidates", lambda features, events: small_setups)
    monkeypatch.setattr("analyzer.pipeline.build_setup_outcomes", lambda features, setups: small_outcomes)

    result = run(fixture, tmp_path)

    assert not result["context_report"].empty
    assert "RelVolume_20" not in result["context_report"]["GroupType"].values
    assert not result["rankings"].empty


def test_pipeline_legacy_output_paths_preserved_with_additive_regime_output(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)

    legacy_paths = {
        "features_path": "analyzer_features.csv",
        "events_path": "analyzer_events.csv",
        "setups_path": "analyzer_setups.csv",
        "outcomes_path": "analyzer_setup_outcomes.csv",
        "report_path": "analyzer_setup_report.csv",
        "context_report_path": "analyzer_setup_context_report.csv",
        "rankings_path": "analyzer_setup_rankings.csv",
        "selections_path": "analyzer_setup_selections.csv",
        "shortlist_path": "analyzer_setup_shortlist.csv",
        "shortlist_explanations_path": "analyzer_setup_shortlist_explanations.csv",
        "research_summary_path": "analyzer_research_summary.csv",
    }

    for key, filename in legacy_paths.items():
        assert result[key].name == filename

    assert result["day_regime_report_path"].name == "analyzer_day_regime_report.csv"


def test_default_pipeline_does_not_write_research_variant_sidecar(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    run(fixture, tmp_path)

    assert not (tmp_path / "research_variants").exists()


def test_explicit_extended_research_variant_writes_sidecar_only(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"
    setup_ts = pd.Timestamp("2025-01-01T00:00:00Z")
    setups = pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "SetupBarTs": setup_ts,
                "Direction": "LONG",
                "ReferenceLevel": 100.0,
            }
        ]
    )
    features = pd.DataFrame(
        {
            "Timestamp": pd.date_range(setup_ts, periods=65, freq="1min", tz="UTC"),
            "High": [100.0 + i for i in range(65)],
            "Low": [99.0 + i for i in range(65)],
            "Close": [99.5 + i for i in range(65)],
        }
    )

    monkeypatch.setattr(
        "analyzer.research_variants._build_failed_break_reclaim_variant",
        lambda input_path, *, config: (
            setups,
            build_setup_outcomes_by_horizon(
                features,
                setups,
                variant_id=config.variant_id,
                outcome_horizons=config.outcome_horizons,
            ),
        ),
    )

    result = run_research_variants(fixture, tmp_path, variants=(FAILED_BREAK_RECLAIM_EXTENDED_V1,))

    sidecar_path = (
        tmp_path
        / "research_variants"
        / "FAILED_BREAK_RECLAIM_EXTENDED_V1"
        / "analyzer_setup_outcomes_by_horizon.csv"
    )
    assert sidecar_path.exists()
    assert result["FAILED_BREAK_RECLAIM_EXTENDED_V1"]["outcomes_by_horizon_path"] == sidecar_path

    sidecar = pd.read_csv(sidecar_path)
    assert sidecar["OutcomeHorizonBars"].tolist() == [60, 240, 1440, 4320, 10080]
    assert set(sidecar["VariantId"]) == {"FAILED_BREAK_RECLAIM_EXTENDED_V1"}
    assert not (tmp_path / "analyzer_setup_outcomes.csv").exists()
