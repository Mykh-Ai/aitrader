import datetime
import importlib
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
