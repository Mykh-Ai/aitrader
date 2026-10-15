# Own-feed strategy search and historical candidate

Research only. The user explicitly authorized iterative signal/filter/exit search after 40C and supplied $3,000 position notional, $5 total commission per completed trade and a minimum $500 historical net result. This package does not activate legacy Backtester promotion or Executor behavior.

Current candidate: `SHI_RESET_40D_HYBRID_CANDIDATE_V1`, frozen in `market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/selected_strategy.json`.

The selected one-position portfolio uses LONG trend retests with completed price/volume/delta context and SHORT accepted support breaks. It has 26 historical trades, +$673.55 gross, $130.00 commissions, $31.28 adverse slippage and **+$512.28** model net. Its April-September entry cohort has 23 trades and **+$579.02**. Initial risk is structural and differs by trade; $3,000 is position notional, not risk. No selected trade is unresolved or uses a conservative missing-data mark.

Reproduce and independently verify the frozen candidate from the repository root:

```powershell
python market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/_verify_selected_candidate.py
```

Read `selected_result.json` and `selected_trade_ledger_usd.csv` for dollars, normalized R, stops/targets and actual exits. Source/code hashes must match. The historical candidate was selected after searching previously researched history; it is not an untouched holdout result, validated edge or a live strategy. Borrow interest is not modeled. Prices are BTCUSDT feed proxies reported as dollars with USDT/USD parity assumed.

`features.py` computes completed H1 references and causal rolling market/flow context from the full prior chronology. `hybrid.py` retains one global position book and a three-minute cooldown. `replay.py` executes minute paths with stop-first collisions, adverse stop gaps, actual timestamps, isolated-minute skip and fixed $5 round-trip commission plus 2 bps adverse slippage per fill. The selected candidate uses strict censoring for extended/recovered data. A separate explicitly labeled short-gap stop-debit sensitivity exists in the run root but is not used in the selected result.

The package's original `search` CLI and run-artifact batch scripts preserve experimental provenance. Completed studies must not be overwritten with changed rules. Original batch 01-03 code is retained in `frozen_code_batch_01_03/`; later source revisions have their own hashes. New candidates require a separately declared study. Ten tests exercise clocks, monetary accounting, trade-specific risk, gap handling, future append invariance, conflicts and global concurrency.
