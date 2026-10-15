# SHI_RESET_40Q_FROZEN_ARCHIVE_REPLAY_V0

Execution date: 2026-10-15. Starting commit: `0268331c839c2936165edb5fd59c4154c1e7498c`. Dedicated branch: `codex/SHI_RESET_40Q_frozen_archive_replay_v0`.

**Research decision: the older interval rejects the current frozen candidate on this source.** March 1 2025–March 9 2026 has 35 completed trades, 7 wins/28 losses, gross −$59.26 and **net −$276.19**, PF 0.806. The extended full-period gain **+$701.26** includes already-known 2026 history and does not establish older-history robustness. No strategy repair is performed inside this task.

## User scope and preserved source failure

After being explicitly told that source parity remained failed and no backtest had run, the user instructed “Ну шо, запускай.” The subsequent instruction expanded the archive replay through **2026-10-14** and requested comparison of months covered by the SHI feed. This is a new authorized source-specific research diagnostic. It does not create a fictitious 40O acceptance, rewrite its verdict, or authorize production. The original 40O `BINANCE_KLINE_SURROGATE_PARITY_FAILED` and its NOT_RUN artifacts remain immutable.

Run root: [SHI_RESET_40Q_frozen_archive_replay_v0](../../market_monitor_runs/SHI_RESET_40Q_frozen_archive_replay_v0/). The [run manifest](../../market_monitor_runs/SHI_RESET_40Q_frozen_archive_replay_v0/run_manifest.json) was frozen before financial results and declares one unchanged 40H strategy, no optimization, no threshold search, one execution of three specified source-comparison books, and no selection between their outcomes.

## Frozen strategy and technical adapters

Selected version: `SHI_RESET_40H_DELTA_FILTER_RESEARCH_V1`; variant: `LONG_DELTA4_POS_BOTH_BAND4`. Rules SHA256: `ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4`. Filter manifest SHA256: `32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56`.

Execution imports byte-verified historical modules from the 0862342 reconstruction previously prepared by 40O, not the current modified runtime. Every executed frozen module and each new research tool has a recorded SHA256. The original 13-row 40H spot-control journal is reproduced with unchanged cash and clocks before archive returns are read.

The only signal adapter removes the three absolute SHI preparation-calendar statements from the frozen `signals` function. Its full remaining AST, including every formula, period, volume/flow threshold and prior-history requirement, is unchanged. Continuous archive admission begins March 1 2025; the matched source books separately apply the original 40L calendar, verified against its immutable helper. No date is chosen from financial outcomes. The rejected SHORT delta4 mirror is not added.

The precise entry adapter keeps the original entry observation/time/open and extends the previously declared 40L final-H1 admission. It supplies entry-minute-only auxiliary OHLC instead of reading unused future first-hour extrema; precise `trade_path` does not consume those auxiliary values. The original 13 control trades and entry tuples reproduce. Stops, 10R LONG / 6R SHORT targets, 168h expiry, risk bounds and intraminute exit policy are unchanged.

## Sources, clocks and history

Official Binance BTCUSDT USD-M Perpetual Futures **1-minute klines**, 65 unique ZIPs with official CHECKSUM verification. Reused unchanged: 22 of the 40P archives and 27 from 40O. Downloaded under 40Q: January 2025 monthly for technical history, March 10 2026 daily, October 1–14 2026 daily. The 40P January 31 boundary archive is unnecessary once full January history is supplied and is not double-counted.

January technical warm-up was declared before outcomes: frozen H4 references may remain in inventory for 30 days plus delayed confirmation, while February 2025 has only 28 days. Full source normalization starts **2025-01-01 00:01 UTC**, first complete H1 at 01:00. Entry admission stays **2025-03-01 00:00 UTC**. The original older evaluation boundary **2026-03-09 23:59 UTC** is retained as a separate earlier-cutoff ledger with later exits and amounts masked; the user-requested extended primary end is **2026-10-14 23:59 UTC**. No post-end expiry tail or forced close is invented.

