"""Multi-run harvesting of Phase 2 research candidates.

Будує deterministic агрегований шар поверх canonical Analyzer run директорій,
використовуючи лише analyzer_research_summary.csv як source surface.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RESEARCH_SUMMARY_ARTIFACT = "analyzer_research_summary.csv"
RUN_MANIFEST = "run_manifest.json"

HARVEST_SOURCE_COLUMNS = [
    "RunId",
    "RunDate",
    "AnalyzerVersion",
    "ArtifactContractVersion",
    "RankingMethod",
    "InputRawDate",
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SelectionDecision",
    "RankingLabel",
    "RankingScore",
    "ResearchPriority",
]

HARVESTED_CANDIDATE_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "OccurrenceCount",
    "DistinctRunCount",
    "FirstSeenRunDate",
    "LastSeenRunDate",
    "StableLead",
    "RankingScoreMean",
    "RunIds",
    "RunDates",
    "AnalyzerVersions",
    "ArtifactContractVersions",
    "RankingMethods",
    "InputRawDates",
    "SelectionDecisions",
    "RankingLabels",
    "ResearchPriorities",
]

FORMALIZATION_CANDIDATE_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "DistinctRunCount",
    "OccurrenceCount",
    "FirstSeenRunDate",
    "LastSeenRunDate",
    "RankingMethods",
    "RunIds",
    "RunDates",
    "RankingScoreMean",
    "SelectionDecisions",
    "RankingLabels",
    "ResearchPriorities",
    "FormalizationStatus",
    "ReadinessFlag",
    "KnownCaveats",
]

FORMALIZATION_REVIEW_COLUMNS = [
    *FORMALIZATION_CANDIDATE_COLUMNS,
    "ProposedSetupFamily",
    "ProposedDirection",
    "ProposedEligibleEventTypes",
    "RuleDraftStatus",
    "OpenQuestions",
    "NextAction",
]

PHASE3_RULESET_DRAFT_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "DistinctRunCount",
    "OccurrenceCount",
    "FirstSeenRunDate",
    "LastSeenRunDate",
    "RankingMethods",
    "RunIds",
    "RunDates",
    "RankingScoreMean",
    "SelectionDecisions",
    "RankingLabels",
    "ResearchPriorities",
    "FormalizationStatus",
    "ReadinessFlag",
    "KnownCaveats",
    "ProposedSetupFamily",
    "ProposedDirection",
    "ProposedEligibleEventTypes",
    "RuleDraftStatus",
    "OpenQuestions",
    "ReviewNextAction",
    "RulesetDraftId",
    "RulesetVersion",
    "DraftStatus",
    "ExecutableStatus",
    "SetupFamily",
    "Direction",
    "EligibleEventTypes",
    "RuleBoundaryStatus",
    "EntryLogicStatus",
    "ExitLogicStatus",
    "RiskLogicStatus",
    "KnownUnresolvedFields",
    "NextAction",
]

PHASE3_RULESET_CONTRACT_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "RulesetDraftId",
    "RulesetVersion",
    "RulesetId",
    "RulesetContractVersion",
    "ContractStatus",
    "ReplayReadinessStatus",
    "SetupFamily",
    "Direction",
    "EligibleEventTypes",
    "EntryTriggerSpec",
    "EntryBoundarySpec",
    "ExitBoundarySpec",
    "RiskSpec",
    "ContractCompleteness",
    "KnownUnresolvedContractFields",
    "NextAction",
]

PHASE3_RULESET_MAPPING_COLUMNS = [
    "SourceReport",
    "GroupType",
    "GroupValue",
    "RulesetId",
    "RulesetContractVersion",
    "MappingVersion",
    "MappingStatus",
    "ReplaySemanticsVersion",
    "SetupFamily",
    "Direction",
    "EligibleEventTypes",
    "EntryTriggerMapping",
    "EntryBoundaryMapping",
    "ExitBoundaryMapping",
    "RiskMapping",
    "ReplayIntegrationStatus",
    "KnownUnresolvedMappings",
c
RULE_DRAFT_STATUS_NOT_DRAFTED = "NOT_DRAFTED"
OPEN_QUESTIONS_RULE_BOUNDARY_REVIEW = "NEED_EXPLICIT_RULE_BOUNDARY_REVIEW"
NEXT_ACTION_MANUAL_RULESET_DRAFT = "MANUAL_RULESET_DRAFT"

RULESET_VERSION_DRAFT_V1 = "DRAFT_V1"
RULESET_DRAFT_STATUS_CREATED = "DRAFT_CREATED"
RULESET_EXECUTABLE_STATUS_NOT_READY = "NOT_EXECUTABLE_YET"
RULESET_RULE_BOUNDARY_REVIEW_REQUIRED = "REVIEW_REQUIRED"
RULESET_ENTRY_LOGIC_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
RULESET_EXIT_LOGIC_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
RULESET_RISK_LOGIC_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
RULESET_KNOWN_UNRESOLVED_ENTRY_EXIT_RISK = "ENTRY_EXIT_RISK_NOT_DEFINED"
RULESET_NEXT_ACTION_SPEC_REVIEW = "EXPLICIT_RULESET_SPEC_REVIEW"

RULESET_CONTRACT_VERSION_V1 = "CONTRACT_V1"
RULESET_CONTRACT_STATUS_DEFINED_PARTIAL = "PARTIAL"
RULESET_REPLAY_READINESS_NOT_READY = "NOT_READY_FOR_REPLAY"
RULESET_ENTRY_TRIGGER_SPEC_NOT_EXPLICIT = "NOT_YET_EXPLICIT"
RULESET_ENTRY_BOUNDARY_SPEC_NOT_EXPLICIT = "NOT_YET_EXPLICIT"
RULESET_EXIT_BOUNDARY_SPEC_NOT_EXPLICIT = "NOT_YET_EXPLICIT"
RULESET_RISK_SPEC_NOT_EXPLICIT = "NOT_YET_EXPLICIT"
RULESET_CONTRACT_COMPLETENESS_PARTIAL = "PARTIAL"
RULESET_CONTRACT_UNRESOLVED_ENTRY_EXIT_RISK = "ENTRY_EXIT_RISK_BOUNDARIES_UNRESOLVED"
RULESET_CONTRACT_NEXT_ACTION_MANUAL_REPLAY_MAPPING = "MANUAL_REPLAY_RULE_MAPPING"

RULESET_MAPPING_VERSION_V1 = "MAPPING_V1"
RULESET_MAPPING_STATUS_DEFINED_PARTIAL = "PARTIAL"
RULESET_REPLAY_SEMANTICS_VERSION_V0_1 = "REPLAY_V0_1"
RULESET_ENTRY_TRIGGER_MAPPING_MANUAL_REQUIRED = "MANUAL_MAPPING_REQUIRED"
RULESET_ENTRY_BOUNDARY_MAPPING_MANUAL_REQUIRED = "MANUAL_MAPPING_REQUIRED"
RULESET_EXIT_BOUNDARY_MAPPING_MANUAL_REQUIRED = "MANUAL_MAPPING_REQUIRED"
RULESET_RISK_MAPPING_MANUAL_REQUIRED = "MANUAL_MAPPING_REQUIRED"
RULESET_REPLAY_INTEGRATION_STATUS_NOT_INTEGRATED = "NOT_INTEGRATED"
RULESET_KNOWN_UNRESOLVED_REPLAY_MAPPING = "ENTRY_EXIT_RISK_REPLAY_MAPPING_UNRESOLVED"
RULESET_NEXT_ACTION_MANUAL_REPLAY_BINDING = "MANUAL_RULESET_TO_REPLAY_BINDING"

PROPOSED_SETUP_FAMILY_UNRESOLVED = "UNRESOLVED_SETUP_FAMILY_REVIEW_REQUIRED"
PROPOSED_DIRECTION_UNRESOLVED = "UNRESOLVED_DIRECTION_REVIEW_REQUIRED"

GROUP_KEY_COLUMNS = ["SourceReport", "GroupType", "GroupValue"]


def _join_unique(values: pd.Series) -> str:
    unique = sorted({str(v) for v in values if pd.notna(v) and str(v) != ""})
    return ";".join(unique)


def _discover_run_dirs(runs_root: Path) -> list[Path]:
    return sorted(
        [path for path in runs_root.iterdir() if path.is_dir() and (path / RUN_MANIFEST).is_file()],
        key=lambda path: path.name,
    )


def _load_manifest(run_dir: Path) -> dict:
    with open(run_dir / RUN_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_input_raw_date(manifest: dict) -> str:
    run_date = manifest.get("run_date")
    if run_date:
        return str(run_date)
    raise ValueError("run_manifest.json missing required field: run_date")


def harvest_source_rows(runs_root: str | Path) -> pd.DataFrame:
    """Збирає provenance-heavy source rows з canonical run директорій."""
    root = Path(runs_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"runs_root does not exist or is not a directory: {root}")

    run_dirs = _discover_run_dirs(root)
    if not run_dirs:
        return pd.DataFrame(columns=HARVEST_SOURCE_COLUMNS)

    frames: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        manifest = _load_manifest(run_dir)
        if manifest.get("status") != "SUCCESS":
            continue

        required_manifest_fields = ["run_id", "run_date", "artifact_contract_version"]
        missing_manifest_fields = [field for field in required_manifest_fields if field not in manifest]
        if missing_manifest_fields:
            raise ValueError(
                f"run_manifest.json missing required fields in {run_dir}: {missing_manifest_fields}"
            )

        summary_path = run_dir / RESEARCH_SUMMARY_ARTIFACT
        if not summary_path.exists():
            raise ValueError(f"Missing {RESEARCH_SUMMARY_ARTIFACT} in run dir: {run_dir}")

        summary_df = pd.read_csv(summary_path)

        missing_columns = [col for col in [
            "SourceReport",
            "GroupType",
            "GroupValue",
            "SelectionDecision",
            "RankingLabel",
            "RankingScore",
            "ResearchPriority",
            "RankingMethod",
        ] if col not in summary_df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required research summary columns in {summary_path}: {missing_columns}"
            )

        source_df = pd.DataFrame(
            {
                "RunId": str(manifest.get("run_id", run_dir.name)),
                "RunDate": str(manifest.get("run_date", "")),
                "AnalyzerVersion": str(manifest["analyzer_version"]) if "analyzer_version" in manifest else pd.NA,
                "ArtifactContractVersion": str(manifest["artifact_contract_version"]),
                "RankingMethod": summary_df["RankingMethod"],
                "InputRawDate": _extract_input_raw_date(manifest),
                "SourceReport": summary_df["SourceReport"],
                "GroupType": summary_df["GroupType"],
                "GroupValue": summary_df["GroupValue"],
                "SelectionDecision": summary_df["SelectionDecision"],
                "RankingLabel": summary_df["RankingLabel"],
                "RankingScore": summary_df["RankingScore"],
                "ResearchPriority": summary_df["ResearchPriority"],
            }
        )
        frames.append(source_df)

    if not frames:
        return pd.DataFrame(columns=HARVEST_SOURCE_COLUMNS)

    source_rows = pd.concat(frames, ignore_index=True)
    source_rows = source_rows.sort_values(by=["RunDate", "RunId", *GROUP_KEY_COLUMNS], kind="stable").reset_index(
        drop=True
    )
    return source_rows[HARVEST_SOURCE_COLUMNS]


def build_phase2_harvested_candidates(source_rows: pd.DataFrame) -> pd.DataFrame:
    """Агрегує source rows в phase2_harvested_candidates surface."""
    if source_rows.empty:
        return pd.DataFrame(columns=HARVESTED_CANDIDATE_COLUMNS)

    grouped = source_rows.groupby(GROUP_KEY_COLUMNS, dropna=False, sort=True)
    harvested = grouped.agg(
        OccurrenceCount=("RunId", "size"),
        DistinctRunCount=("RunId", "nunique"),
        FirstSeenRunDate=("RunDate", "min"),
        LastSeenRunDate=("RunDate", "max"),
        RankingScoreMean=("RankingScore", "mean"),
        RunIds=("RunId", _join_unique),
        RunDates=("RunDate", _join_unique),
        AnalyzerVersions=("AnalyzerVersion", _join_unique),
        ArtifactContractVersions=("ArtifactContractVersion", _join_unique),
        RankingMethods=("RankingMethod", _join_unique),
        InputRawDates=("InputRawDate", _join_unique),
        SelectionDecisions=("SelectionDecision", _join_unique),
        RankingLabels=("RankingLabel", _join_unique),
        ResearchPriorities=("ResearchPriority", _join_unique),
    ).reset_index()

    harvested["RankingScoreMean"] = harvested["RankingScoreMean"].astype(float)
    harvested["StableLead"] = harvested["DistinctRunCount"] >= 2

    harvested = harvested.sort_values(
        by=["DistinctRunCount", "OccurrenceCount", "SourceReport", "GroupType", "GroupValue"],
        ascending=[False, False, True, True, True],
        kind="stable",
    ).reset_index(drop=True)
    return harvested[HARVESTED_CANDIDATE_COLUMNS]


def harvest_phase2_candidates(runs_root: str | Path, output_path: str | Path) -> Path:
    """Збирає source rows з runs_root та зберігає aggregated CSV."""
    source_rows = harvest_source_rows(runs_root)
    harvested = build_phase2_harvested_candidates(source_rows)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    harvested.to_csv(output, index=False)
    return output


def build_phase2_formalization_candidates(harvested: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic single-candidate handoff surface for P3 formalization review."""
    if harvested.empty:
        return pd.DataFrame(columns=FORMALIZATION_CANDIDATE_COLUMNS)

    stable_leads = harvested.loc[harvested["StableLead"] == True].copy()  # noqa: E712
    if stable_leads.empty:
        return pd.DataFrame(columns=FORMALIZATION_CANDIDATE_COLUMNS)

    selected = stable_leads.sort_values(
        by=["DistinctRunCount", "OccurrenceCount", "SourceReport", "GroupType", "GroupValue"],
        ascending=[False, False, True, True, True],
        kind="stable",
    ).head(1)

    selected = selected.assign(
        FormalizationStatus=FORMALIZATION_STATUS_UNDER_REVIEW,
        ReadinessFlag=FORMALIZATION_READINESS_REVIEW_REQUIRED,
        KnownCaveats=FORMALIZATION_CAVEAT_RESEARCH_ONLY,
    )
    return selected[FORMALIZATION_CANDIDATE_COLUMNS].reset_index(drop=True)


