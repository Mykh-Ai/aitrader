# FAILED_BREAK_RECLAIM_EXTENDED_V1 Large-Window Preparation

Research-only preparation run. Strategy logic, Analyzer baseline behavior, and Backtester behavior were not modified. Matrix was not run.

## Requested Feed Inventory

- Requested window: `2026-03-10` to `2026-05-03`
- Missing dates: `<none>`
- Total rows in requested files: `76813`
- Duplicate timestamps in requested concat: `0`
- Max timestamp gap minutes in requested concat: `826.0`
- Synthetic rows in requested concat: `14780`
- Nonpositive OHLC rows in requested concat: `1`

## Warmup / Continuity Decision

- `2026-03-10: partial/non-full day rows=526 start=2026-03-10 15:14:00+00:00 end=2026-03-10 23:59:00+00:00 max_gap=1.0333333333333334`
- `2026-03-11: partial/non-full day rows=615 start=2026-03-11 13:45:00+00:00 end=2026-03-11 23:59:00+00:00 max_gap=1.0`
- Chosen main prep window: `2026-03-30` to `2026-05-02`
- Reason: `largest continuous full 1m calendar-day block in requested range`


### Continuous Full-Day Blocks

| start_date   | end_date   |   number_of_days |   total_rows |
|:-------------|:-----------|-----------------:|-------------:|
| 2026-03-12   | 2026-03-28 |               17 |        24479 |
| 2026-03-30   | 2026-05-02 |               34 |        48960 |

### Non-Full Days In Requested Window

| date       |   rows | start_ts                  | end_ts                    |   duplicate_timestamps |   max_timestamp_gap_minutes |   synthetic_rows |   nonpositive_ohlc_rows | is_full_1m_calendar_day   |
|:-----------|-------:|:--------------------------|:--------------------------|-----------------------:|----------------------------:|-----------------:|------------------------:|:--------------------------|
| 2026-03-10 |    526 | 2026-03-10 15:14:00+00:00 | 2026-03-10 23:59:00+00:00 |                      0 |                     1.03333 |              nan |                       0 | False                     |
| 2026-03-11 |    615 | 2026-03-11 13:45:00+00:00 | 2026-03-11 23:59:00+00:00 |                      0 |                     1       |                4 |                       0 | False                     |
| 2026-03-29 |    834 | 2026-03-29 00:00:00+00:00 | 2026-03-29 13:53:00+00:00 |                      0 |                     1       |                0 |                       0 | False                     |
| 2026-05-03 |   1399 | 2026-05-03 00:00:00+00:00 | 2026-05-03 23:18:00+00:00 |                      0 |                     1       |             1399 |                       0 | False                     |

## Combined Feed

- Path: `research\results\failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03\feed_window_2026-03-30_to_2026-05-02.csv`
- Rows: `48960`
- FeedStartTs: `2026-03-30 00:00:00+00:00`
- FeedEndTs: `2026-05-02 23:59:00+00:00`
- Duplicate timestamps before write/drop: `0`
- Duplicate timestamps removed: `0`
- Max timestamp gap minutes: `1.0`
- Synthetic rows: `13376`
- Nonpositive OHLC rows: `0`
- Deterministic write/read schema+row equality: `True`

## EXTENDED_V1 Setup Summary

- Variant: `FAILED_BREAK_RECLAIM_EXTENDED_V1`
- confirmation_bars: `60`
- Total setups: `153`
- LONG setups: `73`
- SHORT setups: `80`
- H1 setups: `116`
- H4 setups: `37`
- SourceTF counts: `{'H1': 116, 'H4': 37}`

### Setup Count By Date

| SetupDate   |   Total |   LONG |   SHORT |
|:------------|--------:|-------:|--------:|
| 2026-03-30  |       5 |      1 |       4 |
| 2026-03-31  |       5 |      2 |       3 |
| 2026-04-01  |       4 |      1 |       3 |
| 2026-04-02  |       6 |      3 |       3 |
| 2026-04-03  |       4 |      2 |       2 |
| 2026-04-04  |      10 |      4 |       6 |
| 2026-04-05  |       5 |      3 |       2 |
| 2026-04-06  |       4 |      2 |       2 |
| 2026-04-07  |       8 |      4 |       4 |
| 2026-04-08  |       5 |      2 |       3 |
| 2026-04-09  |       7 |      3 |       4 |
| 2026-04-10  |       7 |      2 |       5 |
| 2026-04-11  |      10 |      5 |       5 |
| 2026-04-12  |       5 |      4 |       1 |
| 2026-04-13  |       7 |      1 |       6 |
| 2026-04-14  |       5 |      3 |       2 |
| 2026-04-15  |       6 |      2 |       4 |
| 2026-04-16  |       6 |      3 |       3 |
| 2026-04-17  |       6 |      2 |       4 |
| 2026-04-18  |       7 |      5 |       2 |
| 2026-04-19  |       6 |      5 |       1 |
| 2026-04-20  |       8 |      4 |       4 |
| 2026-04-21  |       9 |      6 |       3 |
| 2026-04-22  |       4 |      1 |       3 |
| 2026-04-23  |       4 |      3 |       1 |

