# SHI RESET 40B Own Signal Run Preparation

Date: 2026-10-13

Quality-policy succession: the subsequent user-directed 40B1 change removes quality-based blocking for isolated missing/synthetic minutes. This audit preserves the original v0 preparation and results; current rules and verification are in `SHI_RESET_40B1_SINGLE_MINUTE_TOLERANCE_AUDIT_2026_10_13.md` and the v1 run root.

Scope authorized by the user: prepare the own-signal historical run. No full-feed signal-discovery or financial profitability campaign was executed in this task.

Implementation: `research/own_signal_run/`.

Run root: `market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v0/`.

## Prepared experiment

A runnable offline package now freezes three entry hypotheses, source/code identity, causal event clocks, structural risk and exit rules, cost assumptions and historical evaluation periods. It contains preparation, causal smoke, signal-generation and fixed-exit proxy-replay commands. Only preparation and smoke were executed on historical feed; financial replay was exercised with synthetic test fixtures.

This is a new bounded research contract. It does not repair or regenerate the 51 saved 38V rows and does not claim source parity with the old builder. It reuses 37E state/pressure and 38M qualified H1 evidence primitives. It imports no Scout seeds, old Analyzer candidates, 38S rows or outcome-selected shortlist. The 39A architecture remains canonical; its full lifecycle backlog and production setup policy are not promoted.

The three hypotheses are seller-dominance upper retest, upper qualified sweep/reclaim and lower qualified sweep/reclaim. H1/H4 references require complete RAW confirmation bars. Immutable reference IDs include timeframe, original bar, side and price. Availability is the final confirmation bar close. An inventory is retained across chronology; one engine instance also retains prior states, qualified sequences and accepted candidate identities across technical chunks. v0 does not support cross-process resume.

Pressure uses only the trailing 24 closed hours at each H1 decision. Sweep/reclaim uses the same frozen reference and the next 1-3 completed H1 closes. Counter sequences and accepted-break context can block admission. Targets query the complete eligible opposite H1/H4 inventory, not a full-period seven-zone selection. The nearest blocker cannot be skipped for a farther convenient target. Rules, weights and restrictions are fully specified in `research/own_signal_run/README.md` and `contract_v0.json`.

This first experiment has three entry variants, one exit policy and three cost scenarios. Volume expansion >=1.3 and signed delta fraction >=0.04 are frozen entry hypotheses; OI/liquidations are recorded as context rather than claimed entry-policy authority. H1 reference strength 65 cannot satisfy the inherited >=70 overhead-supply criterion on its own; the supply baseline therefore requires an H4 reference. This is recorded explicitly rather than hidden as a research result.

## Fixed execution and costs

Raw feed timestamps are minute-close labels. True closed UTC H1 `(00:00,01:00]` uses labels 00:01 through 01:00. Decision at 01:00, explicit one-minute latency, and entry open at 01:01 use the Open of raw row 01:02. Input availability is validated before that entry. The one-minute latency is a research assumption, not measured execution latency.

The baseline exits the full research trade at frozen structural target, initial stop or elapsed 48-hour expiry. It excludes partial TP1, BE and trailing for this first bounded comparison. Stop/target geometry is checked again against actual entry open. Same-minute collisions resolve stop first. Stops crossed by an opening gap fill at the worse open. Favorable target gaps receive no extra credit. Missing/degraded trade data or unfinished tails are censored and retain no fabricated net R.

Three cost cases: zero diagnostic; assumed 5 bp fee +2 bp slippage per fill +0.1 bp adverse carry per hour; assumed stress 10/5/0.2. Both fills are charged. Fees use slipped notionals, slippage is adverse in either direction, and assumed carry is separately deducted. These are not verified account tariffs, actual funding settlement, or actual margin borrowing.

