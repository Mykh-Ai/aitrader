# Promotion Gate Checklist

Candidate: `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`

- [FAIL] >= 25 post-holdout trades. No true post-holdout sample exists.
- [FAIL] >= 10 independent post-holdout trade-days. No true post-holdout sample exists.
- [PASS] positive net after cost stress `0.00015` in sidecar report.
- [PASS] survives cost stress `0.00020` in sidecar report.
- [PASS] no single-day PnL dominance in day-based source concentration report.
- [PASS] source concentration pass in Sprint 02 sidecar day-based report.
- [FAIL] no unresolved same-bar ambiguity. Candidate-level same-bar fields are missing.
- [PASS] execution-observable entry. `ReclaimDepthToImpulseRange > 0.6` is based on setup/impulse state, not future label.
- [FAIL] stop/exit formally defined. Promotion-grade stop/exit contract is not frozen.
- [PASS] no tuning after result inspection. Sprint 02 freezes threshold unchanged.
- [PASS] isolated margin compatible. No cross-margin assumption is required.
- [PASS] no martingale.

Overall: `WAIT / VALIDATE`, no promotion.