Normalized data: **938,879 unique chronological minutes / 652 daily files**, no missing or duplicate timestamp labels. 37 official nontraded rows are retained and marked: January 14 2025 (2), January 29 (17), August 29 (18). The January rows are warm-up only. Nontraded rows are skipped under frozen observation semantics, with actual UTC gaps retained; extended gaps remain subject to the unchanged CENSOR policy. No quality exception is fitted to an outcome.

Timing remains exchange-open +60s → SHI-style right-close label, with raw exchange clocks preserved. OHLC rounds to 2 decimals, base quantities to 6. BuyQty is taker-buy base volume; SellQty is raw total minus raw buy, then rounded. Binance component-trade counts are not claimed equal to SHI callback counts. OI/funding/liquidations are not required and unavailable placeholders are never new filters. The original ZIPs and normalized data are retained in local research caches, with exact paths/URLs/hashes pinned for transfer; bulk caches are not Git-tracked.

## Three predeclared books, one strategy

1. **CONTINUOUS_BINANCE**, the primary result: full causal archive history from January, entries March 2025–October 14 2026, date-neutral admission, one uninterrupted book.
2. **MATCHED_BINANCE**: history starts at the same 2026-03-11 13:45 UTC as SHI, with the unchanged 40L admission calendar; Binance signal source.
3. **MATCHED_SHI**: identical history start and 40L calendar; original protected/recovered SHI signal source, selected read-only with its preserved lineage.

Both matched books use the **same Binance futures minute execution prices**, so their difference compares signal sources. Each cohort begins flat by declaration and carries state/book continuously inside its own interval; the matched diagnostic is not presented as uninterrupted discovery from January. Original published 40L BTCUSDC spot-price cash is listed separately for context, with its different execution market explicit. No aggregate merges these independent books into performance.

All three books use **FUTURES_PRICE_PROXY**, 3,000 dollar-equivalent notional, 5 per completed trade, 2bps adverse slippage per fill, one-minute latency, global one-position book, three-minute cooldown, stop-first collisions and the original 168h fixed exit rules. No funding or actual borrowing charge is introduced. This is not exact spot-margin PnL or executable account evidence.

## Causality and predeclared interpretation

Before financial replay, full features, H4 inventory hashes, raw candidates, gates, blocker reasons and decision-close stops are compared against real source prefixes at June 30 2025 12:30 UTC and July 15 2026 12:30 UTC. Rolling windows are `(decision−hours, decision]`; H4 references must be available by the decision. Exact raw candidate agreement with the original 40L helper is required for each matched source. Every entered trade receives an independent vector first-event, stop/target/risk, book/cooldown and dollar-accounting check.

Financial criteria are predeclared: at least 12 completed trades, net >0, PF >=1.25, net excluding the best two >0, no causality/hash failure or data-censored trade. Passing these gives only `ARCHIVE_REPLAY_FINANCIAL_CRITERIA_MET_SOURCE_UNVALIDATED`. Fewer than 12 gives insufficient sample; sufficient sample failing financial criteria rejects the current candidate **on this source**; data-censored rows give incomplete evidence. These outcomes cannot accept the failed original source-parity gate or promote server/live trading. No rule repair or second candidate is permitted after the first result.

## Results and verification

Financial result and monthly source-comparison artifacts are written only after the above preflight passes. The final evidence is indexed in `result.md`, `oos_metrics.json`, `oos_trades.csv`, `oos_monthly_summary.csv`, `monthly_source_comparison.csv`, `causality_checks.json`, `independent_path_checks.json` and the source/code manifests in the run root.

|Independent evidence cohort|Completed|Wins/losses|Net after costs|PF|Closed-trade DD|
|---|---:|---:|---:|---:|---:|
|Older archive: March1 2025–March9 2026|35|7/28|−$276.19|0.806|$662.77|
|Continuous archive: March1 2025–October14 2026|52|15/37|+$701.26|1.393|$662.77|
|Matched Binance signals / common futures prices|14|8/6|+$1102.42|5.658|$102.35|
|Matched SHI signals / common futures prices|14|8/6|+$1058.30|4.769|$74.66|

