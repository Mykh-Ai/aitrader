# PROJECT_STATE_CURRENT

Last updated: 2026-05-16

## 1. Current Phase

Phase 2 / Phase 3 overlap: data accumulation, Analyzer runs, deterministic Backtester replay, candidate discovery, and statistical evidence building.

Phase 4 Bridge is not active as an approval layer yet. Executor/live trading is out of scope.

## 2. Live / Execution Status

No execution-ready strategy exists. Live trading must not be started.

The repository is a research/backtesting stack. Executor is planned only. Current promotion artifacts explicitly state they are not live authorization.

## 3. Data Status

Primary `feed/` has a confirmed outage/contamination window: `2026-04-23 17:05:00` through `2026-05-06 22:51:00` UTC.

Primary feed day findings:

- `2026-04-24` through `2026-05-05`: 100% synthetic, flat close, zero volume.
- `2026-05-06`: 95.10% synthetic.
- `2026-04-23`: partial contamination, 28.82% synthetic.

`feed_recovered/` exists for `2026-04-23` through `2026-05-06` and officially reruns through Analyzer successfully in `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`. Use recovered data for any gap-window research, with funding/liquidation degradation explicitly noted.

Primary feed gap conclusions are invalid as market evidence.

FE=0 / no setup / no event inside the contaminated window must be treated as data outage, not market behavior.

## 4. Analyzer Status

Analyzer is still a deterministic feature/research layer. It does not open positions and does not make live decisions.

Implemented stable outputs include:

- `analyzer_features.csv`
- `analyzer_events.csv`
- `analyzer_setups.csv`
- `analyzer_setup_outcomes.csv`
- reports/context/rankings/selections/shortlist
- `analyzer_research_summary.csv`
- `analyzer_day_regime_report.csv`

Stable implemented features include structural swings/sweeps/failed-breaks, absorption/context spikes, session context, H2 impulse features, and H2 impulse-reclaim setup extraction.

Sidecar-only research features include `ReclaimDepthToImpulseRange`, deep reclaim filters, late-US structural selectors, entry-delay transforms, and several cluster/concentration diagnostics. These are not Analyzer contract columns except where explicitly materialized in sidecar CSVs.

Recovered feed has been officially reprocessed into `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`: 14/14 days successful, 405 setups, 203 research summary rows, and 13 `FormalizationEligible=True` rows.

## 5. Backtester Status

Backtester performs deterministic replay over pre-generated Analyzer artifacts, separates validation/robustness/promotion artifacts, and has explicit same-bar policy handling.

Important limitations:

- Official routine replay uses `COST_MODEL_ZERO_SKELETON_ONLY`.
- All local promotion decisions found are `REJECT`.
- Validation often fails on source concentration and/or sample/expectancy gates.
- Cost stress exists mostly in research sidecars, not as the official promotion model.
- Broad routine replay has been useful as a control but is now a repeated REJECT loop if used as the main discovery process.
- Official recovered-gap Backtester rerun exists in `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`: 154 trades, 67 validation rows all `FAIL`, 67 promotion rows all `REJECT`, 0 `PROMOTE`.

## 6. Official Promotion Status

Official status: 0 `PROMOTE`, 0 execution-ready models.

Evidence:

- `python -m pytest -q`: 501 passed, 11 warnings.
- `research/run_log.csv`: 59 rows, 33 `BACKTESTED_REJECT`, 24 `NO_REPLAYABLE_RULESETS`, 2 `DUPLICATE_SKIP`, 0 non-REJECT promotion outcomes.
- Local `backtest_runs/`: 220 promotion rows, all `REJECT`; 220 validation rows, all `FAIL`.
- Recovered-gap `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`: 67 promotion rows, all `REJECT`; 67 validation rows, all `FAIL`.

## 7. Active Candidates

- `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`: best short-side research lead; wait/validate only.
- `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL`: long-side late-US watch; wait/validate only.
- `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`: frozen true-holdout candidate; no more tuning.
- `CAND_H4_FAILED_BREAK_RECLAIM_EXTENDED_V1`: active only as redesign watch. Current EXTENDED_V1 implementation is quarantined as invalid for intended H4 A/B/C formation.

## 8. Rejected Families

- Broad H1 reclaim baseline as main edge path.
- Daily broad replay as primary research loop.
- Current H4 EXTENDED_V1 as evidence for intended H4 candle false-break/reclaim.
- Local H1 duplicate cluster family.
- Primary-feed FE=0 conclusions during the synthetic outage.
- Broad long filters such as standalone deep reclaim >0.6, broad low-stress, broad zero-spike, broad compression, and wick-reclaim long.

## 9. Contaminated / Invalidated Findings

Any finding using primary `feed/` over `2026-04-23 17:05..2026-05-06 22:51` is audit-only unless rerun against `feed_recovered/`.

The repeated FE=0/setup starvation from `2026-04-24` onward is not market evidence. Official recovered Analyzer rerun produced normal setup surface and 13 formalizable rows across the gap.

Official recovered rerun replaces gap-window primary-feed conclusions for research evidence. Primary-feed gap artifacts remain forensic/audit-only.

## 10. Current Strategic Verdict

Edge is not confirmed.

The project is not dead, but it has been partly going in circles through broad daily replay that repeatedly ends in `REJECT`. The useful learning is now concentrated in narrower, entry-observable candidate surfaces.

Most promising path:

Data repair -> canonical state -> candidate registry -> frozen candidate contracts -> pooled replay -> forward holdout -> cost stress -> robustness -> promotion verdict -> Phase 4 Bridge.

## 11. What Not To Do

- Do not run Executor or live trading.
- Do not use primary-feed gap days as market evidence.
- Do not treat recovered feed as proof of profitability.
- Do not mutate risk logic or stops to improve backtests.
- Do not continue daily broad H1 replay as the main research loop.
- Do not tune `entry_delay_1` further before true holdout.
- Do not use H4 EXTENDED_V1 current replay arithmetic as evidence for the intended H4 candle setup.
- Do not use `H2_Post12Label_v1` as an entry predicate.

## 12. Next 10 Concrete Actions

1. Preserve `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/` as the official recovered Analyzer rerun.
2. Preserve `backtest_runs/recovered_gap_2026-04-23_2026-05-06/` as the official recovered aggregate replay.
3. Keep primary-feed gap runs marked as contaminated in all future reports.
4. Freeze `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` as a watch contract with threshold `>0.6`; do not add predicates.
5. Freeze `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` for true forward holdout; no tuning.
6. Continue `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL` watch on new clean days.
7. Replace current H4 EXTENDED_V1 with an explicit H4 Candle A/B/C detector before any new H4 replay.
8. Add explicit fee/slippage/spread stress to candidate validation reports.
9. Add same-bar ambiguity summary to each candidate registry update.
10. Promote only after all mandatory gates pass: >=25 post-holdout trades, >=10 post-holdout trade-days, positive net after cost stress, no single-day dominance, no unresolved same-bar bias, stable parameter neighborhood, source concentration pass, execution-observable entry, explicit stop/exit, isolated margin only, no cross, no martingale.
