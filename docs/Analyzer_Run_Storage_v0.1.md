# Analyzer Run Storage — Design Contract v0.1

**Status:** Design-only proposal (no code changes)
**Phase:** Pre-Phase 3 infrastructure
**Date:** 2026-03-13
**Companion to:** `docs/Spec_v1.0.md`, `docs/Backtesting_Architecture_v0.1.md`

---

## 1. Top-level directory structure

Server-side layout under `/opt/aitrader`:

```
/opt/aitrader/
├── feed/                    # Raw 1m bar CSVs (aggregator output)
│                            # One file per day: YYYY-MM-DD.csv
│                            # OWNED BY: aggregator. Read-only for all other subsystems.
│
├── logs/                    # Runtime logs (aggregator.log, future pipeline logs)
│                            # Append-only. Not consumed by pipelines.
│
├── analyzer_runs/           # Analyzer pipeline output runs
│                            # One subdirectory per run. Immutable after generation.
│                            # OWNED BY: Analyzer pipeline runner.
│                            # READ BY: Backtester, human review.
│
├── backtests/               # Backtester output runs (Phase 3, future)
│                            # One subdirectory per backtest run.
│                            # Consumes one analyzer_runs/<run_id>/ as frozen input.
│
├── analyzer/                # Analyzer Python package (source code)
├── backtester/              # Backtester Python package (source code, future)
├── binance_aggregator_shi.py
├── CLAUDE.md
└── ...
```

**Invariants:**

- `feed/` is never written to by Analyzer or Backtester.
- `analyzer_runs/` is never written to by Backtester.
- Each subsystem owns its output directory exclusively.

---

## 2. Run directory naming contract

### Canonical naming scheme

```
{date_from}_to_{date_to}_run_{seq:03d}
```

Examples:

```
2026-03-13_to_2026-03-13_run_001    # single-day run
2026-03-11_to_2026-03-13_run_001    # multi-day run
2026-03-11_to_2026-03-13_run_002    # second run over same range
```

### Design rationale

| Property | Satisfied |
|---|---|
| Deterministic | Yes — derived from input date range + sequence counter |
| Human-readable | Yes — date range is visible in directory name |
| Sortable | Yes — lexicographic sort = chronological sort by start date |
| Safe for repeated runs | Yes — `_run_NNN` suffix increments per unique date range |

### Naming rules

- `date_from` and `date_to` are always `YYYY-MM-DD` (UTC dates).
- For single-day runs, `date_from == date_to` (still use `_to_` separator for consistency).
- `seq` is a zero-padded 3-digit integer starting at `001`.
- Sequence counter is scoped to the exact `{date_from}_to_{date_to}` prefix within `analyzer_runs/`.
- To determine next `seq`: scan existing directories matching the same date prefix, take max + 1.

### Why not datetime-based?

Datetime in the directory name (e.g., `2026-03-13_0726`) adds generation timestamp but:
- conflates generation time with input scope,
- makes re-runs harder to group visually,
- generation timestamp is already captured in `run_manifest.json`.

The input date range is the primary identity. Generation metadata belongs in the manifest.

---

## 3. One run = one frozen artifact directory

Each Analyzer run produces exactly one self-contained directory:

```
analyzer_runs/2026-03-13_to_2026-03-13_run_001/
├── run_manifest.json
├── analyzer_features.csv
├── analyzer_events.csv
├── analyzer_setups.csv
├── analyzer_setup_outcomes.csv
├── analyzer_setup_report.csv
├── analyzer_setup_context_report.csv
├── analyzer_setup_rankings.csv
├── analyzer_setup_selections.csv
├── analyzer_setup_shortlist.csv
├── analyzer_setup_shortlist_explanations.csv
└── analyzer_research_summary.csv
```

**Rules:**

- All 11 CSV artifacts + 1 manifest = 12 files total per run.
- File names are fixed and identical across all runs (no date suffixes, no versioning in filenames).
- No subdirectories within a run directory.
- No files other than the 12 listed above in v0.1.
- A run directory missing any of the 12 files is considered **incomplete** and must not be consumed by Backtester.

