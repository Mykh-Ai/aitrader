import datetime
import importlib
import json
from pathlib import Path

import pytest

pytest.importorskip("websocket")
pytest.importorskip("requests")

agg = importlib.import_module("binance_aggregator_shi")


class FakeDateTime(datetime.datetime):
    current = datetime.datetime(2026, 3, 13, 12, 28, 16)

    @classmethod
    def utcnow(cls):
        return cls.current


def _data_lines(csv_path: Path):
    lines = csv_path.read_text().strip().splitlines()
    return lines[1:]


class FakeWebSocket:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FailingWebSocket:
    def close(self):
        raise RuntimeError("close failed")


@pytest.fixture(autouse=True)
def reset_aggregator_state():
    with agg.lock:
        agg.buffer.reset()
        agg.buffer.open_interest = 0.0
        agg.buffer.funding_rate = 0.0
        agg.buffer.mark_price = 0.0
        agg.buffer.last_price = 0.0
        agg.last_flushed_ts = None
        agg.FEED_STATE["consecutive_synthetic_candles"] = 0
    with agg.state_lock:
        agg.WS_STATE.update(
            {
                "connected": False,
                "connected_at": None,
                "retries": 0,
                "last_agg_trade_ts": None,
                "last_mark_price_ts": None,
                "last_ws_message_ts": None,
                "last_real_trade_price": None,
                "real_trade_minute": None,
                "real_trade_count": 0,
                "watchdog_reconnects": 0,
                "watchdog_close_requested": False,
            }
        )
    with agg.active_ws_lock:
        agg.active_ws = None


def test_futures_ws_url_uses_market_routed_endpoint():
    assert agg.WS_BASE == "wss://fstream.binance.com/market/stream?streams="
    assert agg.WS_URL.startswith("wss://fstream.binance.com/market/stream?streams=")
    assert "btcusdt@aggTrade" in agg.WS_URL
    assert "btcusdt@forceOrder" in agg.WS_URL
    assert "btcusdt@markPrice@1s" in agg.WS_URL


def _set_non_empty_buffer(price: float = 100.0, qty: float = 1.0):
    with agg.lock:
        agg.buffer.reset()
        agg.buffer.add_trade(price, qty, is_buyer_maker=False)


def test_flush_candle_in_memory_guard_prevents_duplicate_same_minute(tmp_path, monkeypatch):
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 28, 16)
    monkeypatch.setattr(agg, "FEED_DIR", str(tmp_path))
    monkeypatch.setattr(agg.datetime, "datetime", FakeDateTime)
    with agg.lock:
        agg.last_flushed_ts = None

    _set_non_empty_buffer()
    agg.flush_candle()

    # Same minute flush call should be skipped by in-memory guard.
    _set_non_empty_buffer(price=101.0)
    agg.flush_candle()

    csv_path = tmp_path / "2026-03-13.csv"
    assert csv_path.exists()
    rows = _data_lines(csv_path)
    assert len(rows) == 1
    assert rows[0].startswith("2026-03-13 12:28:00,")


def test_flush_candle_file_guard_prevents_duplicate_after_restart(tmp_path, monkeypatch):
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 28, 16)
    monkeypatch.setattr(agg, "FEED_DIR", str(tmp_path))
    monkeypatch.setattr(agg.datetime, "datetime", FakeDateTime)

    with agg.lock:
        agg.last_flushed_ts = None

    _set_non_empty_buffer()
    agg.flush_candle()

    # Simulate process restart: in-memory marker gone.
    with agg.lock:
        agg.last_flushed_ts = None

    _set_non_empty_buffer(price=102.0)
    agg.flush_candle()

    csv_path = tmp_path / "2026-03-13.csv"
    rows = _data_lines(csv_path)
    assert len(rows) == 1


def test_next_minute_flush_still_writes(tmp_path, monkeypatch):
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 28, 16)
    monkeypatch.setattr(agg, "FEED_DIR", str(tmp_path))
    monkeypatch.setattr(agg.datetime, "datetime", FakeDateTime)

    with agg.lock:
        agg.last_flushed_ts = None

    _set_non_empty_buffer(price=100.0)
    agg.flush_candle()

    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 29, 1)
    _set_non_empty_buffer(price=105.0)
    agg.flush_candle()

    csv_path = tmp_path / "2026-03-13.csv"
    rows = _data_lines(csv_path)
    assert len(rows) == 2
    assert rows[0].startswith("2026-03-13 12:28:00,")
    assert rows[1].startswith("2026-03-13 12:29:00,")


