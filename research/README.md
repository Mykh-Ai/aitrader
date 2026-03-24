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
Агент запустить `research_cycle.py` на сервері (один SSH call),
отримає JSON з результатами, перевірить якість даних,
оновить `run_log.csv` і сформує `research/handoff/`.

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
                        SERVER                             LOCAL REPO
                          │                                    │
  cron → analyzer         │                                    │
       → analyzer_runs/   │                                    │
                          │                                    │
  research_cycle.py ──────┤   prompts/weekly_research.txt      │
    probe + replay        │              │                     │
    _processed.json       │         [Крок 1: агент]            │
    slice analysis        │              │                     │
    diagnostics           │              ▼                     │
         │                │    parse JSON output               │
         └── JSON ────────┼──► run_log.csv (update)            │
              stdout      │    results/ (snapshot)             │
                          │    handoff/ (7 files)              │
                          │              │                     │
                          │    prompts/Shi_research.txt        │
                          │              │                     │
                          │         [Крок 2: архітектор]       │
                          │              │                     │
                          │              ▼                     │
                          │    reads handoff/                  │
                          │    writes verdicts/                │
                          │    cleans handoff/                 │
```

---

## Structure

```
Aitrader/
├── research_cycle.py                      — automated pipeline script (also on server)
│
├── research/
│   ├── README.md                          — ця інструкція
│   ├── OPS.md                             — операційний довідник
│   ├── run_log.csv                        — журнал всіх оброблених runs
│   ├── slice_analysis_reclaim_context.py  — reusable slice analysis script
│   ├── findings/                          — research memos (frozen, не міняти)
│   │   └── 2026-03_reclaim_context_asymmetry.md
│   ├── results/                           — structured output snapshots
│   │   ├── reclaim_context_asymmetry_summary.csv
│   │   └── reclaim_context_asymmetry_summary_<YYYY-MM-DD>.csv
│   ├── verdicts/                          — weekly architect verdicts
│   │   └── weekly_<YYYY-MM-DD>.md
│   └── handoff/                           — тимчасовий пакет агент→архітектор
│       ├── cycle_meta.json                   (НЕ в git, очищується після verdict)
│       ├── probe_summary.csv
│       ├── promotion_details.csv
│       ├── slice_comparison.csv
│       ├── slice_raw_output.txt
│       ├── previous_verdict.md
│       └── diagnostics.json
│
├── prompts/
│   ├── weekly_research.txt                — промт для агента (крок 1)
│   └── Shi_research.txt                   — промт для архітектора (крок 2)
```

## Running the slice analysis (standalone)

```bash
# Default: uses analyzer_runs/ relative to repo root
python research/slice_analysis_reclaim_context.py

# Custom runs directory (e.g. on server)
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs

# With date filter
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs --date-from 2026-03-12 --date-to 2026-03-17
```

Note: slice analysis is also included in `research_cycle.py` — standalone use is for ad-hoc exploration only.

## Rules

- Do NOT change slicing logic between runs — methodology must be frozen per finding
- Do NOT add new dimensions without a new dated finding memo
- Do NOT use these scripts for live trading decisions
- Do NOT modify `research_cycle.py` parameters — they are frozen

## SSH cleanup (Windows)

Sandboxed AI agents (Codex, Claude Code тощо) можуть додавати службових
користувачів до ACL `~/.ssh` при SSH доступі, що ламає нативний SSH після сесії.
Детальна інструкція — в `OPS.md` секція 1.

**Правило:** кожна сесія агента, що використовує SSH, мусить завершуватись
cleanup командами з OPS.md. Це стосується і `weekly_research.txt` циклу,
і будь-якого ad-hoc SSH доступу.
