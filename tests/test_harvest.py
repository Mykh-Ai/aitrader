from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from analyzer.harvest import (
    FORMALIZATION_CANDIDATE_COLUMNS,
    FORMALIZATION_REVIEW_COLUMNS,
    HARVESTED_CANDIDATE_COLUMNS,
    PHASE3_RULESET_CONTRACT_COLUMNS,
    PHASE3_RULESET_DRAFT_COLUMNS,
    PHASE3_RULESET_MAPPING_COLUMNS,
    build_and_save_phase2_formalization_candidates,
    build_and_save_phase2_formalization_review,
    build_and_save_phase3_ruleset_contract,
    build_and_save_phase3_ruleset_draft,
    build_and_save_phase3_ruleset_mapping,
    build_phase2_formalization_candidates,
    build_phase2_formalization_review,
    build_phase3_ruleset_contract,
    build_phase3_ruleset_draft,
    build_phase3_ruleset_mapping,
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
    assert formalization.iloc[0]["FormalizationStatus"] == "UNDER_REVIEW"
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


def test_build_phase2_formalization_review_extends_single_candidate_with_review_metadata() -> None:
    formalization_candidates = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "DistinctRunCount": 2,
                "OccurrenceCount": 3,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "RankingScoreMean": 0.6,
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
            }
        ]
    )

    review = build_phase2_formalization_review(formalization_candidates)

    assert list(review.columns) == FORMALIZATION_REVIEW_COLUMNS
    assert len(review) == 1
    assert review.iloc[0]["ProposedSetupFamily"] == "FAILED_BREAK_RECLAIM_LONG"
    assert review.iloc[0]["ProposedDirection"] == "LONG"
    assert review.iloc[0]["ProposedEligibleEventTypes"] == "GROUP_TYPE:SetupType"
    assert review.iloc[0]["RuleDraftStatus"] == "NOT_DRAFTED"
    assert review.iloc[0]["OpenQuestions"] == "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW"
    assert review.iloc[0]["NextAction"] == "MANUAL_RULESET_DRAFT"


def test_build_phase2_formalization_review_returns_empty_artifact_when_no_candidate() -> None:
    review = build_phase2_formalization_review(pd.DataFrame(columns=FORMALIZATION_CANDIDATE_COLUMNS))

    assert list(review.columns) == FORMALIZATION_REVIEW_COLUMNS
    assert review.empty


def test_build_and_save_phase2_formalization_review_writes_exactly_one_row(tmp_path: Path) -> None:
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
            }
        ],
    )

    candidate_output = tmp_path / "phase2_formalization_candidates.csv"
    review_output = tmp_path / "phase2_formalization_review.csv"

    build_and_save_phase2_formalization_review(runs_root, candidate_output, review_output)

    written = pd.read_csv(review_output)

    assert list(written.columns) == FORMALIZATION_REVIEW_COLUMNS
    assert len(written) == 1
    assert written.iloc[0]["GroupValue"] == "FAILED_BREAK_RECLAIM_LONG"
    assert written.iloc[0]["RuleDraftStatus"] == "NOT_DRAFTED"


def test_build_phase3_ruleset_draft_materializes_single_explicit_draft_row() -> None:
    review = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "DistinctRunCount": 2,
                "OccurrenceCount": 3,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "RankingScoreMean": 0.6,
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
                "ProposedSetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "ProposedDirection": "LONG",
                "ProposedEligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleDraftStatus": "NOT_DRAFTED",
                "OpenQuestions": "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW",
                "NextAction": "MANUAL_RULESET_DRAFT",
            }
        ]
    )

    draft = build_phase3_ruleset_draft(review)

    assert list(draft.columns) == PHASE3_RULESET_DRAFT_COLUMNS
    assert len(draft) == 1
    row = draft.iloc[0]
    assert row["RulesetDraftId"] == (
        "RULESET_DRAFT::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::DRAFT_V1"
    )
    assert row["RulesetVersion"] == "DRAFT_V1"
    assert row["DraftStatus"] == "DRAFT_CREATED"
    assert row["ExecutableStatus"] == "NOT_EXECUTABLE_YET"
    assert row["SetupFamily"] == "FAILED_BREAK_RECLAIM_LONG"
    assert row["Direction"] == "LONG"
    assert row["EligibleEventTypes"] == "GROUP_TYPE:SetupType"
    assert row["RuleBoundaryStatus"] == "REVIEW_REQUIRED"
    assert row["EntryLogicStatus"] == "NOT_IMPLEMENTED"
    assert row["ExitLogicStatus"] == "NOT_IMPLEMENTED"
    assert row["RiskLogicStatus"] == "NOT_IMPLEMENTED"
    assert row["KnownUnresolvedFields"] == "ENTRY_EXIT_RISK_NOT_DEFINED"
    assert row["ReviewNextAction"] == "MANUAL_RULESET_DRAFT"
    assert row["NextAction"] == "EXPLICIT_RULESET_SPEC_REVIEW"


