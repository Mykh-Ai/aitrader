# FAILED_BREAK_RECLAIM_H4_EXTENDED_V1 Entry Review Index - 2026-05-04

Research-only forensic extraction for manual chart review. No strategy logic, Analyzer behavior, or Backtester behavior was changed. No edge or execution-readiness conclusion is made here.

## Summary

- Setup class: `FAILED_BREAK_RECLAIM_H4_EXTENDED_V1` / source `FAILED_BREAK_RECLAIM_EXTENDED_V1` filtered to `SourceTF=H4`.
- Window: `2026-03-30_to_2026-05-02`; manifest chosen feed range is `2026-03-30 00:00:00+00:00` to `2026-05-02 23:59:00+00:00`.
- H4 setup-events found: `37`.
- Confirmed unique trades/events: `yes` - `37` unique `SetupId` values after de-duplicating stop models.
- Direction split: long `16`, short `21`.
- Setup timestamp range: `2026-03-31 01:37:00+00:00` to `2026-04-23 09:11:00+00:00`.
- Entry timestamp range: `2026-03-31 01:38:00+00:00` to `2026-04-23 09:12:00+00:00`.
- Outcome columns use representative H4 forensic expiry `BARS_AFTER_ACTIVATION:4320`. H4 forensic report says metrics are unchanged between 2880 and 4320; structural by-source-TF shows the same 37 H4 setup-events across all listed expiry and stop-model rows.
- Entry timestamp field: `entry_activation_ts`, because manifest fixed `entry_price_convention` is `NEXT_BAR_OPEN`. This is the next raw bar after `entry_signal_ts` / `SetupBarTs`.
- Symbol: `BTCUSDT`, inferred from repository/feed context; the trade ledger artifact does not carry a symbol column.

## Stop Model De-Duplication

- Reference and sweep-extreme stop rows contain the same setup-events for selected H4 expiry: `yes`.
- Same H4 setup-event set across all stop-model/expiry combinations in `structural_matrix_all_trades.csv`: `yes`.
- The master CSV therefore has one row per setup-event, with stop-model results in separate columns: `reference_outcome`, `reference_R`, `reference_close_ts`, `sweep_outcome`, `sweep_R`, `sweep_close_ts`.

## Missing Or Ambiguous Records

- Missing `backtester_entry_ts`: `0`.
- Duplicate rows within the same selected stop model: `0`.
- Ambiguous/mismatched common fields between reference and sweep rows: `0` setup-events.
- No explicit `reclaim_ts` column exists in the source setup artifact. The CSV fills `reclaim_ts` from `ReferenceEventTs`, which is the failed-break/reclaim setup event timestamp in `extended_v1_setups.csv`; `setup_ts`, `signal_ts`, and `ReferenceEventTs` are equal for these rows in the current artifacts.

## Entry Timestamp List

