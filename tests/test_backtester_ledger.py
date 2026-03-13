from pathlib import Path

import pandas as pd
import pytest

from backtester.engine import ReplayInputs, ZeroCostSkeletonModel, run_replay_engine
from backtester.ledger import (
    LedgerContractError,
    build_trade_ledger,
    validate_trade_ledger,
    write_trade_ledger_csv,
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


def _setups_df(
    force_collision: bool = False,
    force_expiry_close: bool = False,
    direction: str = "LONG",
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SetupId": "S1",
                "SetupType": "FAILED_BREAK_RECLAIM_LONG",
                "Direction": direction,
                "DetectedAt": "2024-01-01T00:00:00Z",
                "SetupBarTs": "2024-01-01T00:00:00Z",
                "ReferenceEventType": "FAILED_BREAK_DOWN",
                "ForceSameBarCollision": force_collision,
                "ForceExpiryClose": force_expiry_close,
            }
        ]
    )


def _rulesets_df(direction: str = "LONG") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ruleset_id": "RULESET_001",
                "direction": direction,
                "setup_type": "FAILED_BREAK_RECLAIM_LONG",
                "entry_timing": "SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN",
                "entry_price_convention": "NEXT_BAR_OPEN",
                "same_bar_policy_id": "SAME_BAR_CONSERVATIVE_V0_1",
                "expiry_start_semantics": "AFTER_ACTIVATION",
                "stop_model": "STOP_MODEL_PLACEHOLDER",
                "take_profit_model": "TP_MODEL_PLACEHOLDER",
                "cost_model_id": "COST_MODEL_ZERO_SKELETON_ONLY",
                "replay_semantics_version": "REPLAY_V0_1",
            }
        ]
    )


def _engine_events(
    force_collision: bool = False,
    force_expiry_close: bool = False,
    policy: object | None = None,
    direction: str = "LONG",
) -> pd.DataFrame:
    inputs = ReplayInputs(
        raw_df=_raw_df(),
        features_df=_features_df(),
        setups_df=_setups_df(
            force_collision=force_collision,
            force_expiry_close=force_expiry_close,
            direction=direction,
        ),
        rulesets_df=_rulesets_df(direction=direction),
    )
    policies = None
    if policy is not None:
        policies = {"SAME_BAR_CONSERVATIVE_V0_1": policy}

    events, _ = run_replay_engine(
        inputs,
        generation_timestamp="2024-01-01T00:00:00+00:00",
        cost_models={"COST_MODEL_ZERO_SKELETON_ONLY": ZeroCostSkeletonModel()},
        same_bar_policies=policies,
    )
    return events


def test_determinism_same_events_produce_identical_ledger_stable_ids_and_order():
    events = _engine_events()
    first = build_trade_ledger(events)
    second = build_trade_ledger(events)

    pd.testing.assert_frame_equal(first, second)
    assert first["trade_id"].tolist() == ["TRADE_RULESET_001_S1"]


def test_entry_materialization_signal_only_does_not_create_trade_and_activation_preserves_timestamps():
    events = _engine_events()
    signal_only = events[events["event_type"] == "SIGNAL_ACTIONABLE"].reset_index(drop=True)
    ledger_empty = build_trade_ledger(signal_only)
    assert ledger_empty.empty

    full_ledger = build_trade_ledger(events)
    row = full_ledger.iloc[0]
    assert row["entry_signal_ts"] == pd.Timestamp("2024-01-01T00:00:00Z")
    assert row["entry_activation_ts"] == pd.Timestamp("2024-01-01T00:01:00Z")


def test_exit_materialization_maps_stop_and_target_and_preserves_unresolved_without_fake_exit():
    class StopWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "STOP_WINS"

    class TargetWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "TARGET_WINS"

    stop_ledger = build_trade_ledger(_engine_events(force_collision=True, policy=StopWinsPolicy()))
    target_ledger = build_trade_ledger(_engine_events(force_collision=True, policy=TargetWinsPolicy()))
    unresolved_ledger = build_trade_ledger(_engine_events(force_collision=False))

    assert stop_ledger.iloc[0]["exit_reason_category"] == "STOP"
    assert target_ledger.iloc[0]["exit_reason_category"] == "TARGET"
    assert unresolved_ledger.iloc[0]["exit_reason_category"] == "UNRESOLVED"
    assert pd.isna(unresolved_ledger.iloc[0]["exit_ts"])
    assert pd.isna(unresolved_ledger.iloc[0]["exit_price_raw"])


