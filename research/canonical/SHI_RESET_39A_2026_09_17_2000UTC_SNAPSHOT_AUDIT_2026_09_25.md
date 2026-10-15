# SHI RESET 39A Historical Snapshot: 2026-09-17 20:00 UTC

Verdict: `PASS / HISTORICAL_DIAGNOSTIC_SNAPSHOT`

This is a read-only BTCUSDT Market Monitor snapshot at the exact closed-minute cutoff `2026-09-17T20:00:00Z`. It is descriptive evidence, not a candidate, trade signal, edge claim, or live-like lifecycle validation.

## Inputs and reproduction

- Run root: `market_monitor_runs/SHI_RESET_39A_2026_09_17_2000UTC_snapshot_v0/`.
- Main feed: server `/opt/aitrader_data/feed/YYYY-MM-DD.csv`, copied into local `feed/`. The 88 previously missing full days `2026-06-29` through `2026-09-24` were added; the incomplete `2026-09-25` day was not retained.
- Existing local files through `2026-06-28` were preserved. The overlapping `2026-06-28` SHA-256 matched the server. All 88 new local files matched the server SHA-256 manifest, retained the expected schema, had 1,440 rows each, and had ordered unique UTC-minute timestamps.
- During the documented outage `2026-04-23T17:05:00Z` through `2026-05-06T22:51:00Z`, the run selected `feed_recovered/` minute by minute and marked it degraded. No feed source was rewritten or synthesized.
- The run used the copied server `market_monitor/` package under `server_copy/`; its v39A builder SHA-256 matches the repository version. `build_snapshot.py`, `source_manifest.csv`, `server_sha256.txt`, `diagnostics.json`, and `snapshot_v39a.json` are in the run root.
- Reproduce locally with `python -m market_monitor_runs.SHI_RESET_39A_2026_09_17_2000UTC_snapshot_v0.build_snapshot`.

## Snapshot at cutoff

| Field | Value |
| --- | ---: |
| Close price | 76,561.20 USDT |
| 5/15/30/60/240/1440-minute windows | All `COMPLETE_RAW` |
| 60-minute change / delta | +0.02874344% / +206.034 BTC |
| 240-minute change / delta | -0.24833294% / -209.755 BTC |
| 1440-minute change / delta | +0.67602841% / -283.343 BTC |
| v1/37E market state | `CONTEXT_BELOW_RESISTANCE`, LOW confidence, MIXED bias |
| v1 support | 72,458.7–73,985.8 USDT |
| v1 resistance | 77,255.0–79,555.5 USDT |

The six local windows contain no missing or duplicate minute. The cutoff row is present, and no later row entered the calculation. The 1440-minute window begins at `2026-09-16T20:01:00Z`.

## Data quality and boundary

The loaded history spans `2026-03-11T13:45:00Z` through the cutoff, with 273,974 rows and 13 missing minutes across that full span. None of those gaps lies in the six snapshot windows. The adapter marks 36,614 historical rows `RECOVERED_DEGRADED`, including recovered outage rows and whole raw files conservatively marked degraded when they contain synthetic rows. Thus the overall readiness reads `READY_WITH_RECOVERED_DATA`, while each local window is `COMPLETE_RAW`.

The v1 base snapshot used 1,201 cutoff-day rows and 43,201 rows of 30-day context, matching the server builder's input shape. Its structure, zone, and state outputs are explicitly v1/37E context; some significant zones carry recovered/degraded provenance. The v39A state file was not loaded or changed. `state_memory.continuity=INITIALIZED` means this offline run did not replay the production runtime state across every earlier closed candle. It must not be presented as a fully continuous live-like monitor run.

The untracked `tmp_llm_last_two_evidence/` directory was not modified.
