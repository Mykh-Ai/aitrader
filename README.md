# AiTrader — BTC research/backtesting stack (execution-first target)

AiTrader is a **research + deterministic backtesting system** for BTC market-structure setups (currently focused on failed-break reclaim family), with a **planned** production execution layer for Binance Spot.

Current strengths in this repository:
- minute-level BTCUSDT collection and raw feed persistence,
- Analyzer pipeline for deterministic research artifacts,
- Backtester baseline for ruleset formalization, replay, validation/robustness/promotion,
- campaign and experiment registry baseline for multi-run observational tracking.

It is **not** a live execution bot yet. Executor concerns (exchange order lifecycle, reconciliation/state recovery, runtime invariants) remain a planned boundary.

## 1) Project overview

- **What AiTrader currently is:** Collector + Analyzer + Backtester research runtime with deterministic artifact contracts.
- **What it is strongest at now:** reproducible historical processing (raw feed → analyzer artifacts → replay/evaluation artifacts).
- **What is still planned:** production execution runtime (Binance Spot integration, order state lifecycle, exchange reconciliation controls).

## 2) Current system state (implemented vs planned)

| Layer | Status | Notes |
|---|---|---|
| Collector / Aggregator | ✅ Implemented | `binance_aggregator_shi.py` builds BTCUSDT 1m futures-derived raw feed |
| Analyzer | ✅ Implemented | Facts engine + setup research pipeline; deterministic CSV artifacts |
| Backtester | ✅ Implemented (baseline) | Ruleset formalization, placement baseline, replay, ledger, metrics, validation, robustness, promotion, orchestration |
| Campaign / Registry (Phase 5 baseline) | ✅ Implemented (baseline) | Multi-run campaign artifacts + append-only experiment registry |
| Research Operations | ✅ Implemented | Automated routine cycle (`research_cycle.py`), weekly agent/architect workflow, verdict persistence |
| Executor | 🔜 Planned | Live exchange runtime is not implemented in this repository |

## 3) System architecture (participants/layers)

```text
Binance market data (WS/REST)
        │
Collector / Aggregator
        │  raw daily CSV feed
        ▼
Analyzer
        │  analyzer artifacts (features/events/setups/outcomes/reports/shortlist/...)
        ▼
Backtester
  - rulesets / ruleset_validation / placement / engine / ledger
  - metrics / validation / robustness / promotion / orchestrator
        │
        ├─ per-run artifacts (manifests, trades, metrics, validation, promotion)
        └─ campaign + experiment_registry (multi-run observational tracking)

Research Operations (research_cycle.py)
  - automated probe → replay → record → slice → diagnostics
  - optional local-only ops workflow can consume cycle output and write local research notes

Executor (planned; separate boundary)
```

Phase naming still exists in docs/specs, but this README is organized by **current module/layer boundaries first**.

## 4) Responsibility boundaries

### Collector / Aggregator
**Does:** collect minute-level market data and persist raw feed CSV by UTC day.

**Does not:** generate setups/rankings, run replay logic, or place orders.

### Analyzer
**Does:** transform raw feed into deterministic research artifacts (features/events/setups/outcomes/reports/rankings/selections/shortlist/research summary).

**Does not:** perform exchange execution, authorize live deployment, or run order lifecycle management.

### Backtester
**Does:** consume Analyzer artifacts and perform deterministic historical replay/evaluation with validation gates and campaign baseline outputs.

**Does not:** call `analyzer.pipeline.run()` implicitly, execute live exchange trades, or replace execution-time reconciliation controls.

### Executor (planned)
Target boundary for production order lifecycle, restart reconciliation with exchange as source of truth, runtime invariants, and fail-loud controls.

## 5) Current repo module map

