import pandas as pd
import pytest

from backtester.engine import ReplayInputs, ZeroCostSkeletonModel, run_replay_engine
from backtester.ledger import build_trade_ledger
from backtester.placement import (
    materialize_stop_target_levels,
)


def _raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Timestamp": "2024-01-01T00:00:00Z", "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "IsSynthetic": 0},
            {"Timestamp": "2024-01-01T00:01:00Z", "Open": 101.0, "High": 102.0, "Low": 100.0, "Close": 101.5, "IsSynthetic": 0},
            {"Timestamp": "2024-01-01T00:02:00Z", "Open": 102.0, "High": 120.0, "Low": 80.0, "Close": 119.0, "IsSynthetic": 0},
        ]
    )


def _setups_df(
    *,
    direction: str = "LONG",
    reference_level: float = 99.0,
    reference_event_anchor_ts: str | None = None,
    sweep_bar_low: float | None = None,
    sweep_bar_high: float | None = None,
) -> pd.DataFrame:
    row = {
        "SetupId": "S1",
        "SetupType": "FAILED_BREAK_RECLAIM_LONG",
        "Direction": direction,
        "DetectedAt": "2024-01-01T00:00:00Z",
        "SetupBarTs": "2024-01-01T00:00:00Z",
        "ReferenceEventType": "FAILED_BREAK_DOWN",
        "ReferenceLevel": reference_level,
    }
    if reference_event_anchor_ts is not None:
        row["ReferenceEventAnchorTs"] = reference_event_anchor_ts
    if sweep_bar_low is not None:
        row["SweepBarLow"] = sweep_bar_low
    if sweep_bar_high is not None:
        row["SweepBarHigh"] = sweep_bar_high
    return pd.DataFrame([row])


def _rulesets_df(*, stop_model: str = "REFERENCE_LEVEL_HARD_STOP", take_profit_model: str = "FIXED_R_MULTIPLE:1.5") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ruleset_id": "RULESET_001",
                "direction": "LONG",
                "setup_type": "FAILED_BREAK_RECLAIM_LONG",
                "entry_timing": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "entry_price_convention": "NEXT_BAR_OPEN",
                "same_bar_policy_id": "SAME_BAR_CONSERVATIVE_V0_1",
                "expiry_model": "BARS_AFTER_ACTIVATION:12",
                "expiry_start_semantics": "AFTER_ACTIVATION",
                "stop_model": stop_model,
                "take_profit_model": take_profit_model,
                "cost_model_id": "COST_MODEL_ZERO_SKELETON_ONLY",
                "replay_semantics_version": "REPLAY_V0_1",
            }
        ]
    )


def _features_df() -> pd.DataFrame:
    return pd.DataFrame([{"Timestamp": "2024-01-01T00:00:00Z"}, {"Timestamp": "2024-01-01T00:01:00Z"}, {"Timestamp": "2024-01-01T00:02:00Z"}])


def test_materialization_happy_path_long():
    out = materialize_stop_target_levels(rulesets_df=_rulesets_df(), setups_df=_setups_df(direction="LONG", reference_level=99.0), raw_df=_raw_df())

    row = out.iloc[0]
    assert row["initial_stop_price"] == 99.0
    assert row["risk_distance"] == pytest.approx(2.0)
    assert row["initial_target_price"] == pytest.approx(104.0)
    assert row["placement_status"] == "PLACED"


def test_materialization_happy_path_short():
    out = materialize_stop_target_levels(rulesets_df=_rulesets_df(), setups_df=_setups_df(direction="SHORT", reference_level=103.0), raw_df=_raw_df())

    row = out.iloc[0]
    assert row["initial_stop_price"] == 103.0
    assert row["risk_distance"] == pytest.approx(2.0)
    assert row["initial_target_price"] == pytest.approx(98.0)
    assert row["placement_status"] == "PLACED"


def test_materialization_unsupported_model_is_explicit_and_no_fake_prices():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="SOMETHING_ELSE"),
        setups_df=_setups_df(),
        raw_df=_raw_df(),
    )
    row = out.iloc[0]
    assert row["placement_status"] == "UNSUPPORTED_MODEL"
    assert pd.isna(row["initial_stop_price"])
    assert pd.isna(row["initial_target_price"])


def test_materialization_invalid_risk_when_stop_equals_entry_proxy():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(),
        setups_df=_setups_df(reference_level=101.0),
        raw_df=_raw_df(),
    )
    row = out.iloc[0]
    assert row["placement_status"] == "INVALID_RISK"
    assert row["risk_distance"] == 0.0
    assert pd.isna(row["initial_target_price"])


