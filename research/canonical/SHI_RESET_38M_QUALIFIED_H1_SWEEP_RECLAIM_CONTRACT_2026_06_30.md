# SHI_RESET_38M_QUALIFIED_H1_SWEEP_RECLAIM_CONTRACT

Status: ACTIVE_RESEARCH_CONTRACT_V0

Scope: research-only quality contract. This contract does not define orders, live execution, entries/exits, PnL, position sizing, Executor behavior, Backtester campaigns, or strategy promotion.

## Taxonomy

### RAW_SWEEP

A raw technical crossing of a previously known swing/reference level.

Examples:

- M1 high crosses above a visible resistance/supply zone.
- M1 low crosses below a visible support/demand zone.
- A row high/low strictly crosses a latest confirmed H1/H4 swing reference.

Contract:

- observation-only
- can support `CONTEXT_ONLY`, `PRE_TRIGGER_CONTEXT`, or `RAW_SWEEP_OBSERVATION`
- cannot by itself create an entry trigger candidate
- cannot by itself set `immediate_entry_valid=true`
- cannot by itself set `policy_replay_allowed=true`

### QUALIFIED_H1_SWEEP

A completed H1 candle sweep of a meaningful H1/H4/structural level.

The level must be meaningful and the sweep must pass minimum level age, prior reaction, penetration, wick/body, and measured-volume quality checks.

### QUALIFIED_H1_FAILED_RECLAIM

A qualified H1 sweep followed by a completed H1 close back through the swept level within the configured reclaim window.

For bearish failed reclaim:

- qualified H1 sweep above resistance/high
- a later completed H1 candle closes back below the swept level
- reclaim close timestamp is after the sweep candle timestamp

For bullish failed reclaim:

- qualified H1 sweep below support/low
- a later completed H1 candle closes back above the swept level
- reclaim close timestamp is after the sweep candle timestamp

### ENTRY_TRIGGER_CANDIDATE

A research-only candidate that occurs after context is already active and after a qualified failed reclaim / structural retest / rejection event is observed.

The entry-candidate timestamp is the confirmation timestamp, not the earlier context timestamp.

## Qualified H1 Sweep Core Conditions

All core conditions must be true.

### 1. Completed H1 Candle

- The sweep must be detected on a completed H1 bar.
- M1 micro-crosses cannot directly become qualified sweeps.
- Incomplete H1 bars cannot qualify.

Output:

- `sweep_h1_completed`

### 2. Meaningful Reference Level

Allowed reference types:

- `H1_SWING_HIGH`
- `H1_SWING_LOW`
- `H4_SWING_HIGH`
- `H4_SWING_LOW`
- `ACTIVE_STRUCTURAL_LIQUIDITY_ZONE`
- `STRUCTURAL_SUPPORT_RESISTANCE_FLIP`

Neighboring candle high/low alone is insufficient.

Output:

- `sweep_reference_level`
- `sweep_reference_type`

### 3. Minimum Level Age / Separation

Default research thresholds:

- `level_age_h1_bars >= 3` after confirmation, or
- `swing_center_to_sweep_distance_h1_bars >= 5`

Constants:

- `MIN_LEVEL_AGE_H1_BARS = 3`
- `MIN_SWING_CENTER_TO_SWEEP_H1_BARS = 5`

Output:

- `level_age_h1_bars`
- `swing_center_to_sweep_distance_h1_bars`

### 4. Prior Reaction Requirement

For swept resistance / high:

- after the reference high formed, price must move down by a meaningful amount before the sweep

For swept support / low:

- after the reference low formed, price must move up by a meaningful amount before the sweep

Default rule:

- `reaction_abs >= max(0.003 * reference_level, 0.25 * ATR_H1_14)`

If ATR is not available:

- reject with `insufficient_reaction_data`
- do not silently pass the reaction gate

Output:

- `reaction_abs`
- `reaction_rel`
- `atr_h1_14`
- `qualified_h1_sweep_reject_reason`

### 5. Minimum Penetration

