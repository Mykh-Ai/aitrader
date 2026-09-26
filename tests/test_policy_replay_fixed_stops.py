from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.policy_replay_fixed_stops import (
    _evaluate_forward_path,
    _tp1_outcome,
    _tp1_price,
    run_policy_replay_fixed_stops,
)
from market_monitor.run_policy_replay_fixed_stops import main


def test_policy_replay_fixed_stops_uses_tradable_anchor_and_structural_stop(tmp_path: Path):
    focus, stops, verdicts, feed = _write_inputs(tmp_path)

    result = run_policy_replay_fixed_stops(
        focus_alignment_path=focus,
        structural_stops_path=stops,
        manual_verdicts_path=verdicts,
        feed_dir=feed,
        output_dir=tmp_path / "out",
    )

    rows = pd.read_csv(result.results_path)
    selected = rows[rows["policy_name"] == "SELECTED_STOP_TARGET_POLICY"].iloc[0]
    tp1 = rows[rows["policy_name"] == "TP1_BE_WITH_SELECTED_STOP_POLICY"].iloc[0]

    assert len(rows) == 2
    assert set(rows["setup_reference_used_as_entry"].astype(str).str.lower()) == {"false"}
    assert selected["setup_reference_level"] == 59628.3709
    assert selected["tradable_entry_anchor"] == 61244.7
    assert selected["selected_research_stop_reference"] == 62200.0
    assert selected["selected_research_stop_type"] == "structural_zone_stop"
    assert selected["selected_research_stop_reference"] != 61395.3
    assert selected["target_touched"] is True or str(selected["target_touched"]).lower() == "true"
    assert selected["policy_outcome_label"] == "TARGET_BEFORE_SELECTED_STOP"
    assert tp1["tp1_touched"] is True or str(tp1["tp1_touched"]).lower() == "true"
    assert tp1["policy_outcome_label"] == "TP1_THEN_TARGET"


def test_policy_replay_fixed_stops_cli_writes_required_outputs(tmp_path: Path):
    focus, stops, verdicts, feed = _write_inputs(tmp_path)
    out = tmp_path / "out"

    code = main(
        [
            "--focus-alignment",
            str(focus),
            "--structural-stops",
            str(stops),
            "--manual-verdicts",
            str(verdicts),
            "--feed-dir",
            str(feed),
            "--out-dir",
            str(out),
        ]
    )

    manifest = json.loads((out / "policy_replay_fixed_stop_manifest.json").read_text(encoding="utf-8"))

    assert code == 0
    assert (out / "policy_replay_fixed_stop_results.csv").exists()
    assert (out / "policy_replay_fixed_stop_summary.md").exists()
    assert manifest["setup_reference_level_used_as_entry"] is False
    assert manifest["sample_expanded"] is False
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False
    assert manifest["uses_pnl"] is False


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    focus = tmp_path / "focus_setup_alignment_check.csv"
    stops = tmp_path / "structural_stop_reference_candidates.csv"
    verdicts = tmp_path / "armed_setup_manual_verdicts.csv"
    feed = tmp_path / "feed"
    feed.mkdir()

    pd.DataFrame(
        [
            {
                "focus_timestamp": "2026-06-25T11:59:00Z",
                "expected_setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "alignment_verdict": "MATCH",
            }
        ]
    ).to_csv(focus, index=False)
    pd.DataFrame(
        [
            {
                "setup_id": "setup_000006",
                "setup_formed_at": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "direction_context": "DOWN",
                "sequence_role": "CORRECTION_END_ENTRY_SETUP",
                "actual_setup_price": 61244.7,
                "tradable_entry_anchor": 61244.7,
                "setup_reference_level": 59628.3709,
                "target_reference": "zone_000102:SELL_SIDE:59500.93465-59560.46535",
                "selected_research_stop_reference": 62200.0,
                "selected_research_stop_type": "structural_zone_stop",
            }
        ]
    ).to_csv(stops, index=False)
    pd.DataFrame(
        [
            {
                "setup_id": "setup_000006",
                "interval_id": "interval_2026_06_21_to_2026_06_28",
                "setup_formed_at": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "direction_context": "DOWN",
                "sequence_role": "CORRECTION_END_ENTRY_SETUP",
                "research_action": "KEEP_FOR_SWING_STOP_REPLAY",
            }
        ]
    ).to_csv(verdicts, index=False)
    pd.DataFrame(
        [
            _feed_row("2026-06-25 12:00:00", 61244.7, 61400.0, 60600.0, 60700.0),
            _feed_row("2026-06-25 12:01:00", 60700.0, 60720.0, 59540.0, 59600.0),
            _feed_row("2026-06-25 12:02:00", 59600.0, 60000.0, 59400.0, 59900.0),
        ]
    ).to_csv(feed / "2026-06-25.csv", index=False)
    return focus, stops, verdicts, feed