---

## 4. Run manifest contract

Each run directory contains `run_manifest.json` at the root.

### Required fields

```json
{
  "run_id": "2026-03-13_to_2026-03-13_run_001",
  "generated_at_utc": "2026-03-13T07:26:14Z",
  "input_feed_dir": "/opt/aitrader/feed",
  "input_feed_files": [
    "2026-03-13.csv"
  ],
  "input_date_from": "2026-03-13",
  "input_date_to": "2026-03-13",
  "input_bar_count": 1440,
  "input_includes_partial_day": false,
  "output_dir": "/opt/aitrader/analyzer_runs/2026-03-13_to_2026-03-13_run_001",
  "artifact_list": [
    "analyzer_features.csv",
    "analyzer_events.csv",
    "analyzer_setups.csv",
    "analyzer_setup_outcomes.csv",
    "analyzer_setup_report.csv",
    "analyzer_setup_context_report.csv",
    "analyzer_setup_rankings.csv",
    "analyzer_setup_selections.csv",
    "analyzer_setup_shortlist.csv",
    "analyzer_setup_shortlist_explanations.csv",
    "analyzer_research_summary.csv"
  ],
  "artifact_count": 11,
  "pipeline_stage_count": 16,
  "analyzer_version": "0.1.0",
  "git_commit": "a1b2c3d",
  "git_branch": "main",
  "status": "complete",
  "notes": null
}
```

### Field definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `run_id` | string | yes | Matches directory name exactly |
| `generated_at_utc` | ISO 8601 | yes | UTC timestamp of run completion |
| `input_feed_dir` | string | yes | Absolute path to feed directory used |
| `input_feed_files` | string[] | yes | Ordered list of feed CSV files consumed |
| `input_date_from` | YYYY-MM-DD | yes | First date in input range (UTC) |
| `input_date_to` | YYYY-MM-DD | yes | Last date in input range (UTC) |
| `input_bar_count` | int | yes | Total 1m bars loaded across all input files |
| `input_includes_partial_day` | bool | yes | True if `date_to` file was incomplete at run time |
| `output_dir` | string | yes | Absolute path to this run directory |
| `artifact_list` | string[] | yes | Fixed list of artifact filenames |
| `artifact_count` | int | yes | Length of `artifact_list` (11 in v0.1) |
| `pipeline_stage_count` | int | yes | Number of pipeline stages executed (16 in v0.1) |
| `analyzer_version` | string | yes | Semantic version of analyzer package |
| `git_commit` | string | yes | Short SHA of HEAD at run time (or `"unknown"`) |
| `git_branch` | string | yes | Branch name (or `"unknown"`) |
| `status` | string | yes | `"complete"` or `"failed"` |
| `notes` | string\|null | yes | Optional free-text annotation |

### Optional fields (recommended for v0.2+)

| Field | Type | Description |
|---|---|---|
| `artifact_row_counts` | object | `{"analyzer_features.csv": 1440, ...}` |
| `artifact_file_sizes_bytes` | object | `{"analyzer_features.csv": 2345678, ...}` |
| `hostname` | string | Machine hostname |
| `python_version` | string | e.g., `"3.11.7"` |
| `container_image_tag` | string | Docker image tag if applicable |
| `schema_version` | string | Manifest schema version for future evolution |
| `duration_seconds` | float | Pipeline wall-clock time |

---

## 5. Run generation policy

### Recommended policy: fully regenerated, new directory, no silent overwrite

1. **Every run regenerates all 11 artifacts from scratch.** No incremental or append mode.
2. **Every run creates a new directory** with an incremented `_run_NNN` suffix.
3. **No silent overwrite.** If a directory with the computed name already exists, the runner must increment the sequence counter, never reuse or overwrite.
4. **Explicit overwrite (opt-in only).** A future `--force` flag may allow overwriting a specific existing run directory, but this is not the default and is not part of v0.1.

### Why?

- Reproducibility: any past run can be inspected as-is.
- Auditability: the sequence of runs is visible in the filesystem.
- Safety: a failed or incorrect run does not destroy a previous good run.
- Backtester compatibility: a frozen directory can be referenced reliably.

