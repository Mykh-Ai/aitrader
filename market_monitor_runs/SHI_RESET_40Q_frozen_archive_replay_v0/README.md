# 40Q — frozen archive replay through October 14 2026

**Older-history result rejects the current candidate on this source:** March 1 2025–March 9 2026, 35 completed trades, 7 wins/28 losses, **−$276.19** net, PF 0.806. The extended full-period gain does not overturn that failure.

The user authorized this source-specific diagnostic after the 40O parity warning, then extended the end to October 14 and requested SHI-month comparisons. Original 40O remains `BINANCE_KLINE_SURROGATE_PARITY_FAILED`; no acceptance record or original OOS result is fabricated. These historical outcomes are now exposed research evidence.

Frozen 40H `LONG_DELTA4_POS_BOTH_BAND4`, no tuning. Rules SHA256 `ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4`; filter manifest `32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56`. The byte-exact original 13-trade spot control reproduces before results. Research adapters change calendar admission and remove unused future first-hour entry summaries; every remaining signal formula/threshold, stop, target and exit is preserved.

Primary **CONTINUOUS_BINANCE**, March 1 2025–October 14 2026: **52 completed / 15 wins / 37 losses / +$701.26** after $260 fees and $62.38 modeled slippage, $3,000 notional per trade. PF 1.393; closed-trade drawdown $662.77. Without best2: **+$16.98**; without best3: **−$271.24**. No open/data-censored rows. This full-history positive includes the already-known 2026 interval and is not a substitute for the failed older-history result.

The matched source books use identical March 11 history initialization, original 40L calendar, and common Binance futures execution prices: Binance signals **14 / +$1,102.42**, SHI signals **14 / +$1,058.30**. Original published 40L spot-price evidence remains separate, 14 / +$1,060.91 USDC. Same counts do not mean same trades: Binance blocks the May 22 SHI short loss −$74.66 via its H4 state and adds a July 5 long loss −$30.54. June 17 also has an extra raw short, rejected by H4. The raw/final decision mismatch count is three; source parity is still failed.

All new financial books are **FUTURES_PRICE_PROXY**, not exact BTCUSDC spot-margin PnL. Fixed assumptions: $3,000 per entry, $5 per completed trade, 2bps adverse slippage per fill, one-minute latency, one position, three-minute cooldown, frozen stop-first collision policy, 10R LONG/6R SHORT targets and 168h expiry. No funding/borrow charge, actual fills or production integration.

- [Compact monthly tables](monthly_comparison.md): all 20 entry months and matched March–October 2026 comparison.
- [Metrics](oos_metrics.json), [primary trade journal](oos_trades.csv), [full monthly CSV](oos_monthly_summary.csv), [source comparison CSV](monthly_source_comparison.csv).
- [Earlier-cutoff journal](older_interval_trades_to_2026_03_09.csv): no post-March9 exits credited.
- [Frozen manifest](run_manifest.json), [causality checks](causality_checks.json), [independent paths](independent_path_checks.json), [verification](verification.json).
- [Canonical audit](../../research/canonical/SHI_RESET_40Q_FROZEN_ARCHIVE_REPLAY_AUDIT_2026_10_15.md).

Sources: 65 checksum-verified official ZIPs, reused from 40O/40P or stored under this run's `official_archives/`. January warm-up is technical: H4 inventory's 30-day age exceeds February's 28 days. Normalization spans January 1 2025 00:01 through October 14 2026 23:59 UTC: 938,879 rows / 652 daily CSVs, zero missing/duplicate labels. 37 official nontraded rows are flagged; 19 are January warm-up, 18 on August 29 2025. All clocks remain exchange-open+60 seconds. No source adaptation was fitted after returns.

Large archive/normalized caches remain local. `run_manifest.json` pins every ZIP URL/path/checksum/size; `normalized_inventory.csv` pins every normalized daily hash. Clone alone does not supply the new bulk cache or the external SHI inputs/frozen reconstruction. Preserve those or reconstruct with the earlier 40N/40O helpers and official source manifests. Do not overwrite any old task manifest.

Offline verification, with those inputs present:

```powershell
python market_monitor_runs/SHI_RESET_40Q_frozen_archive_replay_v0/verify_outputs.py
```

The financial attempt marker prevents another run/search in this folder. 27 targeted and 798 full regression tests pass; 80 entered paths independently verified. Both real-prefix checks preserve full earlier features/H4/candidates/gates/stops. Source equivalence remains unaccepted; server shadow/live are not advanced, and exact spot replay is not the next priority after the older-history failure.
