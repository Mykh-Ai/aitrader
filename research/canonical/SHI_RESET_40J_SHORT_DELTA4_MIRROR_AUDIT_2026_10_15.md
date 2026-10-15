# SHI_RESET_40J — user-directed short4h-delta mirror

Date:2026-10-15. The user explicitly requested testing the natural mirror of longdelta4>0 on shorts. Run root:`market_monitor_runs/SHI_RESET_40J_short_delta4_mirror_v0/`. User-selected40H remains the exact control;40I is not included.

`study_manifest.json` freezes two variants before their financial returns:control40H and the same contract plus **short weighted rolling4h futures delta strictly<0**. Zero/unavailable/nonfinite/unusable4h evidence rejects affected short candidates. The inherited24h strict(-4%,+4%) band and long4h>0 remain. No zero-tolerance fitting or other parameter search follows the result.

Read-only `study.load` verifies original230 source identities/code,40G spot CSV and quote mapping. All52 original candidate delta metrics are recomputed from closed raw observations and reconcile with frozen40H. Both streams inherit the full causal short-space1R screen, original entry families, fixed SL/TP6R-short/10R-long,168h expiry, one-minute latency,3minute cooldown and one global position. Full prior context/H4 state carried forward without resets; isolated omissions continue on next real observation with actualUTC. This is not a full Monitor lifecycle promotion or activation of legacy Backtester gates.

## Results

Control reproduces all13 frozen40H rows:8positive/5negative,1090.811851USDC net;12 April–September entries/1142.108729. Mirror gives12observed rows:7positive/5negative, **703.627513USDC** net;11 April–September entries/**754.924391USDC**. Closed-trade DD remains74.610063. Long9/+678.372792 unchanged; shorts4→3 and412.439059→25.254721USDC. No censors or inferred fills in either run; six spot omissions in each are retained.

Only one actual baseline trade is removed:June1 15:01UTC short, signal_index1969, rolling4h delta+0.040804%, net387.184338USDC. It reaches its original6R target on June4 01:56UTC. Its tiny positive4h delta fails the strict mirror despite passing the original accepted-break/negative24h-pressure entry. No original losing trade is removed and no newly admitted entry appears anywhere in the complete replay. Exact reconciliation:1090.811851−387.184338=703.627513. The25 original short candidates contain5 inherited40H-eligible decisions before occupancy; mirror leaves4, with executed shorts4→3.

Remaining executed short delta4/net pairs:May22−10.148044%/−74.610063USDC;May27−9.339464%/+153.000513;September8−8.340748%/−53.135729. Therefore there is no stop-avoidance benefit in this sample. This rejects this additional rule for selected40H; it does not prove that symmetry never works in another family or interval.

Costs unchanged:3000USDC notional,5USDC per completed trade,2bps/fill adverse slippage. Mirror gross778.165608−60fees−14.538095slip=703.627513. Mean net58.635626USDC/2.152497R; mean initial risk42.444665; without bestthree74.326664. Dollar display assumesUSDC/USD parity. Actual BTC borrowing/orderbook execution unverified and excluded; futures funding remains signal evidence rather than a spot charge. This history is exposed/adaptive, not a pristine holdout.

## Verification and decision

13tests passed in0.71s:three new strict-boundary/side-scope/unavailable/prefix cases plus ten original replay contracts. All25 paths independently checked against actual spot candles for entry open, first stop/target/expiry touch, stop priority, gaps/omissions, global book, available basis quotes and independent net/fee/slip/risk/R/target arithmetic. All52 candidate delta4/24 metrics match the frozen table. Real history through July22 17:30UTC independently rebuilds inherited H4 admission/features and proves both streams/new metrics prefix-invariant. Source and frozen40H code/artifact/selected-pointer identities unchanged. Full regression unnecessary for isolated run-artifact logic.

Decision:do not add shortdelta4<0 to40H. Preserve `research/active_own_signal_selection.json` byte-for-byte. New run CSV/JSON/MD retains both portfolios, candidate screens, the removed winner and exact attribution. Next remains fixed-rule confirmation of selected40H on genuinely subsequent data. No production/live/Executor/order/sizing behavior, protected data, dependency/network/remote action, push or commit changed.
