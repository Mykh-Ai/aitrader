# Sprint 09 Replay Integrity Report

managerial_verdict: `BTC_REPLAY_SURVIVORS_WARN_ONLY`

No live, no Executor, no Phase 4, no PROMOTE, no parameter tuning, no stop/target/expiry changes.

| candidate | status | net_0.00015 | winrate | median | top5 contribution | pnl without top5 net .00015 | rolling | mapper | outlier |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| CAND_BTC_EXH_SHORT_24_V1 | INTEGRITY_WARN_HOLDOUT_REQUIRED | 0.0842446773 | 0.403315 | -0.0005436309 | 0.421710 | 0.0380184434 | PASS | PASS | PASS |
| CAND_BTC_VWAP_DEV_LONG_60_100200_V1 | INTEGRITY_WARN_HOLDOUT_REQUIRED | 0.0926519329 | 0.223443 | -0.0005069957 | 0.515206 | 0.0245694502 | PASS | PASS | WARN |
| CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 | INTEGRITY_WARN_HOLDOUT_REQUIRED | 0.1566910586 | 0.255814 | -0.0005417762 | 0.363019 | 0.0888518598 | PASS | PASS | PASS |

## Managerial Answers

1. Strongest candidate: `CAND_BTC_VWAP_DEV_SHORT_60_100200_V1` by net result at cost 0.00015.
2. Most fragile candidate: `CAND_BTC_VWAP_DEV_LONG_60_100200_V1` by top-5 contribution.
3. Viable for true holdout: `CAND_BTC_EXH_SHORT_24_V1, CAND_BTC_VWAP_DEV_LONG_60_100200_V1, CAND_BTC_VWAP_DEV_SHORT_60_100200_V1`.
4. Positive results are not clean integrity passes: all candidates have negative median trades and high outlier contribution, but top-5 removal remains positive at cost 0.00015.
5. Negative median / low winrate appears to be asymmetric payoff behavior, not immediately fatal, but it requires holdout confirmation.
6. Sprint 10 may start true holdout only for survivors, with WARN status visible.
7. Immediate rejects: `NONE`.

## Path Notes

`research/results/sprint_08_replay_summary.csv` was not present; Sprint 09 used the committed `backtest_runs/sprint_08_btc_formal_replay/sprint_08_replay_summary.csv`.
