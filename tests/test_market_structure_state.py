from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.market_structure_state import (
    MARKET_STRUCTURE_EVENT_COLUMNS,
    MARKET_STRUCTURE_LEVEL_COLUMNS,
    MARKET_STRUCTURE_STATE_COLUMNS,
    run_market_structure_state,
)
from market_monitor.run_market_structure_state import main


def test_market_structure_state_builds_level_memory_and_state_sequence(tmp_path: Path):
    input_root = _write_daily_outputs(tmp_path / "daily")
    feed_dir = _write_feed(tmp_path / "feed")

    result = run_market_structure_state(
        input_root=input_root,
        feed_dir=feed_dir,
        output_dir=tmp_path / "state",
        start="2026-03-29",
        end="2026-04-07",
        as_of="2026-04-07T18:00:00",
    )

    levels = pd.read_csv(result.levels_path)
    events = pd.read_csv(result.events_path)
    states = pd.read_csv(result.state_timeline_path)

    assert levels.columns.tolist() == MARKET_STRUCTURE_LEVEL_COLUMNS
    assert events.columns.tolist() == MARKET_STRUCTURE_EVENT_COLUMNS
    assert states.columns.tolist() == MARKET_STRUCTURE_STATE_COLUMNS
    assert "FAILED_BREAKDOWN_RECLAIM" in set(events["event_type"])
    assert _has_band_covering(levels, 65468, 65970, role="SUPPORT")
    assert "UP_EXPANSION_INTO_MAJOR_RESISTANCE" in set(states["market_state"])
    assert "FAILED_CONTINUATION_ABOVE_ROUND_LEVEL" in set(states["market_state"])
    assert states.iloc[-1]["market_state"] == "PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE"
    assert states.iloc[-1]["candidate_bias"] == "MIXED"
    assert "UNCONFIRMED" in states.iloc[-1]["oi_context"]


