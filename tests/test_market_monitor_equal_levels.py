import pandas as pd

from market_monitor.structure import _equal_level_rows


def test_equal_highs_require_multiple_source_levels_and_preserve_ids():
    levels = pd.DataFrame(
        [
            _level("level_000001", "BUY_SIDE", "H1", "H1_SWING_HIGH", 100.0, "2026-05-07T01:00:00Z"),
            _level("level_000002", "BUY_SIDE", "H4", "H4_SWING_HIGH", 100.03, "2026-05-07T04:00:00Z"),
            _level("level_000003", "BUY_SIDE", "H1", "H1_SWING_HIGH", 110.0, "2026-05-07T05:00:00Z"),
        ]
    )

    equal = _equal_level_rows(levels)

    assert len(equal) == 1
    row = equal.iloc[0]
    assert row["level_type"] == "EQUAL_HIGHS"
    assert row["source_level_ids"] == "level_000001|level_000002"
    assert row["created_at"] == "2026-05-07T04:00:00Z"


def test_equal_lows_are_not_created_from_one_level():
    levels = pd.DataFrame(
        [_level("level_000001", "SELL_SIDE", "H1", "H1_SWING_LOW", 100.0, "2026-05-07T01:00:00Z")]
    )

    equal = _equal_level_rows(levels)

    assert equal.empty


def _level(level_id, side, timeframe, level_type, price, created_at):
    return {
        "level_id": level_id,
        "created_at": created_at,
        "level_timestamp": created_at,
        "timeframe": timeframe,
        "level_type": level_type,
        "side": side,
        "price": price,
        "source_start": created_at,
        "source_end": created_at,
        "touch_count": 1,
        "strength_score": 65,
        "status": "ACTIVE",
        "data_quality": "RAW",
        "source_level_ids": "",
    }
