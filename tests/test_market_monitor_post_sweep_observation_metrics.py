import json

import pandas as pd

from market_monitor.post_sweep_observation import build_post_sweep_observations


def test_buy_side_observation_metrics_are_calculated_deterministically():
    event_log = pd.DataFrame([_event_row("BUY_SIDE")])
    feed = _buy_feed()
    volume_delta = _volume_delta(feed)

    first = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=volume_delta,
    )
    second = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=volume_delta,
    )

    assert first.equals(second)
    row = first.iloc[0]
    assert row["max_high_after_event"] == 130
    assert row["min_low_after_event"] == 95
    assert row["close_at_window_end"] == 106
    assert row["max_excursion_beyond_zone"] == 20
    assert row["max_return_inside_zone"] == 15
    assert row["bars_inside_zone"] == 29
    assert row["bars_above_zone"] == 1
    assert row["bars_below_zone"] == 1
    assert row["first_return_inside_at"] == "2026-05-08T00:03:00Z"
    assert row["first_close_inside_at"] == "2026-05-08T00:03:00Z"
    assert row["first_close_beyond_at"] == "2026-05-08T00:02:00Z"
    assert row["post_volume_sum"] == 195
    assert row["post_buy_qty_sum"] == 105
    assert row["post_sell_qty_sum"] == 90
    assert row["post_delta_sum"] == 15
    assert row["post_delta_pct"] == 15 / 195
    assert row["post_trades_sum"] == 33
    assert row["post_oi_change"] == 31
    assert row["post_max_volume_zscore"] == 30
    assert row["post_max_abs_delta_zscore"] == 30

    evidence = json.loads(row["evidence_json"])
    assert list(evidence.keys()) == sorted(evidence.keys())
    assert evidence["observation_class"] == "POST_SWEEP_OBSERVATION"
    assert evidence["reaction_verdict"] == "NOT_CLASSIFIED"
    assert evidence["observation_complete"] is True


def test_sell_side_max_excursion_and_return_inside_metrics():
    event_log = pd.DataFrame([_event_row("SELL_SIDE")])
    feed = pd.DataFrame(
        [
            _feed_row("2026-05-08T00:01:00Z", 120, 85, 90, 1000, 1, 10, 4, 6),
            _feed_row("2026-05-08T00:02:00Z", 95, 80, 85, 1001, 1, 10, 4, 6),
            _feed_row("2026-05-08T00:03:00Z", 108, 98, 104, 1002, 1, 10, 5, 5),
        ]
    )

    observation = build_post_sweep_observations(
        event_log=event_log,
        feed=feed,
        volume_delta_state=_volume_delta(feed),
    )

    row = observation.iloc[0]
    assert row["side"] == "SELL_SIDE"
    assert row["max_excursion_beyond_zone"] == 20
    assert row["max_return_inside_zone"] == 8
    assert row["first_return_inside_at"] == "2026-05-08T00:03:00Z"
    assert row["first_close_inside_at"] == "2026-05-08T00:03:00Z"
    assert row["first_close_beyond_at"] == "2026-05-08T00:02:00Z"


def _event_row(side):
    return {
        "event_id": "event_000003",
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


def _buy_feed():
    rows = [_feed_row("2026-05-08T00:01:00Z", 125, 90, 120, 1000, 1, 10, 6, 4)]
    templates = [
        (130, 120, 125, 1001, 1, 10, 6, 4),
        (112, 105, 108, 999, 2, 20, 8, 12),
        (109, 95, 99, 1005, 3, 30, 10, 20),
    ]
    for idx in range(30):
        minute = idx + 2
        if idx < len(templates):
            high, low, close, oi, trades, qty, buy, sell = templates[idx]
        else:
            high, low, close, oi, trades, qty, buy, sell = (108, 102, 106, 1000 + minute, 1, 5, 3, 2)
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
