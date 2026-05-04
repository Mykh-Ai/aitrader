"""Research-only bridge from Analyzer sidecar variants to Backtester artifacts."""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from .absorption import detect_absorption
from .base_metrics import add_base_metrics
from .events import build_events
from .failed_breaks import detect_failed_breaks
from .io import ensure_output_dir, save_dataframe
from .loader import load_raw_csv
from .outcomes import build_setup_outcomes_by_horizon
from .research_summary import RESEARCH_SUMMARY_COLUMNS
from .research_variants import (
    FAILED_BREAK_RECLAIM_EXTENDED_V1,
    FailedBreakReclaimVariantConfig,
)
from .schema import REQUIRED_RAW_COLUMNS
from .setups import extract_setup_candidates
from .shortlists import SHORTLIST_COLUMNS
from .sweeps import detect_sweeps
from .swings import annotate_swings


def _eligible_event_type(direction: str) -> str:
    if direction == "LONG":
        return "FAILED_BREAK_DOWN"
    if direction == "SHORT":
        return "FAILED_BREAK_UP"
    raise ValueError(f"Unsupported failed-break/reclaim direction for bridge: {direction}")


def _setup_type_rows(setups: pd.DataFrame, *, variant_id: str) -> list[dict[str, object]]:
    if setups.empty:
        return []

    rows: list[dict[str, object]] = []
    for setup_type, group in setups.groupby("SetupType", sort=True):
        directions = sorted(set(group["Direction"].dropna().astype(str)))
        if len(directions) != 1:
            raise ValueError(
                "Research replay bridge requires one direction per SetupType; "
                f"SetupType={setup_type}, directions={directions}"
            )
        direction = directions[0]
        rows.append(
            {
                "SourceReport": variant_id,
                "GroupType": "SetupType",
                "GroupValue": str(setup_type),
                "Direction": direction,
                "SetupType": str(setup_type),
                "EligibleEventTypes": _eligible_event_type(direction),
                "SampleCount": int(len(group)),
            }
        )
    return rows


