from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.live_like_state_replay import FocusSetupConfig, ReplayRunConfig, run_live_like_state_replay
from market_monitor.run_live_like_state_replay import main


def test_live_like_replay_uses_only_current_and_past_rows_for_focus_setup(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed")
    verdicts, review = _write_inputs(tmp_path)

    result = run_live_like_state_replay(
        runs=[ReplayRunConfig("run_test", "2026-06-25T11:58:00Z", "2026-06-25T12:00:00Z")],
        focus_setups=[FocusSetupConfig("2026-06-25T11:59:00Z", "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP")],
        feed_dir=feed_dir,
        manual_verdicts_path=verdicts,
        review_pack_path=review,
        output_dir=tmp_path / "out",
    )

    replay = pd.read_csv(result.replay_path)
    focus = pd.read_csv(result.focus_alignment_path)
    setup_row = replay[replay["replay_timestamp"] == "2026-06-25T11:59:00Z"].iloc[0]

    assert set(replay["future_data_used_for_detection"].astype(str).str.lower()) == {"false"}
    assert setup_row["setup_type"] == "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP"
    assert setup_row["actual_setup_price"] == 61244.7
    assert setup_row["tradable_entry_anchor"] == 61244.7
    assert setup_row["setup_reference_level"] == 59628.3709
    assert setup_row["source_window_high"] == 61249.7
    assert focus.iloc[0]["alignment_verdict"] == "MATCH"


def test_live_like_replay_cli_writes_required_outputs(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed")
    verdicts, review = _write_inputs(tmp_path)
    out = tmp_path / "out"

    code = main(
        [
            "--run",
            "run_test|2026-06-25T11:58:00Z|2026-06-25T12:00:00Z",
            "--focus",
            "2026-06-25T11:59:00Z|SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
            "--feed-dir",
            str(feed_dir),
            "--manual-verdicts",
            str(verdicts),
            "--review-pack",
            str(review),
            "--out-dir",
            str(out),
        ]
    )

    manifest = json.loads((out / "live_like_replay_manifest.json").read_text(encoding="utf-8"))

    assert code == 0
    assert (out / "live_like_bar_by_bar_state_replay.csv").exists()
    assert (out / "state_transition_log.csv").exists()
    assert (out / "setup_status_transition_log.csv").exists()
    assert (out / "reference_level_transition_log.csv").exists()
    assert (out / "focus_setup_alignment_check.csv").exists()
    assert manifest["future_data_used_for_detection"] is False
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False


def _write_feed(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _feed_row("2026-06-25 11:58:00", 61230.0, 61240.0, 61220.0, 61235.0),
            _feed_row("2026-06-25 11:59:00", 61239.1, 61249.7, 61234.2, 61244.7),
            _feed_row("2026-06-25 12:00:00", 61245.0, 61280.0, 61200.0, 61270.0),
        ]
    ).to_csv(root / "2026-06-25.csv", index=False)
    return root


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    verdicts = tmp_path / "armed_setup_manual_verdicts.csv"
    review = tmp_path / "armed_setup_manual_review.csv"
    pd.DataFrame(
        [
            {
                "setup_id": "setup_000006",
                "interval_id": "interval_test",
                "setup_formed_at": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "direction_context": "DOWN",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "replay_outcome": "INVALIDATION",
                "user_verdict": "ideal setup",
                "sequence_role": "CORRECTION_END_ENTRY_SETUP",
                "research_action": "KEEP_FOR_SWING_STOP_REPLAY",
                "first_event": "INVALIDATION",
                "max_favorable_excursion_pct": 0,
                "max_adverse_excursion_pct": 0,
                "chart_data_path": "",
            }
        ]
    ).to_csv(verdicts, index=False)
    pd.DataFrame(
        [
            {
                "setup_id": "setup_000006",
                "interval_id": "interval_test",
                "setup_formed_at": "2026-06-25T11:59:00Z",
                "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
                "direction_context": "DOWN",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "source_window_start": "2026-06-25T11:58:00Z",
                "source_window_end": "2026-06-25T11:59:00Z",
                "market_state": "MARKDOWN_ABOVE_SUPPORT",
                "dominant_side": "SELLER",
                "setup_reference_level": 59628.3709,
                "actual_setup_price": 61244.7,
                "tradable_entry_anchor": 61244.7,
                "invalidation_reference": 61286.628,
                "stop_reference": 61286.628,
                "target_reference": "zone_000102:SELL_SIDE:59500.93465-59560.46535",
                "target_reference_zone": "zone_000102:SELL_SIDE:59500.93465-59560.46535",
                "target_touched": "false",
                "target_touched_at": "",
                "invalidation_touched": "false",
                "invalidation_touched_at": "",
                "first_event": "",
                "max_favorable_excursion_pct": 0,
                "max_adverse_excursion_pct": 0,
                "chart_window_start": "2026-06-25T05:59:00Z",
                "chart_window_end": "2026-06-26T11:59:00Z",
                "chart_data_path": "",
                "manual_review_question": "",
            }
        ]
    ).to_csv(review, index=False)
    return verdicts, review


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

