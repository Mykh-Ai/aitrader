import pandas as pd

from backtester.ruleset_validation import validate_phase3_ruleset_mapping


def _mapping_df(**overrides) -> pd.DataFrame:
    row = {
        "SourceReport": "report",
        "GroupType": "SetupType",
        "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
        "RulesetId": "RULESET_1",
        "RulesetContractVersion": "CONTRACT_V1",
        "MappingVersion": "MAPPING_V1",
        "MappingStatus": "READY",
        "ReplaySemanticsVersion": "REPLAY_V0_1",
        "SetupFamily": "FAILED_BREAK_RECLAIM_SHORT",
        "Direction": "SHORT",
        "EligibleEventTypes": "FAILED_BREAK_UP",
        "EntryTriggerMapping": "EXPLICIT_TRIGGER",
        "EntryBoundaryMapping": "EXPLICIT_ENTRY_BOUNDARY",
        "ExitBoundaryMapping": "EXPLICIT_EXIT_BOUNDARY",
        "RiskMapping": "EXPLICIT_RISK",
        "ReplayIntegrationStatus": "READY_FOR_BINDING",
        "KnownUnresolvedMappings": "",
        "NextAction": "",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _contract_df(**overrides) -> pd.DataFrame:
    row = {
        "RulesetId": "RULESET_1",
        "RulesetContractVersion": "CONTRACT_V1",
        "SetupFamily": "FAILED_BREAK_RECLAIM_SHORT",
        "Direction": "SHORT",
        "EligibleEventTypes": "FAILED_BREAK_UP",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_status_gate_fail_partial_and_not_integrated() -> None:
    artifacts = validate_phase3_ruleset_mapping(
        mapping_df=_mapping_df(MappingStatus="PARTIAL", ReplayIntegrationStatus="NOT_INTEGRATED")
    )

    row = artifacts.summary.iloc[0]
    assert row["ValidationStatus"] == "INVALID"
    assert bool(row["IsReplayEligible"]) is False


def test_placeholder_fail_on_critical_field() -> None:
    artifacts = validate_phase3_ruleset_mapping(
        mapping_df=_mapping_df(EntryTriggerMapping="MANUAL_MAPPING_REQUIRED")
    )

    assert artifacts.summary.iloc[0]["ValidationStatus"] == "INVALID"


def test_semantics_whitelist_fail_unknown_version() -> None:
    artifacts = validate_phase3_ruleset_mapping(
        mapping_df=_mapping_df(ReplaySemanticsVersion="REPLAY_V0_2")
    )

    assert artifacts.summary.iloc[0]["ValidationStatus"] == "INVALID"


def test_happy_path_ready_row_passes() -> None:
    artifacts = validate_phase3_ruleset_mapping(mapping_df=_mapping_df())

    row = artifacts.summary.iloc[0]
    assert row["ValidationStatus"] == "VALID"
    assert bool(row["IsReplayEligible"]) is True


def test_contract_mismatch_fail() -> None:
    artifacts = validate_phase3_ruleset_mapping(
        mapping_df=_mapping_df(Direction="LONG"),
        contract_df=_contract_df(Direction="SHORT"),
    )

    assert artifacts.summary.iloc[0]["ValidationStatus"] == "INVALID"


def test_baseline_statuses_are_binary_valid_or_invalid() -> None:
    valid = validate_phase3_ruleset_mapping(mapping_df=_mapping_df())
    invalid = validate_phase3_ruleset_mapping(mapping_df=_mapping_df(MappingStatus="PARTIAL"))

    statuses = {valid.summary.iloc[0]["ValidationStatus"], invalid.summary.iloc[0]["ValidationStatus"]}
    assert statuses == {"VALID", "INVALID"}

