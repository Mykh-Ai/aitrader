# Research Operations Guide

Operational reference for the routine research agent.
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
Local repo (`D:\Project_V\Aitrader`) has only 2 analyzer runs — always prefer server.

---

## 2. How to determine which analyzer runs are already processed

**Primary signal: `_processed.json` marker file inside the analyzer run directory.**

```bash
ls /opt/aitrader/analyzer_runs/*/  _processed.json
```

- **File exists** → run was already through the full probe → replay → verdict routine. Do not reprocess.
- **File absent** → run is new / unprocessed → include in current cycle.

### What `_processed.json` contains

```json
{
  "processed_at": "YYYY-MM-DD",
  "routine_status": "BACKTESTED | NO_REPLAYABLE_RULESETS | DUPLICATE_SKIP | SLICE_ONLY",
  "backtest_output": "/opt/aitrader/backtest_runs/<dir>",
  "promotion_outcome": "REJECT | REVIEW | PROMOTE | N/A",
  "notes": "..."
}
```

### How to write it after processing a run

```python
import json, pathlib
from datetime import date

marker = {
    "processed_at": str(date.today()),
    "routine_status": "BACKTESTED",           # or NO_REPLAYABLE_RULESETS etc.
    "backtest_output": "/opt/aitrader/backtest_runs/<dir>",
    "promotion_outcome": "REJECT",            # top-level ALL_TRADES scope decision
    "notes": "routine cycle YYYY-MM-DD"
}
pathlib.Path("/opt/aitrader/analyzer_runs/<run_id>/_processed.json").write_text(
    json.dumps(marker, indent=2)
)
```

### Also update `research/run_log.csv` (in repo, git-tracked)

After writing `_processed.json`, update `research/run_log.csv`:

- If the run already has a row with `routine_status=UNPROCESSED` → **replace** that row with final values.
- If the run has no row yet → **append** a new row.
- Never create duplicate rows for the same `analyzer_run_id`.

Row format:
```
YYYY-MM-DD,<analyzer_run_id>,<backtest_output_dir>,<formalizable_rows>,<promotion_outcome>,<routine_status>,<notes>
```

---

## 3. Standard routine flow per unprocessed run

```
1. Probe: read analyzer_setups.csv, analyzer_setup_shortlist.csv, analyzer_research_summary.csv
2. Count FormalizationEligible rows in research_summary
3. If FormalizationEligible == 0 → status = NO_REPLAYABLE_RULESETS, skip replay, write marker
4. If FormalizationEligible > 0 → run backtester (see section 4)
5. Read promotion decisions
6. Classify outcome (see section 5)
7. Write _processed.json marker
8. Append to research/run_log.csv
```

---

## 4. Backtester invocation (standard parameters — do not change)

```python
from backtester.orchestrator import run_backtester

run_backtester(
    artifact_dir="/opt/aitrader/analyzer_runs/<run_id>",
    output_dir="/opt/aitrader/backtest_runs/<run_id>_routine_YYYYMMDD",
    ruleset_source_formalization_mode="SHORTLIST_FIRST",
    variant_names=("BASE",),
    cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
    same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
    replay_semantics_version="REPLAY_V0_1",
)
```

For fan-out runs (multiple rulesets), child results are in `derived_run_*` subdirs.

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

## 6. Reading promotion decisions after replay

```python
from pathlib import Path
import pandas as pd

out_dir = Path("/opt/aitrader/backtest_runs/<run_id>")

# For single-ruleset runs:
df = pd.read_csv(out_dir / "backtest_promotion_decisions.csv")
print(df[["scope", "promotion_decision", "validation_status", "robustness_status"]])

# For fan-out runs (multiple rulesets):
for child in sorted(out_dir.glob("derived_run_*")):
    print(f"\n== {child.name} ==")
    print(pd.read_csv(child / "backtest_promotion_decisions.csv")
            [["scope", "promotion_decision"]].to_string(index=False))
```

---

## 7. Slice analysis (separate from routine)

The slice analysis script is in `research/slice_analysis_reclaim_context.py`.
Run it separately — it is NOT part of the backtester routine.

```bash
python research/slice_analysis_reclaim_context.py --runs-dir /opt/aitrader/analyzer_runs
```

Results go into `research/results/`. Findings into `research/findings/`.
Methodology is frozen — do NOT change slice logic between runs.

---

## 8. Current project state

**Do not maintain a manual list of processed runs here — it goes stale.**

Authoritative sources:
- **Server**: `ls /opt/aitrader/analyzer_runs/*/_processed.json` — which runs have markers
- **Repo**: `research/run_log.csv` — full processing history with outcomes
- **Verdicts**: `research/verdicts/weekly_<YYYY-MM-DD>.md` — architect interpretation per cycle

The key signal to watch for: first run where `promotion_outcome != REJECT`.
