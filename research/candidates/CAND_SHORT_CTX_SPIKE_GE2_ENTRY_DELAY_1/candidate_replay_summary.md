# Candidate Replay Summary

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`
Rule version: `SPRINT03_CTX_GE2_ENTRY_DELAY_1_V1`

## Formal Mapping

- candidate events: 301
- no-lookahead status: `PASS`
- stop model: `REFERENCE_LEVEL_HARD_STOP`
- exit model: `FIXED_R_MULTIPLE:1.5` plus `BARS_AFTER_ACTIVATION:12` expiry
- hard cost gate: `0.00015`
- warning cost gate: `0.00020`

## Cost Stress

- cost `0.00000`: trades=301, net=0.0575368599, winrate=0.598007, pass_fail=PASS
- cost `0.00010`: trades=301, net=0.0274411088, winrate=0.528239, pass_fail=PASS
- cost `0.00015`: trades=301, net=0.0123921046, winrate=0.498339, pass_fail=PASS
- cost `0.00020`: trades=301, net=-0.0026576521, winrate=0.445183, pass_fail=FAIL

## Source Concentration

- pass_fail: `PASS`
- independent trade days: 61
- largest day abs result share: 0.056238
- top3 day abs result share: 0.149102

## Same-Bar

- verdict: `WAIT`
- ambiguous trades: 40 / 301
- conservative result: 0.0123921046

## Verdict

`WAIT`
