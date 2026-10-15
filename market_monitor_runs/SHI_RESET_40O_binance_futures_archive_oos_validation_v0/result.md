#40O — Binance futures archive source validation

**BINANCE_KLINE_SURROGATE_PARITY_FAILED**

Frozen40H LONG_DELTA4_POS_BOTH_BAND4 reproduced its original13-trade control exactly.27official BTCUSDT USD-M1m kline archives/checksums from known2026 context were verified.

|Validation window|Raw candidates SHI/archive|Final-direction mismatch|Decision parity|
|---|---:|---:|---:|
|July2026|8 /9|1|99.865591%|
|September2026|6 /6|0|100%|

Across1464H1 decisions: 99.931693989% parity; one mismatch is enough to fail the required100% gate.
July5 08:00UTC: archive permits a long, SHI has no raw candidate. Raw24h delta also differs4.077205337% versus3.940742504%, crossing the selected+4% boundary. Prior-history/H4/price source differences are separately retained; no threshold/source shift fitted.

87,840minute labels align;72,690minutes differ in at least one price/quantity/status field beyond declared rounding tolerance.16,888of61,488feature/state comparisons differ. July9andSeptember2traded-status differences recorded.

Both sources pass real-prefix invariance at July15 12:30UTC with3023closed H1 steps each; all rolling observations end at/before decision. No detected lookahead. No original strategy/code/source changed.

OOS2025-03-01–2026-03-09 and warmup2025-02 remain undownloaded and outcome-unseen. OOS CSVs are empty schemas; all OOS performance metrics are null, not zero. This does not reject or validate the strategy on OOS.

Optional aggTrades fallback was not attempted: the observed failure includes OHLC/quality/prior-history/H4 differences, not solely taker-buy mapping. No claim is made about untested aggTrades parity.

Phase decision: do not advance on this task to server shadow; live remains blocked. Resolve source semantics in a separate declared task before OOS, then decide whether exactBTCUSDC spot replay is warranted. Existing40H/L evidence remains a separate historically selected sample.

Artifacts: run_manifest.json;source_manifest.json;archive_inventory.csv;raw_parity_summary.json;raw_parity_mismatches.csv;feature_parity.csv;candidate_parity.csv;parity_report.md;source_semantics_diagnosis.json;causality_checks.json;frozen_identity_verification.json;oos_metrics.json.
