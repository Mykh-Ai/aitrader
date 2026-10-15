# Active Docs

Active docs describe the reset boundary, feed/data lineage, the 39A architecture audit, and the bounded v39A snapshot promotion completed on 2026-09-11.

Current active documents, in source-of-truth order:

1. `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
2. `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
3. `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
4. `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
5. `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`
6. `README.md`
7. `AGENTS.md`
8. `PROJECT_LOG.md`
9. `docs/ACTIVE_DOCS.md`
10. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
11. `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md` (post-38U architecture snapshot; retained as historical context and superseded by 39A where they differ)
12. `research/canonical/PROJECT_STATE_CURRENT.md`
13. `NEXT_TASK_MARKET_MONITOR.md`
14. `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md` (historical baseline / v1 spec)

Current status:

- 39A is the current canonical alignment source and its review is complete.
- The latest read-only point-in-time snapshot is documented in `research/canonical/SHI_RESET_39A_2026_09_29_1919UTC_SNAPSHOT_AUDIT_2026_09_29.md`; it uses the local feed through the latest verified closed minute and does not promote any lifecycle or trading policy.
- The 2026-09-17 20:00 UTC historical diagnostic snapshot and local feed update are documented in `research/canonical/SHI_RESET_39A_2026_09_17_2000UTC_SNAPSHOT_AUDIT_2026_09_25.md`; the 2026-09-18 07:00 and 13:00 UTC snapshots are documented in their respective canonical snapshot audits. These runs do not promote any remaining lifecycle item.
- The v39A snapshot contract is promoted for descriptive entry-time LLM evidence; remaining promotion items require separate scope.
- setup_builder is a context generator, not a final setup engine.
- Sweep must be modeled as a sequence/lifecycle event before new setup logic is added.
- The 38S 227 rows remain discovery material, not canonical candidates.
- 38W1 is corrected replay evidence, not edge proof.
- Chat/manual conclusions are preserved separately from code-confirmed and run-artifact-confirmed facts.
- Canonical 38U/38V/38W/38W1/38X/38Y audit files are absent in this checkout; their available conclusions remain run-artifact evidence unless another canonical source exists.
- Executor consumes the snapshot as advisory entry evidence only; trading-policy authority and Backtester promotion remain future gates.

Current research evidence index:

- [40P user-authorized Binance historical data acquisition](../research/canonical/SHI_RESET_40P_BINANCE_FUTURES_HISTORY_ACQUISITION_AUDIT_2026_10_15.md) —23official ZIP/checksum pairs,2025-03-01–2026-03-09 plus Februarywarmup;578880right-close minutes/402daily files,zero missing/duplicate labels,18nontraded rows retained. Local bulk cache with committed exact URL/hash inventories. Data-only follow-up; OOS strategy outcomes remain unseen and40Ogate remains failed. [Data handoff](../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/README.md).

- [40O official Binance Futures source-parity audit](../research/canonical/SHI_RESET_40O_BINANCE_FUTURES_ARCHIVE_OOS_VALIDATION_AUDIT_2026_10_15.md) — **BINANCE_KLINE_SURROGATE_PARITY_FAILED**:July one extra allowed long/99.865591%parity,September100%,required100%unmet.27checksums/frozen40H13-row reproduction/causal prefixes/784tests pass. Data was undownloaded at40Ostop; later40Pacquires it without inspecting strategy outcomes or tuning. Source-equivalence resolution precedes server shadow/API stages. [Run result](../market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0/result.md).

- [40M canonical research and deployment roadmap](../research/canonical/SHI_RESET_40M_RESEARCH_AND_DEPLOYMENT_ROADMAP_AUDIT_2026_10_15.md) — consolidated40A–40L evidence/decisions, exact selected40H rules/latest40L money, rejected alternatives, offline reproduction and byte-verified transfer inventory, proposed server/API milestones. Documentation handoff only;39A architecture and all research/live boundaries remain unchanged. Run:`market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/`.

- `research/canonical/SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md`, `research/latest_own_signal_replay.json` and `market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/result.md` (latest completed40H continuation throughOctober14;14closed/8wins/6losses/+1060.91USDC, October−29.90, no open/data-censored positions; all13control trades retained,15tests/14paths/prefix and source identity verified; frozen chosen-rule pointer unchanged)

- `research/canonical/SHI_RESET_40K_DATA_REFRESH_AUDIT_2026_10_15.md` and `market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0/data_readiness.json` (user-authorized server futures update and official spot13–14October; both complete, old230source identities preserved; common cutoffOctober14 23:59UTC; the later financial continuation is40L)

- `research/canonical/SHI_RESET_40J_SHORT_DELTA4_MIRROR_AUDIT_2026_10_15.md` and `market_monitor_runs/SHI_RESET_40J_short_delta4_mirror_v0/result.md` (user-directed short4h<0 mirror removes June1winner387.18, no loss avoided/new trade; full net703.63/six-month754.92; extra rule rejected, selected40H pointer preserved;13tests/25paths)