---

## 6. Input range contract

### How a run records its input scope

The input scope is encoded in **two places**:

1. **Directory name** — carries the date range (`date_from_to_date_to`).
2. **Manifest** — carries the full detail:
   - `input_feed_files`: exact list of CSV files consumed.
   - `input_date_from` / `input_date_to`: date boundaries.
   - `input_bar_count`: total bars loaded.
   - `input_includes_partial_day`: completeness flag.

### Single-day vs multi-day

| Scenario | `input_feed_files` | Directory name |
|---|---|---|
| One complete day | `["2026-03-13.csv"]` | `2026-03-13_to_2026-03-13_run_001` |
| Three complete days | `["2026-03-11.csv", "2026-03-12.csv", "2026-03-13.csv"]` | `2026-03-11_to_2026-03-13_run_001` |
| Range with partial last day | `["2026-03-12.csv", "2026-03-13.csv"]` | `2026-03-12_to_2026-03-13_run_001` |

### Multi-day input assembly

When the input range spans multiple days, the runner must:

1. Load all `feed/YYYY-MM-DD.csv` files for dates in the range.
2. Concatenate in chronological order.
3. Pass the combined dataframe to `analyzer.pipeline.run()`.
4. Record all consumed files in `input_feed_files`.

This is a runner-level concern, not an Analyzer pipeline concern. The pipeline receives a single input path or dataframe — the runner handles multi-file assembly.

---

## 7. Partial-day vs full-day handling

### Definitions

- **Complete day:** a `feed/YYYY-MM-DD.csv` file that is no longer being written to (the UTC day has ended, or the aggregator has rotated to the next file). Expected bar count: up to 1440 (some bars may be missing due to gaps).
- **Partial day (in-progress):** the current UTC day's file, still being appended to by the aggregator.

### Policy

| Scenario | Allowed? | `input_includes_partial_day` |
|---|---|---|
| Run on complete days only | Yes (preferred) | `false` |
| Run including today's partial file | Yes (explicit) | `true` |
| Run on only a partial file | Yes (explicit) | `true` |

### Rules

1. The runner must determine whether the last file in the input range is still in-progress (e.g., `date_to == today UTC` and the aggregator is still running).
2. If the last file is partial, set `input_includes_partial_day: true` in the manifest.
3. Runs with `input_includes_partial_day: true` are valid but should be treated as **non-final** — they may be superseded by a later complete run over the same range.
4. The Backtester should prefer runs where `input_includes_partial_day == false` unless explicitly directed otherwise.

### Staleness heuristic (non-normative, for future runner)

A simple check: if `date_to` is today (UTC) and current UTC hour < 23:55, mark as partial. Otherwise assume complete. Exact implementation is deferred.

---

## 8. Backtester compatibility requirement

A future Backtester must be able to consume one `analyzer_runs/<run_id>/` directory as a **frozen artifact input boundary**.

### Requirements for compatibility

1. **Manifest presence:** `run_manifest.json` must exist and parse correctly.
2. **Stable artifact names:** all 11 CSVs must use the exact canonical names listed in §3.
3. **Complete artifact set:** all 11 CSVs must be present. A missing file = incomplete run = Backtester must reject.
4. **No mutation after generation:** once a run directory is created and `status == "complete"`, its contents must not change. No files added, removed, or modified.
5. **Status check:** Backtester should verify `status == "complete"` in manifest before consuming.

### Backtester input contract (preview)

The Backtester's `artifact_dir` parameter (from `Backtesting_Architecture_v0.1.md` §3.2) maps directly to one `analyzer_runs/<run_id>/` directory.

```
backtester.run(
    artifact_dir="/opt/aitrader/analyzer_runs/2026-03-11_to_2026-03-13_run_001",
    ...
)
```

---

## 9. Retention / cleanup policy

### v0.1 policy: keep everything

