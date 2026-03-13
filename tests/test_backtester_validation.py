from pathlib import Path

import pandas as pd

from backtester.metrics import build_trade_metrics_artifacts
from backtester.validation import (
    MAX_PASS_NOT_EVALUATED_CRITICAL,
    build_validation_artifacts,
    write_validation_csvs,
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
        "trade_return_pct": None if exit_ts is None else (0.01 if exit_reason_category == "TARGET" else -0.01),
        "trade_pnl": None if exit_ts is None else (1.0 if exit_reason_category == "TARGET" else -1.0),
        "trade_return_r": None if exit_ts is None else (1.0 if exit_reason_category == "TARGET" else -1.0),
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
    ledger["trade_return_pct"] = [0.02, -0.01]
    metrics = build_trade_metrics_artifacts(ledger)

    base = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    assert base.summary.loc[base.summary["scope"] == "ALL_TRADES", "expectancy_status"].iloc[0] == "PASS"

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
    non_economic_drawdown = metrics.drawdown.copy()
    non_economic_drawdown["drawdown_basis"] = "RESOLVED_TRADE_COUNT"
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=non_economic_drawdown,
    )

    assert (artifacts.summary["drawdown_status"] == "NOT_EVALUATED").all()


def test_drawdown_economic_basis_is_evaluated_and_thresholded():
    ledger = _build_ledger([_make_trade(1), _make_trade(2), _make_trade(3)])
    metrics = build_trade_metrics_artifacts(ledger)
    economic_drawdown = metrics.drawdown.copy()
    economic_drawdown["drawdown_basis"] = "TRADE_RETURN_PCT_CUMSUM"
    economic_drawdown["drawdown_value"] = [0.03, 0.04, 0.05]

    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=economic_drawdown,
    )
    all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert all_row["drawdown_status"] == "PASS"


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
    assert supported_row["long_short_asymmetry_status"] == "FAIL"
    assert supported_row["source_concentration_status"] == "PASS"


def test_coverage_hardening_limits_final_status_when_critical_coverage_is_weak():
    ledger = _build_ledger([
        _make_trade(i, direction="LONG" if i % 2 else "SHORT", source_setup_id=f"S{i % 5}") for i in range(1, 25)
    ])
    ledger["trade_return_pct"] = 0.01
    ledger["trade_pnl"] = 1.0
    metrics = build_trade_metrics_artifacts(ledger)
    metrics_trade = metrics.trade_metrics.copy()
    metrics_trade["expectancy"] = None
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics_trade,
        drawdown_df=None,
    )
    all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    critical_not_evaluated = [
        all_row["expectancy_status"],
        all_row["drawdown_status"],
        all_row["outlier_dependence_status"],
        all_row["long_short_asymmetry_status"],
        all_row["source_concentration_status"],
    ].count("NOT_EVALUATED")
    assert critical_not_evaluated > MAX_PASS_NOT_EVALUATED_CRITICAL
    assert all_row["validation_status"] == "REVIEW"


