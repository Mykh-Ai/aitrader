from pathlib import Path

import pandas as pd

from analyzer.day_regime_report import DAY_REGIME_REPORT_COLUMNS, build_day_regime_report
from analyzer.pipeline import run


def _base_features(*, count: int, bar_range: float, volume: float, delta: float, oi_change: float, liq_total: float, close_location: float) -> pd.DataFrame:
    start = pd.Timestamp("2025-01-01T00:00:00Z")
    rows = []
    for idx in range(count):
        rows.append(
            {
                "Timestamp": start + pd.Timedelta(minutes=idx),
                "Close": 100.0,
                "BarRange": bar_range,
                "Volume": volume,
                "Delta": delta,
                "OI_Change": oi_change,
                "LiqTotal": liq_total,
                "CloseLocation": close_location,
                "IsSynthetic": 0,
                "RelVolume_20": 1.0,
                "AbsorptionScore_v1": 2.0,
            }
        )
    return pd.DataFrame(rows)


def test_day_regime_report_schema_and_required_columns():
    features = _base_features(
        count=120,
        bar_range=0.02,
        volume=100.0,
        delta=10.0,
        oi_change=5.0,
        liq_total=2.0,
        close_location=0.5,
    )

    report = build_day_regime_report(
        features_df=features,
        events_df=pd.DataFrame(columns=["Timestamp", "EventType"]),
        setups_df=pd.DataFrame(columns=["SetupBarTs", "SetupType"]),
        shortlist_df=pd.DataFrame(),
        research_summary_df=pd.DataFrame(columns=["FormalizationEligible"]),
    )

    assert list(report.columns) == DAY_REGIME_REPORT_COLUMNS
    assert len(report) == 1


def test_day_regime_report_honest_unclassified_fallback_on_empty_activity():
    features = _base_features(
        count=120,
        bar_range=0.01,
        volume=100.0,
        delta=0.0,
        oi_change=0.0,
        liq_total=0.0,
        close_location=0.5,
    )

    report = build_day_regime_report(
        features_df=features,
        events_df=pd.DataFrame(columns=["Timestamp", "EventType"]),
        setups_df=pd.DataFrame(columns=["SetupBarTs", "SetupType"]),
        shortlist_df=pd.DataFrame(),
        research_summary_df=pd.DataFrame(columns=["FormalizationEligible"]),
    )

    row = report.iloc[0]
    assert row["PhaseHeuristicLabel"] == "UNCLASSIFIED"


def test_day_regime_report_basic_movement_classification_sanity():
    features = _base_features(
        count=120,
        bar_range=0.4,
        volume=100.0,
        delta=260.0,
        oi_change=100.0,
        liq_total=90.0,
        close_location=0.85,
    )

    event_rows = [
        {"Timestamp": pd.Timestamp("2025-01-01T00:01:00Z"), "EventType": "SWEEP_UP"},
        {"Timestamp": pd.Timestamp("2025-01-01T00:02:00Z"), "EventType": "FAILED_BREAK_UP"},
    ]
    for minute in range(3, 14):
        event_rows.append(
            {"Timestamp": pd.Timestamp("2025-01-01T00:%02d:00Z" % minute), "EventType": "SWEEP_UP"}
        )

    setup_rows = []
    for idx in range(5):
        setup_rows.append(
            {
                "SetupBarTs": pd.Timestamp("2025-01-01T00:%02d:00Z" % (10 + idx)),
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
            }
        )

    report = build_day_regime_report(
        features_df=features,
        events_df=pd.DataFrame(event_rows),
        setups_df=pd.DataFrame(setup_rows),
        shortlist_df=pd.DataFrame([{"x": 1}]),
        research_summary_df=pd.DataFrame([{"FormalizationEligible": True}]),
    )

    row = report.iloc[0]
    assert row["EventDensityClass"] == "HIGH"
    assert row["RangeExpansionClass"] == "EXPANDED"
    assert row["FlowStressClass"] == "HIGH_STRESS"
    assert row["PhaseHeuristicLabel"] == "MOVEMENT"


def test_pipeline_day_regime_report_is_deterministic_for_same_input(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    run(fixture, out_a)
    run(fixture, out_b)

    content_a = (out_a / "analyzer_day_regime_report.csv").read_text(encoding="utf-8")
    content_b = (out_b / "analyzer_day_regime_report.csv").read_text(encoding="utf-8")

    assert content_a == content_b
