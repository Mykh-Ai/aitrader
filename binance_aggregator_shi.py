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

WS streams (fstream.binance.com/market):
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
WS_BASE = "wss://fstream.binance.com/market/stream?streams="
REST_BASE = "https://fapi.binance.com"

FEED_DIR = os.environ.get("FEED_DIR", "./feed")
LOGS_DIR = os.environ.get("LOGS_DIR", "./logs")
os.makedirs(FEED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

AGG_INTERVAL = 60  # секунд
WS_STALE_AGG_TRADE_SECONDS = int(os.environ.get("WS_STALE_AGG_TRADE_SECONDS", "180"))
WS_STALE_MARK_PRICE_SECONDS = int(os.environ.get("WS_STALE_MARK_PRICE_SECONDS", "180"))
WS_WATCHDOG_INTERVAL_SECONDS = int(os.environ.get("WS_WATCHDOG_INTERVAL_SECONDS", "30"))
MAX_CONSECUTIVE_SYNTHETIC_CANDLES = int(os.environ.get("MAX_CONSECUTIVE_SYNTHETIC_CANDLES", "5"))

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
state_lock = threading.Lock()
active_ws_lock = threading.Lock()
last_flushed_ts = None
active_ws = None
FEED_STATE = {
    "consecutive_synthetic_candles": 0,
}


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
#   wss://fstream.binance.com/market/stream?streams=stream1/stream2/stream3
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

WS_STATE = {
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


def _current_minute_key() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _age_seconds(timestamp, now=None):
    if timestamp is None:
        return None
    now = time.time() if now is None else now
    return max(0.0, now - timestamp)


def _age_text(age) -> str:
    return "n/a" if age is None else f"{age:.0f}s"


def _is_stale(timestamp, connected_at, now, threshold_seconds: int) -> bool:
    reference_ts = timestamp if timestamp is not None else connected_at
    return reference_ts is not None and (now - reference_ts) > threshold_seconds


def _ws_snapshot(now=None):
    now = time.time() if now is None else now
    minute_key = _current_minute_key()
    with state_lock:
        connected = WS_STATE["connected"]
        connected_at = WS_STATE["connected_at"]
        last_agg_trade_ts = WS_STATE["last_agg_trade_ts"]
        last_mark_price_ts = WS_STATE["last_mark_price_ts"]
        last_ws_message_ts = WS_STATE["last_ws_message_ts"]
        real_trade_count = (
            WS_STATE["real_trade_count"]
            if WS_STATE["real_trade_minute"] == minute_key
            else 0
        )
        snapshot = {
            "connected": connected,
            "connected_at": connected_at,
            "last_agg_trade_ts": last_agg_trade_ts,
            "last_mark_price_ts": last_mark_price_ts,
            "last_ws_message_ts": last_ws_message_ts,
            "last_real_trade_price": WS_STATE["last_real_trade_price"],
            "real_trade_count": real_trade_count,
            "watchdog_reconnects": WS_STATE["watchdog_reconnects"],
            "watchdog_close_requested": WS_STATE["watchdog_close_requested"],
        }

    snapshot["agg_trade_age"] = _age_seconds(last_agg_trade_ts, now)
    snapshot["mark_price_age"] = _age_seconds(last_mark_price_ts, now)
    snapshot["ws_message_age"] = _age_seconds(last_ws_message_ts, now)
    snapshot["agg_trade_stale"] = connected and _is_stale(
        last_agg_trade_ts, connected_at, now, WS_STALE_AGG_TRADE_SECONDS
    )
    snapshot["mark_price_stale"] = connected and _is_stale(
        last_mark_price_ts, connected_at, now, WS_STALE_MARK_PRICE_SECONDS
    )
    snapshot["stale"] = snapshot["agg_trade_stale"] or snapshot["mark_price_stale"]
    return snapshot


def request_ws_reconnect(reason: str) -> bool:
    """Close the active WS so the single ws_loop reconnects naturally."""

    global active_ws

    with active_ws_lock:
        ws = active_ws
        with state_lock:
            if WS_STATE["watchdog_close_requested"]:
                return False

        if ws is None:
            log("⚠️ WS watchdog found no active WebSocketApp to close")
            return False

        try:
            ws.close()
        except Exception as e:
            log(f"⚠️ WS watchdog close failed: {e}")
            return False

        with state_lock:
            WS_STATE["watchdog_close_requested"] = True
            WS_STATE["watchdog_reconnects"] += 1
            reconnects = WS_STATE["watchdog_reconnects"]

        log(f"⚠️ WS watchdog reconnect #{reconnects}: {reason}")

    return True


def check_ws_freshness(now=None) -> bool:
    """Return True when stale connected WS data triggered a forced close."""

    snapshot = _ws_snapshot(now=now)
    if (
        not snapshot["connected"]
        or not snapshot["stale"]
        or snapshot["watchdog_close_requested"]
    ):
        return False

    reasons = []
    if snapshot["agg_trade_stale"]:
        reasons.append(
            f"aggTrade age={_age_text(snapshot['agg_trade_age'])} "
            f"(threshold={WS_STALE_AGG_TRADE_SECONDS}s)"
        )
    if snapshot["mark_price_stale"]:
        reasons.append(
            f"markPrice age={_age_text(snapshot['mark_price_age'])} "
            f"(threshold={WS_STALE_MARK_PRICE_SECONDS}s)"
        )

    with lock:
        mark_price = buffer.mark_price
        synthetic_count = FEED_STATE["consecutive_synthetic_candles"]

    reason = (
        "; ".join(reasons)
        + f" | last_real_trade_price={snapshot['last_real_trade_price']} "
        + f"| mark_price={mark_price:.2f} "
        + f"| consecutive_synthetic={synthetic_count}"
    )
    return request_ws_reconnect(reason)


def _on_open(ws):
    now = time.time()
    with state_lock:
        WS_STATE["connected"] = True
        WS_STATE["connected_at"] = now
        WS_STATE["last_agg_trade_ts"] = None
        WS_STATE["last_mark_price_ts"] = None
        WS_STATE["last_ws_message_ts"] = now
        WS_STATE["retries"] = 0
        WS_STATE["real_trade_minute"] = None
        WS_STATE["real_trade_count"] = 0
        WS_STATE["watchdog_close_requested"] = False
    log(f"✅ Binance Futures WS connected — {SYMBOL}")
    log(f"   Streams: aggTrade, forceOrder, markPrice@1s")


def _on_message(ws, raw):
    try:
        msg = json.loads(raw)
    except Exception:
        return

    stream = msg.get("stream", "")
    data = msg.get("data", {})
    now = time.time()

    with state_lock:
        WS_STATE["last_ws_message_ts"] = now

    # ── aggTrade ─────────────────────────────────────────────
    # {"e":"aggTrade","s":"BTCUSDT","p":"97123.50","q":"0.010",
    #  "m":true, "T":1717171717000, ...}
    if "aggTrade" in stream:
        price = float(data["p"])
        qty = float(data["q"])
        is_buyer_maker = data["m"]
        minute_key = _current_minute_key()
        with lock:
            buffer.add_trade(price, qty, is_buyer_maker)
            FEED_STATE["consecutive_synthetic_candles"] = 0
        with state_lock:
            WS_STATE["last_agg_trade_ts"] = now
            WS_STATE["last_real_trade_price"] = price
            if WS_STATE["real_trade_minute"] != minute_key:
                WS_STATE["real_trade_minute"] = minute_key
                WS_STATE["real_trade_count"] = 0
            WS_STATE["real_trade_count"] += 1

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
        with state_lock:
            WS_STATE["last_mark_price_ts"] = now


def _on_error(ws, error):
    log(f"⚠️ WS error: {error}")
    try:
        ws.close()
    except Exception:
        pass


def _on_close(ws, code, msg):
    with state_lock:
        WS_STATE["connected"] = False
        WS_STATE["connected_at"] = None
    log(f"⚠️ WS closed: code={code} msg={msg}")


def ws_loop():
    """Reconnect loop з exponential backoff."""
    global active_ws

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
            with active_ws_lock:
                active_ws = ws
            try:
                ws.run_forever(ping_interval=20, ping_timeout=10)
            finally:
                with active_ws_lock:
                    if active_ws is ws:
                        active_ws = None
                with state_lock:
                    WS_STATE["connected"] = False
                    WS_STATE["connected_at"] = None
                    WS_STATE["watchdog_close_requested"] = False
        except Exception as e:
            with state_lock:
                WS_STATE["retries"] += 1
                retries = WS_STATE["retries"]
            log(f"⚠️ WS exception: {e} | retry #{retries}")
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


def watchdog_loop():
    """Close stale connected WS sessions; ws_loop owns reconnection."""
    while True:
        time.sleep(WS_WATCHDOG_INTERVAL_SECONDS)
        check_ws_freshness()


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
        skip_synthetic = False
        if buffer.is_empty():
            FEED_STATE["consecutive_synthetic_candles"] += 1
            synthetic_count = FEED_STATE["consecutive_synthetic_candles"]
            if synthetic_count > MAX_CONSECUTIVE_SYNTHETIC_CANDLES:
                oi = buffer.open_interest
                fr = buffer.funding_rate
                mark = buffer.mark_price
                last_price = buffer.last_price
                buffer.reset()
                buffer.open_interest = oi
                buffer.funding_rate = fr
                buffer.mark_price = mark
                buffer.last_price = last_price
                last_flushed_ts = ts
                skip_synthetic = True
            else:
                selected_price = buffer.mark_price or buffer.last_price or 0.0
                buffer.open = selected_price
                buffer.high = selected_price
                buffer.low = selected_price
                buffer.close = selected_price
                is_synthetic = 1
        else:
            FEED_STATE["consecutive_synthetic_candles"] = 0

        if skip_synthetic:
            synthetic_count = FEED_STATE["consecutive_synthetic_candles"]
            mark_price = buffer.mark_price
            last_price = buffer.last_price
            oi = buffer.open_interest
            fr = buffer.funding_rate
        else:
            synthetic_count = FEED_STATE["consecutive_synthetic_candles"]
            selected_price = None
            row = buffer.to_csv_row(ts, is_synthetic)

            # Зберігаємо OI/FR для наступної свічки
            oi = buffer.open_interest
            fr = buffer.funding_rate
            mark = buffer.mark_price
            last_price = buffer.last_price
            buffer.reset()
            buffer.open_interest = oi
            buffer.funding_rate = fr
            buffer.mark_price = mark
            buffer.last_price = last_price

    if skip_synthetic:
        log(
            f"🚨 Synthetic candle limit exceeded at {ts}: "
            f"consecutive_synthetic={synthetic_count}, "
            f"max={MAX_CONSECUTIVE_SYNTHETIC_CANDLES}; "
            f"skipping CSV write until real aggTrade data resumes | "
            f"mark_price={mark_price:.2f} last_price={last_price:.2f} "
            f"OI={oi:.0f} FR={fr:.6f}"
        )
        request_ws_reconnect(
            f"synthetic candle limit exceeded "
            f"({synthetic_count}>{MAX_CONSECUTIVE_SYNTHETIC_CANDLES})"
        )
        return

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

        snapshot = _ws_snapshot()
        with lock:
            open_interest = buffer.open_interest
            funding_rate = buffer.funding_rate
            mark_price = buffer.mark_price
            synthetic_count = FEED_STATE["consecutive_synthetic_candles"]

        if not snapshot["connected"]:
            ws_status = "DISCONNECTED"
        elif snapshot["stale"]:
            ws_status = "STALE"
        else:
            ws_status = "OK"

        log(
            f"💓 Health: WS={ws_status} connected={snapshot['connected']} | "
            f"aggTradeAge={_age_text(snapshot['agg_trade_age'])} | "
            f"markPriceAge={_age_text(snapshot['mark_price_age'])} | "
            f"wsMsgAge={_age_text(snapshot['ws_message_age'])} | "
            f"consecutive_synthetic={synthetic_count} | "
            f"real_trade_count_current_minute={snapshot['real_trade_count']} | "
            f"last_real_trade_price={snapshot['last_real_trade_price']} | "
            f"mark_price={mark_price:.2f} | "
            f"watchdog_reconnects={snapshot['watchdog_reconnects']} | "
            f"OI={open_interest:.0f} | "
            f"FR={funding_rate:.6f} | "
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
    log(
        f"   WS watchdog   : aggTrade>{WS_STALE_AGG_TRADE_SECONDS}s, "
        f"markPrice>{WS_STALE_MARK_PRICE_SECONDS}s, check={WS_WATCHDOG_INTERVAL_SECONDS}s"
    )
    log(f"   Synthetic cap : {MAX_CONSECUTIVE_SYNTHETIC_CANDLES} consecutive candles")
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
    threading.Thread(target=watchdog_loop, daemon=True, name="ws-watchdog").start()
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
