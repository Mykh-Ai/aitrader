# SHI_RESET_40O — Binance Futures archive source parity before historical OOS

Date:2026-10-15. **Verdict: `BINANCE_KLINE_SURROGATE_PARITY_FAILED`.** Research/validation only. The required source-equivalence gate failed; older OOS data were not downloaded and OOS strategy returns were not computed or inspected. No optimization, variant, strategy rule change, production promotion, deployment, private API, orders, borrowing, Executor/live service change or production-branch merge occurred.

Run root:[SHI_RESET_40O_binance_futures_archive_oos_validation_v0](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0). Starting publication commit:`def5060680b31b6639c39d3e00b061ccf147d4c9`. Dedicated branch:`codex/SHI_RESET_40O_binance_futures_archive_oos_validation_v0`. Final research commit is identified by Git history and the completion report; it is not written self-referentially inside its own content.

## Frozen identity and inspected dependency chain

User-selected40H version:`SHI_RESET_40H_DELTA_FILTER_RESEARCH_V1`, variant **`LONG_DELTA4_POS_BOTH_BAND4`**. Verified both against the selected contract and actual source bytes:

- Rules/filters SHA256:`ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4`.
- Filter manifest SHA256:`32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56`.

Current main includes later production-continuity code identities; it was not silently substituted. The40N reproduction helper recovered immutable0862342 files and existing source inputs into an isolated, untracked local reconstruction. Every executed historical strategy module is checked to reside there. Original13selected spot-control rows and +1090.8118508490645USDC reproduce exactly within serialization tolerance. This is a known-data identity check, not an OOS result. It reuses existing local spot evidence and performs no spot download.

[frozen_identity_verification.json](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/frozen_identity_verification.json) and [code_hashes.csv](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/code_hashes.csv) retain all executed code identities. Core unchanged files:

|Module|SHA256|
|---|---|
|research/strategy_search/features.py|e8a89f29a96097ee7cbba1ae88517b2656422948567addf3249567a395a94cb3|
|research/strategy_search/hybrid.py|44d547d3b732b0fed20514ed0d17ab881223a6400b1cdf4f56f563cbd9b406e0|
|research/strategy_search/replay.py|a48af0986e81c1c36cd159ad3a5003faf9e34dd2abfd43e0f52cab10e0c0b7e8|
|40F/interventions.py|e6a81090662ab4e210201595c2cba5e51b8197b7b5bc28dd54db09306de41949|
|40H/filters.py|ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4|

Inspected chain: official archive→separate normalized minute observations→full prior H1/H4 state→frozen features→frozen hybrid candidates→40F short-space→40H rolling delta gates→pre-book parity→only after acceptance, one frozen book/replay. Exact dependencies/units/clocks are recorded in [data_dependency_contract.md](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/data_dependency_contract.md).

Required market columns are timestamp, OHLC, total base quantity and taker-buy/sell quantities, plus observed/nontraded/quality status. Exact SHI aggTrade-event count versus Binance component-trade count is not a selected strategy input. OI/funding/liquidations are not required; schema placeholders are marked unavailable and do not form filters. No funding charge is introduced.

## Official source acquisition and normalization

