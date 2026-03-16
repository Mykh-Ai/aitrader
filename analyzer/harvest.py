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

FORMALIZATION_STATUS_UNDER_REVIEW = "CANDIDATE_UNDER_REVIEW"
FORMALIZATION_READINESS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
FORMALIZATION_CAVEAT_RESEARCH_ONLY = "RESEARCH_ONLY_NOT_YET_RULESET"

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
    args = parser.parse_args()

    out_path = harvest_phase2_candidates(args.runs_root, args.output)
    formalization_out = build_and_save_phase2_formalization_candidates(
        args.runs_root, args.formalization_output
    )
    print(f"✅ Harvested candidates saved: {out_path}")
    print(f"✅ Formalization candidates saved: {formalization_out}")


if __name__ == "__main__":
    main()
