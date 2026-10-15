# Historical candidate: own signals, dollars per $3,000 position

**Full available history: +$512.28 after $5 commission per completed trade and 2 bps adverse slippage per fill.**

| Entry interval | Trades | Gross price PnL | Commission | Slippage | Model net |
| --- | ---: | ---: | ---: | ---: | ---: |
| March 18-September 30, exits through October 12 | 26 | +$673.55 | $130.00 | $31.28 | **+$512.28** |
| April 1-September 30, with exit tail | 23 | +$721.70 | $115.00 | $27.69 | **+$579.02** |

One global position, fixed $3,000 raw entry notional, no compounding. LONG on a trend retest; SHORT after two completed H1 closes accept a support break. Signals use AiTrader feed only. LONG target is 10 times its own structural price risk, SHORT target 6 times; both have a seven-day maximum hold. This is a target multiplier, not a constant dollar stop.

- Average net trade: **+$19.70 / +0.77R** across all 26. April-September: **+$25.17 / +0.92R**.
- Initial stop risk: average **$48.78**, minimum $18.27, maximum $74.39. Each trade has its own initial price stop.
- Planned full target: average **$380.17 / 8.15R** across all trades; not every trade reaches it.
- Four actual target exits: mean **+$238.28 net**, mean target multiple 8R, mean time to target 55.87 hours.
- Closed-trade cash drawdown: **$459.17**. Profit factor: 1.578. All 26 trades have observed exits; no short-gap conservative mark contributes to this result. Four isolated omitted minutes are recorded and tolerated.

Files: `selected_strategy.json` (frozen rules and code identity), `selected_trade_ledger_usd.csv` (all trades), `selected_result.json` (metrics and verification), `selected_monthly_results.csv` (monthly entry cohorts), `selected_artifact_hashes.json` (identity).

Reproduce from the repository root:

```powershell
python market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/_verify_selected_candidate.py
```

This is a candidate selected on already researched history, not independent unseen-data confirmation. The small sample depends on a few large wins. The price market is a BTCUSDT proxy; actual margin borrow interest and executable BTC/USDC prices are not modeled. Commission is the user's stated $5 assumption, not an independently verified account tariff.
