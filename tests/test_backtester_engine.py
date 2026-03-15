from pathlib import Path

import pandas as pd
import pytest

from backtester.engine import (
    ReplayContractError,
    REPLAY_EVENT_COLUMNS,
    ReplayInputs,
    ZeroCostSkeletonModel,
    load_replay_inputs,
    run_replay_engine,
    write_engine_outputs,
)


def _raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Timestamp": "2024-01-01T00:00:00Z",
                "Open": 100.0,
                "High": 101.0,
                "Low": 99.0,
                "Close": 100.5,
                "IsSynthetic": 0,
            },
            {
                "Timestamp": "2024-01-01T00:01:00Z",
                "Open": 101.0,
                "High": 103.0,
                "Low": 99.5,
                "Close": 102.0,
                "IsSynthetic": 0,
            },
            {
                "Timestamp": "2024-01-01T00:02:00Z",
                "Open": 102.0,
                "High": 102.5,
                "Low": 100.0,
                "Close": 101.0,
                "IsSynthetic": 0,
            },
        ]
    )


def _features_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "DummyFeature": 1.0},
            {"Timestamp": "2024-01-01T00:01:00Z", "DummyFeature": 1.1},
            {"Timestamp": "2024-01-01T00:02:00Z", "DummyFeature": 1.2},
        ]
    )


def _setups_df(force_collision: bool = False, force_expiry_close: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": "LONG",
                "DetectedAt": "2024-01-01T00:00:00Z",
                "SetupBarTs": "2024-01-01T00:00:00Z",
                "ReferenceEventType": "FAILED_BREAK_DOWN",
                "ForceSameBarCollision": force_collision,
                "ForceExpiryClose": force_expiry_close,
            }
        ]
    )


def _rulesets_df(cost_model_id: str = "COST_MODEL_ZERO_SKELETON_ONLY") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ruleset_id": "RULESET_001",
                "direction": "LONG",
                "setup_type": "FAILED_BREAK_RECLAIM_LONG",
                "entry_timing": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "entry_price_convention": "NEXT_BAR_OPEN",
                "same_bar_policy_id": "SAME_BAR_CONSERVATIVE_V0_1",
                "expiry_start_semantics": "AFTER_ACTIVATION",
                "stop_model": "STOP_MODEL_PLACEHOLDER",
                "take_profit_model": "TP_MODEL_PLACEHOLDER",
                "cost_model_id": cost_model_id,
                "replay_semantics_version": "REPLAY_V0_1",
            }
        ]
    )


def _inputs(
    force_collision: bool = False,
    force_expiry_close: bool = False,
    cost_model_id: str = "COST_MODEL_ZERO_SKELETON_ONLY",
) -> ReplayInputs:
    return ReplayInputs(
        raw_df=_raw_df(),
        features_df=_features_df(),
        setups_df=_setups_df(force_collision=force_collision, force_expiry_close=force_expiry_close),
        rulesets_df=_rulesets_df(cost_model_id=cost_model_id),
    )


def _cost_models() -> dict[str, ZeroCostSkeletonModel]:
    return {"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()}


def test_determinism_same_input_produces_identical_events_and_stable_ordering():
    first_events, first_manifest = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )
    second_events, second_manifest = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    pd.testing.assert_frame_equal(first_events, second_events)
    assert first_events["event_id"].tolist() == [f"EV_{i:08d}" for i in range(1, len(first_events) + 1)]
    assert first_manifest == second_manifest


def test_bar_driven_causality_event_order_matches_replay_progression_without_posthoc_sort():
    events, _ = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )
    assert events["event_type"].tolist() == [
        "SIGNAL_ACTIONABLE",
        "ENTRY_PENDING",
        "ENTRY_ACTIVATED",
        "STOP_EVALUATED",
        "TARGET_EVALUATED",
        "CLOSE_RESOLVED",
        "EXPIRY_EVALUATED",
    ]


