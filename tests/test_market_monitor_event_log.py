import json
from pathlib import Path

import pandas as pd

from market_monitor.events import EVENT_LOG_COLUMNS, build_event_log
from market_monitor.run_market_monitor import main


def test_event_log_csv_is_always_written_with_exact_schema(tmp_path: Path):
    input_file = tmp_path / "feed.csv"
    input_file.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                "2026-05-07T00:00:00Z,100,101,99,100,10,1,5,5,1000,0.0001",
                "2026-05-07T23:59:00Z,100,101,99,100,10,1,5,5,1000,0.0001",
            ]
        ),
        encoding="utf-8",
    )
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

    assert pd.read_csv(output_dir / "event_log.csv").columns.tolist() == EVENT_LOG_COLUMNS


def test_event_ids_and_evidence_json_are_deterministic():
    registry = pd.DataFrame([_registry_row("zone_000001", "ACTIVE", "BUY_SIDE", 100, 110)])
    feed = _feed([90, 101])
    volume_delta = _volume_delta(feed)

    first = build_event_log(registry=registry, feed=feed, volume_delta_state=volume_delta)
    second = build_event_log(registry=registry, feed=feed, volume_delta_state=volume_delta)

    assert first.equals(second)
    assert first.loc[0, "event_id"] == "event_000001"
    evidence = json.loads(first.loc[0, "evidence_json"])
    assert list(evidence.keys()) == sorted(evidence.keys())
    assert evidence["zone_id"] == "zone_000001"


def _registry_row(zone_id, status, side, lower, upper):
    return {
        "zone_id": zone_id,
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": side,
        "zone_type": "H1_SWING_HIGH_ZONE" if side == "BUY_SIDE" else "H1_SWING_LOW_ZONE",
        "price_lower": lower,
        "price_upper": upper,
        "price_mid": (lower + upper) / 2,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": status,
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "age_bars": 2,
        "age_days": 0,
        "touch_count": 1,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "2026-05-08T00:01:00Z",
        "last_cross_at": "",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _feed(closes):
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
                "OpenInterest": 1000 + idx,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceFile": "synthetic.csv",
            }
        )
    return pd.DataFrame(rows)


def _volume_delta(feed):
    return pd.DataFrame(
        {
            "timestamp": feed["Timestamp"].map(lambda value: value.isoformat().replace("+00:00", "Z")),
            "volume_zscore": [0.0] * len(feed),
            "delta_zscore": [0.0] * len(feed),
            "oi_change": [0.0] * len(feed),
        }
    )
