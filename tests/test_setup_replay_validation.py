from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.run_setup_replay_validation import main
from market_monitor.setup_replay_validation import SETUP_REPLAY_COLUMNS, ReplayInterval, run_setup_replay_validation


def test_down_setup_replay_records_target_first(tmp_path: Path):
    timeline = _write_timeline(
        tmp_path / "setup_research_timeline.csv",
        [
            {
                "setup_id": "setup_000001",
                "setup_formed_at": "2026-06-01T12:59:00Z",
                "setup_type": "SELLER_DOMINANCE_RETEST_DOWN_SETUP",
                "direction_context": "DOWN",
                "trigger_status": "ARMED",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "entry_reference_level": 100.0,
                "invalidation_level": 106.0,
                "target_reference_zone": "zone_demand:SELL_SIDE:92.0-94.0",
                "evidence_summary": "source setup",
            }
        ],
    )
    feed_dir = _write_feed(
        tmp_path / "feed",
        [
            ("2026-06-01 12:59:00", 100.0, 100.5, 99.8, 100.0),
            ("2026-06-01 13:00:00", 100.0, 101.0, 96.0, 97.0),
            ("2026-06-01 13:01:00", 97.0, 98.0, 93.5, 94.0),
            ("2026-06-01 13:02:00", 94.0, 107.0, 93.0, 106.0),
        ],
    )

    result = run_setup_replay_validation(
        intervals=[
            ReplayInterval(
                "interval_test",
                "2026-06-01T00:00:00Z",
                "2026-06-01T23:59:00Z",
                timeline,
                tmp_path / "setup_builder_manifest.json",
            )
        ],
        feed_dir=feed_dir,
        output_dir=tmp_path / "out",
    )

    rows = pd.read_csv(result.results_path)

    assert rows.columns.tolist() == SETUP_REPLAY_COLUMNS
    assert rows.iloc[0]["target_touched"] is True or str(rows.iloc[0]["target_touched"]).lower() == "true"
    assert rows.iloc[0]["invalidation_touched"] is True or str(rows.iloc[0]["invalidation_touched"]).lower() == "true"
    assert rows.iloc[0]["first_event"] == "TARGET"
    assert rows.iloc[0]["outcome_label"] == "BOTH_TARGET_AND_INVALIDATION_TARGET_FIRST"
    assert rows.iloc[0]["max_favorable_excursion_pct"] == 7.0
    assert rows.iloc[0]["max_adverse_excursion_pct"] == -7.0


def test_up_setup_replay_records_invalidation_first(tmp_path: Path):
    timeline = _write_timeline(
        tmp_path / "setup_research_timeline.csv",
        [
            {
                "setup_id": "setup_000002",
                "setup_formed_at": "2026-03-25T01:59:00Z",
                "setup_type": "DEMAND_SWEEP_RECLAIM_UP_SETUP",
                "direction_context": "UP",
                "trigger_status": "WATCH",
                "source_time_precision": "RAW_REGIME_WINDOW_60M",
                "entry_reference_level": 100.0,
                "invalidation_level": 95.0,
                "target_reference_zone": "zone_supply:BUY_SIDE:106.0-108.0",
                "evidence_summary": "source setup",
            }
        ],
    )
    feed_dir = _write_feed(
        tmp_path / "feed",
        [
            ("2026-03-25 02:00:00", 100.0, 101.0, 94.0, 95.0),
            ("2026-03-25 02:01:00", 95.0, 106.5, 94.5, 106.0),
        ],
    )

    result = run_setup_replay_validation(
        intervals=[ReplayInterval("interval_test", "2026-03-25T00:00:00Z", "2026-03-25T23:59:00Z", timeline)],
        feed_dir=feed_dir,
        output_dir=tmp_path / "out",
    )

    rows = pd.read_csv(result.results_path)

    assert rows.iloc[0]["first_event"] == "INVALIDATION"
    assert rows.iloc[0]["outcome_label"] == "BOTH_TARGET_AND_INVALIDATION_INVALIDATION_FIRST"
    assert rows.iloc[0]["max_favorable_excursion_pct"] == 6.5
    assert rows.iloc[0]["max_adverse_excursion_pct"] == -6.0


def test_unresolved_reference_still_records_mfe_mae_and_cli(tmp_path: Path):
    timeline = _write_timeline(
        tmp_path / "setup_research_timeline.csv",
        [
            {
                "setup_id": "setup_000003",
                "setup_formed_at": "2026-03-25T01:59:00Z",
                "setup_type": "DEMAND_SWEEP_RECLAIM_UP_SETUP",
                "direction_context": "UP",
                "trigger_status": "WATCH",
                "source_time_precision": "STATE_WINDOW",
                "entry_reference_level": 100.0,
                "invalidation_level": "",
                "target_reference_zone": "",
                "evidence_summary": "source setup",
            }
        ],
    )
    feed_dir = _write_feed(
        tmp_path / "feed",
        [
            ("2026-03-25 02:00:00", 100.0, 103.0, 99.0, 101.0),
            ("2026-03-25 02:01:00", 101.0, 104.0, 98.0, 102.0),
        ],
    )
    output_dir = tmp_path / "out"

    code = main(
        [
            "--interval",
            f"interval_test|2026-03-25T00:00:00Z|2026-03-25T23:59:00Z|{timeline}|",
            "--feed-dir",
            str(feed_dir),
            "--out-dir",
            str(output_dir),
        ]
    )

    rows = pd.read_csv(output_dir / "setup_replay_results.csv")
    manifest = json.loads((output_dir / "setup_replay_manifest.json").read_text(encoding="utf-8"))

    assert code == 0
    assert rows.iloc[0]["outcome_label"] == "TARGET_OR_INVALIDATION_UNRESOLVED"
    assert rows.iloc[0]["max_favorable_excursion_pct"] == 4.0
    assert rows.iloc[0]["max_adverse_excursion_pct"] == -2.0
    assert manifest["changes_setup_detection_logic"] is False
    assert manifest["uses_backtester"] is False
    assert manifest["uses_executor"] is False


def _write_timeline(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_feed(root: Path, rows: list[tuple[str, float, float, float, float]]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        [
            {
                "Timestamp": ts,
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": 1,
                "AggTrades": 1,
                "BuyQty": 0.5,
                "SellQty": 0.5,
                "VWAP": close,
                "OpenInterest": 1,
                "FundingRate": 0,
                "LiqBuyQty": 0,
                "LiqSellQty": 0,
                "IsSynthetic": 0,
            }
            for ts, open_price, high, low, close in rows
        ]
    )
    day = rows[0][0][:10]
    frame.to_csv(root / f"{day}.csv", index=False)
    return root
