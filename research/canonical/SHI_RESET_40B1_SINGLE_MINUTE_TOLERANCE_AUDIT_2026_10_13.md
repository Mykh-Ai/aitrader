# SHI RESET 40B1 Single Minute Tolerance

Date: 2026-10-13

Verification completed: 2026-10-14.

User-directed correction: one missing or synthetic minute must not interrupt the experiment; continue with the next real candle. The former single-minute/24-hour quarantine was an assistant-selected preparation assumption and is superseded.

Active contract: `research/own_signal_run/contract_v1.json`.

Run root: `market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/`.

## Changed behavior

- Skip primary synthetic/invalid observations in memory; preserve their original rows, timestamps and hashes in protected source files and the source inventory. Do not invent OHLC/flow or fill a missing candle.
- Aggregate H1/H4 from real observations. Isolated one-minute omissions, including several separated omissions, do not invalidate the bar, the confirming structure window, the prior-volume baseline, or trailing 24-hour entry context. Omitted quantities are not estimated; ordinary market thresholds still use actual observed values.
- Retain the original UTC clock, prior market state, structure inventory, qualified sequences and deduplication. Time is never compressed to close gaps. If the H1 boundary minute is absent, wait for the next real close; record nominal H1 close and actual decision/availability separately. A future candle cannot make that decision available earlier.
- When the planned entry minute is missing/synthetic, use the chronologically next real open after the isolated omission. Recheck stop/target geometry at its actual price and record planned time, actual time and delay. No selection by favorable price is allowed.
- During a trade, skip an isolated unavailable minute and continue on the next real bar rather than censoring the trade or stopping the family book. Preserve real elapsed time for expiry/carry. If expiry falls in the omitted minute, exit at the next real open without crediting a later target touch.
- Record H1/context omissions in candidate/continuity outputs and entry/trade omissions in the admission, trade and summary outputs. Omission annotations do not reject an otherwise valid single-minute case or remove its resolved return.

Consecutive omissions longer than one minute, recovered/unsupported observations and the documented multi-day outage/exclusion remain separate conditions. The user changed isolated-minute handling; this task does not rewrite or silently promote degraded recovery evidence. One minute at an unfinished data tail cannot be filled from unavailable future data; processing resumes when a real observation exists.

## Version and scope

v0 preparation/results remain historical evidence. v1 changes only the user-directed quality/clock handling; family thresholds, structural/exit parameters, evaluation periods, costs, source interval and promotion boundaries are unchanged. Source and code identity are frozen again under a new run root, so changed code cannot silently pass the old preparation hashes.

This is research preparation. No full-feed signal generation, historical financial replay, live behavior, legacy campaign, active Backtester promotion gate, network or source-data edit was performed.

## Verification

Controls cover isolated missing/synthetic rows in state context and level-forming/confirming bars, contaminated synthetic price/volume exclusion, delayed boundary availability without future leakage, uninterrupted trade processing, delayed actual entry open, expiry after an omitted minute, state continuity and separation from consecutive gaps/recovery. Final regression, source/code checks and same-cutoff smoke comparison are recorded in `validation_checks.json` and `PROJECT_LOG.md` after the final check.

Final full regression: **752 passed, 11 existing warnings**, in 58.63 seconds, including **31** research-contract cases. The durable command output is `full_regression_20261014.txt` in the v1 run root; a fresh neutral workspace basetemp was used without deleting existing test directories.

The v1 source/code hashes match their frozen preparation, and all 230 source hashes are identical to v0. Original hypothesis parameters differ only in the version label; the isolated-minute policy is explicitly added. Thirty-five unusable primary rows are skipped in memory. Complete RAW H1 bars remain 4,833; usable closed H1 bars increase to 4,848 with isolated-minute tolerance. No source rows were rewritten.

The same startup diagnostic through March 25 14:00 contains 337 H1 updates and **164** decisions versus v0's 152. Ten candidates pass research signal gates, all demand sweep/reclaim; their family/time/source/sequence evidence keys are preserved from v0. The other two families still have zero admissions in this short diagnostic. Future-append invariance and technical-chunk continuity both pass. This comparison is causal preparation evidence, not a financial result. Full-feed signal generation and historical profitability replay have not been performed.