```text
/ (repo root)
├── binance_aggregator_shi.py
├── analyzer/
│   ├── schema.py
│   ├── loader.py
│   ├── base_metrics.py
│   ├── swings.py
│   ├── sweeps.py
│   ├── failed_breaks.py
│   ├── absorption.py
│   ├── events.py
│   ├── setups.py
│   ├── outcomes.py
│   ├── reports.py
│   ├── context_reports.py
│   ├── rankings.py
│   ├── selections.py
│   ├── shortlists.py
│   ├── shortlist_explanations.py
│   ├── research_summary.py
│   ├── context.py
│   ├── thresholds.py
│   ├── harvest.py
│   ├── io.py
│   ├── pipeline.py
│   └── run_daily.py
├── backtester/
│   ├── rulesets.py
│   ├── ruleset_validation.py
│   ├── placement.py
│   ├── engine.py
│   ├── ledger.py
│   ├── metrics.py
│   ├── validation.py
│   ├── robustness.py
│   ├── promotion.py
│   ├── orchestrator.py
│   ├── campaign.py
│   └── experiment_registry.py
├── research_cycle.py              — automated routine pipeline (runs on server)
├── prompts/
│   ├── weekly_research.example.txt — public-safe local prompt placeholder
│   └── Shi_research.example.txt    — public-safe local prompt placeholder
├── research/
│   ├── OPS.example.md             — public-safe local ops template
│   ├── run_log.csv                — processing history
│   ├── slice_analysis_reclaim_context.py
│   ├── findings/                  — frozen research memos
│   ├── results/                   — slice analysis snapshots
│   ├── verdicts/                  — local-only research verdict area
│   └── handoff/                   — private runbook area (not in git)
├── scripts/run_analyzer_daily.example.sh
├── docs/
│   ├── Spec_v1.0.md
│   ├── Phase2_Implementation_Plan_AiTrader_v2_2_updated.md
│   ├── Backtesting_Architecture_v0.1.md
│   └── Backtesting_Spec_v0.1.md
└── tests/
```

### Backtester baseline modules (what they do)

- `rulesets.py` — formalizes replayable rulesets from analyzer shortlist/research outputs.
- `ruleset_validation.py` — strict Phase 4 pre-replay validation for mapping artifacts.
- `placement.py` — owned deterministic v1 SL/TP placement materialization before replay.
- `engine.py` — deterministic multi-bar replay lifecycle and engine event stream.
- `ledger.py` — trade ledger generation from replay outputs.
- `metrics.py` — metrics/equity/drawdown/exit summaries.
- `validation.py` — baseline validation decisions from replay results.
- `robustness.py` — baseline robustness checks.
- `promotion.py` — baseline research progression decisions.
- `orchestrator.py` — end-to-end single-run orchestration and artifact writing.
- `campaign.py` — multi-run campaign execution and campaign-level summaries/index/manifest.
- `experiment_registry.py` — append-only registry records (`phase5_experiment_registry.csv`).

### Analyzer module architecture (practical map)

**Facts engine (Phase 1 scope):** `schema.py`, `loader.py`, `base_metrics.py`, `swings.py`, `sweeps.py`, `failed_breaks.py`, `absorption.py`, `events.py`.

**Research pipeline (Phase 2 scope):** `setups.py`, `outcomes.py`, `reports.py`, `context_reports.py`, `rankings.py`, `selections.py`, `shortlists.py`, `shortlist_explanations.py`, `research_summary.py`.

**Infrastructure/runtime:** `io.py`, `pipeline.py`, `run_daily.py`, plus context/threshold support modules.

## 6) Artifact flow (maintainer-level)

1. **Analyzer artifacts (single analyzer run)**
   - Input: raw feed CSV (`feed/YYYY-MM-DD.csv` or explicit path).
   - Key outputs: `analyzer_features.csv`, `analyzer_events.csv`, `analyzer_setups.csv`, `analyzer_setup_shortlist.csv`, `analyzer_research_summary.csv`, `analyzer_day_regime_report.csv` (+ full intermediate report stack).
   - Frozen-run mode writes run directory with `run_manifest.json`.

2. **Backtest artifacts (single backtester run)**
   - Input: analyzer artifact dir.
   - Raw lineage resolution for replay: explicit `raw_path` → `run_manifest.json` input paths → compatibility fallback `artifact_dir/raw.csv`.
   - Key outputs: `backtest_rulesets.csv`, `backtest_engine_events.csv`, `backtest_trades.csv`, `backtest_trade_metrics.csv`, `backtest_orchestration_manifest.json`.
   - For `N > 1` replayable rulesets, replay fans out into `N` isolated child runs; each child remains a normal replay-completed unit with its own one-row canonical ruleset input.
   - The parent fan-out manifest is lineage/orchestration-only: it is not a merged replay result, does not aggregate siblings, and does not auto-promote any child.
   - If a later child fails after earlier children completed, completed child artifacts remain valid; the parent manifest records partial failure explicitly and campaign outputs may retain completed child rows while also recording the failed parent execution.

3. **Phase 4 validation artifacts**
   - `phase4_ruleset_validation_summary.csv`
   - `phase4_ruleset_validation_details.csv`

