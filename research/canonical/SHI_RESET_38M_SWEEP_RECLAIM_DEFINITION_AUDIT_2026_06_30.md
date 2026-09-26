# SHI_RESET_38M_SWEEP_RECLAIM_DEFINITION_AUDIT

Verdict: RAW_SWEEP_OBSERVATION_ONLY_UNLESS_QUALIFIED

Scope: research-only audit. No Executor, orders, live trading, entries/exits, PnL, position sizing, Backtester execution logic, live-readiness, or strategy promotion were introduced.

## Files Inspected

- `analyzer/README.md`
- `analyzer/swings.py`
- `analyzer/sweeps.py`
- `analyzer/failed_breaks.py`
- `analyzer/events.py`
- `market_monitor/events.py`
- `market_monitor/liquidity_zones.py`
- `market_monitor/setup_builder.py`
- `market_monitor/wider_research_window.py`
- `tests/test_sweeps.py`
- `tests/test_setups.py`
- `tests/test_market_monitor_sweep_unresolved.py`
- `tests/test_market_monitor_sweep_unresolved_evidence.py`
- `tests/test_market_monitor_post_sweep_observation.py`
- `tests/test_wider_research_window.py`

## Current Raw Sweep Definitions

### Legacy Analyzer

`analyzer/swings.py` creates confirmed H1/H4 swing references from strict three-bar pivots:

- swing high: current timeframe high is greater than previous and next timeframe highs
- swing low: current timeframe low is less than previous and next timeframe lows
- delayed confirmation: a swing becomes visible only after the next timeframe candle closes

`analyzer/sweeps.py` then marks a sweep as a strict crossing of the latest confirmed reference:

- H1/H4 upward sweep: `High > latest confirmed swing high price`
- H1/H4 downward sweep: `Low < latest confirmed swing low price`
- equal touch is not a sweep
- synthetic rows cannot trigger a sweep
- only the first cross per unchanged reference lineage is emitted
- ambiguous same-row up/down crosses are suppressed

The analyzer sweep model records penetration amount and a shallow/medium/deep band, but the model version is `v1_observation_only`. It does not require the crossing candle to be a completed H1 candle in the sense of a separate qualified-trigger contract; it works on the rows it receives after swing features have been materialized.

### Legacy Analyzer Failed Break / Reclaim

`analyzer/failed_breaks.py` builds failed-break facts on top of materialized sweep rows:

- a sweep bar creates a pending candidate
- a later bar must close back through the swept level
- upward sweep fails when a later close is below the swept level
- downward sweep fails when a later close is above the swept level
- the sweep bar itself is not retroactively marked as the failed break
- pending candidates expire after `confirmation_bars`
- a large timestamp gap clears pending state

This is a reclaim/failed-break lifecycle model, but it is legacy analyzer code and not active Market Monitor strategy evidence.

### Market Monitor Sweep

`market_monitor/events.py` emits `LIQUIDITY_SWEEP_UNRESOLVED` from zone interaction, not from the legacy analyzer H1/H4 swing sweep model.

The event requires:

- a pre-existing unconsumed zone
- a first cross of the zone far side:
  - BUY_SIDE zone: M1 `HiPrice > zone_outer_upper`
  - SELL_SIDE zone: M1 `LowPrice < zone_outer_lower`
- minimum excursion: `max(10 USD, price_mid * 0.0002)`
- raw data quality
- activity evidence from volume z-score, delta z-score, or nonzero OI change
- no too-wide zone
- no repeated prior cross without a new transition

This Market Monitor event is explicitly unresolved and observational. It does not require a completed H1 candle, H1 wick/body structure, minimum H1 level age, H1 prior reaction, H1 ATR-confirmed penetration, or reclaim close.

## Audit Answers

1. Current code defines sweep as either:
   - legacy analyzer strict crossing of latest confirmed H1/H4 swing high/low, or
   - Market Monitor M1 cross through a visible liquidity zone with minimum excursion and activity evidence.

