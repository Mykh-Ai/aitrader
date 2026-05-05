# FAILED_BREAK_RECLAIM_H4_EXTENDED_V1 Reconciliation Audit - 2026-05-04

Scope: reconcile the earlier H4 forensic/backtester metrics with `failed_break_reclaim_h4_extended_v1_entry_review_2026-03-30_to_2026-05-02.csv`. This is an audit only. No strategy logic, Analyzer behavior, Backtester behavior, or optimization was changed.

## Conclusion

**A) The previous positive H4 backtester/forensic arithmetic is confirmed, and the entry-review CSV is not the artifact that produced those TP/SL, NetR, or MFE figures.**

Important boundary: this does **not** create a new edge claim and does **not** override the manual visual rejection. The current `entry_review` CSV uses blank `outcome` cells for manual-review candidates. Those blanks are not backtester ledger outcomes, not Analyzer reject reasons, and not stop-model-specific results.

## Source Of Claimed Figures

- `REFERENCE_LEVEL_HARD_STOP`: Trades `37`, TP `23`, SL `14`, NetR `20.5`, MeanR `0.554054`, SameBarExit `13`, SameBarCollision `9`.
- `SWEEP_EXTREME_HARD_STOP`: Trades `37`, TP `22`, SL `15`, NetR `18.0`, MeanR `0.486486`, SameBarExit `2`, SameBarCollision `0`.

Exact source files for these figures:
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_summary.csv`: direct source for `37`, `23 TP / 14 SL`, `NetR 20.5`, `22 TP / 15 SL`, `NetR 18.0`.
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_by_source_tf.csv`: cross-check by SourceTF and expiry; H4 rows show the same 37 counts across listed expiries.
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_all_trades.csv`: per-trade ledger source used below, filtered to `SourceTF=H4` and representative expiry `BARS_AFTER_ACTIVATION:4320`.
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_research_report.md`: narrative H4 forensic report that summarized those CSVs.

## Source Of MFE Figures

- `REFERENCE_LEVEL_HARD_STOP`: MFE_R>=3 `37/37` (1.0), MFE_R>=5 `36/37` (0.972973), MFE_R>=10 `31/37` (0.837838), median MFE_R `42.644178`.
- `SWEEP_EXTREME_HARD_STOP`: MFE_R>=3 `34/37` (0.918919), MFE_R>=5 `29/37` (0.783784), MFE_R>=10 `23/37` (0.621622), median MFE_R `12.411209`.

