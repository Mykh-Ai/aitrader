import pandas as pd

from research.scripts.h4_active_level_reclaim_close_test import (
    ConfirmedLevel,
    add_forward_diagnostics,
    add_compressed_buffer_gates,
    add_local_h4_sweep_extreme_stop_gates,
    add_trade_gates,
    build_long_low_selection_audit,
    build_long_active_low_audit,
    build_h4_bars,
    _drop_expired_pending,
    _drop_swept_pending,
    _promote_latest_pending,
    scan_local_h4_reclaim_candidates,
    scan_candidates,
)


def _h4_bars(highs: list[float], lows: list[float], closes: list[float]) -> pd.DataFrame:
    opens = pd.date_range("2026-01-01T00:00:00Z", periods=len(highs), freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "h4_open_ts": opens,
            "h4_close_ts": opens + pd.Timedelta(hours=4),
            "Open": closes,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "RowCount": 240,
        }
    )


def test_short_active_high_is_not_replaced_by_lower_high_before_sweep():
    h4 = _h4_bars(
        highs=[90, 100, 80, 70, 95, 70, 70, 101, 99, 98],
        lows=[50] * 10,
        closes=[70, 70, 70, 70, 70, 70, 70, 99, 103, 99],
    )

    candidates = scan_candidates(h4)

    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "SHORT"
    assert row["active_level_price"] == 100
    assert row["reclaim_bar_number_after_sweep"] == 2


def test_long_reclaim_window_excludes_sweep_candle():
    h4 = _h4_bars(
        highs=[150] * 10,
        lows=[110, 100, 120, 130, 105, 130, 130, 99, 101, 102],
        closes=[130, 130, 130, 130, 130, 130, 130, 101, 99, 101],
    )

    candidates = scan_candidates(h4)

    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "LONG"
    assert row["active_level_price"] == 100
    assert row["reclaim_bar_number_after_sweep"] == 2


def test_active_low_occupied_new_higher_low_is_promoted_from_pending_after_expiry():
    highs = [200.0] * 38
    lows = [130.0] * 38
    closes = [130.0] * 38
    lows[0:8] = [110.0, 100.0, 120.0, 130.0, 130.0, 110.0, 130.0, 130.0]
    lows[35] = 109.0
    closes[35] = 109.0
    closes[36] = 111.0
    h4 = _h4_bars(highs=highs, lows=lows, closes=closes)

    candidates = scan_candidates(h4)

    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "LONG"
    assert row["active_level_price"] == 110.0
    assert row["active_level_source"] == "promoted_from_pending"
    assert bool(row["promoted_from_pending"]) is True
    assert row["pending_queue_size_at_activation"] == 1
    assert row["previous_expired_level_price"] == 100.0


def test_swept_pending_low_before_promotion_is_not_promoted():
    pending = [
        ConfirmedLevel(
            side="LOW",
            price=110.0,
            confirmed_ts=pd.Timestamp("2026-01-01T00:00:00Z"),
            confirmed_idx=7,
        )
    ]
    bar = pd.Series({"High": 200.0, "Low": 109.0})

    kept, dropped = _drop_swept_pending(pending, bar=bar)
    active, remaining = _promote_latest_pending(
        kept,
        previous_expired_level=None,
        stats={"ignored": 1, "dropped_swept": dropped, "dropped_expired": 0},
    )

    assert dropped == 1
    assert remaining == []
    assert active is None


def test_expired_pending_low_before_promotion_is_not_promoted():
    pending = [
        ConfirmedLevel(
            side="LOW",
            price=110.0,
            confirmed_ts=pd.Timestamp("2026-01-01T00:00:00Z"),
            confirmed_idx=7,
        )
    ]

    kept, dropped = _drop_expired_pending(pending, idx=38)
    active, remaining = _promote_latest_pending(
        kept,
        previous_expired_level=None,
        stats={"ignored": 1, "dropped_swept": 0, "dropped_expired": dropped},
    )

    assert dropped == 1
    assert remaining == []
    assert active is None


def test_active_high_occupied_new_lower_high_is_promoted_from_pending_after_expiry():
    highs = [80.0] * 38
    lows = [0.0] * 38
    closes = [80.0] * 38
    highs[0:8] = [80.0, 100.0, 70.0, 80.0, 80.0, 90.0, 80.0, 80.0]
    highs[35] = 91.0
    closes[35] = 91.0
    closes[36] = 89.0
    h4 = _h4_bars(highs=highs, lows=lows, closes=closes)

    candidates = scan_candidates(h4)

    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "SHORT"
    assert row["active_level_price"] == 90.0
    assert row["active_level_source"] == "promoted_from_pending"
    assert bool(row["promoted_from_pending"]) is True
    assert row["pending_queue_size_at_activation"] == 1
    assert row["previous_expired_level_price"] == 100.0


