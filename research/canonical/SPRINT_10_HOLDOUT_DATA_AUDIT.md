# Sprint 10 Holdout Data Audit

as_of_date_utc: `2026-05-17`
sprint08_rules_commit: `50d43566c03759b18d1c7cfac9d094e76496df59`
sprint09_integrity_commit: `fa8a30fe0bc7474076ad8dbfb4e76dd75a9e9fea`

feed_days_audited: `68`
usable_holdout_days: `0`
days_blocked_as_already_used: `66`

Holdout rule: any day present in the frozen Sprint 06/Sprint 08 source feature window is excluded.
Synthetic rows, zero OHLC rows, partial UTC days, and contaminated primary gap rows are not accepted as holdout evidence.

No usable holdout day exists in the current local feed snapshot.