def test_stale_watchdog_closes_active_ws_and_counts_reconnect(monkeypatch):
    fake_ws = FakeWebSocket()
    monkeypatch.setattr(agg, "WS_STALE_AGG_TRADE_SECONDS", 180)
    monkeypatch.setattr(agg, "WS_STALE_MARK_PRICE_SECONDS", 180)
    with agg.active_ws_lock:
        agg.active_ws = fake_ws
    with agg.state_lock:
        agg.WS_STATE.update(
            {
                "connected": True,
                "connected_at": 1000.0,
                "last_agg_trade_ts": 1001.0,
                "last_mark_price_ts": 1002.0,
                "last_ws_message_ts": 1002.0,
                "last_real_trade_price": 77973.5,
            }
        )
    with agg.lock:
        agg.buffer.mark_price = 77973.5

    assert agg.check_ws_freshness(now=1205.0) is True

    assert fake_ws.closed is True
    with agg.state_lock:
        assert agg.WS_STATE["watchdog_reconnects"] == 1
        assert agg.WS_STATE["watchdog_close_requested"] is True


def test_reconnect_request_without_active_ws_does_not_latch_watchdog_flag():
    assert agg.request_ws_reconnect("test no active ws") is False

    with agg.state_lock:
        assert agg.WS_STATE["watchdog_reconnects"] == 0
        assert agg.WS_STATE["watchdog_close_requested"] is False


def test_reconnect_request_close_failure_does_not_latch_watchdog_flag():
    with agg.active_ws_lock:
        agg.active_ws = FailingWebSocket()

    assert agg.request_ws_reconnect("test close failure") is False

    with agg.state_lock:
        assert agg.WS_STATE["watchdog_reconnects"] == 0
        assert agg.WS_STATE["watchdog_close_requested"] is False


def test_ws_open_resets_stream_freshness_for_new_connection(monkeypatch):
    monkeypatch.setattr(agg, "WS_STALE_AGG_TRADE_SECONDS", 180)
    monkeypatch.setattr(agg, "WS_STALE_MARK_PRICE_SECONDS", 180)
    monkeypatch.setattr(agg.time, "time", lambda: 5000.0)
    with agg.state_lock:
        agg.WS_STATE.update(
            {
                "last_agg_trade_ts": 1000.0,
                "last_mark_price_ts": 1000.0,
                "last_real_trade_price": 77973.5,
            }
        )

    agg._on_open(None)
    snapshot = agg._ws_snapshot(now=5010.0)

    assert snapshot["connected"] is True
    assert snapshot["agg_trade_age"] is None
    assert snapshot["mark_price_age"] is None
    assert snapshot["stale"] is False
    with agg.state_lock:
        assert agg.WS_STATE["last_real_trade_price"] == 77973.5


def test_synthetic_flushes_stop_after_configured_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(agg, "FEED_DIR", str(tmp_path))
    monkeypatch.setattr(agg, "MAX_CONSECUTIVE_SYNTHETIC_CANDLES", 2)
    monkeypatch.setattr(agg.datetime, "datetime", FakeDateTime)
    with agg.lock:
        agg.buffer.mark_price = 100.0
        agg.buffer.last_price = 100.0

    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 28, 1)
    agg.flush_candle()
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 29, 1)
    agg.flush_candle()
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 30, 1)
    agg.flush_candle()

    csv_path = tmp_path / "2026-03-13.csv"
    rows = _data_lines(csv_path)
    assert len(rows) == 2
    assert rows[0].endswith(",1")
    assert rows[1].endswith(",1")
    with agg.lock:
        assert agg.FEED_STATE["consecutive_synthetic_candles"] == 3


def test_agg_trade_resets_synthetic_counter_and_updates_freshness(monkeypatch):
    monkeypatch.setattr(agg.time, "time", lambda: 2000.0)
    FakeDateTime.current = datetime.datetime(2026, 3, 13, 12, 31, 5)
    monkeypatch.setattr(agg.datetime, "datetime", FakeDateTime)
    with agg.lock:
        agg.FEED_STATE["consecutive_synthetic_candles"] = 3

    raw = json.dumps(
        {
            "stream": "btcusdt@aggTrade",
            "data": {"p": "101.25", "q": "0.5", "m": False},
        }
    )
    agg._on_message(None, raw)

    with agg.lock:
        assert agg.FEED_STATE["consecutive_synthetic_candles"] == 0
        assert agg.buffer.trades == 1
        assert agg.buffer.close == 101.25
    with agg.state_lock:
        assert agg.WS_STATE["last_agg_trade_ts"] == 2000.0
        assert agg.WS_STATE["last_real_trade_price"] == 101.25
        assert agg.WS_STATE["real_trade_count"] == 1
