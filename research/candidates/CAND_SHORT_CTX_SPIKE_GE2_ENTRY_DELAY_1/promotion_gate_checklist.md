# Promotion Gate Checklist

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`

- [FAIL] >= 25 post-holdout trades. True future holdout is missing.
- [FAIL] >= 10 independent post-holdout trade-days. True future holdout is missing.
- [PASS] positive net after cost stress `0.00015` in sidecar report.
- [FAIL] survives cost stress `0.00020` or fails transparently. It fails transparently at `0.00020`.
- [PASS] no single-day PnL dominance in day-based source concentration report.
- [PASS] source concentration pass in Sprint 02 sidecar day-based report.
- [FAIL] no unresolved same-bar ambiguity. Candidate-level same-bar fields are missing.
- [PASS] execution-observable entry. `entry_delay_1` is observable and deterministic.
- [FAIL] stop/exit formally defined. Promotion-grade stop/exit contract is not frozen.
- [PASS] no tuning after result inspection. Sprint 02 freezes `ctx_spike_count >= 2` and `entry_delay_1`.
- [PASS] isolated margin compatible. No cross-margin assumption is required.
- [PASS] no martingale.

Overall: `WAIT / VALIDATE`, no promotion.

