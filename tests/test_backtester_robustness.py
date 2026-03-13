from pathlib import Path

import pandas as pd

from backtester.robustness import build_robustness_artifacts, write_robustness_csvs

LEDGER_COLUMNS = [
    "trade_id",
    "ruleset_id",
    "source_setup_id",
    "direction",
    "entry_signal_ts",
    "entry_activation_ts",
    "entry_price_raw",
    "entry_price_effective",
    "initial_stop_price",
    "initial_target_price",
    "expiry_ts",
    "exit_ts",
    "exit_price_raw",
    "exit_price_effective",
    "exit_reason",
    "exit_reason_category",
    "holding_bars",
    "cost_model_id",
    "same_bar_policy_id",
    "replay_semantics_version",
    "notes",
    "trade_return_pct",
]


def _build_ledger(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    for col in ["entry_signal_ts", "entry_activation_ts", "expiry_ts", "exit_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


def _make_trade(index: int, *, ret: float | None = 0.01, resolved: bool = True, regime: str | None = None) -> dict:
    start = pd.Timestamp("2024-01-01T00:00:00Z") + pd.Timedelta(minutes=index * 3)
    exit_ts = start + pd.Timedelta(minutes=1) if resolved else None
    row = {
        "trade_id": f"T{index}",
        "ruleset_id": "R1",
        "source_setup_id": "S1",
        "direction": "LONG",
        "entry_signal_ts": start.isoformat(),
        "entry_activation_ts": (start + pd.Timedelta(seconds=5)).isoformat(),
        "entry_price_raw": 100.0,
        "entry_price_effective": 100.0,
        "initial_stop_price": 99.0,
        "initial_target_price": 101.0,
        "expiry_ts": None,
        "exit_ts": None if exit_ts is None else exit_ts.isoformat(),
        "exit_price_raw": None if exit_ts is None else 101.0,
        "exit_price_effective": None if exit_ts is None else 101.0,
        "exit_reason": "NO_EXIT_RESOLVED_YET" if not resolved else "RULE_CLOSE",
        "exit_reason_category": "UNRESOLVED" if not resolved else "RULE_CLOSE",
        "holding_bars": None if exit_ts is None else 1,
        "cost_model_id": "ZERO",
        "same_bar_policy_id": "SBP",
        "replay_semantics_version": "REPLAY_V0_1",
        "notes": "",
        "trade_return_pct": ret,
    }
    if regime is not None:
        row["regime"] = regime
    return row


def test_determinism_same_inputs_identical_outputs():
    ledger = _build_ledger([_make_trade(i, ret=0.02) for i in range(1, 10)])

    first = build_robustness_artifacts(trade_ledger_df=ledger)
    second = build_robustness_artifacts(trade_ledger_df=ledger)

    pd.testing.assert_frame_equal(first.summary, second.summary)
    pd.testing.assert_frame_equal(first.details, second.details)


def test_oos_honesty_without_return_basis_is_not_evaluated():
    ledger = _build_ledger([_make_trade(i, ret=0.01) for i in range(1, 8)]).drop(columns=["trade_return_pct"])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["oos_status"] == "NOT_EVALUATED"


def test_oos_positive_is_broken_oos_is_fragile():
    returns = [0.03, 0.02, 0.04, 0.01, 0.02, -0.03, -0.02, -0.01, -0.04, -0.02]
    ledger = _build_ledger([_make_trade(i + 1, ret=r) for i, r in enumerate(returns)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["oos_status"] == "FRAGILE"


def test_oos_consistent_is_oos_is_robust():
    returns = [0.03, 0.02, 0.04, 0.01, 0.02, 0.03, 0.02, 0.01, 0.04, 0.02]
    ledger = _build_ledger([_make_trade(i + 1, ret=r) for i, r in enumerate(returns)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["oos_status"] == "ROBUST"


def test_walkforward_honesty_insufficient_observations_not_evaluated():
    ledger = _build_ledger([_make_trade(i, ret=0.02) for i in range(1, 7)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["walkforward_status"] == "NOT_EVALUATED"


def test_walkforward_inconsistent_windows_deterministic_fragile():
    returns = [0.03, 0.02, 0.01, -0.03, -0.02, -0.01, -0.04, -0.02, -0.01]
    ledger = _build_ledger([_make_trade(i + 1, ret=r) for i, r in enumerate(returns)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["walkforward_status"] == "FRAGILE"


def test_regime_honesty_missing_label_not_evaluated():
    ledger = _build_ledger([_make_trade(i, ret=0.02) for i in range(1, 10)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["regime_status"] == "NOT_EVALUATED"


def test_regime_with_explicit_label_is_evaluated_deterministically():
    rows = [
        _make_trade(1, ret=0.03),
        _make_trade(2, ret=0.02),
        _make_trade(3, ret=0.01),
        _make_trade(4, ret=0.03),
        _make_trade(5, ret=0.02),
        _make_trade(6, ret=0.01),
    ]
    ledger = _build_ledger(rows)
    rulesets_df = pd.DataFrame([{"ruleset_id": "R1", "regime": "trend"}])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger, rulesets_df=rulesets_df)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["regime_status"] == "NOT_EVALUATED"

    ledger["regime"] = ["trend", "trend", "range", "range", "trend", "range"]
    artifacts2 = build_robustness_artifacts(trade_ledger_df=ledger)
    row2 = artifacts2.summary.loc[artifacts2.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row2["regime_status"] == "ROBUST"


def test_perturbation_honesty_no_surface_is_not_evaluated():
    ledger = _build_ledger([_make_trade(i, ret=0.02) for i in range(1, 10)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["perturbation_status"] == "NOT_EVALUATED"


def test_unresolved_trades_explicitly_excluded_from_return_checks():
    ledger = _build_ledger([
        _make_trade(1, ret=0.03, resolved=True),
        _make_trade(2, ret=0.02, resolved=True),
        _make_trade(3, ret=0.01, resolved=False),
    ])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert row["trade_count"] == 3
    assert row["resolved_trade_count"] == 2
    assert "unresolved trades excluded from return-based checks=1" in row["notes"]


def test_write_robustness_csvs(tmp_path: Path):
    ledger = _build_ledger([_make_trade(i, ret=0.02) for i in range(1, 10)])
    artifacts = build_robustness_artifacts(trade_ledger_df=ledger)

    paths = write_robustness_csvs(artifacts=artifacts, output_dir=tmp_path)

    assert (tmp_path / "backtest_robustness_summary.csv").exists()
    assert (tmp_path / "backtest_robustness_details.csv").exists()
    assert set(paths.keys()) == {
        "backtest_robustness_summary.csv",
        "backtest_robustness_details.csv",
    }