def build_and_save_phase2_formalization_candidates(
    runs_root: str | Path, output_path: str | Path
) -> Path:
    """Harvest and materialize a single deterministic formalization candidate CSV."""
    source_rows = harvest_source_rows(runs_root)
    harvested = build_phase2_harvested_candidates(source_rows)
    formalization_candidates = build_phase2_formalization_candidates(harvested)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    formalization_candidates.to_csv(output, index=False)
    return output


def _derive_proposed_setup_family(candidate: pd.Series) -> str:
    if candidate.get("GroupType") == "SetupType":
        group_value = candidate.get("GroupValue")
        if pd.notna(group_value) and str(group_value) != "":
            return str(group_value)
    return PROPOSED_SETUP_FAMILY_UNRESOLVED


def _derive_proposed_direction(candidate: pd.Series) -> str:
    group_value = str(candidate.get("GroupValue", ""))
    if group_value.endswith("_LONG"):
        return "LONG"
    if group_value.endswith("_SHORT"):
        return "SHORT"
    return PROPOSED_DIRECTION_UNRESOLVED


def _derive_proposed_eligible_event_types(candidate: pd.Series) -> str:
    group_type = candidate.get("GroupType")
    if pd.notna(group_type) and str(group_type) != "":
        return f"GROUP_TYPE:{group_type}"
    return "UNRESOLVED_EVENT_TYPES_REVIEW_REQUIRED"


