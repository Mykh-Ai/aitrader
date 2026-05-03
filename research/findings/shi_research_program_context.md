# Shi Research Program Context

## Purpose

Цей документ є довгоживучим контекстом дослідницького розвитку Ші.

Його задача:
- зафіксувати головну мету дослідження;
- зберігати поточний напрямок пошуку edge;
- коротко накопичувати weekly research outcomes;
- передавати контекст майбутнім моделям без потреби перечитувати всі weekly verdicts;
- відділяти стратегічну лінію проєкту від окремих локальних verdict-файлів.

Цей документ **не замінює** weekly verdicts.
Він є їхнім накопичувальним контекстом.

---

## Core research goal

Головна мета Ші:
виявити прибуткові, повторювані ринкові патерни через дисципліноване дослідження,
а не через підгонку параметрів або передчасний перехід до execution.

Проєкт рухається так:

**гіпотеза → формалізація → replay / validation → robustness → verdict**

Ключові правила:
- відсутність edge — це теж результат;
- REJECT — валідний research outcome;
- відсутність replayable rulesets — теж валідний outcome;
- production-рішення не приймаються без evidence.

---

## Current research direction

### H1 baseline
Поточна контрольна гіпотеза H1:
**level-failure / failed-break reclaim model**

Її роль:
- бути baseline control hypothesis;
- перевіряти, чи дає ринок достатню setup density для level-failure path;
- проходити через current shortlist / formalization / replay discipline.

### H2 parallel research track
H2:
**impulse-first observational model**

Його роль:
- дати другу research surface там, де H1 level-failure model голодує;
- вивчати impulse → reclaim / fade behavior;
- залишатися observational, non-formalizable, non-replay-ready,
  поки не буде достатнього evidence.

H2 не замінює H1.
H2 не змішується з H1 baseline.
H2 — additive research track.

---

## Stable project-level conclusions so far

### 1. H1 does not fail only through REJECT
Зафіксовано дві негативні форми outcome:
1. ruleset доходить до replay, але завершується REJECT;
2. analyzer не формує replayable candidate, бо setup density недостатня для shortlist / formalization.

### 2. Weak / compressed regime can starve H1
У weak / compressed / accumulation regime H1 може не отримувати достатньої density
для formalization-grade signals.
Це не було підтверджено як pipeline bug.

### 3. Multi-day accumulation is not edge by itself
Ширше multi-day window може частково повертати replayability,
але саме по собі це не доводить promotable edge.

### 4. H2 research surface is confirmed
У bounded comparative review H2 показав стабільну observational surface
на тому самому weak/compressed window, де H1 був значно рідшим.

### 5. H2 is not edge yet
H2 підтверджений як корисний observational research track,
але ще не є formalization-ready або replay-ready model.

### 6. H2 aggregate is not homogeneous — subgroup structure confirmed
H2 subslice review (2026-03-18 → 2026-03-29) показав чітку бімодальну структуру:
- `RECLAIM_HELD` (36.8% setups): MFE_median ~+0.244%, MAE ≈ 0, PosRate 79–82%
- `RECLAIM_FAILED` (63.2% setups): негативний CloseReturn, MAE спайк, PosRate ~43%

Агрегований H2 виглядає слабко тільки тому, що RECLAIM_FAILED розмиває RECLAIM_HELD.
H2 треба трактувати як subgroup-based research object, а не як єдину масу.

### 7. First H2 filter candidate is emerging — not yet confirmed
H2 predictor review того ж вікна знайшов перші at-entry correlates RECLAIM_HELD:
- **позитивний кандидат:** `CtxLiqSpike_v1 = True` (SHORT): held rate 63.6% vs 33.6% baseline (+30pp, n=22)
- **corroborating кандидат:** `AbsorptionScore_v1 = HIGH (3+)` (SHORT): held rate 63.0% (+25pp, n=27)
- **AVOID сигнал:** `AbsorptionScore_v1 = 1` (SHORT): held rate 15.9% (−22pp, n=44 — достатній sample)

