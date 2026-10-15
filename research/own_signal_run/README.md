# Own-signal offline experiment v1

Preparation task: `SHI_RESET_40B_OWN_SIGNAL_RUN_PREPARATION`.

User correction, 40B1: an isolated missing or synthetic minute must not interrupt the experiment. `contract_v1.json` and preparation output `SHI_RESET_40B_own_signal_run_preparation_v1/` supersede v0's strict single-minute quality blocks. Historical v0 artifacts and rules remain unchanged as evidence. Entry-family thresholds, costs, exits and periods are unchanged.

This package prepares a bounded research experiment from AiTrader's own feed. It imports 37E pressure/state and 38M qualification primitives, and adds a versioned causal chronology, explicit signal contract and an isolated fixed-exit proxy replay. It does not import Scout seeds, old Analyzer candidates, 38S candidates or saved 38V/38W1 outcomes. It does not enable the legacy Backtester as a promotion gate or change production Monitor/Executor behavior.

These are three new, explicit research hypotheses. They are not a claim that the historical 51 candidates have been repaired or reproduced.

The user-authorized frozen v1 run completed as 40C on 2026-10-14 under `market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0/`: 63 gate-passing signals, 21 resolved trades, zero censored. Demand has 20 trades and -2.41R assumed base net (-10.12R stress); seller has one trade and -2.03R base; supply has none. No profitable family is established. Read `research/canonical/SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md` before a follow-up; preserve these outputs and freeze changed studies separately.

## Frozen entry rules

All three use closed UTC H1 bars, confirmed H1/H4 swings, immutable level identity and fixed zones at +/-5 bps. H1 swings require two usable closed bars on each side; H4 requires one. An isolated omitted minute does not invalidate a bar: OHLC/flow use real observations only, with the omission count retained. Availability is the close of the final confirming bar; if its boundary minute is absent, availability waits for the next real close. No future value fills the hole. Extended gaps/recovered confirmation windows cannot form references.

At each available H1 close the engine updates its retained level inventory, qualified sequences, deduplication and 37E state/pressure context. Pressure is computed from real observations in the trailing 24 hours through the current decision, never from the remainder of the day. Missing/synthetic minutes are skipped without compressing physical time or resetting retained state. The explicit initial warm-up is 168 hours. Technical chunks must use the same engine instance; cross-process resume is not supported.

| Family | Price/sequence trigger | Existing pressure criteria |
| --- | --- | --- |
| Seller dominance retest down | H1 touches the known upper band, closes below its lower bound and below its open | SELLER dominant, seller pressure >=70, buyer response <=35 |
| Supply sweep/reclaim down | Existing 38M qualified H1 sweep of the same known upper reference, followed by completed close-back within the next 1-3 hours | overhead supply >=70 and seller pressure >=50 |
| Demand sweep/reclaim up | Symmetric 38M lower-reference sequence and later completed close-back | underlying demand >=55 or buyer response >=25 |

Additional frozen gates:

- Entry H1 volume >=1.3 times the median of the **previous** 20 usable closed H1 bars; volume is summed from observed rows without imputing skipped quantities.
- Directional `(BuyQty-SellQty)/Volume` >=0.04 for long, <=-0.04 for short.
- Stop distance at decision >=0.25 of the current closed H1 ATR(14).
- Sweep stops use the penetration high/low plus the existing 1 bp buffer. Retest stops use the farther of the upper band and rejection H1 high, plus 1 bp.
- The nearest complete opposite structural band is the target/blocker. If its first boundary provides less than 2R, reject; never skip it to select a convenient farther target.
- One accepted candidate per family, immutable source level and UTC day. Every rejection remains in the candidate journal.
- Two successive usable closes beyond a source band classify it as an accepted break for this experiment. Pending opposite qualified penetrations in the same confirmation sequence block admission. Levels older than 30 days are ineligible but remain in memory.
- An isolated missing, synthetic or invalid primary minute is omitted from calculation without a quality-based entry refusal or 24-hour quarantine. Several separated single-minute omissions are also tolerated. Consecutive omissions longer than one minute and recovered/unsupported observations remain a separate quality condition. All counts/provenance remain visible; source data is never rewritten.

H1 reference strength is 65 and H4 is 75, inherited from Monitor structure weights. Consequently the >=70 supply-context criterion makes H4 references necessary for this initial supply experiment. That restriction is explicit, not a fitted result. OI/liquidation observations are recorded; this first baseline does not promote them to additional entry gates. The complete 39A lifecycle/backlog is not implemented or promoted by this research package.

