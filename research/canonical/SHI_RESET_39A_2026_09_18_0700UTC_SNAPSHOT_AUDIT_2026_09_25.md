# SHI RESET 39A Historical Snapshot: 2026-09-18 07:00 UTC

Verdict: `PASS / HISTORICAL_DIAGNOSTIC_SNAPSHOT`

This is a read-only BTCUSDT Market Monitor snapshot at the exact closed-minute cutoff `2026-09-18T07:00:00Z`. It follows the same offline method as the 2026-09-17 20:00 UTC snapshot. It is descriptive evidence, not a candidate, trade signal, edge claim, or live-like lifecycle validation.

## Inputs and reproduction

- Run root: `market_monitor_runs/SHI_RESET_39A_2026_09_18_0700UTC_snapshot_v0/`.
- Main source: locally updated SHI `feed/`; `feed/2026-09-18.csv` SHA-256 is `8aec2ec514f68a79e3e49231d755ac805f03143d435fe8b32139809f4e12b4ba`, previously checked against the server copy.
- During the documented outage `2026-04-23T17:05:00Z` through `2026-05-06T22:51:00Z`, the run selected `feed_recovered/` minute by minute and marked it degraded. No feed source was modified.
- The run used the copied server `market_monitor/` package under `server_copy/`; its v39A builder matches the repository version. Source hashes, code, diagnostics, and the full snapshot JSON are retained in the run root.
- Reproduce locally with `python -m market_monitor_runs.SHI_RESET_39A_2026_09_18_0700UTC_snapshot_v0.build_snapshot`.

## Snapshot at cutoff

| Field | Value |
| --- | ---: |
| Close price | 77,561.30 USDT |
| 5/15/30/60/240/1440-minute windows | All `COMPLETE_RAW` |
| 60-minute change / delta | +0.13375042% / -883.401 BTC |
| 240-minute change / delta | +0.79729375% / -387.915 BTC |
| 1440-minute change / delta | +1.45588587% / +112.140 BTC |
| v1/37E market state | `EXPANSION_UP`, MEDIUM confidence, UP bias |
| v1 support | 73,635.1–75,767.5 USDT |
| v1 resistance | 78,113.2–79,974.8 USDT |

The six local windows contain no missing or duplicate minute. The cutoff row is present, and no later row entered the calculation. The 1440-minute window begins at `2026-09-17T07:01:00Z`.

## Data quality and boundary

The loaded history spans `2026-03-11T13:45:00Z` through the cutoff, with 274,634 rows and 13 missing minutes across that full span. None of those gaps lies in the six snapshot windows. The adapter conservatively marks 36,614 historical rows `RECOVERED_DEGRADED`; overall readiness is `READY_WITH_RECOVERED_DATA`, while each local window is `COMPLETE_RAW`.

The v1 base snapshot used 421 cutoff-day rows and 43,201 rows of 30-day context. Its structure, zone, and state outputs are explicitly v1/37E context. The v39A state file was not loaded or changed; `state_memory.continuity=INITIALIZED`. This offline run did not replay production runtime state across every earlier closed candle and must not be presented as fully continuous live-like monitoring.

Compared with the separate 2026-09-17 20:00 UTC diagnostic snapshot, the close price is 1,000.10 USDT higher and the v1 state label differs (`CONTEXT_BELOW_RESISTANCE` then, `EXPANSION_UP` here). These two point-in-time results alone do not establish a validated state transition or trading conclusion.
