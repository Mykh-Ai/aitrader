# CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1 Contract

Status: frozen holdout candidate, `VALIDATE`

## Frozen Definition

- side = `SHORT`
- timeframe = reclaim surface / M1 replay over H1/H2 context
- family = `SHORT reclaim context timing`
- condition = `ctx_spike_count >= 2`
- entry transform = `entry_delay_1`
- entry logic = shift original setup entry forward by one raw bar, keep original context slice unchanged
- current source = diagnostic replay experiment, not official Phase 4 mapping
- risk/exits = inherited baseline replay exit; not promotion-frozen yet

## Lock Rules

- status = `frozen`
- do not change `ctx_spike_count >= 2`
- do not change `entry_delay_1`
- do not test `entry_delay_2` as a replacement after inspecting this result
- do not add new filters before true holdout
- no live trading

## Current Evidence

- Diagnostic slice: 191 trades, 34 trade-days.
- Cost stress sidecar result:
  - `0.00000`: PASS
  - `0.00010`: PASS
  - `0.00015`: PASS
  - `0.00020`: FAIL
- Source concentration report passes day-based Sprint 02 threshold.
- True future holdout is missing.

## Required Next Replay

1. Split a true holdout using only future clean days.
2. Replay the frozen `ctx_spike_count >= 2` + `entry_delay_1` contract unchanged.
3. Repeat cost stress at `0.00000`, `0.00010`, `0.00015`, `0.00020`.
4. Add source concentration and same-bar ambiguity reports from the replay engine.
5. Do not tune based on holdout result.

## Promotion Status

No promotion. This candidate is `WAIT / VALIDATE`.