def _feed_row(ts: str, open_price: float, high: float, low: float, close: float) -> dict[str, object]:
    return {
        "Timestamp": ts,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": 1,
        "AggTrades": 1,
        "BuyQty": 0.4,
        "SellQty": 0.6,
        "VWAP": close,
        "OpenInterest": 1,
        "FundingRate": 0,
        "LiqBuyQty": 0,
        "LiqSellQty": 0,
        "IsSynthetic": 0,
    }


def test_policy_replay_fixed_stops_does_not_allow_later_tp1_after_selected_stop(tmp_path: Path):
    focus, stops, verdicts, feed = _write_inputs(tmp_path)
    pd.DataFrame(
        [
            _feed_row("2026-06-25 12:00:00", 61244.7, 62210.0, 61200.0, 62100.0),
            _feed_row("2026-06-25 12:01:00", 62100.0, 62120.0, 60200.0, 60300.0),
            _feed_row("2026-06-25 12:02:00", 60300.0, 60400.0, 59540.0, 59600.0),
        ]
    ).to_csv(feed / "2026-06-25.csv", index=False)

    result = run_policy_replay_fixed_stops(
        focus_alignment_path=focus,
        structural_stops_path=stops,
        manual_verdicts_path=verdicts,
        feed_dir=feed,
        output_dir=tmp_path / "out",
    )

    rows = pd.read_csv(result.results_path)
    tp1 = rows[rows["policy_name"] == "TP1_BE_WITH_SELECTED_STOP_POLICY"].iloc[0]

    assert tp1["selected_stop_touched_at"] == "2026-06-25T12:00:00Z"
    assert tp1["tp1_touched_at"] == "2026-06-25T12:01:00Z"
    assert tp1["target_touched_at"] == "2026-06-25T12:02:00Z"
    assert tp1["first_event"] == "SELECTED_STOP"
    assert tp1["policy_outcome_label"] == "NO_TP1_SELECTED_STOP"


def test_policy_replay_fixed_stops_regression_2026_06_23_1859_stop_before_tp1(tmp_path: Path):
    root = Path("market_monitor_runs")
    required = [
        root / "SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0" / "focus_setup_alignment_check.csv",
        root / "SHI_RESET_38H_structural_swing_stop_resolver_v0" / "structural_stop_reference_candidates.csv",
        root / "SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0" / "armed_setup_manual_verdicts.csv",
        Path("feed") / "2026-06-24.csv",
    ]
    if not all(path.exists() for path in required):
        return

    result = run_policy_replay_fixed_stops(
        focus_alignment_path=required[0],
        structural_stops_path=required[1],
        manual_verdicts_path=required[2],
        feed_dir="feed",
        output_dir=tmp_path / "out",
    )

    rows = pd.read_csv(result.results_path)
    row = rows[
        (rows["setup_formed_at"] == "2026-06-23T18:59:00Z")
        & (rows["setup_type"] == "SELLER_DOMINANCE_RETEST_DOWN_SETUP")
        & (rows["policy_name"] == "TP1_BE_WITH_SELECTED_STOP_POLICY")
    ].iloc[0]

    assert row["selected_stop_touched_at"] == "2026-06-24T00:10:00Z"
    assert row["tp1_touched_at"] == "2026-06-24T13:42:00Z"
    assert row["target_touched_at"] == "2026-06-24T16:52:00Z"
    assert row["first_event"] == "SELECTED_STOP"
    assert row["policy_outcome_label"] == "NO_TP1_SELECTED_STOP"
    assert row["policy_outcome_label"] != "TP1_THEN_TARGET"

