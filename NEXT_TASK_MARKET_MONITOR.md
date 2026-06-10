# NEXT TASK: SHI_RESET_37D_EPISODE_CONTEXT_CLASSIFIER

## Status

This is the next intended research-infrastructure task after SHI_RESET_37A hidden-flow research and the local SHI_RESET_37C pruning branch.

Do not implement it as part of unrelated cleanup or merge work.

## Goal

Add descriptive episode context for promoted hidden-flow review candidates.

This is not a strategy search task.

This is not a Backtester task.

This is not live trading.

## Scope

The next accepted direction is research-only episode readability:

- carry 1D / 3D / 7D market context into promoted hidden-flow review output;
- classify reviewed episodes descriptively, for example:
  - `PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION`;
  - `RANGE_UPPER_DISTRIBUTION_REJECTION`;
  - `BEAR_MARKET_BOUNCE_REJECTED_AT_BUY_SIDE`;
  - `UNRESOLVED_COMPRESSION_CONTEXT`;
- keep raw `market_regime_windows.csv` available for audit;
- keep future outcome labels audit-only;
- no trading signals;
- no Backtester.

## Hard Boundaries

Do not:

- generate trading signals;
- call Backtester;
- call Executor;
- open Phase 4;
- reuse old candidate thresholds as strategy logic;
- tune failed-break/reclaim parameters;
- write orders or exchange logic;
- infer short/long actions from `SWEEP_REJECTED` or `SWEEP_ACCEPTED`;
- infer buy/sell recommendations from `BUY_SIDE` or `SELL_SIDE` liquidity terms;
- calculate PnL.

## Expected Direction

Future implementation should explain hidden-flow market-reading episodes in context:

- `7D UP` plus `1D DOWN` pullback plus `BUY_SIDE` compression can read as absorbed pullback context.
- `7D RANGE` plus upper `BUY_SIDE` hidden distribution/compression can read as range upper rejection context.
- `7D DOWN` plus local bounce into upper `BUY_SIDE` hidden distribution/compression can read as bearish bounce rejection context.

It must remain descriptive research infrastructure. It must not create entries, exits, signals, position sizing, PnL, Backtester verdicts, Executor actions, or live-readiness claims.

## Current Branch Dependency

Before starting SHI_RESET_37D, decide what to do with:

- branch: `codex/SHI_RESET_37C_prune_hidden_flow_labels_v0`
- commit: `169ecd4 Prune hidden flow review labels`

Accepted options:

- merge 37C first, then branch 37D from updated `main`;
- or intentionally replace 37C with 37D if pruning should be folded into the next branch.

Do not leave the pruning behavior ambiguous.

## Reference Spec

Use:

`docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`

Research log:

`research/canonical/SHI_RESET_37_HIDDEN_FLOW_RESEARCH_LOG_2026_06_10.md`
