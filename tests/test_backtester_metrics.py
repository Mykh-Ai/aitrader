from pathlib import Path

import pandas as pd
import pytest

from backtester.metrics import (
    MetricsContractError,
    build_trade_metrics_artifacts,
    write_trade_metrics_csvs,
)


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
    "trade_return_pct",
    "trade_pnl",
    "trade_return_r",
    "notes",
]


def _ledger_df() -> pd.DataFrame:
    rows = [
        {
            "trade_id": "T1",
            "ruleset_id": "R1",
            "source_setup_id": "S1",
            "direction": "LONG",
            "entry_signal_ts": "2024-01-01T00:00:00Z",
            "entry_activation_ts": "2024-01-01T00:01:00Z",
            "entry_price_raw": 100.0,
            "entry_price_effective": 100.0,
            "initial_stop_price": 98.0,
            "initial_target_price": 103.0,
            "expiry_ts": None,
            "exit_ts": "2024-01-01T00:03:00Z",
            "exit_price_raw": 103.0,
            "exit_price_effective": 103.0,
            "exit_reason": "SAME_BAR_TARGET_WINS_POLICY",
            "exit_reason_category": "TARGET",
            "holding_bars": 2,
            "cost_model_id": "ZERO",
            "same_bar_policy_id": "SBP",
            "replay_semantics_version": "REPLAY_V0_1",
            "trade_return_pct": None,
            "trade_pnl": None,
            "trade_return_r": None,
            "notes": "",
        },
        {
            "trade_id": "T2",
            "ruleset_id": "R1",
            "source_setup_id": "S2",
            "direction": "SHORT",
            "entry_signal_ts": "2024-01-01T00:04:00Z",
            "entry_activation_ts": "2024-01-01T00:05:00Z",
            "entry_price_raw": 101.0,
            "entry_price_effective": 101.0,
            "initial_stop_price": 103.0,
            "initial_target_price": 99.0,
            "expiry_ts": None,
            "exit_ts": "2024-01-01T00:07:00Z",
            "exit_price_raw": 103.0,
            "exit_price_effective": 103.0,
            "exit_reason": "SAME_BAR_STOP_WINS_POLICY",
            "exit_reason_category": "STOP",
            "holding_bars": 2,
            "cost_model_id": "ZERO",
            "same_bar_policy_id": "SBP",
            "replay_semantics_version": "REPLAY_V0_1",
            "trade_return_pct": None,
            "trade_pnl": None,
            "trade_return_r": None,
            "notes": "",
        },
        {
            "trade_id": "T3",
            "ruleset_id": "R2",
            "source_setup_id": "S3",
            "direction": "LONG",
            "entry_signal_ts": "2024-01-01T00:08:00Z",
            "entry_activation_ts": "2024-01-01T00:09:00Z",
            "entry_price_raw": 99.0,
            "entry_price_effective": 99.0,
            "initial_stop_price": 97.0,
            "initial_target_price": 102.0,
            "expiry_ts": None,
            "exit_ts": None,
            "exit_price_raw": None,
            "exit_price_effective": None,
            "exit_reason": "NO_EXIT_RESOLVED_YET",
            "exit_reason_category": "UNRESOLVED",
            "holding_bars": None,
            "cost_model_id": "ZERO",
            "same_bar_policy_id": "SBP",
            "replay_semantics_version": "REPLAY_V0_1",
            "trade_return_pct": None,
            "trade_pnl": None,
            "trade_return_r": None,
            "notes": "",
        },
    ]
    df = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    for col in ["entry_signal_ts", "entry_activation_ts", "expiry_ts", "exit_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


def _ledger_with_explicit_returns(*, include_return_pct: bool = True, include_pnl: bool = True, include_return_r: bool = True) -> pd.DataFrame:
    df = _ledger_df()
    if include_return_pct:
        df["trade_return_pct"] = [0.03, -0.02, None]
    else:
        df["trade_return_pct"] = None
    if include_pnl:
        df["trade_pnl"] = [30.0, -20.0, None]
    else:
        df["trade_pnl"] = None
    if include_return_r:
        df["trade_return_r"] = [1.5, -1.0, None]
    else:
        df["trade_return_r"] = None
    return df


def test_determinism_same_ledger_produces_identical_artifacts_and_order():
    ledger = _ledger_df()

    first = build_trade_metrics_artifacts(ledger)
    second = build_trade_metrics_artifacts(ledger)

    pd.testing.assert_frame_equal(first.trade_metrics, second.trade_metrics)
    pd.testing.assert_frame_equal(first.equity_curve, second.equity_curve)
    pd.testing.assert_frame_equal(first.drawdown, second.drawdown)
    pd.testing.assert_frame_equal(first.exit_reason_summary, second.exit_reason_summary)
    assert first.equity_curve["trade_id"].tolist() == ["T1", "T2"]


def test_unresolved_honesty_counts_and_no_fake_resolution():
    artifacts = build_trade_metrics_artifacts(_ledger_df())
    all_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    resolved_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "RESOLVED_ONLY"].iloc[0]

    assert all_scope["trade_count"] == 3
    assert all_scope["resolved_trade_count"] == 2
    assert all_scope["unresolved_trade_count"] == 1
    assert resolved_scope["trade_count"] == 2
    assert resolved_scope["unresolved_trade_count"] == 0
    assert "T3" not in set(artifacts.equity_curve["trade_id"])


