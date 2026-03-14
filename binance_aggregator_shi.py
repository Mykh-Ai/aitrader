"""
Стратегія Ші v1.0 — Фаза 1: Raw Data Collector
Binance BTCUSDT Perpetual Futures — публічні дані для сигналів
Торгівля: Binance Spot Margin BTC/USDC

Збирає (1m агрегація):
  - OHLCV (Open, High, Low, Close, Volume)
  - Trades count
  - BuyQty / SellQty (для delta/CVD в Фазі 2)
  - Open Interest (REST polling — WS не дає OI для futures)
  - Funding Rate (з markPrice WS stream)
  - Liquidation volume Buy/Sell (з forceOrder WS stream)

Зберігання: CSV по днях → feed/YYYY-MM-DD.csv

WS streams (fstream.binance.com):
  - btcusdt@aggTrade        → trades
  - btcusdt@forceOrder      → liquidations
  - btcusdt@markPrice@1s    → funding rate + mark price

REST (fapi.binance.com):
  - /fapi/v1/openInterest   → OI snapshot кожну хвилину
"""

import json
import time
import datetime
import threading
import os
import sys
import signal

# ─── Опціональні залежності ──────────────────────────────────────
try:
    import websocket
except ImportError:
    print("❌ pip install websocket-client")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ pip install requests")
    sys.exit(1)

# ─── Конфігурація ────────────────────────────────────────────────
SYMBOL = "BTCUSDT"
WS_BASE = "wss://fstream.binance.com/stream?streams="
REST_BASE = "https://fapi.binance.com"