These cohorts are not added together. The primary continuous book has 197 raw candidates, 73 gate-passing candidates, 42 LONG and 10 SHORT entries, 36 stops/6targets/10expiries, zero open/data-censored rows. Gross $1023.63 less $260 commission and $62.38 slippage gives $701.26. Average trade $13.49, median −$32.93, mean initial risk $44.54 (1.485%), mean net outcome 0.5003R. LONG net +$191.36 / SHORT +$509.90. Best1/2/3 contributions $387.83/$684.27/$972.50; corresponding net excluding them +$313.43/+$16.98/−$271.24. The narrowly positive result without the best two is recorded without rounding it into robust evidence.

Older-only evidence: 125 raw/47 gate-passing candidates, 29 LONG/6SHORT entries; LONG net −$362.51 / SHORT +$86.32. Fees $175, slippage $41.94. Net excluding best1/2/3 is −$572.64/−$860.87/−$1090.66. All 35 paths are completed within the original cutoff; no later exit or known-period return is credited. Verdict: `ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE`. The full 52-trade source-specific financial criteria narrowly pass, producing `ARCHIVE_REPLAY_FINANCIAL_CRITERIA_MET_SOURCE_UNVALIDATED`, but that descriptive classification does not replace the failed older result or source gate.

All 20 months are retained in [compact monthly tables](../../market_monitor_runs/SHI_RESET_40Q_frozen_archive_replay_v0/monthly_comparison.md). Calendar2025 entries net −$267.03; calendar2026 entries +$968.29. These yearly entry cohorts describe the full book; the original older interval instead ends March9 and has −$276.19. No profitable months are selected or loss months omitted.

Matched source results differ in two executed entries: SHI admits May22 20:00short, losing $74.66; Binance H4 inventory blocks it. Binance admits July5 08:00long, losing $30.54; SHI produces no candidate. June17 12:00has an extra Binance raw short rejected by H4. Across5218H1 states, three raw/final mismatches give99.9425067%combined decision agreement, two final-direction mismatches. Among61union raw candidates,58match=95.0819672%. Each source has22gate-passing and14entered trades, despite different rows. Counts/financial closeness therefore do not restore100%source parity. Matched net difference +$44.12 follows the two observed loss differences; no filter is retuned from this observation.

Original40L spot-price result remains14/+1060.907640USDC; matchedSHI/common-futures result is14/+1058.299936. They use different execution prices and are explicitly separated. The two matched books isolate the signal-source comparison by sharing the same futures execution prices. The primary continuous archive includes clean-source dates outside the SHI preparation calendar, while both matched books preserve those original40L admissions; its2026monthly cash therefore need not equal the matched Binance cash.

Real-prefix checks pass at4332closedH1steps (June2025) and13452steps (July2026), including features/H4hashes/candidates/gates/stops. Independent first-event/cash/risk/book checks pass for52+14+14=80entered paths. All65official checksums/652normalized hashes/oldO/P/source/pointer identities pass. The auxiliary40Lcalendar helper and40Oarchive normalizer are additionally verified against expected hashes that preexist in40O's frozen manifest and40Q's pre-result context plan. Core code/hashes remain unchanged after the first financial outcome.

27 targeted research tests and 798 full regression tests pass, with 11 existing warnings. A preparatory fixture initially triggered its accepted-break event before the required prior-history window; the fixture was corrected before manifest freeze and replay. Existing tests and strategy code were not weakened. No protected feeds/aggregator, existing 40D/H/L/O/P evidence, selection pointers, Executor or live services are modified. No push or merge to main is authorized by this task.

**Phase decision:** server shadow is not justified by this diagnostic after the older-history rejection and unresolved source equivalence; live trading remains blocked. Exact BTCUSDC historical replay is not the next priority for advancing this candidate. Any later changed hypothesis requires a separately declared research task; this now-seen history cannot be relabeled pristine holdout. This task ends with the frozen negative older result preserved.
