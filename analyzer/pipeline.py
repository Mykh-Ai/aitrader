"""Analyzer pipeline entrypoint (Phase 0 wiring)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .absorption import detect_absorption
from .base_metrics import add_base_metrics
from .context_reports import build_setup_context_report
from .day_regime_report import build_day_regime_report
from .events import build_events
from .failed_breaks import detect_failed_breaks
from .impulses import detect_impulses
from .impulse_setups import extract_impulse_setups
from .io import ensure_output_dir, save_dataframe
from .loader import load_raw_csv
from .rankings import build_setup_rankings
from .outcomes import build_setup_outcomes
from .selections import build_setup_selections
from .reports import build_setup_report
from .research_summary import build_research_summary
from .schema import FEATURE_COLUMNS_IMPLEMENTED, REQUIRED_RAW_COLUMNS
from .setups import extract_setup_candidates
from .shortlist_explanations import build_setup_shortlist_explanations
from .shortlists import build_setup_shortlist
from .sweeps import detect_sweeps
from .swings import annotate_swings


def _concat_and_validate_setups(h1_setups: pd.DataFrame, h2_setups: pd.DataFrame) -> pd.DataFrame:
    if h1_setups.empty and h2_setups.empty:
        return h1_setups.copy()
    if h1_setups.empty:
        setups = h2_setups.copy()
    elif h2_setups.empty:
        setups = h1_setups.copy()
    else:
        setups = pd.concat([h1_setups, h2_setups], ignore_index=True, sort=False)
    sort_columns = [
        col for col in ["DetectedAt", "ReferenceEventType", "Direction", "SetupId"]
        if col in setups.columns
    ]
    if sort_columns:
        setups = setups.sort_values(by=sort_columns, kind="mergesort").reset_index(drop=True)
    else:
        setups = setups.reset_index(drop=True)

    duplicate_setup_ids = setups["SetupId"].duplicated(keep=False)
    if duplicate_setup_ids.any():
        dup_ids = sorted(set(setups.loc[duplicate_setup_ids, "SetupId"].astype(str)))
        raise ValueError(f"Expected unique SetupId values after H1+H2 setup concat; duplicates={dup_ids}")

    return setups


def _canonicalize_feature_columns(features: pd.DataFrame) -> pd.DataFrame:
    """Persist analyzer_features.csv in the canonical schema order expected by run_daily."""
    expected_columns = [*REQUIRED_RAW_COLUMNS, *FEATURE_COLUMNS_IMPLEMENTED]
    missing = [col for col in expected_columns if col not in features.columns]
    if missing:
        raise ValueError(f'Missing expected feature columns before save: {missing}')
    return features.loc[:, expected_columns].copy()


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
    features = detect_impulses(features)
    events = build_events(features)
    h1_setups = extract_setup_candidates(features, events)
    h2_setups = extract_impulse_setups(features)
    setups = _concat_and_validate_setups(h1_setups, h2_setups)
    outcomes = build_setup_outcomes(features, setups)
    report = build_setup_report(setups, outcomes)
    context_report = build_setup_context_report(setups, outcomes)
    rankings = build_setup_rankings(report, context_report)
    selections = build_setup_selections(rankings)
    shortlist = build_setup_shortlist(rankings, selections)
    shortlist_explanations = build_setup_shortlist_explanations(shortlist)
    research_summary = build_research_summary(shortlist, shortlist_explanations, setups)
    day_regime_report = build_day_regime_report(features, events, setups, shortlist, research_summary)
    features = _canonicalize_feature_columns(features)

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
    research_summary_path = save_dataframe(research_summary, out_dir / "analyzer_research_summary.csv")
    day_regime_report_path = save_dataframe(day_regime_report, out_dir / "analyzer_day_regime_report.csv")

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
        "research_summary": research_summary,
        "day_regime_report": day_regime_report,
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
        "research_summary_path": research_summary_path,
        "day_regime_report_path": day_regime_report_path,
    }
