# SHI RESET 40A Own Signal Causality Preflight

Date: 2026-10-13

Verdict: `SAVED_COHORT_REJECTED_FOR_CAUSAL_FINANCIAL_VALIDATION`

## Objective and scope

The user restated the intended result: AiTrader's own feed must produce its own signals, followed by a Backtester trade journal and results by family after costs. Scout is a reference system, not a required signal source. No profitable family has been established.

This preflight inspects saved 38V candidates, 38W1 outcomes, their selected-zone inputs, and current reusable code. It does not generate new signals, calculate PnL, run the financial Backtester, alter feed assets, or promote a trading policy. The 39A architecture audit remains canonical. This finding adds a previously unrecorded source-causality limitation to the historical 38V/38W1 evidence.

Run root: `market_monitor_runs/SHI_RESET_40A_own_signal_causality_preflight_v0/`.

## Confirmed source-causality failure

49 of 51 candidates record `setup_formed_at` before the end of the market-state row they consume; the largest difference is 23 hours. Two have equal timestamps. Equal timestamps do not validate their other inputs.

Code mechanism:

- `market_monitor.market_structure_state._build_state_timeline` computes price, delta, OI, pressure and classification from each day's feed through `end_timestamp`, normally 23:59 UTC.
- `market_monitor.setup_builder._build_rows` passes that completed daily state and its pressure context to the family predicates.
- `_formed_at` assigns the earlier raw regime window's end as the setup review timestamp when a raw window exists.
- The 38W1 script enters at the first minute after that earlier timestamp. Therefore later daily state evidence influences an earlier simulated entry.

Concrete example: `setup_000001` is recorded at `2026-03-12T16:59:00Z`, consumes a state ending at `2026-03-12T23:59:00Z`, and is replayed from the next minute. That state includes seven hours of observations unavailable at the entry decision.

Evidence classes: `CODE_CONFIRMED` and `RUN_ARTIFACT_CONFIRMED`. The 38V manifest's `future_data_used_for_setup_builder=false` is contradicted by this input/timestamp mechanism. This audit does not edit or erase that manifest.

## Full-period zone selection and target geometry

The 38V runner selects seven visible zones once over the full March 11-June 28 interval and supplies that same table to every historical setup. Neither `_visible_zones` nor `_target_reference_zone` applies a per-setup availability cutoff.

24 of 51 target references match a selected snapshot from a later calendar day. For example, the March 12 candidate uses `zone_001106:BUY_SIDE:77509.72575-77587.27425`, whose selected row has `source_day=2026-05-25`.

`source_day` is the snapshot date, not the original level's formation date. This proves use of a later selected snapshot without a causal availability check; it does not, by itself, prove that the price geometry first formed in May. The global full-period ranking also prevents treating older-snapshot matches as automatically causal.

26 of 51 saved target zones are on the wrong side of the actual replay entry: the complete zone is not strictly below entry for a short or strictly above entry for a long. This is a separate entry-relative geometry check. The existing 38X fix is directional relative to its supplied price, but `_row` currently supplies the daily state close; it is not proof of geometry at an earlier intraday entry. Current target behavior must be regenerated from causal inputs.

## Historical family counts

These are the preserved 38W1 labels, not net trade results:

| Family | Rows | Stop before TP1 | TP1 then BE | TP1 then target | TP1 without completed continuation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seller-dominance retest down | 28 | 9 | 17 | 2 | 0 |
| Supply sweep/reclaim down | 14 | 6 | 7 | 0 | 1 |
| Demand sweep/reclaim up | 9 | 2 | 7 | 0 | 0 |

TP1 is 1R in the 38W1 script. These labels lack a frozen partial-exit fraction and complete financial cost model. They cannot be converted into net expectancy merely by counting TP1 reactions. More fundamentally, the source-causality failure makes this saved cohort unsuitable for validating a tradable strategy even if a subsequent financial calculation looks positive.

## Concrete next experiment

The next bounded research task should deliver a causal own-feed candidate stream and a cost-aware family comparison, rather than require completion of the entire Monitor backlog before asking whether any family has promise.

1. Build an H1-close runner from AiTrader feed only. At every close, use prior history, confirmed structure and zones available by that close, carried state, and completed flow evidence. Freeze candidate evidence and timestamps. Use no Scout/NEG trigger timestamps or 38S source rows.
2. Keep the three current families separate. Their initial rules and any finite volume/delta/OI/liquidation ablations must be written before evaluating their returns. An outcome-selected shortlist is not a signal filter.
3. Require `available_at <= decision_at < entry_at` for every consumed state, level, zone and flow window. Use the next minute open for an initial market-entry research model. Reject wrong-side/unresolved stops and targets, stops inside a sequence-linked sweep, and incomplete execution data. Fix deduplication and concurrent-trade policy before replay.
4. Freeze entry, expiry, partial exits, BE, target/trailing and conservative ambiguous-bar handling. Then connect only that explicit candidate contract to a separately scoped offline financial replay. Include commissions, slippage and the financing appropriate to the intended execution instrument. Futures signal prices alone cannot establish executable Spot Margin BTC/USDC returns; a proxy experiment must identify that limitation.
5. Produce all candidate decisions, rejection reasons, fills/exits, gross and net R, net expectancy, profit factor, drawdown, holding time and results by family and chronological period. Report counts and uncertainty; a tiny positive sample does not establish edge. Retain every trial, including negative ones. Test sensitivity to costs and dependence on the largest trades.
6. Freeze rules before the evaluation interval; carry warm-up context without counting warm-up trades. Existing history already examined during research must not be relabelled as a pristine untouched holdout. Use chronological validation and reserve genuinely unexamined data or subsequent paper observations for confirmation.

A causal, reproducible positive result after costs is a candidate for further validation. Negative or insufficient evidence is a valid research verdict. Neither verdict activates live trading, Executor policy or automatic edge promotion. Backtester remains inactive as a project promotion gate; this preflight does not change that governance.

## Verification

`build_preflight.py` validates one-to-one setup identity across 51 source/outcome rows, exact target-bound matches to the visible zone inputs, and unchanged SHA-256 values of its source artifacts. The generated per-row CSV contains all temporal and geometry flags. Deterministic rerun and documentation diff checks are recorded in `PROJECT_LOG.md`.

No strategy discovery or profitability test was performed in 40A. No production source, feed data, historical run output, or trading policy was changed.