def test_source_concentration_prefers_explicit_surface_then_falls_back_to_source_setup_id():
    ledger = _build_ledger([
        _make_trade(1, source_setup_id="S1"),
        _make_trade(2, source_setup_id="S1"),
        _make_trade(3, source_setup_id="S1"),
        _make_trade(4, source_setup_id="S2"),
    ])
    ledger["source_candidate_group"] = ["G1", "G2", "G1", "G2"]
    metrics = build_trade_metrics_artifacts(ledger)
    with_explicit = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    explicit_row = with_explicit.summary.loc[with_explicit.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert explicit_row["source_concentration_status"] == "PASS"
    assert "source_surface=source_candidate_group" in explicit_row["notes"]

    fallback_ledger = ledger.drop(columns=["source_candidate_group"])
    fallback = build_validation_artifacts(
        trade_ledger_df=fallback_ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    fallback_row = fallback.summary.loc[fallback.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert fallback_row["source_concentration_status"] == "REVIEW"
    assert "source_surface=source_setup_id" in fallback_row["notes"]


def test_source_concentration_can_use_ruleset_lineage_surface_when_available():
    ledger = _build_ledger([
        _make_trade(1),
        _make_trade(2),
        _make_trade(3),
        _make_trade(4),
    ])
    metrics = build_trade_metrics_artifacts(ledger)
    rulesets_df = pd.DataFrame(
        [
            {"ruleset_id": "R1", "source_candidate_group": "GROUP_A"},
        ]
    )
    artifacts = build_validation_artifacts(
        trade_ledger_df=ledger,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
        rulesets_df=rulesets_df,
    )
    all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert "source_surface=rulesets_df.source_candidate_group" in all_row["notes"]


def test_long_short_asymmetry_uses_side_returns_when_available_and_remains_honest_when_unsupported():
    balanced_counts_divergent_returns = _build_ledger([
        _make_trade(1, direction="LONG"),
        _make_trade(2, direction="LONG"),
        _make_trade(3, direction="SHORT"),
        _make_trade(4, direction="SHORT"),
    ])
    balanced_counts_divergent_returns["trade_return_pct"] = [0.03, 0.03, -0.03, -0.02]
    metrics = build_trade_metrics_artifacts(balanced_counts_divergent_returns)
    artifacts = build_validation_artifacts(
        trade_ledger_df=balanced_counts_divergent_returns,
        trade_metrics_df=metrics.trade_metrics,
        drawdown_df=metrics.drawdown,
    )
    all_row = artifacts.summary.loc[artifacts.summary["scope"] == "ALL_TRADES"].iloc[0]
    assert all_row["long_short_asymmetry_status"] == "FAIL"

    unsupported = _build_ledger([
        _make_trade(1, direction="LONG", resolved=False),
        _make_trade(2, direction="SHORT", resolved=False),
    ])
    unsupported_metrics = build_trade_metrics_artifacts(unsupported)
    unsupported_artifacts = build_validation_artifacts(
        trade_ledger_df=unsupported,
        trade_metrics_df=unsupported_metrics.trade_metrics,
        drawdown_df=unsupported_metrics.drawdown,
    )
    details = unsupported_artifacts.details
    asymmetry_note = details.loc[
        (details["scope"] == "ALL_TRADES") & (details["check"] == "long_short_asymmetry"), "notes"
    ].iloc[0]
    assert "side expectancy not evaluated" in asymmetry_note



def test_return_basis_consistency_prefers_pct_then_pnl_then_r_across_metrics_and_validation():
    ledger = _build_ledger([_make_trade(1), _make_trade(2), _make_trade(3)])

    ledger_pct = ledger.copy()
    ledger_pct["trade_return_pct"] = [0.03, -0.02, 0.01]
    ledger_pct["trade_pnl"] = [3.0, -2.0, 1.0]
    ledger_pct["trade_return_r"] = [1.5, -1.0, 0.5]
    metrics_pct = build_trade_metrics_artifacts(ledger_pct)
    validation_pct = build_validation_artifacts(
        trade_ledger_df=ledger_pct,
        trade_metrics_df=metrics_pct.trade_metrics,
        drawdown_df=metrics_pct.drawdown,
    )
    pct_note = validation_pct.summary.loc[validation_pct.summary["scope"] == "ALL_TRADES", "notes"].iloc[0]
    assert "basis=trade_return_pct" in pct_note

    ledger_pnl = ledger_pct.copy()
    ledger_pnl["trade_return_pct"] = None
    metrics_pnl = build_trade_metrics_artifacts(ledger_pnl)
    validation_pnl = build_validation_artifacts(
        trade_ledger_df=ledger_pnl,
        trade_metrics_df=metrics_pnl.trade_metrics,
        drawdown_df=metrics_pnl.drawdown,
    )
    pnl_note = validation_pnl.summary.loc[validation_pnl.summary["scope"] == "ALL_TRADES", "notes"].iloc[0]
    assert "basis=trade_pnl" in pnl_note

    ledger_r = ledger_pct.copy()
    ledger_r["trade_return_pct"] = None
    ledger_r["trade_pnl"] = None
    metrics_r = build_trade_metrics_artifacts(ledger_r)
    validation_r = build_validation_artifacts(
        trade_ledger_df=ledger_r,
        trade_metrics_df=metrics_r.trade_metrics,
        drawdown_df=metrics_r.drawdown,
    )
    r_note = validation_r.summary.loc[validation_r.summary["scope"] == "ALL_TRADES", "notes"].iloc[0]
    assert "basis=trade_return_r" in r_note

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
