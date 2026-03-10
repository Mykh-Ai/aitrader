# Стратегія Ші v1.0 — AI Trader

Алгоритмічна торгова система на BTC. Сигнали з Binance Futures, execution через Binance Spot Margin.

## Архітектура

```
Binance Futures API (fstream/fapi)     Binance Spot API
        │                                     │
   [сигнал/дані]                        [execution]
        │                                     │
   aggregator (Phase 1)                 executor (Phase 3)
   BTCUSDT Perpetual                    BTC/USDC margin 2x
```

## Стратегія

**Liquidity Grab + CVD Divergence**

- H1/H4 structural swing визначає ключові рівні
- Ціна знімає рівень (sweep) → volume spike + delta spike підтверджують
- CVD дивергенція на 15m (контекст 4H/1D) → вхід
- TP1 на 2R (50%), решта трейл по структурі
- Ризик: 1% на трейд, isolated margin, max 2x

## Фази проєкту

| Фаза | Статус | Опис |
|------|--------|------|
| 1. Raw Data | ✅ LIVE | Збір 1m даних: OHLCV, OI, funding, liquidations |
| 2. Analyzer | 🔜 | Delta, CVD, absorption, свінги, distance_to_liquidity |
| 3. Backtesting | 🔜 | Валідація edge на 6 міс. даних |
| 4. Execution | 🔜 | Live торгівля через Spot Margin API |

## Phase 1: Aggregator

### Що збирає (1m інтервал)

| Колонка | Джерело | Опис |
|---------|---------|------|
| Timestamp | system | UTC час свічки |
| Open, High, Low, Close | aggTrade WS | OHLCV ціни |
| Volume | aggTrade WS | Загальний обсяг |
| Trades | aggTrade WS | Кількість угод |
| BuyQty | aggTrade WS | Обсяг buy taker (для delta) |
| SellQty | aggTrade WS | Обсяг sell taker (для delta) |
| OpenInterest | REST /fapi/v1/openInterest | Відкритий інтерес (BTC) |
| FundingRate | markPrice WS | Ставка фінансування |
| LiqBuyQty | forceOrder WS | Обсяг ліквідацій шортів |
| LiqSellQty | forceOrder WS | Обсяг ліквідацій лонгів |

### Зберігання

CSV по днях: `feed/YYYY-MM-DD.csv`

### WS streams

- `btcusdt@aggTrade` — трейди
- `btcusdt@forceOrder` — ліквідації
- `btcusdt@markPrice@1s` — funding rate, mark price

### REST endpoints

- `GET /fapi/v1/openInterest?symbol=BTCUSDT` — OI snapshot раз/хв

## Запуск

### Docker (production)

```bash
docker compose up -d --build
docker logs -f shi-aggregator
```

### Локально (dev)

```bash
pip install websocket-client requests
python binance_aggregator_shi.py
```

### Змінні середовища

| Змінна | Default | Опис |
|--------|---------|------|
| FEED_DIR | ./feed | Директорія для CSV |
| LOGS_DIR | ./logs | Директорія для логів |

## Інфраструктура

- **Сервер:** VPS 95.216.139.172 (Ubuntu 24.04, 4GB RAM, 38GB disk)
- **Розміщення:** /opt/aitrader
- **Контейнер:** shi-aggregator
- **Дані:** /opt/aitrader/feed/ (монтується як volume)
- **Логи:** /opt/aitrader/logs/aggregator.log

## Health monitoring

Кожні 5 хвилин в лог пишеться:
```
💓 Health: WS=✅ | OI=83287 | FR=0.000027 | Mark=70400.00 | Candles=120/1440
```

## Обмеження (MiCA / ЄС)

- Futures торгівля заборонена для ЄС резидентів
- Futures API (публічні дані) — без обмежень
- Execution: Binance Spot Margin BTC/USDC (до 10x, ми використовуємо 2x)

## Ризик-менеджмент (зафіксований)

- Risk per trade: 1%
- Position size = Risk / StopDistance
- Режим: Isolated Margin, max 2x
- Без cross, без мартінгейлу, без ручного втручання
- Drawdown limit: 3% день / 7% тиждень → стоп торгівлі

## Заборонено

- Змінювати параметри під час просадки
- Збільшувати ризик після мінуса
- Ручне втручання в позиції
- Додавати нові активи (тільки BTC)
