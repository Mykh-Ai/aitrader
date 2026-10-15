from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from policy import TailAwareReplayData, classify_tail, open_marks, signals
from research.strategy_search.replay import trade_path, ExitRules


def specimen():
    stamps = pd.date_range("2026-10-14T23:00Z", periods=60, freq="min")
    feed = pd.DataFrame({"Timestamp": stamps, "OpenPrice": 100., "HiPrice": 100.1, "LowPrice": 99.9,
                         "ClosePrice": 100., "DataQuality": "RAW"})
    bars = pd.DataFrame({"timestamp": stamps[:1], "available_at": stamps[:1], "open": 100., "high": 100.1,
                         "low": 99.9, "close": 100., "atr": .2, "usable": True, "lower6": 99., "upper6": 101.})
    return feed, bars


def test_last_closed_h1_can_enter_and_remains_open_without_future_expiry():
    feed, bars = specimen()
    trade = trade_path(TailAwareReplayData(feed, bars), 0, 1, ExitRules(6, 2, 10, 0, 168), precise=True)
    assert trade["entry_at"] == pd.Timestamp("2026-10-14T23:01Z")
    assert trade["exit_reason"] == "OPEN" and trade["net_usd"] is None
    ledger = classify_tail(pd.DataFrame([trade]), feed.Timestamp.iloc[-1])
    assert ledger.status_at_cutoff.iloc[0] == "OPEN_AT_CUTOFF"
    assert ledger.expiry_at.iloc[0] == pd.Timestamp("2026-10-21T23:01Z")


def test_no_entry_without_real_observation_and_one_omission_delays_entry():
    feed, bars = specimen()
    assert TailAwareReplayData(feed.iloc[:2], bars).entry(0) is None
    data = TailAwareReplayData(feed.drop(2), bars)
    assert pd.Timestamp(data.entry(0)[1], tz="UTC") == pd.Timestamp("2026-10-14T23:02Z")
    feed.loc[2, "DataQuality"] = "RECOVERED_DEGRADED"
    assert TailAwareReplayData(feed, bars).entry(0) is None


def test_cutoff_mark_ignores_future_quote_and_never_credits_realized_net():
    feed, bars = specimen()
    trade = trade_path(TailAwareReplayData(feed, bars), 0, 1, ExitRules(6, 2, 10, 0, 168), precise=True)
    cutoff = feed.Timestamp.iloc[-1]
    future = feed.iloc[-1:].copy()
    future.Timestamp += pd.Timedelta(minutes=1)
    future.ClosePrice = 99999.
    marks = open_marks(pd.DataFrame([trade]), pd.concat([feed, future]), cutoff)
    assert marks.mark_price_usdc.iloc[0] == 100
    np.testing.assert_allclose(marks.hypothetical_net_if_closed_at_mark_usdc.iloc[0], -6.2)
    assert not marks.included_in_realized_net.iloc[0]


def test_data_gap_censor_is_not_a_normal_open_tail():
    feed, bars = specimen()
    feed = feed.drop([4, 5])
    trade = trade_path(TailAwareReplayData(feed, bars), 0, 1, ExitRules(6, 2, 10, 0, 168), precise=True)
    ledger = classify_tail(pd.DataFrame([trade]), feed.Timestamp.iloc[-1])
    assert ledger.status_at_cutoff.iloc[0] == "CENSORED_DATA"


def test_october_admission_keeps_other_calendar_exclusions():
    stamps = pd.date_range("2026-03-01", "2026-10-15", freq="h", tz="UTC")
    bars = pd.DataFrame({"timestamp": stamps, "close": 101., "open": 100., "low": 99., "high": 102.,
                         "ema24": 100., "ema72": 99., "ema168": 98., "delta": .05,
                         "context_usable": True, "usable": True, "volume_ratio": 2., "upper96": 103., "lower96": 97.})
    result = signals(bars, "TREND_RETEST", 96, .04, 1.3, "EMA")
    assert (result[bars.timestamp.between(pd.Timestamp("2026-10-01", tz="UTC"), pd.Timestamp("2026-10-14T23:00Z"))] == 1).all()
    for start, end in [("2026-04-24", "2026-05-09"), ("2026-06-22", "2026-06-28"), ("2026-08-25", "2026-08-31")]:
        assert (result[bars.timestamp.between(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"))] == 0).all()
