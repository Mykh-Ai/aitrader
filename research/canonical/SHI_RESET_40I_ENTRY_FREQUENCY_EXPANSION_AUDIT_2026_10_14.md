# SHI_RESET_40I — entry-frequency expansion

Date:2026-10-14. User requested moderately expanding entry conditions and filters because40H's12 April–September trades are too few. Run root:`market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/`. Preserve40H as frozen control; no production/reusable strategy change. Same230 protected futures source identities,40G verified spot CSV, causal reference mapping, costs and execution engine.

## Scope and adaptive sequence

`study_manifest.json` fixed74 variants before their financial returns. Long H1 delta threshold4/2/0%; relative volume1.3/1.1/1.0; low-to-EMA24 tolerance0/.15/.30ATR; close-distance maturity1.5/2ATR; signal range2/2.5ATR. Short accepted-break lookback48/24H1 with two closes, relative volume1.3/1.1/1.0; opposing-H4 space1/.75R. Post-entry-decision flow screens:24h-band4/6%, long4h-delta floor0/−1%. Both one-variable diagnostics and finite preset combinations retained. Calendar, source quality, isolated-minute tolerance, same-book occupancy, stop/target/costs are not relaxed.

The strict generation control matches original `hybrid_signals` exactly and reproduces all13 frozen40H financial rows. Its6%-band sensitivity reproduces40H exactly. Baseline funnel:3770 eligible calendar/quality H1s→1614 long trend→155 retests→102 hourly flow→37 volume→27 maturity/impulse long candidates, plus25short candidates=52. Existing short-space gate leaves36; delta screens leave20; one global book blocks6 and entry/risk geometry rejects1, resulting13 trades. Do not confuse raw candidates with actual frequency or infer that long position occupancy is the sole limitation.

Simple relaxing adds mostly losers. After this evidence, `event_manifest.json` fixed48 additional-event variants before their returns:accepted-range long, first range-break long/short and mirrored short retest,24/48h range, volume1.3/1.1 and bounded pairs, new-event delta-band4/6. First break means first signal of a raw closed-H1 breakout episode; repeated candles are suppressed. All use known prior levels and inherited quality/time exclusions. New events cap distanceEMA24 at2ATR and range at2.5ATR. Extra short retests require negative rolling4h delta; this was not imposed retroactively on the old short family, whose profitable June1 event has a small positive4h delta. No shallow sweep shortcut or old Analyzer/Scout seed is introduced.

After those results, `combination_manifest.json` fixed8 combinations of the declared0.75R short-space gate with selected existing entry alternatives, including a high-frequency case. Prior stage result hashes and rule code are retained. These three adaptive stages total130 declared portfolios. No claim that all130 were specified before stage1 diagnosis or constitute untouched confirmation.

Unchanged economics:3000USDC notional,5USDC per completed trade,2bps adverse slippage per fill, one global position,1minute entry latency,3minute cooldown,6H structural stop/ATR floors and initial-risk bounds,10R-long/6R-short and168h expiry. Futures BTCUSDT generates signals; BTCUSDC Spot executes; quote conversion uses closes available at decision. Actual borrow rates/availability and orderbook fills are still unverified and excluded. Full history and confirmed H4 inventory carried without technical resets; this does not promote a full Monitor lifecycle implementation.

## Selection discipline and results

First manifest fixed a research challenge:at least24 April–September trades (twice40H), at least500USDC net full and six-month, zero censor. Strong criterion additionally preserves40H full/six-month cash, DD≤225 and positive result without bestthree. Thirteen portfolios meet the minimum; **zero meet the strong criterion**. It was not silently reduced.40H remains control. A moderate frequency alternative is frozen separately, even though it does not satisfy the24-trade challenge.

`JOINT_PAIR48_V13_B6_SPACE075` keeps old40H entries with short-space floor0.75R, and adds first closed48h range breaks in both directions. Extra long uses EMA trend; extra short negative24h price change/delta; H1 delta≥4% in side direction, volume≥1.3prior24h median, distance≤2ATR/range≤2.5ATR, new-event |delta24|<6%, longdelta4>0. Opposite simultaneous candidates are suppressed before replay; same-side candidates merge. Core24h-band4 remains. Absence of known opposing H4 reference passes the inherited gate and is not proof of clear space.

