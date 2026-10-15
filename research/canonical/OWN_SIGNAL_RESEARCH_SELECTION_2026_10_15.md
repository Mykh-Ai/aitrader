# User selection — frozen40H candidate

Date:2026-10-15, Europe/Budapest. The user quoted the original40H two-delta result and chose that version as the main research candidate. This records a selection decision, not a new experiment or production promotion.

Selected contract:`market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/selected_research_contract.json`, variant `LONG_DELTA4_POS_BOTH_BAND4`.

-Both long and short require weighted rolling24h futures delta strictly between−4% and+4%.
-Long additionally requires weighted rolling4h futures delta strictly positive.

The selection inherits the **entire frozen40H baseline**, including own entry families, the short opposing-H4-space1R screen, causal futures-to-spot reference mapping, fixed exits, costs and global book. It does not remove all other original entry requirements. The user's singular word "filter" refers here to the quoted combined screen; selecting24h-band alone would instead be a different15-trade result and must not be silently substituted.

40I's added first48h breaks, new-event6% band and0.75R short-space relaxation remain preserved experimental alternatives and are not part of the selected candidate. Their evidence is retained without deletion or rewriting.

Existing historical evidence:13trades/8positive/5negative,1090.811851USDC full net; April–September12entries/1142.108729USDC; closed-trade DD74.610063. Figures include stipulated5USDC/trade commission and2bps/fill slippage, before actual borrowing. No new replay or parameter tuning performed for this decision. Historical selection is still not pristine holdout or live-edge evidence.

Machine-readable research selection:`research/active_own_signal_selection.json`. It points to the immutable contract/result/ledger with SHA256; no runtime consumer or live behavior is added. Next research confirmation uses40H fixed rules on a genuinely unused subsequent period. Previous audits and run artifacts remain immutable.
