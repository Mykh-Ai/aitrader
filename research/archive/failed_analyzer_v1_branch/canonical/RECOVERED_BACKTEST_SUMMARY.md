# RECOVERED_BACKTEST_SUMMARY

Date: 2026-05-16

## Scope

- Source Analyzer run: `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`
- Source raw feed: explicit `raw_path=feed_recovered/YYYY-MM-DD.csv`
- Backtest output dir: `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`
- Ruleset source mode: `SHORTLIST_FIRST`
- Variant: `BASE`
- Cost model used: `COST_MODEL_ZERO_SKELETON_ONLY`
- Same-bar policy: `SAME_BAR_CONSERVATIVE_V0_1`
- Replay semantics: `REPLAY_V0_1`

## Result

| Metric | Value |
|---|---:|
| Analyzer artifact days replayed | 14 |
| Replay run dirs with `backtest_trades.csv` | 27 |
| Nonzero-trade replay dirs | 13 |
| Rulesets replayed | 27 |
| Trades | 154 |
| Independent trade days | 13 |
| Validation rows | 67 |
| Validation `FAIL` | 67 |
| Promotion rows | 67 |
| Promotion `REJECT` | 67 |
| Promotion `PROMOTE` | 0 |

## Exit Summary

| Exit category | Count |
|---|---:|
| `TARGET` | 83 |
| `STOP` | 67 |
| `EXPIRY` | 4 |

## Source Concentration

| Status | Rows |
|---|---:|
| `FAIL` | 39 |
| `NOT_EVALUATED` | 28 |

Source concentration remains a hard blocker for promotion. The recovered rerun produced clean replay evidence, but it did not produce a promotable ruleset.

## Same-Bar Ambiguity

All 154 recovered replay trades carry `SAME_BAR_CONSERVATIVE_V0_1`. The official recovered output does not expose a per-candidate same-bar collision count column. Treat same-bar ambiguity as policy-handled for aggregate replay, not as candidate-level promotion evidence.

## Errors / Notes

- Initial replay attempt without explicit `raw_path` failed because Analyzer manifest relative feed paths resolved under each artifact dir. No market evidence was produced by that failed attempt.
- Final replay with explicit `raw_path=feed_recovered/YYYY-MM-DD.csv` completed successfully for all 14 recovered Analyzer artifact dirs.
- Cost model is still zero skeleton. Candidate-level fee/slippage/spread stress is recorded separately under `research/candidates/<candidate_id>/cost_stress_summary.csv`.

## Verdict

Recovered Backtester rerun confirms clean replay mechanics over recovered Analyzer artifacts. It confirms `0 PROMOTE` and `67 REJECT` for the recovered gap aggregate replay. No execution-ready strategy exists.

