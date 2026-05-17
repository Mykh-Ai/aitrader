# CAND_H4_FAILED_BREAK_RECLAIM_EXTENDED_V1

Status: quarantined as current implementation; redesign watch only. Not live.

Current `FAILED_BREAK_RECLAIM_EXTENDED_V1` is invalid for the intended H4 Candle A/B/C false-break/reclaim setup. It detects M1 failed-break events against latest H4 swing-level lineage.

Do not use current R/MFE/backtester arithmetic as evidence for H4 edge.

Next action: implement a new explicit H4 A/B/C detector, then replay on clean/recovered data with minimum risk and cost viability gates.
