# 40C frozen own-feed run completed

2026-10-14. Source interval: March 11-October 12, 2026. Active contract: v1 single-minute skip. Rules and costs unchanged from preparation.

**No profitable family is established after the frozen assumed costs.**

| Family | Distinct trades | Zero costs | Base net | Stress net |
| --- | ---: | ---: | ---: | ---: |
| Demand sweep/reclaim up | 20 | +4.38R | -2.41R | -10.12R |
| Seller-dominance retest down | 1 | -1.00R | -2.03R | -3.21R |
| Supply sweep/reclaim down | 0 | No trades | No trades | No trades |

5,170 H1 updates, 3,741 candidate decision records, 63 gate-passing signals. Thirty-four signals were blocked by an open family trade and eight by actual-entry geometry. Twenty-one trades resolved; zero censored. Sixty-three ledger rows represent those same trades under three cost cases.

Base: fee 5 bps/fill, slippage 2 bps/fill, assumed carry 0.1 bps/hour. Stress: 10/5/0.2. Independent family R books, BTCUSDT feed-price proxy, no account-equity or executable Spot Margin claim.

Demand's base result by period: development -9.41R/13 trades; chronological validation +1.29R/4; later historical validation +5.70R/3. Later samples are small and previously researched. Base overall mean -0.121R/trade, PF 0.862, drawdown 11.24R. Removing the best three trades leaves -10.18R. Fees/slippage/carry consume 6.79R against gross +4.38R.

Three trades skipped one synthetic minute and continued without interruption. No returns were discarded for those omissions. Source hashes, frozen code/rules, clocks, state continuity, entry prices and independent cost arithmetic passed verification. The startup prefix matches the 40B1 smoke exactly.

Detailed audit: `research/canonical/SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md` in the repository.

Current run status and checks: `run_verification.json`. `readiness.json`, `validation_checks.json` and `preparation_manifest.json` are inherited preparation records; their pre-run status is preserved historical evidence. Full trade journal: `financial_proxy_replay/trade_ledger.csv`; net results: `family_overall_results.csv` and `financial_proxy_replay/family_period_results.csv`.
