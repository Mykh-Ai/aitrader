from __future__ import annotations

from pathlib import Path

import pandas as pd

from analyzer.absorption import detect_absorption
from analyzer.base_metrics import add_base_metrics
from analyzer.events import build_events
from analyzer.failed_breaks import detect_failed_breaks
from analyzer.impulses import IMPULSE_FEATURE_COLUMNS, detect_impulses
from analyzer.loader import load_raw_csv
from analyzer.pipeline import run
from analyzer.sweeps import detect_sweeps
from analyzer.swings import annotate_swings


def _base_features() -> pd.DataFrame:
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"
    df = load_raw_csv(fixture)
    df = add_base_metrics(df)
    df = annotate_swings(df)
    df = detect_sweeps(df)
    df = detect_failed_breaks(df)
    df = detect_absorption(df)
    return df


def test_impulse_detector_is_deterministic_for_same_input():
    features = _base_features()

    out1 = detect_impulses(features)
    out2 = detect_impulses(features)

    pd.testing.assert_frame_equal(out1[IMPULSE_FEATURE_COLUMNS], out2[IMPULSE_FEATURE_COLUMNS])


def test_impulse_detector_has_no_forward_dependency_for_existing_prefix():
    features = _base_features()

    baseline = detect_impulses(features)

    last_ts = pd.to_datetime(features["Timestamp"], utc=True).max()
    extra = features.tail(2).copy()
    extra["Timestamp"] = [
        last_ts + pd.Timedelta(minutes=1),
        last_ts + pd.Timedelta(minutes=2),
    ]
    extra["BarRange"] = [500.0, 400.0]
    extra["RelVolume_20"] = [3.0, 2.8]
    extra["DeltaAbsRatio_20"] = [3.0, 2.7]
    extra["OIChangeAbsRatio_20"] = [3.0, 2.7]
    extra["CtxLiqSpike_v1"] = [True, True]
    extra["Close"] = extra["Open"] + 50.0
    extra["CloseLocation"] = 0.9

    extended = pd.concat([features, extra], ignore_index=True)
    extended_out = detect_impulses(extended)

    pd.testing.assert_frame_equal(
        baseline[IMPULSE_FEATURE_COLUMNS].reset_index(drop=True),
        extended_out.loc[: len(features) - 1, IMPULSE_FEATURE_COLUMNS].reset_index(drop=True),
    )


def test_impulse_direction_and_ambiguous_bar_behavior():
    df = pd.DataFrame(
        {
            "BarRange": [10.0, 10.0, 60.0, 120.0, 30.0],
            "RelVolume_20": [1.0, 1.0, 2.0, 2.0, 2.0],
            "DeltaAbsRatio_20": [1.0, 1.0, 2.0, 2.0, 2.0],
            "OIChangeAbsRatio_20": [1.0, 1.0, 2.0, 2.0, 2.0],
            "CtxLiqSpike_v1": [False, False, True, True, True],
            "Close": [100.0, 100.0, 130.0, 70.0, 100.0],
            "Open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "CloseLocation": [0.5, 0.5, 0.8, 0.2, 0.5],
            "High": [101.0, 101.0, 131.0, 101.0, 101.0],
            "Low": [99.0, 99.0, 99.0, 69.0, 99.0],
            "VWAP": [100.0, 100.0, 120.0, 80.0, 100.0],
        }
    )

    out = detect_impulses(df)

    assert bool(out.loc[2, "ImpulseDetected_v1"]) is True
    assert out.loc[2, "ImpulseDirection_v1"] == "IMPULSE_UP"

    assert bool(out.loc[3, "ImpulseDetected_v1"]) is True
    assert out.loc[3, "ImpulseDirection_v1"] == "IMPULSE_DOWN"

    assert bool(out.loc[4, "ImpulseDetected_v1"]) is False
    assert pd.isna(out.loc[4, "ImpulseDirection_v1"])
    assert pd.isna(out.loc[4, "ImpulseAnchorHigh_v1"])


def test_impulse_cooldown_blocks_same_direction_within_window():
    rows = 30
    bar_range = [10.0] * rows
    for idx in [2, 5, 15, 17, 28]:
        bar_range[idx] = 60.0

    df = pd.DataFrame(
        {
            "BarRange": bar_range,
            "RelVolume_20": [2.0] * rows,
            "DeltaAbsRatio_20": [2.0] * rows,
            "OIChangeAbsRatio_20": [2.0] * rows,
            "CtxLiqSpike_v1": [True] * rows,
            "Close": [120.0] * rows,
            "Open": [100.0] * rows,
            "CloseLocation": [0.8] * rows,
            "High": [121.0] * rows,
            "Low": [99.0] * rows,
            "VWAP": [110.0] * rows,
        }
    )

    out = detect_impulses(df)
    detected_idx = out.index[out["ImpulseDetected_v1"].fillna(False)].tolist()

    assert detected_idx == [2, 15, 28]
    assert set(out.loc[detected_idx, "ImpulseDirection_v1"]) == {"IMPULSE_UP"}


def test_pipeline_materializes_h2_features_and_does_not_change_events(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv"

    result = run(fixture, tmp_path)

    for col in IMPULSE_FEATURE_COLUMNS:
        assert col in result["features"].columns

    baseline_features = _base_features()
    baseline_events = build_events(baseline_features)

    pd.testing.assert_frame_equal(
        baseline_events.reset_index(drop=True),
        result["events"].reset_index(drop=True),
    )

    assert result["setups"].empty
    assert result["shortlist"].empty
    assert result["research_summary"].empty
