# Canonical branch audit — 2026-09-26

Repository: `Mykh-Ai/aitrader`. Scope: branch lineage, PR status, canonical-base consolidation, and governance only.

## Decision

Use `canonical/market-monitor-39a` for all subsequent Market Monitor research, including 39B/39C. It is created from named 39A `0a67575af2da9f897ac759a314af6a75d9d87b5a` and joins current implementation `1c18766462148943d99aa326f6093aed46e620e5` as its second parent. Both histories are retained.

`main` is an obsolete research base. `v2.0` does not exist among this repository’s seven remote branches; it must not be imported from the separate btc-orderflow-system repository.

Do not merge the named 39A branch alone into main: it adds documentation but leaves current replay modules, target correction, snapshot v39a, and tests absent. The permitted alternative—a separate canonical branch—is selected. Main receives only a retirement notice in README/AGENTS; no implementation is promoted into main.

## Evidence and graph

- GitHub default branch at audit: `main`, `1d868e8877551b2aca20e97740559f395b7b9f80`.
- Named 39A: `0a67575af2da9f897ac759a314af6a75d9d87b5a`, last commit 2026-07-05; 12 commits ahead of main, zero behind.
- Current 38G: `1c18766462148943d99aa326f6093aed46e620e5`, last commit 2026-09-11; 23 commits ahead of main, zero behind.
- Their common ancestor is the old main head. They diverge by 12 / 23 commits; neither contains the other.
- All 11 files changed by named 39A are documents. All 11 conflict with the newer implementation branch; each is resolved to the 38G version. Before adding this audit/governance, the merged tree is byte-for-byte identical to 38G.
- The full branch comparison has 95 differing paths. This is not a proposed deletion patch: the document-only branch lacks substantial implementation and evidence already present in 38G.
- Live GitHub branch collection returned seven branches. All 94 PR records were inspected; collection size is below the requested 100, so there was no omitted PR page.

## Remote branch inventory

Heads and merge bases below are pinned to the pre-change inventory. Full SHAs, PR merge timestamps/base SHAs, and local heads are in `CANONICAL_BRANCH_INVENTORY_2026_09_26.json`.