The numerical market is `BTCUSDT_FEED_PRICE_PROXY`. It cannot establish executable BTC/USDC Spot Margin returns without execution-market data and costs. Output R books are independent per family with one concurrent position per family; combining them does not produce account equity or a portfolio drawdown. No capital allocation, live sizing, Executor behavior or orders are added. Legacy Backtester campaigns/promotion logic remain inactive; the financial component is an isolated research replay.

## Feed inventory

| Measure | Result |
| --- | ---: |
| Primary and recovery source files inspected and hashed | 230 |
| Missing source files | 0 |
| Selected minute rows | 310,213 |
| Missing selected minutes | 2 |
| Recovered minute rows | 19,067 |
| All degraded selected rows | 19,102 |
| Invalid selected rows | 1 |
| Complete RAW H1 bars | 4,833 |

Source interval: `2026-03-11T13:45:00Z -> 2026-10-12T23:59:00Z`. Last complete actual UTC H1 closes at `2026-10-12T23:00:00Z`. The changing October 13 file is excluded.

Gaps: `2026-03-15T09:47:00Z` and `2026-05-18T19:31:00Z`. The invalid synthetic row is `2026-03-15T09:50:00Z`. Source files were not corrected or rewritten. Recovery selection is minute-precise within April 23 17:05-May 6 22:51. Missing recovery is reported as a gap, never replaced by primary outage placeholders. Entrances in the degraded/post-outage exclusion through May 9 are blocked, and any incomplete/degraded trailing 24-hour context blocks entries thereafter. Prior context remains carried.

Development and two chronological historical-validation intervals have explicit 48-hour context-only purges and a final exit tail. Existing history is labelled previously researched/not pristine holdout. No unseen-data claim or automatic parameter search exists.

## Validation and actual task boundary

Eighteen targeted tests exercise real causal code with positive synthetic controls for all three families, delayed confirmation, future-evidence rejection, future-append invariance, chunk continuity, opposing penetration, degraded-flow rejection, stops outside sweeps, strict entry clocks, collision/gap handling, expiry/censoring, cost deduction, source recovery selection and unchanged files.

The startup diagnostic processes the full available prior feed chronologically through `2026-03-25T14:00:00Z`: 337 H1 updates, 152 candidate decisions and 10 candidates passing the research signal gates. All ten are demand sweep/reclaim; seller retest and supply sweep/reclaim have zero admitted candidates in this short startup sample. That restriction is recorded without changing thresholds. Entry-fill admission and profitability were not evaluated on those candidates.

The diagnostic compares the same cutoff with two appended future hours and with two technical chunks; both comparisons produce identical candidate/continuity tables. These are source-causality/continuity checks, not trading-edge evidence. Final regression passed: **739 tests, 11 existing warnings**, in 54.34 seconds with a fresh neutral workspace `--basetemp`. All **18** new targeted tests passed. Frozen source/code hashes match, and RAW buy/sell quantity parity has zero mismatches. Full evidence is in `readiness.json` and `validation_checks.json`. No rule was selected using a financial return.

The first full regression encountered three existing snapshot atomic-rename failures in the sandbox's external temp directory (`WinError 5`). A workspace temp retry passed those but an existing selector text-ban test matched the word `signal` in the temp path. A fresh neutral workspace test directory avoids both environmental path issues without editing production/test governance. Those attempts are retained as verification history.

Preparation/source hashes are deterministic and checked before a later run. Altered frozen contract, code, source file or generated candidate journal aborts the run. Once full signal/replay outputs exist, preparation refuses to overwrite that study directory.

## Next action

After preparation passes, run the frozen signal chronology, then the isolated financial proxy replay. Preserve every family and cost case, including no-trade, negative and censored results. Outputs are candidate decisions/rejections, continuity evidence, entry admission/rejections, trade economics and family-period net results with concentration and sample limitations. A numerical positive result requires subsequent validation; it grants no edge/live/production authority.

The complete commands and assumptions are in `research/own_signal_run/README.md`. Protected feeds, current Monitor implementation and Executor were not edited by 40B. No network, dependency installation, deployment, push, legacy campaign or profitability run occurred.
