# SHI Market Monitor Known Gaps and Next Promotions

Date: 2026-07-02
Status: Documentation-only backlog

No new code promotion should happen until `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md` is reviewed.

This file records future work only. SHI_RESET_39A does not implement any of these items and does not add tests for them.

## Next promotion candidates

1. Level lifecycle memory.
2. Sweep sequence classifier with next 1-3 H1 confirmation.
3. Counter-sweep invalidation.
4. Accepted break vs reclaim classifier.
5. Support/resistance blocker for setup_builder.
6. Target resolver using market_structure_levels, not only visible selected_zones.
7. Last-wagon by prior move distance/maturity.
8. Minimum structural risk / meaningful R validation.
9. Local sequence direction override versus broad market state.

## Boundary

Market Monitor remains research infrastructure. `setup_builder` remains a context candidate generator, not a final setup engine. 38S rows remain discovery material, not candidates. Replay evidence is not edge proof. Manual conclusions remain separate from code-confirmed facts.
