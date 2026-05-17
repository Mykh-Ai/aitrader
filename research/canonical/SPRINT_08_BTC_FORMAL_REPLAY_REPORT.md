# Sprint 08 BTC Formal Replay Report

managerial_verdict: `BTC_REPLAY_CANDIDATE_SURVIVED`

Sprint 08 formalized and replayed only three selected BTC candidates from Sprint 07. It did not change Sprint 06 predicates, Analyzer v1, Backtester core, CTX holdout, Executor/live, Phase 4, or universe.

No `PROMOTE` was created. Promotion status remains `NO_PROMOTE_HOLDOUT_REQUIRED` for every candidate.

| candidate | trades | days | net_0.00015 | winrate | median | max_dd | same_bar | source | dominance | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| CAND_BTC_EXH_SHORT_24_V1 | 181 | 54 | 0.0842446773 | 0.403315 | -0.0005436309 | -0.0152688594 | 0 | PASS | PASS | REPLAY_PASS_REVIEW |
| CAND_BTC_VWAP_DEV_LONG_60_100200_V1 | 273 | 30 | 0.0926519329 | 0.223443 | -0.0005069957 | -0.0119221437 | 0 | PASS | PASS | REPLAY_PASS_REVIEW |
| CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 | 215 | 31 | 0.1566910586 | 0.255814 | -0.0005417762 | -0.0147033624 | 0 | PASS | PASS | REPLAY_PASS_REVIEW |

## Boundary Confirmation

- no live
- no Executor
- no Phase 4
- no PROMOTE
- no universe change
- no CTX tuning
- no Analyzer v1 contract change
- no Backtester core change
- no future outcomes as entry predicates