## Forward Coverage

- Coverage status counts: `{'FULL': 153}`
- Main-test eligible setups with FULL 5760-bar coverage: `153`
- Coverage CSV: `research\results\failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03\extended_v1_forward_coverage.csv`
- Eligible set CSV: `research\results\failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03\extended_v1_main_test_eligible_set.csv`

### Coverage Preview

| SetupId                  | SetupBarTs                | Direction   | SourceTF   |   ForwardBarsAvailable | Supports1440   | Supports2880   | Supports4320   | Supports5760   | CoverageStatus   |
|:-------------------------|:--------------------------|:------------|:-----------|-----------------------:|:---------------|:---------------|:---------------|:---------------|:-----------------|
| aa05eab67329244350a47266 | 2026-03-30 04:30:00+00:00 | SHORT       | H1         |                  48689 | True           | True           | True           | True           | FULL             |
| 6ded84a264bd234ef565b710 | 2026-03-30 08:08:00+00:00 | SHORT       | H1         |                  48471 | True           | True           | True           | True           | FULL             |
| cdd9e320ed5efa3409afe54a | 2026-03-30 11:28:00+00:00 | SHORT       | H1         |                  48271 | True           | True           | True           | True           | FULL             |
| 89522034e456a3a1c21cacdc | 2026-03-30 13:26:00+00:00 | SHORT       | H1         |                  48153 | True           | True           | True           | True           | FULL             |
| 025e7e075769825cf28e132d | 2026-03-30 14:21:00+00:00 | LONG        | H1         |                  48098 | True           | True           | True           | True           | FULL             |
| 3711c617488c92d9828c70cf | 2026-03-31 01:37:00+00:00 | SHORT       | H4         |                  47422 | True           | True           | True           | True           | FULL             |
| e5379aee533aa6102ed030a3 | 2026-03-31 09:28:00+00:00 | LONG        | H1         |                  46951 | True           | True           | True           | True           | FULL             |
| c3eed66a7fa6c67beef867a1 | 2026-03-31 10:06:00+00:00 | LONG        | H4         |                  46913 | True           | True           | True           | True           | FULL             |
| 6a8bf19c00c0f910ef988ca9 | 2026-03-31 16:45:00+00:00 | SHORT       | H1         |                  46514 | True           | True           | True           | True           | FULL             |
| 1aa6954e4d80fdcf5dbd92dd | 2026-03-31 17:16:00+00:00 | SHORT       | H4         |                  46483 | True           | True           | True           | True           | FULL             |
| 53ce81ab3558fd452e180d5e | 2026-04-21 20:01:00+00:00 | LONG        | H1         |                  16078 | True           | True           | True           | True           | FULL             |
| f47b3e7705299fffae725c1a | 2026-04-21 23:42:00+00:00 | SHORT       | H1         |                  15857 | True           | True           | True           | True           | FULL             |
| faabff822baa2bc8469718c6 | 2026-04-22 02:20:00+00:00 | SHORT       | H4         |                  15699 | True           | True           | True           | True           | FULL             |
| 9002a65aedaa23d6742567d2 | 2026-04-22 11:05:00+00:00 | SHORT       | H1         |                  15174 | True           | True           | True           | True           | FULL             |
| fe9fbd07fb8111aed2450434 | 2026-04-22 12:19:00+00:00 | SHORT       | H4         |                  15100 | True           | True           | True           | True           | FULL             |
| 61785825c076c85d3d731b91 | 2026-04-22 23:23:00+00:00 | LONG        | H1         |                  14436 | True           | True           | True           | True           | FULL             |
| d242492dd6326c57a795e5d4 | 2026-04-23 03:42:00+00:00 | LONG        | H1         |                  14177 | True           | True           | True           | True           | FULL             |
| 78a602a40a9f851489d94748 | 2026-04-23 09:11:00+00:00 | LONG        | H1         |                  13848 | True           | True           | True           | True           | FULL             |
| a677c262f570695e493cd91f | 2026-04-23 09:11:00+00:00 | LONG        | H4         |                  13848 | True           | True           | True           | True           | FULL             |
| 6e61c08bda2a0cf64c034380 | 2026-04-23 15:47:00+00:00 | SHORT       | H1         |                  13452 | True           | True           | True           | True           | FULL             |

## Files

- `feed_inventory.csv`
- `continuous_calendar_blocks.csv`
- `continuous_full_day_blocks.csv`
- `non_full_days_in_requested_window.csv`
- `feed_window_2026-03-30_to_2026-05-02.csv`
- `combined_feed_nonpositive_ohlc_rows.csv`
- `extended_v1_events.csv`
- `extended_v1_setups.csv`
- `extended_v1_outcomes_by_horizon.csv`
- `setup_count_by_date.csv`
- `extended_v1_forward_coverage.csv`
- `extended_v1_main_test_eligible_set.csv`
- `large_window_prep_manifest.json`

No edge claim. This is preparation only.