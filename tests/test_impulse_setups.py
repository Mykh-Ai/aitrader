from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from analyzer.impulse_setups import extract_impulse_setups
from analyzer.pipeline import run
from analyzer.setups import SETUP_COLUMNS


def _features_with_impulses() -> pd.DataFrame:
    start = pd.Timestamp("2025-01-01T00:00:00Z")
    rows: list[dict] = []
    for i in range(12):
        ts = start + pd.Timedelta(minutes=i)
        rows.append(
            {
                "Timestamp": ts,
                "Close": 100.0,
                "AbsorptionScore_v1": 1.0 + i,
                "CtxRelVolumeSpike_v1": bool(i % 2),
                "CtxDeltaSpike_v1": bool((i + 1) % 2),
                "CtxOISpike_v1": False,
                "CtxLiqSpike_v1": True,
                "CtxWickReclaim_v1": False,
                "RelVolume_20": 1.5,
                "DeltaAbsRatio_20": 1.2,
                "OIChangeAbsRatio_20": 1.1,
                "LiqTotalRatio_20": 1.3,
                "ImpulseDetected_v1": False,
                "ImpulseDirection_v1": pd.NA,
                "ImpulseAnchorMid_v1": pd.NA,
                "ImpulseAnchorVWAP_v1": pd.NA,
            }
        )

    # bearish impulse -> long reclaim at first qualifying bar (idx=3)
    rows[1]["ImpulseDetected_v1"] = True
    rows[1]["ImpulseDirection_v1"] = "IMPULSE_DOWN"
    rows[1]["ImpulseAnchorMid_v1"] = 101.0
    rows[1]["ImpulseAnchorVWAP_v1"] = 100.0
    rows[2]["Close"] = 100.5
    rows[3]["Close"] = 101.2
    rows[4]["Close"] = 102.0

    # bullish impulse -> short reclaim at first qualifying bar (idx=9)
    rows[7]["ImpulseDetected_v1"] = True
    rows[7]["ImpulseDirection_v1"] = "IMPULSE_UP"
    rows[7]["ImpulseAnchorMid_v1"] = 99.0
    rows[7]["ImpulseAnchorVWAP_v1"] = 100.0
    rows[8]["Close"] = 99.5
    rows[9]["Close"] = 98.8
    rows[10]["Close"] = 98.0

    return pd.DataFrame(rows)


def test_extract_impulse_setups_long_and_short_basic():
    setups = extract_impulse_setups(_features_with_impulses())

    assert len(setups) == 2
    assert list(setups.columns) == SETUP_COLUMNS

    long_row = setups.loc[setups["Direction"] == "LONG"].iloc[0]
    assert long_row["SetupType"] == "IMPULSE_FADE_RECLAIM_LONG_V1"
    assert long_row["ReferenceEventType"] == "IMPULSE_DOWN"
    assert long_row["SetupBarTs"] == pd.Timestamp("2025-01-01T00:03:00Z")
    assert long_row["ReferenceEventTs"] == pd.Timestamp("2025-01-01T00:01:00Z")

    short_row = setups.loc[setups["Direction"] == "SHORT"].iloc[0]
    assert short_row["SetupType"] == "IMPULSE_FADE_RECLAIM_SHORT_V1"
    assert short_row["ReferenceEventType"] == "IMPULSE_UP"
    assert short_row["SetupBarTs"] == pd.Timestamp("2025-01-01T00:09:00Z")
    assert short_row["ReferenceEventTs"] == pd.Timestamp("2025-01-01T00:07:00Z")


def test_extract_impulse_setups_materializes_only_first_qualifying_reclaim_bar():
    setups = extract_impulse_setups(_features_with_impulses())
    long_row = setups.loc[setups["Direction"] == "LONG"].iloc[0]
    short_row = setups.loc[setups["Direction"] == "SHORT"].iloc[0]

    assert long_row["SetupBarTs"] == pd.Timestamp("2025-01-01T00:03:00Z")
    assert short_row["SetupBarTs"] == pd.Timestamp("2025-01-01T00:09:00Z")


def test_extract_impulse_setups_no_reclaim_in_window_returns_empty():
    features = _features_with_impulses()
    features.loc[:, "Close"] = 100.0
    features.loc[1, ["ImpulseDetected_v1", "ImpulseDirection_v1", "ImpulseAnchorMid_v1", "ImpulseAnchorVWAP_v1"]] = [
        True,
        "IMPULSE_DOWN",
        101.0,
        100.0,
    ]

    setups = extract_impulse_setups(features)

    assert setups.empty
    assert list(setups.columns) == SETUP_COLUMNS


def test_extract_impulse_setups_setup_id_is_deterministic_for_same_input():
    features = _features_with_impulses()

    first = extract_impulse_setups(features)
    second = extract_impulse_setups(features)

    assert first["SetupId"].tolist() == second["SetupId"].tolist()


