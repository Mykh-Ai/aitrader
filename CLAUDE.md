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

## Фази

1. **Raw Data (LIVE)** — aggregator збирає 1m свічки: OHLCV, OI, funding, liquidations
2. **Analyzer (IMPLEMENTED)** — facts engine + setup research pipeline (Phase 1 + Phase 2 complete)
3. **Backtesting (TODO)** — валідація edge на 6 міс. даних
4. **Execution (TODO)** — live торгівля через Spot Margin API

## Структура проєкту

```
/opt/aitrader/                    # production (VPS)
D:\Project_V\Aitrader\            # dev (Windows)

├── binance_aggregator_shi.py     # Phase 1: raw data collector (LIVE)
├── analyzer/                     # Analyzer package (Phase 1 + 2)
│   ├── schema.py                 # Schema contracts, column registries
│   ├── loader.py                 # Raw CSV loader + validation
│   ├── base_metrics.py           # Per-bar derived metrics
│   ├── swings.py                 # H1/H4 structural swing detection
│   ├── sweeps.py                 # Sweep detection
│   ├── failed_breaks.py          # Failed-break confirmation
│   ├── absorption.py             # Rolling-ratio context features
│   ├── events.py                 # Normalized event table
│   ├── setups.py                 # Setup candidate extraction
│   ├── outcomes.py               # Forward-looking outcome metrics
│   ├── reports.py                # Grouped setup statistics
│   ├── context_reports.py        # Context-bucketed statistics
│   ├── rankings.py               # Setup group rankings
│   ├── selections.py             # Research candidate selection (SELECT/REVIEW/REJECT)
│   ├── shortlists.py             # Shortlist export view
│   ├── shortlist_explanations.py # Explanation bands + composite codes
│   ├── research_summary.py       # Final research summary surface
│   ├── io.py                     # Output helpers (CSV)
│   └── pipeline.py               # Orchestration entrypoint
├── tests/                        # Unit tests (one per module)
│   └── fixtures/                 # Shared CSV test fixtures
├── docs/
│   └── Spec_v1.0.md              # Normative Analyzer contract
├── feed/                         # CSV дані по днях (не в git)
├── logs/                         # Логи (не в git)
├── Dockerfile
├── docker-compose.yml
└── CLAUDE.md
```

## Analyzer — поточний стан

Analyzer — це **facts engine + research pipeline**. Він НЕ торгує, НЕ генерує сигнали,
НЕ розміщує ордери. Весь вихід — research-only артефакти.

### Pipeline (16 кроків)

```
load_raw_csv → add_base_metrics → annotate_swings → detect_sweeps
→ detect_failed_breaks → detect_absorption → build_events
→ extract_setup_candidates → build_setup_outcomes
→ build_setup_report → build_setup_context_report
→ build_setup_rankings → build_setup_selections
→ build_setup_shortlist → build_setup_shortlist_explanations
→ build_research_summary
```

### Data lineage

```
raw CSV → features (one row per 1m bar)
features → events (structural events)
features + events → setups (currently from failed breaks; additional types planned)
features + setups → outcomes (forward metrics: MFE, MAE, CloseReturn)
setups + outcomes → report (grouped stats)
setups + outcomes → context_report (bucketed stats)
report + context_report → rankings (scored vs baseline)
rankings → selections (SELECT/REVIEW/REJECT)
rankings + selections → shortlist (top candidates ranked)
shortlist → shortlist_explanations (categorical bands + code)
shortlist + shortlist_explanations → research_summary (final surface)
```

### Output artifacts (11 CSV)

```
analyzer_features.csv                    — one row per 1m bar
analyzer_events.csv                      — structural events
analyzer_setups.csv                      — setup candidates
analyzer_setup_outcomes.csv              — forward metrics per setup
analyzer_setup_report.csv                — grouped statistics
analyzer_setup_context_report.csv        — context-bucketed statistics
analyzer_setup_rankings.csv              — scored and ranked groups
analyzer_setup_selections.csv            — SELECT/REVIEW/REJECT per group
analyzer_setup_shortlist.csv             — ranked shortlist
analyzer_setup_shortlist_explanations.csv — explanation bands
analyzer_research_summary.csv            — final research summary
```

### Ключові константи

```
SETUP_TTL_BARS = 12              # setup lifecycle window
OUTCOME_HORIZON_BARS = 12        # forward-looking horizon
MIN_REAL_BARS_H1 = 45            # H1 completeness threshold (з 60)
MIN_REAL_BARS_H4 = 180           # H4 completeness threshold (з 240)
MAX_STATE_GAP_MINUTES = 3        # gap reset для stateful logic
MIN_SELECTION_SCORE = 0.05       # мінімальний RankingScore для SELECT
MIN_SELECTION_SAMPLE = 5         # мінімальний SampleCount
```

### Structural safety

- Synthetic bars (`IsSynthetic == 1`) виключені зі структурного аналізу
- Incomplete TF bars виключені з swing detection
- ConfirmedAt — перша матеріалізація на першому real row >= confirmation time
- Gap > 3 хвилин → reset pending state (fail-closed)
- Anti-lookahead: 10 enforced rules (див. Spec_v1.0.md)

## Стратегія — деталі

### Торгова гіпотеза

Liquidity grab + failed break reclaim. Ціна робить sweep структурного рівня
(збирає стопи за swing high/low), потім повертається. Якщо повернення підтверджене
volume spike + delta divergence — це mean-reversion вхід після ліквідності.

Перший імплементований тип сетапу: `FAILED_BREAK_UP/DOWN` → setup candidate.
Додаткові типи сетапів будуть додані пізніше.

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

## Стек

- Python 3.11
- pandas (Analyzer)
- websocket-client, requests (Aggregator)
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
- Тести: один файл на модуль, `pytest tests/`
- Spec: `docs/Spec_v1.0.md` — нормативний контракт, тести пишуться під spec

## Binance API

### Futures (сигнали, публічні, без ключа)
- WS: wss://fstream.binance.com/stream?streams=
- REST: https://fapi.binance.com
- Streams: aggTrade, forceOrder, markPrice@1s

### Spot (execution, потребує API ключ)
- REST: https://api.binance.com
- Пара: BTC/USDC
- Margin mode: isolated

## Деплой

```bash
# Локально: commit + push
git add -A && git commit -m "опис" && git push

# На сервері: pull + rebuild
cd /opt/aitrader
git pull
docker compose up -d --build
```

## SSH cleanup (Windows / sandboxed AI agents)

Sandboxed AI agents (Codex, Claude Code тощо) можуть додавати службових
користувачів (напр. CodexSandboxUsers) до ACL `~/.ssh` при SSH операціях.
Це ламає нативний SSH користувача після завершення сесії.

**Кожна сесія з SSH МУСИТЬ завершуватись:**
```powershell
icacls C:\Users\User\.ssh /remove *S-1-5-21-3584294112-1179844679-616002924-1003
icacls C:\Users\User\.ssh\config /inheritance:r /grant:r "User:(R)" "SYSTEM:(R)" "Administrators:(R)"
```
Перевірка: `ssh root@95.216.139.172 "echo ssh-ok"` → `ssh-ok`.
Детальніше: `research/OPS.md` секція 1.

## Що НЕ робити

- Не додавати альткоіни
- Не змінювати ризик під час просадки
- Не зашивати логіку аналізатора в агрегатор
- Не видаляти CSV файли (потрібні 6 міс. історії)
- Не використовувати cross margin
- Не збільшувати плече вище 2x
- Не описувати selections/shortlist як торгові рішення — це research triage
- Не додавати execution логіку до Phase 4
