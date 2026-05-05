# LOCAL H4 Reclaim Buffer50 R-Size And R-Expansion Expectancy Audit

Date: 2026-05-05

Status: diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.

Input: `research/results/local_h4_reclaim_sweep_extreme_stop_v1_buffer50_2026-05-05.csv`. MFE is measured over the 96h path window before first stop touch, or full 96h if stop is not touched. This does not run the Backtester and does not run the old `FAILED_BREAK_RECLAIM` detector.

## Direct Answers

- 1. High R-multiple results are partly meaningful in dollars: 2 rows reached >=5R before stop, with median MFE_usd 5475.0 and median net_MFE_usd 5337.1. The strongest rows are not only tiny-risk artifacts, but row-level clustering still matters.
- 2. Small-R trades are not only noise in this sample: 1/6 rows in <=500 risk bands reached >=5R before stop. None are ultra-small <150 risk rows; the useful small-R band here is mainly 300-500.
- 3. Large-R trades look weak unless they expand beyond 3R: 9/9 high-risk rows stayed below 3R MFE, and rejected >1500 risk rows remain especially poor candidates for this fixed-risk diagnostic.
- 4. The 0.2% round-trip proxy is material: median fee_as_R is 0.1850R overall, much harsher for high-risk/low-expansion rows in net_R terms. Median net_MFE_R is 1.4398; median net_MFE_usd is 1036.6.
- 5. Best exemplars are rows with both high net_MFE_R and meaningful net_MFE_usd. Misleading rows are high-MFE_R but low-dollar or clustered rows, plus large-risk rows that only reach 1.5R/2R or fail the risk gate.

## By Direction

| direction | candidate_count | allowed_count | median_risk | median_MFE_R | median_MFE_usd | median_fee_as_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 13.0 | 12.0 | 760.2 | 2.2114 | 1681.1 | 0.1897 | 2.0217 | 9.0 | 8.0 | 6.0 | 2.0 | 1.0 |
| SHORT | 13.0 | 11.0 | 810.0 | 1.1988 | 915.1 | 0.1803 | 0.8232 | 5.0 | 4.0 | 1.0 | 0.0 | 0.0 |

## By Level Family

| level_family | candidate_count | allowed_count | median_risk | median_MFE_R | median_MFE_usd | median_fee_as_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOCAL_HIGHER_LOW_SWEEP | 13.0 | 12.0 | 760.2 | 2.2114 | 1681.1 | 0.1897 | 2.0217 | 9.0 | 8.0 | 6.0 | 2.0 | 1.0 |
| LOCAL_LOWER_HIGH_SWEEP | 7.0 | 7.0 | 622.3 | 1.7291 | 1022.1 | 0.24 | 1.395 | 4.0 | 3.0 | 0.0 | 0.0 | 0.0 |
| MAIN_STRUCTURAL_HIGH_SWEEP | 6.0 | 4.0 | 1075.35 | 0.5962 | 690.3 | 0.1437 | 0.513 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 |

## By Risk Band

| risk_band | candidate_count | allowed_count | median_risk | median_MFE_R | median_MFE_usd | median_fee_as_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R_1000_1500 | 6.0 | 6.0 | 1214.1 | 0.9835 | 1130.1 | 0.1204 | 0.8605 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| R_150_300 | 1.0 | 1.0 | 291.8 | 2.2077 | 644.2 | 0.5179 | 1.6898 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| R_300_500 | 5.0 | 5.0 | 408.6 | 1.7291 | 687.2 | 0.334 | 1.395 | 3.0 | 2.0 | 1.0 | 1.0 | 1.0 |
| R_500_1000 | 11.0 | 11.0 | 756.0 | 3.1546 | 2555.2 | 0.1962 | 2.9743 | 9.0 | 8.0 | 6.0 | 1.0 | 0.0 |
| R_GT_1500 | 3.0 | 0.0 | 1874.6 | 0.4849 | 915.1 | 0.0836 | 0.4063 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## By Expansion Band

| expansion_band | candidate_count | allowed_count | median_risk | median_MFE_R | median_MFE_usd | median_fee_as_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAILED_BEFORE_1R | 12.0 | 9.0 | 1158.5 | 0.4931 | 460.35 | 0.1229 | 0.3193 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| HIT_10R | 1.0 | 1.0 | 447.2 | 13.1614 | 5885.8 | 0.2995 | 12.8619 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| HIT_1_5R | 2.0 | 2.0 | 582.3 | 1.7049 | 988.55 | 0.2651 | 1.4398 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| HIT_2R | 5.0 | 5.0 | 622.3 | 2.2077 | 1410.9 | 0.24 | 1.952 | 5.0 | 5.0 | 0.0 | 0.0 | 0.0 |
| HIT_3R | 5.0 | 5.0 | 812.0 | 3.2104 | 2828.4 | 0.1643 | 3.0552 | 5.0 | 5.0 | 5.0 | 0.0 | 0.0 |
| HIT_5R | 1.0 | 1.0 | 536.6 | 9.4376 | 5064.2 | 0.2644 | 9.1731 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |

