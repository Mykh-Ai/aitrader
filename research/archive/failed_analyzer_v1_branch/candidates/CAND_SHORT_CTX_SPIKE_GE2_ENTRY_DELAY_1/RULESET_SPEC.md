# RULESET_SPEC - CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1

## 1. Candidate Identity

- candidate_id: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`
- side: `SHORT`
- timeframe: `H1_H2_CONTEXT_M1_REPLAY`
- rule_version: `SPRINT03_CTX_GE2_ENTRY_DELAY_1_V1`

## 2. Input Files

- candidate_events: `research/candidates/CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1/candidate_events.csv`
- source_sidecar_file: `research/results/short_reclaim_timing_survival_diagnostic_trades_2026-05-03.csv`
- analyzer source: canonical already-seen Analyzer artifacts plus recovered gap Analyzer artifacts.

## 3. Required Features

- `CtxRelVolumeSpike_v1`, `CtxDeltaSpike_v1`, `CtxOISpike_v1`, `CtxLiqSpike_v1`, `CtxWickReclaim_v1`.
- No future/outcome fields such as `H2_Post*`, `TradeReturn*`, `TradePnl`, `ExitTs`, `ExitReason`, `Win*`, `FullFade`, or `NoFade` are allowed as entry predicates.

## 4. Entry Rule

- SHORT reclaim setup with ctx_spike_count >= 2, then apply entry_delay_1.

## 5. Entry Timing

- `SIGNAL_BAR_CLOSE__ENTRY_NEXT_BAR_OPEN`.
- Entry price is next raw bar open after `setup_timestamp`.

## 6. Stop Rule

- Primary stop model: `REFERENCE_LEVEL_HARD_STOP`.
- For SHORT, `stop_price = ReferenceLevel`; invalid when `stop_price <= entry_price`.

## 7. Exit Rule

- Primary target: `FIXED_R_MULTIPLE:1.5`.
- Expiry: `BARS_AFTER_ACTIVATION:12`.
- No target optimization in Sprint 03.

## 8. Same-Bar Policy

- Primary replay: `SAME_BAR_CONSERVATIVE_V0_1`.
- Audit variants: pessimistic stop-wins and optimistic target-wins at cost 0.00015.

## 9. Cost Model

- Cost is applied inside Backtester via round-trip price adjustment.
- Levels: `0.00000`, `0.00010`, `0.00015`, `0.00020`.
- `0.00015` is the hard gate; `0.00020` is the warning stress gate.

## 10. Invalid Conditions

- Missing raw entry bar.
- Missing `ReferenceLevel`.
- Non-positive short risk distance.
- Any future/outcome label in entry predicate.

## 11. No-Tuning Declaration

- No thresholds, stop model, target model, expiry, or entry timing may be changed after inspecting Sprint 03 replay outputs.
- This ruleset is not live and not Phase 4 approved.