| Entry cohort/result |40H control|Moderate alternative|Lower-volume extra entries|Double-frequency relaxation|
|---|---:|---:|---:|---:|
|April–September trades|12|16|17|24|
|Positive/negative|8/4|10/6|10/7|8/16|
|April–September netUSDC|1142.108729|1150.204867|1092.991065|692.847887|
|Closed-trade DD USDC|74.610063|125.272198|125.272198|398.346187|
|Full-history trades/netUSDC|13/1090.811851|18/1156.804084|19/1099.590282|26/719.031152|

The double-frequency row is `L_FLOW02_VOL11_S_LB24_VOL11_B6_F-1`:long flow2%/volume1.1, short24h lookback/volume1.1, band6%, long4hdelta>−1%. It loses a baseline April7 winner218.305273 through changed book occupancy, adds14 trades (2wins/12losses) totaling−153.475426 and has net without bestthree−161.707706. The most permissive portfolio has32full/29six-month trades but only344.91USDC rounded full net (exact CSV retained); more trades is not proof of better economics. All failures and negative months remain recorded.

Moderate full-history outcome:18observed,11positive/7negative, gross1268.463325−90fees−21.659241slip=**1156.804084USDC**. Long11/+713.977472; short7/+442.826612. Mean64.266894USDC/1.791111R, mean initial risk44.119806; planned target mean8.444444R/367.350697USDC, distinct from realized return. Four full targets unchanged; seven profitable168h expiries and seven stops. Mean hold90.557407h; holding horizon remains unresolved. PF4.432469, closed-trade DD125.272198. Without bestthree+316.784459. Ten isolated spot omissions, no censor/inferred exit.

All8 original winners retained unchanged. Six new entries (three positive/three negative) net+33.365977USDC. Old July12 long loss32.626256 does not enter because the new July10 long occupies the book through July13. Exact difference:1090.811851+33.365977+32.626256=1156.804084. New entries:March26short+57.896095, July2long+83.632387, July10long−47.950802, July17short−37.808678, July23short+10.300137, September7long−32.703162. March trade is outside the six-month cohort, so April–September improvement is only8.096138USDC for four more trades. July remains−31.339674USDC. Do not present larger full-history gain as the six-month improvement or add overlapping independent paths.

Lower-volume extra-event sensitivity1.1 adds another loss57.213802, giving19full/17six-month trades and1099.590282/1092.991065USDC. Reducing short-space to0.75R alone adds only a March winner57.896095 and leaves six-month count/net unchanged; this is not a solution to half-year frequency on its own. All three stages, attribution and monthly tables remain available.

## Verification and handoff

17tests passed in0.74s:seven new focused entry contracts plus ten original replay tests. They cover baseline generator parity/no mutation, near-EMA geometry and green close, unchanged degraded/calendar guards, known-price0.75R space, opposing-signal conflicts, first-break episode/prefix semantics and unusable window rejection.

`verify_study.py` recomputes all130 complete signal streams and compares them to saved decisions, then verifies future-prefix invariance for every stream and new raw metric at2026-08-20 23:59UTC. H4 inventory is independently rebuilt from prefix. All2450 portfolio trade rows are cash/risk/target/cost checked;59unique entry paths receive independent first stop/target/expiry-touch checks, and every duplicate row matches. All portfolios preserve one global book/cooldown and available same-clock basis quotes. All outcomes observed. All47 frozen40H artifacts, original source/code identities and three batch code hashes unchanged. A first verifier execution passed causal/path checks but failed final export because of a missing directory-constant import; corrected only the verifier import and reran it fully. `verification_execution_note.json` and durable `verification_output.txt` retain this non-financial repair.

Frozen alternative:`frequency_alternative_contract.json`, `frequency_alternative_result.json`, `frequency_alternative_trade_ledger_usdc.csv`, `frequency_alternative_attribution.csv`; comparison:`user_comparison.csv`; Ukrainian report:`result.md`. Stage2 raw ledger `family` is the inherited exit-configuration label, with actual added entry in `entry_event`; the final alternative carries both accurate `family=FIRST_RANGE_BREAK` for added breaks and `exit_configuration_family` for the inherited stop/target configuration. Do not relabel added breakouts as the old retest family.

This meets the user's modest frequency-expansion request with an explicit risk/cash tradeoff, while the stronger doubled-frequency objective remains unmet. History is adaptive/exposed; subsequent fixed-rule confirmation is still needed. Preserve40H and this alternative separately. No production/Executor/live/order/sizing behavior, protected-data edit, legacy Backtester gate, dependency, network, commit, push or remote mutation occurred.
