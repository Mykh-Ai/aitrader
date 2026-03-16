from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from analyzer.harvest import (
    FORMALIZATION_CANDIDATE_COLUMNS,
    HARVESTED_CANDIDATE_COLUMNS,
    build_and_save_phase2_formalization_candidates,
    build_phase2_formalization_candidates,
    harvest_phase2_candidates,
    harvest_source_rows,
)


def _write_run(
    run_dir: Path,
    *,
    run_id: str,
    run_date: str,
    rows: list[dict],
    status: str = "SUCCESS",
    include_analyzer_version: bool = True,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "run_date": run_date,
        "artifact_contract_version": "phase2.analyzer-run.v1",
        "status": status,
    }
    if include_analyzer_version:
        manifest["analyzer_version"] = "abc123"

    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    pd.DataFrame(rows).to_csv(run_dir / "analyzer_research_summary.csv", index=False)


def test_harvest_phase2_candidates_aggregates_repeats_across_runs(tmp_path: Path) -> None:
    runs_root = tmp_path / "analyzer_runs"

    _write_run(
        runs_root / "2026-01-01_to_2026-01-01_run_001",
        run_id="2026-01-01_to_2026-01-01_run_001",
        run_date="2026-01-01",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.55,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            },
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "REVIEW",
                "RankingLabel": "B",
                "RankingScore": 0.22,
                "ResearchPriority": "MEDIUM",
                "RankingMethod": "delta_weighted",
            },
        ],
    )

    _write_run(
        runs_root / "2026-01-02_to_2026-01-02_run_001",
        run_id="2026-01-02_to_2026-01-02_run_001",
        run_date="2026-01-02",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.65,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            }
        ],
    )

    output_path = tmp_path / "phase2_harvested_candidates.csv"
    harvest_phase2_candidates(runs_root, output_path)

    harvested = pd.read_csv(output_path)

    assert list(harvested.columns) == HARVESTED_CANDIDATE_COLUMNS
    assert len(harvested) == 2

    stable_row = harvested.loc[
        (harvested["SourceReport"] == "setup_report")
        & (harvested["GroupType"] == "SetupType")
        & (harvested["GroupValue"] == "FAILED_BREAK_RECLAIM_LONG")
    ].iloc[0]

    assert int(stable_row["OccurrenceCount"]) == 2
    assert int(stable_row["DistinctRunCount"]) == 2
    assert stable_row["FirstSeenRunDate"] == "2026-01-01"
    assert stable_row["LastSeenRunDate"] == "2026-01-02"
    assert bool(stable_row["StableLead"]) is True
    assert float(stable_row["RankingScoreMean"]) == pytest.approx(0.6)


def test_harvest_source_rows_skips_non_success_runs(tmp_path: Path) -> None:
    runs_root = tmp_path / "analyzer_runs"

    _write_run(
        runs_root / "run_success",
        run_id="run_success",
        run_date="2026-01-01",
        status="SUCCESS",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.5,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            }
        ],
    )

    _write_run(
        runs_root / "run_failed",
        run_id="run_failed",
        run_date="2026-01-02",
        status="FAILED",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "REVIEW",
                "RankingLabel": "B",
                "RankingScore": 0.2,
                "ResearchPriority": "LOW",
                "RankingMethod": "delta_weighted",
            }
        ],
    )

    source_rows = harvest_source_rows(runs_root)

    assert len(source_rows) == 1
    assert source_rows.iloc[0]["RunId"] == "run_success"


def test_harvest_source_rows_uses_run_date_as_input_raw_date_without_input_date_range(tmp_path: Path) -> None:
    runs_root = tmp_path / "analyzer_runs"

    _write_run(
        runs_root / "run_success",
        run_id="run_success",
        run_date="2026-01-03",
        include_analyzer_version=False,
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.5,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            }
        ],
    )

    source_rows = harvest_source_rows(runs_root)

    assert len(source_rows) == 1
    assert source_rows.iloc[0]["InputRawDate"] == "2026-01-03"
    assert pd.isna(source_rows.iloc[0]["AnalyzerVersion"])


def test_build_phase2_formalization_candidates_selects_single_deterministic_stable_lead() -> None:
    harvested = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "OccurrenceCount": 2,
                "DistinctRunCount": 2,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-02",
                "StableLead": True,
                "RankingScoreMean": 0.4,
                "RunIds": "run_1;run_2",
                "RunDates": "2026-01-01;2026-01-02",
                "AnalyzerVersions": "abc",
                "ArtifactContractVersions": "phase2.analyzer-run.v1",
                "RankingMethods": "delta_weighted",
                "InputRawDates": "2026-01-01;2026-01-02",
                "SelectionDecisions": "REVIEW",
                "RankingLabels": "B",
                "ResearchPriorities": "MEDIUM",
            },
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "OccurrenceCount": 3,
                "DistinctRunCount": 2,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "StableLead": True,
                "RankingScoreMean": 0.6,
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "AnalyzerVersions": "abc",
                "ArtifactContractVersions": "phase2.analyzer-run.v1",
                "RankingMethods": "delta_weighted",
                "InputRawDates": "2026-01-01;2026-01-02;2026-01-03",
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
            },
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "ABSORPTION_LONG",
                "OccurrenceCount": 5,
                "DistinctRunCount": 1,
                "FirstSeenRunDate": "2026-01-03",
                "LastSeenRunDate": "2026-01-03",
                "StableLead": False,
                "RankingScoreMean": 0.9,
                "RunIds": "run_3",
                "RunDates": "2026-01-03",
                "AnalyzerVersions": "abc",
                "ArtifactContractVersions": "phase2.analyzer-run.v1",
                "RankingMethods": "delta_weighted",
                "InputRawDates": "2026-01-03",
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
            },
        ]
    )

    formalization = build_phase2_formalization_candidates(harvested)

    assert list(formalization.columns) == FORMALIZATION_CANDIDATE_COLUMNS
    assert len(formalization) == 1
    assert formalization.iloc[0]["GroupValue"] == "FAILED_BREAK_RECLAIM_LONG"
    assert formalization.iloc[0]["FormalizationStatus"] == "CANDIDATE_UNDER_REVIEW"
    assert formalization.iloc[0]["ReadinessFlag"] == "REVIEW_REQUIRED"
    assert formalization.iloc[0]["KnownCaveats"] == "RESEARCH_ONLY_NOT_YET_RULESET"


def test_build_and_save_phase2_formalization_candidates_writes_exactly_one_row(tmp_path: Path) -> None:
    runs_root = tmp_path / "analyzer_runs"

    _write_run(
        runs_root / "run_001",
        run_id="run_001",
        run_date="2026-01-01",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.55,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            }
        ],
    )

    _write_run(
        runs_root / "run_002",
        run_id="run_002",
        run_date="2026-01-02",
        rows=[
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "SelectionDecision": "SELECT",
                "RankingLabel": "A",
                "RankingScore": 0.60,
                "ResearchPriority": "HIGH",
                "RankingMethod": "delta_weighted",
            },
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "REVIEW",
                "RankingLabel": "B",
                "RankingScore": 0.30,
                "ResearchPriority": "MEDIUM",
                "RankingMethod": "delta_weighted",
            },
        ],
    )

    output_path = tmp_path / "phase2_formalization_candidates.csv"
    build_and_save_phase2_formalization_candidates(runs_root, output_path)

    written = pd.read_csv(output_path)

    assert list(written.columns) == FORMALIZATION_CANDIDATE_COLUMNS
    assert len(written) == 1
    assert written.iloc[0]["GroupValue"] == "FAILED_BREAK_RECLAIM_LONG"