Ці два позитивні кандидати корелюють між собою (confirmed liquidity event = high absorption).
Samples для позитивних кандидатів ще недостатні (n=22–27). Потрібно наступне bounded вікно для перевірки стабільності.

### 8. Broad H1 replay families are rejected in current formalization; cause unknown
Routine cycles `2026-03-30 -> 2026-04-09` and `2026-04-10 -> 2026-05-02`
both produced replayable H1 surface, but all replayed broad families ended in
`REJECT` with `validation_status=FAIL`.
This does not close H1 and does not prove the reclaim idea is dead.
The failure may come from signal weakness, entry timing, SL/TP placement,
validation gates, low sample, direction/regime mixing, or unstable replay
behavior.
Before parameter tuning or filter experiments, the next required step is a
reject decomposition audit.

### 9. Short-side reclaim-context asymmetry is a live observational surface
The reclaim-context history expanded to `LONG=460`, `SHORT=606` setups by
snapshot `2026-05-03`.
SHORT high-stress and multi-spike slices continued to outperform broad SHORT
baseline observationally:
- `high-stress (all 3 >= median)`: `n=197`, `pos_rate=59.4%`, `mean_ret=+0.051%`
- `>=2 ctx spikes active`: `n=197`, `pos_rate=61.9%`, `mean_ret=+0.072%`

This is not an edge, not a formalized ruleset, and not execution evidence.
It is the current strongest context-specific research surface.

### 10. Reject decomposition keeps H1 alive but blocks blind tuning
Reject decomposition audit on the available backtest artifacts showed the latest
routine replay window is not pure dead reject.
Ruleset-scope rows are mostly `LIVE_BUT_NEGATIVE`, `LIVE_BUT_UNSTABLE`, with one
`VALIDATION_GATE_FAIL`.
This means H1 should not be closed as dead, but broad rulesets should not be
tuned blindly.

### 11. SHORT context diagnostic supports a narrow filter experiment design
The pre-registered SHORT reclaim diagnostic found `ctx_spike_count_ge2` as the
cleanest current slice:
- `n=197`
- `pos_rate=61.93%`
- `mean_ret=0.071894`
- `median_ret=0.041615`
- `largest_day_share=6.60%`

This supports designing a narrow parameterized filter experiment for SHORT
reclaim context. It does not support production execution or broad optimizer
search.

### 12. Narrow replay experiment confirms only `ctx_spike_count_ge2` as useful
The narrow replay experiment over temporary filtered analyzer artifacts kept all
slices in `REJECT` under the current per-run gate, but campaign-level comparison
improved only for `ctx_spike_count_ge2`.

Replay comparison:
- baseline SHORT reclaim: `751` resolved trades, weighted mean ~= `-0.000024`,
  positive-run rate `43.18%`
- `ctx_spike_count_ge2`: `236` resolved trades, weighted mean ~= `+0.000046`,
  positive-run rate `61.54%`
- `high_stress_all3_ge_median`: weighted mean ~= `-0.000024`
- `absorption_low_le1`: weighted mean ~= `-0.000056`

The per-run `REJECT` labels remain important warnings, but they are partly
structural for this experiment because each filtered artifact uses one explicit
mapping and small per-day samples. This result supports pooled / campaign-level
validation design for `ctx_spike_count_ge2`, not production or broad ruleset
changes.

### 13. `ctx_spike_count_ge2` survives as research surface, but replay mechanics destroy most of the raw outcome
Pooled validation deduped by `source_setup_id` showed that `ctx_spike_count_ge2`
is still better than fair SHORT reclaim baseline on the same active days, but
not tradable:
- `ctx_spike_count_ge2`: `191` trades, pos_rate `48.69%`, mean `+0.00002978`,
  median `-0.00001265`
- fair baseline on ctx-active days: `570` trades, pos_rate `41.40%`,
  mean `-0.00002355`, median `-0.00006433`
- minimal cost stress around `0.00005` per trade turns ctx mean negative