def test_as_of_uses_completed_daily_artifacts_only_for_intraday_state(tmp_path: Path):
    input_root = _write_daily_outputs(tmp_path / "daily")
    feed_dir = _write_feed(tmp_path / "feed")

    result = run_market_structure_state(
        input_root=input_root,
        feed_dir=feed_dir,
        output_dir=tmp_path / "state",
        start="2026-04-05",
        end="2026-04-07",
        as_of="2026-04-07T18:00:00",
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    states = pd.read_csv(result.state_timeline_path)

    assert manifest["completed_daily_artifacts_through"] == "2026-04-06"
    assert states.iloc[-1]["end_timestamp"] == "2026-04-07T18:00:00Z"


def test_market_structure_state_cli_writes_outputs(tmp_path: Path):
    input_root = _write_daily_outputs(tmp_path / "daily")
    feed_dir = _write_feed(tmp_path / "feed")
    output_dir = tmp_path / "state"

    code = main(
        [
            "--start",
            "2026-04-05",
            "--end",
            "2026-04-07",
            "--input-root",
            str(input_root),
            "--feed-dir",
            str(feed_dir),
            "--out-dir",
            str(output_dir),
            "--as-of",
            "2026-04-07T18:00:00",
        ]
    )

    assert code == 0
    assert (output_dir / "market_structure_levels.csv").exists()
    assert (output_dir / "market_structure_events.csv").exists()
    assert (output_dir / "market_structure_state_timeline.csv").exists()
    assert (output_dir / "market_structure_state_summary.md").exists()
    assert (output_dir / "market_structure_state_manifest.json").exists()


def _has_band_covering(levels: pd.DataFrame, lower: float, upper: float, *, role: str) -> bool:
    matching = levels[
        (levels["role"] == role)
        & (pd.to_numeric(levels["price_lower"]) <= lower + 1)
        & (pd.to_numeric(levels["price_upper"]) >= upper - 1)
    ]
    return not matching.empty


def _write_daily_outputs(root: Path) -> Path:
    for day in [
        "2026-03-29",
        "2026-03-30",
        "2026-03-31",
        "2026-04-01",
        "2026-04-02",
        "2026-04-03",
        "2026-04-04",
        "2026-04-05",
        "2026-04-06",
        "2026-04-07",
    ]:
        day_dir = root / day
        day_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(_registry_rows(day)).to_csv(day_dir / "liquidity_zone_registry.csv", index=False)
        pd.DataFrame(_post_sweep_rows() if day == "2026-03-29" else []).to_csv(
            day_dir / "post_sweep_observation.csv",
            index=False,
        )
    return root


def _registry_rows(day: str) -> list[dict[str, object]]:
    return [
        _registry_row("zone_support_1", "SELL_SIDE", 65468.2495, 65533.7505, 65501.0, day, confidence=85, cross=1),
        _registry_row("zone_support_2", "SELL_SIDE", 65643.26195, 65787.0771, 65715.169525, day, confidence=85),
        _registry_row("zone_support_3", "SELL_SIDE", 65855.056, 65970.969, 65913.0125, day, confidence=85),
        _registry_row("zone_local_resistance", "BUY_SIDE", 67250.358, 67648.70745, 67449.532725, day, confidence=85),
        _registry_row("zone_major_1", "BUY_SIDE", 68114.3258, 68182.4742, 68148.4, day, confidence=85),
        _registry_row("zone_major_2", "BUY_SIDE", 68739.51305, 68973.2694, 68856.391225, day, confidence=85),
        _registry_row("zone_major_3", "BUY_SIDE", 69073.446, 69322.644, 69198.045, day, confidence=97),
    ]


def _registry_row(
    zone_id: str,
    side: str,
    lower: float,
    upper: float,
    mid: float,
    day: str,
    *,
    confidence: int,
    cross: int = 0,
) -> dict[str, object]:
    return {
        "zone_id": zone_id,
        "first_seen_at": "2026-03-27T00:00:00Z",
        "last_seen_at": f"{day}T23:59:00Z",
        "last_updated_at": f"{day}T23:59:00Z",
        "side": side,
        "zone_type": "CLUSTERED_SELL_SIDE_ZONE" if side == "SELL_SIDE" else "CLUSTERED_BUY_SIDE_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": mid,
        "source_level_ids": "level_a|level_b",
        "source_timeframes": "CLUSTER|H1|H4|SESSION",
        "status": "ACTIVE",
        "confidence_score": confidence,
        "confidence_tier": "HIGH",
        "age_bars": 0,
        "age_days": 7,
        "touch_count": 2,
        "cross_count": cross,
        "active_days": 8,
        "last_touch_at": "2026-03-29T22:46:00Z" if side == "SELL_SIDE" else "",
        "last_cross_at": "2026-03-29T22:46:00Z" if cross else "",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _post_sweep_rows() -> list[dict[str, object]]:
    return [
        {
            "observation_id": "observation_000001",
            "source_event_id": "event_000001",
            "source_event_timestamp": "2026-03-29T22:46:00Z",
            "market_move_id": "move_20260329_224600_SELL_SIDE_000001",
            "zone_id": "zone_support_1",
            "side": "SELL_SIDE",
            "zone_type": "CLUSTERED_SELL_SIDE_ZONE",
            "zone_price_lower": 65468.2495,
            "zone_price_upper": 65533.7505,
            "zone_price_mid": 65501.0,
            "confidence_score": 85,
            "confidence_tier": "HIGH",
            "net_close_change_pct": 1.24,
            "bars_above_zone": 21,
            "bars_below_zone": 9,
            "max_return_inside_zone": 882.15,
            "max_excursion_beyond_zone": 550.04,
        }
    ]


def _write_feed(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    feed_by_day = {
        "2026-03-29": [
            _feed_row("2026-03-29 00:00:00", 66300, 67100, 64918, 65985, 1000, 530, 470, 90000),
            _feed_row("2026-03-29 23:59:00", 65985, 66350, 64918, 66042, 1000, 560, 440, 90200),
        ],
        "2026-03-30": [
            _feed_row("2026-03-30 00:00:00", 66042, 68148, 65754, 66717, 1000, 540, 460, 90400),
            _feed_row("2026-03-30 23:59:00", 66717, 68148, 65754, 66717, 1000, 510, 490, 90500),
        ],
        "2026-03-31": [
            _feed_row("2026-03-31 00:00:00", 66717, 68600, 65938, 68255, 1000, 535, 465, 90600),
            _feed_row("2026-03-31 23:59:00", 68255, 68600, 65938, 68255, 1000, 520, 480, 90700),
        ],
        "2026-04-01": [
            _feed_row("2026-04-01 00:00:00", 68255, 69288, 67534, 68071, 1000, 500, 500, 90800),
            _feed_row("2026-04-01 23:59:00", 68071, 69288, 67534, 68071, 1000, 490, 510, 90900),
        ],
        "2026-04-02": [
            _feed_row("2026-04-02 00:00:00", 66800, 68639, 65676, 66863, 1000, 505, 495, 89910),
            _feed_row("2026-04-02 23:59:00", 66863, 67500, 66123, 66870, 1000, 510, 490, 90400),
        ],
        "2026-04-03": [
            _feed_row("2026-04-03 00:00:00", 66870, 67350, 66240, 66921, 1000, 505, 495, 90400),
            _feed_row("2026-04-03 23:59:00", 66921, 67300, 66240, 66930, 1000, 505, 495, 90500),
        ],
        "2026-04-04": [
            _feed_row("2026-04-04 00:00:00", 66930, 67554, 66745, 67271, 1000, 520, 480, 90275),
            _feed_row("2026-04-04 23:59:00", 67271, 67554, 66745, 67271, 1000, 520, 480, 91400),
        ],
        "2026-04-05": [
            _feed_row("2026-04-05 00:00:00", 67271, 67828, 66575, 67378, 1000, 530, 470, 91400),
            _feed_row("2026-04-05 20:00:00", 67378, 67681, 67250, 67636, 1000, 670, 330, 89944),
            _feed_row("2026-04-05 23:59:00", 67636, 69108, 67313, 68992, 1000, 575, 425, 91016),
        ],
        "2026-04-06": [
            _feed_row("2026-04-06 00:00:00", 68997, 70332, 68227, 68821, 1000, 498, 502, 91016),
            _feed_row("2026-04-06 23:59:00", 68821, 70332, 68227, 68821, 1000, 495, 505, 91500),
        ],
        "2026-04-07": [
            _feed_row("2026-04-07 00:00:00", 68818, 69219, 67711, 68670, 1000, 504, 496, 91500),
            _feed_row("2026-04-07 18:00:00", 68670, 68670, 68652, 68670, 1000, 500, 500, 89041),
            _feed_row("2026-04-07 23:59:00", 68670, 69000, 68000, 68400, 1000, 500, 500, 88800),
        ],
    }
    for day, rows in feed_by_day.items():
        pd.DataFrame(rows).to_csv(root / f"{day}.csv", index=False)
    return root


def _feed_row(
    timestamp: str,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    buy_qty: float,
    sell_qty: float,
    oi: float,
) -> dict[str, object]:
    return {
        "Timestamp": timestamp,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
        "AggTrades": 1,
        "BuyQty": buy_qty,
        "SellQty": sell_qty,
        "VWAP": close,
        "OpenInterest": oi,
        "FundingRate": 0.0,
        "LiqBuyQty": 0.0,
        "LiqSellQty": 0.0,
        "IsSynthetic": 0,
    }
