# AiTrader

AiTrader is a BTCUSDT research system that has gone through three major eras:

1. data collection and Analyzer v1 setup research;
2. Backtester/replay infrastructure for those early setup artifacts;
3. a reset into BTC Market Monitor research after Analyzer v1 failed as a strategy architecture.

The current project is not starting from zero. The feed, aggregator, tests, audit discipline, and several low-level primitives survived the reset. What changed is the research object: the project is no longer trying to promote shallow false-break/reclaim rows. It is trying to build a market-state model first, then define candidate contracts only after state, liquidity, sweep/reclaim sequence quality, and data lineage are clear.

## Current State

Current active stage: post-39A Market Monitor promotion and validation.

Latest canonical source of truth: `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`.

The 39A review is complete. A bounded stateful snapshot contract was promoted on 2026-09-11 for descriptive Executor LLM entry evidence; the remaining lifecycle and setup-quality backlog is not promoted.

Current facts:

- The latest full-feed discovery pass is 38S redo, reviewed by 38T and 38U, then crosschecked against setup_builder in 38V.
- 38S redo processed `2026-03-11T13:45:00Z -> 2026-06-28T23:59:00Z` in live-like form and carried state forward across technical chunks.
- 38S generated 227 setup/context rows and 140 policy-allowed research candidates.
- 38T found this is overgenerated discovery material, not validated edge.
- 38T identified 8 specimen-like primary setup ids and 17 data-quality review candidates touching recovered degraded periods.
- 38U reviewed only those 8 specimen-like primary candidates: 1 strong canonical match, 6 partial matches, and 1 numeric-only lookalike.
- 38V generated 51 canonical setup_builder context rows and matched only 10 of the 227 38S rows by its crosscheck categories; 38S remains discovery material, not a source-candidate stream.
- 38W1 corrected replay chronology to 34 valid TP1-before-stop reactions and 17 stop-before-TP1 rows. This is replay evidence, not edge proof.
- setup_builder remains a context candidate generator, not a final setup engine.
- Sweep must be treated as a sequence/lifecycle event before new setup logic is added.
- Chat/manual conclusions are preserved in 39A separately from code-confirmed and run-artifact-confirmed facts.
- One research specimen is confirmed: the 2026-05-26 sequence-linked H1 sweep/reclaim candidate packaged in 38R and corrected in 38Q.
- The v39A snapshot is active as descriptive entry-time evidence in Executor; it is not a setup, order, or position-management policy.
- Backtester is a future validation gate after the candidate contract is tightened; it is not the current authority for 38S/38T/38U rows.

## Current Architecture Map

The current intended architecture is:

`Aggregator / feed -> Market Monitor base layer -> structure levels -> liquidity zones -> zone registry / carry-forward -> event log / post-sweep observation -> significant zone selector -> hidden flow research -> market structure state -> setup_builder -> qualified H1 sweep/reclaim sequence check -> stage-gate replay -> policy replay review -> QC / evidence packs -> future Backtester -> future Executor`

Current reusable work includes the Market Monitor research chain and the bounded v39A entry snapshot. Backtester validation and any Executor trading-policy authority remain future gates.

## 38S 227 Rows: What They Are And What They Are Not

38S generated 227 discovery rows with:

`market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/_build_full_feed_live_like_setup_discovery.py`

Those rows are important research material, but they are not canonical setup_builder candidates.

What 38S rows are:

- full-feed live-like discovery/context rows;
- generated from feed-derived H1 swing references and qualified H1 sweep/reclaim events;
- raw material for QC and evidence review;
- proof that the current permissive discovery runner can reproduce the 2026-05-26 specimen.

What 38S rows are not:

- not produced by old Analyzer v1;
- not produced by canonical `setup_builder.py` as the candidate source;
- not validated Market Monitor candidates;
- not Backtester-ready;
- not strategy candidates;
- not Executor/live candidates.

38S transformed every qualified H1 failed-reclaim context into an `ARMED` review row. That is why all 227 rows were ARMED and why 140 became policy-allowed under the current sequence gate. This is overgenerated discovery material. 38T and 38U reviewed the rows after generation; they were not pre-generation monitor filters.

Historical next step 38V was completed as a run artifact. Its result is incorporated into 39A: the 38S discovery stream is not the canonical setup_builder candidate source.

## What The Project Is Trying To Build

The goal is a research path that can eventually support:

`market state -> qualified candidate contract -> audited Backtester validation -> Executor integration`

The current Market Monitor work focuses on the first two pieces:

- market state from complete prior context, not isolated feed slices;
- liquidity zones and structural levels;
- completed H1 sweep evidence;
- completed H1 failed reclaim evidence;
- sequence role and timing;
- stop-anchor validity;
- R-profile and quality-control filters;
- explicit data-lineage caveats.

