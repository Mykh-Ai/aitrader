# Canonical development base

Effective: 2026-09-26. Repository: Mykh-Ai/aitrader.

The only base for new Market Monitor research is `canonical/market-monitor-39a`.
Old `main`, the named 39A documentation branch, and 38G are not new-work bases.
This applies to 39B, 39C, and every subsequent research task.

## Required start checks

Use a clean worktree; preserve existing changes. Fetch current remote refs, then create the task branch from `origin/canonical/market-monitor-39a`. Do not reset user branches or discard work.

Before editing, run all three checks and stop if any fails:

```bash
git merge-base --is-ancestor origin/canonical/market-monitor-39a HEAD
git merge-base --is-ancestor 0a67575af2da9f897ac759a314af6a75d9d87b5a HEAD
git merge-base --is-ancestor 1c18766462148943d99aa326f6093aed46e620e5 HEAD
```

Record the fetched canonical SHA in the task log. At PR time, target `canonical/market-monitor-39a` and synchronize again if canonical advanced. A ref name or an audit filename alone is not proof that the required history is present.

## Scope and authority

- Canonical contains both historical branches, with current implementation and updated 39A documents from `1c18766462148943d99aa326f6093aed46e620e5`.
- No strategy, live, Backtester, or Executor promotion follows from this branch decision.
- 39A's historical evidence classes remain in force; unavailable run artifacts must be retrieved before a task relies on their detailed results.
- `main` remains the GitHub default only for compatibility and carries a retirement notice. Starting new research there is prohibited by repository instructions.
- This is a governance rule, not a GitHub branch-protection rule. Server-side push restrictions were not changed.
- Existing branches are preserved; ARCHIVE and SUPERSEDED do not authorize deletion.

Full inventory and rationale: `research/canonical/CANONICAL_BRANCH_AUDIT_2026_09_26.md`.
