import pandas as pd

from market_monitor.liquidity_zones import build_liquidity_map


def test_h4_and_pdh_score_higher_than_single_session_zone():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "SESSION", "ASIA_HIGH", 100.0),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 200.0),
            _level("level_000003", "BUY_SIDE", "D1", "PDH", 300.0),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=50.0)
    scores = dict(zip(zones["source_level_ids"], zones["confidence_score"]))

    assert scores["level_000002"] > scores["level_000001"]
    assert scores["level_000003"] > scores["level_000001"]
    assert zones["confidence_score"].between(0, 100).all()


def test_degraded_data_gets_confidence_penalty():
    raw = build_liquidity_map(
        pd.DataFrame([_level("level_000001", "BUY_SIDE", "H4", "H4_SWING_HIGH", 100.0, "RAW")]),
        latest_close=50.0,
    )
    degraded = build_liquidity_map(
        pd.DataFrame(
            [
                _level(
                    "level_000001",
                    "BUY_SIDE",
                    "H4",
                    "H4_SWING_HIGH",
                    100.0,
                    "RECOVERED_DEGRADED",
                )
            ]
        ),
        latest_close=50.0,
    )

    assert degraded.loc[0, "confidence_score"] < raw.loc[0, "confidence_score"]


def test_low_confidence_degraded_session_noise_is_pruned_but_h4_survives():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "SESSION", "ASIA_HIGH", 100.0, "RECOVERED_DEGRADED"),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 200.0, "RECOVERED_DEGRADED"),
        ]
    )

    zones = build_liquidity_map(levels, latest_close=50.0)

    assert zones["source_level_ids"].tolist() == ["level_000002"]


def _level(level_id, side, timeframe, level_type, price, quality="RAW"):
    return {
        "level_id": level_id,
        "created_at": "2026-05-07T00:00:00Z",
        "level_timestamp": "2026-05-07T00:00:00Z",
        "timeframe": timeframe,
        "level_type": level_type,
        "side": side,
        "price": price,
        "source_start": "2026-05-07T00:00:00Z",
        "source_end": "2026-05-07T00:00:00Z",
        "touch_count": 1,
        "strength_score": 65,
        "status": "ACTIVE",
        "data_quality": quality,
        "source_level_ids": "",
    }