A valid future candidate should come from market state and sequence evidence. It should not come from a raw label, arbitrary 12-bar outcome, or a setup row that only looks good in a local window.

## Project Evolution From First Commit

### 1. Feed And Aggregator Foundation

The project began with a Binance BTCUSDT aggregator and feed handling:

- `3f9219e Phase 1: Binance BTCUSDT aggregator`
- `1908ef8 Fix empty candle flush and move OI polling to daemon thread`

This remains one of the durable assets. Current feed/data-lineage rules are documented in `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`.

### 2. Analyzer v1 Phase 1: Primitive Market Features

Analyzer v1 then built feed loading, base metrics, swing detection, sweep detection, failed-break detection, event normalization, and absorption/context features. The key early implementation commits include Phase 1A/1C/1D work such as:

- `c6b96fb Analyzer Phase 1A cleanup: strict IsSynthetic and feature contracts`
- `e4c3552 Fix swing confirmation timing to post-close availability`
- `efb98c3 Implement phase 1C sweep detection with anti-lookahead tests`
- `9ca9235 Implement Phase 1D failed-break detection with deterministic tests`
- `52ff959 Add deterministic absorption context features and tests`

What survived: schema discipline, anti-lookahead mindset, timestamp contracts, and some low-level primitives.

What failed later: these primitives were promoted toward setup logic before a real market-state model existed.

### 3. Analyzer v1 Phase 2: Research Artifacts And Shortlists

Phase 2 added setup extraction, enrichment, lifecycle annotations, outcomes, rankings, selections, shortlist exports, explanations, and research summaries.

Representative commits:

- `0e233f3 Add baseline failed-break setup extraction and pipeline output`
- `72f60cd Add strict setup enrichment snapshots from feature rows`
- `93180bc Add research lifecycle annotations to setup candidates`
- `a916a2e Add research-only setup outcomes layer`
- `2e5d131 Enforce fail-loud rankings in pipeline`
- `1f92822 Add research selection layer and pipeline output`
- `fdee2af Add deterministic shortlist export layer and pipeline artifact`
- `d9b3946 Add final Phase 2 research summary layer`

This era produced strong artifact discipline but weak research object quality. It could rank and explain rows, but those rows were still rooted in shallow failed-break/reclaim definitions.

### 4. Backtester Phase 3/4/5: Replay Infrastructure

The project then built a Backtester baseline: rulesets, engine replay, ledger materialization, metrics, statistical validation, robustness, promotion decisions, campaign orchestration, deterministic exit resolution, and placement contracts.

Representative commits:

- `a80e755 Harden ruleset formalization source/mapping contracts`
- `d9b8339 Fix Step 2A engine replay contract blockers`
- `95fe1d6 Add deterministic backtest trade ledger materialization`
- `2e0ab88 Add deterministic backtester metrics artifacts layer`
- `9f0a526 Add phase 3 step 4 statistical validation module`
- `ae4ad02 Implement Phase 3 Step 5 robustness artifacts and tests`
- `2fd7cea Add phase 3 step 6 promotion decision layer`
- `d780beb Add Phase 4 (Ruleset Validation) and Phase 5 (Experiment Registry) to plan`
- `2ed6107 Harden replay close resolution for stop/target/expiry`
- `4f25799 Add deterministic pre-engine SL/TP materialization layer`

This matters for the future: the Backtester may be reusable as a validation harness. But the old candidate source was not good enough, so Backtester evidence could not rescue Analyzer v1.

### 5. Research Operations, H2, And Sprint 02-10

After the first Analyzer/Backtester build, the project ran research operations, H2 impulse/reclaim investigations, weekly cycles, recovered-feed work, and Sprint 02-10 candidate/replay/holdout work.

Representative commits:

- `67f3819 research: add reclaim context asymmetry finding + reproducible analysis artifacts`
- `5ac0cd6 research: add research_cycle.py automation + update agent prompt`
- `dae7b63 Add H2 impulse feature detector and pipeline integration`
- `6040e5b Add H2 observational outcome labels for impulse reclaim setups`
- `cc1e668 Normalize close-labeled feed timestamps to candle-open UTC`
- `3086f8f Sprint 02 recovered validation and canonical state`
- `23d1cc3 Sprint 03 formal candidate rulesets and holdout protocol`
- `887e212 Start holdout tracking after Sprint 03 freeze`
- `9ad4e53 Sprint 10 true holdout for BTC replay survivors`

This era produced useful negative evidence. The conclusion was that the branch had audit machinery, but the research object was still wrong.

### 6. Reset: Analyzer v1 Failed As Strategy Architecture

The reset happened here:

- `928bcc6 Archive failed Analyzer v1 research branch and define market state monitor`
- `d7de18a Reset active tree after failed Analyzer v1 branch`
- `e955d77 Clean active docs after Analyzer v1 reset`
- `7611712 Clean active docs after Analyzer v1 reset`
- `2c3f40d Clean governance after Analyzer v1 reset`

