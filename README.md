# AiTrader

Publication40N: the user explicitly requested publishing the research to`main`. Read [40N publication/reproduction notes](research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md) with the40M roadmap. The preserved research snapshot is commit`0862342`; current main also retains the existing [production-continuity ADR](docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md). Historical replay uses the frozen snapshot and raw inputs, not rehashed current runtime code.

AiTrader is a BTCUSDT research system that has gone through three major eras:

1. data collection and Analyzer v1 setup research;
2. Backtester/replay infrastructure for those early setup artifacts;
3. a reset into BTC Market Monitor research after Analyzer v1 failed as a strategy architecture.

The current project is not starting from zero. The feed, aggregator, tests, audit discipline, and several low-level primitives survived the reset. What changed is the research object: the project is no longer trying to promote shallow false-break/reclaim rows. It is trying to build a market-state model first, then define candidate contracts only after state, liquidity, sweep/reclaim sequence quality, and data lineage are clear.

## Current State

User-directed40P has acquired the older Binance BTCUSDT USD-M1m source:2025-03-01–2026-03-09 plus February2025 warm-up.23official checksums pass;578880right-close minute rows/402daily files,zero missing/duplicate minutes,18official nontraded rows retained. Raw ZIPs and normalized data are retained in a separate local research cache with exact hashed transfer references. Read [40P data acquisition audit](research/canonical/SHI_RESET_40P_BINANCE_FUTURES_HISTORY_ACQUISITION_AUDIT_2026_10_15.md). This later user instruction authorizes data download only;40O source parity remains failed and no OOS signals/trades/returns were inspected.

40O source-validation gate failed before historical OOS:official BTCUSDT USD-M1m archives reproduce99.865591% of July decisions and100% of September, with one extra allowed long onJuly5 08:00UTC. Required100% parity is unmet. All27checksums/frozen40H identities pass; original13-row40H control reproduces;784tests and real-prefix checks pass. Older data was undownloaded when40O stopped; subsequent40P supplies it without inspecting strategy outcomes. No strategy tuning or production advancement. Read [40O canonical audit](research/canonical/SHI_RESET_40O_BINANCE_FUTURES_ARCHIVE_OOS_VALIDATION_AUDIT_2026_10_15.md) and [result](market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/result.md) before continuing the40M deployment roadmap. Source semantics require resolution first; live remains blocked.

Canonical own-signal research and deployment handoff: [40M roadmap](research/canonical/SHI_RESET_40M_RESEARCH_AND_DEPLOYMENT_ROADMAP_AUDIT_2026_10_15.md). It records the40A–40L decisions and results, exact selected40H entry/SL/TP/book rules, latest40L journal, rejected alternatives, reproducibility commands, working-tree/ignored-artifact transfer inventory with SHA256, and staged server/API work with acceptance criteria. This is documentation, not deployment or production promotion. Start here when preparing the next server-integration task.

Current active stage: post-39A Market Monitor promotion and validation.

User-directed40L completed the full chronological40H continuation through October14 23:59UTC:14closed trades/8wins/6losses, **+1060.91USDC** after5USDC/trade and2bps/fill slippage, before actual borrowing. All13 original trades remain unchanged; October adds one long stopped for−29.90USDC, no13/14entries, no open/data-censored positions. April–September remains12/+1142.11; closed-trade drawdown74.61. Only October admission/data coverage and a declared last-H1 precise-entry cutoff adapter changed; selected trading thresholds/exits remain40H.15tests/all14independent paths/real-prefix/source checks pass. Read `research/canonical/SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md` and `market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/result.md`. Latest replay journal is indexed in`research/latest_own_signal_replay.json`; the frozen chosen-rule pointer stays unchanged. This retrospective extension is not pristine holdout or production promotion.

Data refresh40K supplies complete futures October13/14 and matching official BTCUSDC spot data; October15partial is excluded. All old source/artifact identities remain intact. Read `research/canonical/SHI_RESET_40K_DATA_REFRESH_AUDIT_2026_10_15.md`;40L uses its separate spot extension and preserves frozen40B/40G/40H inputs/results.

User selection2026-10-15:the main own-signal research candidate is frozen40H, both delta screens together:rolling24h futures delta in(-4%,+4%) for either side, plus rolling4h delta>0 for long, inheriting all40H baseline entry/short-space1R/execution/exit rules.40I frequency additions remain unselected alternatives. Read `research/canonical/OWN_SIGNAL_RESEARCH_SELECTION_2026_10_15.md` and `research/active_own_signal_selection.json`. This selects the next research-confirmation contract, not production/live policy.

