"""Exact state/clock parity for the canonical replay's bounded fast paths."""
import numpy as np
import pandas as pd
import pytest

from market_monitor import zone_registry as registry
from test_market_monitor_main_integrity import minutes, zone


def test_acceptance_vectorization_preserves_elapsed_gap_semantics():
    rng = np.random.default_rng(9017)
    for length in [0, 1, 2, 3, 9, 100, 1000]:
        for _ in range(20):
            flags = rng.random(length) > .4
            offsets = np.cumsum(rng.choice([1, 1, 1, 2, 3, 120], size=length))
            times = pd.Timestamp("2026-05-07T00:00Z") + pd.to_timedelta(offsets, unit="min")
            frame = pd.DataFrame({"Timestamp": times})
            expected, count, previous = "", 0, None
            for flag, timestamp in zip(flags, times):
                if previous is not None and timestamp - previous > pd.Timedelta(minutes=2):
                    count = 0
                count = count + 1 if flag else 0
                previous = timestamp
                if count >= registry.ACCEPTANCE_CLOSE_BARS:
                    expected = registry._format_ts(timestamp)
                    break
            assert registry._consecutive_threshold_at(frame, flags.tolist()) == expected


@pytest.mark.parametrize("side,price", [("BUY_SIDE", 110.), ("SELL_SIDE", 90.)])
@pytest.mark.parametrize("extended_gap", [False, True])
def test_accepted_htf_run_updates_from_carried_state_without_lifetime_rescan(monkeypatch, side, price, extended_gap):
    frame = minutes(count=120)
    frame[["OpenPrice", "ClosePrice"]] = price
    frame["HiPrice"], frame["LowPrice"] = price + 1, price - 1
    source = zone()
    source["side"] = side
    initial, _ = registry.build_zone_registry(liquidity_map=pd.DataFrame([source]), feed=frame.iloc[:60])
    if extended_gap:
        frame = frame.drop(index=[70, 71, 72]).reset_index(drop=True)
    expected = registry._update_lifecycle(initial, frame, use_cache=False)
    calls = []
    original = registry._consumption_fields
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(registry, "_consumption_fields", counted)
    actual = registry._update_lifecycle(initial, frame, use_cache=True)
    pd.testing.assert_frame_equal(actual, expected, check_exact=True)
    assert calls == ([1] if extended_gap else []), "only uninterrupted accepted HTF runs may skip the lifetime scan"
