# SHI_RESET_37E Failed Regime Classification Audit

Verdict: 37E_FAILED_REGIME_CLASSIFICATION_AUDIT

Promotion status: DO_NOT_PROMOTE_AS_TRADER_MONITOR

Root cause: ROOT_CAUSE: incorrect feature priority + missing down-regime gate + support fallback masquerading as range

## Scope

This audit covers the SHI_RESET_37E Market Structure State Memory classifier as research infrastructure only.

It does not introduce trading signals, entries, exits, position logic, PnL, Backtester use, Executor use, orders, or live-readiness claims.

## Failure

The current `_classify_state` path treats strong support as primary evidence for range-like states after the one-sided UP and failed-round checks. In expanded bearish windows, the existence of support below price can therefore become `RANGE_ABOVE_SUPPORT`, even when price change, range expansion, close location, and negative delta show seller dominance.

The classifier has an UP / MARKUP priority branch, but no symmetric DOWN / MARKDOWN priority branch before support fallback. This makes the state model asymmetric and lets support context override actual market pressure.

The hidden-flow episode context also remains too thin for regime reading when 1D / 3D / 7D context is reduced to `price_change_pct` only. Range size, close position, and pressure need to participate in the descriptive context read.

## Required Repair Direction

- Add failing regression coverage before classifier changes.
- Add `close_position` to market-structure window metrics and output.
- Add a market pressure / level dominance helper comparing seller pressure, buyer response, overhead supply, underlying demand, dominant side, and range quality.
- Reorder `_classify_state` so DOWN / MARKDOWN and failed-breakout / seller-reclaim evidence are evaluated before support fallback.
- Keep support and resistance as context modifiers, not primary regimes by themselves.
- Demote or replace `RANGE_ABOVE_SUPPORT` so expanded bearish moves cannot classify as range.
- Keep all outputs descriptive and research-only.