User-directed40J tested the strict short4h-delta<0 mirror on that selected40H. It removes the June1winning short387.18USDC, saves no losses and admits no new trades. Full net1090.81→703.63; April–September1142.11→754.92; DD74.61 unchanged. Thus the extra short4h rule is not selected; the40H pointer is unchanged. Read `market_monitor_runs/SHI_RESET_40J_short_delta4_mirror_v0/result.md`;13tests,25independent paths and real-prefix checks pass. This is sample-specific research, not universal evidence against symmetry.

The 40B preparation inventories local SHI history through `2026-10-12T23:59:00Z`; its last complete UTC H1 closes at 23:00, and October 13 and later files are outside the frozen interval. Selected source hashes and explicit gap/degradation evidence are frozen under the 40B run root. Read-only v39A snapshots, including the latest September 29 snapshot, remain indexed in `PROJECT_LOG.md`; they do not establish continuous runtime state or trading edge.

Latest canonical source of truth: `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`.

The 2026-10-13 own-signal preflight found that the saved 38V/38W1 cohort is unsuitable for causal financial validation: 49/51 rows consume daily state ending after the recorded setup time, targets come from one full-period zone selection, and 26/51 saved targets are directionally invalid at replay entry. See `research/canonical/SHI_RESET_40A_OWN_SIGNAL_CAUSALITY_PREFLIGHT_AUDIT_2026_10_13.md`. Historical reaction counts remain forensic evidence. The next research prerequisite is causal own-feed signal generation before cost-aware family replay; no profitable family is established.

40B prepares an executable bounded experiment in `research/own_signal_run/`: three new causal own-feed hypotheses, one frozen structural exit/48-hour expiry policy, three assumed cost scenarios, source/code hashes and a startup continuity diagnostic. See `research/canonical/SHI_RESET_40B_OWN_SIGNAL_RUN_PREPARATION_AUDIT_2026_10_13.md` and the package README. The user-authorized 40C full chronology and financial proxy replay completed on October 14 with the active v1 rules. This research package does not promote production setup policy or legacy Backtester gates.

The user-directed 40B1 correction is active in `contract_v1.json` and `market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/`: isolated missing/synthetic minutes are skipped without a 24-hour quarantine, technical reset or trade interruption. Actual timestamps and omission provenance are retained, and the next real candle is used. Multi-day outage/recovery handling remains separate. See `research/canonical/SHI_RESET_40B1_SINGLE_MINUTE_TOLERANCE_AUDIT_2026_10_13.md`; v0 results remain historical evidence.

40B1 verification completed on October 14: 752 regression tests passed; same-cutoff startup causality/continuity checks passed. The subsequent 40C run processed 5,170 H1 steps, generated 63 gate-passing signals and resolved 21 trades. Demand sweep/reclaim: 20 trades, +4.38R gross, -2.41R assumed base net, -10.12R stress. Seller retest: one trade, -2.03R base; supply sweep/reclaim: no trades. No net-profitable family is established. Source/code identity, clocks, carried state and independent cost arithmetic passed; three trades continued across isolated synthetic minutes. See `research/canonical/SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0/`. The next research step is to diagnose cost-to-risk and short-context restrictions before freezing any changed hypothesis. Later positive periods have only seven demand trades and are not pristine holdout evidence.

The user then authorized iterative strategy search with $3,000 position notional, $5 total commission per completed trade and a minimum $500 historical net benchmark. 40D found and reproduced a directional hybrid: LONG trend retests and SHORT accepted support breaks, one global position. Full history: 26 trades, +$673.55 gross, $130 commission, $31.28 adverse slippage, **+$512.28 model net**. April-September entries: 23 trades, **+$579.02**. Average initial stop risk is $48.78, not a fixed dollar R. All selected outcomes are observed; no conservative data-gap mark contributes. Independent money/clock/path checks and 762 tests passed. Read `research/strategy_search/README.md` and `market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/result.md`. This is a historically selected candidate after extensive search; small-sample concentration, unmodeled borrow interest and BTCUSDT proxy prices prevent an edge/live claim. Fixed-rule confirmation is the next step; production policy and Backtester gates remain unchanged.

The 39A review is complete. A bounded stateful snapshot contract was promoted on 2026-09-11 for descriptive Executor LLM entry evidence; the remaining lifecycle and setup-quality backlog is not promoted.

