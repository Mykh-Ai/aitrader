# CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 No-Lookahead Check

Result: `PASS_MAPPING_NO_OUTCOME_PREDICATES`.

- Selected Sprint 06 clustered discovery events: 305.
- Valid replay mappings: 301.
- Invalid mappings: 4.
- Entry uses only event close plus next M1 open from Sprint 06 feature rows.
- Stop uses event high/low from event bar.
- Target uses DayVWAP observed at entry timestamp and is frozen.
- Sprint 06 discovery outcomes are not read by this mapper.

Invalid reasons:

- `short_stop_not_above_entry`: 2
- `short_target_not_below_entry`: 2