Exact MFE source files:
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_summary_by_stop_model.csv`: direct source for MFE_R threshold counts and medians.
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_per_trade.csv`: per-event MFE_R source used below.
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_extension_report.md`: narrative MFE diagnostic report that summarized those CSVs.

## Dataset Identity Check

- Selected reference-stop H4 events at `BARS_AFTER_ACTIVATION:4320`: `37` unique `source_setup_id`.
- Selected sweep-extreme H4 events at `BARS_AFTER_ACTIVATION:4320`: `37` unique `source_setup_id`.
- Reference and sweep sets identical: `yes`.
- Same H4 setup-event set across all stop-model/expiry combinations in `structural_matrix_all_trades.csv`: `yes`.
- Entry-review CSV rows matched back to these events by `(date, entry_date, direction)`: `37/37`.
- Missing manual labels after match: `0`.

No evidence of mixed datasets was found for the 37 H4 setup-events. The conflict is semantic: backtester/forensic artifacts contain replay outcomes and MFE diagnostics; entry-review contains blank manual-review outcomes plus optional manual notes.

## Meaning Of Blank `outcome`

Blank `outcome` cells in the entry-review CSV are manual-review candidates and should be treated as potentially profitable unless separately annotated. They are not present in original Analyzer artifacts, not present in `structural_matrix_all_trades.csv`, and not produced by the Backtester.

Because the entry-review CSV was simplified to `date, entry_date, direction, outcome`, it no longer carries `setup_id`, `entry_price`, stop prices, stop model, R, or TP/SL. It should not be used as the source for the earlier H4 TP/SL/NetR/MFE figures.

## Reconciled Counts

- Reconciled events: `37`.
- Reference outcomes from backtester ledger: `{'SL': 14, 'TP': 23}`.
- Sweep outcomes from backtester ledger: `{'TP': 22, 'SL': 15}`.
- Manual entry-review outcomes: 37 blank `outcome` cells; 2 rows additionally marked `potential_after_resweep`.

## Per-Event Reconciliation

| # | setup_id | setup_ts | entry_ts | dir | ref | ref_R | sweep | sweep_R | ref_MFE_R_5760 | sweep_MFE_R_5760 | manual |
|---:|---|---|---|---|---|---:|---|---:|---:|---:|---|
| 1 | `3711c617488c92d9828c70cf` | 2026-03-31 01:37:00+00:00 | 2026-03-31 01:38:00+00:00 | short | SL | -1 | TP | 1.5 | 95.1984 | 9.62092 |  |
| 2 | `c3eed66a7fa6c67beef867a1` | 2026-03-31 10:06:00+00:00 | 2026-03-31 10:07:00+00:00 | long | TP | 1.5 | TP | 1.5 | 154.955 | 21.9778 |  |
| 3 | `1aa6954e4d80fdcf5dbd92dd` | 2026-03-31 17:16:00+00:00 | 2026-03-31 17:17:00+00:00 | short | TP | 1.5 | TP | 1.5 | 72.1951 | 13.8318 |  |
| 4 | `513de79500f119ebdc89e724` | 2026-04-01 05:27:00+00:00 | 2026-04-01 05:28:00+00:00 | short | TP | 1.5 | SL | -1 | 72.8359 | 17.4594 |  |
| 5 | `752a04162f5f952bae4ebb52` | 2026-04-02 01:08:00+00:00 | 2026-04-02 01:09:00+00:00 | long | TP | 1.5 | SL | -1 | 16.8311 | 4.20997 |  |
| 6 | `41b0c0d1c811e60feabed7db` | 2026-04-04 15:16:00+00:00 | 2026-04-04 15:17:00+00:00 | short | SL | -1 | TP | 1.5 | 27.7918 | 3.23077 |  |
| 7 | `a7041ce1f10fd1f3af817637` | 2026-04-05 06:28:00+00:00 | 2026-04-05 06:29:00+00:00 | long | SL | -1 | TP | 1.5 | 30564 | 62.6311 |  |
| 8 | `fbac09144b83157ce6e05ade` | 2026-04-05 15:32:00+00:00 | 2026-04-05 15:33:00+00:00 | short | SL | -1 | SL | -1 | 5.71383 | 1.32473 |  |
| 9 | `0c73ebb37dc32d075b0c2c2b` | 2026-04-06 16:50:00+00:00 | 2026-04-06 16:51:00+00:00 | short | TP | 1.5 | TP | 1.5 | 39.4118 | 17.3965 |  |
| 10 | `7d7d5ff4a49433f6625e6d11` | 2026-04-07 10:54:00+00:00 | 2026-04-07 10:55:00+00:00 | long | SL | -1 | SL | -1 | 827.968 | 63.6122 |  |
| 11 | `ee3a427c406780624a37e615` | 2026-04-07 20:37:00+00:00 | 2026-04-07 20:38:00+00:00 | short | SL | -1 | SL | -1 | 9.93827 | 0.426377 |  |
| 12 | `db5b6d371b68357ad98b0e95` | 2026-04-08 13:15:00+00:00 | 2026-04-08 13:16:00+00:00 | short | SL | -1 | SL | -1 | 14.1333 | 10.3168 |  |
| 13 | `f015269d47c4d8b05862fd28` | 2026-04-09 00:50:00+00:00 | 2026-04-09 00:51:00+00:00 | long | SL | -1 | SL | -1 | 64.3011 | 35.0666 |  |
| 14 | `0a844825ee63e3ed0feb88be` | 2026-04-09 22:19:00+00:00 | 2026-04-09 22:20:00+00:00 | short | TP | 1.5 | TP | 1.5 | 129.451 | 8.27336 |  |
| 15 | `84b4a773e173b42be1f3ea1f` | 2026-04-10 08:09:00+00:00 | 2026-04-10 08:10:00+00:00 | long | TP | 1.5 | TP | 1.5 | 247.896 | 34.3593 |  |
| 16 | `4a4a99cd318717852e39bf35` | 2026-04-10 15:27:00+00:00 | 2026-04-10 15:28:00+00:00 | short | TP | 1.5 | SL | -1 | 8.6036 | 5.89549 |  |
| 17 | `d2f44849f48086dd3d5aa521` | 2026-04-10 20:33:00+00:00 | 2026-04-10 20:34:00+00:00 | short | TP | 1.5 | TP | 1.5 | 26.4534 | 9.10061 |  |
| 18 | `3006cd3533f5bb2880b10b4d` | 2026-04-11 13:13:00+00:00 | 2026-04-11 13:14:00+00:00 | long | SL | -1 | TP | 1.5 | 116.897 | 23.7537 |  |
| 19 | `405013a764fde5de604ad58a` | 2026-04-11 18:43:00+00:00 | 2026-04-11 18:44:00+00:00 | short | SL | -1 | SL | -1 | 128.515 | 11.5784 |  |
| 20 | `9ec69c6605ca85675e0e6e06` | 2026-04-12 22:29:00+00:00 | 2026-04-12 22:30:00+00:00 | long | TP | 1.5 | SL | -1 | 379.594 | 92.3163 |  |
| 21 | `7b888d3386fe39dad14954b7` | 2026-04-13 13:52:00+00:00 | 2026-04-13 13:53:00+00:00 | short | TP | 1.5 | SL | -1 | 3.3024 | 0.502506 |  |
| 22 | `24821ea89eb16e5962052714` | 2026-04-14 07:11:00+00:00 | 2026-04-14 07:12:00+00:00 | short | TP | 1.5 | TP | 1.5 | 8.00223 | 6.85468 |  |
| 23 | `a4b5b44714ca7e13a0dfd875` | 2026-04-15 08:07:00+00:00 | 2026-04-15 08:08:00+00:00 | long | TP | 1.5 | TP | 1.5 | 497.154 | 20.027 |  |
| 24 | `2b972c2d5c1154445cef48ed` | 2026-04-15 20:08:00+00:00 | 2026-04-15 20:09:00+00:00 | short | TP | 1.5 | TP | 1.5 | 109.627 | 28.6914 |  |
| 25 | `20bbebe07f85f5df26d3a600` | 2026-04-16 10:08:00+00:00 | 2026-04-16 10:09:00+00:00 | long | SL | -1 | SL | -1 | 43.5714 | 38.2014 |  |
| 26 | `ac0976106dd13f30947fcfe9` | 2026-04-16 20:02:00+00:00 | 2026-04-16 20:03:00+00:00 | short | TP | 1.5 | TP | 1.5 | 23.3296 | 11.4898 |  |
| 27 | `5b5778d8476b895e6de94ff8` | 2026-04-17 08:52:00+00:00 | 2026-04-17 08:53:00+00:00 | short | SL | -1 | SL | -1 | 29.5676 | 7.84019 |  |
| 28 | `5aa6ca780f474006f1ad7e92` | 2026-04-18 04:34:00+00:00 | 2026-04-18 04:35:00+00:00 | long | TP | 1.5 | TP | 1.5 | 39.6154 | 16.1886 |  |
| 29 | `08ece5642f91aaa3c0c93b7d` | 2026-04-18 16:20:00+00:00 | 2026-04-18 16:21:00+00:00 | long | SL | -1 | SL | -1 | 15.8399 | 10.0853 |  |
| 30 | `09dceefa4eb6595922e2fb7b` | 2026-04-19 02:27:00+00:00 | 2026-04-19 02:28:00+00:00 | long | TP | 1.5 | TP | 1.5 | 58.2694 | 35.7896 |  |
| 31 | `0d25765ec7778c11c037cd24` | 2026-04-19 18:02:00+00:00 | 2026-04-19 18:03:00+00:00 | long | SL | -1 | SL | -1 | 1923.88 | 21.8106 |  |
| 32 | `898f378842a15c489d666e43` | 2026-04-20 12:22:00+00:00 | 2026-04-20 12:23:00+00:00 | short | TP | 1.5 | TP | 1.5 | 9.07615 | 4.42896 |  |
| 33 | `747855283015820c70664969` | 2026-04-21 08:53:00+00:00 | 2026-04-21 08:54:00+00:00 | short | TP | 1.5 | TP | 1.5 | 356.776 | 3.69677 |  |
| 34 | `028f210d6ae7398f319e4a59` | 2026-04-21 15:06:00+00:00 | 2026-04-21 15:07:00+00:00 | long | TP | 1.5 | TP | 1.5 | 42.6442 | 23.0801 |  |
| 35 | `faabff822baa2bc8469718c6` | 2026-04-22 02:20:00+00:00 | 2026-04-22 02:21:00+00:00 | short | TP | 1.5 | TP | 1.5 | 27.4138 | 3.2806 |  |
| 36 | `fe9fbd07fb8111aed2450434` | 2026-04-22 12:19:00+00:00 | 2026-04-22 12:20:00+00:00 | short | TP | 1.5 | TP | 1.5 | 17.5391 | 12.4112 |  |
| 37 | `a677c262f570695e493cd91f` | 2026-04-23 09:11:00+00:00 | 2026-04-23 09:12:00+00:00 | long | TP | 1.5 | TP | 1.5 | 33.6583 | 26.0087 |  |

## Audit Notes

- The earlier positive H4 metrics are reproducible from existing deterministic artifacts, but they are replay/MFE diagnostics, not an execution-ready claim.
- The manual review label is intentionally stricter and visually motivated. It can coexist with positive backtester arithmetic because it answers a different question: whether the shape is worth future manual consideration.
- No new optimization, parameter change, Analyzer change, or Backtester change was performed for this audit.

## Superseding Manual Review Note

After timezone-corrected visual review, the entry-review CSV has blank `outcome` cells and additional manual notes. Blank cells are potentially profitable/manual-review candidates, not no-continuation discards. Two rows are explicitly flagged as `potential_after_resweep`: `2026-04-11 18:44:00+00:00` and `2026-04-15 20:09:00+00:00`.



