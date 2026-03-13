from pathlib import Path

import pandas as pd
import pytest

from backtester.rulesets import (
    RULESET_COLUMNS,
    build_backtest_rulesets,
    validate_rulesets,
    write_backtest_rulesets_csv,
)


def _shortlist_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "SELECT",
            },
            {
                "SourceReport": "report",
                "GroupType": "Direction",
                "GroupValue": "LONG",
                "SelectionDecision": "REVIEW",
            },
        ]
    )


def _research_summary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "SELECT",
                "ResearchPriority": "P1",
            }
        ]
    )


def test_determinism_same_input_produces_identical_rows_and_order_and_ids():
    first, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())
    second, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())

    pd.testing.assert_frame_equal(first, second)
    assert first["ruleset_id"].tolist() == second["ruleset_id"].tolist()


def test_schema_missing_required_field_fails_validation():
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())
    broken = rulesets.drop(columns=["entry_price_convention"])

    with pytest.raises(KeyError, match="Missing required columns"):
        validate_rulesets(broken)


@pytest.mark.parametrize(
    "column",
    ["cost_model_id", "same_bar_policy_id", "replay_semantics_version", "entry_price_convention"],
)
def test_missing_required_semantic_columns_fail(column: str):
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())
    rulesets.loc[0, column] = ""

    with pytest.raises(ValueError, match="required semantic column"):
        validate_rulesets(rulesets)


def test_invalid_enum_value_fails():
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())
    rulesets.loc[0, "direction"] = "INVALID"

    with pytest.raises(ValueError, match="invalid direction"):
        validate_rulesets(rulesets)


def test_lineage_preserves_source_candidate_group_and_primary_artifact_when_available():
    rulesets, warnings = build_backtest_rulesets(_shortlist_df(), _research_summary_df())

    assert "report|SetupType|FAILED_BREAK_RECLAIM_SHORT" in set(rulesets["source_candidate_group"])
    assert "analyzer_research_summary.csv" in set(rulesets["source_lineage_artifact"])
    assert any("shortlist-only lineage" in w for w in warnings)


def test_secondary_lineage_is_optional_for_generation():
    rulesets, warnings = build_backtest_rulesets(_shortlist_df(), None)

    assert not rulesets.empty
    assert "analyzer_setup_shortlist.csv" in set(rulesets["source_lineage_artifact"])
    assert any("shortlist-only lineage" in w for w in warnings)


def test_one_candidate_emits_multiple_deterministic_variants():
    shortlist = _shortlist_df().iloc[[0]].copy()
    rulesets, _ = build_backtest_rulesets(
        shortlist,
        _research_summary_df(),
        variant_names=("BASE", "ALT_ENTRY_01"),
        max_variants_per_candidate=3,
    )

    assert rulesets["ruleset_variant"].tolist() == ["ALT_ENTRY_01", "BASE"]
    assert rulesets["ruleset_id"].tolist() == sorted(rulesets["ruleset_id"].tolist())


def test_variant_proliferation_is_prevented_by_budget_guard():
    with pytest.raises(ValueError, match="Variant budget exceeded"):
        build_backtest_rulesets(
            _shortlist_df().iloc[[0]],
            _research_summary_df(),
            variant_names=("BASE", "ALT_ENTRY_01", "ALT_STOP_01", "ALT_EXPIRY_01"),
            max_variants_per_candidate=3,
        )


def test_generation_with_primary_sources_only_does_not_require_raw_feed_or_features():
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())

    assert list(rulesets.columns) == RULESET_COLUMNS
    assert (rulesets["entry_timing"] == "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN").all()


def test_inheritance_guard_explicitly_encodes_analyzer_lineage_constants():
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())

    assert (rulesets["inherited_setup_ttl_bars"] == 12).all()
    assert (rulesets["inherited_outcome_horizon_bars"] == 12).all()
    assert (rulesets["inherited_min_selection_score"] == 0.05).all()
    assert (rulesets["inherited_min_selection_sample"] == 5).all()


