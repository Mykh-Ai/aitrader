from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.policy_replay_fixed_stops import run_policy_replay_fixed_stops
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
