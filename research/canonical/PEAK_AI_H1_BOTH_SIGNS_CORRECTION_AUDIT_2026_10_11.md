# Peak_Ai H1 both-sign SHORT correction audit

2026-10-11. User clarified the already intended hypothesis: every new raw
DELTA_MAX or DELTA_MIN, independent of numeric sign, may trigger the same
upper-zone / four-hour closed-H1 reclaim SHORT setup. No LONG entries.

The completed v1 run was incomplete for that hypothesis: its engine excluded
DELTA_MIN. Its 210 portfolio trades and -1242.08 USDC result remain valid only
for its positive-only implemented scope, not the full requested hypothesis.
The unrelated earlier raw-v2 LONG/SHORT study must not be presented as evidence
that negative-delta triggers were tested under this H1 rule.

Correction in btc-orderflow-system: research/peak_ai_delta_h1_all_signs,
implementation commit 33f1cd9. Only raw-event admission and research identity
change in the candidate engine. Level selection, geometry, recent-cross rule,
four-hour confirmation, stop, exits and costs remain fixed. Both signs share
pending episodes and one portfolio. Per-sign results attribute the original
trigger, not a new isolated strategy for each sign.

The same unchanged native bounded H1/H4 adapter is used. Its deterministic as-of
queries are parallelized while each query reconstructs the full available zone
lifetime. Candidate state and portfolio run chronologically without partition
resets. Exact reproduction of all original 400 positive-only candidate records
is required before consuming cached queries in the corrected run.

Seven new admission/shared-timer/unchanged-rule checks passed with stdlib unittest.
Historical preparation and both replay cost scenarios are now complete. Output root: market_monitor_runs/PEAK_AI_H1_BOTH_SIGNS_V2/.
No production, protected feed, full-Monitor promotion, or live behavior changes.

## Completed result

226 closed simulated SHORT trades: net -1401.95 USDC. Positive triggers: 151 trades, -995.77 USDC; negative triggers: 75 trades, -406.18 USDC. Both groups negative. Exact original-candidate parity and 34 ledger checks passed. See the run SUMMARY.md and REPORT_UA.md. The sign groups are contributions to one shared portfolio, not standalone filtered strategies. No new promotion is justified.
