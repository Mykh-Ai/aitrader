# SHI_RESET_40E — directional stop diagnosis and controlled target sensitivity

Date: 2026-10-14. Scope: the user asked to investigate the 16 stop outcomes, separate long/short and explain the empirical origin of 6R short / 10R long. This is a diagnosis of the frozen 40D candidate, not a new policy promotion.

## Evidence and method

Run root: `market_monitor_runs/SHI_RESET_40E_hybrid_stop_diagnosis_v0/`. Baseline: `SHI_RESET_40D_HYBRID_CANDIDATE_V1`, its selected strategy, selected dollar ledger and selected result. Their SHA256 identities are frozen before diagnostics in `study_manifest.json`. Both scripts verify the existing five research-code hashes and all frozen feed inputs. No saved 38V candidate or Scout signal is used.

All 26 baseline paths and all 16 stops are reconciled. Favorable/adverse excursions use actual minute observations from the entry minute through observed closure. Pre-terminal MFE excludes the exit minute to avoid inventing intraminute order; including that minute does not change any stop-case 1R/2R count. Isolated omitted primary minutes retain the active 40B1 policy. Stop-only post-exit excursions through the original deadline are explicitly diagnostic future outcomes and require RAW continuity with at most an isolated omission, including interval boundaries; one short post-stop continuation is unavailable because of the extended July gap. No future diagnostic is a pre-entry feature.

Causal opposing H4 references are a bounded diagnostic inventory, not the canonical Monitor zone registry: strict three-bar H4 swing, right-bar-close availability, two H1 closes through the 5-bp band retire a reference, and an age limit of 30 days at each entry. All history is processed chronologically and inventory is retained. Availability is checked against each decision. No level formed later in the trade is used at entry.

Early reference failure is a post-entry observation: one of the next three completed H1 closes, while the original trade remains open, crosses the frozen entry EMA24 (long) or accepted-break support (short) by 5 bps. It cannot be used retrospectively to admit/reject the original entry. Any future management test requires causal availability, entry/exit latency and a fresh one-position portfolio replay.

## Findings

| Direction | Trades | Stops | Stop model net USD | All model net USD | Median hours to stop | Stops reaching 1R / 2R before exit |
|---|---:|---:|---:|---:|---:|---:|
| LONG | 14 | 8 | -355.919523 | +442.443309 | 6.958333 | 0 / 0 |
| SHORT | 12 | 8 | -518.040757 | +69.832705 | 57.141667 | 3 / 0 |

Long: six/eight stops fail the frozen EMA24 reference in the first three H1 closes versus one/six non-stop outcomes. Six/eight stops never reach 0.5R; all eight stay below 1R. Five/eight stops are in July. Five/eight stop anchors are the 2-ATR floor, three prior-six-H1 structure. The surviving early-failure long is April16 and made +139.077748 USD under the baseline; a proposed early exit therefore has a known opportunity-cost counterexample.

Short: six/eight stops have a pre-existing opposing H4 reference within 1R, versus one/four non-stop outcomes. Median distance among stopped shorts with an available reference is0.363671R. Their signal-volume ratio median3.994962 exceeds non-stops2.673843; low volume is not supported as a unifying explanation. All eight stop anchors are prior-six-H1 structural highs. Three stops first reach1R, none2R. Early support reclaim is only two/eight stops and also two/four non-stops, including a6R target; it is not the strong discriminator observed in long.

These are descriptive associations on eight losses per side, not statistical proof or validated filters. Mean initial risks across all direction trades differ: long40.629348 USD, short58.283758 USD. Thus6R short and10R long correspond to mean planned gross targets349.702545 and406.293484 USD, not a universal dollar R.

## Targets: selection provenance and controlled replay

The original6R/10R are fixed multiples empirically selected from 40D accepted-break and trend-retest component batches. They were not established by live practice or by a separate full pair optimization before the hybrid selection. They are not per-signal liquidity-derived target prices.

The declared20-pair sensitivity changes only targets: short[2,4,6,8] × long[2,4,6,8,10]. Every pair uses the same signal array, original stop rules, $3,000 notional, $5 round-trip fee,2 bps per fill,168-hour deadline, actual minute execution and one global position with three-minute cooldown. Target timing can change subsequent entry admission; alternate portfolios are never obtained by simply summing overlapping independent trade cases.

The baseline6R/10R reproduces all26 rows and +512.276015 USD within strict numerical tolerance. It is the largest observed net among the declared20 pairs; long10R is the upper grid boundary, so no unbounded optimum is established. Holding short6R fixed, long4/6/8/10R all retain the same26 entries and16 stops and yield281.029813/342.380833/427.328424/512.276015 USD respectively. This directly shows that shrinking the long target does not cure any baseline stop and reduces surviving-winner profits. Short4R/long10R yields343.768566; short8R/long10R yields177.539500 with25 entries and one rather than two short target outcomes.

Negative and incomplete sensitivity evidence is retained: four long2R portfolios each contain one censored trade due to an extended data gap. Their reported cash sum is observed resolved cash only, not a complete result. All20 journals and the complete table, including every failure, are preserved. This is exposed historical sensitivity, not independent holdout validation.

## Verification and next implication

`diagnostic_verification.json` and `target_sensitivity_verification.json` record baseline/source/code identity, complete case accounting, causal reference clocks, terminal-minute bounds, target-pair baseline equality, one global book/cooldown and independent cash arithmetic. Only run-artifact scripts/reports and handoff documentation changed; the applicable762-test40D regression remains recorded. No reusable research/production code changed, so the full regression was not redundantly rerun for this diagnostic task. `git diff --check` is the final documentation check.

Next bounded experiments: separately test long retest confirmation/early invalidation and short opposing-structure space. A1R partial/BE experiment has relevance to three initial short losses and zero initial long losses. Preserve baseline and run each change with causal fills on the complete chronology; do not silently install an outcome-selected entry filter or pretend alternative rules have untouched-data evidence. Subsequent fixed-rule confirmation remains necessary before any production/edge claim.

No protected feed, production Monitor/Executor source, position/order behavior, legacy Backtester gate, governance promotion, network, dependencies or remote state was changed. BTCUSDT price-proxy reporting, assumed costs, unmodeled borrowing, small-sample concentration and prior adaptive history exposure remain40D limitations. Working-tree task; no commit hash.