Canonical verdicts:

- `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
- `research/canonical/SHI_RESET_2026_05_ANALYZER_V1_VERDICT.md`
- `research/canonical/ARCHIVE_MANIFEST_FAILED_ANALYZER_V1.csv`

The key conclusion: false break/reclaim was not rejected as a market idea, but Analyzer v1's implementation was rejected. It did not model real liquidity sweeps, accumulation/distribution, market state, volume/delta/OI/funding/liquidation context, or professional state transitions before promoting candidates.

### 7. Market Monitor Reset Track: SHI_RESET_01-38U

After reset, Market Monitor rebuilt the research stack around state and liquidity:

- skeleton and feed adapter;
- structure and liquidity zones;
- zone registry and carry-forward;
- lifecycle event log;
- unresolved sweep candidates;
- post-sweep observation;
- batch research runner;
- confidence scoring and zone precision patches;
- strict event grouping;
- sweep label taxonomy and label quality;
- visible liquidity structure monitor;
- M15 first-class structure registry;
- significant zone selector and trader snapshot;
- hidden-flow research;
- market-structure state memory;
- live replay setup timeline;
- setup replay validation and manual review;
- qualified H1 sweep/reclaim sequence detection;
- stage-gated policy review;
- full-feed live-like discovery QC;
- specimen-like candidate evidence review.

Important commits include:

- `542ff83 Add market monitor sprint 1 skeleton`
- `3f390fe Improve market monitor structure and liquidity zones`
- `2166eef Add liquidity zone registry carry-forward`
- `3c0c80f Populate market monitor lifecycle event log`
- `e02ce23 Add unresolved liquidity sweep candidates`
- `a4f31d9 Add post-sweep observation window`
- `dbfe8ab Add market monitor batch research runner`
- `80a933c Implement sweep label taxonomy v1`
- `cde8213 Add label quality report`
- `406e017 Complete SHI_RESET_32 visible liquidity structure monitor`
- `8e80d63 Add SHI_RESET_33 M15 first-class structure registry`
- `39f698f Add SHI_RESET_36B significant zone selector v0`
- `c087007 Add SHI_RESET_36C trader snapshot builder v0`
- `f66be3f Add SHI_RESET_37A hidden flow research detector v0`
- `5a7f862 Add SHI_RESET_37D episode context classifier`
- `4c9038d Add SHI_RESET_37E market structure state memory`
- `1d868e8 Implement live replay setup timeline builder`
- `785aa1e Add sequence-window H1 reclaim replay`
- `31ba79f Add stage gate replay and fix sequence stop anchoring`
- `c06ad73 Record full feed live-like discovery scan`
- `434f10f Record full feed discovery quality control audit`

## Current Research Chain

The active chain is:

`full feed -> state carry-forward -> structure/liquidity registry -> setup_builder -> qualified H1 sweep -> qualified H1 failed reclaim -> sequence-linked setup review -> stop anchor validation -> policy replay review -> QC/evidence review`

The important current semantic rules are:

- `RAW_SWEEP` is observation/context only.
- `QUALIFIED_H1_SWEEP` needs completed H1 evidence at a meaningful level.
- `QUALIFIED_H1_FAILED_RECLAIM` needs a completed H1 close back through that level.
- `entry_candidate_ts` is reclaim/rejection close time.
- `setup_formed_at` is review time.
- Stops inside the sweep range are invalid for sequence-linked H1 sweep/reclaim candidates.

## Current Evidence And Logs

Use `PROJECT_LOG.md` as the compact index of recent research tasks and output folders.

Detailed canonical audit summaries are in:

`research/canonical/`

Generated run outputs are in:

`market_monitor_runs/`

The current 38U output root is:

`market_monitor_runs/SHI_RESET_38U_specimen_like_candidate_evidence_review_v0/`

## Next Direction

Review the 39A master audit, control-case ledger, research-to-code decision matrix, terminology contract, and documented promotion backlog.

No implementation candidate is approved by documentation alone. After review, select one narrow promotion task. The intended order starts with a unified level lifecycle and a next-1-3-H1 sweep sequence classifier, then addresses counter-sweep invalidation, accepted break versus reclaim, structural blockers/targets, prior-move maturity, meaningful structural risk, and local-sequence direction precedence.

Backtester and Executor remain inactive future gates. Nothing in 39A proves edge or live readiness.

## Useful Commands

Canonical local test command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

PowerShell form:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -q
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
```

Current targeted 38-chain tests:

```bash
python -m pytest -q tests/test_stage_gate_replay.py tests/test_policy_replay_fixed_stops.py tests/test_qualified_h1_sweep_reclaim.py tests/test_sequence_window_h1_replay.py
```
