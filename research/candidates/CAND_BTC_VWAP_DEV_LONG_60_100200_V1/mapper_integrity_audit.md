# CAND_BTC_VWAP_DEV_LONG_60_100200_V1 Mapper Integrity Audit

verdict: `PASS`

- event_time <= signal_close_time < entry_time checked through candidate mapping and executed trades.
- entry price equals next M1 open.
- stop equals event high/low according to side.
- target equals entry-time DayVWAP.
- expiry equals frozen horizon.
- one-active-position overlap check applied.
- skipped events recorded: `150`.
- no future outcome fields are used by Sprint 08 mapper/replay.

Issues:
- None.