Replay mismatch audit then explained why the earlier `61.93%` observational
number should not be read as replay winrate. On the same `191` deduplicated
setups, analyzer fixed-horizon outcome pos_rate is `62.83%`, but replay trade
pos_rate is only `48.69%`. There are `47` outcome-positive/replay-negative
setups versus `20` outcome-negative/replay-positive setups. Mean fixed-horizon
outcome is `+0.00075743`, while mean replay return is only `+0.00002978`.

Conclusion:
the raw short-reclaim / multi-spike context signal exists, but current
entry/SL/TP/expiry semantics extract almost none of it. The next research step
is a placement/exit mismatch audit on the `47` outcome-positive/replay-negative
setups, not promotion and not broad optimizer search.

### 14. Mismatch path order points to timing / stop-before-move, not target distance
Exit placement audit on the `47` outcome-positive/replay-negative setups showed
`STOP:42`, `EXPIRY:5`, median holding `1` bar, and `74.47%` of exits within
`3` bars. Fixed-horizon MFE reaches the current target distance in `89.36%` of
these cases, but raw path order shows target does not come first.

Path-order audit over raw feed showed:
- activation first events: `STOP_FIRST:38`, `SAME_BAR:2`, `NONE:7`
- setup-window first events: `STOP_FIRST:38`, `SAME_BAR:2`, `NONE:7`
- setup target-before-stop share: `0.00%`
- setup stop-before-target share: `80.85%`
- target-after-replay-exit share: `44.68%`
- median stop offset from activation: `0` bars
- median target offset from activation: `4` bars

Conclusion:
the current replay loses the raw signal mostly because stop comes before the
move, often immediately. This is not a target-widening proof. The next
diagnostic should test entry-delay / confirmation / stop-survival mechanics for
`ctx_spike_count_ge2`, pre-registered and compared against the same fair
baseline.

### 15. One-bar delayed entry is the first executable-semantics variant that materially improves replay
Timing / stop-survival diagnostic over the same `ctx_spike_count_ge2` surface
tested five pre-registered variants:
- `baseline_current`: `191` trades, pos_rate `48.69%`, mean `+0.00002978`,
  median `-0.00001265`, sum `+0.00568846`, max_dd `-0.01288895`
- `entry_delay_1`: `191` trades, pos_rate `61.26%`, mean `+0.00017416`,
  median `+0.00016674`, sum `+0.03326394`, max_dd `-0.00702553`
- `entry_delay_2`: `191` trades, pos_rate `58.64%`, mean `+0.00002879`,
  median `+0.00008501`, max_dd `-0.02067334`
- `survival_confirm_1`: `122` trades, pos_rate `50.00%`, mean `+0.00013756`,
  median `+0.00002484`
- `favorable_close_confirm_1`: `94` trades, pos_rate `50.00%`,
  mean `+0.00016087`, median `+0.00002799`

Cost read:
baseline turns negative by cost `0.00005`; `entry_delay_1` remains positive at
cost `0.00015` and turns negative around `0.00020`.

Conclusion:
`entry_delay_1` is not production-ready, because per-run validation remains
`FAIL`, promotions remain `REJECT`, and robustness is mostly `UNSTABLE`.
However, it is the first executable replay variant that materially improves the
same sample without reducing trade count. Next step should be strict
holdout/source-concentration/cost-aware validation for `entry_delay_1`, not more
parameter search.

### 16. Pseudo-holdout supports `entry_delay_1`, but true future holdout is still required
Entry-delay pseudo-holdout / concentration validation used already generated
timing diagnostic trades, so it is not true unseen evidence. It did, however,
show that the `entry_delay_1` improvement is not isolated to one early regime:
- all `entry_delay_1`: `191` trades, mean `+0.00017416`, median
  `+0.00016674`, sum `+0.03326387`
- late-half pseudo-holdout: `95` trades, mean `+0.00023207`, median
  `+0.00015668`, sum `+0.02204640`
- final-third pseudo-holdout: `70` trades, mean `+0.00032079`, median
  `+0.00027329`, sum `+0.02245548`
- paired all-sample mean delta vs baseline: `+0.00014437`; delay better share:
  `63.87%`