def test_same_bar_honesty_unresolved_same_bar_outcome_remains_unresolved():
    class UnresolvedPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "UNRESOLVED"

    ledger = build_trade_ledger(_engine_events(force_collision=True, policy=UnresolvedPolicy()))
    row = ledger.iloc[0]
    assert row["exit_reason"] == "SAME_BAR_UNRESOLVED"
    assert row["exit_reason_category"] == "UNRESOLVED"
    assert pd.isna(row["exit_ts"])


def test_validation_duplicate_trade_id_fails():
    ledger = build_trade_ledger(_engine_events())
    duplicated = pd.concat([ledger, ledger], ignore_index=True)

    with pytest.raises(LedgerContractError, match="Duplicate trade_id"):
        validate_trade_ledger(duplicated)


def test_validation_inconsistent_timestamps_negative_holding_and_missing_activation_fail():
    ledger = build_trade_ledger(_engine_events())

    bad_ts = ledger.copy()
    bad_ts.loc[0, "entry_signal_ts"] = pd.Timestamp("2024-01-01T00:02:00Z")
    with pytest.raises(LedgerContractError, match="entry_activation_ts < entry_signal_ts"):
        validate_trade_ledger(bad_ts)

    bad_holding = ledger.copy()
    bad_holding.loc[0, "holding_bars"] = -1
    with pytest.raises(LedgerContractError, match="holding_bars < 0"):
        validate_trade_ledger(bad_holding)

    bad_activation = ledger.copy()
    bad_activation.loc[0, "entry_activation_ts"] = pd.NaT
    with pytest.raises(LedgerContractError, match="entry_activation_ts is required"):
        validate_trade_ledger(bad_activation)


def test_boundary_ledger_consumes_engine_events_only_and_does_not_require_shortlist_or_research_summary():
    events = _engine_events()
    ledger = build_trade_ledger(events, rulesets_df=None, setup_lineage_df=None)
    assert not ledger.empty


def test_write_trade_ledger_csv(tmp_path: Path):
    ledger = build_trade_ledger(_engine_events())
    out = write_trade_ledger_csv(ledger_df=ledger, output_dir=tmp_path)

    assert out.name == "backtest_trades.csv"
    assert out.exists()


def test_ledger_consumes_explicit_close_fields_not_notes_for_resolved_exit():
    class StopWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "STOP_WINS"

    events = _engine_events(force_collision=True, policy=StopWinsPolicy())
    events.loc[events["event_type"] == "CLOSE_RESOLVED", "notes"] = "misleading_notes_should_not_drive_exit"
    ledger = build_trade_ledger(events)
    row = ledger.iloc[0]
    assert row["exit_reason"] == "SAME_BAR_STOP_WINS_POLICY"
    assert row["exit_reason_category"] == "STOP"


def test_trade_result_contract_resolved_long_short_and_unresolved():
    class TargetWinsPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "TARGET_WINS"

    class UnresolvedPolicy:
        def resolve(self, *, ruleset_row: pd.Series, setup_row: pd.Series, bar_row: pd.Series) -> str:
            return "UNRESOLVED"

    long_row = build_trade_ledger(_engine_events(force_collision=True, policy=TargetWinsPolicy(), direction="LONG")).iloc[0]
    short_row = build_trade_ledger(_engine_events(force_collision=True, policy=TargetWinsPolicy(), direction="SHORT")).iloc[0]
    unresolved_row = build_trade_ledger(_engine_events(force_collision=True, policy=UnresolvedPolicy(), direction="LONG")).iloc[0]

    assert long_row["trade_return_pct"] == pytest.approx((103.0 - 101.0) / 101.0)
    assert long_row["trade_pnl"] == pytest.approx(2.0)

    assert short_row["trade_return_pct"] == pytest.approx((101.0 - 99.5) / 101.0)
    assert short_row["trade_pnl"] == pytest.approx(1.5)

    assert pd.isna(unresolved_row["trade_return_pct"])
    assert pd.isna(unresolved_row["trade_pnl"])