| Branch | Head | Git base with main / PR base | PR / historical merge | Head in current main | Contains named 39A / current code | Before → after |
| --- | --- | --- | --- | --- | --- | --- |
| `codex/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0` | `1c18766` | 1d868e8 / no PR | No exact-head PR | no | no / yes | MERGE_CANDIDATE → SUPERSEDED |
| `codex/SHI_RESET_39A_master_research_to_monitor_alignment_audit_v0` | `0a67575` | 1d868e8 / no PR | No exact-head PR | no | yes / no | SUPERSEDED → SUPERSEDED |
| `codex/define-explicit-binding-bridge-and-update-spec` | `eb991c6` | 1908ef8 / main@5393097 | [#94](https://github.com/Mykh-Ai/aitrader/pull/94) MERGED | no | no / no | ARCHIVE → ARCHIVE |
| `codex/fix-empty-minute-handling-and-open-interest-polling` | `3f9219e` | 3f9219e / no PR | No exact-head PR | yes | no / no | ARCHIVE → ARCHIVE |
| `codex/implement-h2-observational-outcome-layer` | `cad06d0` | 1908ef8 / main@52cf8a3 | [#93](https://github.com/Mykh-Ai/aitrader/pull/93) MERGED | no | no / no | ARCHIVE → ARCHIVE |
| `codex/implement-h2-patch-2-setup-extraction` | `40d476a` | 1908ef8 / main@3aea8da | [#92](https://github.com/Mykh-Ai/aitrader/pull/92) MERGED | no | no / no | ARCHIVE → ARCHIVE |
| `main` | `1d868e8` | 1d868e8 / no PR | No exact-head PR | yes | no / no | ARCHIVE → ARCHIVE |

New `canonical/market-monitor-39a`: **KEEP**; contains both 39A histories. It has no PR because this task creates a canonical branch instead of merging into main.

`ARCHIVE` / `SUPERSEDED` are dispositions, not deletion operations. All existing refs remain available.

### What each branch adds

- `codex/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0`: 23 commits after main: 38-chain replay/stops/H1 gates, target-direction correction, persistent snapshot v39a, updated 39A audit and handoff.
- `codex/SHI_RESET_39A_master_research_to_monitor_alignment_audit_v0`: 12 documentation-only commits; earlier 39A alignment package. No 38-chain replay or snapshot implementation.
- `codex/define-explicit-binding-bridge-and-update-spec`: Historical Phase 3 binding bridge/spec documents, PR #94. The named bridge file is absent from current main. No automatic reintroduction of legacy scope.
- `codex/fix-empty-minute-handling-and-open-interest-polling`: Head is the original aggregator commit, already an ancestor of main. Actual OI/empty-minute fix is later 1908ef8. No unique contribution.
- `codex/implement-h2-observational-outcome-layer`: Legacy H2 observational outcomes, PR #93. Current history has rewritten counterpart 6040e5b / merge a6f7099; not a current monitor promotion.
- `codex/implement-h2-patch-2-setup-extraction`: Legacy H2 impulse/reclaim extraction and research summary, PR #92; current history includes rewritten merge c8751af. Not a current monitor promotion.
- `main`: Old 37K-era base; retains GitHub default-branch role only. No new research may start here.

### Why “PR merged” is not “head contained”

GitHub reports #92, #93, and #94 as merged into historical main. Their original head objects are not ancestors of current main; current main shares only `1908ef8` with those old histories. Rewritten counterparts for #92/#93 exist in current history. The named #94 bridge file is absent from current main. This audit records those facts separately and does not merge hundreds of legacy commits to make ancestry look tidy.

Git records commits and parents, not a permanent “created from branch” property. The table therefore gives verified merge bases and, where available, the PR target/base SHA. Exact creation branch for refs without a PR is not claimed.

## Uploaded local branches

The ZIP is older than GitHub: checked-out local 38G is `434f10f`, remote 38G is `1c18766`; ZIP origin/main is `c83564f`, remote main is `1d868e8`. The ZIP has five modified tracked governance files plus untracked PROJECT_LOG and 38U audit. The supplied worktree is preserved; consolidation uses a separate worktree.

| Local codex ref | Local head | Base with main | Head in main / 38G | PR | Disposition |
| --- | --- | --- | --- | --- | --- |
| `codex/SHI_RESET_31_governance_cleanup` | `6fd59c1` | `6fd59c1` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_32_visible_liquidity_structure_monitor_v1` | `406e017` | `406e017` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_33_m15_first_class_structure_registry` | `8e80d63` | `8e80d63` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_36B_significant_zone_selector_v0` | `2cbfea3` | `2cbfea3` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_36C_trader_snapshot_builder_v0` | `c087007` | `c087007` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_37A_market_regime_hidden_flow_research_v0` | `5744a14` | `5744a14` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_37C_prune_hidden_flow_labels_v0` | `4076894` | `4076894` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_37D_episode_context_classifier_v0` | `5a7f862` | `5a7f862` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_37E_online_market_structure_state_memory_v0` | `4c9038d` | `4c9038d` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_38A_setup_replay_validation_v0` | `1d868e8` | `1d868e8` | True / True | none | SUPERSEDED |
| `codex/SHI_RESET_38B_armed_setup_manual_review_pack_v0` | `8678c87` | `1d868e8` | False / True | none | SUPERSEDED |
| `codex/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0` | `434f10f` | `1d868e8` | False / True | none | SUPERSEDED |
| `codex/research_episode_2026_03_22_to_2026_04_05` | `406e017` | `406e017` | True / True | none | SUPERSEDED |

These local milestones contribute no code beyond current 38G; every local codex head is its ancestor. They do not contain named 39A. Their head subjects and full SHAs are retained in the JSON inventory.

## Evidence limits

- 39A architecture source means the updated audit carried by current 38G, not the stale branch name alone. Existing research conclusions remain at their original evidence class.
- Current 38G documentation references local run outputs for 38U–38Y, but no files for those run roots are tracked in its tree. The supplied Aitrader ZIP and separate 38W ZIP do not establish a complete 38V/38W1/38X/38Y evidence set. Their historical numeric claims are not revalidated here.
- The supplied 38W summary is the original replay (51 TP1 touches, 48 stop-first rows), not the corrected 38W1 run. Do not treat it as corrected chronology or edge proof.
- No running server/container or cross-repository Executor integration was inspected. Existing statements about snapshot deployment are historical documentation, not a deployment verification from this audit.
- The uploaded untracked 38U audit is preserved in the input snapshot, not silently promoted into the canonical branch.

## Mandatory base policy

See `docs/CANONICAL_BASE.md`. New Market Monitor tasks must fetch and branch from the latest canonical branch and verify both historical anchors. No 39B/39C work from main, the old named 39A branch, or 38G directly is permitted. Existing research branches must first integrate canonical history.

Enforcement here is repository governance in AGENTS/README and mandatory ancestry checks. GitHub branch protection/default-branch settings are not changed; no server-side rejection of pushes is claimed.

## Validation

- The pre-governance merge tree equals the pinned 38G tree exactly.
- All existing Python, tests, configuration, feed, and run artifacts remain byte-for-byte unchanged relative to 38G; only Markdown plus the new audit inventory JSON are added/edited.
- `git diff --cached --check 1c18766462148943d99aa326f6093aed46e620e5`, repository/document consistency checks, and AST parsing of existing Market Monitor Python files passed before publication. Relative to the older named-39A parent, Git reports three pre-existing blank-at-EOF warnings inherited from 38G (setup_replay_validation.py, the 38I audit, and test_live_like_state_replay.py); they were preserved to keep source/tests unchanged.
- Attempted `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`: could not start because this environment has no `pytest` module. No passing-test claim is made. No dependencies were installed. The historical 718-pass record in 39A is not a result of this task.
- 39B/39C implementation, replay campaigns, feed changes, production changes, deployment, and service restarts are outside this task.

## Next gate

After remote canonical head and main retirement notice are verified, 39B/39C may be scoped from canonical. Canonical-base repair is not approval of a lifecycle algorithm or a trading strategy. Each implementation still needs its own contract/control cases.
