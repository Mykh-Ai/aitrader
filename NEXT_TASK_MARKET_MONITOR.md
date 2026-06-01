# NEXT TASK: SHI_RESET_32_VISIBLE_LIQUIDITY_STRUCTURE_MONITOR_V1

## Status

This is the next intended research-infrastructure direction after governance alignment is accepted.

Do not implement it as part of the governance cleanup task.

## Goal

Design and implement a Visible Liquidity Structure Monitor for Market Monitor research outputs.

This is not a strategy search task.

This is not a Backtester task.

This is not live trading.

## Scope

The next accepted direction is research-only visibility into liquidity structure:

- visual overlays;
- consumed/chopped-through level lifecycle;
- pattern-derived liquidity structures;
- missed-case explanation;
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
- calculate PnL.

## Expected Direction

Future implementation should explain what price did around known structure and liquidity zones, including why a case was or was not emitted as an unresolved sweep candidate.

It must remain descriptive research infrastructure. It must not create entries, exits, signals, position sizing, PnL, Backtester verdicts, Executor actions, or live-readiness claims.

## Reference Spec

Use:

`docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
