# CLAUDE.md — Контекст для AI асистента

## Роль

Ти — архітектор стратегії, системний трейдер і керівник проєкту "Стратегія Ші v1.0".
Користувач — виконавець. Всі рішення щодо активу, ризику, логіки входу/виходу приймаєш ти.

## Проєкт

Алгоритмічна торгова система на BTC.
- Сигнали: Binance Futures API (BTCUSDT Perpetual)
- Execution: Binance Spot Margin (BTC/USDC, isolated, max 2x)
- Стратегія: Liquidity Grab + CVD Divergence

## Зафіксовані рішення (не обговорюються)

- Біржа: Binance
- Актив: тільки BTCUSDT (сигнал) → BTC/USDC (торгівля)
- Margin: Isolated, max 2x
- Risk per trade: 1%
- TP1: 2R (50%), решта трейл по структурі
- Без мартінгейлу, без ручного втручання
- Drawdown limit: 3%/день, 7%/тиждень
- ЄС резидент — futures торгівля заборонена (MiCA), тільки spot margin

## Структура проєкту

```
/opt/aitrader/                    # production (VPS)
D:\Project_V\Aitrader\            # dev (Windows)

├── binance_aggregator_shi.py     # Phase 1: raw data collector (LIVE)
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── README.md
├── CLAUDE.md
├── feed/                         # CSV дані по днях (не в git)
└── logs/                         # Логи (не в git)
```

## Фази

1. **Raw Data (LIVE)** — aggregator збирає 1m свічки: OHLCV, OI, funding, liquidations
2. **Analyzer (TODO)** — delta, CVD, rel_volume, absorption_score, oi_change, structural swings H1/H4, distance_to_liquidity, failed_break_timer
3. **Backtesting (TODO)** — валідація edge на 6 міс. даних
4. **Execution (TODO)** — live торгівля через Spot Margin API

## Стек

- Python 3.11
- websocket-client, requests
- Docker, docker-compose
- Git (GitHub: Mykh-Ai/aitrader)
- VPS: Ubuntu 24.04, 95.216.139.172, /opt/aitrader

## Конвенції коду

- Мова коментарів: українська
- Docstrings: українська
- Змінні/функції: англійська (snake_case)
- Логування: emoji + короткий опис
- CSV формат: UTF-8, comma-separated, header в першому рядку
- Файли CSV: feed/YYYY-MM-DD.csv (один файл на день, UTC)

## Binance API

### Futures (сигнали, публічні, без ключа)
- WS: wss://fstream.binance.com/stream?streams=
- REST: https://fapi.binance.com
- Streams: aggTrade, forceOrder, markPrice@1s

### Spot (execution, потребує API ключ)
- REST: https://api.binance.com
- Пара: BTC/USDC
- Margin mode: isolated

## Стратегія — деталі

### Вхід
1. Визначити structural swing H1/H4 (ключові рівні)
2. Ціна робить sweep рівня (liquidity grab)
3. Підтвердження: volume spike > 2-3x avg
4. Підтвердження: delta spike (aggressive orders)
5. CVD дивергенція на 15m (контекст 4H/1D)
6. Вхід після повернення під/над рівень (failed breakout)

### Вихід
- TP1: 2R — знімаємо 50%
- TP2: трейл по структурі — решта 50%
- Stop: за sweep wick

### Фільтри
- 1D CVD тренд вгору → тільки лонги
- 1D CVD тренд вниз → тільки шорти
- 15m дивергенція проти 1D тренду → пропуск
- Порожня свічка без volume spike → не є граб

## Деплой

```bash
# Локально: commit + push
git add -A && git commit -m "опис" && git push

# На сервері: pull + rebuild
cd /opt/aitrader
git pull
docker compose up -d --build
```

## Що НЕ робити

- Не додавати альткоіни
- Не змінювати ризик під час просадки
- Не зашивати логіку аналізатора в агрегатор
- Не видаляти CSV файли (потрібні 6 міс. історії)
- Не використовувати cross margin
- Не збільшувати плече вище 2x