## By Combined Class

| combined_class | candidate_count | allowed_count | median_risk | median_MFE_R | median_MFE_usd | median_fee_as_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_R_LOW_EXPANSION | 18.0 | 15.0 | 919.05 | 0.9835 | 810.8 | 0.1571 | 0.7601 | 6.0 | 4.0 | 0.0 | 0.0 | 0.0 |
| LOW_R_LOW_EXPANSION | 1.0 | 1.0 | 291.8 | 2.2077 | 644.2 | 0.5179 | 1.6898 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| MID_R_GOOD_EXPANSION | 7.0 | 7.0 | 810.0 | 4.8324 | 3155.8 | 0.1803 | 4.6934 | 7.0 | 7.0 | 7.0 | 2.0 | 1.0 |

## Best Exemplars

| row_number | direction | level_family | risk_band | final_risk_usd | MFE_R | MFE_usd | fee_as_R | net_MFE_R | net_MFE_usd | expansion_band | combined_class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_300_500 | 447.2 | 13.1614 | 5885.8 | 0.2995 | 12.8619 | 5751.8546 | HIT_10R | MID_R_GOOD_EXPANSION |
| 17.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_500_1000 | 536.6 | 9.4376 | 5064.2 | 0.2644 | 9.1731 | 4922.3104 | HIT_5R | MID_R_GOOD_EXPANSION |
| 11.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_500_1000 | 567.0 | 4.9884 | 2828.4 | 0.2502 | 4.7381 | 2686.51 | HIT_3R | MID_R_GOOD_EXPANSION |
| 10.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_500_1000 | 992.8 | 4.8324 | 4797.6 | 0.139 | 4.6934 | 4659.6484 | HIT_3R | MID_R_GOOD_EXPANSION |
| 25.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_500_1000 | 983.0 | 3.2104 | 3155.8 | 0.1552 | 3.0552 | 3003.2236 | HIT_3R | MID_R_GOOD_EXPANSION |
| 3.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_500_1000 | 812.0 | 3.1872 | 2588.0 | 0.1643 | 3.0229 | 2454.6 | HIT_3R | MID_R_GOOD_EXPANSION |

## Potentially Misleading High-R Rows

_No rows._

## Small-R High Expansion Rows

| row_number | direction | level_family | risk_band | final_risk_usd | MFE_R | MFE_usd | net_MFE_usd | combined_class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_300_500 | 447.2 | 13.1614 | 5885.8 | 5751.8546 | MID_R_GOOD_EXPANSION |

## Large-R Low Expansion Rows

| row_number | direction | level_family | risk_band | final_risk_usd | MFE_R | MFE_usd | net_MFE_usd | combined_class | no_trade_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19.0 | SHORT | MAIN_STRUCTURAL_HIGH_SWEEP | R_GT_1500 | 1887.1 | 0.4849 | 915.1 | 766.7562 | HIGH_R_LOW_EXPANSION | sweep_extreme_risk_too_large |
| 26.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_GT_1500 | 1874.6 | 0.0734 | 137.6 | -19.0584 | HIGH_R_LOW_EXPANSION | sweep_extreme_risk_too_large |
| 9.0 | SHORT | MAIN_STRUCTURAL_HIGH_SWEEP | R_GT_1500 | 1564.5 | 0.7076 | 1107.0 | 969.364 | HIGH_R_LOW_EXPANSION | sweep_extreme_risk_too_large |
| 12.0 | SHORT | MAIN_STRUCTURAL_HIGH_SWEEP | R_1000_1500 | 1340.7 | 0.3395 | 455.2 | 311.5254 | HIGH_R_LOW_EXPANSION |  |
| 24.0 | SHORT | LOCAL_LOWER_HIGH_SWEEP | R_1000_1500 | 1249.0 | 0.8183 | 1022.1 | 870.5 | HIGH_R_LOW_EXPANSION |  |
| 15.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_1000_1500 | 1233.9 | 0.0105 | 13.0 | -134.2716 | HIGH_R_LOW_EXPANSION |  |
| 5.0 | SHORT | LOCAL_LOWER_HIGH_SWEEP | R_1000_1500 | 1194.3 | 2.0661 | 2467.6 | 2331.3126 | HIGH_R_LOW_EXPANSION |  |
| 2.0 | SHORT | LOCAL_LOWER_HIGH_SWEEP | R_1000_1500 | 1083.1 | 1.298 | 1405.9 | 1271.2122 | HIGH_R_LOW_EXPANSION |  |
| 1.0 | LONG | LOCAL_HIGHER_LOW_SWEEP | R_1000_1500 | 1077.9 | 1.1486 | 1238.1 | 1103.8222 | HIGH_R_LOW_EXPANSION |  |

## Files

- Detail CSV: `research/results/local_h4_reclaim_buffer50_r_size_expansion_expectancy_audit_2026-05-05.csv`
- Report: `research/findings/LOCAL_H4_RECLAIM_BUFFER50_R_SIZE_EXPANSION_EXPECTANCY_AUDIT_2026-05-05.md`