def test_no_lookahead_entry_not_activated_on_signal_bar_under_next_bar_open_contract():
    events, _ = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    signal_ts = pd.Timestamp("2024-01-01T00:00:00Z")
    activation_ts = events.loc[events["event_type"] == "ENTRY_ACTIVATED", "timestamp"].iloc[0]
    assert activation_ts > signal_ts


def test_entry_timing_actionable_signal_bar_t_activates_earliest_at_t_plus_1_open():
    events, _ = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    activation_row = events.loc[events["event_type"] == "ENTRY_ACTIVATED"].iloc[0]
    assert activation_row["timestamp"] == pd.Timestamp("2024-01-01T00:01:00Z")
    assert activation_row["price_raw"] == 101.0


def test_ruleset_enforcement_missing_replay_critical_field_fails_loudly():
    broken = _rulesets_df().drop(columns=["same_bar_policy_id"])
    inputs = ReplayInputs(
        raw_df=_raw_df(),
        features_df=_features_df(),
        setups_df=_setups_df(),
        rulesets_df=broken,
    )

    with pytest.raises(ReplayContractError, match="Missing required columns"):
        run_replay_engine(inputs, cost_models=_cost_models())


def test_cost_model_honesty_no_silent_zero_cost_fallback_for_production_like_id():
    with pytest.raises(ReplayContractError, match="No cost model hook registered"):
        run_replay_engine(
            _inputs(cost_model_id="COST_MODEL_V0_1_BASE"),
            generation_timestamp="2024-01-01T00:00:00+00:00",
            cost_models=_cost_models(),
        )


def test_stop_target_placeholder_safety_no_fake_plus_minus_levels_by_default():
    events, _ = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    stop_row = events.loc[events["event_type"] == "STOP_EVALUATED"].iloc[0]
    target_row = events.loc[events["event_type"] == "TARGET_EVALUATED"].iloc[0]
    assert pd.isna(stop_row["price_raw"])
    assert pd.isna(target_row["price_raw"])
    assert stop_row["notes"] == "stop_evaluation_not_implemented_step2a"
    assert target_row["notes"] == "target_evaluation_not_implemented_step2a"


def test_same_bar_policy_routing_materializes_explicit_outcome_not_notes_only():
    class StopWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "STOP_WINS"

    events, _ = run_replay_engine(
        _inputs(force_collision=True),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
        same_bar_policies={"SAME_BAR_CONSERVATIVE_V0_1": StopWinsPolicy()},
    )

    close_row = events.loc[events["event_type"] == "CLOSE_RESOLVED"].iloc[0]
    assert close_row["state_after"] == "CLOSE_POLICY_ROUTED"
    assert close_row["same_bar_outcome"] == "STOP_WINS"


def test_artifact_boundary_missing_required_analyzer_artifacts_fails_loudly(tmp_path: Path):
    ruleset_path = tmp_path / "rulesets.csv"
    _rulesets_df().to_csv(ruleset_path, index=False)

    with pytest.raises(ReplayContractError, match="Missing required artifact path keys"):
        load_replay_inputs(artifact_paths={"raw": tmp_path / "raw.csv"}, rulesets=ruleset_path)


def test_artifact_boundary_replay_core_does_not_require_shortlist_or_research_summary(tmp_path: Path):
    raw_path = tmp_path / "raw.csv"
    features_path = tmp_path / "features.csv"
    setups_path = tmp_path / "setups.csv"
    rulesets_path = tmp_path / "rulesets.csv"

    _raw_df().to_csv(raw_path, index=False)
    _features_df().to_csv(features_path, index=False)
    _setups_df().to_csv(setups_path, index=False)
    _rulesets_df().to_csv(rulesets_path, index=False)

    loaded = load_replay_inputs(
        artifact_paths={"raw": raw_path, "features": features_path, "setups": setups_path},
        rulesets=rulesets_path,
    )

    assert loaded.events_df is None
    assert loaded.lineage_df is None