def test_build_phase3_ruleset_draft_returns_empty_artifact_when_no_review_candidate() -> None:
    draft = build_phase3_ruleset_draft(pd.DataFrame(columns=FORMALIZATION_REVIEW_COLUMNS))

    assert list(draft.columns) == PHASE3_RULESET_DRAFT_COLUMNS
    assert draft.empty


def test_build_phase3_ruleset_draft_preserves_unresolved_safe_defaults() -> None:
    review = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "EventType",
                "GroupValue": "SOMETHING",
                "DistinctRunCount": 2,
                "OccurrenceCount": 2,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-02",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2",
                "RunDates": "2026-01-01;2026-01-02",
                "RankingScoreMean": 0.4,
                "SelectionDecisions": "REVIEW",
                "RankingLabels": "B",
                "ResearchPriorities": "MEDIUM",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
                "ProposedSetupFamily": "UNRESOLVED_SETUP_FAMILY_REVIEW_REQUIRED",
                "ProposedDirection": "UNRESOLVED_DIRECTION_REVIEW_REQUIRED",
                "ProposedEligibleEventTypes": "UNRESOLVED_EVENT_TYPES_REVIEW_REQUIRED",
                "RuleDraftStatus": "NOT_DRAFTED",
                "OpenQuestions": "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW",
                "NextAction": "MANUAL_RULESET_DRAFT",
            }
        ]
    )

    draft = build_phase3_ruleset_draft(review)
    row = draft.iloc[0]

    assert row["SetupFamily"] == "UNRESOLVED_SETUP_FAMILY_REVIEW_REQUIRED"
    assert row["Direction"] == "UNRESOLVED_DIRECTION_REVIEW_REQUIRED"
    assert row["EligibleEventTypes"] == "UNRESOLVED_EVENT_TYPES_REVIEW_REQUIRED"


def test_build_and_save_phase3_ruleset_draft_writes_exactly_one_row(tmp_path: Path) -> None:
    review_path = tmp_path / "phase2_formalization_review.csv"
    output_path = tmp_path / "phase3_ruleset_draft.csv"
    pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "DistinctRunCount": 2,
                "OccurrenceCount": 3,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "RankingScoreMean": 0.6,
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
                "ProposedSetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "ProposedDirection": "LONG",
                "ProposedEligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleDraftStatus": "NOT_DRAFTED",
                "OpenQuestions": "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW",
                "NextAction": "MANUAL_RULESET_DRAFT",
            }
        ]
    ).to_csv(review_path, index=False)

    build_and_save_phase3_ruleset_draft(review_path, output_path)
    written = pd.read_csv(output_path)

    assert list(written.columns) == PHASE3_RULESET_DRAFT_COLUMNS
    assert len(written) == 1
    assert written.iloc[0]["ExecutableStatus"] == "NOT_EXECUTABLE_YET"


