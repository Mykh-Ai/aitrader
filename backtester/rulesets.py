"""Deterministic ruleset formalization layer for Backtester Phase 3 Step 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

import pandas as pd

RULESET_COLUMNS = [
    "ruleset_id",
    "ruleset_version",
    "source_candidate_group",
    "source_selection_status",
    "source_lineage_artifact",
    "ruleset_variant",
    "direction",
    "setup_type",
    "eligible_event_types",
    "entry_trigger",
    "entry_timing",
    "entry_price_convention",
    "max_entry_delay_bars",
    "invalidation_condition",
    "stop_model",
    "take_profit_model",
    "trailing_model",
    "expiry_model",
    "expiry_start_semantics",
    "conflict_policy",
    "position_policy",
    "cost_model_id",
    "same_bar_policy_id",
    "replay_semantics_version",
    "notes",
    "inherited_setup_ttl_bars",
    "inherited_outcome_horizon_bars",
    "inherited_min_selection_score",
    "inherited_min_selection_sample",
]

_REQUIRED_SHORTLIST_COLUMNS = {
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SelectionDecision",
}

_OPTIONAL_RESEARCH_SUMMARY_COLUMNS = {
    "SourceReport",
    "GroupType",
    "GroupValue",
    "SelectionDecision",
}

_VALID_DIRECTIONS = {"LONG", "SHORT", "BOTH"}
_VALID_VARIANT_PATTERN = re.compile(r"^[A-Z0-9_]+$")
_VALID_SELECTION_STATUS = {"SELECT", "REVIEW", "REJECT"}
_VALID_SOURCE_FORMALIZATION_MODES = {
    "SHORTLIST_FIRST",
    "RESEARCH_SUMMARY_FIRST",
    "INTERSECTION",
}
_SUPPORTED_BASELINE_GROUP_TYPES = {"Direction", "SetupType"}


def _filter_formalization_eligible(df: pd.DataFrame) -> pd.DataFrame:
    if "FormalizationEligible" not in df.columns:
        return df

    eligible_mask = df["FormalizationEligible"] == True
    return df.loc[eligible_mask].copy()

_DEFAULT_VARIANTS = ("BASE",)


@dataclass(frozen=True)
class RulesetRow:
    """Typed schema for one fully specified replayable ruleset hypothesis row."""

    ruleset_id: str
    ruleset_version: str
    source_candidate_group: str
    source_selection_status: str
    source_lineage_artifact: str
    ruleset_variant: str
    direction: str
    setup_type: str
    eligible_event_types: str
    entry_trigger: str
    entry_timing: str
    entry_price_convention: str
    max_entry_delay_bars: int
    invalidation_condition: str
    stop_model: str
    take_profit_model: str
    trailing_model: str
    expiry_model: str
    expiry_start_semantics: str
    conflict_policy: str
    position_policy: str
    cost_model_id: str
    same_bar_policy_id: str
    replay_semantics_version: str
    notes: str
    inherited_setup_ttl_bars: int
    inherited_outcome_horizon_bars: int
    inherited_min_selection_score: float
    inherited_min_selection_sample: int


def _empty_rulesets() -> pd.DataFrame:
    return pd.DataFrame(columns=RULESET_COLUMNS)


def _normalize_token(value: str, max_len: int = 56) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").upper()
    token = re.sub(r"_+", "_", token)
    return token[:max_len] if token else "NA"


def _validate_required_columns(df: pd.DataFrame, required_columns: set[str], df_name: str) -> None:
    missing = required_columns - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for backtest ruleset formalization in "
            f"{df_name}: {sorted(missing)}"
        )


def _derive_direction_setup(group_type: str, group_value: str) -> tuple[str, str, str]:
    value = str(group_value)
    upper_value = value.upper()

    if group_type == "Direction":
        if upper_value not in {"LONG", "SHORT"}:
            raise ValueError(f"Unsupported Direction group value for ruleset formalization: {group_value}")
        setup_type = "FAILED_BREAK_RECLAIM"
        event_type = "FAILED_BREAK_DOWN" if upper_value == "LONG" else "FAILED_BREAK_UP"
        return upper_value, setup_type, event_type

    if group_type == "SetupType":
        if upper_value.endswith("_LONG"):
            return "LONG", value, "FAILED_BREAK_DOWN"
        if upper_value.endswith("_SHORT"):
            return "SHORT", value, "FAILED_BREAK_UP"
        return "BOTH", value, "FAILED_BREAK_DOWN|FAILED_BREAK_UP"

    raise ValueError(
        "Cannot derive direction/setup/event mapping from shortlist group without explicit mapping "
        f"for GroupType='{group_type}', GroupValue='{group_value}'. "
        "Provide explicit Direction/SetupType/EligibleEventTypes columns or use supported baseline groups."
    )


def _resolve_row_semantics(
    row: dict,
    *,
    direction_column: str,
    setup_type_column: str,
    eligible_event_types_column: str,
) -> tuple[str, str, str]:
    explicit_direction = row.get(direction_column)
    explicit_setup_type = row.get(setup_type_column)
    explicit_events = row.get(eligible_event_types_column)

    explicit_values = [explicit_direction, explicit_setup_type, explicit_events]
    has_any_explicit = any(pd.notna(v) and str(v).strip() != "" for v in explicit_values)
    has_all_explicit = all(pd.notna(v) and str(v).strip() != "" for v in explicit_values)

    if has_any_explicit and not has_all_explicit:
        raise ValueError(
            "Partial explicit semantics provided. Direction/SetupType/EligibleEventTypes must be either "
            "all present or all absent for fail-loud mapping."
        )

    if has_all_explicit:
        return str(explicit_direction), str(explicit_setup_type), str(explicit_events)

    return _derive_direction_setup(str(row["GroupType"]), str(row["GroupValue"]))


def _is_descriptive_context_group_skip_candidate(row: dict) -> bool:
    group_type = str(row.get("GroupType", ""))
    if group_type in _SUPPORTED_BASELINE_GROUP_TYPES:
        return False

    explicit_direction = row.get("Direction")
    explicit_setup_type = row.get("SetupType")
    explicit_events = row.get("EligibleEventTypes")
    explicit_values = [explicit_direction, explicit_setup_type, explicit_events]
    has_any_explicit = any(pd.notna(v) and str(v).strip() != "" for v in explicit_values)
    return not has_any_explicit


def _build_skip_warning(row: dict, reason: str) -> str:
    return (
        "RULESET_SHORTLIST_ROW_SKIPPED"
        f"|reason={reason}"
        f"|SourceReport={row.get('SourceReport')}"
        f"|GroupType={row.get('GroupType')}"
        f"|GroupValue={row.get('GroupValue')}"
        f"|SelectionDecision={row.get('SelectionDecision')}"
    )


def _family_token(source_report: str, group_type: str, group_value: str) -> str:
    return _normalize_token(f"{source_report}_{group_type}_{group_value}")


def _source_candidate_group(source_report: str, group_type: str, group_value: str) -> str:
    return f"{source_report}|{group_type}|{group_value}"


def _lineage_artifact_for_row(
    shortlist_row: pd.Series,
    research_summary_lookup: dict[tuple[str, str, str], dict] | None,
) -> str:
    if research_summary_lookup is None:
        return "analyzer_setup_shortlist.csv"

    key = (
        str(shortlist_row["SourceReport"]),
        str(shortlist_row["GroupType"]),
        str(shortlist_row["GroupValue"]),
    )
    return "analyzer_research_summary.csv" if key in research_summary_lookup else "analyzer_setup_shortlist.csv"


def build_backtest_rulesets(
    shortlist_df: pd.DataFrame,
    research_summary_df: pd.DataFrame | None = None,
    *,
    ruleset_version: str = "V1",
    variant_names: tuple[str, ...] = _DEFAULT_VARIANTS,
    max_variants_per_candidate: int = 3,
    cost_model_id: str = "COST_MODEL_V0_1_BASE",
    same_bar_policy_id: str = "SAME_BAR_CONSERVATIVE_V0_1",
    replay_semantics_version: str = "REPLAY_V0_1",
    expiry_model: str = "BARS_AFTER_ACTIVATION:12",
    expiry_start_semantics: str = "AFTER_ACTIVATION",
    inherited_setup_ttl_bars: int = 12,
    inherited_outcome_horizon_bars: int = 12,
    inherited_min_selection_score: float = 0.05,
    inherited_min_selection_sample: int = 5,
    source_formalization_mode: str = "SHORTLIST_FIRST",
    direction_column: str = "Direction",
    setup_type_column: str = "SetupType",
    eligible_event_types_column: str = "EligibleEventTypes",
) -> tuple[pd.DataFrame, list[str]]:
    """Map Phase 2 research candidates to deterministic, fully specified ruleset rows."""
    _validate_required_columns(shortlist_df, _REQUIRED_SHORTLIST_COLUMNS, "shortlist_df")

    if research_summary_df is not None:
        _validate_required_columns(
            research_summary_df,
            _OPTIONAL_RESEARCH_SUMMARY_COLUMNS,
            "research_summary_df",
        )

    if source_formalization_mode not in _VALID_SOURCE_FORMALIZATION_MODES:
        raise ValueError(
            "Unsupported source_formalization_mode for ruleset formalization: "
            f"{source_formalization_mode}. Allowed values: {sorted(_VALID_SOURCE_FORMALIZATION_MODES)}"
        )

    if not variant_names:
        raise ValueError("variant_names must contain at least one variant for ruleset formalization")

    normalized_variants = tuple(_normalize_token(variant) for variant in variant_names)
    invalid_variants = [variant for variant in normalized_variants if not _VALID_VARIANT_PATTERN.fullmatch(variant)]
    if invalid_variants:
        raise ValueError(f"Invalid ruleset_variant values: {invalid_variants}")

    if len(normalized_variants) > max_variants_per_candidate:
        raise ValueError(
            "Variant budget exceeded for ruleset formalization: "
            f"{len(normalized_variants)} variants > max_variants_per_candidate={max_variants_per_candidate}"
        )

    if shortlist_df.empty:
        return _empty_rulesets(), []

    shortlist = shortlist_df.copy()

    if source_formalization_mode == "RESEARCH_SUMMARY_FIRST":
        if research_summary_df is None or research_summary_df.empty:
            raise ValueError(
                "source_formalization_mode='RESEARCH_SUMMARY_FIRST' requires non-empty research_summary_df"
            )
        shortlist = research_summary_df.copy()
    elif source_formalization_mode == "INTERSECTION":
        if research_summary_df is None or research_summary_df.empty:
            raise ValueError(
                "source_formalization_mode='INTERSECTION' requires non-empty research_summary_df"
            )
        shortlist = shortlist.merge(
            research_summary_df[["SourceReport", "GroupType", "GroupValue", "SelectionDecision"]],
            on=["SourceReport", "GroupType", "GroupValue", "SelectionDecision"],
            how="inner",
            validate="one_to_one",
        )

    shortlist = _filter_formalization_eligible(shortlist)

    shortlist = shortlist.sort_values(
        by=["SourceReport", "GroupType", "GroupValue", "SelectionDecision"],
        kind="mergesort",
    )

    if shortlist.duplicated(subset=["SourceReport", "GroupType", "GroupValue"], keep=False).any():
        dupes = shortlist.loc[
            shortlist.duplicated(subset=["SourceReport", "GroupType", "GroupValue"], keep=False),
            ["SourceReport", "GroupType", "GroupValue"],
        ].drop_duplicates()
        raise ValueError(
            "Duplicate shortlist candidate groups are not allowed for ruleset formalization: "
            f"{dupes.to_dict('records')}"
        )

    research_lookup = None
    if research_summary_df is not None and not research_summary_df.empty:
        research_lookup = {
            (str(row.SourceReport), str(row.GroupType), str(row.GroupValue)): row._asdict()
            for row in research_summary_df.itertuples(index=False)
        }

    rows: list[RulesetRow] = []
    skipped_warnings: list[str] = []

    for short_row in shortlist.itertuples(index=False):
        source_report = str(short_row.SourceReport)
        group_type = str(short_row.GroupType)
        group_value = str(short_row.GroupValue)
        selection_status = str(short_row.SelectionDecision)

        if selection_status not in _VALID_SELECTION_STATUS:
            raise ValueError(
                "Unsupported SelectionDecision for ruleset formalization: "
                f"{selection_status}. Allowed values: {sorted(_VALID_SELECTION_STATUS)}"
            )

        row_dict = short_row._asdict()
        if _is_descriptive_context_group_skip_candidate(row_dict):
            skipped_warnings.append(
                _build_skip_warning(
                    row_dict,
                    reason="unsupported_group_type_without_explicit_direction_setup_events",
                )
            )
            continue

        direction, setup_type, eligible_events = _resolve_row_semantics(
            row_dict,
            direction_column=direction_column,
            setup_type_column=setup_type_column,
            eligible_event_types_column=eligible_event_types_column,
        )
        family = _family_token(source_report, group_type, group_value)
        source_candidate_group = _source_candidate_group(source_report, group_type, group_value)
        source_lineage_artifact = _lineage_artifact_for_row(pd.Series(short_row._asdict()), research_lookup)

        for variant in normalized_variants:
            ruleset_id = f"RULESET_{family}_{ruleset_version}_{direction}_{variant}"
            row = RulesetRow(
                ruleset_id=ruleset_id,
                ruleset_version=ruleset_version,
                source_candidate_group=source_candidate_group,
                source_selection_status=selection_status,
                source_lineage_artifact=source_lineage_artifact,
                ruleset_variant=variant,
                direction=direction,
                setup_type=setup_type,
                eligible_event_types=eligible_events,
                entry_trigger=(
                    "ANALYZER_CANDIDATE_GROUP_MATCH:"
                    f"SourceReport={source_report};GroupType={group_type};GroupValue={group_value}"
                ),
                entry_timing="SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                entry_price_convention="NEXT_BAR_OPEN",
                # Contract clarification: this is an activation window from signal materialization,
                # not an intrabar fill optimization knob.
                max_entry_delay_bars=1,
                invalidation_condition="SETUP_INVALIDATED_OR_EXPIRED",
                stop_model="REFERENCE_LEVEL_HARD_STOP",
                take_profit_model="FIXED_R_MULTIPLE:1.5",
                trailing_model="NONE",
                expiry_model=expiry_model,
                expiry_start_semantics=expiry_start_semantics,
                conflict_policy="ONE_ACTIVE_POSITION_PER_RULESET",
                position_policy="SINGLE_POSITION_NO_PYRAMID",
                cost_model_id=cost_model_id,
                same_bar_policy_id=same_bar_policy_id,
                replay_semantics_version=replay_semantics_version,
                notes=(
                    "Baseline formalization policy; explicit inherited constants and policy references are "
                    f"materialized in dedicated columns. source_formalization_mode={source_formalization_mode}"
                ),
                inherited_setup_ttl_bars=inherited_setup_ttl_bars,
                inherited_outcome_horizon_bars=inherited_outcome_horizon_bars,
                inherited_min_selection_score=inherited_min_selection_score,
                inherited_min_selection_sample=inherited_min_selection_sample,
            )
            rows.append(row)

    rulesets_df = pd.DataFrame([asdict(row) for row in rows], columns=RULESET_COLUMNS)

    rulesets_df = rulesets_df.sort_values(
        by=["source_candidate_group", "direction", "ruleset_variant", "ruleset_id"],
        kind="mergesort",
    ).reset_index(drop=True)

    warnings = validate_rulesets(
        rulesets_df,
        max_variants_per_candidate=max_variants_per_candidate,
    )
    warnings.extend(skipped_warnings)
    return rulesets_df, warnings


def validate_rulesets(rulesets_df: pd.DataFrame, *, max_variants_per_candidate: int = 3) -> list[str]:
    """Validate ruleset table before save. Raises on hard contract violations."""
    _validate_required_columns(rulesets_df, set(RULESET_COLUMNS), "rulesets_df")

    required_semantic_columns = {
        "entry_timing",
        "entry_price_convention",
        "same_bar_policy_id",
        "expiry_start_semantics",
        "stop_model",
        "take_profit_model",
        "cost_model_id",
        "replay_semantics_version",
    }

    warnings: list[str] = []

    for column in required_semantic_columns:
        if rulesets_df[column].isna().any() or (rulesets_df[column].astype(str).str.strip() == "").any():
            raise ValueError(f"Ruleset validation failed: required semantic column '{column}' contains null/blank")

    duplicated_ids = rulesets_df[rulesets_df["ruleset_id"].duplicated(keep=False)]
    if not duplicated_ids.empty:
        raise ValueError(
            "Ruleset validation failed: duplicate ruleset_id values found: "
            f"{sorted(duplicated_ids['ruleset_id'].unique())}"
        )

    invalid_directions = sorted(set(rulesets_df["direction"]) - _VALID_DIRECTIONS)
    if invalid_directions:
        raise ValueError(
            "Ruleset validation failed: invalid direction values: "
            f"{invalid_directions}. Allowed values: {sorted(_VALID_DIRECTIONS)}"
        )

    invalid_selection_status = sorted(set(rulesets_df["source_selection_status"]) - _VALID_SELECTION_STATUS)
    if invalid_selection_status:
        raise ValueError(
            "Ruleset validation failed: invalid source_selection_status values: "
            f"{invalid_selection_status}. Allowed values: {sorted(_VALID_SELECTION_STATUS)}"
        )

    invalid_variant_names = [
        value
        for value in rulesets_df["ruleset_variant"].astype(str)
        if not _VALID_VARIANT_PATTERN.fullmatch(value)
    ]
    if invalid_variant_names:
        raise ValueError(
            "Ruleset validation failed: invalid ruleset_variant values: "
            f"{sorted(set(invalid_variant_names))}"
        )

    expected_order = rulesets_df.sort_values(
        by=["source_candidate_group", "direction", "ruleset_variant", "ruleset_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    if not expected_order.equals(rulesets_df.reset_index(drop=True)):
        raise ValueError("Ruleset validation failed: row ordering is not deterministic")

    variant_counts = rulesets_df.groupby("source_candidate_group", sort=False)["ruleset_variant"].nunique()
    overloaded = variant_counts[variant_counts > max_variants_per_candidate]
    if not overloaded.empty:
        details = {str(k): int(v) for k, v in overloaded.items()}
        warnings.append(
            "Variant budget warning: candidate groups exceed variant budget "
            f"{max_variants_per_candidate}: {details}"
        )

    weak_lineage = rulesets_df[rulesets_df["source_lineage_artifact"] == "analyzer_setup_shortlist.csv"]
    if not weak_lineage.empty:
        warnings.append(
            "Lineage enrichment warning: some rulesets use shortlist-only lineage without research_summary match"
        )

    placeholder_notes = rulesets_df[rulesets_df["notes"].astype(str).str.contains("TODO|TBD", na=False)]
    if not placeholder_notes.empty:
        warnings.append("Notes warning: placeholder notes found (TODO/TBD)")

    return warnings


def write_backtest_rulesets_csv(rulesets_df: pd.DataFrame, output_path: str | Path) -> Path:
    """Write deterministic full-regeneration backtest_rulesets.csv (UTF-8, stable order)."""
    validate_rulesets(rulesets_df)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rulesets_df.loc[:, RULESET_COLUMNS].to_csv(path, index=False, encoding="utf-8")
    return path