- paired delay better share remains positive in early half (`66.67%`),
  late half (`61.05%`), and final third (`65.71%`)

Concentration read:
removing the best single day keeps `entry_delay_1` gross-positive
(`sum=+0.02639593`), but removing the top three days leaves a thinner gross sum
(`+0.01576928`) and cost `0.00010` turns that top-3-removed sum slightly
negative (`-0.00103072`).

Conclusion:
`entry_delay_1` deserves true future holdout with the candidate frozen. It does
not justify promotion, additional tuning, or production interpretation.

---

## Current project state

- Project state: **research-only**
- Confirmed production-ready ruleset: **none**
- H1 status: **control hypothesis**
- H2 status: **observational track confirmed; subgroup structure confirmed; first filter candidate emerging (not yet validated)**
- Replay-ready H2 family: **none**
- Execution readiness: **absent**
- Current focus: **true future holdout for frozen SHORT reclaim `ctx_spike_count_ge2 + entry_delay_1`; no production interpretation**

---

## What matters most now

Головний пріоритет:
не класифікувати rules заради самих rules,
а просувати пошук прибуткових патернів через розвиток дослідження.

Тому пріоритет інтерпретації такий:
1. Чи з’явився новий корисний research signal?
2. Чи з’явилась нова жива research surface?
3. Чи наблизив cycle проєкт до edge / anti-edge висновку?
4. І тільки потім:
   - replayed reject classification
   - archival follow-up for rules

---

## Weekly development log

- [short_reclaim_pooled_validation_2026-05-03.md](./short_reclaim_pooled_validation_2026-05-03.md) + [short_reclaim_replay_mismatch_audit_2026-05-03.md](./short_reclaim_replay_mismatch_audit_2026-05-03.md) —
  Pooled validation after `source_setup_id` dedupe showed `ctx_spike_count_ge2`
  is better than fair baseline but too thin and cost-sensitive: `191` trades,
  replay pos_rate `48.69%`, mean `+0.00002978`, median `-0.00001265`.
  Mismatch audit explained the gap: on the same setup ids, fixed-horizon
  analyzer outcome pos_rate is `62.83%`, while replay pos_rate is only
  `48.69%`; `47` setups are outcome-positive but replay-negative. Decision:
  live research surface, not edge; next step is placement/exit mismatch audit,
  not optimizer search.

- [short_reclaim_exit_placement_audit_2026-05-03.md](./short_reclaim_exit_placement_audit_2026-05-03.md) + [short_reclaim_path_order_audit_2026-05-03.md](./short_reclaim_path_order_audit_2026-05-03.md) —
  Exit / path-order audit on the `47` outcome-positive/replay-negative cases
  showed the replay collapse is mostly timing / stop-before-move: `STOP:42`,
  `EXPIRY:5`, median holding `1` bar, setup target-before-stop share `0.00%`,
  setup stop-before-target share `80.85%`, and target-after-replay-exit share
  `44.68%`. This does not support target widening or promotion. Next step:
  pre-registered entry-delay / confirmation / stop-survival diagnostic for
  `ctx_spike_count_ge2`.

- [short_reclaim_timing_survival_diagnostic_2026-05-03.md](./short_reclaim_timing_survival_diagnostic_2026-05-03.md) —
  Timing diagnostic found the first material executable-semantics improvement:
  `entry_delay_1` kept the full `191` trades and improved replay from baseline
  `48.69%` pos_rate, mean `+0.00002978`, median `-0.00001265` to `61.26%`,
  mean `+0.00017416`, median `+0.00016674`; max drawdown improved from
  `-0.01288895` to `-0.00702553`. Cost read is also better: baseline turns
  negative by `0.00005`, while `entry_delay_1` remains positive through
  `0.00015`. Still no promotion: all per-run gates remain `FAIL/REJECT` and
  robustness is mostly `UNSTABLE`. Next step: holdout / source-concentration /
  cost-aware validation for `entry_delay_1`.

