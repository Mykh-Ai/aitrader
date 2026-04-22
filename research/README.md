# research/

Offline research artifacts for AiTrader strategy development.

Boundary:
- Nothing here touches production logic.
- Public materials stay research-focused and host-agnostic.
- Server access details, private prompts, verdict workflows, and operator handoff files belong in local-only ops materials.

## Public structure

```text
research/
├── OPS.example.md                   — safe template for local ops notes
├── run_log.csv                      — processing history
├── slice_analysis_reclaim_context.py
├── findings/                        — frozen research memos
├── results/                         — structured research snapshots
├── verdicts/README.md               — placeholder for local-only verdicts
└── handoff/README.md                — placeholder for private runbook area
```

## Public workflow boundary

1. Run `research_cycle.py` in your own environment.
2. Review the structured output locally.
3. Commit only safe artifacts such as findings or summary CSVs that do not expose private operational context.

Examples:

```bash
python3 research_cycle.py
python3 research_cycle.py --dry-run
python research/slice_analysis_reclaim_context.py --runs-dir analyzer_runs
```

## Local-only boundary

Keep these out of the public repo:
- server host, IP, SSH, and absolute path details
- cron, deploy, runtime, and virtualenv procedures
- private prompts and verdict runbooks
- ephemeral handoff packages
- copied transition-data archives from local server context

Public docs should refer to these generically as `local-only ops materials`, `private runbook area`, or `local server context`.
