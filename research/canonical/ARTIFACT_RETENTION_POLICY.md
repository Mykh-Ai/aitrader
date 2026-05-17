# ARTIFACT_RETENTION_POLICY

Last updated: 2026-05-17

## KEEP

- Canonical state files under `research/canonical/`.
- Candidate contracts and current active validation files under `research/candidates/`.
- Official summaries and manifests, including recovered rerun summaries, Sprint 03 pooled replay summary, and Sprint 04 holdout summary.
- Holdout logs, feed audits, no-lookahead reports, same-bar reports, cost stress summaries, source concentration reports, and promotion checklists.
- Rejected/quarantined verdict summaries that explain why a candidate is not active.

## DO NOT KEEP IN GIT

- Local scratch runs.
- Debug CSVs.
- Temporary probe files.
- Duplicated generated outputs.
- `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, coverage outputs.
- Old one-off diagnostics not referenced by canonical registry/state.

## EXTERNAL / OPTIONAL

- Large raw feed snapshots.
- `feed_recovered/` recovered mirror data.
- Large Analyzer/Backtester generated run directories.
- Server feed snapshots and local copies used for audit.
- Sidecar research findings/results that are useful for traceability but not current canonical truth.

## RULE

If an artifact is not referenced by canonical registry/state and is not needed for reproducibility, it should be deleted, archived externally, or gitignored.

If an artifact is referenced by canonical registry/state but is too large or too local for git, it must have a manifest, hash/provenance where practical, and an explicit external/archive-only status.