4. **Validation / robustness / promotion artifacts**
   - `backtest_validation_summary.csv`, `backtest_validation_details.csv`
   - `backtest_robustness_summary.csv`, `backtest_robustness_details.csv`
   - `backtest_promotion_decisions.csv`, `backtest_promotion_details.csv`

5. **Campaign / registry artifacts (Phase 5 baseline)**
   - `backtest_campaign_manifest.json`
   - `backtest_campaign_run_index.csv`
   - `backtest_campaign_summary.csv`
   - registry row append to `phase5_experiment_registry.csv`

## 7) Collector section (operational details preserved)

### Raw feed schema (1m candles)

| Column | Source | Description |
|---|---|---|
| Timestamp | system | UTC close label written at flush time by `binance_aggregator_shi.py`; Analyzer normalizes it to candle-open `Timestamp` |
| Open, High, Low, Close | aggTrade WS | OHLC prices |
| Volume | aggTrade WS | Total traded volume |
| AggTrades | aggTrade WS | Count of Binance aggTrade messages (not individual fills) |
| BuyQty | aggTrade WS | Taker buy volume |
| SellQty | aggTrade WS | Taker sell volume |
| VWAP | aggTrade WS | 1m VWAP (`sum(price*qty)/sum(qty)`) |
| OpenInterest | REST `/fapi/v1/openInterest` | OI snapshot |
| FundingRate | markPrice WS | Funding rate snapshot |
| LiqBuyQty | forceOrder WS | Short liquidation volume |
| LiqSellQty | forceOrder WS | Long liquidation volume |
| IsSynthetic | system | `1` for synthetic no-trade interval candle |

### Data notes

- **Feed time contract:** `FEED_TIMEZONE = UTC`, `FEED_TIMESTAMP_LABEL = CLOSE` for the current `binance_aggregator_shi.py` feed. The raw label is preserved by Analyzer as `FeedTimestampUTC`; Analyzer derives `CandleOpenTsUTC = FeedTimestampUTC - 1 minute` and uses that as canonical `Timestamp`.
- **AggTrades** counts aggTrade messages, not full exchange fill count.
- **BuyQty / SellQty** are taker-aggressor volumes useful for delta/CVD context; interpret together with price response.
- **Synthetic candles (`IsSynthetic=1`)** keep continuity when interval has no trades; VWAP falls back to Close.
- **Liquidation data** comes from `forceOrder` stream and should be treated as contextual observed events.

### Storage pattern

- Raw feed files: `feed/YYYY-MM-DD.csv` (UTC-day partitioning).
- Because the current feed is close-labeled, a full raw file normally has labels `00:00..23:59`, but the first label represents the prior minute interval after normalization.
- Runtime directories are deployment-specific and should be kept in local server context rather than hard-coded in the public repo.

### Sources

**WebSocket streams**
- `btcusdt@aggTrade`
- `btcusdt@forceOrder`
- `btcusdt@markPrice@1s`

**REST endpoint**
- `GET /fapi/v1/openInterest?symbol=BTCUSDT` (minute snapshot)

### Collector running instructions

```bash
docker compose up -d --build
```

Local dev:

```bash
python binance_aggregator_shi.py
```

### Collector stale-feed recovery

The collector treats Binance WebSocket market-data freshness separately from
the socket connection flag. A stale feed is visible as repeated rows with
`IsSynthetic=1`, `Volume=0`, and a constant `Close` for many minutes.

Operational inspection on the current server deployment:

```bash
docker logs --tail 200 shi-aggregator
tail -20 /opt/aitrader/feed/YYYY-MM-DD.csv
```

Manual recovery:

```bash
docker restart shi-aggregator
```

Runtime archives cannot reconstruct every enriched field after a collector
outage. Open interest, funding, and liquidation quantities may be missing or
only partially recoverable historically.

## 8) Analyzer section (operational details preserved)

### Scope

Analyzer is the research layer that converts raw feed into deterministic artifacts for downstream review/backtesting. It does **not** execute on exchange.

### Data lineage

```text
raw CSV → features → events → setups → outcomes
        → report/context_report → rankings → selections
        → shortlist → shortlist_explanations → research_summary
```

### Direct pipeline usage

```python
from analyzer.pipeline import run

result = run("feed/2024-03-15.csv", output_dir="output/")
# key files written under output/: analyzer_features.csv, analyzer_events.csv,
# analyzer_setups.csv, analyzer_setup_outcomes.csv, analyzer_setup_report.csv,
# analyzer_setup_context_report.csv, analyzer_setup_rankings.csv,
# analyzer_setup_selections.csv, analyzer_setup_shortlist.csv,
# analyzer_setup_shortlist_explanations.csv, analyzer_research_summary.csv, analyzer_day_regime_report.csv
```

