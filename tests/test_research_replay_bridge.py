from pathlib import Path

import pandas as pd

from analyzer.research_replay_bridge import build_failed_break_reclaim_replay_bridge
from analyzer.research_variants import FAILED_BREAK_RECLAIM_EXTENDED_V1


RAW_COLUMNS = [
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "AggTrades",
    "BuyQty",
    "SellQty",
    "VWAP",
    "OpenInterest",
    "FundingRate",
    "LiqBuyQty",
    "LiqSellQty",
    "IsSynthetic",
]


def _raw_fixture(path: Path) -> Path:
    pd.DataFrame(
        [
            {
                "Timestamp": "2026-01-01T00:00:00Z",
                "Open": 100.0,
                "High": 101.0,
                "Low": 99.0,
                "Close": 100.5,
                "Volume": 1.0,
                "AggTrades": 1,
                "BuyQty": 0.5,
                "SellQty": 0.5,
                "VWAP": 100.0,
                "OpenInterest": 10.0,
                "FundingRate": 0.0,
                "LiqBuyQty": 0.0,
                "LiqSellQty": 0.0,
                "IsSynthetic": 0,
            },
            {
                "Timestamp": "2026-01-01T00:01:00Z",
                "Open": 100.5,
                "High": 102.0,
                "Low": 100.0,
                "Close": 101.0,
                "Volume": 1.0,
                "AggTrades": 1,
                "BuyQty": 0.5,
                "SellQty": 0.5,
                "VWAP": 101.0,
                "OpenInterest": 10.0,
                "FundingRate": 0.0,
                "LiqBuyQty": 0.0,
                "LiqSellQty": 0.0,
                "IsSynthetic": 0,
            },
        ],
        columns=RAW_COLUMNS,
    ).to_csv(path, index=False)
    return path


def test_research_replay_bridge_writes_isolated_backtester_artifacts(tmp_path: Path, monkeypatch):
    input_path = _raw_fixture(tmp_path / "raw.csv")

    setups = pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "Status": "CANDIDATE",
                "DetectedAt": pd.Timestamp("2026-01-01T00:00:00Z"),
                "SetupBarTs": pd.Timestamp("2026-01-01T00:00:00Z"),
                "ReferenceEventTs": pd.Timestamp("2026-01-01T00:00:00Z"),
                "ReferenceEventType": "FAILED_BREAK_DOWN",
                "SourceTF": "H4",
                "ReferenceEventAnchorTs": pd.Timestamp("2026-01-01T00:00:00Z"),
                "ReferenceLevel": 99.0,
                "AbsorptionScore_v1": 0.0,
                "CtxRelVolumeSpike_v1": False,
                "CtxDeltaSpike_v1": False,
                "CtxOISpike_v1": False,
                "CtxLiqSpike_v1": False,
                "CtxWickReclaim_v1": False,
                "RelVolume_20": 1.0,
                "DeltaAbsRatio_20": 0.0,
                "OIChangeAbsRatio_20": 0.0,
                "LiqTotalRatio_20": 0.0,
                "LifecycleStatus": "EXPIRED",
                "InvalidatedAt": pd.NaT,
                "ExpiredAt": pd.Timestamp("2026-01-01T00:01:00Z"),
                "LifecycleBarsForward": 1,
            }
        ]
    )

    monkeypatch.setattr("analyzer.research_replay_bridge.add_base_metrics", lambda df: df)
    monkeypatch.setattr("analyzer.research_replay_bridge.annotate_swings", lambda df: df)
    monkeypatch.setattr("analyzer.research_replay_bridge.detect_sweeps", lambda df: df)
    monkeypatch.setattr("analyzer.research_replay_bridge.detect_failed_breaks", lambda df, confirmation_bars: df)
    monkeypatch.setattr("analyzer.research_replay_bridge.detect_absorption", lambda df: df)
    monkeypatch.setattr("analyzer.research_replay_bridge.build_events", lambda df: pd.DataFrame())
    monkeypatch.setattr("analyzer.research_replay_bridge.extract_setup_candidates", lambda df, events, setup_ttl_bars: setups)
    monkeypatch.setattr(
        "analyzer.research_replay_bridge.build_setup_outcomes_by_horizon",
        lambda features, setups, variant_id, outcome_horizons: pd.DataFrame(
            [{"VariantId": variant_id, "SetupId": "S1", "OutcomeHorizonBars": outcome_horizons[0]}]
        ),
    )

    result = build_failed_break_reclaim_replay_bridge(input_path, tmp_path / "bridge")

    assert result["variant_id"] == FAILED_BREAK_RECLAIM_EXTENDED_V1.variant_id
    assert (tmp_path / "bridge" / "analyzer_features.csv").exists()
    assert (tmp_path / "bridge" / "analyzer_setups.csv").exists()
    assert (tmp_path / "bridge" / "analyzer_setup_shortlist.csv").exists()
    assert (tmp_path / "bridge" / "analyzer_research_summary.csv").exists()
    assert (tmp_path / "bridge" / "research_replay_bridge_manifest.json").exists()

    shortlist = pd.read_csv(tmp_path / "bridge" / "analyzer_setup_shortlist.csv")
    research_summary = pd.read_csv(tmp_path / "bridge" / "analyzer_research_summary.csv")

    assert shortlist.loc[0, "SourceReport"] == "FAILED_BREAK_RECLAIM_EXTENDED_V1"
    assert shortlist.loc[0, "SelectionDecision"] == "SELECT"
    assert research_summary.loc[0, "FormalizationEligible"] == True
    assert research_summary.loc[0, "EligibleEventTypes"] == "FAILED_BREAK_DOWN"
