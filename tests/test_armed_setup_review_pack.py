from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.armed_setup_review_pack import ARMED_REVIEW_COLUMNS, ReviewIntervalInput, run_armed_setup_review_pack
from market_monitor.run_armed_setup_review_pack import main


def test_review_pack_includes_only_armed_rows_and_writes_chart_data(tmp_path: Path):
    replay = _write_replay_results(tmp_path / "setup_replay_results.csv")
    timeline = _write_timeline(tmp_path / "setup_research_timeline.csv")
    feed_dir = _write_feed(tmp_path / "feed")

    result = run_armed_setup_review_pack(
        replay_results_path=replay,
        intervals=[
            ReviewIntervalInput(
                "interval_test",
                "2026-03-25T00:00:00Z",
                "2026-03-27T23:59:00Z",
                timeline,
            )
        ],
        feed_dir=feed_dir,
        output_dir=tmp_path / "out",
    )

    review = pd.read_csv(result.review_path)
    chart_files = sorted((tmp_path / "out" / "chart_data").glob("*.csv"))
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert review.columns.tolist() == ARMED_REVIEW_COLUMNS
    assert len(review) == 2
    assert set(review["setup_id"]) == {"setup_000001", "setup_000003"}
    assert set(review["source_time_precision"]) == {"RAW_REGIME_WINDOW_60M", "RAW_REGIME_WINDOW_1440M"}
    assert len(chart_files) == 2
    assert manifest["watch_rows_excluded"] == 1
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False
    assert manifest["uses_pnl"] is False


def test_chart_windows_follow_precision_rules_and_cli(tmp_path: Path):
    replay = _write_replay_results(tmp_path / "setup_replay_results.csv")
    timeline = _write_timeline(tmp_path / "setup_research_timeline.csv")
    feed_dir = _write_feed(tmp_path / "feed")
    out = tmp_path / "out"

    code = main(
        [
            "--replay-results",
            str(replay),
            "--interval",
            f"interval_test|2026-03-25T00:00:00Z|2026-03-27T23:59:00Z|{timeline}|",
            "--feed-dir",
            str(feed_dir),
            "--out-dir",
            str(out),
        ]
    )

    review = pd.read_csv(out / "armed_setup_manual_review.csv")
    by_id = {row["setup_id"]: row for _, row in review.iterrows()}

    assert code == 0
    assert by_id["setup_000001"]["chart_window_start"] == "2026-03-26T01:59:00Z"
    assert by_id["setup_000001"]["chart_window_end"] == "2026-03-27T07:59:00Z"
    assert by_id["setup_000003"]["chart_window_start"] == "2026-03-25T07:59:00Z"
    assert by_id["setup_000003"]["chart_window_end"] == "2026-03-28T07:59:00Z"
    assert "Should this setup_type be kept" in by_id["setup_000001"]["manual_review_question"]


def _write_replay_results(path: Path) -> Path:
    pd.DataFrame(
        [
            _replay_row("setup_000001", "ARMED", "2026-03-26T07:59:00Z"),
            _replay_row("setup_000002", "WATCH", "2026-03-26T08:59:00Z"),
            _replay_row("setup_000003", "ARMED", "2026-03-26T07:59:00Z"),
        ]
    ).to_csv(path, index=False)
    return path


def _write_timeline(path: Path) -> Path:
    pd.DataFrame(
        [
            {
                "setup_id": "setup_000001",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "source_window_start": "2026-03-26T07:00:00Z",
                "source_window_end": "2026-03-26T07:59:00Z",
                "market_state": "PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE",
                "dominant_side": "SELLER",
                "entry_reference_level": 100.0,
                "invalidation_level": 106.0,
                "target_reference_zone": "zone_demand:SELL_SIDE:92.0-94.0",
            },
            {
                "setup_id": "setup_000002",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "source_window_start": "2026-03-26T08:00:00Z",
                "source_window_end": "2026-03-26T08:59:00Z",
                "market_state": "MARKDOWN_ABOVE_SUPPORT",
                "dominant_side": "SELLER",
                "entry_reference_level": 100.0,
                "invalidation_level": 95.0,
                "target_reference_zone": "zone_supply:BUY_SIDE:106.0-108.0",
            },
            {
                "setup_id": "setup_000003",
                "source_time_precision": "RAW_REGIME_WINDOW_1440M",
                "source_window_start": "2026-03-25T08:00:00Z",
                "source_window_end": "2026-03-26T07:59:00Z",
                "market_state": "PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE",
                "dominant_side": "SELLER",
                "entry_reference_level": 100.0,
                "invalidation_level": 106.0,
                "target_reference_zone": "zone_demand:SELL_SIDE:92.0-94.0",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _write_feed(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for day in ["2026-03-25", "2026-03-26", "2026-03-27", "2026-03-28"]:
        pd.DataFrame(
            [
                {
                    "Timestamp": f"{day} 00:00:00",
                    "Open": 100,
                    "High": 101,
                    "Low": 99,
                    "Close": 100,
                    "Volume": 1,
                    "AggTrades": 1,
                    "BuyQty": 0.5,
                    "SellQty": 0.5,
                    "VWAP": 100,
                    "OpenInterest": 1,
                    "FundingRate": 0,
                    "LiqBuyQty": 0,
                    "LiqSellQty": 0,
                    "IsSynthetic": 0,
                }
            ]
        ).to_csv(root / f"{day}.csv", index=False)
    return root


def _replay_row(setup_id: str, trigger_status: str, formed_at: str) -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "interval_id": "interval_test",
        "setup_formed_at": formed_at,
        "setup_type": "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
        "direction_context": "DOWN",
        "trigger_status": trigger_status,
        "source_time_precision": "RAW_REGIME_WINDOW_60M",
        "evaluation_start": "2026-03-26T08:00:00Z",
        "evaluation_end": "2026-03-27T23:59:00Z",
        "entry_reference_price": 100,
        "invalidation_reference": 106,
        "target_reference_zone": "zone_demand:SELL_SIDE:92.0-94.0",
        "max_favorable_excursion_pct": 3.5,
        "max_adverse_excursion_pct": -1.0,
        "target_touched": "true",
        "target_touched_at": "2026-03-26T10:00:00Z",
        "invalidation_touched": "false",
        "invalidation_touched_at": "",
        "first_event": "TARGET",
        "outcome_label": "TARGET_FIRST",
        "evidence_summary": "replay evidence",
    }
