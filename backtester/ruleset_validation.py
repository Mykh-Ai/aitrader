"""Phase 4 deterministic ruleset validation gate for Phase 3 mapping artifacts.

Baseline contract: for PHASE3_MAPPING_ONLY this gate is intentionally strict and binary
(VALID/INVALID). REVIEW_REQUIRED is reserved for future policy extensions;
WarningCount/Notes are retained as compatibility placeholders.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

SUMMARY_COLUMNS = [
    "RulesetId",
    "ValidationStatus",
    "IsReplayEligible",
    "MappingStatusObserved",
    "ReplayIntegrationStatusObserved",
    "ReplaySemanticsVersionObserved",
    "ErrorCount",
    "WarningCount",
    "Notes",
]

DETAIL_COLUMNS = [
    "RulesetId",
    "CheckCategory",
    "CheckName",
    "CheckStatus",
    "ObservedValue",
    "ExpectedValue",
    "Message",
]

VALIDATION_STATUS_VALID = "VALID"
VALIDATION_STATUS_INVALID = "INVALID"
VALIDATION_STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"  # reserved, not emitted in current baseline

_CHECK_PASS = "PASS"
_CHECK_FAIL = "FAIL"
_CHECK_WARN = "WARN"

_REQUIRED_MAPPING_COLUMNS = {
    "RulesetId",
    "SetupFamily",
    "Direction",
    "EligibleEventTypes",
    "ReplaySemanticsVersion",
    "EntryTriggerMapping",
    "EntryBoundaryMapping",
    "ExitBoundaryMapping",
    "RiskMapping",
    "MappingStatus",
    "ReplayIntegrationStatus",
}

_REQUIRED_EXECUTABLE_FIELDS = [
    "RulesetId",
    "SetupFamily",
    "Direction",
    "EligibleEventTypes",
    "ReplaySemanticsVersion",
    "EntryTriggerMapping",
    "EntryBoundaryMapping",
    "ExitBoundaryMapping",
    "RiskMapping",
]

_CRITICAL_PLACEHOLDER_FIELDS = [
    "ReplaySemanticsVersion",
    "EntryTriggerMapping",
    "EntryBoundaryMapping",
    "ExitBoundaryMapping",
    "RiskMapping",
]

_ALLOWED_MAPPING_STATUS = "READY"
_ALLOWED_INTEGRATION_STATUS = "READY_FOR_BINDING"
_ALLOWED_SEMANTICS = "REPLAY_V0_1"


@dataclass(frozen=True)
class RulesetValidationArtifacts:
    summary: pd.DataFrame
    details: pd.DataFrame


@dataclass(frozen=True)
class _SummaryRow:
    RulesetId: str
    ValidationStatus: str
    IsReplayEligible: bool
    MappingStatusObserved: str
    ReplayIntegrationStatusObserved: str
    ReplaySemanticsVersionObserved: str
    ErrorCount: int
    WarningCount: int
    Notes: str


@dataclass(frozen=True)
class _DetailRow:
    RulesetId: str
    CheckCategory: str
    CheckName: str
    CheckStatus: str
    ObservedValue: str
    ExpectedValue: str
    Message: str


def _stringify(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _is_blank(value: object) -> bool:
    normalized = _stringify(value)
    return normalized == "" or normalized.upper() in {"NULL", "NONE", "NAN"}


def _has_unresolved_marker(value: object) -> bool:
    upper = _stringify(value).upper()
    if upper.startswith("UNRESOLVED_"):
        return True
    if upper.startswith("NOT_YET_"):
        return True
    if upper.startswith("MANUAL_"):
        return True
    return upper in {"TBD", "TODO"}


def _append_detail(details: list[_DetailRow], **kwargs: object) -> None:
    details.append(_DetailRow(**kwargs))


def _candidate_ruleset_ids(mapping_df: pd.DataFrame) -> list[str]:
    if "RulesetId" not in mapping_df.columns:
        return ["<UNKNOWN_RULESET>"]
    ids = sorted({_stringify(v) or "<UNKNOWN_RULESET>" for v in mapping_df["RulesetId"].tolist()})
    return ids or ["<UNKNOWN_RULESET>"]


def validate_phase3_ruleset_mapping(
    *,
    mapping_df: pd.DataFrame,
    contract_df: pd.DataFrame | None = None,
    draft_df: pd.DataFrame | None = None,
) -> RulesetValidationArtifacts:
    details: list[_DetailRow] = []
    missing_columns = sorted(_REQUIRED_MAPPING_COLUMNS - set(mapping_df.columns))

    if missing_columns:
        for ruleset_id in _candidate_ruleset_ids(mapping_df):
            _append_detail(
                details,
                RulesetId=ruleset_id,
                CheckCategory="STRUCTURAL",
                CheckName="required_mapping_columns",
                CheckStatus=_CHECK_FAIL,
                ObservedValue=",".join(sorted(mapping_df.columns)),
                ExpectedValue=",".join(sorted(_REQUIRED_MAPPING_COLUMNS)),
                Message=f"Missing required mapping columns: {missing_columns}",
            )
        summary = [
            _SummaryRow(
                RulesetId=ruleset_id,
                ValidationStatus=VALIDATION_STATUS_INVALID,
                IsReplayEligible=False,
                MappingStatusObserved="",
                ReplayIntegrationStatusObserved="",
                ReplaySemanticsVersionObserved="",
                ErrorCount=1,
                WarningCount=0,
                Notes=f"Missing required mapping columns: {missing_columns}",
            )
            for ruleset_id in _candidate_ruleset_ids(mapping_df)
        ]
        return RulesetValidationArtifacts(
            summary=pd.DataFrame([asdict(row) for row in summary], columns=SUMMARY_COLUMNS),
            details=pd.DataFrame([asdict(row) for row in details], columns=DETAIL_COLUMNS),
        )

    if mapping_df.empty:
        return RulesetValidationArtifacts(
            summary=pd.DataFrame(columns=SUMMARY_COLUMNS),
            details=pd.DataFrame(columns=DETAIL_COLUMNS),
        )

    contract_by_id = {}
    if contract_df is not None and not contract_df.empty and "RulesetId" in contract_df.columns:
        contract_by_id = {k: v.copy() for k, v in contract_df.groupby("RulesetId", dropna=False, sort=False)}

    draft_ids: set[str] = set()
    if draft_df is not None and not draft_df.empty and "RulesetId" in draft_df.columns:
        draft_ids = {_stringify(v) for v in draft_df["RulesetId"].tolist() if _stringify(v)}

    summary_rows: list[_SummaryRow] = []

    for _, row in mapping_df.sort_values(by=["RulesetId"], kind="mergesort").iterrows():
        ruleset_id = _stringify(row.get("RulesetId")) or "<UNKNOWN_RULESET>"
        errors = 0
        warnings = 0
        notes: list[str] = []

        for field in _REQUIRED_EXECUTABLE_FIELDS:
            value = row.get(field)
            if _is_blank(value):
                errors += 1
                _append_detail(
                    details,
                    RulesetId=ruleset_id,
                    CheckCategory="STRUCTURAL",
                    CheckName=f"required_field_{field}",
                    CheckStatus=_CHECK_FAIL,
                    ObservedValue=_stringify(value),
                    ExpectedValue="non-empty",
                    Message=f"Required executable field '{field}' is blank/null-equivalent",
                )

        for field in _CRITICAL_PLACEHOLDER_FIELDS:
            value = row.get(field)
            if _has_unresolved_marker(value):
                errors += 1
                _append_detail(
                    details,
                    RulesetId=ruleset_id,
                    CheckCategory="PLACEHOLDER",
                    CheckName=f"critical_unresolved_{field}",
                    CheckStatus=_CHECK_FAIL,
                    ObservedValue=_stringify(value),
                    ExpectedValue="resolved executable mapping",
                    Message=f"Critical executable field '{field}' contains unresolved marker",
                )

        mapping_status = _stringify(row.get("MappingStatus")).upper()
        if mapping_status != _ALLOWED_MAPPING_STATUS:
            errors += 1
            _append_detail(
                details,
                RulesetId=ruleset_id,
                CheckCategory="READINESS",
                CheckName="mapping_status",
                CheckStatus=_CHECK_FAIL,
                ObservedValue=_stringify(row.get("MappingStatus")),
                ExpectedValue=_ALLOWED_MAPPING_STATUS,
                Message="MappingStatus must be READY for replay eligibility",
            )

        integration_status = _stringify(row.get("ReplayIntegrationStatus")).upper()
        if integration_status != _ALLOWED_INTEGRATION_STATUS:
            errors += 1
            _append_detail(
                details,
                RulesetId=ruleset_id,
                CheckCategory="READINESS",
                CheckName="replay_integration_status",
                CheckStatus=_CHECK_FAIL,
                ObservedValue=_stringify(row.get("ReplayIntegrationStatus")),
                ExpectedValue=_ALLOWED_INTEGRATION_STATUS,
                Message="ReplayIntegrationStatus must be READY_FOR_BINDING for replay eligibility",
            )

        semantics = _stringify(row.get("ReplaySemanticsVersion"))
        if semantics != _ALLOWED_SEMANTICS:
            errors += 1
            _append_detail(
                details,
                RulesetId=ruleset_id,
                CheckCategory="SEMANTICS",
                CheckName="replay_semantics_version",
                CheckStatus=_CHECK_FAIL,
                ObservedValue=semantics,
                ExpectedValue=_ALLOWED_SEMANTICS,
                Message="ReplaySemanticsVersion is not in supported whitelist",
            )

        if contract_by_id:
            matches = contract_by_id.get(row.get("RulesetId"), pd.DataFrame())
            if matches.empty:
                errors += 1
                _append_detail(
                    details,
                    RulesetId=ruleset_id,
                    CheckCategory="INTEGRITY",
                    CheckName="contract_lineage_exists",
                    CheckStatus=_CHECK_FAIL,
                    ObservedValue="missing",
                    ExpectedValue="exactly one matching contract row",
                    Message="Mapping row has no contract lineage",
                )
            elif len(matches.index) > 1:
                errors += 1
                _append_detail(
                    details,
                    RulesetId=ruleset_id,
                    CheckCategory="INTEGRITY",
                    CheckName="contract_lineage_uniqueness",
                    CheckStatus=_CHECK_FAIL,
                    ObservedValue=str(len(matches.index)),
                    ExpectedValue="1",
                    Message="Mapping row has duplicate ambiguous contract lineage",
                )
            else:
                contract_row = matches.iloc[0]
                for field in ("RulesetId", "SetupFamily", "Direction", "EligibleEventTypes"):
                    observed = _stringify(row.get(field))
                    expected = _stringify(contract_row.get(field))
                    if observed != expected:
                        errors += 1
                        _append_detail(
                            details,
                            RulesetId=ruleset_id,
                            CheckCategory="CONTRACT_MAPPING",
                            CheckName=f"{field.lower()}_consistency",
                            CheckStatus=_CHECK_FAIL,
                            ObservedValue=observed,
                            ExpectedValue=expected,
                            Message=f"Mapping '{field}' contradicts contract",
                        )
                if "RulesetContractVersion" in row.index and "RulesetContractVersion" in contract_row.index:
                    observed = _stringify(row.get("RulesetContractVersion"))
                    expected = _stringify(contract_row.get("RulesetContractVersion"))
                    if observed and expected and observed != expected:
                        errors += 1
                        _append_detail(
                            details,
                            RulesetId=ruleset_id,
                            CheckCategory="CONTRACT_MAPPING",
                            CheckName="ruleset_contract_version_consistency",
                            CheckStatus=_CHECK_FAIL,
                            ObservedValue=observed,
                            ExpectedValue=expected,
                            Message="RulesetContractVersion mismatch between mapping and contract",
                        )

        if draft_ids and ruleset_id not in draft_ids:
            errors += 1
            _append_detail(
                details,
                RulesetId=ruleset_id,
                CheckCategory="INTEGRITY",
                CheckName="draft_lineage_exists",
                CheckStatus=_CHECK_FAIL,
                ObservedValue="missing",
                ExpectedValue="RulesetId present in draft artifact",
                Message="Mapping row has no draft lineage",
            )

        if errors == 0 and warnings == 0:
            status = VALIDATION_STATUS_VALID
        elif errors > 0:
            status = VALIDATION_STATUS_INVALID
        else:
            status = VALIDATION_STATUS_REVIEW_REQUIRED

        summary_rows.append(
            _SummaryRow(
                RulesetId=ruleset_id,
                ValidationStatus=status,
                IsReplayEligible=status == VALIDATION_STATUS_VALID,
                MappingStatusObserved=_stringify(row.get("MappingStatus")),
                ReplayIntegrationStatusObserved=_stringify(row.get("ReplayIntegrationStatus")),
                ReplaySemanticsVersionObserved=_stringify(row.get("ReplaySemanticsVersion")),
                ErrorCount=errors,
                WarningCount=warnings,
                Notes="; ".join(notes),
            )
        )

    summary_df = pd.DataFrame([asdict(row) for row in summary_rows], columns=SUMMARY_COLUMNS)
    details_df = pd.DataFrame([asdict(row) for row in details], columns=DETAIL_COLUMNS)
    return RulesetValidationArtifacts(summary=summary_df, details=details_df)


def write_ruleset_validation_csvs(
    *, artifacts: RulesetValidationArtifacts, output_dir: str | Path
) -> tuple[Path, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary_path = root / "phase4_ruleset_validation_summary.csv"
    details_path = root / "phase4_ruleset_validation_details.csv"
    artifacts.summary.to_csv(summary_path, index=False)
    artifacts.details.to_csv(details_path, index=False)
    return summary_path, details_path
