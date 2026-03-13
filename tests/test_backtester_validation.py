from pathlib import Path

import pandas as pd

from backtester.metrics import build_trade_metrics_artifacts
from backtester.validation import build_validation_artifacts, write_validation_csvs


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
]


def _build_ledger(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    for col in ["entry_signal_ts", "entry_activation_ts", "expiry_ts", "exit_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


def _make_trade(index: int, *, direction: str = "LONG", source_setup_id: str = "S1", resolved: bool = True) -> dict:
    start = pd.Timestamp("2024-01-01T00:00:00Z") + pd.Timedelta(minutes=index * 2)
    if resolved:
        exit_ts = start + pd.Timedelta(minutes=1)
        exit_reason_category = "TARGET" if index % 2 == 0 else "STOP"
        exit_reason = "SAME_BAR_TARGET_WINS_POLICY" if exit_reason_category == "TARGET" else "SAME_BAR_STOP_WINS_POLICY"
    else:
        exit_ts = None
        exit_reason_category = "UNRESOLVED"
        exit_reason = "NO_EXIT_RESOLVED_YET"

    return {
        "trade_id": f"T{index}",
        "ruleset_id": "R1",
        "source_setup_id": source_setup_id,
        "direction": direction,
        "entry_signal_ts": start.isoformat(),
        "entry_activation_ts": (start + pd.Timedelta(seconds=10)).isoformat(),
        "entry_price_raw": 100.0,
        "entry_price_effective": 100.0,
        "initial_stop_price": 99.0,
        "initial_target_price": 101.0,
        "expiry_ts": None,
        "exit_ts": None if exit_ts is None else exit_ts.isoformat(),
        "exit_price_raw": None if exit_ts is None else 101.0,
        "exit_price_effective": None if exit_ts is None else 101.0,
        "exit_reason": exit_reason,
        "exit_reason_category": exit_reason_category,
        "holding_bars": None if exit_ts is None else 1,
        "cost_model_id": "ZERO",
        "same_bar_policy_id": "SBP",
        "replay_semantics_version": "REPLAY_V0_1",
        "notes": "",
    }


def test_determinism_same_inputs_identical_validation_output():
    ledger = _build_ledger([_make_trade(1), _make_trade(2), _make_trade(3, resolved=False)])
    metrics = build_trade_metrics_artifacts(ledger)

    first = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    second = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )

    pd.testing.assert_frame_equal(first.summary, second.summary)
    pd.testing.assert_frame_equal(first.details, second.details)


def test_sample_sufficiency_thresholds_are_deterministic():
    for resolved_count, expected in [(4, "FAIL"), (5, "REVIEW"), (20, "PASS")]:
        ledger = _build_ledger([_make_trade(i) for i in range(1, resolved_count + 1)])
        metrics = build_trade_metrics_artifacts(ledger)
        artifacts = build_validation_artifacts(
            trade_ledger_df=ledger,
            trade_metrics_df=metrics.trade_metrics,
            drawdown_df=metrics.drawdown,
        )
        all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
        assert all_row["sample_sufficiency_status"] == expected


def test_expectancy_honesty_not_evaluated_and_pass_fail_when_explicit_metric_available():
    ledger = _build_ledger([_make_trade(1), _make_trade(2)])
    metrics = build_trade_metrics_artifacts(ledger)

    base = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    assert (base.summary["expectancy_status"] == "NOT_EVALUATED").all()

    pos_metrics = metrics.trade_metrics.copy()
    pos_metrics.loc[pos_metrics["scope"] == "ALL_TRADES", "expectancy"] = 0.1
    pos = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=pos_metrics,
        drawdown_df=metrics.drawdown,
    )
    assert pos.summary.loc[pos.summary["scope"] == "ALL_TRADES", "expectancy_status"].iloc[0] == "PASS"

    neg_metrics = metrics.trade_metrics.copy()
    neg_metrics.loc[neg_metrics["scope"] == "ALL_TRADES", "expectancy"] = -0.1
    neg = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=neg_metrics,
        drawdown_df=metrics.drawdown,
    )
    assert neg.summary.loc[neg.summary["scope"] == "ALL_TRADES", "expectancy_status"].iloc[0] == "FAIL"


def test_drawdown_honesty_non_economic_basis_is_not_evaluated():
    ledger = _build_ledger([_make_trade(1), _make_trade(2)])
    metrics = build_trade_metrics_artifacts(ledger)
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )

    assert (artifacts.summary["drawdown_status"] == "NOT_EVALUATED").all()


def test_unresolved_trades_are_explicit_in_counts_and_notes():
    ledger = _build_ledger([_make_trade(1), _make_trade(2), _make_trade(3, resolved=False)])
    metrics = build_trade_metrics_artifacts(ledger)
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )

    all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert all_row["trade_count"] == 3
    assert all_row["resolved_trade_count"] == 2
    assert all_row["unresolved_trade_count"] == 1
    assert "unresolved trades explicit=1" in all_row["notes"]


def test_long_short_and_source_checks_not_evaluated_when_unsupported_or_zero_side_and_deterministic_when_supported():
    unresolved_ledger = _build_ledger([
        _make_trade(1, direction="LONG", resolved=False),
        _make_trade(2, direction="LONG", resolved=False),
    ])
    unresolved_metrics = build_trade_metrics_artifacts(unresolved_ledger)
    unresolved_artifacts = build_validation_artifacts(
        trade_ledger_df=unresolved_ledger,
        trade_metrics_df=unresolved_metrics.trade_metrics,
        drawdown_df=unresolved_metrics.drawdown,
    )

    unresolved_row = unresolved_artifacts.summary.loc[
        unresolved_artifacts.summary["scope"] == "RESOLVED_ONLY"
    ].iloc[0]
    assert unresolved_row["long_short_asymmetry_status"] == "NOT_EVALUATED"
    assert unresolved_row["source_concentration_status"] == "NOT_EVALUATED"

    supported_ledger = _build_ledger([
        _make_trade(1, direction="LONG", source_setup_id="S1"),
        _make_trade(2, direction="SHORT", source_setup_id="S1"),
        _make_trade(3, direction="LONG", source_setup_id="S2"),
        _make_trade(4, direction="SHORT", source_setup_id="S2"),
    ])
    supported_metrics = build_trade_metrics_artifacts(supported_ledger)
    supported = build_validation_artifacts(
        trade_ledger_df=supported_ledger,
        trade_metrics_df=supported_metrics.trade_metrics,
        drawdown_df=supported_metrics.drawdown,
    )
    supported_row = supported.summary.loc[supported.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert supported_row["long_short_asymmetry_status"] == "PASS"
    assert supported_row["source_concentration_status"] == "PASS"


def test_write_validation_csvs(tmp_path: Path):
    ledger = _build_ledger([_make_trade(1), _make_trade(2)])
    metrics = build_trade_metrics_artifacts(ledger)
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )

    paths = write_validation_csvs(artifacts=artifacts, output_dir=tmp_path)

    assert (tmp_path / "backtest_validation_summary.csv").exists()
    assert (tmp_path / "backtest_validation_details.csv").exists()
    assert set(paths.keys()) == {
        "backtest_validation_summary.csv",
        "backtest_validation_details.csv",
    }
