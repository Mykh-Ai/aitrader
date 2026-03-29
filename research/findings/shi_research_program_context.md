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

---

## Current project state

- Project state: **research-only**
- Confirmed production-ready ruleset: **none**
- H1 status: **control hypothesis**
- H2 status: **observational research track confirmed**
- Replay-ready H2 family: **none**
- Execution readiness: **absent**
- Current focus: **develop research evidence, not accelerate live**

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

> Формат запису:
> `- [weekly_YYYY-MM-DD.md](../verdicts/weekly_YYYY-MM-DD.md) — 2–5 речень: що нового, що це означає, яке рішення, який next step.`

- [weekly_2026-03-29.md](../verdicts/weekly_2026-03-29.md) —
  FE=0 streak у H1 підтверджено на більшій вибірці; weak/compressed regime не дає current H1 path достатньої setup density для shortlist / formalization. Це не виглядає як pipeline bug. На цьому фоні затверджено розвиток H2 як parallel observational research track. Наступний крок: bounded H2 comparative review без replay.

- [2026-03_h2_bounded_comparative_review.md](../findings/2026-03_h2_bounded_comparative_review.md) —
  H2 підтверджений як жива observational surface на weak/compressed window: 316 setups vs 28 у H1 за 12 днів, із кращим MAE та позитивним median CloseReturn. H2 SHORT показує слабку, але повторювану перевагу над H2 LONG, однак evidence ще недостатньо для formalization. Рішення: продовжувати H2 observation без tuning, replay або execution interpretation.

---

## Active research watchpoints

- Чи зберігається H2 SHORT asymmetry на більшій вибірці?
- Чи стабільний H2 у regime shift, а не тільки в bounded compressed window?
- Чи є у H2 окремий контекст, де observational surface переходить у формалізовану гіпотезу?
- Чи H1 дає нову density після зміни regime, чи слабкість у weak regime є структурною?

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