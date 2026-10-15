# SHI_RESET_40L — selected40H chronological continuation through October14

Date:2026-10-15. User instruction: start the replay after the authorized40K data refresh. Run root:`market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/`. Working-tree task; no commit, network, protected-feed write, live/Executor behavior or legacy Backtester activation.

## Frozen scope and clocks

One experiment was declared in`study_manifest.json` before extended financial returns. Keep the entire user-selected40H: long TREND_RETEST/short ACCEPTED_BREAK, short-space1R from decision-close risk and causal confirmed H4 inventory, weighted actual-minute rolling24h delta strictly within(-4%,+4%) for both directions, rolling4h delta>0 for long only, inherited stop/risk/volume/trend/maturity/impulse rules. No40I expansion, no40J mirrored short4h filter, no parameter search.

Only the obsolete October calendar restriction and old entry_end are extended to admit October1–14. March warmup, April outage/recovery, June22–29 and August25–September1 restrictions remain unchanged. BTCUSDT perpetual futures generates signals; BTCUSDC Spot supplies entry/exit prices. Structural/ATR references use the frozen spot/futures close ratio, known no later than decision, with maximum one-minute quote age. Full-position targets remain10R long/6R short;168actual UTC hours to expiry; one global position, one-minute entry latency and three-minute cooldown; same-minute stop/target collision is stop-first. A single missing/synthetic primary minute is skipped while preserving actual time and state. Extended gaps/recovered execution cannot become resolved profit.

An artifact-local precise-entry adapter removes the legacy helper's requirement for another completed H1 after the last closed H1. The observed entry minute must exist with the same RAW/latency rules; no future H1 is manufactured. This changes cutoff handling, not financial thresholds. Tests cover available/unavailable/delayed last-H1 entry, data censor versus normal open tail, future-quote exclusion and calendar retention. Reusable frozen modules are unchanged.

The whole chronology starts March11 13:45UTC, not October1. Updated sources:313093 futures rows across232 read files,313063 RAW spot observations to the common October14 23:59UTC cutoff. Last completed H1 is October14 23:00UTC. Spot's right-close October15 00:00 observation is outside that common cutoff. All five continuity/reset flags are false within the inherited research feature/H4-inventory/book scope; this does not assert full Monitor lifecycle promotion. October1–12 already existed as context;13/14 are newly acquired inputs. This retrospective continuation is not pristine holdout or prospective confirmation.

## Results in USDC

Fixed3000USDC notional per position,5USDC total commission per completed trade,2bps adverse slippage per fill; actual BTC borrowing and executable orderbook fills remain unverified and excluded. Dollar presentation assumes USDC/USD parity.

|Entry cohort|Completed|Wins/losses|Net after assumed fees/slippage|
|---|---:|---:|---:|
|Full history through October14|14|8/6|+1060.907640|
|April–September|12|8/4|+1142.108729|
|October1–14|1|0/1|−29.904211|
|October13–14|0|0/0|0|

Full cash reconciliation:1147.7623318797375 gross−70 fees−16.854691814954485 slippage=1060.9076400647832 net. Long10trades/+648.468581; short4/+412.439059. Closed-trade drawdown74.610063. Mean net75.779117/trade; mean initial risk42.756848 (variable, not a constant dollar R); mean realized net2.176805R. Preset target is10R long/6R short, weighted mean8.857143R. Net excluding the best three trades remains+220.888015; concentration and small sample remain material.

All13 original40H trades and their money paths are unchanged. Extension adds only October3long:decision13:00UTC,entry13:01 at84856.33USDC,stop84185.71176545291,target91562.51234547088. It stops October7 02:02UTC:−23.708952575 gross−5 commission−1.195258209 slippage=−29.904210784 net. Budapest entry15:01, exit04:02. The full result falls from1090.8118508490645 by precisely this loss; the April–September result is unchanged. No losses or displaced entries are hidden.

There are59 raw family candidates,22 pass all pre-book gates,14 enter the global book. October contains7 raw candidates and2 passing all pre-book gates; one enters and the other is blocked while the position is open. Per-candidate reasons are retained in`candidate_book_decisions.csv`. There are no open positions at cutoff and no data-censored trades. Open-tail handling exists and is tested; no hypothetical mark or future expiry contributes to realized net.

## Verification and handoff

-15 targeted tests pass (five new cutoff/calendar tests plus ten existing strategy replay tests).
-All13 frozen control rows reproduce exactly within floating serialization tolerance and remain in the extended ledger.
-Real October12 prefix reconstruction from the full prior feed reproduces features, signal streams, rolling metrics, H4 candidates/rejections and asof quotes without future dependence; pre-October formulas match the original generator.
-All14 closed paths independently pass first-touch, entry clock, stop/target, expiry, commission, slippage, per-trade R and one-global-book checks. Aggregate cash and all candidate admissions independently reconcile.
-All232 source hashes, all original40H artifact hashes, all40K artifact hashes, selected pointer bindings and frozen engine/code identities remain unchanged.

`research/active_own_signal_selection.json` stays byte-for-byte unchanged as the chosen40H rule pointer. `research/latest_own_signal_replay.json` points separately to the new40L journal/result/manifest with hashes; use it for latest executed research trades. Full evidence is in`trade_journal_usdc.csv`,`monthly_entry_results_usdc.csv`,`verification.json`,`final_verification.json`,`artifact_hashes.json`. Next meaningful confirmation requires later completed data with the same rules; actual borrowing/fill evidence and any production promotion remain separate. This run improves period coverage, not an established edge claim.
