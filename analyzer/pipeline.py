"""Analyzer pipeline entrypoint (Phase 0 wiring)."""

from __future__ import annotations

from pathlib import Path

from .absorption import detect_absorption
from .base_metrics import add_base_metrics
from .context_reports import build_setup_context_report
from .events import build_events
from .failed_breaks import detect_failed_breaks
from .io import ensure_output_dir, save_dataframe
from .loader import load_raw_csv
from .rankings import build_setup_rankings
from .outcomes import build_setup_outcomes
from .selections import build_setup_selections
from .reports import build_setup_report
from .setups import extract_setup_candidates
from .shortlist_explanations import build_setup_shortlist_explanations
from .shortlists import build_setup_shortlist
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
    report = build_setup_report(setups, outcomes)
    context_report = build_setup_context_report(setups, outcomes)
    rankings = build_setup_rankings(report, context_report)
    selections = build_setup_selections(rankings)
    shortlist = build_setup_shortlist(rankings, selections)
    shortlist_explanations = build_setup_shortlist_explanations(shortlist)

    out_dir = ensure_output_dir(output_dir)
    features_path = save_dataframe(features, out_dir / "analyzer_features.csv")
    events_path = save_dataframe(events, out_dir / "analyzer_events.csv")
    setups_path = save_dataframe(setups, out_dir / "analyzer_setups.csv")
    outcomes_path = save_dataframe(outcomes, out_dir / "analyzer_setup_outcomes.csv")
    report_path = save_dataframe(report, out_dir / "analyzer_setup_report.csv")
    context_report_path = save_dataframe(context_report, out_dir / "analyzer_setup_context_report.csv")
    rankings_path = save_dataframe(rankings, out_dir / "analyzer_setup_rankings.csv")
    selections_path = save_dataframe(selections, out_dir / "analyzer_setup_selections.csv")
    shortlist_path = save_dataframe(shortlist, out_dir / "analyzer_setup_shortlist.csv")
    shortlist_explanations_path = save_dataframe(
        shortlist_explanations,
        out_dir / "analyzer_setup_shortlist_explanations.csv",
    )

    return {
        "features": features,
        "events": events,
        "setups": setups,
        "outcomes": outcomes,
        "report": report,
        "context_report": context_report,
        "rankings": rankings,
        "selections": selections,
        "shortlist": shortlist,
        "shortlist_explanations": shortlist_explanations,
        "features_path": features_path,
        "events_path": events_path,
        "setups_path": setups_path,
        "outcomes_path": outcomes_path,
        "report_path": report_path,
        "context_report_path": context_report_path,
        "rankings_path": rankings_path,
        "selections_path": selections_path,
        "shortlist_path": shortlist_path,
        "shortlist_explanations_path": shortlist_explanations_path,
    }