- [short_reclaim_entry_delay_holdout_validation_2026-05-03.md](./short_reclaim_entry_delay_holdout_validation_2026-05-03.md) —
  Pseudo-holdout / concentration validation supported `entry_delay_1` as a
  frozen candidate: late-half pseudo-holdout had `95` trades, mean
  `+0.00023207`, median `+0.00015668`, sum `+0.02204640`; final-third
  pseudo-holdout had `70` trades, mean `+0.00032079`, median `+0.00027329`.
  Paired all-sample mean delta vs baseline was `+0.00014437`, with delay better
  in `63.87%` of matched setup pairs. Concentration warning remains: after
  dropping top 3 days, cost `0.00010` turns the remaining sum slightly negative.
  Decision: freeze `ctx_spike_count_ge2 + entry_delay_1` and wait for true
  future holdout; no tuning or promotion.

- [weekly_2026-05-03.md](../verdicts/weekly_2026-05-03.md) —
  Cycle `2026-04-10 -> 2026-05-02` не дав REVIEW/PROMOTE: 13 replayed runs знову завершилися `REJECT/FAIL`, а останні 10 runs перейшли в FE=0/setup=0 starvation. Це показує, що broad H1 не підтверджений у поточній формалізації, але причина reject ще невідома. Водночас short-side reclaim-context surface на більшому sample не розсипалась: `>=2 ctx spikes active` має `n=197`, `pos_rate=61.9%`, `mean_ret=+0.072%`. Уточнене рішення після review: спершу `reject decomposition audit`, потім вирішувати, чи робити targeted SHORT context filter experiment.

- [reject_decomposition_audit_2026-05-03.md](./reject_decomposition_audit_2026-05-03.md) + [short_reclaim_context_filter_diagnostic_2026-05-03.md](./short_reclaim_context_filter_diagnostic_2026-05-03.md) —
  Decomposition показав, що latest routine rejects не є pure dead rejects: surface існує, але вона negative/unstable або падає на validation gate. SHORT context diagnostic підтвердив, що `ctx_spike_count_ge2` є найчистішим pre-registered slice (`n=197`, `pos_rate=61.93%`, `median_ret=0.041615`, `largest_day_share=6.60%`). Це не edge і не production signal, але достатньо для наступного research step: design narrow parameterized filter experiment без optimizer search.

- [short_reclaim_context_replay_experiment_2026-05-03.md](./short_reclaim_context_replay_experiment_2026-05-03.md) —
  Narrow replay experiment не дав promotion: усі slices лишились `REJECT` під current per-run gate. Але campaign-level comparison підтвердив, що тільки `ctx_spike_count_ge2` покращує baseline: `236` resolved trades, weighted mean ~= `+0.000046`, positive-run rate `61.54%` проти baseline `-0.000024` і `43.18%`. `high_stress_all3_ge_median` як primary candidate не вижив replay, а `absorption_low_le1` виглядає як avoid/downweight slice. Наступний research step: pooled / campaign-level validation design для `ctx_spike_count_ge2`, без production interpretation.

- local-only weekly verdict for 2026-04-10 —
  H1 вийшов із FE=0 starvation: у більшості runs зявилась replay surface, але broad replay families системно завершилися REJECT/FAIL. H2 active filter candidate нового material evidence не отримав. Водночас reclaim-context history на більшій вибірці підсвітив окрему short-side observational surface: high-stress / multi-spike reclaim виглядає сильніше за broad short baseline. Рішення: `INVESTIGATE SPECIFIC SIGNAL`. Наступний крок: targeted validation note по short-side reclaim context.
- local-only weekly verdict for 2026-03-29 —
  FE=0 streak у H1 підтверджено на більшій вибірці; weak/compressed regime не дає current H1 path достатньої setup density для shortlist / formalization. Це не виглядає як pipeline bug. На цьому фоні затверджено розвиток H2 як parallel observational research track. Наступний крок: bounded H2 comparative review без replay.

