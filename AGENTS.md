# AGENTS.md

## Purpose

Publication40N records the user's explicit request to push this research to`main`. Read `research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md` for commit`0862342` offline reproduction and byte-preserving transfer. The existing production-continuity package/ADR is preserved on main. Publishing here does not alter the retired-main research-base policy or authorize live promotion; future work still follows the task's explicitly selected base and scope.

This file tells a new agent how to work in this repository. It is not the project history and it is not the research log. For the project story and current state, read `README.md`. For commit/task summaries and links to evidence folders, read `PROJECT_LOG.md`.

Current work is BTC Market Monitor research after the Analyzer v1 reset. The 39A master research-to-monitor alignment audit remains the canonical architecture source. Its review is complete, and the bounded v39A snapshot contract was promoted on 2026-09-11 for descriptive Executor LLM entry evidence. Remaining lifecycle promotions still require separate scope and evidence.

## Autonomy And Permissions

Do not ask the user for routine permission when the action is normal project work:

- reading files;
- searching the repository;
- inspecting git history and diffs;
- running local tests or lint/check commands;
- creating or editing files directly related to the requested task;
- adding documentation entries, canonical audit notes, or run-output summaries for the current task;
- working around quoting/path/sandbox friction with an equivalent safe local command.

Ask before serious or potentially destructive actions:

- deleting files or directories;
- `git reset`, destructive checkout/restore, or discarding user changes;
- broad formatting or mass rewrites outside the task scope;
- modifying `feed/`, `feed_recovered/`, or other data-lineage assets;
- enabling Backtester as an active validation gate;
- adding Executor/live/order/position-sizing behavior;
- installing dependencies, using network, deploying, pushing, or touching remote systems;
- changing project governance in a way that promotes research outputs to edge/live/production status.

If a tool-level sandbox approval is required by the environment, request it only when the action is actually necessary. Do not use approval prompts as a substitute for normal repository work.

## Start Every Task Here

40Q is the later user-authorized source-specific replay after the explicit failed-parity warning, extended throughOctober14 with matched SHI-month comparisons. Read `research/canonical/SHI_RESET_40Q_FROZEN_ARCHIVE_REPLAY_AUDIT_2026_10_15.md`:olderMarch2025–March9 2026rejects frozen40H on this source,35/−276.19/PF0.806. Full52/+701.26includes known2026and must not mask that failure. Matched Binance/SHI common-futures-price books14/+1102.42and14/+1058.30still differ in decisions; original40O source gate remains failed. No optimization after this first result;798tests/80paths/real prefixes pass. All now-used history is exposed. No server/live/spot-replay advancement is justified; preserve old40O/40P artifacts and selected pointers unchanged.

40P is the preceding user-authorized historical data download, not a parity waiver. Read `research/canonical/SHI_RESET_40P_BINANCE_FUTURES_HISTORY_ACQUISITION_AUDIT_2026_10_15.md`:23official BTCUSDT futures archives supply2025-03-01–2026-03-09 plus Februarywarmup,578880rows/402daily files,checksums/grid verified. Bulk data remain in the local40Pcache; committed manifests pin URLs/hashes for transfer/reproduction. No strategy outcomes were inspected by40P itself; the later40Q diagnostic records them separately. Keep the completed40O artifacts immutable.

40O is inserted before server shadow/production/API integration. Read `research/canonical/SHI_RESET_40O_BINANCE_FUTURES_ARCHIVE_OOS_VALIDATION_AUDIT_2026_10_15.md`:strict official-kline source parity failed onJuly5 08:00UTC (one extra allowed long), despite frozen40H control/27checksums/prefix checks passing. Verdict`BINANCE_KLINE_SURROGATE_PARITY_FAILED`; older data was undownloaded at that task's stop;40Pwas data-only and later40Qexposes outcomes in a separate authorized diagnostic. Do not proceed to OOS or shadow by bypassing the gate, retune40H, discard bad SHI history, fit timestamp offsets or treat this as a measured OOS loss. Preserve the failure; any next source-semantics investigation requires its own declared scope. Existing40H/L pointers/rules/results stay immutable.784regression tests pass; no live promotion is implied.

