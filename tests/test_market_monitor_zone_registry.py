from pathlib import Path

import pandas as pd

from market_monitor.outputs import REQUIRED_CSV_SCHEMAS
from market_monitor.run_market_monitor import main
from market_monitor.zone_registry import (
    REGISTRY_COLUMNS,
    build_zone_registry,
    forward_liquidity_from_registry,
)


def test_registry_file_is_written_every_run(tmp_path: Path):
    input_file = _write_feed(tmp_path, "feed.csv", close=100)
    output_dir = tmp_path / "out"

    assert main(
        [
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    registry_path = output_dir / "liquidity_zone_registry.csv"
    assert registry_path.exists()
    assert pd.read_csv(registry_path).columns.tolist() == REGISTRY_COLUMNS
    assert "liquidity_zone_registry.csv" in REQUIRED_CSV_SCHEMAS


def test_registry_summary_lines_are_written(tmp_path: Path):
    input_file = _write_feed(tmp_path, "feed.csv", close=100)
    output_dir = tmp_path / "out"

    assert main(
        [
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    summary = (output_dir / "market_summary.md").read_text(encoding="utf-8")
    assert "Registry input:" in summary
    assert "Registry output:" in summary
    assert "Carried zones loaded:" in summary
    assert "Active registry zones:" in summary


def test_no_sweep_or_trading_statuses_are_produced():
    registry, _ = build_zone_registry(
        liquidity_map=_liquidity_map([_zone("zone_000001", "BUY_SIDE", 100, 110)]),
        feed=_path_feed([90, 120]),
    )

    statuses = set(registry["status"])
    assert "SWEPT_REJECTED" not in statuses
    assert "SWEPT_ACCEPTED" not in statuses
    assert "signal" not in registry.columns
    assert "order" not in registry.columns
    assert "position" not in registry.columns


def test_too_wide_registry_zone_is_not_emitted_as_forward_liquidity():
    registry = pd.DataFrame(
        [
            {
                **_zone("zone_000001", "BUY_SIDE", 70000, 70550),
                "first_seen_at": "2026-05-07T00:00:00Z",
                "precision_status": "TOO_WIDE",
            },
            {
                **_zone("zone_000002", "BUY_SIDE", 71000, 71070),
                "first_seen_at": "2026-05-07T00:00:00Z",
                "precision_status": "PRECISE",
            },
        ]
    )

    forward = forward_liquidity_from_registry(registry, latest_close=65000)

    assert forward["zone_id"].tolist() == ["zone_000002"]
    assert "precision_status" in forward.columns


def _write_feed(tmp_path: Path, filename: str, close: float) -> Path:
    path = tmp_path / filename
    path.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                f"2026-05-07T00:00:00Z,{close},{close + 1},{close - 1},{close},10,1,5,5,1000,0.0001",
                f"2026-05-07T23:59:00Z,{close},{close + 2},{close - 2},{close},10,1,5,5,1000,0.0001",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _liquidity_map(rows):
    return pd.DataFrame(rows)


def _zone(zone_id, side, lower, upper, quality="RAW"):
    return {
        "zone_id": zone_id,
        "created_at": "2026-05-07T00:00:00Z",
        "last_updated_at": "2026-05-07T00:00:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE" if side == "BUY_SIDE" else "H1_SWING_LOW_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": "ACTIVE",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "touch_count": 1,
        "sweep_count": 0,
        "distance_from_close_pct": 0,
        "data_quality": quality,
        "invalidation_reason": "",
    }


def _path_feed(closes):
    rows = []
    for idx, close in enumerate(closes):
        rows.append(
            {
                "Timestamp": pd.Timestamp(f"2026-05-08T00:0{idx}:00Z"),
                "OpenPrice": close,
                "HiPrice": close,
                "LowPrice": close,
                "ClosePrice": close,
                "TotalQty": 10,
                "Trades": 1,
                "BuyQty": 5,
                "SellQty": 5,
                "OpenInterest": 1000,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceFile": "synthetic.csv",
            }
        )
    return pd.DataFrame(rows)