def test_tp1_be_short_be_before_tp1_does_not_trigger():
    path = _tp1_path(
        direction="DOWN",
        entry=100.0,
        stop=110.0,
        rows=[
            _path_row("2026-01-01T00:01:00Z", high=101.0, low=99.0),
            _path_row("2026-01-01T00:02:00Z", high=100.5, low=98.0),
        ],
    )

    assert path["tp1_touched"] is False
    assert path["be_hit_after_tp1"] is False
    assert _tp1_outcome(path=path, unresolved=False, insufficient=False) != "TP1_THEN_BE"


def test_tp1_be_short_tp1_then_be_is_valid():
    path = _tp1_path(
        direction="DOWN",
        entry=100.0,
        stop=110.0,
        rows=[
            _path_row("2026-01-01T00:01:00Z", high=99.0, low=89.0),
            _path_row("2026-01-01T00:02:00Z", high=100.0, low=95.0),
        ],
    )

    assert path["tp1_touched"] is True
    assert path["be_hit_after_tp1"] is True
    assert _tp1_outcome(path=path, unresolved=False, insufficient=False) == "TP1_THEN_BE"


def test_tp1_be_short_selected_stop_before_tp1_is_terminal():
    path = _tp1_path(
        direction="DOWN",
        entry=100.0,
        stop=110.0,
        rows=[
            _path_row("2026-01-01T00:01:00Z", high=110.0, low=99.0),
            _path_row("2026-01-01T00:02:00Z", high=100.0, low=89.0),
            _path_row("2026-01-01T00:03:00Z", high=95.0, low=80.0),
        ],
    )

    assert path["tp1_touched"] is True
    assert path["target_touched"] is True
    assert path["tp1_policy_first_event"] == "SELECTED_STOP"
    assert _tp1_outcome(path=path, unresolved=False, insufficient=False) == "NO_TP1_SELECTED_STOP"


def test_tp1_be_long_be_before_tp1_does_not_trigger():
    path = _tp1_path(
        direction="UP",
        entry=100.0,
        stop=90.0,
        rows=[
            _path_row("2026-01-01T00:01:00Z", high=101.0, low=99.0),
            _path_row("2026-01-01T00:02:00Z", high=102.0, low=99.5),
        ],
    )

    assert path["tp1_touched"] is False
    assert path["be_hit_after_tp1"] is False
    assert _tp1_outcome(path=path, unresolved=False, insufficient=False) != "TP1_THEN_BE"


def test_tp1_be_same_candle_tp1_and_be_is_ambiguous():
    path = _tp1_path(
        direction="DOWN",
        entry=100.0,
        stop=110.0,
        rows=[_path_row("2026-01-01T00:01:00Z", high=100.0, low=89.0)],
    )

    assert path["tp1_touched"] is True
    assert path["be_hit_after_tp1"] is True
    assert path["tp1_be_same_bar"] is True
    assert path["tp1_policy_first_event"] == "AMBIGUOUS_SAME_BAR"
    assert _tp1_outcome(path=path, unresolved=False, insufficient=False) == "AMBIGUOUS_SAME_BAR"


def _tp1_path(*, direction: str, entry: float, stop: float, rows: list[dict[str, object]]) -> dict[str, object]:
    stop_distance = abs(stop - entry)
    tp1_price = _tp1_price(direction=direction, entry=entry, stop_distance=stop_distance)
    target = {"lower": 80.0, "upper": 80.0} if direction == "DOWN" else {"lower": 120.0, "upper": 120.0}
    return _evaluate_forward_path(
        forward=pd.DataFrame(rows),
        direction=direction,
        entry=entry,
        selected_stop=stop,
        target=target,
        stop_distance=stop_distance,
        tp1_price=tp1_price,
    )


def _path_row(ts: str, *, high: float, low: float) -> dict[str, object]:
    return {
        "_ts": pd.Timestamp(ts),
        "High": high,
        "Low": low,
    }
