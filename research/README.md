# research/

Offline research artifacts for AiTrader strategy development.

**Boundary:** Nothing here touches production logic.
All scripts are read-only against existing analyzer/backtester artifacts.

---

## Щотижневий цикл — покрокова інструкція

### Що робити

Два промти, два кроки, один за одним:

**Крок 1 — Агент (збір даних + replay)**
```
Відкрий prompts/weekly_research.txt → вставь в чат → виконай
```
Агент підключиться до сервера, знайде нові analyzer runs, прожене backtester,
запише результати і сформує `research/handoff/` з пакетом даних для архітектора.

**Крок 2 — Архітектор (verdict)**
```
Відкрий prompts/Shi_research.txt → вставь в чат → виконай
```
Архітектор прочитає `research/handoff/`, порівняє з попереднім verdict,
напише новий verdict в `research/verdicts/weekly_<YYYY-MM-DD>.md`,
і очистить `research/handoff/`.

### Після обох кроків

- Перевір що `research/handoff/` порожній (архітектор очистив)
- Перевір що новий verdict є в `research/verdicts/`
- `git push` — щоб зміни потрапили на GitHub

---

## Data flow

```
prompts/weekly_research.txt          prompts/Shi_research.txt
         │                                      │
    [Крок 1: агент]                     [Крок 2: архітектор]
         │                                      │
         ▼                                      ▼
  server: probe + replay              reads research/handoff/
  research/run_log.csv (update)        reads previous verdict
  research/results/ (snapshot)         writes research/verdicts/
  research/handoff/ (6 files) ───────► cleans research/handoff/
```

---

## Structure

```
research/
├── README.md                              — ця інструкція
├── OPS.md                                 — операційний довідник агента
├── run_log.csv                            — журнал всіх оброблених runs
├── slice_analysis_reclaim_context.py      — reusable slice analysis script
├── findings/                              — research memos (frozen, не міняти)
│   └── 2026-03_reclaim_context_asymmetry.md
├── results/                               — structured output snapshots
│   ├── reclaim_context_asymmetry_summary.csv
│   └── reclaim_context_asymmetry_summary_<YYYY-MM-DD>.csv
├── verdicts/                              — weekly architect verdicts
│   └── weekly_<YYYY-MM-DD>.md
└── handoff/                               — тимчасовий пакет агент→архітектор
    ├── cycle_meta.json                       (НЕ в git, очищується після verdict)
    ├── probe_summary.csv
    ├── promotion_details.csv
    ├── slice_comparison.csv
    ├── slice_raw_output.txt
    └── previous_verdict.md
```

## Running the slice analysis

```bash
# Default: uses analyzer_runs/ relative to repo root
python research/slice_analysis_reclaim_context.py

# Custom runs directory (e.g. on server)
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs

# With date filter
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs --date-from 2026-03-12 --date-to 2026-03-17
```

## Rules

- Do NOT change slicing logic between runs — methodology must be frozen per finding
- Do NOT add new dimensions without a new dated finding memo
- Do NOT use these scripts for live trading decisions