40E answers the user's follow-up about the 16 stops and target asymmetry. Eight stops are long, eight short; median time to stop is 6.96 versus 57.14 hours. No long stop reached 1R, while three short stops did and none reached 2R. Early frozen-EMA failure is present in six/eight long stops versus one/six other long outcomes; nearby causal H4 support is present in six/eight short stops versus one/four other short outcomes. The target-only 20-pair sensitivity reproduces 6R short / 10R long as the strongest complete result in that grid, not a proven optimum or live-practice rule. The 40D baseline is unchanged; these descriptive hypotheses require separate causal portfolio tests. See `market_monitor_runs/SHI_RESET_40E_hybrid_stop_diagnosis_v0/diagnosis_summary.md` and its canonical audit.

40F extends that diagnosis with all six expiry cases and 16 declared portfolio interventions. Long-only gives +$387.17; removing short changes admission and adds a losing long. The strongest complete result in this bounded study blocks short when a known opposing H4 reference is less than 1R from the decision close: 21 trades, +$671.05 net, eight positive/13 negative, $224.01 closed-trade drawdown; April-September entries +$839.79. This reduces losses but does not increase the absolute number of wins. All six seven-day closures are reviewed: five positive/one negative, +$433.10. The new variant and dollar journal are frozen in `market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/`; 20 targeted tests, prefix causality, unchanged-engine reproduction and independent first touches passed. Baseline 40D remains preserved; the new filter is historically selected research, with subsequent confirmation and long-entry improvement still outstanding.

The user-directed 40F1 checks short protection after 2R instead of 1R, keeping the protective stop at +0.25R. Original strategy net is +$408.15, versus +$512.28 without protection; the short-space candidate remains +$671.05 because its actual exits do not change. All six controls are observed; two focused tests and independent first-trigger/terminal checks pass. See `market_monitor_runs/SHI_RESET_40F1_short_protection_2R_v0/result.md`. No new variant replaces 40F.

40G applies the user's execution-market clarification: futures BTCUSDT generates signals; BTCUSDC Spot supplies entry/exit prices for the Spot Margin price model. All previous40C–40F1 numbers remain futures-price proxies. Imported/downloaded48 official BTCUSDC archives pass checksums; source data and Executor remain unchanged. The primary two-feed replay has21 observed trades, eight positive/13 negative, **+676.37 USDC** after5-USDC commission per completed trade and2-bps-per-fill slippage; April–September19 entries **+845.02 USDC**. Closed-trade drawdown223.92 USDC. Reference conversion uses only already closed same-clock quotes. Actual borrowing and orderbook execution are unverified. Thirteen declared H4/management/control variants,22 tests and258 independent path checks do not support adding the proposed H4 long gates or profit-management changes. Read `market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/result.md` and its frozen spot contract. Subsequent fixed-rule confirmation remains open.

40H answers the user's losing-trade/24h-delta/time-window follow-up using all21 spot baseline trades and52 original candidate decisions. Twenty-two declared full-book replays identify a research successor: both directions require weighted rolling24h delta strictly between−4% and+4%, long additionally requires rolling4h delta>0. Result13 observed trades,8positive/5negative, **+1090.81USDC** after the unchanged fee/slippage model; April–September12entries/+1142.11. All8 baseline winners are retained;9 losses are blocked, but a new July22long loses39.51 and is included. Closed-trade drawdown74.61; without bestthree+250.79. Time/OI gates lose profitable trades; no calendar exclusion is selected. Read `market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/result.md` and its frozen research contract. Sixteen tests,345 independent paths and real-prefix invariance pass. These filters are adaptive on exposed history, not holdout/production evidence; actual borrowing remains unverified.40G is preserved as control, and subsequent fixed-rule confirmation is still pending.

Current facts:

40I addresses the user's request for more trades through entry/filter expansion. Three bounded adaptive batches(74+48+8=130portfolios) preserve40H as control and freeze a moderate frequency alternative:old core plus first closed48h range breaks, short-space0.75R, extra-event delta-band6%, volume1.3 and directional H1delta4%; original stops/targets/168h/costs unchanged. April–September16trades/10wins/6losses/+1150.20USDC versus40H12/8/4/+1142.11; closed-trade drawdown rises74.61→125.27. Full history18/11wins/7losses/+1156.80USDC. All8 baseline winners retained; six new entries net33.37 and one old loss32.63 displaced by book occupancy. Double-frequency24trades yields only692.85USDC with398.35DD; no doubled-frequency strong success. Read `market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/result.md` and frozen frequency alternative contract/journal.17tests,2450portfolio rows/59unique first-touch paths and all130stream prefix checks pass. This remains exposed-history research before actual borrowing; subsequent fixed-rule confirmation and production authority are unchanged.

- The latest full-feed discovery pass in the historical 38-chain is 38S redo, reviewed by 38T and 38U, then crosschecked against setup_builder in 38V. The separate 40C own-feed research contract now has causal full-history signals and a negative cost-aware financial proxy result.
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
