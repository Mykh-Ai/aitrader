# research/

Offline research artifacts for AiTrader strategy development.

**Boundary:** Nothing here touches production logic.
All scripts are read-only against existing analyzer/backtester artifacts.

---

## Structure

```
research/
├── README.md                              — this file
├── slice_analysis_reclaim_context.py      — reusable slice analysis script
├── findings/                              — research memos (frozen findings)
│   └── 2026-03_reclaim_context_asymmetry.md
└── results/                               — structured output snapshots
    └── reclaim_context_asymmetry_summary.csv
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
