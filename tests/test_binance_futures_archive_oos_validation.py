"""40O research source/causality/phase contracts, never a strategy search."""
from pathlib import Path
import hashlib
import importlib.util
import json

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0"


def module(name):
    spec = importlib.util.spec_from_file_location("test40O_" + name, RUN / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


source = module("archive_source")
policy = module("phase_policy")


def kline():
    stamp = pd.Timestamp("2026-07-01T12:00:00Z").value // 1_000_000
    return pd.DataFrame([[stamp, "100.10", "101.20", "99.30", "100.50", "3.123456", stamp + 59_999,
                          "312.3", 7, "1.123456", "112.3", 0]])


def test_exchange_open_maps_to_shi_right_close_and_preserves_both_clocks():
    normalized = source.normalize_klines(kline())
    assert normalized.Timestamp.iloc[0] == pd.Timestamp("2026-07-01T12:01Z")
    assert normalized.ExchangeOpenAt.iloc[0] == pd.Timestamp("2026-07-01T12:00Z")
    assert normalized.ExchangeCloseAt.iloc[0] < normalized.Timestamp.iloc[0]


def test_taker_buy_base_quantity_mapping():
    normalized = source.normalize_klines(kline())
    assert normalized.BuyQty.iloc[0] == 1.123456


def test_sell_is_total_minus_taker_buy_and_unavailable_context_is_not_a_blocker():
    normalized = source.normalize_klines(kline())
    assert normalized.SellQty.iloc[0] == 2
    assert abs(normalized.TotalQty.iloc[0] - normalized.BuyQty.iloc[0] - normalized.SellQty.iloc[0]) < 1e-10
    assert normalized.DataQuality.iloc[0] == "RAW"
    assert not normalized.OIFundingLiquidationsAvailable.iloc[0]


def test_zero_trade_row_is_an_omission_not_an_execution_candle():
    frame = kline()
    frame.iloc[0, [5, 8, 9]] = ["0", 0, "0"]
    normalized = source.normalize_klines(frame)
    assert not normalized.Traded.iloc[0] and normalized.IsSynthetic.iloc[0] == 1


def test_warmup_never_counts_a_pre_start_trade():
    stamps = pd.Series(pd.date_range("2025-02-01", "2025-03-02", freq="h", tz="UTC"))
    allowed = policy.scored_entries(stamps)
    assert not allowed.loc[stamps < policy.OOS_START].any()
    assert allowed.loc[stamps >= policy.OOS_START].all()


def test_scored_start_end_are_inclusive_and_no_post_end_trade():
    stamps = [policy.OOS_START - pd.Timedelta(minutes=1), policy.OOS_START, policy.OOS_END, policy.OOS_END + pd.Timedelta(minutes=1)]
    assert policy.scored_entries(stamps).tolist() == [False, True, True, False]


def test_rolling_window_is_open_left_closed_right_without_future_rows():
    decision = pd.Timestamp("2026-07-01T12:00Z")
    frame = pd.DataFrame({"Timestamp": [decision - pd.Timedelta(hours=4), decision - pd.Timedelta(minutes=1), decision, decision + pd.Timedelta(minutes=1)]})
    chosen = policy.rolling_window(frame, decision, 4)
    assert chosen.Timestamp.tolist() == frame.Timestamp.iloc[1:3].tolist()


def test_future_append_does_not_change_prior_feature_prefix():
    from research.strategy_search.features import features
    stamp = pd.date_range("2026-07-01T00:00Z", periods=181, freq="min")
    frame = pd.DataFrame({"Timestamp": stamp, "OpenPrice": 100., "HiPrice": 100.1, "LowPrice": 99.9, "ClosePrice": 100.,
                          "TotalQty": 1., "BuyQty": .5, "SellQty": .5, "OpenInterest": 0., "LiqBuyQty": 0., "LiqSellQty": 0., "DataQuality": "RAW"})
    before = features(frame)
    future = frame.iloc[-60:].copy()
    future.Timestamp += pd.Timedelta(hours=1)
    future.HiPrice = 9999.
    after = features(pd.concat([frame, future], ignore_index=True))
    pd.testing.assert_frame_equal(before, after.loc[after.available_at.le(stamp[-1])].reset_index(drop=True))


def test_parity_checks_candidate_direction_and_rejection_reason():
    left = pd.DataFrame({"timestamp": [pd.Timestamp("2026-07-01", tz="UTC")], "raw_direction": [-1], "final_direction": [0], "blocker_reasons": ["H4_SPACE_REJECTED"]})
    assert policy.decisions_equal(left, left.copy()).all()
    right = left.copy()
    right.loc[0, "blocker_reasons"] = "DELTA24_OUTSIDE_STRICT_BAND4"
    assert not policy.decisions_equal(left, right).all()
    right.loc[0, "raw_direction"] = 1
    assert not policy.decisions_equal(left, right).all()


def test_actual_selected_rule_identities_are_frozen():
    h = ROOT / "market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
    assert hashlib.sha256((h / "filters.py").read_bytes()).hexdigest() == "ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4"
    assert hashlib.sha256((h / "filter_manifest.json").read_bytes()).hexdigest() == "32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56"


def test_hash_mutation_fails_loudly(tmp_path):
    file = tmp_path / "rules.py"
    file.write_text("frozen", encoding="utf-8")
    expected = hashlib.sha256(file.read_bytes()).hexdigest()
    policy.verify_hashes(tmp_path, {file.name: expected})
    file.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="FROZEN"):
        policy.verify_hashes(tmp_path, {file.name: expected})


def test_no_oos_before_parity_and_no_second_attempt_or_variant_search(tmp_path):
    manifest = {"strategy_count": 1, "variant_search_allowed": False, "optimization_allowed": False}
    with pytest.raises(ValueError, match="PARITY_NOT_ACCEPTED"):
        policy.authorize_first_oos_attempt(tmp_path, manifest)
    (tmp_path / "parity_acceptance.json").write_text(json.dumps({"status": "ACCEPTED_100_PERCENT_DECISION_PARITY"}))
    with pytest.raises(ValueError, match="OPTIMIZATION"):
        policy.authorize_first_oos_attempt(tmp_path, {**manifest, "variant_search_allowed": True})
    policy.authorize_first_oos_attempt(tmp_path, manifest)
    with pytest.raises(FileExistsError):
        policy.authorize_first_oos_attempt(tmp_path, manifest)


def test_predeclared_verdict_is_not_a_search_trigger():
    assert policy.oos_verdict(11, 1000, 10, 500, True, True, True) == "OOS_INSUFFICIENT_SAMPLE"
    assert policy.oos_verdict(12, 100, 1.24, 1, True, True, True) == "OOS_REJECTS_CURRENT_CANDIDATE"
    assert policy.oos_verdict(12, 100, 1.25, 1, True, True, True) == "OOS_SUPPORTS_CONTINUED_VALIDATION"