Before changing anything, read in this order:

1. `README.md`
2. `PROJECT_LOG.md`
3. `docs/ACTIVE_DOCS.md`
4. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
5. the canonical audit for the task you are continuing

Canonical audits live in:

`research/canonical/`

Generated run outputs live in:

`market_monitor_runs/`

Current audit:

`research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`

Current companion artifacts:

- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

For own-signal continuation/server handoff, read `research/canonical/SHI_RESET_40M_RESEARCH_AND_DEPLOYMENT_ROADMAP_AUDIT_2026_10_15.md`. It consolidates40A–40L evidence, exact selected40H rules/latest40L results, rejected variants and proposed server/API milestones. Its40M run root contains a SHA256 transfer inventory and read-only `handoff.py verify`; current Git HEAD alone omits uncommitted research code and ignored run/data artifacts. Keep40H/L frozen pointers unchanged. The roadmap does not authorize network/deployment/orders or promote research-run scripts into production modules; existing permissions/scoping remain applicable.

## Live-Like Market Monitor Discipline

The Market Monitor must be treated as a stateful market reader, not as a tool that cuts a convenient window from the feed and pretends that window is the market.

For live-like research runs:

1. Process candles chronologically.
2. At each newly closed H1 candle, recompute or update the monitor using all feed history available up to that candle close.
3. Carry forward market state, structure levels, liquidity zones, qualified sweep/reclaim state, and setup review context from prior data.
4. Do not reset state between technical chunks unless the task is explicitly a reset/diagnostic task and the artifact names that reset clearly.
5. If chunking is needed for performance, write an audit field proving continuity, such as `market_state_reset=false`, `structure_levels_reset=false`, `liquidity_zones_reset=false`, `qualified_h1_state_reset=false`, and `setup_context_reset=false`.
6. Treat a narrow date window as a diagnostic replay only. A diagnostic window must not be presented as live-like discovery unless it reconstructs prior context from earlier feed data.

Market logic should model a live market as state that changes with each new closed candle and new trades. It should not infer setup quality from an isolated slice that lacks prior structure, liquidity, and state memory.

## Post-39A Architecture Rules

- Never treat `analyzer/` as an active source of current 38-chain candidates.
- Never say the 227 rows came from old Analyzer v1; they came from the 38S run script under `market_monitor_runs/`.
- Never treat the 38S 227 rows as the canonical candidate source. They remain discovery material even when a row matched the 38V crosscheck.
- Scripts under `market_monitor_runs/` are run artifacts, not reusable modules unless explicitly promoted into `market_monitor/` with tests and docs.
- Treat `setup_builder` as a context candidate generator, not a final setup engine.
- Treat a sweep as a sequence/lifecycle event, not one penetration candle or a generic quality label.
- Keep chat/manual conclusions separate from code-confirmed, run-artifact-confirmed, and canonical-doc-confirmed facts.
- Scope and validate every remaining 39A promotion separately; the completed snapshot promotion does not approve the remaining lifecycle backlog.
- Canonical live-like monitor work must process closed candles chronologically and carry market state forward.
- A valid future live monitor must update market state, structure levels, liquidity zones, hidden flow, setup context, and stage gates after each new closed candle.
- 38T and 38U are post-generation QC/evidence reviews, not pre-generation monitor filters.
- 38W1 is corrected replay evidence, not edge proof.
- The 40A preflight found 49/51 saved 38V rows backdate setup time before consumed daily state closes; full-period zone selection also lacks per-signal availability checks. Do not use the saved 51-row cohort for causal financial validation. Read `research/canonical/SHI_RESET_40A_OWN_SIGNAL_CAUSALITY_PREFLIGHT_AUDIT_2026_10_13.md` before continuing own-signal research.
- 40B preparation provides an isolated research experiment under `research/own_signal_run/`, not production setup/lifecycle promotion or activation of legacy Backtester gates. Before its later run, read the 40B canonical audit and package README; preserve frozen rules, source/code identity, close-label clocks, assumed-cost/proxy-market labels and prior-state continuity. Historical validation is not pristine holdout evidence.
- User-directed 40B1 policy: an isolated missing/synthetic primary minute must not quarantine entries for 24 hours, invalidate H1/H4 confirmation or interrupt an active research trade. Skip that observation, continue on the next real candle, preserve actual UTC time/state and record the omission. The active preparation is v1; extended gaps/recovered data remain separate. Read the 40B1 audit before continuing this experiment.
- 40C executed the frozen v1 chronology and financial proxy replay on 2026-10-14: 63 gate-passing signals, 21 resolved trades, no net-profitable family established. Demand has 20 trades and -2.41R base net; seller has one and -2.03R; supply has none. Read `research/canonical/SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md` before follow-up research. Preserve this negative baseline and its code/source identity; changed rules require a new declared experiment. The later positive demand samples are seven trades, previously researched, not edge or untouched holdout proof.
- 40D's user-authorized iterative search uses $3,000 notional and $5 total commission per completed trade. The selected directional hybrid in `research/strategy_search/` yields +$512.28 full-history model net (26 trades) and +$579.02 for April-September entries (23), including 2 bps adverse slippage per fill. Read `research/canonical/SHI_RESET_40D_OWN_SIGNAL_STRATEGY_SEARCH_AUDIT_2026_10_14.md` and the frozen `selected_strategy.json` before continuing. It is historically selected, not pristine holdout or validated edge; borrow interest and executable BTC/USDC are not modeled. No selected trade uses an inferred short-gap mark. Preserve all trials, source/code hashes and the one global book. The user prefers dollar results and does not want intermediate failed-run/audit dumps in chat; retain negative evidence internally.