FEED_DIR = os.environ.get("FEED_DIR", "./feed")
LOGS_DIR = os.environ.get("LOGS_DIR", "./logs")
os.makedirs(FEED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

AGG_INTERVAL = 60  # секунд

# ─── CSV ─────────────────────────────────────────────────────────
CSV_HEADER = (
    "Timestamp,Open,High,Low,Close,"
    "Volume,AggTrades,BuyQty,SellQty,"
    "VWAP,"
    "OpenInterest,FundingRate,"
    "LiqBuyQty,LiqSellQty,"
    "IsSynthetic\n"
)


# ─── Буфер свічки ───────────────────────────────────────────────
class CandleBuffer:
    """Агрегує трейди і ліквідації за 1 хвилину в пам'яті."""

    def __init__(self):
        self.reset()
        self.open_interest = 0.0
        self.funding_rate = 0.0
        self.mark_price = 0.0
        self.last_price = 0.0

    def reset(self):
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = 0.0
        self.trades = 0
        self.buy_qty = 0.0
        self.sell_qty = 0.0
        self.notional = 0.0
        self.liq_buy_qty = 0.0
        self.liq_sell_qty = 0.0

    def add_trade(self, price: float, qty: float, is_buyer_maker: bool):
        """
        Binance aggTrade: m=True → seller is taker (Sell),
                          m=False → buyer is taker (Buy).
        """
        if self.open is None:
            self.open = price
        self.close = price
        self.last_price = price
        self.high = max(self.high, price) if self.high is not None else price
        self.low = min(self.low, price) if self.low is not None else price
        self.volume += qty
        self.notional += price * qty
        self.trades += 1
        if is_buyer_maker:
            self.sell_qty += qty
        else:
            self.buy_qty += qty

    def add_liquidation(self, qty: float, side: str):
        """
        forceOrder: side='SELL' → лонг ліквідований (market sell).
                    side='BUY'  → шорт ліквідований (market buy).
        """
        if side == "SELL":
            self.liq_sell_qty += qty
        else:
            self.liq_buy_qty += qty

    def is_empty(self) -> bool:
        return self.trades == 0

    def to_csv_row(self, timestamp: str, is_synthetic: int) -> str:
        vwap = self.notional / self.volume if self.volume > 0 else self.close
        return (
            f"{timestamp},"
            f"{self.open:.2f},{self.high:.2f},{self.low:.2f},{self.close:.2f},"
            f"{self.volume:.6f},{self.trades},{self.buy_qty:.6f},{self.sell_qty:.6f},"
            f"{vwap:.2f},"
            f"{self.open_interest:.2f},{self.funding_rate:.8f},"
            f"{self.liq_buy_qty:.6f},{self.liq_sell_qty:.6f},"
            f"{is_synthetic}\n"
        )


buffer = CandleBuffer()
lock = threading.Lock()
last_flushed_ts = None


# ─── Логування ───────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        log_path = os.path.join(LOGS_DIR, "aggregator.log")
        with open(log_path, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# WebSocket — Combined Stream
# ═══════════════════════════════════════════════════════════════════
#
# Binance дозволяє підписатись на кілька стрімів одним з'єднанням:
#   wss://fstream.binance.com/stream?streams=stream1/stream2/stream3
#
# Формат повідомлення: {"stream": "btcusdt@aggTrade", "data": {...}}
# ═══════════════════════════════════════════════════════════════════

websocket.setdefaulttimeout(10)

STREAMS = "/".join([
    f"{SYMBOL.lower()}@aggTrade",
    f"{SYMBOL.lower()}@forceOrder",
    f"{SYMBOL.lower()}@markPrice@1s",
])
WS_URL = WS_BASE + STREAMS

WS_STATE = {"connected": False, "retries": 0}


def _on_open(ws):
    WS_STATE["connected"] = True
    WS_STATE["retries"] = 0
    log(f"✅ Binance Futures WS connected — {SYMBOL}")
    log(f"   Streams: aggTrade, forceOrder, markPrice@1s")


def _on_message(ws, raw):
    try:
        msg = json.loads(raw)
    except Exception:
        return

    stream = msg.get("stream", "")
    data = msg.get("data", {})

    # ── aggTrade ─────────────────────────────────────────────
    # {"e":"aggTrade","s":"BTCUSDT","p":"97123.50","q":"0.010",
    #  "m":true, "T":1717171717000, ...}
    if "aggTrade" in stream:
        price = float(data["p"])
        qty = float(data["q"])
        is_buyer_maker = data["m"]
        with lock:
            buffer.add_trade(price, qty, is_buyer_maker)

    # ── forceOrder (liquidations) ────────────────────────────
    # {"e":"forceOrder","o":{"s":"BTCUSDT","S":"SELL","q":"0.500",
    #  "p":"96500.00","ap":"96480.30", ...}}
    elif "forceOrder" in stream:
        order = data.get("o", {})
        qty = float(order.get("q", 0))
        side = order.get("S", "")  # "BUY" або "SELL"
        with lock:
            buffer.add_liquidation(qty, side)

    # ── markPrice (funding rate) ─────────────────────────────
    # {"e":"markPriceUpdate","s":"BTCUSDT","p":"97100.00",
    #  "r":"0.00010000","T":1717171717000, ...}
    elif "markPrice" in stream:
        with lock:
            buffer.funding_rate = float(data.get("r", 0))
            buffer.mark_price = float(data.get("p", 0))


def _on_error(ws, error):
    log(f"⚠️ WS error: {error}")
    try:
        ws.close()
    except Exception:
        pass


def _on_close(ws, code, msg):
    WS_STATE["connected"] = False
    log(f"⚠️ WS closed: code={code} msg={msg}")


def ws_loop():
    """Reconnect loop з exponential backoff."""
    backoff = 2
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=_on_open,
                on_message=_on_message,
                on_error=_on_error,
                on_close=_on_close,
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            WS_STATE["retries"] += 1
            log(f"⚠️ WS exception: {e} | retry #{WS_STATE['retries']}")
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)


# ═══════════════════════════════════════════════════════════════════
# REST — Open Interest (Binance не дає OI через futures WS)
# ═══════════════════════════════════════════════════════════════════
def fetch_open_interest():
    """GET /fapi/v1/openInterest — раз на хвилину перед flush."""
    try:
        r = requests.get(
            f"{REST_BASE}/fapi/v1/openInterest",
            params={"symbol": SYMBOL},
            timeout=5,
        )
        data = r.json()
        oi = float(data.get("openInterest", 0))
        with lock:
            buffer.open_interest = oi
    except Exception as e:
        log(f"⚠️ REST OI error: {e}")


def oi_loop():
    """Окремий цикл polling OI кожні 60 секунд."""
    while True:
        fetch_open_interest()
        time.sleep(60)


# ═══════════════════════════════════════════════════════════════════
# Flush — запис у CSV
# ═══════════════════════════════════════════════════════════════════
def get_csv_path() -> str:
    day = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return os.path.join(FEED_DIR, f"{day}.csv")


def _read_last_data_timestamp(csv_path: str):
    """Дешево читає Timestamp останнього data-рядка (без повного scan)."""
    if not os.path.isfile(csv_path):
        return None

    try:
        with open(csv_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            if file_size == 0:
                return None

            pos = file_size
            chunk_size = 4096
            tail = b""

            while pos > 0:
                read_size = min(chunk_size, pos)
                pos -= read_size
                f.seek(pos)
                tail = f.read(read_size) + tail
                lines = tail.splitlines()
                if len(lines) >= 2 or pos == 0:
                    for raw_line in reversed(lines):
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if line:
                            ts = line.split(",", 1)[0]
                            if ts != "Timestamp":
                                return ts
                            return None
    except Exception as e:
        log(f"⚠️ Tail read error ({os.path.basename(csv_path)}): {e}")

    return None


def flush_candle():
    """Зберігає хвилинну свічку в CSV і скидає буфер."""

    global last_flushed_ts

    with lock:
        bar_time = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        ts = bar_time.strftime("%Y-%m-%d %H:%M:%S")

        if last_flushed_ts == ts:
            log(f"⏭️ Skip duplicate flush (in-memory guard): {ts}")
            return

        is_synthetic = 0
        if buffer.is_empty():
            selected_price = buffer.mark_price or buffer.last_price or 0.0
            buffer.open = selected_price
            buffer.high = selected_price
            buffer.low = selected_price
            buffer.close = selected_price
            is_synthetic = 1

        row = buffer.to_csv_row(ts, is_synthetic)

        # Зберігаємо OI/FR для наступної свічки
        oi = buffer.open_interest
        fr = buffer.funding_rate
        buffer.reset()
        buffer.open_interest = oi
        buffer.funding_rate = fr

    csv_path = get_csv_path()
    existing_last_ts = _read_last_data_timestamp(csv_path)
    if existing_last_ts == ts:
        with lock:
            last_flushed_ts = ts
        log(f"⏭️ Skip duplicate flush (file tail guard): {ts} already in {os.path.basename(csv_path)}")
        return

    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, "a") as f:
            if not file_exists:
                f.write(CSV_HEADER)
            f.write(row)
        with lock:
            last_flushed_ts = ts
    except Exception as e:
        log(f"❌ CSV write error: {e}")
        return

    log(f"📊 {os.path.basename(csv_path)} | OI={oi:.0f} | FR={fr:.6f}")


# ═══════════════════════════════════════════════════════════════════
# Health monitor
# ═══════════════════════════════════════════════════════════════════
def health_loop():
    while True:
        time.sleep(300)
        csv_path = get_csv_path()
        candles = 0
        if os.path.isfile(csv_path):
            with open(csv_path, "r") as f:
                candles = max(0, sum(1 for _ in f) - 1)

        ws_icon = "✅" if WS_STATE["connected"] else "❌"
        log(
            f"💓 Health: WS={ws_icon} | "
            f"OI={buffer.open_interest:.0f} | "
            f"FR={buffer.funding_rate:.6f} | "
            f"Mark={buffer.mark_price:.2f} | "
            f"Candles={candles}/1440"
        )


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════
def main():
    log("=" * 60)
    log("🚀 Стратегія Ші v1.0 — Phase 1 Aggregator")
    log(f"   Signal source : Binance Futures {SYMBOL} Perpetual")
    log(f"   Execution     : Binance Spot Margin BTC/USDC")
    log(f"   Interval      : {AGG_INTERVAL}s")
    log(f"   Feed dir      : {FEED_DIR}")
    log("=" * 60)

    # Graceful shutdown
    def _shutdown(sig, frame):
        log("🛑 Shutdown — flushing last candle...")
        flush_candle()
        log("👋 Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Потоки
    threading.Thread(target=ws_loop, daemon=True, name="ws-binance").start()
    threading.Thread(target=oi_loop, daemon=True, name="oi-poller").start()
    threading.Thread(target=health_loop, daemon=True, name="health").start()

    # Синхронізація на початок хвилини
    sleep_to = AGG_INTERVAL - (time.time() % AGG_INTERVAL)
    log(f"⏳ Перша свічка через {sleep_to:.0f}с")
    time.sleep(sleep_to)

    # Основний цикл
    while True:
        flush_candle()
        delay = AGG_INTERVAL - (time.time() % AGG_INTERVAL)
        time.sleep(delay)


if __name__ == "__main__":
    main()