def test_csv_writer_generates_stable_utf8_csv(tmp_path: Path):
    rulesets, _ = build_backtest_rulesets(_shortlist_df(), _research_summary_df())
    output = tmp_path / "backtest_rulesets.csv"

    saved = write_backtest_rulesets_csv(rulesets, output)

    assert saved == output
    reloaded = pd.read_csv(output)
    assert list(reloaded.columns) == RULESET_COLUMNS


def test_research_summary_first_requires_research_summary_input():
    with pytest.raises(ValueError, match="RESEARCH_SUMMARY_FIRST"):
        build_backtest_rulesets(
            _shortlist_df(),
            None,
            source_formalization_mode="RESEARCH_SUMMARY_FIRST",
        )


def test_unknown_group_type_without_explicit_semantics_fails_loudly():
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "UnknownGroup",
                "GroupValue": "X",
                "SelectionDecision": "SELECT",
            }
        ]
    )

    with pytest.raises(ValueError, match="Cannot derive direction/setup/event mapping"):
        build_backtest_rulesets(shortlist, None)


def test_explicit_semantics_columns_override_baseline_mapping():
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": "report",
                "GroupType": "UnknownGroup",
                "GroupValue": "X",
                "SelectionDecision": "SELECT",
                "Direction": "SHORT",
                "SetupType": "FAILED_BREAK_RECLAIM_SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP",
            }
        ]
    )

    rulesets, _ = build_backtest_rulesets(shortlist, None)

    assert rulesets.loc[0, "direction"] == "SHORT"
    assert rulesets.loc[0, "setup_type"] == "FAILED_BREAK_RECLAIM_SHORT"
    assert rulesets.loc[0, "eligible_event_types"] == "FAILED_BREAK_UP"


def test_research_summary_context_group_with_explicit_semantics_is_formalizable():
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
            }
        ]
    )
    research_summary = pd.DataFrame(
        [
            {
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
                "Direction": "BOTH",
                "SetupType": "FAILED_BREAK_RECLAIM",
                "EligibleEventTypes": "FAILED_BREAK_DOWN|FAILED_BREAK_UP",
            }
        ]
    )

    rulesets, _ = build_backtest_rulesets(
        shortlist,
        research_summary,
        source_formalization_mode="RESEARCH_SUMMARY_FIRST",
    )

    assert rulesets.loc[0, "direction"] == "BOTH"
    assert rulesets.loc[0, "setup_type"] == "FAILED_BREAK_RECLAIM"
    assert rulesets.loc[0, "eligible_event_types"] == "FAILED_BREAK_DOWN|FAILED_BREAK_UP"


def test_research_summary_first_filters_non_formalizable_rows_via_flag():
    shortlist = pd.DataFrame(
        [
            {
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
            },
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "SELECT",
            },
        ]
    )
    research_summary = pd.DataFrame(
        [
            {
                "SourceReport": "context_report",
                "GroupType": "AbsorptionScore_v1",
                "GroupValue": "LOW",
                "SelectionDecision": "REVIEW",
                "FormalizationEligible": False,
            },
            {
                "SourceReport": "report",
                "GroupType": "SetupType",
                "GroupValue": "FAILED_BREAK_RECLAIM_SHORT",
                "SelectionDecision": "SELECT",
                "FormalizationEligible": True,
                "Direction": "SHORT",
                "SetupType": "FAILED_BREAK_RECLAIM_SHORT",
                "EligibleEventTypes": "FAILED_BREAK_UP",
            },
        ]
    )

    rulesets, _ = build_backtest_rulesets(
        shortlist,
        research_summary,
        source_formalization_mode="RESEARCH_SUMMARY_FIRST",
    )

    assert len(rulesets) == 1
    assert rulesets.loc[0, "source_candidate_group"] == "report|SetupType|FAILED_BREAK_RECLAIM_SHORT"


def test_notes_are_neutral_and_include_source_mode_not_hardcoded_constants_text():
    rulesets, _ = build_backtest_rulesets(
        _shortlist_df(),
        _research_summary_df(),
        inherited_setup_ttl_bars=99,
    )

    assert "SETUP_TTL_BARS=12" not in rulesets.loc[0, "notes"]
    assert "source_formalization_mode=SHORTLIST_FIRST" in rulesets.loc[0, "notes"]