- **No auto-deletion.** All runs are retained indefinitely.
- **No archival.** No compression or cold storage mechanism in v0.1.
- **Cleanup is manual.** An operator may delete old run directories manually if disk space is needed.
- **Future:** a separate retention process may be designed later (e.g., keep last N runs per date range, archive runs older than M days). This is out of scope for v0.1.

### Disk budget estimate (non-normative)

A single-day run with ~1440 bars produces roughly:
- `analyzer_features.csv`: ~2–5 MB (wide table, many columns)
- Remaining 10 CSVs: ~10–500 KB each
- Total per run: ~3–8 MB

At 1 run/day: ~250 MB/year. At 5 runs/day: ~1.5 GB/year. No urgency for cleanup in v0.1.

---

## 10. Operational examples

### Example 1: single complete day

```
/opt/aitrader/analyzer_runs/2026-03-13_to_2026-03-13_run_001/
├── run_manifest.json
├── analyzer_features.csv
├── analyzer_events.csv
├── analyzer_setups.csv
├── analyzer_setup_outcomes.csv
├── analyzer_setup_report.csv
├── analyzer_setup_context_report.csv
├── analyzer_setup_rankings.csv
├── analyzer_setup_selections.csv
├── analyzer_setup_shortlist.csv
├── analyzer_setup_shortlist_explanations.csv
└── analyzer_research_summary.csv
```

Manifest excerpt:
```json
{
  "run_id": "2026-03-13_to_2026-03-13_run_001",
  "input_feed_files": ["2026-03-13.csv"],
  "input_bar_count": 1437,
  "input_includes_partial_day": false,
  "status": "complete"
}
```

### Example 2: re-run of the same day (new sequence)

```
/opt/aitrader/analyzer_runs/2026-03-13_to_2026-03-13_run_002/
└── ... (same 12 files)
```

Manifest: `run_id` = `2026-03-13_to_2026-03-13_run_002`, possibly different `input_bar_count` if feed was updated between runs.

### Example 3: multi-day range for backtesting

```
/opt/aitrader/analyzer_runs/2026-03-01_to_2026-03-13_run_001/
└── ... (same 12 files)
```

Manifest excerpt:
```json
{
  "run_id": "2026-03-01_to_2026-03-13_run_001",
  "input_feed_files": [
    "2026-03-01.csv",
    "2026-03-02.csv",
    "2026-03-03.csv",
    "2026-03-04.csv",
    "2026-03-05.csv",
    "2026-03-06.csv",
    "2026-03-07.csv",
    "2026-03-08.csv",
    "2026-03-09.csv",
    "2026-03-10.csv",
    "2026-03-11.csv",
    "2026-03-12.csv",
    "2026-03-13.csv"
  ],
  "input_bar_count": 18694,
  "input_includes_partial_day": false,
  "status": "complete"
}
```

---

## 11. Unresolved decisions (to fix before implementation)

| # | Decision | Notes |
|---|---|---|
| 1 | **Multi-file loader** | Current `pipeline.run()` accepts a single `input_path`. Multi-day runs require either a runner-level concat wrapper or a pipeline change to accept multiple paths / a directory. |
| 2 | **Analyzer version source** | Where does `analyzer_version` come from? A `__version__` in `analyzer/__init__.py`? A config file? Must be defined before manifest generation. |
| 3 | **Partial-day detection** | Exact heuristic for determining whether a feed file is still in-progress. Simple date check vs aggregator lock file vs file mtime. |
| 4 | **Manifest schema versioning** | Should `run_manifest.json` include a `schema_version` field from v0.1? Likely yes, but deferred to implementation. |
| 5 | **Dev vs production paths** | Dev environment uses `D:\Project_V\Aitrader\`, production uses `/opt/aitrader/`. The runner must resolve paths correctly per environment. Manifest should store absolute paths as-generated. |
| 6 | **Concurrent run safety** | If two runs start simultaneously with the same date range, sequence counter increment must be atomic (or use a lock). Unlikely in v0.1 but worth noting. |

---

## 12. Scope statement

This document defines the **storage layout and manifest contract** for Analyzer runs.
It does not introduce code, test, or runtime behavior changes.
It does not define the runner script that creates these directories — that is a separate implementation task.