### Failed-break reclaim research variants

The default Analyzer pipeline remains `FAILED_BREAK_RECLAIM_MICRO_V1`:
`confirmation_bars=5`, `setup_ttl_bars=12`, `outcome_horizon_bars=12`, with the
existing artifact filenames and schemas.

An explicit research-only sidecar is available as `FAILED_BREAK_RECLAIM_EXTENDED_V1`:
`confirmation_bars=60`, `setup_ttl_bars=12`, and
`outcome_horizons=(60, 240, 1440, 4320, 10080)`. It writes only namespaced sidecar
artifacts and is not consumed by baseline rankings, selections, shortlist,
research summary, or Backtester.

```python
from analyzer.research_variants import run_research_variants

run_research_variants("feed/2024-03-15.csv", output_dir="output/")
# writes output/research_variants/FAILED_BREAK_RECLAIM_EXTENDED_V1/analyzer_setup_outcomes_by_horizon.csv
```

### Daily-run operational mode

Recommended current baseline: run Analyzer once per day after UTC rollover on the previous UTC-day feed file.

Example:

```bash
python -m analyzer.run_daily feed/2026-03-13.csv --runs-root analyzer_runs
```

For deployment scheduling, keep any host-specific wrapper in local-only ops materials. The public repo ships only a safe example wrapper.

### Structural safety notes (kept practical)

- Structural swing detection excludes synthetic rows from structure-defining logic.
- H1/H4 completeness thresholds protect against sparse bucket contamination.
- H4 structure uses normalized UTC candle-open bars (`H4_BARS_UTC`) with fixed bucket boundaries `00:00 / 04:00 / 08:00 / 12:00 / 16:00 / 20:00 UTC`; do not use a UTC+2 variant unless another verified feed/postprocessor actually shifts timestamps.
- Stateful logic resets on large timestamp gaps (`MAX_STATE_GAP_MINUTES`) as fail-closed safety.

Normative analyzer contract: `docs/Spec_v1.0.md`.

## 9) Backtester section

### Current baseline scope

Backtester consumes pre-generated analyzer artifacts and runs deterministic replay + evaluation. This includes ruleset formalization, optional strict Phase 4 mapping validation, deterministic v1 placement materialization, replay engine, ledger, metrics, validation/robustness/promotion, and orchestration artifacts.

### Boundary contract

- Backtester **consumes analyzer artifacts**.
- Backtester **does not call analyzer implicitly** and is not an execution runtime.
- Campaign/registry outputs are observational research tracking, not live execution authorization.

### Phase 4 gate and v1 placement notes

- `PHASE3_MAPPING_ONLY` mode includes strict pre-replay validation gate with explicit summary/details artifacts.
- SL/TP placement is currently deterministic **v1 baseline** (`placement.py`) and should not be treated as full execution-grade order lifecycle handling.
- Stop placement models are explicit research/backtest controls:
  - `REFERENCE_LEVEL_HARD_STOP` is the existing baseline and uses setup `ReferenceLevel`.
  - `SWEEP_EXTREME_HARD_STOP` is a failed-break/reclaim alternative: LONG uses the sweep candle low, SHORT uses the sweep candle high. Missing sweep extremes fail explicitly instead of falling back to `ReferenceLevel`.
  Both are replay models, not live-ready execution order logic.

### Phase 3 replay cardinality baseline

- Shortlist-based formalization may yield `0..N` canonical replayable rulesets for one analyzer artifact.
- `0` replayable rulesets is a fail-loud pre-placement stop, not a silent collapse into a no-op replay.
- `1` replayable ruleset preserves the existing single-run baseline.
- `N > 1` replayable rulesets fan out into `N` derived isolated replay runs; each derived run receives a one-row canonical `backtest_rulesets.csv`, so the placement exact-one-ruleset contract remains unchanged per run.
- The parent run scope records orchestration/lineage only; replay-completed units are the derived child runs. Campaign/registry outputs append one fact row per completed derived run, with no aggregation, best-of selection, or auto-promotion.

## 10) Operational usage

### Collector

```bash
docker compose up -d --build
```

### Analyzer

```bash
python -m analyzer.run_daily feed/<YYYY-MM-DD>.csv --runs-root analyzer_runs
```

