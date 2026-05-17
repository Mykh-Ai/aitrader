# REJECTED_FAMILIES

Last updated: 2026-05-17

## Broad H1 Reclaim Baseline

- Tested windows: routine history in `research/run_log.csv`, plus local `backtest_runs/`.
- Reason rejected: repeated `REJECT`; no `PROMOTE`; validation fails across all local promotion rows.
- Metrics summary: `research/run_log.csv` has 33 `BACKTESTED_REJECT`, 24 `NO_REPLAYABLE_RULESETS`, 0 non-REJECT promotion outcomes. Local `backtest_runs/` has 220 promotion rows, all `REJECT`.
- Status: permanently rejected as main edge path; keep as control family only.
- Required to reopen: a frozen candidate contract that clearly outperforms broad control on clean/recovered data.
- Warning: do not keep running daily broad H1 as the primary process. It creates a REJECT loop, not learning.

## Daily Broad Replay Loop

- Tested windows: 2026-03 routine through 2026-05 routine.
- Reason rejected: broad replay finds non-zero surfaces but repeatedly fails validation/robustness; it does not isolate an edge.
- Metrics summary: reject decomposition found 169 audited promotion rows, all `REJECT`; ruleset-scope failures are mainly `LIVE_BUT_UNSTABLE`, `LIVE_BUT_NEGATIVE`, and validation-gate failures.
- Status: archived as control process.
- Required to reopen: use only as baseline comparison for a frozen candidate, not as a discovery engine.
- Warning: broad replay should not drive candidate selection without a pre-registered narrow hypothesis.

## Current H4 EXTENDED_V1 As Intended H4 Setup Evidence

- Tested windows: `2026-03-30_to_2026-05-02` H4 diagnostics.
- Reason rejected: detector is invalid for intended H4 Candle A/B/C false-break/reclaim. It detects raw M1 failed-breaks against latest H4 swing level lineage.
- Metrics summary: 37 diagnostic H4-lineage trades are reproducible, but root-cause audit shows micro risk distances and same-bar/micro target artifacts. Reference-stop had SameBarExit 13/37 and SameBarCollision 9/37.
- Status: rejected as current implementation; concept may be redesigned.
- Required to reopen: new explicit H4 A/B/C detector, minimum risk/fee viability, clean/recovered replay.
- Warning: do not cite current EXTENDED_V1 R/MFE as evidence for H4 setup-class edge.

## Sprint 03 Formal Deep-Reclaim Short Ruleset

- Tested windows: already-seen canonical Analyzer artifacts plus recovered gap artifacts, formal Sprint 03 pooled replay.
- Reason rejected: formal Backtester-integrated cost stress is negative at baseline and at hard gate `0.00015`.
- Metrics summary: 14 trades, 7 trade-days, cost `0.00015` net `-0.0023540122`, source concentration FAIL.
- Status: rejected as current formal ruleset.
- Required to reopen: only as a new pre-declared candidate with a new holdout clock.
- Warning: do not reopen by lowering `0.6`, adding a filter after seeing this result, or repeating a threshold tuning loop.

## Local H1 Duplicate Entries

- Tested windows: `2026-03-12_to_2026-05-04` local H1 diagnostic.
- Reason rejected: 71 allowed rows collapse to 3 retained 48h clusters; 68 rows are duplicates under conservative clustering.
- Metrics summary: 48h cluster-first retained only 3 clusters; best rows are often later duplicates inside the same impulse, not independent setups.
- Status: rejected as noisy duplicate family.
- Required to reopen: independent setup definition that avoids same-impulse fragmentation.
- Warning: shrinking cluster windows mainly retains more fragments; it does not prove an edge.

## Primary-Feed Gap FE=0 Conclusions

- Tested windows: primary `feed/` 2026-04-24..2026-05-06.
- Reason rejected: data outage, not market behavior.
- Metrics summary: primary feed was 100% synthetic from 2026-04-24 through 2026-05-05 and 95.10% synthetic on 2026-05-06. Recovered Analyzer audit restored 405 setups and 13 formalizable rows across the gap.
- Status: permanently rejected as market evidence.
- Required to reopen: rerun from `feed_recovered/`.
- Warning: do not use FE=0 starvation in this window as strategy evidence.

## Broad Long Filters

- Tested windows: H2 long diagnostics 2026-03-17..2026-05-14.
- Reason rejected: broad `low_stress_long`, standalone `ReclaimDepthToImpulseRange > 0.6`, broad zero-spike, broad compression, and wick-reclaim filters do not show robust long edge.
- Metrics summary: long deep reclaim `>0.6` had 32 trades, PnL +3.29, post PnL -137.85. Broad `low_stress_long` had 200 trades, PnL -27.69. `zero_spike_long` had PnL -315.91.
- Status: archived unless new data changes the surface.
- Required to reopen: late-US structural watch must fail or new clean sample must show a different stable, entry-observable selector.
- Warning: do not transfer short-side deep reclaim threshold to long side.