def test_row5_regression_promotes_prior_valid_low_instead_of_later_local_low():
    highs = [80000.0] * 42
    lows = [72000.0] * 42
    closes = [72000.0] * 42
    lows[0:8] = [71000.0, 70000.0, 71500.0, 72000.0, 72000.0, 70500.0, 72000.0, 72000.0]
    lows[35] = 70400.0
    closes[35] = 70400.0
    closes[36] = 70550.0
    lows[38:41] = [72000.0, 70671.6, 72000.0]
    h4 = _h4_bars(highs=highs, lows=lows, closes=closes)

    candidates = scan_candidates(h4)

    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "LONG"
    assert row["active_level_price"] == 70500.0
    assert row["active_level_price"] != 70671.6
    assert row["active_level_source"] == "promoted_from_pending"


def _candidate(
    *,
    direction: str,
    sweep_extreme_price: float,
    entry_price: float,
    reclaim_open: float,
    reclaim_close: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "C1",
                "direction": direction,
                "active_level_price": 100.0,
                "active_level_confirmed_ts": pd.Timestamp("2026-01-01T00:00:00Z"),
                "active_level_age_h4_bars": 1,
                "sweep_h4_open_ts": pd.Timestamp("2026-01-01T04:00:00Z"),
                "sweep_h4_close_ts": pd.Timestamp("2026-01-01T08:00:00Z"),
                "sweep_extreme_price": sweep_extreme_price,
                "reclaim_h4_open_ts": pd.Timestamp("2026-01-01T08:00:00Z"),
                "reclaim_h4_close_ts": pd.Timestamp("2026-01-01T12:00:00Z"),
                "reclaim_h4_open_price": reclaim_open,
                "reclaim_close_price": reclaim_close,
                "reclaim_bar_number_after_sweep": 1,
                "entry_ts": pd.Timestamp("2026-01-01T12:00:00Z"),
                "entry_price": entry_price,
                "_active_level_confirmed_idx": 0,
                "_sweep_h4_idx": 1,
                "_reclaim_h4_idx": 2,
                "notes": "diagnostic_only",
            }
        ]
    )


def test_short_green_reclaim_candle_fails_diagnostic_trade_allowed():
    gated = add_trade_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=101.0,
            entry_price=100.0,
            reclaim_open=99.0,
            reclaim_close=100.0,
        )
    )

    assert bool(gated.loc[0, "risk_gate_pass"]) is True
    assert bool(gated.loc[0, "candle_color_gate_pass"]) is False
    assert bool(gated.loc[0, "diagnostic_trade_allowed"]) is False
    assert gated.loc[0, "no_trade_reason"] == "bearish_reclaim_required"


def test_long_red_reclaim_candle_fails_diagnostic_trade_allowed():
    gated = add_trade_gates(
        _candidate(
            direction="LONG",
            sweep_extreme_price=99.0,
            entry_price=100.0,
            reclaim_open=101.0,
            reclaim_close=100.0,
        )
    )

    assert bool(gated.loc[0, "risk_gate_pass"]) is True
    assert bool(gated.loc[0, "candle_color_gate_pass"]) is False
    assert bool(gated.loc[0, "diagnostic_trade_allowed"]) is False
    assert gated.loc[0, "no_trade_reason"] == "bullish_reclaim_required"


def test_risk_too_large_sets_no_trade_reason():
    gated = add_trade_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=2000.0,
            entry_price=100.0,
            reclaim_open=101.0,
            reclaim_close=100.0,
        )
    )

    assert gated.loc[0, "risk_usd"] > 1500
    assert bool(gated.loc[0, "risk_gate_pass"]) is False
    assert gated.loc[0, "no_trade_reason"] == "risk_too_large"


def test_short_and_long_stop_prices_use_sweep_extreme_buffer():
    short = add_trade_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=101.0,
            entry_price=100.0,
            reclaim_open=101.0,
            reclaim_close=100.0,
        )
    )
    long = add_trade_gates(
        _candidate(
            direction="LONG",
            sweep_extreme_price=99.0,
            entry_price=100.0,
            reclaim_open=99.0,
            reclaim_close=100.0,
        )
    )

    assert short.loc[0, "stop_price"] == 451.0
    assert long.loc[0, "stop_price"] == -251.0