## Clock and execution experiment

Raw `Timestamp=T` describes the minute ending at T. H1 `(00:00,01:00]` therefore comprises raw close labels 00:01 through 01:00. Normal decision is at 01:00. The frozen latency is one full minute: planned entry open at 01:01 uses the `Open` from raw row **01:02**. If exactly that minute is missing/synthetic, use the next real candle open, record its actual timestamp and one-minute delay, and check geometry at its real price. The candle is selected by chronology, never by a favorable price. Require every input's `available_at <= decision_at < planned_entry_open_at`. A missing H1 boundary similarly defers the decision until the next real close rather than backdating it; reclaim windows retain nominal H1 close times.

One fixed exit policy is tested per family: full exit at the frozen structural target, initial stop, or 48-hour expiry. TP1 partials, BE, trailing and portfolio sizing are not part of this baseline. Entry gap geometry is checked at the actual open. Stops gapped through fill at the worse open; simultaneous stop/target touches resolve stop first and retain the collision flag. Targets never receive favorable gap improvement. Expiry/carry use elapsed UTC time. During a trade, an isolated missing/synthetic minute is skipped and replay continues with the next real bar. No touch or fill is fabricated inside the absent minute. Entry/trade omission counts are included in the journal and summary. Extended gaps, recovered data or unfinished tails remain explicitly censored.

Each family has one independent position book. Families can overlap, so summed family R must not be presented as account equity. Output drawdown is in cumulative trade R per independent family/period.

The market is `BTCUSDT_FEED_PRICE_PROXY`. This is not executable BTC/USDC Spot Margin evidence. Three frozen cost scenarios apply to the identical fills:

| Scenario | Fee per fill | Adverse slippage per fill | Assumed adverse carry per hour |
| --- | ---: | ---: | ---: |
| Zero-cost diagnostic | 0 bps | 0 bps | 0 bps |
| Assumed base | 5 bps | 2 bps | 0.1 bps |
| Assumed stress | 10 bps | 5 bps | 0.2 bps |

Fees apply to both slipped fill notionals; slippage and adverse carry are deducted separately. Carry applies conservatively to full entry notional for elapsed hours; it is not a reconstruction of actual funding or margin borrowing. These are hypotheses, not verified account tariffs. R normalization does not allocate capital or size live positions.

## Dataset and period discipline

`contract_v1.json` freezes source March 11 13:45 through October 12 23:59 UTC. October 13's changing file is excluded. Recovery selection is minute-precise inside the known April 23-May 6 outage. Primary placeholder rows are not substituted for missing recovery. Entry exclusions continue through May 9, preserving the earlier user-directed exclusion; context is carried without a reset.

Development, chronological validation and later historical validation are separated by 48-hour context-only purges. A final context-only tail allows exits to complete. Every historical period is already exposed to prior research to some degree and is labelled accordingly; no untouched holdout claim is made. Rule changes require a separately versioned experiment. No automatic threshold or parameter search exists.

## Commands

Run from the repository root with the existing Python environment:

```powershell
python -m research.own_signal_run prepare
python -m research.own_signal_run smoke
```

Preparation freezes the contract, source-file hashes, relevant code hashes and data-quality inventory under `market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/`. Smoke processes the startup chronology through March 25 14:00 with all available prior context, verifies future-append invariance and chunk continuity, and produces no financial replay. Full-run modes below are supported by the package. The user subsequently authorized their financial experiment in 40C, which used copied verified preparation records in a separate run root and one engine instance across weekly progress checkpoints:

```powershell
python -m research.own_signal_run signals
python -m research.own_signal_run replay
```

Changed source files, code or contract abort a frozen run. Replay additionally verifies the generated candidate journal's recorded hash. The numerical output is an isolated research harness rather than activation of legacy Backtester campaigns or their promotion logic.

The package's default output remains the preparation root. 40C used `--output market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0` for replay; its signal progress wrapper is a run artifact, not promoted package code. Preserve completed outputs before any rerun, since package signal/replay commands can overwrite their own output files. A changed hypothesis requires a new version and preparation identity.

Outputs include candidate decisions/rejections, state continuity, entry admission/rejections, trade/fill economics and family-period results for every cost scenario, including zero-trade families. Censored counts, sample limitations and concentration in the best three trades are explicit. Thirty trades is only a small-sample warning threshold, never an edge acceptance rule.