### Routine research cycle (automated)

Weekly cycle is automated via `research_cycle.py`:

```bash
# Full routine: probe → replay → record → slice → diagnostics
python3 research_cycle.py

# Dry run (probe + diagnostics only, no replay)
python3 research_cycle.py --dry-run
```

The script outputs structured JSON. Local teams may optionally feed that output into local-only ops materials for note-taking or review workflow.

See `research/README.md` for the public research workflow boundary. Private runbooks should stay in the local-only ops area.

### Practical manual probe before Backtester

For ad-hoc exploration outside the routine cycle, use your local environment or local server context.

Choose the exact Analyzer run directory. Keep dates in `YYYY-MM-DD` format and the run directory in `YYYY-MM-DD_to_YYYY-MM-DD_run_001` format.

**Template**

```text
analyzer_runs/YYYY-MM-DD_to_YYYY-MM-DD_run_001
```

**Example**

```text
analyzer_runs/2026-03-14_to_2026-03-14_run_001
```

Inspect the shortlist artifact first.

**Template**

```bash
python - <<'PY'
import pandas as pd
run_dir = "analyzer_runs/YYYY-MM-DD_to_YYYY-MM-DD_run_001"
df = pd.read_csv(f"{run_dir}/analyzer_setup_shortlist.csv")
print(df.head(20).to_string(index=False))
PY
```

**Example**

```bash
python - <<'PY'
import pandas as pd
run_dir = "analyzer_runs/2026-03-14_to_2026-03-14_run_001"
df = pd.read_csv(f"{run_dir}/analyzer_setup_shortlist.csv")
print(df.head(20).to_string(index=False))
PY
```

Inspect the research summary artifact next.

**Template**

```bash
python - <<'PY'
import pandas as pd
run_dir = "analyzer_runs/YYYY-MM-DD_to_YYYY-MM-DD_run_001"
df = pd.read_csv(f"{run_dir}/analyzer_research_summary.csv")
print(df.head(30).to_string(index=False))
PY
```

Inspect only formalizable rows before starting Backtester.

**Template**

```bash
python - <<'PY'
import pandas as pd
run_dir = "analyzer_runs/YYYY-MM-DD_to_YYYY-MM-DD_run_001"
df = pd.read_csv(f"{run_dir}/analyzer_research_summary.csv")
formalizable = df[df["FormalizationEligible"] == True]
print(formalizable.to_string(index=False))
print(f"\nFormalizationEligible rows: {len(formalizable)}")
PY
```

Practical interpretation:

- `FormalizationEligible == 0` rows after the filter means Backtester will stop before placement.
- `FormalizationEligible > 0` means replayable canonical rulesets may exist and Backtester can be run.

Run Backtester only after the probe above.

**Template**

```bash
python - <<'PY'
from backtester.orchestrator import run_backtester

run_backtester(
    artifact_dir="analyzer_runs/YYYY-MM-DD_to_YYYY-MM-DD_run_001",
    output_dir="backtests/smoke_YYYYMMDD_manual",
    ruleset_source_formalization_mode="SHORTLIST_FIRST",
    variant_names=("BASE",),
    cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
    same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
    replay_semantics_version="REPLAY_V0_1",
    expiry_model="BARS_AFTER_ACTIVATION:12",
)
PY
```

**Example**

```bash
python - <<'PY'
from backtester.orchestrator import run_backtester

run_backtester(
    artifact_dir="analyzer_runs/2026-03-14_to_2026-03-14_run_001",
    output_dir="backtests/smoke_20260314_manual",
    ruleset_source_formalization_mode="SHORTLIST_FIRST",
    variant_names=("BASE",),
    cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
    same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
    replay_semantics_version="REPLAY_V0_1",
    expiry_model="BARS_AFTER_ACTIVATION:12",
)
PY
```

Read promotion output first after the run finishes. For fan-out runs, inspect each `derived_run_*` child separately.

**Template**

```bash
python - <<'PY'
from pathlib import Path
import pandas as pd

out_dir = Path("backtests/smoke_YYYYMMDD_manual")
for child in sorted(out_dir.glob("derived_run_*")):
    print(f"\n== {child.name} ==")
    print(pd.read_csv(child / "backtest_rulesets.csv").to_string(index=False))
    print(pd.read_csv(child / "backtest_promotion_decisions.csv").to_string(index=False))
PY
```

Very short interpretation:

- Start with each child `derived_run_*` directory, not the parent shell, as the first post-run summary surface.
- Read `backtest_rulesets.csv` together with `backtest_promotion_decisions.csv` before deeper artifact inspection.

