from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import (
    POST_SWEEP_OBSERVATION_BARS,
    POST_SWEEP_OBSERVATION_COLUMNS,
    build_post_sweep_observations,
)
from market_monitor.run_market_monitor import main


def test_post_sweep_observation_csv_is_always_written_header_only_without_unresolved(tmp_path: Path):
    input_file = tmp_path / "feed.csv"
    input_file.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                "2026-05-08T00:00:00Z,100,101,99,100,10,1,5,5,1000,0.0001",
                "2026-05-08T00:01:00Z,100,101,99,100,10,1,5,5,1000,0.0001",
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

    output_file = output_dir / "post_sweep_observation.csv"
    assert output_file.exists()
    observation = pd.read_csv(output_file)
    assert observation.columns.tolist() == POST_SWEEP_OBSERVATION_COLUMNS
    assert observation.empty


def test_buy_side_unresolved_event_creates_complete_observation_after_event_candle():
    event_log = pd.DataFrame([_event_row(side="BUY_SIDE")])
    feed = _buy_feed(POST_SWEEP_OBSERVATION_BARS)

    observation = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=_volume_delta(feed),
    )

    row = observation.iloc[0]
    assert row["observation_id"] == "observation_000001"
    assert row["source_event_id"] == "event_000002"
    assert row["observation_start_timestamp"] == "2026-05-08T00:02:00Z"
    assert row["observation_bars_expected"] == 30
    assert row["observation_bars_available"] == 30
    assert row["observation_complete"] == True


def test_incomplete_observation_written_when_future_window_is_short():
    event_log = pd.DataFrame([_event_row(side="BUY_SIDE")])
    feed = _buy_feed(5)

    observation = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=_volume_delta(feed),
    )

    row = observation.iloc[0]
    assert row["observation_bars_available"] == 5
    assert row["observation_complete"] == False


def _event_row(side):
    return {
        "event_id": "event_000002",
        "event_timestamp": "2026-05-08T00:01:00Z",
        "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
        "zone_id": "zone_000001",
        "side": side,
        "price_before": 95,
        "event_high": 125 if side == "BUY_SIDE" else 120,
        "event_low": 90 if side == "BUY_SIDE" else 85,
        "event_close": 120 if side == "BUY_SIDE" else 90,
        "excursion_abs": 15,
        "excursion_atr": 0,
        "volume_zscore": 2,
        "delta_zscore": 2,
        "oi_change": 1,
        "reaction_status": "UNRESOLVED",
        "evidence_json": (
            '{"data_quality":"RAW","event_class":"LIQUIDITY_SWEEP_UNRESOLVED",'
            '"price_lower":100,"price_mid":105,"price_upper":110,'
            f'"side":"{side}","zone_id":"zone_000001","zone_type":"H1_LEVEL_HIGH_ZONE"}}'
        ),
        "data_quality": "RAW",
    }


def _buy_feed(future_bars):
    rows = [_feed_row("2026-05-08T00:01:00Z", 125, 90, 120, 1000, 1, 10, 6, 4)]
    templates = [
        (130, 120, 125, 1001, 1, 10, 6, 4),
        (112, 105, 108, 999, 2, 20, 8, 12),
        (109, 95, 99, 1005, 3, 30, 10, 20),
    ]
    for idx in range(future_bars):
        minute = idx + 2
        if idx < len(templates):
            high, low, close, oi, trades, qty, buy, sell = templates[idx]
        else:
            high, low, close, oi, trades, qty, buy, sell = (108, 102, 106, 1005 + idx, 1, 5, 3, 2)
        rows.append(
            _feed_row(
                f"2026-05-08T00:{minute:02d}:00Z",
                high,
                low,
                close,
                oi,
                trades,
                qty,
                buy,
                sell,
            )
        )
    return pd.DataFrame(rows)


def _feed_row(ts, high, low, close, oi, trades, qty, buy, sell):
    return {
        "Timestamp": pd.Timestamp(ts),
        "OpenPrice": close,
        "HiPrice": high,
        "LowPrice": low,
        "ClosePrice": close,
        "TotalQty": qty,
        "Trades": trades,
        "BuyQty": buy,
        "SellQty": sell,
        "OpenInterest": oi,
        "FundingRate": 0.0001,
        "DataQuality": "RAW",
        "SourceFile": "synthetic.csv",
    }


def _volume_delta(feed):
    return pd.DataFrame(
        {
            "timestamp": feed["Timestamp"].map(lambda value: value.isoformat().replace("+00:00", "Z")),
            "volume_zscore": [float(idx) for idx in range(len(feed))],
            "delta_zscore": [float(idx) * -1 for idx in range(len(feed))],
            "oi_change": [0.0] * len(feed),
        }
    )
