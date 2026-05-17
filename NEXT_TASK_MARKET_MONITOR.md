# NEXT TASK: SHI_RESET_02_BUILD_MARKET_STATE_MONITOR_SKELETON

## Goal

Build the first skeleton of the Shi Market State Monitor.

This is not a strategy search task.

This is not a Backtester task.

This is not live trading.

## Required Package

Create:

`market_monitor/`

The package must be separate from old Analyzer v1 setup logic.

## Scope

The skeleton must:

- read the protected raw feed format;
- build `structure_levels.csv`;
- build `liquidity_map.csv`;
- build `event_log.csv`;
- generate `market_summary.md`;
- include tests.

## Hard Boundaries

Do not:

- generate trading signals;
- call Backtester;
- call Executor;
- open Phase 4;
- reuse old candidate thresholds as strategy logic;
- tune failed-break/reclaim parameters;
- write orders or exchange logic.

## Minimum Expected Outputs

For a run over one or more daily feed files, write:

- `market_state_timeline.csv`
- `liquidity_map.csv`
- `structure_levels.csv`
- `volume_delta_state.csv`
- `accumulation_zones.csv`
- `event_log.csv`
- `market_summary.md`

Initial versions may contain partial scaffolding, but schemas must be explicit and deterministic.

## First Tests

Add tests that prove:

- raw feed is read without mutation;
- output schemas exist;
- output rows are deterministic for the same input;
- no trading signal/order/position fields are produced;
- future labels are not required for event generation.

## Reference Spec

Use:

`docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
