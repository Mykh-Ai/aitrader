from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.run_structural_stop_resolver import main
from market_monitor.structural_stop_resolver import run_structural_stop_resolver


def test_structural_stop_resolver_keeps_price_reference_contract_and_compares_stop_candidates(tmp_path: Path):
    live_like, focus, verdicts = _write_inputs(tmp_path)

    result = run_structural_stop_resolver(
        live_like_replay_path=live_like,
        focus_alignment_path=focus,
        manual_verdicts_path=verdicts,
        output_dir=tmp_path / "out",
    )

    candidates = pd.read_csv(result.candidates_path)
    row = candidates.iloc[0]

    assert row["setup_formed_at"] == "2026-06-25T11:59:00Z"
    assert row["actual_setup_price"] == 61244.7
    assert row["tradable_entry_anchor"] == 61244.7
    assert row["setup_reference_level"] == 59628.3709
    assert row["source_window_high"] == 61395.3
    assert row["source_window_stop_reference"] == 61395.3
    assert row["local_swing_high_candidate"] == 61897.6
    assert row["local_swing_stop_reference"] == 61897.6
    assert row["structural_zone_lower"] == 62000.0
    assert row["structural_zone_upper"] == 62200.0
    assert row["structural_zone_role"] == "support_resistance_flip_review_zone"
    assert row["structural_zone_stop_reference"] == 62200.0
    assert row["selected_research_stop_reference"] == 62200.0
    assert row["selected_research_stop_type"] == "structural_zone_stop"
    assert "setup_reference_is_not_entry=true" in row["evidence_summary"]


def test_structural_stop_resolver_cli_writes_required_outputs(tmp_path: Path):
    live_like, focus, verdicts = _write_inputs(tmp_path)
    out = tmp_path / "out"

    code = main(
        [
            "--live-like-replay",
            str(live_like),
            "--focus-alignment",
            str(focus),
            "--manual-verdicts",
            str(verdicts),
            "--out-dir",
            str(out),
        ]
    )

    manifest = json.loads((out / "structural_stop_resolver_manifest.json").read_text(encoding="utf-8"))

    assert code == 0
    assert (out / "structural_stop_reference_candidates.csv").exists()
    assert (out / "structural_stop_resolver_summary.md").exists()
    assert manifest["changes_setup_detection_logic"] is False
    assert manifest["changes_setup_builder"] is False
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False
    assert manifest["uses_pnl"] is False


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    live_like = tmp_path / "live_like_bar_by_bar_state_replay.csv"
    focus = tmp_path / "focus_setup_alignment_check.csv"
    verdicts = tmp_path / "armed_setup_manual_verdicts.csv"

    pd.DataFrame(
        [
            {
                "replay_timestamp": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "setup_reference_level": 59628.3709,
                "actual_setup_price": 61244.7,
                "tradable_entry_anchor": 61244.7,
                "target_reference": "zone_000102:SELL_SIDE:59500.93465-59560.46535",
                "stop_reference": 61286.628,
                "source_window_high": 61395.3,
                "source_window_low": 61033.5,
                "local_swing_high_candidate": 61897.6,
                "local_swing_low_candidate": 61033.5,
                "structural_zone_context": "below_62000_62200_support_resistance_flip_review_zone",
            }
        ]
    ).to_csv(live_like, index=False)
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
                "interval_id": "interval_2026_06_21_to_2026_06_28",
                "setup_formed_at": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "direction_context": "DOWN",
                "sequence_role": "CORRECTION_END_ENTRY_SETUP",
                "research_action": "KEEP_FOR_SWING_STOP_REPLAY",
            }
        ]
    ).to_csv(verdicts, index=False)
    return live_like, focus, verdicts