def test_structural_metrics_and_exit_reason_distribution_are_correct():
    artifacts = build_trade_metrics_artifacts(_ledger_df())
    all_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]

    assert all_scope["long_trade_count"] == 2
    assert all_scope["short_trade_count"] == 1
    assert all_scope["average_holding_bars"] == pytest.approx(2.0)
    assert all_scope["median_holding_bars"] == pytest.approx(2.0)

    grouped = artifacts.exit_reason_summary.set_index(["exit_reason", "exit_reason_category"])["trade_count"].to_dict()
    assert grouped[("SAME_BAR_TARGET_WINS_POLICY", "TARGET")] == 1
    assert grouped[("SAME_BAR_STOP_WINS_POLICY", "STOP")] == 1
    assert grouped[("NO_EXIT_RESOLVED_YET", "UNRESOLVED")] == 1


def test_curve_honesty_basis_explicit_and_drawdown_basis_matches_equity():
    artifacts = build_trade_metrics_artifacts(_ledger_with_explicit_returns())

    assert set(artifacts.equity_curve["equity_basis"]) == {"TRADE_RETURN_PCT_CUMSUM"}
    assert set(artifacts.drawdown["drawdown_basis"]) == {"TRADE_RETURN_PCT_CUMSUM"}
    assert (artifacts.drawdown["drawdown_value"] >= 0).all()
    assert artifacts.drawdown["sequence"].tolist() == [1, 2]
    assert artifacts.equity_curve["equity_step_value"].tolist() == pytest.approx([0.03, 0.01])
    assert artifacts.drawdown["drawdown_value"].tolist() == pytest.approx([0.0, 0.02])


def test_unsupported_return_metrics_are_not_invented_and_are_explicitly_noted():
    artifacts = build_trade_metrics_artifacts(_ledger_df())

    assert artifacts.trade_metrics["win_rate"].isna().all()
    assert artifacts.trade_metrics["average_win"].isna().all()
    assert artifacts.trade_metrics["average_loss"].isna().all()
    assert artifacts.trade_metrics["payoff_ratio"].isna().all()
    assert artifacts.trade_metrics["expectancy"].isna().all()
    assert artifacts.trade_metrics["notes"].str.contains("return metrics omitted", regex=False).all()


