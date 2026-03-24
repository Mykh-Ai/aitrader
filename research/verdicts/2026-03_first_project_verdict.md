# A. Executive verdict

У першому заархівованому керівному verdict для Ші зафіксовано два негативні режими дослідження.

Перший режим:
- candidate доходить до replay,
- але replay завершується REJECT.

Другий режим:
- analyzer не формує replayable candidate,
- бо daily setup density падає до рівня, недостатнього для shortlist і formalization.

Перший non-REJECT candidate досі не з’явився.
Project state залишається research-only.
Підстав для зміни production logic, execution policy або architecture transition немає.

# B. Що реально нового

- Runs `2026-03-15`, `2026-03-16`, `2026-03-17` дали replayable rulesets, але всі derived runs завершились REJECT.
- Runs `2026-03-18` → `2026-03-23` показали інший негативний режим:
  `NO_REPLAY / FormalizationEligible=0` на daily windows.
- Follow-up diagnostic показав, що FE=0 серія не є pipeline bug.
- Основний розрив у weak regime виникає на рівні setup density:
  daily windows у періоді `2026-03-18 → 2026-03-23`
  дали лише `1–3 setups` на run і в більшості випадків `0 shortlist`.
- Multi-day accumulation частково відновлює replayability:
  window `2026-03-18_to_2026-03-22` дав
  `shortlist_rows=4`, `FormalizationEligible=2`, `replayable_rulesets_count=2`.
- Але replay цих two replayable rulesets не підтвердив edge:
  обидва derived runs завершились REJECT.
- Отже, multi-day accumulation відновлює replayability,
  але поки не створює promotable edge.

# C. Що це означає для Ші

Ші все ще перебуває в чистому research mode.

На поточному етапі відсутність результату має вже не одну, а дві форми:
1. ruleset формалізується, доходить до replay, але валиться на validation / robustness;
2. ринок не дає достатньої setup density для replayable formalization на daily windows.

Це важливе уточнення для проєкту:
проблема не зводиться лише до “усі replay — REJECT”.
Частина періодів узагалі не дає щільності сигналу, достатньої для чесної формалізації.

Follow-up diagnostic також показав:
навіть якщо ширше multi-day window тимчасово повертає replayability,
це ще не означає появу edge.

Отже, Ші поки не має підстав:
- змінювати selection logic,
- послаблювати formalization gates,
- переходити до нового execution-oriented режиму,
- трактувати multi-day accumulation як новий baseline.

# D. Рішення

DO NOT CHANGE ANYTHING YET

# E. Наступний крок

Повернутись до routine collection and routine replay,
без зміни architecture baseline на основі поточного evidence.

# F. Якщо потрібні додаткові дані

None

---

## Follow-up diagnostic closure

Після первинного verdict було виконано targeted follow-up дослідження по transition
`REPLAY→REJECT` vs `NO_REPLAY / FormalizationEligible=0`.

Деталі заархівовано в
[transition note](../findings/2026-03_transition_replay_reject_to_fe0.md).

### Що встановлено

- FE=0 серія не виявилась pipeline bug.
- Основний розрив у weak regime виникає раніше:
  на рівні setup density.
- Daily windows у періоді `2026-03-18 → 2026-03-23`
  дали setup drought:
  `1–3 setups per run`, у більшості cases — `0 shortlist`.
- Multi-day accumulation частково відновлює replayability:
  window `2026-03-18_to_2026-03-22` дав
  `shortlist_rows=4`,
  `FormalizationEligible=2`,
  `replayable_rulesets_count=2`.
- Але replay цих rulesets не підтвердив edge.

### Replay outcomes

- `RULESET_REPORT_DIRECTION_LONG_V1_LONG_BASE`
  → validation FAIL, robustness UNSTABLE, promotion REJECT, trade_count=0

- `RULESET_REPORT_SETUPTYPE_FAILED_BREAK_RECLAIM_LONG_V1_LONG_BASE`
  → validation FAIL, robustness FRAGILE, promotion REJECT, trade_count=6

### Closed follow-up conclusion

> Multi-day accumulation can restore replayability in weak daily regimes,
> but it does not yet produce a promotable edge.

### Project state after follow-up

- first non-REJECT candidate still absent
- no basis to change selection logic, formalization gates, or replay policy
- continue routine collection / replay without architecture change on this basis