# Candidate Replay Summary

Candidate: `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`
Rule version: `SPRINT03_SHORT_DEEP_RECLAIM_GT_0_6_V1`

## Formal Mapping

- candidate events: 14
- no-lookahead status: `PASS`
- stop model: `REFERENCE_LEVEL_HARD_STOP`
- exit model: `FIXED_R_MULTIPLE:1.5` plus `BARS_AFTER_ACTIVATION:12` expiry
- hard cost gate: `0.00015`
- warning cost gate: `0.00020`

## Cost Stress

- cost `0.00000`: trades=14, net=-0.0002538167, winrate=0.571429, pass_fail=FAIL
- cost `0.00010`: trades=14, net=-0.001653912, winrate=0.5, pass_fail=FAIL
- cost `0.00015`: trades=14, net=-0.0023540122, winrate=0.428571, pass_fail=FAIL
- cost `0.00020`: trades=14, net=-0.0030541475, winrate=0.428571, pass_fail=FAIL

## Source Concentration

- pass_fail: `FAIL`
- independent trade days: 7
- largest day abs result share: 0.409027
- top3 day abs result share: 0.738923

## Same-Bar

- verdict: `PASS`
- ambiguous trades: 1 / 14
- conservative result: -0.0023540122

## Verdict

`REJECT`
