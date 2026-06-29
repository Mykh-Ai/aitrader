# SHI RESET 38G Live-Like Bar-By-Bar State Replay Audit

Scope: research-only live-like M1 bar-by-bar state replay. No sample expansion, no setup detection rule changes, no Setup Builder rule changes, no Backtester execution logic, no Executor, no orders, no entries/exits, no PnL, no position sizing, no live-readiness, and no strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0`

Required outputs:

- `live_like_bar_by_bar_state_replay.csv`
- `state_transition_log.csv`
- `setup_status_transition_log.csv`
- `reference_level_transition_log.csv`
- `focus_setup_alignment_check.csv`
- `live_like_replay_summary.md`
- `live_like_replay_manifest.json`

## Replay Runs

- `run_2026_06_25_0800_1500`: `2026-06-25T08:00:00Z -> 2026-06-25T15:00:00Z`
- `run_2026_06_23_0600_2200`: `2026-06-23T06:00:00Z -> 2026-06-23T22:00:00Z`
- `run_2026_03_26_0000_1000`: `2026-03-26T00:00:00Z -> 2026-03-26T10:00:00Z`

Runner boundaries are inspection boundaries only. They are not market concepts and are not passed into monitor logic.

## Results

- Replay rows: 1983
- State transitions: 27
- Setup/status transitions: 10
- Reference transitions: 13
- Focus setup matches: 5/5
- `future_data_used_for_detection=false`: 1983/1983 rows

## Focus Setup Alignment

| focus_timestamp | expected_setup_type | alignment_verdict | setup_reference_level | actual_setup_price | tradable_entry_anchor | stop_reference |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-25T11:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | MATCH | 59628.3709 | 61244.7 | 61244.7 | 61286.628 |
| 2026-06-23T08:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | MATCH | 62637.36565 | 62326.6 | 62326.6 | 63241.2048 |
| 2026-06-23T18:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | MATCH | 63241.2048 | 62219.4 | 62219.4 | 63241.2048 |
| 2026-03-26T01:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | MATCH | 68081.7421 | 71233.6 | 71233.6 | 71267.616 |
| 2026-03-26T07:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | MATCH | 71267.616 | 70057.2 | 70057.2 | 71267.616 |

## 2026-06-25T11:59Z Inspection

- Setup type: `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- Setup reference level: `59628.3709`
- Actual setup price: `61244.7`
- Tradable entry anchor: `61244.7`
- Stop reference: `61286.628`
- Target reference: `zone_000102:SELL_SIDE:59500.93465-59560.46535`
- Source-window high: `61395.3`
- Source-window low: `61033.5`
- Local swing high candidate over live-like rolling context: `61897.6`
- Local swing low candidate over live-like rolling context: `61033.5`
- Structural zone context: `below_62000_62200_support_resistance_flip_review_zone`

This confirms the 38F price-reference contract: `59628.3709` is a structural/reference level, not the tradable entry anchor. The replay uses `61244.7` as the actual/tradable setup price.

`61395.3` is the source-window high. It differs from the broader local swing high candidate `61897.6`, so it should remain context only until a structural swing-stop resolver exists.

## Required Conclusions

1. Batch setup artifacts reproduce in live-like bar-by-bar mode when the corresponding setup timestamp is reached.
2. This replay does not prove independent live detection, because it uses existing 38C reviewed setup rows as status checkpoints. It verifies timestamp availability, non-future use, and price-reference behavior.
3. No setup depends on runner end boundaries; every replay row records `future_data_used_for_detection=false`.
4. The 38F price-reference contract is respected.
5. Source-window high/low should be treated only as context until a structural swing-stop resolver exists.
6. The next task should be either:
   - structural swing-stop resolver, or
   - state-transition explanation audit.

## Governance Check

- Sample expansion: false
- Setup detection changed: false
- Setup Builder changed: false
- Backtester execution logic added: false
- Executor added: false
- Orders added: false
- Entries/exits added: false
- PnL added: false
- Position sizing added: false
- Live-readiness added: false
- Strategy promotion added: false

## Verdict

SHI_RESET_38G_LIVE_LIKE_BAR_BY_BAR_STATE_REPLAY_V0_CREATED
