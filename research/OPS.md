# Research Operations Guide

Operational reference for the routine research cycle.
Read this before executing any research cycle prompt.

---

## 1. Environment

```bash
# Server
ssh root@95.216.139.172
cd /opt/aitrader
source .venv/bin/activate
```

All analyzer runs and backtest outputs live on the server.
Local repo (`D:\Project_V\Aitrader`) has only code and research artifacts.

---

## 2. Automated pipeline: research_cycle.py

**Основний інструмент — один скрипт замість ручних SSH calls.**

```bash
# Повний цикл (probe → replay → record → slice → diagnostics)
python3 research_cycle.py

# Тільки probe + діагностика, без replay
python3 research_cycle.py --dry-run

# Інший шлях до runs
python3 research_cycle.py --runs-dir /opt/aitrader/analyzer_runs
```

Скрипт автоматично:
1. Знаходить unprocessed runs (`_processed.json` відсутній)
2. Probe кожного (setups, shortlist, FormalizationEligible)
3. Replay через backtester якщо FE > 0 (заморожені параметри)
4. Читає promotion decisions (включно з fan-out derived_run_*)
5. Пише `_processed.json` маркери
6. Запускає slice analysis
7. Перевіряє якість даних (feed gaps, anomalies, patterns)
8. Виводить структурований JSON на stdout

**Заморожені параметри backtester** (зашиті в скрипт, не міняти):
```python
ruleset_source_formalization_mode = "SHORTLIST_FIRST"
variant_names = ("BASE",)
cost_model_id = "COST_MODEL_ZERO_SKELETON_ONLY"
same_bar_policy_id = "SAME_BAR_CONSERVATIVE_V0_1"
replay_semantics_version = "REPLAY_V0_1"
```

Output dir convention: `/opt/aitrader/backtest_runs/<run_id>_routine_YYYYMMDD`

---

## 3. _processed.json marker protocol

**Маркери пишуться скриптом автоматично.** Ця секція — reference.

```json
{
  "processed_at": "YYYY-MM-DD",
  "routine_status": "BACKTESTED | NO_REPLAYABLE_RULESETS | REPLAY_FAILED",
  "backtest_output": "/opt/aitrader/backtest_runs/<dir>",
  "promotion_outcome": "REJECT | REVIEW | PROMOTE | N/A",
  "notes": "..."
}
```

- **File exists** in `analyzer_runs/<run_id>/` → run processed, skip.
- **File absent** → run is new, include in cycle.

---

## 4. run_log.csv protocol

**Оновлюється агентом (не скриптом) після парсингу JSON output.**

- Якщо рядок з `routine_status=UNPROCESSED` вже є → **replace**
- Якщо рядка немає → **append**
- Ніколи не дублювати для одного `analyzer_run_id`

Row format:
```
YYYY-MM-DD,<analyzer_run_id>,<backtest_output_dir>,<formalizable_rows>,<promotion_outcome>,<routine_status>,<notes>
```

---

## 5. Run outcome states

| State | Meaning |
|---|---|
| `NO_REPLAYABLE_RULESETS` | FormalizationEligible == 0, backtester not run |
| `BACKTESTED_REJECT` | All promotion decisions = REJECT |
| `BACKTESTED_REVIEW` | At least one promotion_decision = REVIEW |
| `BACKTESTED_PROMOTE` | At least one promotion_decision = PROMOTE |
| `REPLAY_FAILED` | Backtester raised exception |
| `DUPLICATE_SKIP` | Same-day re-run with identical SetupIds, skipped |

---

## 6. Slice analysis

Вбудована в `research_cycle.py` (крок 6). Також можна запустити окремо:

```bash
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs
```

Results: `research/results/`. Findings: `research/findings/`.
Methodology frozen — do NOT change slice logic between runs.

---

## 7. Current project state

**Do not maintain a manual list here — it goes stale.**

Authoritative sources:
- **Server**: `ls /opt/aitrader/analyzer_runs/*/_processed.json` — which runs have markers
- **Repo**: `research/run_log.csv` — full processing history with outcomes
- **Verdicts**: `research/verdicts/weekly_<YYYY-MM-DD>.md` — architect interpretation per cycle
- **Diagnostics**: `research_cycle.py --dry-run` — live data quality check

The key signal to watch for: first run where `promotion_outcome != REJECT`.