### Backtester (single run)

```python
from backtester.orchestrator import run_backtester

run_backtester(
    artifact_dir="analyzer_runs/<run_id>",
    output_dir="backtests/<bt_run_id>",
    ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
    variant_names=("BASE",),
    cost_model_id="DEFAULT_COST_V1",
    same_bar_policy_id="DEFAULT_SAME_BAR_V1",
    replay_semantics_version="REPLAY_V0_1",
    expiry_model="BARS_AFTER_ACTIVATION:12",
)
```

Replay expiry is explicit and research-only. `BARS_AFTER_ACTIVATION:12` is the current MICRO baseline and remains the default. Structural failed-break/reclaim research can opt into `BARS_AFTER_ACTIVATION:60`, `:240`, `:1440`, `:4320`, or `:10080` without changing entry logic, TP logic, stop-model defaults, or Analyzer artifacts. These are deterministic backtest holding horizons, not live-ready execution rules.

### Campaign baseline

```python
from backtester.campaign import run_backtest_campaign

run_backtest_campaign(
    artifact_dirs=["analyzer_runs/<run_id_1>", "analyzer_runs/<run_id_2>"],
    output_dir="backtests/campaigns/<campaign_id>",
    campaign_label="baseline",
    ruleset_source_formalization_mode="PHASE3_MAPPING_ONLY",
    variant_names=("BASE",),
    cost_model_id="DEFAULT_COST_V1",
    same_bar_policy_id="DEFAULT_SAME_BAR_V1",
    replay_semantics_version="REPLAY_V0_1",
)
```

### Binance Futures WebSocket routing

The SHI feed collector uses Binance USD-M Futures market streams via `wss://fstream.binance.com/market/stream?streams=`. Binance decommissioned unrouted legacy Futures stream paths for market/private channels after 2026-04-23; using `wss://fstream.binance.com/stream?streams=` can complete the WebSocket handshake but not push `aggTrade`, `forceOrder`, or `markPrice` payloads.

### Environment quick reference

| Variable | Default | Description |
|---|---|---|
| `FEED_DIR` | `./feed` | Collector CSV directory |
| `LOGS_DIR` | `./logs` | Collector log directory |
| `WS_STALE_AGG_TRADE_SECONDS` | `180` | Watchdog threshold for missing aggTrade messages while WS is connected |
| `WS_STALE_MARK_PRICE_SECONDS` | `180` | Watchdog threshold for missing markPrice messages while WS is connected |
| `WS_WATCHDOG_INTERVAL_SECONDS` | `30` | Collector stale-WS watchdog check interval |
| `MAX_CONSECUTIVE_SYNTHETIC_CANDLES` | `5` | Maximum flat synthetic candle writes before skipping until real aggTrade data resumes |

## 11) Known current limitations

- Several Backtester components are baseline-policy level (validation thresholds, robustness surfaces, promotion semantics).
- SL/TP placement is deterministic v1 baseline and not execution-grade order lifecycle logic.
- Analyzer + Backtester are research/progression layers; they do not replace exchange-execution safeguards.
- Executor/live exchange integration is planned and not implemented in this repository.

## 12) Source-of-truth docs

When wording differs, prefer current runtime/code behavior and these aligned docs:
- `docs/Spec_v1.0.md`
- `docs/Phase2_Implementation_Plan_AiTrader_v2_2_updated.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/Backtesting_Spec_v0.1.md`

---

## Infrastructure / health quick reference (operational note)

- Deployment layout and runtime naming are environment-specific.
- Keep hostnames, container names, absolute paths, and operator procedures in local-only ops materials.

Example health log format:

```text
💓 Health: WS=OK connected=True | aggTradeAge=0s | markPriceAge=1s | wsMsgAge=0s | consecutive_synthetic=0 | real_trade_count_current_minute=18 | last_real_trade_price=70400.5 | mark_price=70400.4 | watchdog_reconnects=0 | OI=83287 | FR=0.000027 | Candles=120/1440
```

## Target architecture constraints (execution layer, planned)

These are design constraints for planned execution runtime, not currently implemented runtime behavior.

- Regulatory context: futures market data can be used for research; execution target is Binance Spot (margin constraints per deployment policy).
- Risk constraints (design target): fixed per-trade risk, isolated-margin discipline, explicit drawdown halts.
- Scope constraints: BTC-first execution scope; no hidden auto-risk escalation.