- [2026-03_h2_bounded_comparative_review.md](../findings/2026-03_h2_bounded_comparative_review.md) —
  H2 підтверджений як жива observational surface на weak/compressed window: 316 setups vs 28 у H1 за 12 днів, із кращим MAE та позитивним median CloseReturn. H2 SHORT показує слабку, але повторювану перевагу над H2 LONG, однак evidence ще недостатньо для formalization. Рішення: продовжувати H2 observation без tuning, replay або execution interpretation.

- [2026-03_h2_subslice_review.md](../findings/2026-03_h2_subslice_review.md) —
  H2 aggregate виявився не однорідним. Subslice по `H2_Post6Label_v1` показав чітку бімодальну структуру: RECLAIM_HELD (~37% setups) має MFE_median 2x вищий, MAE ≈ 0, PosRate 79–82%; RECLAIM_FAILED (~63%) — негативний CloseReturn, MAE спайк. Найсильніший subgroup: `SHORT_RECLAIM_HELD` (MFE_median +0.240%, MAE_median +0.005%, PosRate 82.1%). Рішення: трактувати H2 як subgroup-based research object, не як агрегатну поверхню.

- [2026-03_h2_reclaim_durability_predictors.md](../findings/2026-03_h2_reclaim_durability_predictors.md) —
  Перший at-entry predictor gap частково закрито. `CtxLiqSpike_v1 = True` (SHORT): held rate +30pp vs baseline (n=22, borderline); `AbsorptionScore_v1 = HIGH` (SHORT): +25pp (n=27). Обидва вимірюють один феномен — confirmed liquidity event at formation. Найнадійніший сигнал: `AbsorptionScore_v1 = 1` як AVOID (held rate 15.9%, n=44). Decision: H2_FILTER_CANDIDATE_EMERGING. Наступний крок: next bounded 2-week window (≈ 2026-04-01 → 2026-04-14), rerun predictor analysis, no code changes.

---

## Active research watchpoints

- Чи зберігається H2 SHORT asymmetry на більшій вибірці?
- Чи стабільний H2 у regime shift, а не тільки в bounded compressed window?
- Чи є у H2 окремий контекст, де observational surface переходить у формалізовану гіпотезу?
- Чи H1 дає нову density після зміни regime, чи слабкість у weak regime є структурною?
- Чи зберігається split `RECLAIM_HELD` vs `RECLAIM_FAILED` при більшому n?
- Чи стабільний `CtxLiqSpike_v1 = True` (SHORT) held rate ≥50% на наступному 2-тижневому вікні?
- Чи стабільний `AbsorptionScore_v1 = HIGH` (SHORT) held rate при n≥50?
- Чи залишається `AbsorptionScore_v1 = 1` AVOID сигналом (held rate <20%) поза compressed regime?
- Чи підтвердить наступне bounded вікно ці predictor candidates чи вони розсипляться?
- Чи broad H1 `REJECT/FAIL` є dead reject, low-sample issue, unresolved-trade issue, validation-gate issue, чи live-but-unstable surface?
- Чи short-side reclaim `high-stress` / `>=2 ctx spikes active` лишається сильнішим за broad SHORT baseline після reject decomposition і наступного sample update?
- Чи можна перетворити short-side reclaim context surface у parameterized filter experiment без tuning broad ruleset, якщо decomposition покаже non-zero but mixed surface?

---

## Rules for future updates

Після кожного нового weekly verdict:
1. Не переписувати цей документ повністю.
2. Додавати короткий новий запис у секцію **Weekly development log**.
3. У кожному новому записі обов’язково:
   - посилання на відповідний weekly verdict;
   - 2–5 речень про новий факт;
   - коротко: що це означає для Ші;
   - коротко: яке рішення або next step випливає.
4. Не дублювати весь weekly verdict.
5. Якщо weekly cycle нічого принципово нового не дав — так і писати прямо.
6. Якщо з’явився новий confirmed research track, archival candidate або стратегічний зсув — оновити також відповідні секції вище, а не лише weekly log.

---

## Status of this document

Це canonical long-lived research context document.
Weekly verdicts залишаються первинними артефактами окремих циклів.
Цей файл потрібен для накопичення розвитку, передачі контексту
і швидкого входу майбутніх моделей у стан проєкту.