def test_buffer50_alias_columns_and_long_without_color_gate_mode():
    gated = add_trade_gates(
        _candidate(
            direction="LONG",
            sweep_extreme_price=99.0,
            entry_price=100.0,
            reclaim_open=101.0,
            reclaim_close=100.0,
        ),
        stop_buffer_usd=50.0,
    )

    assert gated.loc[0, "stop_buffer_usd"] == 50.0
    assert gated.loc[0, "stop_price_buffer_50"] == 49.0
    assert gated.loc[0, "risk_usd_buffer_50"] == 51.0
    assert bool(gated.loc[0, "diagnostic_trade_allowed_buffer_50"]) is False
    assert gated.loc[0, "no_trade_reason_buffer_50"] == "bullish_reclaim_required"
    assert bool(gated.loc[0, "diagnostic_trade_allowed_buffer_50_long_with_color_gate"]) is False
    assert bool(gated.loc[0, "diagnostic_trade_allowed_buffer_50_long_without_color_gate"]) is True
    assert gated.loc[0, "no_trade_reason_buffer_50_long_without_color_gate"] == ""


def test_same_bar_stop_target_is_not_clean_target_before_stop():
    raw = pd.DataFrame(
        [
            {
                "Timestamp": pd.Timestamp("2026-01-01T12:00:00Z"),
                "Open": 100.0,
                "High": 451.0,
                "Low": -251.0,
                "Close": 100.0,
            }
        ]
    )
    gated = add_trade_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=101.0,
            entry_price=100.0,
            reclaim_open=101.0,
            reclaim_close=100.0,
        )
    )
    out = add_forward_diagnostics(gated, raw)

    assert bool(out.loc[0, "same_bar_stop_1R"]) is True
    assert bool(out.loc[0, "hit_1R_before_stop"]) is False
    assert bool(out.loc[0, "stop_before_1R"]) is False


def test_long_active_low_audit_outputs_h4_low_broke_active_low():
    raw = pd.DataFrame(
        {
            "Timestamp": pd.date_range("2026-01-01T00:00:00Z", periods=10, freq="4h", tz="UTC"),
            "Open": [1.0] * 10,
            "High": [150] * 10,
            "Low": [110, 100, 120, 130, 105, 130, 130, 99, 101, 102],
            "Close": [130, 130, 130, 130, 130, 130, 130, 101, 99, 101],
        }
    )
    h4 = build_h4_bars(raw)
    candidates = scan_candidates(h4)

    audit = build_long_active_low_audit(candidates, h4)

    assert "h4_low_broke_active_low" in audit.columns
    assert bool(audit.loc[0, "h4_low_broke_active_low"]) is True


def test_long_low_selection_audit_flags_internal_sweep_without_main_sweep():
    h4 = _h4_bars(
        highs=[150] * 11,
        lows=[110, 100, 120, 130, 105, 130, 130, 101, 102, 103, 104],
        closes=[130] * 11,
    )
    candidates = pd.DataFrame(
        [
            {
                "row_number": 5,
                "candidate_id": "C_LONG",
                "entry_ts": pd.Timestamp("2026-01-02T12:00:00Z"),
                "direction": "LONG",
                "active_level_price": 100.0,
                "active_level_confirmed_ts": pd.Timestamp("2026-01-01T12:00:00Z"),
                "active_level_age_h4_bars": 4,
                "sweep_h4_open_ts": pd.Timestamp("2026-01-02T04:00:00Z"),
                "sweep_extreme_price": 104.0,
                "reclaim_h4_close_ts": pd.Timestamp("2026-01-02T12:00:00Z"),
                "reclaim_close_price": 130.0,
                "_active_level_confirmed_idx": 3,
                "_sweep_h4_idx": 7,
            }
        ]
    )

    audit = build_long_low_selection_audit(candidates, h4, row_numbers=(5,))

    assert bool(audit.loc[0, "swept_main_active_low"]) is False
    assert bool(audit.loc[0, "swept_internal_higher_low"]) is True
    assert bool(audit.loc[0, "contract_violation"]) is True
    assert audit.loc[0, "suspected_issue"] == "higher_low_replaced_unswept_active_low"
    assert audit.loc[0, "possible_separate_pattern"] == "INTERNAL_HIGHER_LOW_SWEEP_RECLAIM"


def test_short_compressed_buffer_caps_risk_instead_of_rejecting():
    compressed = add_compressed_buffer_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=1400.0,
            entry_price=0.0,
            reclaim_open=1.0,
            reclaim_close=0.0,
        )
    )

    assert compressed.loc[0, "desired_risk_usd"] == 1750.0
    assert compressed.loc[0, "final_stop_price"] == 1500.0
    assert compressed.loc[0, "final_risk_usd"] == 1500.0
    assert compressed.loc[0, "applied_buffer_usd"] == 100.0
    assert bool(compressed.loc[0, "buffer_was_compressed"]) is True
    assert bool(compressed.loc[0, "diagnostic_trade_allowed"]) is True


