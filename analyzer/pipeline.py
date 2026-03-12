"""Analyzer pipeline entrypoint (Phase 0 wiring)."""

from __future__ import annotations

from pathlib import Path

from .absorption import detect_absorption
from .base_metrics import add_base_metrics
from .events import build_events
from .failed_breaks import detect_failed_breaks
from .io import ensure_output_dir, save_dataframe
from .loader import load_raw_csv
from .outcomes import build_setup_outcomes
from .setups import extract_setup_candidates
from .sweeps import detect_sweeps
from .swings import annotate_swings


def run(input_path: str | Path, output_dir: str | Path) -> dict:
    """Run analyzer pipeline and save phase-0 artifacts.

    Returns metadata dictionary with in-memory dataframes and output paths.
    """
    features = load_raw_csv(input_path)
    features = add_base_metrics(features)
    features = annotate_swings(features)
    features = detect_sweeps(features)
    features = detect_failed_breaks(features)
    features = detect_absorption(features)
    events = build_events(features)
    setups = extract_setup_candidates(features, events)
    outcomes = build_setup_outcomes(features, setups)

    out_dir = ensure_output_dir(output_dir)
    features_path = save_dataframe(features, out_dir / "analyzer_features.csv")
    events_path = save_dataframe(events, out_dir / "analyzer_events.csv")
    setups_path = save_dataframe(setups, out_dir / "analyzer_setups.csv")
    outcomes_path = save_dataframe(outcomes, out_dir / "analyzer_setup_outcomes.csv")

    return {
        "features": features,
        "events": events,
        "setups": setups,
        "outcomes": outcomes,
        "features_path": features_path,
        "events_path": events_path,
        "setups_path": setups_path,
        "outcomes_path": outcomes_path,
    }