## Run And Artifact Rules

The user-directed 40F1 tested short protection after2R with the same+0.25R stop; read `research/canonical/SHI_RESET_40F1_SHORT_PROTECTION_2R_AUDIT_2026_10_14.md` before repeating protection research. Original net falls to+$408.15; the filtered40F candidate remains+$671.05 with unchanged exits. All six portfolios are observed. Keep40F frozen; this sensitivity does not justify adding a new selected protection rule or relabeling exposed history as holdout.

40F continues the stop/short/expiry work in `research/canonical/SHI_RESET_40F_DIRECTION_EXPIRY_STOP_INTERVENTIONS_AUDIT_2026_10_14.md`. Its improved research variant screens short for 1R space to a known H4 reference, using the decision close, not future entry open. All 21 selected paths are observed: +$671.05 net /+$839.79 April-September. Loss count fell17->13 but wins9->8; do not claim more absolute winning trades. Read the frozen study and `selected_research_variant.json` before follow-ups, preserve baseline 40D and all censored variants, and do not promote this bounded H4 proxy as the canonical Monitor registry or untouched-data edge.

Before continuing the user's stop follow-up, read `research/canonical/SHI_RESET_40E_HYBRID_STOP_DIAGNOSIS_AUDIT_2026_10_14.md`. It diagnoses eight long/eight short losses and tests 20 target pairs without changing 40D. Early reference failure is post-entry evidence, not an admissible hindsight entry filter; the causal H4 inventory is a bounded diagnostic, not a promoted Monitor registry. Preserve profitable counterexamples, censored sensitivity rows and the frozen baseline when testing separate new rules. 6R/10R are historically selected fixed multiples; long 10R remains the sensitivity grid boundary, not a live-proven optimum.

For each new SHI_RESET research task:

1. Create a run root under `market_monitor_runs/<TASK_ID>_v0/` or a clearly versioned successor.
2. Write generated CSV/JSON/MD artifacts into that run root.
3. Write a canonical audit summary under `research/canonical/<TASK_ID>_AUDIT_<YYYY_MM_DD>.md`.
4. Add a short entry to `PROJECT_LOG.md` with the task id, commit hash if available, canonical audit path, run-output root, key result, verification, and next implication.
5. Keep `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, `docs/ACTIVE_DOCS.md`, and `NEXT_TASK_MARKET_MONITOR.md` aligned when the project state changes.

Do not bury negative evidence. If a run overgenerates, fails a gate, depends on degraded feed, or contradicts a prior assumption, record that directly in the audit and project log.

## Feed/Data Rules

40L completed the user-authorized40H chronological continuation throughOctober14 23:59UTC. Read `research/canonical/SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md` and use `research/latest_own_signal_replay.json` for the latest executed research journal/result.14closed trades/8wins/6losses/+1060.907640USDC, no open/data-censored positions; original13retained exactly, October adds one stopped long−29.904211. April–September12/+1142.108729 unchanged. Only October admission and the declared last-H1 precise-entry cutoff adapter differ; full40H trading thresholds/exits persist.15tests/14independent paths/real-prefix/all232source checks pass. Preserve the frozen chosen-rule pointer `research/active_own_signal_selection.json` byte-for-byte; latest replay evidence has a separate pointer. No new parameter search, actual-borrow evidence, pristine holdout or production/Backtester promotion is implied.

The user explicitly authorized40K refresh on2026-10-15. Local`feed/2026-10-13.csv` and`2026-10-14.csv` now contain1440server-matchedRAW minutes each; old480-rowOctober13partial preserved in40Krun. Latest complete primary cutoffOctober14 23:59UTC; October15partial excluded. Matching officialBTCUSDC spot extension lives only under`market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0/spot_BTCUSDC/`. Read `research/canonical/SHI_RESET_40K_DATA_REFRESH_AUDIT_2026_10_15.md` before extending replay. Existing230source/code/contract hashes remain unchanged; do not edit frozen40B/40H manifests to pretend they covered new data or new October entries. A separate declared extension must preserve chosen40H trading filters, reconstruct full prior state and distinguish still-open trades at cutoff.

Protected data-lineage assets:

- `binance_aggregator_shi.py`
- `feed/`
- `feed_recovered/`

Do not modify feed data or recovered feed data unless the user explicitly asks for a feed/data-lineage task.

Known outage/contamination window:

`2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`

Inside that window, use `feed_recovered/YYYY-MM-DD.csv` when available and mark affected conclusions as recovered/degraded. Do not copy recovered rows into `feed/` and do not hide the degraded provenance.

## Current Research Semantics

The user clarified the market contract in40G: BTCUSDT perpetual futures is the signal generator; BTCUSDC Spot is the execution-price source for Spot Margin research. All financial follow-ups must keep those feeds separate. Do not fill entries/exits from futures prices and call them spot returns. Convert structural price references using only quotes available at or before the decision; record the mapping and currency. Funding/OI/liquidations remain futures signal evidence, not spot execution prices or automatic spot financing charges. Actual BTC-borrow availability/rates and orderbook fills require their own evidence.

Read `research/canonical/SHI_RESET_40G_FUTURES_SIGNALS_SPOT_EXECUTION_AUDIT_2026_10_14.md` and the frozen `selected_spot_contract.json` under its run root before continuing. The21-trade spot price model gives+676.37 USDC /+845.02 April–September, after5-USDC round-trip fee and2bps slippage per fill, before actual borrow interest. Old40C–40F1 numbers remain futures-price proxy evidence. Preserve all48 spot archive hashes, original futures sources, asof quote clocks, isolated-minute policy and global book. Simple H4 long gates, half2R exits and H1 trailing were tested in40G and did not improve the primary spot contract; do not repeat or install them as proven fixes without a new declared hypothesis. No production/legacy Backtester gate was promoted.

Use current semantics carefully:

40J tested the user's strict short4h-delta<0 mirror; read `research/canonical/SHI_RESET_40J_SHORT_DELTA4_MIRROR_AUDIT_2026_10_15.md` before repeating it. It removes June1short+387.18USDC (delta4+0.040804%), saves no losing trade and admits no replacement. Full net703.63 versus40H1090.81; six-month754.92 versus1142.11. Do not install this extra rule as a proven symmetry fix or silently change `research/active_own_signal_selection.json`; selected40H remains long4h>0 with no extra short4h sign screen. Both rules use rolling closed raw windows, not a calendarH4 candle. Preserve this small exposed-sample failure and its scope.

User decision2026-10-15 selects frozen40H as the main own-signal research candidate. Read `research/canonical/OWN_SIGNAL_RESEARCH_SELECTION_2026_10_15.md` and `research/active_own_signal_selection.json` first when continuing confirmation. Keep BOTH delta conditions:24h strict(-4%,+4%) on both sides and4h>0 on long, with the entire40H baseline including short-space1R. The word "filter" in that decision does not mean deleting the inherited entry requirements or choosing the separately tested24h-only variant.40I breakouts/6% extra band/0.75R gate remain preserved but unselected. This is a research choice, not live/production promotion.

40I continues the user's frequency-expansion request. Read `research/canonical/SHI_RESET_40I_ENTRY_FREQUENCY_EXPANSION_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/frequency_alternative_contract.json` before continuing. Preserve40H as control and the moderate alternative separately:old core plus first closed48h breaks, short-space0.75R, new-event band6%/volume1.3/directional H1delta4%, inherited fixed exits/costs. April–September16trades/+1150.20USDC/DD125.27 versus12/+1142.11/DD74.61; full18/+1156.80. Do not equate the full gain65.99 with six-month gain8.10, hide new losses/displaced entries, or call it a successful24-trade doubling. All130adaptive trials remain exposed-history evidence; genuinely subsequent confirmation, actual borrowing and production promotion are still pending. Signal/family labels in final journal distinguish first-range-break entry from inherited exit configuration.

40H is the latest user-directed loss-metric/filter study. Before continuing it, read `research/canonical/SHI_RESET_40H_LOSS_METRICS_FILTER_STUDY_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/selected_research_contract.json`. The adaptive research successor uses rolling24h weighted futures delta strictly within(-4%,+4%) for both sides and rolling4h delta>0 for longs; keep inherited40F short-space gate and40G spot mapping/execution unchanged.13trades/8wins/5losses/+1090.81USDC full/+1142.11 April–September are exposed-history results, not pristine holdout or production promotion. All8 baseline winners remain;9 losses are blocked and one new loss is included. Preserve22-trial registry, source/code hashes,52-candidate availability clocks and full global-book replay. Do not present deleted-row sums as filtered portfolio results, label rolling4h as a calendarH4 candle, or install time/OI gates that lost winners as proven improvements. Subsequent fixed-rule confirmation and actual BTC borrowing remain open.

- `RAW_SWEEP` is observation/context only.
- `QUALIFIED_H1_SWEEP` requires completed H1 evidence and a meaningful H1/H4/structural level.
- `QUALIFIED_H1_FAILED_RECLAIM` requires a completed H1 close back through the swept level.
- `entry_candidate_ts` is the reclaim/rejection close timestamp.
- `setup_formed_at` is a setup review timestamp, not the entry timestamp.
- `policy_allowed` means a row passed the current research policy screen. It is not edge proof.
- `specimen_like` means similar to the current evidence specimen by QC criteria. It still requires review.

For sequence-linked H1 sweep/reclaim candidates:

- short stop anchor should be `sweep_h1_high_stop` unless a farther valid structural stop exists;
- long stop anchor should be `sweep_h1_low_stop` unless a farther valid structural stop exists;
- a structural stop inside the sweep range is invalid.

## Backtester And Executor Gates

Backtester and Executor are future gates, not current active layers.

The legacy `backtester/` package can become relevant again only after the current Market Monitor candidate contract is explicit enough to backtest. Do not run old Backtester campaigns against old Analyzer v1 survivors.

Executor integration requires a later explicit user-scoped phase after research and Backtester evidence. Do not add live/order/position-sizing behavior during Market Monitor research tasks.

## Tests

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

Current targeted tests for the 38M-38U chain:

```bash
python -m pytest -q tests/test_stage_gate_replay.py tests/test_policy_replay_fixed_stops.py tests/test_qualified_h1_sweep_reclaim.py tests/test_sequence_window_h1_replay.py
```

Passing tests proves executable contracts still run. It does not prove market edge.