def build_phase2_formalization_review(formalization_candidates: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic single-row formalization review surface from nominated candidate CSV data."""
    if formalization_candidates.empty:
        return pd.DataFrame(columns=FORMALIZATION_REVIEW_COLUMNS)

    selected = formalization_candidates.head(1).copy()
    candidate = selected.iloc[0]
    selected = selected.assign(
        ProposedSetupFamily=_derive_proposed_setup_family(candidate),
        ProposedDirection=_derive_proposed_direction(candidate),
        ProposedEligibleEventTypes=_derive_proposed_eligible_event_types(candidate),
        RuleDraftStatus=RULE_DRAFT_STATUS_NOT_DRAFTED,
        OpenQuestions=OPEN_QUESTIONS_RULE_BOUNDARY_REVIEW,
        NextAction=NEXT_ACTION_MANUAL_RULESET_DRAFT,
    )
    return selected[FORMALIZATION_REVIEW_COLUMNS].reset_index(drop=True)


def build_and_save_phase2_formalization_review(
    runs_root: str | Path,
    candidate_output_path: str | Path,
    review_output_path: str | Path,
) -> Path:
    """Materialize deterministic single-candidate review CSV from the formalization-candidate surface."""
    candidate_path = build_and_save_phase2_formalization_candidates(runs_root, candidate_output_path)
    formalization_candidates = pd.read_csv(candidate_path)
    formalization_review = build_phase2_formalization_review(formalization_candidates)

    output = Path(review_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    formalization_review.to_csv(output, index=False)
    return output


def _derive_ruleset_draft_id(review_row: pd.Series) -> str:
    return (
        f"RULESET_DRAFT::{review_row.get('SourceReport','')}::"
        f"{review_row.get('GroupType','')}::{review_row.get('GroupValue','')}::"
        f"{RULESET_VERSION_DRAFT_V1}"
    )


def _safe_value_or_unresolved(value: object, unresolved_value: str) -> str:
    if pd.isna(value):
        return unresolved_value
    text = str(value)
    if text == "" or text.startswith("UNRESOLVED_"):
        return unresolved_value
    return text


def build_phase3_ruleset_draft(formalization_review: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic single-row Phase 3 ruleset draft surface from formalization review."""
    if formalization_review.empty:
        return pd.DataFrame(columns=PHASE3_RULESET_DRAFT_COLUMNS)

    selected = formalization_review.head(1).copy()
    review_row = selected.iloc[0]

    selected = selected.rename(columns={"NextAction": "ReviewNextAction"}).assign(
        RulesetDraftId=_derive_ruleset_draft_id(review_row),
        RulesetVersion=RULESET_VERSION_DRAFT_V1,
        DraftStatus=RULESET_DRAFT_STATUS_CREATED,
        ExecutableStatus=RULESET_EXECUTABLE_STATUS_NOT_READY,
        SetupFamily=_safe_value_or_unresolved(
            review_row.get("ProposedSetupFamily"), PROPOSED_SETUP_FAMILY_UNRESOLVED
        ),
        Direction=_safe_value_or_unresolved(
            review_row.get("ProposedDirection"), PROPOSED_DIRECTION_UNRESOLVED
        ),
        EligibleEventTypes=_safe_value_or_unresolved(
            review_row.get("ProposedEligibleEventTypes"), "UNRESOLVED_EVENT_TYPES_REVIEW_REQUIRED"
        ),
        RuleBoundaryStatus=RULESET_RULE_BOUNDARY_REVIEW_REQUIRED,
        EntryLogicStatus=RULESET_ENTRY_LOGIC_NOT_IMPLEMENTED,
        ExitLogicStatus=RULESET_EXIT_LOGIC_NOT_IMPLEMENTED,
        RiskLogicStatus=RULESET_RISK_LOGIC_NOT_IMPLEMENTED,
        KnownUnresolvedFields=RULESET_KNOWN_UNRESOLVED_ENTRY_EXIT_RISK,
        NextAction=RULESET_NEXT_ACTION_SPEC_REVIEW,
    )
    return selected[PHASE3_RULESET_DRAFT_COLUMNS].reset_index(drop=True)


def build_and_save_phase3_ruleset_draft(
    formalization_review_path: str | Path,
    ruleset_draft_output_path: str | Path,
) -> Path:
    """Materialize deterministic single-candidate Phase 3 ruleset draft CSV from review artifact."""
    formalization_review = pd.read_csv(formalization_review_path)
    ruleset_draft = build_phase3_ruleset_draft(formalization_review)

    output = Path(ruleset_draft_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ruleset_draft.to_csv(output, index=False)
    return output


def _derive_ruleset_id_from_draft(draft_row: pd.Series) -> str:
    return (
        f"RULESET::{draft_row.get('SourceReport','')}::"
        f"{draft_row.get('GroupType','')}::{draft_row.get('GroupValue','')}::"
        f"{RULESET_CONTRACT_VERSION_V1}"
    )


def build_phase3_ruleset_contract(ruleset_draft: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic single-row Phase 3 ruleset contract from ruleset draft artifact."""
    if ruleset_draft.empty:
        return pd.DataFrame(columns=PHASE3_RULESET_CONTRACT_COLUMNS)

    selected = ruleset_draft.head(1).copy()
    draft_row = selected.iloc[0]

    selected = selected.assign(
        RulesetId=_derive_ruleset_id_from_draft(draft_row),
        RulesetContractVersion=RULESET_CONTRACT_VERSION_V1,
        ContractStatus=RULESET_CONTRACT_STATUS_DEFINED_PARTIAL,
        ReplayReadinessStatus=RULESET_REPLAY_READINESS_NOT_READY,
        EntryTriggerSpec=RULESET_ENTRY_TRIGGER_SPEC_NOT_EXPLICIT,
        EntryBoundarySpec=RULESET_ENTRY_BOUNDARY_SPEC_NOT_EXPLICIT,
        ExitBoundarySpec=RULESET_EXIT_BOUNDARY_SPEC_NOT_EXPLICIT,
        RiskSpec=RULESET_RISK_SPEC_NOT_EXPLICIT,
        ContractCompleteness=RULESET_CONTRACT_COMPLETENESS_PARTIAL,
        KnownUnresolvedContractFields=RULESET_CONTRACT_UNRESOLVED_ENTRY_EXIT_RISK,
        NextAction=RULESET_CONTRACT_NEXT_ACTION_MANUAL_REPLAY_MAPPING,
    )

    return selected[PHASE3_RULESET_CONTRACT_COLUMNS].reset_index(drop=True)


def build_and_save_phase3_ruleset_contract(
    ruleset_draft_path: str | Path,
    ruleset_contract_output_path: str | Path,
) -> Path:
    """Materialize deterministic single-candidate Phase 3 ruleset contract CSV from draft artifact."""
    ruleset_draft = pd.read_csv(ruleset_draft_path)
    ruleset_contract = build_phase3_ruleset_contract(ruleset_draft)

    output = Path(ruleset_contract_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ruleset_contract.to_csv(output, index=False)
    return output


def build_phase3_ruleset_mapping(ruleset_contract: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic single-row Phase 3 replay mapping surface from ruleset contract artifact."""
    if ruleset_contract.empty:
        return pd.DataFrame(columns=PHASE3_RULESET_MAPPING_COLUMNS)

    selected = ruleset_contract.head(1).copy()
    selected = selected.assign(
        MappingVersion=RULESET_MAPPING_VERSION_V1,
        MappingStatus=RULESET_MAPPING_STATUS_DEFINED_PARTIAL,
        ReplaySemanticsVersion=RULESET_REPLAY_SEMANTICS_VERSION_V0_1,
        EntryTriggerMapping=RULESET_ENTRY_TRIGGER_MAPPING_MANUAL_REQUIRED,
        EntryBoundaryMapping=RULESET_ENTRY_BOUNDARY_MAPPING_MANUAL_REQUIRED,
        ExitBoundaryMapping=RULESET_EXIT_BOUNDARY_MAPPING_MANUAL_REQUIRED,
        RiskMapping=RULESET_RISK_MAPPING_MANUAL_REQUIRED,
        ReplayIntegrationStatus=RULESET_REPLAY_INTEGRATION_STATUS_NOT_INTEGRATED,
        KnownUnresolvedMappings=RULESET_KNOWN_UNRESOLVED_REPLAY_MAPPING,
        NextAction=RULESET_NEXT_ACTION_MANUAL_REPLAY_BINDING,
    )
    return selected[PHASE3_RULESET_MAPPING_COLUMNS].reset_index(drop=True)


def build_and_save_phase3_ruleset_mapping(
    ruleset_contract_path: str | Path,
    ruleset_mapping_output_path: str | Path,
) -> Path:
    """Materialize deterministic single-candidate Phase 3 ruleset replay mapping CSV from contract artifact."""
    ruleset_contract = pd.read_csv(ruleset_contract_path)
    ruleset_mapping = build_phase3_ruleset_mapping(ruleset_contract)

    output = Path(ruleset_mapping_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ruleset_mapping.to_csv(output, index=False)
    return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Harvest repeated Phase 2 candidates across canonical analyzer runs."
    )
    parser.add_argument("runs_root", help="Path to parent directory with analyzer run subdirectories")
    parser.add_argument(
        "--output",
        default="phase2_harvested_candidates.csv",
        help="Path to output harvested candidates CSV",
    )
    parser.add_argument(
        "--formalization-output",
        default="phase2_formalization_candidates.csv",
        help="Path to output single-candidate formalization handoff CSV",
    )
    parser.add_argument(
        "--formalization-review-output",
        default="phase2_formalization_review.csv",
        help="Path to output single-candidate formalization review CSV",
    )
    parser.add_argument(
        "--phase3-ruleset-draft-output",
        default="phase3_ruleset_draft.csv",
        help="Path to output single-candidate Phase 3 ruleset draft CSV",
    )
    parser.add_argument(
        "--phase3-ruleset-contract-output",
        default="phase3_ruleset_contract.csv",
        help="Path to output single-candidate Phase 3 ruleset contract CSV",
    )
    parser.add_argument(
        "--phase3-ruleset-mapping-output",
        default="phase3_ruleset_mapping.csv",
        help="Path to output single-candidate Phase 3 ruleset mapping CSV",
    )
    args = parser.parse_args()

    out_path = harvest_phase2_candidates(args.runs_root, args.output)
    formalization_out = build_and_save_phase2_formalization_candidates(
        args.runs_root, args.formalization_output
    )
    formalization_review_out = build_and_save_phase2_formalization_review(
        args.runs_root, args.formalization_output, args.formalization_review_output
    )
    phase3_ruleset_draft_out = build_and_save_phase3_ruleset_draft(
        formalization_review_out, args.phase3_ruleset_draft_output
    )
    phase3_ruleset_contract_out = build_and_save_phase3_ruleset_contract(
        phase3_ruleset_draft_out, args.phase3_ruleset_contract_output
    )
    phase3_ruleset_mapping_out = build_and_save_phase3_ruleset_mapping(
        phase3_ruleset_contract_out, args.phase3_ruleset_mapping_output
    )
    print(f"✅ Harvested candidates saved: {out_path}")
    print(f"✅ Formalization candidates saved: {formalization_out}")
    print(f"✅ Formalization review saved: {formalization_review_out}")
    print(f"✅ Phase 3 ruleset draft saved: {phase3_ruleset_draft_out}")
    print(f"✅ Phase 3 ruleset contract saved: {phase3_ruleset_contract_out}")
    print(f"✅ Phase 3 ruleset mapping saved: {phase3_ruleset_mapping_out}")


if __name__ == "__main__":
    main()