Default rule:

- `penetration_abs >= max(0.0003 * reference_level, 0.05 * ATR_H1_14)`

If ATR is unavailable:

- use `penetration_rel >= 0.0003` as fallback
- mark fallback usage in `penetration_quality` and `evidence_summary`

Output:

- `penetration_abs`
- `penetration_rel`
- `penetration_quality`

### 6. Sweep Candle Quality

Bearish sweep/reclaim setup:

- H1 high sweeps above the level
- H1 close does not strongly hold above the level
- upper wick is present
- bearish body is a positive quality flag, not a hard v0 requirement

Bullish sweep/reclaim setup:

- H1 low sweeps below the level
- H1 close does not strongly hold below the level
- lower wick is present
- bullish body is a positive quality flag, not a hard v0 requirement

Output:

- `sweep_wick_present`
- `sweep_body_direction`

### 7. Volume Confirmation

Volume is measured but not a mandatory hard reject in v0.

Output:

- `sweep_h1_total_qty`
- `rolling_h1_volume_median_20`
- `sweep_volume_ratio`
- `volume_expansion_flag`

Default quality flag:

- `volume_expansion_flag = sweep_volume_ratio >= 1.3`

## Qualified Failed Reclaim Rules

### Bearish Failed Reclaim

Requirements:

- `QUALIFIED_H1_SWEEP` above a resistance/high level occurred
- within `RECLAIM_WINDOW_H1_BARS = 3`, a completed H1 candle closes back below the swept level
- reclaim close timestamp is after the sweep candle timestamp
- `entry_candidate_ts = reclaim_h1_close_ts`
- stop candidate is sweep high plus buffer, or a structural resistance zone above the sweep when provided by a later resolver

### Bullish Failed Reclaim

Requirements:

- `QUALIFIED_H1_SWEEP` below a support/low level occurred
- within `RECLAIM_WINDOW_H1_BARS = 3`, a completed H1 candle closes back above the swept level
- reclaim close timestamp is after the sweep candle timestamp
- `entry_candidate_ts = reclaim_h1_close_ts`
- stop candidate is sweep low minus buffer, or a structural support zone below the sweep when provided by a later resolver

Output:

- `qualified_h1_failed_reclaim`
- `reclaim_h1_close_ts`
- `reclaim_bar_number_after_sweep`
- `reclaim_close_price`
- `reclaim_direction`
- `entry_candidate_ts`
- `entry_candidate_price`
- `stop_candidate_price`
- `reclaim_reject_reason`

## Downstream Classification Rule

Raw sweep alone can only support:

- `CONTEXT_ONLY`
- `PRE_TRIGGER_CONTEXT`
- `RAW_SWEEP_OBSERVATION`

Entry-candidate roles require qualified evidence:

- `FAILED_RECLAIM_TRIGGER_CANDIDATE` requires `qualified_h1_failed_reclaim=true`
- `MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP` requires `qualified_h1_failed_reclaim=true`
- `STRUCTURAL_RETEST_TRIGGER_CANDIDATE` requires qualified structural retest/rejection evidence in a future layer
- `FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW` can be review-only if it follows a qualified primary trigger

If only raw sweep exists:

- `immediate_entry_valid=false`
- `policy_replay_allowed=false`
- `classification_reason=raw_sweep_not_qualified`

Broad raw windows:

- `RAW_REGIME_WINDOW_720M` / `RAW_REGIME_WINDOW_1440M` do not automatically decide late/entry
- without a qualified local trigger they remain context/pre-trigger
- with a qualified local H1 sweep/reclaim they may be reviewed as primary trigger candidates

## Required Regression Coverage

Covered by focused tests:

- tiny M1 micro-cross does not qualify
- adjacent weak swing does not qualify
- proper bearish H1 sweep qualifies
- bearish failed reclaim qualifies and uses reclaim close timestamp
- stop-before-TP event ordering remains covered by wider replay tests
- 720M broad context does not automatically become late wagon and can be overridden by local qualified H1 evidence
