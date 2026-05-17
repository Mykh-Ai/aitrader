# Discovery Output Schema

Last updated: 2026-05-17

## Purpose

This schema defines the minimum future Analyzer v2 Discovery artifacts. The goal is to separate observable features, discovered events, forward outcomes, surface summaries, and shortlist candidates without allowing outcome leakage into entry predicates.

## Required Files

Future Analyzer v2 Discovery must write at least:

- `discovery_features.csv`
- `discovery_events.csv`
- `discovery_outcomes.csv`
- `discovery_surface_summary.csv`
- `discovery_candidate_shortlist.csv`

Sprint 05 prototype currently writes:

- `research/results/feed_opportunity_audit.csv`
- `research/results/discovery_surface_summary.csv`

## discovery_features.csv

One row per clean bar or derived clean state row.

Minimum columns:

- `Timestamp`
- `date`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `BuyQty`
- `SellQty`
- `VWAP`
- `OpenInterest`
- `FundingRate`
- `LiqBuyQty`
- `LiqSellQty`
- `IsSynthetic`
- `data_source`
- `lineage_note`
- `degraded_funding`
- `degraded_open_interest`
- `degraded_liquidations`
- `session`
- `weekday`
- `range_pct`
- `body_to_range`
- `close_location`
- `delta`
- `delta_pct`
- `volume_regime`
- `oi_regime`
- `realized_volatility_regime`
- `vwap_distance_pct`
- `vwap_slope`
- `atr_or_realized_volatility`
- `compression_state`
- `trend_slope`

All feature columns must be observable at or before `Timestamp`.

## discovery_events.csv

One row per discovered behavior event.

Minimum columns:

- `discovery_event_id`
- `Timestamp`
- `date`
- `family`
- `side`
- `event_type`
- `event_version`
- `source_timeframe`
- `feature_snapshot_ref`
- `data_source`
- `lineage_note`
- `observable_predicates`
- `predicate_version`
- `degraded_field_flags`
- `notes`

Allowed `family` values for the first v2 spec:

- `MOMENTUM_CONTINUATION`
- `EXHAUSTION_REVERSAL`
- `VWAP_DEVIATION`
- `SESSION_BEHAVIOR`
- `REGIME_CLASSIFIER`
- `H4_ABC_SPEC`

`observable_predicates` must contain only features available at event creation time.

## discovery_outcomes.csv

One row per event and outcome horizon.

Minimum columns:

- `discovery_event_id`
- `outcome_horizon_bars`
- `outcome_start_ts`
- `outcome_end_ts`
- `forward_return_pct`
- `continuation_flag`
- `reversal_flag`
- `time_to_vwap_touch_bars`
- `time_to_mean_revert_bars`
- `mfe_pct`
- `mae_pct`
- `best_high`
- `best_low`
- `final_close`
- `outcome_status`

Outcomes may be used for labeling, ranking, diagnostics, and shortlist review only.

Outcomes must not be used as entry predicates.

## discovery_surface_summary.csv

One row per family, surface, label, or regime aggregate.

Minimum columns:

- `surface`
- `family`
- `event_version`
- `days`
- `events`
- `independent_event_days`
- `avg_forward_return_pct`
- `median_forward_return_pct`
- `positive_rate`
- `avg_mfe_pct`
- `avg_mae_pct`
- `source_concentration_note`
- `degraded_field_note`
- `research_verdict`
- `notes`

Allowed `research_verdict` values:

- `DESCRIPTIVE_ONLY`
- `DISCOVERY_REVIEW`
- `CONTROL_ONLY`
- `QUARANTINED`
- `REJECT_RESEARCH_SURFACE`

No `PROMOTE` value is allowed in Analyzer v2 Discovery outputs.

## discovery_candidate_shortlist.csv

One row per candidate surface selected for future formalization review.

Minimum columns:

- `candidate_surface_id`
- `family`
- `side`
- `event_version`
- `feature_predicate_summary`
- `outcome_summary_ref`
- `sample_events`
- `independent_event_days`
- `clean_data_window`
- `recovered_data_usage`
- `degraded_field_flags`
- `known_risks`
- `required_replay_contract`
- `holdout_requirement`
- `status`
- `next_action`

Allowed `status` values:

- `DISCOVERY_REVIEW`
- `NEEDS_REPLAY_SPEC`
- `CONTROL_ONLY`
- `QUARANTINED`
- `REJECTED_DISCOVERY_SURFACE`

Shortlist status is not promotion. A shortlisted discovery surface still needs a separate replayable ruleset contract, replay, holdout, cost stress, source concentration review, and same-bar audit.

## Leakage Rule

The hard boundary is:

- features and events can feed candidate predicates;
- outcomes can feed labels, ranking, and review;
- outcomes cannot feed entry predicates, stop placement, target placement, expiry, or replay activation logic.

Any future candidate whose predicate depends on `forward_return_pct`, `mfe_pct`, `mae_pct`, continuation/reversal labels, or time-to-outcome fields is invalid.