The official [Binance Public Data USD-M schema](https://github.com/binance/binance-public-data/blob/master/README.md#futures) and [official archives](https://data.binance.vision/) were inspected. Source:`BTCUSDT`,USD-M Perpetual Futures,1m klines.27ZIPs:dailyMarch11–31 and monthlyApril–September2026, **12,258,259 original ZIP bytes**,293760source rows. Every original ZIP and published `.CHECKSUM` is preserved; all27local SHA256 match official values. Records include URL/path, market/symbol/interval/date, bytes, checksums, rows and first/last original/normalized timestamps.

The default sandbox could not resolve the public host. A necessary user-authorized escalated public-download invocation succeeded; no approval rejection occurred. Initial DNS errors remain in`acquisition_attempt_sandbox.json`; no source error was relabeled as a strategy failure.

Source context after the same first-history/cutoff restriction is **292935 normalized observations**,2026-03-11 13:45 throughSeptember30 23:59UTC. NoMarch1–9 observations were fetched; the older scored interval was not used during normalization. Daily normalized observations retain raw exchange open/close clocks and converted UTC timestamps under`normalized_futures_feed/`.

Mapping:exchange-open+60s→SHI right-close label; observed official USD-M timestamp unit is milliseconds. OHLC rounded2dec; base quantities6dec; BuyQty=taker-buy base volume, SellQty=unrounded total−unrounded buy then quantized. Both original exchange times and normalized labels are retained. No fitted minute shift or data deletion is used to improve parity. Exact trade count equality is not demanded; traded/nontraded equivalence is compared.

## Source parity results

The complete preferred July/September windows were tested outside the known April/May recovered interval. The SHI source nevertheless contains9traded-status discrepancies inJuly and2inSeptember; all are retained. Both full-history states are reconstructed independently from the same declaredMarch11clock start; no chunk/context reset.

|Window|Aligned minute labels|Raw candidates SHI/archive|Final-direction mismatch|Full candidate/gate parity|
|---|---:|---:|---:|---:|
|2026-07-01 00:00–07-31 23:59UTC|44640|8/9|1|99.86559139784946%|
|2026-09-01 00:00–09-30 23:59UTC|43200|6/6|0|100%|
|Combined|87840|14/15|1|99.93169398907104%|

Among the union of actual raw candidates, match rate is8/9=88.888889% inJuly,6/6=100% inSeptember,14/15=93.333333% combined. This denominator is supplied to avoid diluting the failure among many no-signal H1 rows. The required gate is100%, not a rounded99.93% substitute.

No missing/extra minute labels occur, but **72690/87840minutes** differ in price/quantity/status beyond declared tolerance. Raw price tolerance1e-8 after2dec normalization; quantity tolerance1.0001e-6 accounts for independently rounded components, not collector volume loss. Maximum close deviation:July328.40USDT,September256.70; maximum total-base-quantity deviation:6834.639BTC/1269.798BTC. All field counts/maxima and all mismatching rows are preserved.

**16888/61488feature/state comparisons differ**. Compared:closed H1/availability,OHLC/volume/signed delta,EMA24/72/168,ATR,volume ratio,rolling raw4/24delta,prior6/48/96references,decision-close stop estimates,H4 inventory and threshold predicates. Additional exact prior-history/frozen short-reference,H4 levels/availability/space and known-candidate stop/target previews are recorded separately. Stop/target preview inspects only declared entry observation, not future trade returns.

Decisive mismatch:**2026-07-05 08:00UTC**. Archive has a long raw candidate and allows it pre-book; SHI has no raw candidate. SHI's previous96H1 usable requirement fails because the H1 closingJuly2 23:00 omitted3minutes, while archive history is complete. No omission is hidden or patched away. At the same decision rolling24h delta is **SHI+4.077205337% versus archive+3.940742504%**, crossing the frozen+4% boundary as well. Relevant H1 OHLC happen to match at that decision; the earlier state/flow differs.

Collector code accumulates received callbacks without exchange-time bucketing and labels the buffer at UTC flush. This is a mechanism consistent with observed receipt/flush versus archive event-time differences; individual packet losses or arrival delays are not proven without receipt logs. It is not an exact-trade-count or floating-rounding explanation.

Optional aggTrades fallback: **not attempted**. Failure includes OHLC, prior-history quality and H4 inventory, not only taker-buy reconstruction; no claim is made that an untested aggTrades source passes or fails. No alternate source/shift/window/threshold was fitted to rescue the candidate. A separately declared source-semantics investigation may consider archived aggTrades; it must preserve this failure and keep OOS unopened until an accepted source gate.

Evidence:[raw summary](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/raw_parity_summary.json),[all raw mismatches](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/raw_parity_mismatches.csv),[features](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/feature_parity.csv),[candidates](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/candidate_parity.csv),[source diagnosis](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/source_semantics_diagnosis.json),[H4 space](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/H4_space_evidence.csv),[H4 inventory](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/H4_inventory_evidence.csv).

## Causality and phase discipline

Both originalSHI and official-kline states pass real-prefix future-append invariance atJuly15 12:30UTC:3023closed H1 steps per source. Complete features,H4 inventory-derived hashes,raw candidates,gate decisions and blockers are identical before/after append within each source. Rolling windows are `(decision−h,decision]`; last source observation never exceeds decision. Frozen H4 right-side confirmation availability and decision-close risk screen are retained. No detected future leakage.

The [run manifest](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/run_manifest.json) froze all user verdict criteria before archive outcomes:minimum12completed,net>0,PF≥1.25,net excluding best2>0,causality/frozen identity/source gate. One strategy,zero variants,no optimization,one allowed OOS attempt. Tests ensure no OOS access without accepted parity and no second attempt/search. Since parity failed, no acceptance or OOS-attempt marker exists.

## Historical OOS and phase decision

Declared score:**2025-03-01 00:00–2026-03-09 23:59UTC**; predeclared warmup from**2025-02-01**. Neither downloaded nor executed. Every requested OOS count/PnL/PF/drawdown/mean/median/extreme/best1/2/3/concentration/direction/month/frequency/risk/R-distribution metric is **null / NOT_RUN**, not zero. Empty`oos_candidates.csv`,`oos_trades.csv`,`oos_monthly_summary.csv` contain only schemas. [oos_metrics.json](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/oos_metrics.json) explains the gate. There is no OOS concentration or LONG/SHORT/month comparison to make and no pooled performance number with40H/L.

The hypothetical permitted execution model was predeclared **FUTURES_PRICE_PROXY**:3000notional,5USDC-equivalent fee,2bps/fill,one-minute latency,one global book,3mincooldown,stop-first,unchanged10R-long/6R-short/168h. It was not executed. Existing40H13/+1090.81USDC and40L14/+1060.91USDC remain separate exposed-history spot-price evidence.

**Server shadow is not justified as the immediate next validation stage by this task.** Resolve source equivalence first, then run the single untouched OOS contract if accepted. Live remains blocked. ExactBTCUSDC historical execution replay is not the next useful step while the signal-source gate fails; reconsider it after a valid frozen OOS result. This is a source-equivalence failure, not an observed negative or positive OOS strategy return.

## Verification and repository disposition

13new research tests cover clock conversion,buy/sell,traded status,warmup/start/end boundaries,rolling future exclusion,prefix invariance,decision comparison,actual rule identities/hash mutation and hard no-OOS/no-search gates. Targeted regression:**23passed**; full relevant regression:**784passed**,11existing deprecation/future warnings. Existing tests were not weakened. The already-existing own-signal preparation/replay regression files, previously untracked, are included unchanged so the recorded suite can be reproduced after clone. JUnit and final verification are retained under the run root.

All protected source/code hashes,old40D/40H/40L evidence and selection pointers remain unchanged. Only the dedicated research branch,new40O tooling/data/tests/audit and aligned project indexes are intended for commit. The local frozen reconstruction and pytest caches are reproducible support directories, not additional source downloads or published modified versions of old runs. No push or merge to main is performed for40O. [result.md](../../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/result.md) is the concise handoff.