- `research/canonical/OWN_SIGNAL_RESEARCH_SELECTION_2026_10_15.md` and `research/active_own_signal_selection.json` (user selects frozen40H combined24h-band4%/long4h-positive candidate with all inherited baseline rules;40I remains unselected alternative; research selection only, no new run or production authority)

- `research/canonical/SHI_RESET_40I_ENTRY_FREQUENCY_EXPANSION_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/result.md` (130finite adaptive portfolios; moderate alternative16April–September trades/+1150.20USDC/DD125.27 versus40H12/+1142.11/DD74.61, full18/+1156.80; all baseline winners retained;17tests/2450rows/59unique first touches;24trade strong goal unmet,40H retained control; borrowing/holdout/production not established)

- `research/canonical/SHI_RESET_40H_LOSS_METRICS_FILTER_STUDY_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/result.md` (all13 spot losses versus8wins;22 full-book filter replays; frozen adaptive delta24-band/longdelta4 research candidate13trades/8wins/5losses/+1090.81USDC full/+1142.11 April–September; all original winners retained, new loss included;16tests/345paths; no holdout/production or actual-borrow claim;40G preserved control)

- `research/canonical/SHI_RESET_40G_FUTURES_SIGNALS_SPOT_EXECUTION_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/result.md` (current two-feed research contract: futures BTCUSDT signals, BTCUSDC Spot execution, +676.37 USDC full/+845.02 April–September after assumed fees/slippage; borrowing unverified; H4/management additions did not improve baseline; all prior proxy results retained)

- `research/canonical/SHI_RESET_40F1_SHORT_PROTECTION_2R_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40F1_short_protection_2R_v0/result.md` (user-directed 2R trigger with unchanged +0.25R stop; original net +$408.15, filtered candidate unchanged +$671.05; no selected successor)

- `research/canonical/SHI_RESET_40F_DIRECTION_EXPIRY_STOP_INTERVENTIONS_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/result.md` (all six expiry cases; 16 declared interventions; short-space research variant +$671.05 full net /+$839.79 April-September; fewer losses but fewer absolute wins; baseline and all incomplete trials retained)

- `research/canonical/SHI_RESET_40E_HYBRID_STOP_DIAGNOSIS_AUDIT_2026_10_14.md` and `market_monitor_runs/SHI_RESET_40E_hybrid_stop_diagnosis_v0/diagnosis_summary.md` (all 16 stops separated by direction; 20 controlled target pairs; 40D baseline preserved; diagnostic associations are not promoted filters)

- `PROJECT_LOG.md`
- `research/canonical/`
- `market_monitor_runs/`
- `research/canonical/SHI_RESET_40A_OWN_SIGNAL_CAUSALITY_PREFLIGHT_AUDIT_2026_10_13.md` (saved 38V/38W1 source-causality failure; own-signal research prerequisite, no financial Backtester run or edge promotion)
- `research/canonical/SHI_RESET_40B_OWN_SIGNAL_RUN_PREPARATION_AUDIT_2026_10_13.md` and `research/own_signal_run/README.md` (executable isolated experiment preparation; fixed hypotheses/cost assumptions, subsequently executed in 40C without production promotion)
- `research/canonical/SHI_RESET_40B1_SINGLE_MINUTE_TOLERANCE_AUDIT_2026_10_13.md` (current user-directed quality policy; v1 skips isolated missing/synthetic minutes without entry quarantine or trade interruption, retaining clocks and provenance)
- `research/canonical/SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md` (completed frozen own-feed signals and financial proxy replay; 21 resolved trades, demand -2.41R base net, seller -2.03R, supply no trades; no profitable family or production promotion)
- `research/canonical/SHI_RESET_40D_OWN_SIGNAL_STRATEGY_SEARCH_AUDIT_2026_10_14.md` and `research/strategy_search/README.md` (user-authorized iterative search; historically selected one-book candidate +$512.28 full net /+$579.02 six-month entries at $3,000 notional, $5 commission and explicit slippage; no pristine holdout, borrow-cost or live-edge claim)
- `research/canonical/PEAK_AI_FIVE_DELTA_LEVEL_FLOW_ABLATION_AUDIT_2026_10_12.md` (research-only liquidation/OI level-qualification ablation; not promoted selector policy)

Archived historical docs remain evidence and must not be used as current implementation plans unless the user explicitly asks for archive review:

- `docs/Spec_v1.0.md`
- `docs/Phase2_Implementation_Plan_AiTrader_v2_2_updated.md`
- `docs/Analyzer_Run_Storage_v0.1.md`
- `docs/Phase3_Multi_Ruleset_Replay_Roadmap.md`
- `docs/Backtesting_Spec_v0.1.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/H4_False_Break_Reclaim_Research_Contract_v0.1.md`

New work must keep `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, this file, `research/canonical/PROJECT_STATE_CURRENT.md`, and `NEXT_TASK_MARKET_MONITOR.md` aligned.

40N publication preserves both the40M research handoff and the existing production-continuity ADR`docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md`. Read `research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md` for exact snapshot reproduction after the merge; do not rewrite historical source/code hashes to match current runtime files.
