# Holdout Feed Audit

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`
Freeze commit: `23d1cc3`
Freeze timestamp: `2026-05-17T11:12:14.334104+00:00`
Feed root: `feed`
Verdict: `WAIT_NO_HOLDOUT_DATA`

## Rule

- Analyze only completed UTC days after the Sprint 03 freeze timestamp.
- A usable day requires rows >= 1000, synthetic_pct <= 5, zero_ohlc_rows = 0, volume_sum > 0, and near-full UTC coverage.
- `feed/2026-05-17.csv` single synthetic zero row, if present from the zip state, is invalid holdout evidence.

## Rows

No local feed files at or after the freeze day were found.

## First Usable Day

`NONE`

Do not run holdout replay while verdict is `WAIT_NO_HOLDOUT_DATA`.