def test_long_compressed_buffer_caps_risk_instead_of_rejecting():
    compressed = add_compressed_buffer_gates(
        _candidate(
            direction="LONG",
            sweep_extreme_price=-1400.0,
            entry_price=0.0,
            reclaim_open=-1.0,
            reclaim_close=0.0,
        )
    )

    assert compressed.loc[0, "desired_risk_usd"] == 1750.0
    assert compressed.loc[0, "final_stop_price"] == -1500.0
    assert compressed.loc[0, "final_risk_usd"] == 1500.0
    assert compressed.loc[0, "applied_buffer_usd"] == 100.0
    assert bool(compressed.loc[0, "buffer_was_compressed"]) is True
    assert bool(compressed.loc[0, "diagnostic_trade_allowed"]) is True


def test_compressed_buffer_rejects_when_raw_sweep_risk_exceeds_max_risk():
    compressed = add_compressed_buffer_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=1600.0,
            entry_price=0.0,
            reclaim_open=1.0,
            reclaim_close=0.0,
        )
    )

    assert bool(compressed.loc[0, "diagnostic_trade_allowed"]) is False
    assert compressed.loc[0, "no_trade_reason"] == "sweep_extreme_risk_too_large"


def test_compressed_allowed_rows_never_exceed_max_risk():
    compressed = add_compressed_buffer_gates(
        pd.concat(
            [
                _candidate(
                    direction="SHORT",
                    sweep_extreme_price=1400.0,
                    entry_price=0.0,
                    reclaim_open=1.0,
                    reclaim_close=0.0,
                ),
                _candidate(
                    direction="LONG",
                    sweep_extreme_price=-1000.0,
                    entry_price=0.0,
                    reclaim_open=-1.0,
                    reclaim_close=0.0,
                ),
            ],
            ignore_index=True,
        )
    )

    allowed = compressed.loc[compressed["diagnostic_trade_allowed"] == True]
    assert (allowed["final_risk_usd"] <= 1500.0).all()


def test_compressed_path_order_uses_final_stop_and_risk_not_desired_values():
    raw = pd.DataFrame(
        [
            {
                "Timestamp": pd.Timestamp("2026-01-01T12:00:00Z"),
                "Open": 0.0,
                "High": 1500.0,
                "Low": -1500.0,
                "Close": 0.0,
            }
        ]
    )
    compressed = add_compressed_buffer_gates(
        _candidate(
            direction="SHORT",
            sweep_extreme_price=1400.0,
            entry_price=0.0,
            reclaim_open=1.0,
            reclaim_close=0.0,
        )
    )
    out = add_forward_diagnostics(compressed, raw)

    assert out.loc[0, "final_risk_usd"] == 1500.0
    assert out.loc[0, "desired_risk_usd"] == 1750.0
    assert pd.Timestamp(out.loc[0, "first_stop_touch_ts"]) == pd.Timestamp("2026-01-01T12:00:00Z")
    assert pd.Timestamp(out.loc[0, "first_1R_touch_ts"]) == pd.Timestamp("2026-01-01T12:00:00Z")
    assert bool(out.loc[0, "same_bar_stop_1R"]) is True


def test_local_h4_scanner_allows_lower_high_sweep_family():
    h4 = _h4_bars(
        highs=[80, 100, 70, 80, 80, 90, 80, 80, 91, 89],
        lows=[50] * 10,
        closes=[80, 80, 80, 80, 80, 80, 80, 80, 92, 89],
    )

    candidates = scan_local_h4_reclaim_candidates(h4)

    assert len(candidates.index) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "SHORT"
    assert row["level_price"] == 90
    assert row["level_family"] == "LOCAL_LOWER_HIGH_SWEEP"
    assert row["reclaim_bar_number_after_sweep"] == 1


def test_local_h4_buffer50_rejects_large_risk_without_compression():
    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "L1",
                "direction": "SHORT",
                "sweep_extreme_price": 1600.0,
                "entry_price": 100.0,
            }
        ]
    )

    gated = add_local_h4_sweep_extreme_stop_gates(candidates)

    assert gated.loc[0, "stop_price"] == 1650.0
    assert gated.loc[0, "final_risk_usd"] == 1550.0
    assert bool(gated.loc[0, "diagnostic_trade_allowed"]) is False
    assert gated.loc[0, "no_trade_reason"] == "sweep_extreme_risk_too_large"
