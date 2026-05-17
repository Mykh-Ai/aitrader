# Analyzer v1 Limitation Report

Last updated: 2026-05-17

## Current State Audit

Canonical state reviewed:

- `research/canonical/PROJECT_STATE_CURRENT.md`
- `research/canonical/CANDIDATE_REGISTRY.csv`
- `research/canonical/ACTIVE_WATCHLIST.md`
- `research/canonical/REJECTED_FAMILIES.md`
- `research/canonical/HOLDOUT_PROTOCOL.md`

Confirmed state:

- Official promotion status is `PROMOTE = 0`.
- Phase 4 Bridge is closed as an approval layer.
- Executor and live trading are prohibited.
- `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` is the only active validation candidate.
- `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL` is passive `WATCH_ONLY`, not a replayable strategy.
- Broad H1 reclaim baseline, daily broad replay, current H4 `EXTENDED_V1`, local H1 duplicate entries, primary-gap FE=0 conclusions, broad long filters, and Sprint 03 deep-reclaim short are rejected, control-only, or quarantined.

## Analyzer v1 Scope

Analyzer v1 is a deterministic facts and research-artifact layer. Its implemented core is centered on:

- H1/H4 structural swings.
- H1/H4 sweeps.
- H1/H4 failed-break detection.
- Failed-break/reclaim setup extraction.
- Absorption/context spike features.
- Session context.
- H2 impulse and impulse-reclaim research surfaces where materialized.

This is useful and should remain preserved. It gives reproducible artifacts, an auditable baseline/control, and source lineage for existing candidate families.

## Limitation

Analyzer v1 is not a broad strategy discovery engine.

It was built around structural swing, sweep, failed-break, reclaim, and H2 impulse-reclaim hypotheses. Re-running every old Analyzer v1 routine or broad replay path will mostly retest the same rejected/control surfaces. That will not answer whether other market behaviors in the clean feed contain edge.

The old broad H1 daily loop and broad failed-break/reclaim family are now control surfaces, not the main research path. The current H4 `EXTENDED_V1` arithmetic is quarantined and must not be cited as proof of the intended H4 candle A/B/C idea. The deep-reclaim short formal ruleset is rejected as currently specified and must not be reopened by threshold changes.

## Required Pivot

Analyzer v1 remains useful for:

- deterministic control comparisons;
- existing candidate lineage and artifacts;
- candidate-specific holdout flows already frozen before Sprint 05;
- validating that Analyzer v2 does not accidentally recreate old rejected claims.

Main research should pivot to Analyzer v2 Discovery:

- describe market behavior across the whole clean feed before selecting entries;
- create feature and outcome surfaces across multiple behavior families;
- separate observable features from forward outcome labels;
- rank research opportunities without using future outcomes as entry predicates;
- promote nothing without replay, holdout, cost, source concentration, and same-bar gates.

## Frozen Candidate Boundary

`CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` remains `ACTIVE_VALIDATION / WAIT`.

Do not tune:

- `ctx_spike_count >= 2`;
- `entry_delay_1`;
- `REFERENCE_LEVEL_HARD_STOP`;
- fixed `1.5R` target;
- `BARS_AFTER_ACTIVATION:12` expiry.

Sprint 05 discovery work must not build around this candidate or modify its holdout protocol.