2. Current code defines reclaim / failed break in the legacy analyzer as a later close back through a swept level within a confirmation window. Market Monitor setup-builder wording such as reclaim / failed bounce is descriptive context derived from raw windows or state labels, not a qualified H1 reclaim detector.

3. Sweep detection is mixed:
   - analyzer sweep references are H1/H4 swings but the sweep is evaluated on the row stream after those features are attached
   - Market Monitor unresolved sweep is evaluated from M1 feed rows against zones
   - setup-builder/wider-classifier use raw hidden-flow windows and state rows, not a dedicated qualified H1 sweep/reclaim event

4. Yes. A tiny penetration over a weak nearby swing can be counted as raw sweep in the analyzer if it is strictly greater/less than the reference. Market Monitor has a small zone excursion threshold, but it can still emit an unresolved raw sweep without the new H1 structural quality contract.

5. Current raw sweep code does not consistently require:
   - completed H1 candle: no dedicated qualified H1 completion requirement
   - minimum level age: no general qualified-age gate
   - minimum reaction from reference level: not in raw sweep
   - minimum penetration beyond tiny noise: analyzer records penetration but does not reject shallow raw sweeps; Market Monitor has a small zone-cross excursion threshold
   - visible volume expansion: Market Monitor unresolved sweep requires activity evidence, but volume expansion is not the H1 quality contract; analyzer does not require it
   - close back below/above swept level: only legacy failed-break does this after raw sweep
   - candle body/wick evidence: not required
   - separation from adjacent candle noise: not in raw sweep beyond swing confirmation and first-cross logic

6. Downstream modules that treat raw sweep as setup evidence:
   - `market_monitor/setup_builder.py` uses raw hidden-flow windows and descriptive `sweep_status` / `reclaim_status` fields for setup candidates.
   - `market_monitor/wider_research_window.py` previously allowed supply sweep/reclaim rows to become policy-eligible from raw setup context without a qualified H1 reclaim flag.
   - Market Monitor research summaries and label-quality modules treat unresolved sweeps as observational artifacts.

7. Downstream modules that treat raw sweep/reclaim as potential entry evidence:
   - `market_monitor/wider_research_window.py` was the main active research layer that could classify setup rows as immediate/policy-eligible candidates.
   - legacy analyzer setup/backtester paths contain failed-break/reclaim setup logic, but they are explicitly legacy/read-only and not active under `AGENTS.md`.

## Required Correction

Raw sweep must be treated as observation-only unless it passes a qualified structural sweep contract.

The 38M correction introduces a separate research-only quality layer:

- `RAW_SWEEP`: raw technical crossing; observation-only
- `QUALIFIED_H1_SWEEP`: completed H1 candle sweep of meaningful H1/H4/structural level with age, reaction, penetration, wick, and measured volume evidence
- `QUALIFIED_H1_FAILED_RECLAIM`: qualified H1 sweep followed by a completed H1 close back through the swept level within the reclaim window
- `ENTRY_TRIGGER_CANDIDATE`: requires qualified failed reclaim / structural retest / rejection after context is already active

`RAW_SWEEP` alone must not set:

- `immediate_entry_valid=true`
- `policy_replay_allowed=true`
- `FAILED_RECLAIM_TRIGGER_CANDIDATE`
- `MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP`

## 38M Implementation Notes

Added:

- `market_monitor/qualified_h1_sweep_reclaim.py`
- `tests/test_qualified_h1_sweep_reclaim.py`

Updated research classifier behavior:

- raw unqualified sweep rows classify as `RAW_SWEEP_OBSERVATION`
- broad `RAW_REGIME_WINDOW_720M` context is no longer automatically `LATE_LAST_WAGON`
- broad context can be overridden by `qualified_h1_failed_reclaim=true`
- `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` requires `qualified_h1_failed_reclaim=true` before it can become `FAILED_RECLAIM_TRIGGER_CANDIDATE`

Historical 38J/38K/38L artifacts were not rewritten by this audit.