def test_build_phase3_ruleset_contract_materializes_single_explicit_contract_row() -> None:
    draft = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "DistinctRunCount": 2,
                "OccurrenceCount": 3,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "RankingScoreMean": 0.6,
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
                "ProposedSetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "ProposedDirection": "LONG",
                "ProposedEligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleDraftStatus": "NOT_DRAFTED",
                "OpenQuestions": "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW",
                "ReviewNextAction": "MANUAL_RULESET_DRAFT",
                "RulesetDraftId": "RULESET_DRAFT::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::DRAFT_V1",
                "RulesetVersion": "DRAFT_V1",
                "DraftStatus": "DRAFT_CREATED",
                "ExecutableStatus": "NOT_EXECUTABLE_YET",
                "SetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "EligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleBoundaryStatus": "REVIEW_REQUIRED",
                "EntryLogicStatus": "NOT_IMPLEMENTED",
                "ExitLogicStatus": "NOT_IMPLEMENTED",
                "RiskLogicStatus": "NOT_IMPLEMENTED",
                "KnownUnresolvedFields": "ENTRY_EXIT_RISK_NOT_DEFINED",
                "NextAction": "EXPLICIT_RULESET_SPEC_REVIEW",
            }
        ]
    )

    contract = build_phase3_ruleset_contract(draft)

    assert list(contract.columns) == PHASE3_RULESET_CONTRACT_COLUMNS
    assert len(contract) == 1
    row = contract.iloc[0]
    assert row["RulesetId"] == "RULESET::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::CONTRACT_V1"
    assert row["RulesetContractVersion"] == "CONTRACT_V1"
    assert row["ContractStatus"] == "PARTIAL"
    assert row["ReplayReadinessStatus"] == "NOT_READY_FOR_REPLAY"
    assert row["SetupFamily"] == "FAILED_BREAK_RECLAIM_LONG"
    assert row["Direction"] == "LONG"
    assert row["EligibleEventTypes"] == "GROUP_TYPE:SetupType"
    assert row["EntryTriggerSpec"] == "NOT_YET_EXPLICIT"
    assert row["EntryBoundarySpec"] == "NOT_YET_EXPLICIT"
    assert row["ExitBoundarySpec"] == "NOT_YET_EXPLICIT"
    assert row["RiskSpec"] == "NOT_YET_EXPLICIT"
    assert row["ContractCompleteness"] == "PARTIAL"
    assert row["KnownUnresolvedContractFields"] == "ENTRY_EXIT_RISK_BOUNDARIES_UNRESOLVED"
    assert row["NextAction"] == "MANUAL_REPLAY_RULE_MAPPING"


def test_build_phase3_ruleset_contract_returns_empty_artifact_when_no_draft() -> None:
    contract = build_phase3_ruleset_contract(pd.DataFrame(columns=PHASE3_RULESET_DRAFT_COLUMNS))

    assert list(contract.columns) == PHASE3_RULESET_CONTRACT_COLUMNS
    assert contract.empty


def test_build_and_save_phase3_ruleset_contract_writes_exactly_one_row(tmp_path: Path) -> None:
    draft_path = tmp_path / "phase3_ruleset_draft.csv"
    output_path = tmp_path / "phase3_ruleset_contract.csv"
    pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "DistinctRunCount": 2,
                "OccurrenceCount": 3,
                "FirstSeenRunDate": "2026-01-01",
                "LastSeenRunDate": "2026-01-03",
                "RankingMethods": "delta_weighted",
                "RunIds": "run_1;run_2;run_3",
                "RunDates": "2026-01-01;2026-01-02;2026-01-03",
                "RankingScoreMean": 0.6,
                "SelectionDecisions": "SELECT",
                "RankingLabels": "A",
                "ResearchPriorities": "HIGH",
                "FormalizationStatus": "UNDER_REVIEW",
                "ReadinessFlag": "REVIEW_REQUIRED",
                "KnownCaveats": "RESEARCH_ONLY_NOT_YET_RULESET",
                "ProposedSetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "ProposedDirection": "LONG",
                "ProposedEligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleDraftStatus": "NOT_DRAFTED",
                "OpenQuestions": "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW",
                "ReviewNextAction": "MANUAL_RULESET_DRAFT",
                "RulesetDraftId": "RULESET_DRAFT::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::DRAFT_V1",
                "RulesetVersion": "DRAFT_V1",
                "DraftStatus": "DRAFT_CREATED",
                "ExecutableStatus": "NOT_EXECUTABLE_YET",
                "SetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "EligibleEventTypes": "GROUP_TYPE:SetupType",
                "RuleBoundaryStatus": "REVIEW_REQUIRED",
                "EntryLogicStatus": "NOT_IMPLEMENTED",
                "ExitLogicStatus": "NOT_IMPLEMENTED",
                "RiskLogicStatus": "NOT_IMPLEMENTED",
                "KnownUnresolvedFields": "ENTRY_EXIT_RISK_NOT_DEFINED",
                "NextAction": "EXPLICIT_RULESET_SPEC_REVIEW",
            }
        ]
    ).to_csv(draft_path, index=False)

    build_and_save_phase3_ruleset_contract(draft_path, output_path)
    written = pd.read_csv(output_path)

    assert list(written.columns) == PHASE3_RULESET_CONTRACT_COLUMNS
    assert len(written) == 1
    assert written.iloc[0]["ReplayReadinessStatus"] == "NOT_READY_FOR_REPLAY"