def test_summary_return_metrics_use_explicit_trade_return_pct_and_exclude_unresolved():
    artifacts = build_trade_metrics_artifacts(_ledger_with_explicit_returns())

    all_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    resolved_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "RESOLVED_ONLY"].iloc[0]

    assert all_scope["win_rate"] == pytest.approx(0.5)
    assert all_scope["average_win"] == pytest.approx(0.03)
    assert all_scope["average_loss"] == pytest.approx(-0.02)
    assert all_scope["payoff_ratio"] == pytest.approx(1.5)
    assert all_scope["expectancy"] == pytest.approx(0.005)
    assert resolved_scope["expectancy"] == pytest.approx(0.005)
    assert artifacts.trade_metrics["notes"].str.contains("explicit trade_return_pct", regex=False).all()


def test_economic_basis_falls_back_to_trade_pnl_when_trade_return_pct_absent():
    artifacts = build_trade_metrics_artifacts(_ledger_with_explicit_returns(include_return_pct=False, include_pnl=True))

    assert set(artifacts.equity_curve["equity_basis"]) == {"TRADE_PNL_CUMSUM"}
    assert set(artifacts.drawdown["drawdown_basis"]) == {"TRADE_PNL_CUMSUM"}
    assert artifacts.equity_curve["equity_step_value"].tolist() == pytest.approx([30.0, 10.0])
    all_scope = artifacts.trade_metrics.loc[artifacts.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    assert all_scope["expectancy"] == pytest.approx(5.0)


def test_honest_fallback_to_resolved_trade_count_when_no_economic_result_fields():
    artifacts = build_trade_metrics_artifacts(_ledger_df())

    assert set(artifacts.equity_curve["equity_basis"]) == {"RESOLVED_TRADE_COUNT"}
    assert set(artifacts.drawdown["drawdown_basis"]) == {"RESOLVED_TRADE_COUNT"}
    assert artifacts.equity_curve["notes"].str.contains("not monetary equity", regex=False).all()


def test_return_basis_priority_is_deterministic_pct_then_pnl_then_r():
    pct = build_trade_metrics_artifacts(_ledger_with_explicit_returns(include_return_pct=True, include_pnl=True, include_return_r=True))
    pct_all = pct.trade_metrics.loc[pct.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    assert pct_all["expectancy_basis"] == "trade_return_pct"

    pnl = build_trade_metrics_artifacts(_ledger_with_explicit_returns(include_return_pct=False, include_pnl=True, include_return_r=True))
    pnl_all = pnl.trade_metrics.loc[pnl.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    assert pnl_all["expectancy_basis"] == "trade_pnl"

    ret_r = build_trade_metrics_artifacts(_ledger_with_explicit_returns(include_return_pct=False, include_pnl=False, include_return_r=True))
    ret_r_all = ret_r.trade_metrics.loc[ret_r.trade_metrics["scope"] == "ALL_TRADES"].iloc[0]
    assert ret_r_all["expectancy_basis"] == "trade_return_r"


def test_missing_required_metrics_field_fails_loudly():
    ledger = _ledger_df().drop(columns=["direction"])

    with pytest.raises((MetricsContractError, Exception), match="required|missing|Missing"):
        build_trade_metrics_artifacts(ledger)


def test_write_metrics_csvs(tmp_path: Path):
    artifacts = build_trade_metrics_artifacts(_ledger_df())
    paths = write_trade_metrics_csvs(artifacts=artifacts, output_dir=tmp_path)

    assert (tmp_path / "backtest_trade_metrics.csv").exists()
    assert (tmp_path / "backtest_equity_curve.csv").exists()
    assert (tmp_path / "backtest_drawdown.csv").exists()
    assert (tmp_path / "backtest_exit_reason_summary.csv").exists()
    assert set(paths.keys()) == {
        "backtest_trade_metrics.csv",
        "backtest_equity_curve.csv",
        "backtest_drawdown.csv",
        "backtest_exit_reason_summary.csv",
    }
