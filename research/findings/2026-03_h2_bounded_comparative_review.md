# H2 Bounded Comparative Review — 2026-03-29

**Window:** `2026-03-18` → `2026-03-29` (12 днів)
**Regime:** MIXED / MEDIUM density / LOW_STRESS (однорідний, без переключень)
**Code version:** `32c842e` (H2 Patches 1–3 applied)
**Run source:** local analyzer run directory for the bounded H2 review window.
**Summary CSV:** `research/results/h2_comparative_summary_2026-03-29.csv`

---

## Контекст

Bounded window обраний свідомо: `2026-03-18` → `2026-03-28` — це повний
FE=0 streak (11 consecutive runs), де H1 level-failure model не зміг
сформувати жодного formalization-eligible candidate.

Ціль review: перевірити, чи H2 impulse-first model дає осмислену research surface
у тому самому compressed regime, де H1 голодує.

---

## 1. H1 vs H2 density

| Date | H1 | H2 | H1 L/S | H2 L/S |
|------|----|----|--------|--------|
| 03-18 | 1 | 26 | 1/0 | 13/13 |
| 03-19 | 1 | 23 | 0/1 | 11/12 |
| 03-20 | 1 | 27 | 1/0 | 16/11 |
| 03-21 | 2 | 34 | 1/1 | 14/20 |
| 03-22 | 1 | 25 | 0/1 | 15/10 |
| 03-23 | 3 | 15 | 1/2 | 7/8 |
| 03-24 | 5 | 36 | 4/1 | 20/16 |
| 03-25 | 2 | 34 | 1/1 | 18/16 |
| 03-26 | 3 | 27 | 2/1 | 16/11 |
| 03-27 | 4 | 17 | 2/2 | 10/7 |
| 03-28 | 2 | 38 | 1/1 | 21/17 |
| 03-29 | 3 | 14 | 2/1 | 7/7 |
| **Total** | **28** | **316** | **16/12** | **168/148** |

- H2 avg: **26.3/day** vs H1 avg: **2.3/day** (11.4x ratio)
- Zero-setup days: 0 for both
- H2 L/S balance: 53.2% / 46.8% — без directional bias

---

## 2. H2 observational labels (n=316)

### Post-12 (terminal outcome)

| Label | Count | % |
|-------|-------|---|
| FULL_FADE | 96 | 30.4% |
| PARTIAL_FADE | 164 | 51.9% |
| NO_FADE | 56 | 17.7% |

82.3% setups показують хоча б partial fade.

### Post-6 (reclaim durability)

| Label | Count | % |
|-------|-------|---|
| RECLAIM_HELD | 116 | 36.7% |
| RECLAIM_FAILED | 200 | 63.3% |

Більшість reclaim'ів не витримують 6 барів.

### Post-3 (early continuation)

| Label | Count | % |
|-------|-------|---|
| EARLY_CONTINUATION | 154 | 48.7% |
| NO_EARLY_CONTINUATION | 162 | 51.3% |

Близько до 50/50 — ранній сигнал продовження не є домінуючим.

---

## 3. Directional split

| Metric | H2 LONG (n=168) | H2 SHORT (n=148) |
|--------|------------------|-------------------|
| FULL_FADE | 27.4% | **33.8%** |
| PARTIAL_FADE | 54.2% | 49.3% |
| NO_FADE | 18.5% | **16.9%** |
| RECLAIM_HELD | 35.7% | **37.8%** |
| EARLY_CONTINUATION | 46.4% | **51.4%** |

SHORT має м'яку перевагу: +6.4pp FULL_FADE, +2.1pp RECLAIM_HELD, +5.0pp EARLY_CONTINUATION.

---

## 4. Outcome metrics

| Metric | H2 ALL | H2 LONG | H2 SHORT | H1 ALL |
|--------|--------|---------|----------|--------|
| MFE mean | +0.184% | +0.184% | +0.183% | +0.185% |
| MFE median | +0.128% | +0.136% | +0.117% | +0.136% |
| MAE mean | −0.124% | −0.121% | −0.128% | −0.164% |
| MAE median | −0.077% | −0.081% | −0.072% | −0.109% |
| CloseReturn mean | +0.018% | +0.023% | +0.012% | +0.005% |
| CloseReturn median | +0.024% | +0.022% | +0.024% | −0.014% |

- H2 має кращий MAE ніж H1 (−0.124 vs −0.164) — менше drawdown
- H2 має кращий CloseReturn ніж H1 (+0.018 vs +0.005)
- MFE практично ідентичний
- H2 CloseReturn median позитивний (+0.024), H1 — негативний (−0.014)

---

## 5. Висновки

### Q1: Чи H2 стабільно дає surface там, де H1 голодує?

**Так.** 316 setups vs 28 за 12 днів. Кожен день H2 дав від 14 до 38 setups.
H1 давав 1–5. Це не випадковість — H2 impulse model стабільно знаходить
сигнали у compressed regime.

### Q2: Чи є directional асиметрія?

**Слабка, на користь SHORT.** FULL_FADE 33.8% vs 27.4%, RECLAIM_HELD 37.8% vs 35.7%.
Різниця ~5–6pp — потребує більшої вибірки для підтвердження.
На рівні outcome metrics різниця мінімальна.

### Q3: Чи H2 — осмислений observational object?

**Так.** Три аргументи:
1. 82.3% setups показують хоча б partial fade — це не випадковий розподіл
2. Outcome metrics кращі за H1 (менший MAE, позитивний median CloseReturn)
3. Label distribution стабільна across 12 днів — не артефакт одного дня

### Що це НЕ означає

- H2 не є formalization-ready
- H2 не є replay-ready
- Жодних execution interpretations
- SHORT перевага може бути шумом на n=148

---

## 6. Статус H2 після review

- **observational** — labels спостерігають, не формалізують
- **non-formalizable** — `FormalizationEligible = False` для Direction rows
- **non-replay-ready** — replay pipeline не працює з H2 setup types
- **research surface confirmed** — H2 дає стабільний observational object у weak regime

---

## 7. Наступні кроки

1. Продовжити збір H2 даних через daily runs (сервер оновлено)
2. Наступний H2 review — після накопичення ≥30 днів або зміни regime
3. Не тюнити detector, не змінювати thresholds
4. Спостерігати за SHORT asymmetry на більшій вибірці