def test_build_phase3_ruleset_mapping_materializes_single_explicit_mapping_row() -> None:
    contract = pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "RulesetDraftId": "RULESET_DRAFT::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::DRAFT_V1",
                "RulesetVersion": "DRAFT_V1",
                "RulesetId": "RULESET::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::CONTRACT_V1",
                "RulesetContractVersion": "CONTRACT_V1",
                "ContractStatus": "PARTIAL",
                "ReplayReadinessStatus": "NOT_READY_FOR_REPLAY",
                "SetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "EligibleEventTypes": "GROUP_TYPE:SetupType",
                "EntryTriggerSpec": "NOT_YET_EXPLICIT",
                "EntryBoundarySpec": "NOT_YET_EXPLICIT",
                "ExitBoundarySpec": "NOT_YET_EXPLICIT",
                "RiskSpec": "NOT_YET_EXPLICIT",
                "ContractCompleteness": "PARTIAL",
                "KnownUnresolvedContractFields": "ENTRY_EXIT_RISK_BOUNDARIES_UNRESOLVED",
                "NextAction": "MANUAL_REPLAY_RULE_MAPPING",
            }
        ]
    )

    mapping = build_phase3_ruleset_mapping(contract)

    assert list(mapping.columns) == PHASE3_RULESET_MAPPING_COLUMNS
    assert len(mapping) == 1
    row = mapping.iloc[0]
    assert row["RulesetId"] == "RULESET::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::CONTRACT_V1"
    assert row["RulesetContractVersion"] == "CONTRACT_V1"
    assert row["MappingVersion"] == "MAPPING_V1"
    assert row["MappingStatus"] == "PARTIAL"
    assert row["ReplaySemanticsVersion"] == "REPLAY_V0_1"
    assert row["SetupFamily"] == "FAILED_BREAK_RECLAIM_LONG"
    assert row["Direction"] == "LONG"
    assert row["EligibleEventTypes"] == "GROUP_TYPE:SetupType"
    assert row["EntryTriggerMapping"] == "MANUAL_MAPPING_REQUIRED"
    assert row["EntryBoundaryMapping"] == "MANUAL_MAPPING_REQUIRED"
    assert row["ExitBoundaryMapping"] == "MANUAL_MAPPING_REQUIRED"
    assert row["RiskMapping"] == "MANUAL_MAPPING_REQUIRED"
    assert row["ReplayIntegrationStatus"] == "NOT_INTEGRATED"
    assert row["KnownUnresolvedMappings"] == "ENTRY_EXIT_RISK_REPLAY_MAPPING_UNRESOLVED"
    assert row["NextAction"] == "MANUAL_RULESET_TO_REPLAY_BINDING"


def test_build_phase3_ruleset_mapping_returns_empty_artifact_when_no_contract() -> None:
    mapping = build_phase3_ruleset_mapping(pd.DataFrame(columns=PHASE3_RULESET_CONTRACT_COLUMNS))

    assert list(mapping.columns) == PHASE3_RULESET_MAPPING_COLUMNS
    assert mapping.empty


def test_build_and_save_phase3_ruleset_mapping_writes_exactly_one_row(tmp_path: Path) -> None:
    contract_path = tmp_path / "phase3_ruleset_contract.csv"
    output_path = tmp_path / "phase3_ruleset_mapping.csv"
    pd.DataFrame(
        [
            {
                "SourceReport": "setup_report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_LONG",
                "RulesetDraftId": "RULESET_DRAFT::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::DRAFT_V1",
                "RulesetVersion": "DRAFT_V1",
                "RulesetId": "RULESET::setup_report::SetupType::FAILED_BREAK_RECLAIM_LONG::CONTRACT_V1",
                "RulesetContractVersion": "CONTRACT_V1",
                "ContractStatus": "PARTIAL",
                "ReplayReadinessStatus": "NOT_READY_FOR_REPLAY",
                "SetupFamily": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "EligibleEventTypes": "GROUP_TYPE:SetupType",
                "EntryTriggerSpec": "NOT_YET_EXPLICIT",
                "EntryBoundarySpec": "NOT_YET_EXPLICIT",
                "ExitBoundarySpec": "NOT_YET_EXPLICIT",
                "RiskSpec": "NOT_YET_EXPLICIT",
                "ContractCompleteness": "PARTIAL",
                "KnownUnresolvedContractFields": "ENTRY_EXIT_RISK_BOUNDARIES_UNRESOLVED",
                "NextAction": "MANUAL_REPLAY_RULE_MAPPING",
            }
        ]
    ).to_csv(contract_path, index=False)

    build_and_save_phase3_ruleset_mapping(contract_path, output_path)
    written = pd.read_csv(output_path)

    assert list(written.columns) == PHASE3_RULESET_MAPPING_COLUMNS
    assert len(written) == 1
    assert written.iloc[0]["ReplayIntegrationStatus"] == "NOT_INTEGRATED"