def test_manifest_contains_required_metadata_fields():
    _, manifest = run_replay_engine(
        _inputs(),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    assert "artifact_paths" in manifest
    assert "ruleset_ids" in manifest
    assert "replay_semantics_version" in manifest
    assert "cost_model_ids" in manifest
    assert "generated_at_utc" in manifest
    assert "git_commit" in manifest


def test_close_resolved_emits_explicit_structured_fields_for_same_bar_stop():
    class StopWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "STOP_WINS"

    events, _ = run_replay_engine(
        _inputs(force_collision=True),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
        same_bar_policies={"SAME_BAR_CONSERVATIVE_V0_1": StopWinsPolicy()},
    )
    close_row = events.loc[events["event_type"] == "CLOSE_RESOLVED"].iloc[0]
    assert close_row["close_reason"] == "SAME_BAR_STOP_WINS_POLICY"
    assert close_row["close_reason_category"] == "STOP"
    assert close_row["close_resolved"] == True
    assert close_row["same_bar_outcome"] == "STOP_WINS"


def test_close_resolved_emits_explicit_structured_fields_for_same_bar_target():
    class TargetWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "TARGET_WINS"

    events, _ = run_replay_engine(
        _inputs(force_collision=True),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
        same_bar_policies={"SAME_BAR_CONSERVATIVE_V0_1": TargetWinsPolicy()},
    )
    close_row = events.loc[events["event_type"] == "CLOSE_RESOLVED"].iloc[0]
    assert close_row["close_reason"] == "SAME_BAR_TARGET_WINS_POLICY"
    assert close_row["close_reason_category"] == "TARGET"
    assert close_row["close_resolved"] == True


def test_expiry_close_emits_explicit_structured_close_truth():
    events, _ = run_replay_engine(
        _inputs(force_expiry_close=True),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )
    close_row = events.loc[events["event_type"] == "CLOSE_RESOLVED"].iloc[0]
    assert close_row["close_reason"] == "EXPIRY_CLOSE"
    assert close_row["close_reason_category"] == "EXPIRY"
    assert close_row["close_resolved"] == True
    assert close_row["close_price_raw"] == 102.0


def test_same_bar_unresolved_emits_structured_unresolved_not_notes_only():
    class UnresolvedPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "UNRESOLVED"

    events, _ = run_replay_engine(
        _inputs(force_collision=True),
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
        same_bar_policies={"SAME_BAR_CONSERVATIVE_V0_1": UnresolvedPolicy()},
    )
    close_row = events.loc[events["event_type"] == "CLOSE_RESOLVED"].iloc[0]
    assert close_row["close_reason"] == "SAME_BAR_UNRESOLVED"
    assert close_row["close_reason_category"] == "UNRESOLVED"
    assert close_row["close_resolved"] == False


def test_no_eligible_setups_returns_empty_events_with_canonical_schema():
    inputs = ReplayInputs(
        raw_df=_raw_df(),
        features_df=_features_df(),
        setups_df=_setups_df(),
        rulesets_df=_rulesets_df().assign(direction="SHORT"),
    )

    events, _ = run_replay_engine(
        inputs,
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models=_cost_models(),
    )

    assert events.empty
    assert list(events.columns) == list(REPLAY_EVENT_COLUMNS)


def test_write_engine_outputs_persists_header_only_csv_for_empty_events(tmp_path: Path):
    empty_events = pd.DataFrame(columns=["event_type"])
    events_path, manifest_path = write_engine_outputs(
        events_df=empty_events,
        manifest={"generated_at_utc": "2024-01-01T00:00:00+00:00"},
        output_dir=tmp_path,
    )

    written = pd.read_csv(events_path)
    assert written.empty
    assert list(written.columns) == list(REPLAY_EVENT_COLUMNS)
    assert manifest_path.exists()
