# Analyzer v2 Discovery Specification

Last updated: 2026-05-17

## Purpose

Analyzer v2 Discovery is a research reset layer. It should discover and rank market behavior families across the whole clean feed before converting anything into a replayable strategy.

Analyzer v2 must not replace the frozen CTX holdout flow, change Backtester, touch Executor, or promote anything directly.

## Non-Goals

- No live trading.
- No Executor or exchange order lifecycle.
- No Phase 4 bridge reopening.
- No parameter tuning on `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`.
- No deep-reclaim threshold rescue.
- No H4 `EXTENDED_V1` reuse as proof.
- No old broad H1 daily loop as the main research process.
- No future labels as entry predicates.
- No promotion without replay, holdout, cost, source concentration, and same-bar gates.

## Input Surface

Use clean feed only:

- Primary `feed/` outside `2026-04-23 17:05:00` to `2026-05-06 22:51:00` UTC.
- `feed_recovered/` inside that window only when lineage is available and degraded fields are documented.

Analyzer v2 should preserve source lineage per row or per event:

- `primary`
- `primary_gap_excluded`
- `primary_plus_recovered_gap`
- degraded-field flags for recovered funding, OI, and liquidation fields.

## Discovery Principles

Features are observable at or before the event timestamp. Outcomes are forward labels for ranking and analysis only.

Outcomes must not be used as entry predicates.

Every candidate that later moves toward replay needs:

- frozen feature predicates;
- explicit entry timing;
- explicit stop/target/expiry;
- deterministic replay;
- cost stress;
- source concentration review;
- same-bar ambiguity review;
- true holdout.

## Family A: Momentum Continuation

Feature surface:

- range expansion;
- volume expansion;
- delta dominance;
- open interest expansion;
- close location in candle/range;
- no immediate reclaim after expansion.

Candidate event object:

- an expansion bar or expansion cluster with observable volume/delta/OI context;
- direction anchored to close location and signed return;
- no use of forward continuation labels in event creation.

Outcomes:

- forward 3/6/12/24 bar continuation;
- MFE and MAE;
- later fixed-R replay surface after candidate freeze.

Questions:

- Does expansion continue more often in specific sessions or volatility regimes?
- Does delta/OI confirmation separate continuation from exhaustion?
- Does immediate reclaim invalidate continuation behavior?

## Family B: Exhaustion Reversal

Feature surface:

- climax volume;
- delta extreme;
- wick rejection;
- failed continuation;
- OI spike then stall;
- liquidation spike when available;
- VWAP distance.

Candidate event object:

- a climax bar or cluster with observable rejection/failed-continuation context;
- side is opposite the exhausted move only after observable rejection is present.

Outcomes:

- reversal magnitude;
- time to mean revert;
- MFE and MAE.

Questions:

- Which climax events revert and which continue?
- Are liquidation fields reliable enough outside recovered degraded windows?
- Does VWAP distance improve separation without becoming a hindsight label?

## Family C: VWAP / Deviation Model

Feature surface:

- price distance from VWAP;
- VWAP slope;
- deviation bands;
- session context;
- volume regime.

Candidate event object:

- deviation state at closed bar;
- session and regime context frozen at event time.

Outcomes:

- reversion to VWAP;
- continuation away from VWAP;
- time to VWAP touch or deviation extension.

Questions:

- Are large deviations mean-reverting only in chop regimes?
- Does VWAP slope separate trend continuation from reversion?
- Are session-specific deviations materially different?

## Family D: Session Behavior

Feature surface:

- Asia, London, US, late-US;
- weekday/weekend;
- funding windows;
- session volatility;
- session volume and delta regime.

Candidate event object:

- session bucket and pre-session state;
- no directional label from future session close.

Outcomes:

- directional edge by session;
- reversal/continuation behavior by session;
- session-specific MFE/MAE.

Questions:

- Which sessions produce expansion versus chop?
- Are weekend sessions structurally different?
- Do funding windows coincide with directional or reversal behavior?

## Family E: Regime Classifier

Feature surface:

- ATR or realized volatility;
- range compression;
- trend slope;
- volume regime;
- OI regime;
- chop/trend classification.

Candidate event object:

- regime row or regime segment using only historical rolling windows;
- regime labels frozen before setup-family evaluation.

Outcomes:

- which setup families work in which regime;
- conditional MFE/MAE and continuation/reversion rates;
- later replay gates stratified by regime.

Questions:

- Are prior rejected families only bad globally, or bad in specific regimes?
- Which new family has stable behavior across regimes?
- Which regimes should be controls instead of candidates?

## Family F: Proper H4 A/B/C Detector

This is specification-only for Sprint 05 unless explicitly implemented later.

Definitions:

- A = confirmed H4 swing or H4 level.
- B = H4 sweep candle that breaches A after A is known.
- C = H4 close reclaim or close failure after B.
- M1 entry can occur only after H4 C confirmation is closed and observable.

Rules:

- Do not reuse current H4 `EXTENDED_V1` as proof.
- Do not use raw M1 failed-break arithmetic as an H4 candle A/B/C proxy.
- H4 confirmation timestamps must be explicit.
- M1 entry timing must be after H4 confirmation, not during the B or C candle.
- Same-bar and micro-risk artifacts must be audited before replay claims.

Outcomes:

- H4 A/B/C continuation or reversal after confirmation;
- M1 path MFE/MAE after H4 confirmation;
- later replay only after a new detector contract is frozen.

## Sprint 05 Prototype Boundary

`research/scripts/sprint_05_discovery_surface_scan.py` is only a prototype. It writes feed opportunity and preliminary discovery summary outputs. It does not create strategies, emit `PROMOTE`, call Backtester, run Analyzer v1, or touch Executor.