| # | setup_id | entry_ts | direction |
|---:|---|---|---|
| 1 | `3711c617488c92d9828c70cf` | 2026-03-31 01:38:00+00:00 | short |
| 2 | `c3eed66a7fa6c67beef867a1` | 2026-03-31 10:07:00+00:00 | long |
| 3 | `1aa6954e4d80fdcf5dbd92dd` | 2026-03-31 17:17:00+00:00 | short |
| 4 | `513de79500f119ebdc89e724` | 2026-04-01 05:28:00+00:00 | short |
| 5 | `752a04162f5f952bae4ebb52` | 2026-04-02 01:09:00+00:00 | long |
| 6 | `41b0c0d1c811e60feabed7db` | 2026-04-04 15:17:00+00:00 | short |
| 7 | `a7041ce1f10fd1f3af817637` | 2026-04-05 06:29:00+00:00 | long |
| 8 | `fbac09144b83157ce6e05ade` | 2026-04-05 15:33:00+00:00 | short |
| 9 | `0c73ebb37dc32d075b0c2c2b` | 2026-04-06 16:51:00+00:00 | short |
| 10 | `7d7d5ff4a49433f6625e6d11` | 2026-04-07 10:55:00+00:00 | long |
| 11 | `ee3a427c406780624a37e615` | 2026-04-07 20:38:00+00:00 | short |
| 12 | `db5b6d371b68357ad98b0e95` | 2026-04-08 13:16:00+00:00 | short |
| 13 | `f015269d47c4d8b05862fd28` | 2026-04-09 00:51:00+00:00 | long |
| 14 | `0a844825ee63e3ed0feb88be` | 2026-04-09 22:20:00+00:00 | short |
| 15 | `84b4a773e173b42be1f3ea1f` | 2026-04-10 08:10:00+00:00 | long |
| 16 | `4a4a99cd318717852e39bf35` | 2026-04-10 15:28:00+00:00 | short |
| 17 | `d2f44849f48086dd3d5aa521` | 2026-04-10 20:34:00+00:00 | short |
| 18 | `3006cd3533f5bb2880b10b4d` | 2026-04-11 13:14:00+00:00 | long |
| 19 | `405013a764fde5de604ad58a` | 2026-04-11 18:44:00+00:00 | short |
| 20 | `9ec69c6605ca85675e0e6e06` | 2026-04-12 22:30:00+00:00 | long |
| 21 | `7b888d3386fe39dad14954b7` | 2026-04-13 13:53:00+00:00 | short |
| 22 | `24821ea89eb16e5962052714` | 2026-04-14 07:12:00+00:00 | short |
| 23 | `a4b5b44714ca7e13a0dfd875` | 2026-04-15 08:08:00+00:00 | long |
| 24 | `2b972c2d5c1154445cef48ed` | 2026-04-15 20:09:00+00:00 | short |
| 25 | `20bbebe07f85f5df26d3a600` | 2026-04-16 10:09:00+00:00 | long |
| 26 | `ac0976106dd13f30947fcfe9` | 2026-04-16 20:03:00+00:00 | short |
| 27 | `5b5778d8476b895e6de94ff8` | 2026-04-17 08:53:00+00:00 | short |
| 28 | `5aa6ca780f474006f1ad7e92` | 2026-04-18 04:35:00+00:00 | long |
| 29 | `08ece5642f91aaa3c0c93b7d` | 2026-04-18 16:21:00+00:00 | long |
| 30 | `09dceefa4eb6595922e2fb7b` | 2026-04-19 02:28:00+00:00 | long |
| 31 | `0d25765ec7778c11c037cd24` | 2026-04-19 18:03:00+00:00 | long |
| 32 | `898f378842a15c489d666e43` | 2026-04-20 12:23:00+00:00 | short |
| 33 | `747855283015820c70664969` | 2026-04-21 08:54:00+00:00 | short |
| 34 | `028f210d6ae7398f319e4a59` | 2026-04-21 15:07:00+00:00 | long |
| 35 | `faabff822baa2bc8469718c6` | 2026-04-22 02:21:00+00:00 | short |
| 36 | `fe9fbd07fb8111aed2450434` | 2026-04-22 12:20:00+00:00 | short |
| 37 | `a677c262f570695e493cd91f` | 2026-04-23 09:12:00+00:00 | long |

## Source Files

- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_research_report.md`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_summary.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_all_trades.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_by_source_tf.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_stop_model_comparison.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_per_trade.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_extension_report.md`
- `research/results/failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03/extended_v1_setups.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_manifest.json`

## Output

- Master CSV: `research/results/failed_break_reclaim_h4_extended_v1_entry_review_2026-03-30_to_2026-05-02.csv`

## Manual Review Update

Superseded: the previous `discard_no_real_continuation` label was removed from the entry-review CSV. Blank `outcome` cells are manual-review candidates and should not be interpreted as no-continuation discards.

## Manual Review Update 2

After timezone-corrected visual review, blank/manual-review rows should be treated as potentially profitable rather than automatically discarded. Two rows are explicitly marked in the CSV:

- `2026-04-11 18:44:00+00:00` short entry: user visual review notes entry existed; double sweep/resweep about 70 USD, then about 3000 USD move. User referred to this as Apr 4 18:44; exact artifact match is `2026-04-11 18:44:00+00:00`.
- `2026-04-15 20:09:00+00:00` short entry: user visual review notes wicks/resweep about 150 USD, then about 1500 USD move.


