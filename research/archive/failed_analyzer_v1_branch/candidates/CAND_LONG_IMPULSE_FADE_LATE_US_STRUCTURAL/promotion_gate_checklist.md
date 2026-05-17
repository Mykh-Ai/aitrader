# Promotion Gate Checklist

Candidate: `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL`

- [FAIL] >= 25 post-holdout trades. Current sample is 20 rows, 19 resolved returns, and not a true holdout.
- [FAIL] >= 10 independent post-holdout trade-days. Post-recovery/forward evidence is below gate.
- [PASS] positive net after cost stress `0.00015` in sidecar report, based on 19 resolved return rows.
- [PASS] survives cost stress `0.00020` in sidecar report, based on 19 resolved return rows.
- [PASS] no single-day PnL dominance in day-based source concentration report.
- [PASS] source concentration pass in Sprint 02 sidecar day-based report.
- [FAIL] no unresolved same-bar ambiguity. Candidate-level same-bar fields are missing.
- [PASS] execution-observable entry. Selector uses observable setup/session/impulse fields.
- [FAIL] stop/exit formally defined. Promotion-grade stop/exit contract is not frozen.
- [PASS] no tuning after result inspection. Sprint 02 freezes watch selector unchanged.
- [PASS] isolated margin compatible. No cross-margin assumption is required.
- [PASS] no martingale.

Overall: `WATCH`, no promotion.