def _build_bridge_shortlist(setups: pd.DataFrame, *, variant_id: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rank, row in enumerate(_setup_type_rows(setups, variant_id=variant_id), start=1):
        rows.append(
            {
                "ShortlistRank": rank,
                "SourceReport": row["SourceReport"],
                "GroupType": row["GroupType"],
                "GroupValue": row["GroupValue"],
                "SemanticClass": "RESEARCH_BRIDGE_DIRECT",
                "FormalizationPath": "RESEARCH_ONLY_BRIDGE",
                "SampleCount": row["SampleCount"],
                "RankingMethod": "RESEARCH_BRIDGE_DIRECT_SETUPTYPE",
                "RankingScore": 0.0,
                "RankingLabel": "RESEARCH_ONLY",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
                "SelectionDecision": "SELECT",
                "SelectionReason": "FAILED_BREAK_RECLAIM_EXTENDED_V1 replay bridge; not baseline shortlist",
            }
        )

    if not rows:
        return pd.DataFrame(columns=SHORTLIST_COLUMNS)
    return pd.DataFrame(rows, columns=SHORTLIST_COLUMNS)


def _build_bridge_research_summary(setups: pd.DataFrame, *, variant_id: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rank, row in enumerate(_setup_type_rows(setups, variant_id=variant_id), start=1):
        rows.append(
            {
                "ShortlistRank": rank,
                "ResearchPriority": "P1",
                "SourceReport": row["SourceReport"],
                "GroupType": row["GroupType"],
                "GroupValue": row["GroupValue"],
                "SampleCount": row["SampleCount"],
                "RankingMethod": "RESEARCH_BRIDGE_DIRECT_SETUPTYPE",
                "RankingScore": 0.0,
                "RankingLabel": "RESEARCH_ONLY",
                "Delta_Mean_CloseReturn_Pct": 0.0,
                "Delta_PositiveCloseReturnRate": 0.0,
                "SelectionDecision": "SELECT",
                "SelectionReason": "FAILED_BREAK_RECLAIM_EXTENDED_V1 replay bridge; not baseline research summary",
                "ScoreBand": "RESEARCH_ONLY",
                "SampleBand": "RESEARCH_ONLY",
                "DeltaDirection": "RESEARCH_ONLY",
                "PositiveRateDirection": "RESEARCH_ONLY",
                "ExplanationCode": "RESEARCH_BRIDGE_DIRECT_SETUPTYPE",
                "OutcomeSemantics": "REPLAY_OUTCOME_ONLY",
                "ConfidenceModelStatus": "RESEARCH_BRIDGE_NO_RANKING",
                "AcceptedBreakSemanticsStatus": "NOT_IMPLEMENTED",
                "ContextFormalizationStatus": "NOT_USED",
                "ExecutableEntrySemanticsStatus": "IMPLEMENTED_IN_BACKTEST_RULESET_V1",
                "FormalizationEligible": True,
                "Direction": row["Direction"],
                "SetupType": row["SetupType"],
                "EligibleEventTypes": row["EligibleEventTypes"],
                "ContextModelVersion": "RESEARCH_BRIDGE",
            }
        )

    if not rows:
        return pd.DataFrame(columns=RESEARCH_SUMMARY_COLUMNS)
    return pd.DataFrame(rows, columns=RESEARCH_SUMMARY_COLUMNS)


def build_failed_break_reclaim_replay_bridge(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    config: FailedBreakReclaimVariantConfig = FAILED_BREAK_RECLAIM_EXTENDED_V1,
) -> dict[str, object]:
    """Write Backtester-compatible artifacts for one failed-break/reclaim research variant.

    This is an explicit research bridge. It creates an isolated artifact directory
    with standard Backtester input filenames, but it does not alter baseline
    Analyzer outputs, rankings, selections, or research summaries.
    """
    raw = load_raw_csv(input_path)
    features = add_base_metrics(raw)
    features = annotate_swings(features)
    features = detect_sweeps(features)
    features = detect_failed_breaks(features, confirmation_bars=config.confirmation_bars)
    features = detect_absorption(features)
    events = build_events(features)
    setups = extract_setup_candidates(features, events, setup_ttl_bars=config.setup_ttl_bars)
    outcomes = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id=config.variant_id,
        outcome_horizons=config.outcome_horizons,
    )
    shortlist = _build_bridge_shortlist(setups, variant_id=config.variant_id)
    research_summary = _build_bridge_research_summary(setups, variant_id=config.variant_id)

    out_dir = ensure_output_dir(output_dir)
    raw_path = save_dataframe(raw.loc[:, REQUIRED_RAW_COLUMNS], out_dir / "raw.csv")
    features_path = save_dataframe(features, out_dir / "analyzer_features.csv")
    events_path = save_dataframe(events, out_dir / "analyzer_events.csv")
    setups_path = save_dataframe(setups, out_dir / "analyzer_setups.csv")
    shortlist_path = save_dataframe(shortlist, out_dir / "analyzer_setup_shortlist.csv")
    research_summary_path = save_dataframe(research_summary, out_dir / "analyzer_research_summary.csv")

    sidecar_dir = ensure_output_dir(out_dir / config.artifact_namespace)
    outcomes_path = save_dataframe(outcomes, sidecar_dir / "analyzer_setup_outcomes_by_horizon.csv")

    manifest = {
        "bridge_type": "FAILED_BREAK_RECLAIM_RESEARCH_REPLAY_BRIDGE",
        "research_only": True,
        "variant_id": config.variant_id,
        "confirmation_bars": config.confirmation_bars,
        "setup_ttl_bars": config.setup_ttl_bars,
        "outcome_horizons": list(config.outcome_horizons),
        "input_path": str(input_path),
        "notes": [
            "Backtester-compatible artifact bridge only",
            "does not alter baseline Analyzer artifacts",
            "does not feed baseline shortlist, research_summary, selections, or promotion",
            "not execution-ready logic",
        ],
    }
    manifest_path = out_dir / "research_replay_bridge_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "variant_id": config.variant_id,
        "artifact_dir": out_dir,
        "raw_path": raw_path,
        "features_path": features_path,
        "events_path": events_path,
        "setups_path": setups_path,
        "shortlist_path": shortlist_path,
        "research_summary_path": research_summary_path,
        "outcomes_by_horizon_path": outcomes_path,
        "manifest_path": manifest_path,
        "setups": setups,
        "shortlist": shortlist,
        "research_summary": research_summary,
        "outcomes_by_horizon": outcomes,
    }
