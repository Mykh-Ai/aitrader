# CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6 Contract

Status: frozen research candidate, `WAIT / VALIDATE`

## Frozen Definition

- side = `SHORT`
- timeframe = `H2`
- family = `H2 impulse fade / reclaim`
- condition = `ReclaimDepthToImpulseRange > 0.6`
- entry logic = short after upward impulse reclaim with deep reclaim depth already observable at setup/entry decision time
- current source = sidecar diagnostic slice, not official Phase 4 mapping
- risk/exits = not promotion-frozen yet

## Lock Rules

- status = `frozen`
- no tuning before holdout
- do not lower `0.6` to improve result
- do not add a new filter after inspecting this result
- do not convert `H2_Post12Label_v1` into an entry predicate; it remains diagnostic label evidence only
- no live trading

## Current Evidence

- Diagnostic threshold slice: 34 trades, 16 trade-days.
- Diagnostic gross result on return basis: `0.0077161351`.
- Cost stress remains positive through `0.00020` in sidecar report, but this is not a formal promotion pass.
- Day-based source concentration report passes the Sprint 02 threshold, while prior trade-level PnL concentration remains a weakness.
- True forward holdout is missing.

## Required Next Replay

1. Build a formal candidate mapping or dedicated deterministic replay script that materializes this exact frozen condition.
2. Run recovered-gap replay from `feed_recovered/` only.
3. Run pooled replay over clean pre-gap + recovered gap + clean post-gap.
4. Preserve the `>0.6` threshold unchanged.
5. Add official source concentration and same-bar ambiguity outputs.

## Promotion Status

No promotion. This candidate is `WAIT / VALIDATE`.