def test_engine_consumes_canonical_fields_without_legacy_aliases():
    setups = materialize_stop_target_levels(rulesets_df=_rulesets_df(), setups_df=_setups_df(reference_level=99.0), raw_df=_raw_df())
    events, _ = run_replay_engine(
        ReplayInputs(raw_df=_raw_df(), features_df=_features_df(), setups_df=setups, rulesets_df=_rulesets_df()),
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
        generation_timestamp="2024-01-01T00:00:00+00:00",
    )
    stop_eval = events[events["event_type"] == "STOP_EVALUATED"].iloc[0]
    target_eval = events[events["event_type"] == "TARGET_EVALUATED"].iloc[0]
    assert stop_eval["price_raw"] == 99.0
    assert target_eval["price_raw"] == pytest.approx(104.0)


def test_ledger_initial_prices_match_canonical_materialized_levels():
    setups = materialize_stop_target_levels(rulesets_df=_rulesets_df(), setups_df=_setups_df(reference_level=99.0), raw_df=_raw_df())
    events, _ = run_replay_engine(
        ReplayInputs(raw_df=_raw_df(), features_df=_features_df(), setups_df=setups, rulesets_df=_rulesets_df()),
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
        generation_timestamp="2024-01-01T00:00:00+00:00",
    )
    ledger = build_trade_ledger(events)
    row = ledger.iloc[0]
    assert row["initial_stop_price"] == 99.0
    assert row["initial_target_price"] == pytest.approx(104.0)


def test_no_lookahead_target_uses_activation_open_not_later_bar_extremes():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(),
        setups_df=_setups_df(reference_level=99.0),
        raw_df=_raw_df(),
    )
    row = out.iloc[0]
    # If later extremes were used, target would drift. It must stay at 104 from activation open=101 and risk=2.
    assert row["initial_target_price"] == pytest.approx(104.0)
    assert row["placement_basis_ts"] == pd.Timestamp("2024-01-01T00:01:00Z")


def test_sweep_extreme_stop_model_long_uses_sweep_bar_low_and_recomputes_r_target():
    raw = _raw_df()
    raw.loc[0, "Low"] = 97.0

    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="SWEEP_EXTREME_HARD_STOP"),
        setups_df=_setups_df(
            direction="LONG",
            reference_level=100.0,
            reference_event_anchor_ts="2024-01-01T00:00:00Z",
        ),
        raw_df=raw,
    )

    row = out.iloc[0]
    assert row["placement_status"] == "PLACED"
    assert row["initial_stop_price"] == 97.0
    assert row["risk_distance"] == pytest.approx(4.0)
    assert row["initial_target_price"] == pytest.approx(107.0)
    assert "stop_basis=sweep_bar_low" in row["placement_notes"]


def test_sweep_extreme_stop_model_short_uses_sweep_bar_high_and_recomputes_r_target():
    raw = _raw_df()
    raw.loc[0, "High"] = 105.0

    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="SWEEP_EXTREME_HARD_STOP"),
        setups_df=_setups_df(
            direction="SHORT",
            reference_level=100.0,
            reference_event_anchor_ts="2024-01-01T00:00:00Z",
        ),
        raw_df=raw,
    )

    row = out.iloc[0]
    assert row["placement_status"] == "PLACED"
    assert row["initial_stop_price"] == 105.0
    assert row["risk_distance"] == pytest.approx(4.0)
    assert row["initial_target_price"] == pytest.approx(95.0)
    assert "stop_basis=sweep_bar_high" in row["placement_notes"]


def test_sweep_extreme_stop_model_missing_sweep_extreme_fails_explicitly():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="SWEEP_EXTREME_HARD_STOP"),
        setups_df=_setups_df(direction="LONG", reference_level=100.0),
        raw_df=_raw_df(),
    )

    row = out.iloc[0]
    assert row["placement_status"] == "MISSING_SWEEP_EXTREME"
    assert row["placement_notes"] == "missing_sweep_bar_ts"
    assert pd.isna(row["initial_stop_price"])
    assert pd.isna(row["initial_target_price"])


def test_sweep_extreme_stop_model_invalid_risk_fails_explicitly():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="SWEEP_EXTREME_HARD_STOP"),
        setups_df=_setups_df(direction="LONG", reference_level=100.0, sweep_bar_low=102.0),
        raw_df=_raw_df(),
    )

    row = out.iloc[0]
    assert row["placement_status"] == "INVALID_RISK"
    assert row["initial_stop_price"] == 102.0
    assert row["risk_distance"] == pytest.approx(-1.0)
    assert pd.isna(row["initial_target_price"])


def test_reference_level_hard_stop_baseline_unchanged_when_sweep_extreme_fields_exist():
    out = materialize_stop_target_levels(
        rulesets_df=_rulesets_df(stop_model="REFERENCE_LEVEL_HARD_STOP"),
        setups_df=_setups_df(
            direction="LONG",
            reference_level=99.0,
            reference_event_anchor_ts="2024-01-01T00:00:00Z",
            sweep_bar_low=50.0,
        ),
        raw_df=_raw_df(),
    )

    row = out.iloc[0]
    assert row["placement_status"] == "PLACED"
    assert row["initial_stop_price"] == 99.0
    assert row["risk_distance"] == pytest.approx(2.0)
    assert row["initial_target_price"] == pytest.approx(104.0)