def test_pipeline_concat_adds_h2_rows_and_keeps_h1_rows_unchanged(monkeypatch, tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    h1 = pd.DataFrame(
        [
            {
                "SetupId": "h1-1",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "Status": "CANDIDATE",
                "DetectedAt": pd.Timestamp("2025-01-01T00:00:00Z"),
                "SetupBarTs": pd.Timestamp("2025-01-01T00:00:00Z"),
                "ReferenceEventTs": pd.Timestamp("2025-01-01T00:00:00Z"),
                "ReferenceEventType": "FAILED_BREAK_DOWN",
                "SourceTF": "H1",
                "ReferenceEventAnchorTs": pd.Timestamp("2025-01-01T00:00:00Z"),
                "ReferenceLevel": 100.0,
                "AbsorptionScore_v1": 1.0,
                "CtxRelVolumeSpike_v1": True,
                "CtxDeltaSpike_v1": False,
                "CtxOISpike_v1": False,
                "CtxLiqSpike_v1": True,
                "CtxWickReclaim_v1": False,
                "RelVolume_20": 1.0,
                "DeltaAbsRatio_20": 1.0,
                "OIChangeAbsRatio_20": 1.0,
                "LiqTotalRatio_20": 1.0,
                "LifecycleStatus": "PENDING",
                "InvalidatedAt": pd.NaT,
                "ExpiredAt": pd.NaT,
                "LifecycleBarsForward": 0,
            }
        ]
    )
    h2 = h1.copy()
    h2.loc[0, "SetupId"] = "h2-1"
    h2.loc[0, "SetupType"] = "IMPULSE_FADE_RECLAIM_LONG_V1"
    h2.loc[0, "ReferenceEventType"] = "IMPULSE_DOWN"

    monkeypatch.setattr("analyzer.pipeline.extract_setup_candidates", lambda features, events: h1)
    monkeypatch.setattr("analyzer.pipeline.extract_impulse_setups", lambda features: h2)

    result = run(fixture, tmp_path)

    assert set(result["setups"]["SetupId"]) == {"h1-1", "h2-1"}
    merged_h1 = result["setups"].loc[result["setups"]["SetupId"] == "h1-1"].reset_index(drop=True)
    pd.testing.assert_frame_equal(merged_h1, h1.reset_index(drop=True), check_like=False)


def test_pipeline_mixed_family_survives_research_summary_seam(monkeypatch, tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    base_row = {
        "SetupId": "h1-1",
        "SetupType": "FAILED_BREAK_RECLAIM_LONG",
        "Direction": "LONG",
        "Status": "CANDIDATE",
        "DetectedAt": pd.Timestamp("2025-01-01T00:00:00Z"),
        "SetupBarTs": pd.Timestamp("2025-01-01T00:00:00Z"),
        "ReferenceEventTs": pd.Timestamp("2025-01-01T00:00:00Z"),
        "ReferenceEventType": "FAILED_BREAK_DOWN",
        "SourceTF": "H1",
        "ReferenceEventAnchorTs": pd.Timestamp("2025-01-01T00:00:00Z"),
        "ReferenceLevel": 100.0,
        "AbsorptionScore_v1": 1.0,
        "CtxRelVolumeSpike_v1": True,
        "CtxDeltaSpike_v1": False,
        "CtxOISpike_v1": False,
        "CtxLiqSpike_v1": True,
        "CtxWickReclaim_v1": False,
        "RelVolume_20": 1.0,
        "DeltaAbsRatio_20": 1.0,
        "OIChangeAbsRatio_20": 1.0,
        "LiqTotalRatio_20": 1.0,
        "LifecycleStatus": "PENDING",
        "InvalidatedAt": pd.NaT,
        "ExpiredAt": pd.NaT,
        "LifecycleBarsForward": 0,
    }
    h1 = pd.DataFrame([base_row])
    h2 = pd.DataFrame([{**base_row, "SetupId": "h2-1", "SetupType": "IMPULSE_FADE_RECLAIM_LONG_V1", "ReferenceEventType": "IMPULSE_DOWN"}])

    monkeypatch.setattr("analyzer.pipeline.extract_setup_candidates", lambda features, events: h1)
    monkeypatch.setattr("analyzer.pipeline.extract_impulse_setups", lambda features: h2)
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_report",
        lambda setups, outcomes: pd.DataFrame(
            [{
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 1,
                "Mean_MFE_Pct": 0.0,
                "Median_MFE_Pct": 0.0,
                "Mean_MAE_Pct": 0.0,
                "Median_MAE_Pct": 0.0,
                "Mean_CloseReturn_Pct": 0.0,
                "Median_CloseReturn_Pct": 0.0,
                "PositiveCloseReturnRate": 0.0,
                "InvalidatedRate": 0.0,
                "ExpiredRate": 0.0,
                "PendingRate": 1.0,
                "FullHorizonRate": 0.0,
                "PartialHorizonRate": 0.0,
                "NoForwardBarsRate": 1.0,
            }]
        ),
    )
    monkeypatch.setattr("analyzer.pipeline.build_setup_context_report", lambda setups, outcomes: pd.DataFrame())
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_rankings",
        lambda report, context_report: pd.DataFrame(
            [{
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 1,
                "RankingMethod": "R",
                "RankingScore": 0.1,
                "RankingLabel": "X",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
            }]
        ),
    )
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_selections",
        lambda rankings: pd.DataFrame(
            [{
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SampleCount": 1,
                "RankingMethod": "R",
                "RankingScore": 0.1,
                "RankingLabel": "X",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
                "SelectionDecision": "SELECT",
                "SelectionReason": "ok",
            }]
        ),
    )
    monkeypatch.setattr(
        "analyzer.pipeline.build_setup_shortlist",
        lambda rankings, selections: selections.assign(ShortlistRank=[1]),
    )

    result = run(fixture, tmp_path)

    assert not result["research_summary"].empty
    direction_row = result["research_summary"].iloc[0]
    assert direction_row["SetupType"] == "MIXED_FAMILY"
    assert direction_row["Direction"] == "LONG"
    assert pd.isna(direction_row["EligibleEventTypes"])
    assert bool(direction_row["FormalizationEligible"]) is False
