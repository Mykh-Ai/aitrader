# AGENTS.md

## 1) Purpose
This file defines repository-wide working rules for coding agents in `aitrader`.
Use it as a practical operating guide; keep behavior evidence-first and fail-loud.

## 2) Repository working model
AiTrader in this repo is currently a **research + deterministic backtesting stack**:
- **Implemented:** collector/aggregator, Analyzer, Backtester baseline, campaign/experiment registry baseline.
- **Planned boundary:** live Executor runtime for exchange order lifecycle and production reconciliation.

Operational implication: treat this repository as research/backtest infrastructure first; do not present it as a live execution bot.

## 3) Sources of truth
Consult these in this order before making claims or changes:
1. `README.md` (current system boundaries and module map)
2. `research/OPS.md` (authoritative routine research-cycle operations)
3. `docs/Spec_v1.0.md` (normative Analyzer contract)
4. `docs/Backtesting_Spec_v0.1.md` + `docs/Backtesting_Architecture_v0.1.md` (backtester behavior/architecture)
5. `research/README.md` (research-folder boundary)
6. Tests in `tests/` as executable contract checks

If documents conflict, prefer the most operationally current source supported by code/tests, and note the conflict explicitly in your summary.

## 4) Work modes

### A) Codebase tasks (analyzer/backtester/collector)
- Preserve deterministic artifact contracts and file naming expected by pipeline/backtester/tests.
- Keep module boundaries explicit:
  - `analyzer/`: research artifact generation only.
  - `backtester/`: deterministic replay/evaluation over analyzer artifacts.
  - `binance_aggregator_shi.py`: raw data collection.
- Make minimal, localized changes; do not refactor broadly without direct evidence/need.


## 4.1) Critical feed recovery context

- Binance USD-M Futures legacy WebSocket paths without routing (`wss://fstream.binance.com/stream?streams=...`) stopped pushing market/private stream payloads after `2026-04-23`; collector code must use `wss://fstream.binance.com/market/stream?streams=...`.
- The SHI enriched feed has a known historical gap from `2026-04-23 17:05:00` through `2026-05-06 22:51:00` UTC. Original `feed/YYYY-MM-DD.csv` files in that window contain flat/broken synthetic rows and must be treated as forensic evidence, not valid market data.
- Do not overwrite `feed/` to hide the outage. Use `feed_recovered/` for patched Analyzer/Backtester input in the affected window.
- `feed_recovered/` mirrors DeltaScout's recovered SHI-compatible feed. Its provenance lives in `D:\Project_V\btc-orderflow-system\deltascout\research_material\recovery_reports\recovery_quality_2026-04-23_1705_to_2026-05-06_2251.csv`.
- Recovered rows use real price/OHLCV/trades/buy/sell/VWAP from the legacy volume-alert archive, OI copied or forward-filled where possible, untrusted funding during the WS gap, and missing historical liquidation quantities. Do not make funding/liquidation-based conclusions from recovered rows unless explicitly marked degraded/unsupported.
- The recovery builder is in DeltaScout: `python -m deltascout.research_bundle.build_recovered_feed_gap --mirror-output-root D:\Project_V\Aitrader\feed_recovered`.

### B) Research tasks
- `research/OPS.md` governs detailed routine-cycle execution.
- Respect existing project-memory pattern:
  - routine markers: `_processed.json` in analyzer run dirs (server-side workflow);
  - tracking log: `research/run_log.csv`.
- Keep research methodology stable across cycles unless task explicitly changes methodology.

### C) Runtime / ops-sensitive tasks
- Treat exchange/runtime assumptions conservatively:
  - exchange state is source of truth,
  - restart flows must reconcile state, not resume blindly,
  - invariants are detectors; non-deterministic mismatch => halt + alert, not silent auto-fix.
- Do not change deployment/runtime behavior (Docker/server/startup/run scripts) unless explicitly requested and justified by evidence.
- For server-path procedures, keep `/opt/aitrader` instructions aligned with existing docs; mark anything unverified.

## 5) Safety and evidence rules
- Inspect repository evidence first; do not invent architecture, status, or missing components.
- When status is uncertain, label it `needs verification`.
- Prefer explicit invariants/contracts over implicit assumptions.
- Preserve append-only/audit-oriented artifacts where documented (manifests, ledgers, run logs, registry outputs).


## 6) Task execution discipline

## 6.1) Approval and Command Batching

For routine repository operations, minimize approval noise and batch obvious command sequences whenever the environment requires escalation.

- If the user explicitly asks to run tests, merge, pull, fetch, commit, or push, do not ask separate conversational permission questions for each sub-step.
- Prefer one grouped approval/tool request for the whole obvious sequence (`git status` + `git fetch` + `git merge` + `git push`, or `pytest` run + result capture).
- Do not generate extra commentary about sandbox/escalation mechanics unless the command actually fails or the user asks why.
- This rule also applies when executing repository prompts such as `prompts/weekly_research.txt`: batch the expected SSH/git/test/file-update actions as tightly as the environment allows.
- If escalation is required by the tool, request it once in the most compact form possible and proceed.

This rule is about reducing interaction noise, not about skipping safety for destructive actions.
For every task:
1. Read relevant sources of truth first.
2. State assumptions and uncertainty explicitly.
3. Apply the smallest change set that solves the task.
4. Preserve existing contracts/invariants and compatibility with tests.
5. Summarize: what changed, what did not, and what still needs verification.

## 7) Key files and directories to inspect first
- `README.md`
- `research/OPS.md`
- `docs/Spec_v1.0.md`
- `docs/Backtesting_Spec_v0.1.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/Analyzer_Run_Storage_v0.1.md` (storage contract is design-oriented; verify against runtime before enforcing as fact)
- `research/README.md`, `research/run_log.csv`, `research/findings/`, `research/results/`
- `analyzer/`, `backtester/`, `tests/`, `scripts/run_analyzer_daily.sh`

## 8) Open items / needs verification
- **DeltaScout responsibilities:** no concrete `deltascout` module/docs found in this repo; treat as `needs verification` until a canonical source is provided.
- **Doc-state conflict:** `CLAUDE.md` contains historical phase/status statements that may lag current README/backtester docs; verify before using it as primary status authority.
