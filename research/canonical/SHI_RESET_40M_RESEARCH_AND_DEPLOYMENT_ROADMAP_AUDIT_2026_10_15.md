# AiTrader: канонічна дорожня карта досліджень і передачі до розгортання

Стан на **15 жовтня 2026 року**. Завдання **SHI_RESET_40M**: зафіксувати результати, рішення, точні правила та порядок наступної інтеграції. Це документування і передача роботи; серверний сервіс та біржовий адаптер у цьому завданні не створюються й не запускаються.

## 1. З чого почати наступному агенту

Мета AiTrader — власна система: **власний фід → власні сигнали → відтворюваний replay → журнал і гроші → серверний генератор → виконання через біржу**. Scout був прикладом, а не потрібним джерелом входів. Поточні сигнали не залежать від його повідомлень або ручних часових міток.

Перший README у коміті `5a93bfb` уже задавав BTCUSDT Perpetual як джерело сигналів і BTC/USDC Spot Margin як виконання. Початкові sweep/CVD, частковий TP1, ризик 1% і margin 2x є історією задуму: вони **не є правилами відібраного нижче кандидата**. Історію перезапуску див. у [README](../../README.md) та [PROJECT_LOG](../../PROJECT_LOG.md).

| Питання | Поточна відповідь і джерело |
|---|---|
| Які правила вибрані користувачем? | **40H**, `LONG_DELTA4_POS_BOTH_BAND4`: [рішення](OWN_SIGNAL_RESEARCH_SELECTION_2026_10_15.md), [машинний покажчик](../active_own_signal_selection.json), [заморожений контракт](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/selected_research_contract.json). Успадковується весь контракт, а не лише дві дельти. |
| Який прогін останній? | **40L**, до `2026-10-14 23:59 UTC`: [покажчик із SHA256](../latest_own_signal_replay.json), [результат](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/result.json), [повний журнал](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/trade_journal_usdc.csv). |
| Чому два покажчики? | `active_own_signal_selection.json` зберігає незмінний вибір правил 40H; `latest_own_signal_replay.json` окремо адресує пізніший доказ 40L. Не переписувати старі контракти/журнали під нові дати. |
| Яка архітектурна опора? | [39A — master alignment audit](SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md). Цей документ узагальнює trading research і передачу, не замінює архітектурний аудит. |
| Який статус? | Історично відібраний дослідницький кандидат. Є позитивна історична модель після заданих витрат; незалежний holdout, реальні запозичення BTC, виконання заявок і виробнича готовність не доведені. |

Порядок читання: цей документ → вибраний контракт/обидва покажчики → 40L журнал і перевірки → потрібні рядки історії нижче → [AGENTS](../../AGENTS.md), [активні документи](../../docs/ACTIVE_DOCS.md), [контракт фіду](../../docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md) перед змінами.

## 2. Що отримали в останньому прогоні

Усі періоди нижче групуються **за датою входу UTC**. Початок вхідних даних — 11 березня; warmup допускає рішення з 18 березня, перша вибрана угода — 25 березня. Виконання і виходи спостерігаються лише до спільного cutoff 14 жовтня 23:59 UTC.

| Входи | Угоди | Плюсові / мінусові | Net, USDC |
|---|---:|---:|---:|
| Березень | 1 | 0 / 1 | −51,296878 |
| Квітень–вересень | 12 | 8 / 4 | +1 142,108729 |
| Жовтень 1–14 | 1 | 0 / 1 | −29,904211 |
| **Разом** | **14** | **8 / 6** | **+1 060,907640** |

Жовтень 13–14: нових виконаних входів немає. На cutoff немає відкритих або data-censored позицій. Усі 13 попередніх угод 40H відтворені й збережені без зміни грошей. Додано один лонг 3 жовтня, закритий стопом 7 жовтня. Це зменшило загальний результат на 29,904211 USDC, а не покращило його.

Кошторис: **1 147,762332 gross − 70,00 комісій − 16,854692 прослизання = 1 060,907640 USDC net**. Лонги: 10 / +648,468581; шорти: 4 / +412,439059. Середня угода +75,779117 USDC / +2,176805R; середній початковий ризик 42,756848 USDC. Просадка **за закритими угодами** 74,610063 USDC; це не внутрішньопозиційна mark-to-market просадка. Без трьох найбільших виграшів +220,888015 USDC.

Це модель із фіксованими 3 000 USDC на позицію, 5 USDC сумарної комісії на завершену угоду, 2 bps несприятливого прослизання на кожне виконання. Фактичні відсотки позики BTC не включені. Позначення `$` у старих поясненнях припускало паритет котирувальної монети до USD; це не перевірений обмінний курс. Поля журналу з історичним суфіксом `_usd` у 40G–40L означають **USDC**.

Докази: [40L аудит](SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md), [помісячні суми](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/monthly_entry_results_usdc.csv), [кандидати та рішення книги](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/candidate_book_decisions.csv), [перевірки](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/verification.json), [незалежна звірка](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/final_verification.json).

## 3. Карта досліджень і прийнятих рішень

Результати різних ринків і періодів не додавати один до одного. 40C–40F1 виконувалися на ф'ючерсних цінах як proxy; окремі спотові ціни починаються з 40G. Кожен рядок є окремим експериментом, не додатковим прибутком одного рахунку.

| Етап / запит | Що з'ясовано | Рішення та докази |
|---|---|---|
| Перезапуск Analyzer, 38-chain, 39A | Monitor, структура/ліквідність, hidden flow і setup_builder побудовані. Старі 51 кандидати та реакції TP1 не доводять фінансового edge; setup_builder — генератор контексту. | [39A](SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md); [виправлений 38W1 replay](../../market_monitor_runs/SHI_RESET_38W1_fix_chronological_tp1_stop_labels_v0/setup_builder_replay_summary.md). Snapshot v39A дозволений лише як описовий контекст для Executor LLM. |
| 40A: чи можна бектестити збережені 51 рядок? | 49/51 backdate часу щодо спожитого daily state; targets із повноперіодних зон; 26/51 targets напрямно невалідні на вході. | Не використовувати як причинний потік фінансових входів. [Аудит](SHI_RESET_40A_OWN_SIGNAL_CAUSALITY_PREFLIGHT_AUDIT_2026_10_13.md). |
| 40B / 40B1: підготовка власного потоку | Окремий causal research runner, заморожені джерела/правила; користувач уточнив політику одиничної відсутньої/синтетичної хвилини. | Активна підготовка v1: пропустити спостереження, зберегти UTC/стан, продовжити на наступній реальній свічці. [40B](SHI_RESET_40B_OWN_SIGNAL_RUN_PREPARATION_AUDIT_2026_10_13.md), [40B1](SHI_RESET_40B1_SINGLE_MINUTE_TOLERANCE_AUDIT_2026_10_13.md), [пакет](../own_signal_run/README.md). |
| 40C: перший заморожений прогін | 63 gate-passing сигнали, 21 завершена угода. Demand 20 угод / −2,41R base net; seller 1 / −2,03R; supply 0. Прибуткову сім'ю не встановлено. | Негативна опора збережена. [Аудит](SHI_RESET_40C_OWN_SIGNAL_FROZEN_PROXY_RUN_AUDIT_2026_10_14.md), [результат](../../market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0/result_summary.md). |
| 40D: ітеративний пошук за 3 000 / 5 і порогом +500 | LONG trend retest + SHORT accepted break, одна книга: 26 угод / +512,28 proxy net; квітень–вересень 23 / +579,02. | Власні H1-сім'ї стали дослідницькою основою. Усі trials збережені. [Аудит](SHI_RESET_40D_OWN_SIGNAL_STRATEGY_SEARCH_AUDIT_2026_10_14.md), [результат](../../market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/result.md), [контракт](../../market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/selected_strategy.json). |
| 40E: спільне у стопах, 6R/10R | Стопи лонгів часто ранні; у шортів часто близька відома H4-підтримка. 20 пар цілей не дали кращої повної моделі за short6R/long10R; 10R — верхня межа тієї сітки. | Post-entry failure не перетворювати на entry filter заднім числом. [Аудит](SHI_RESET_40E_HYBRID_STOP_DIAGNOSIS_AUDIT_2026_10_14.md), [діагностика](../../market_monitor_runs/SHI_RESET_40E_hybrid_stop_diagnosis_v0/diagnosis_summary.md). |
| 40F: шорти, стопи, сім днів | Вимога short-space ≥1R до відомої H4-підтримки: 21 угода / +671,05 proxy net; квітень–вересень +839,79. Розібрані всі шість expiry, разом +433,10. | Short-space gate успадковано. Зменшились збитки, але абсолютних виграшів стало 8 замість 9. [Аудит](SHI_RESET_40F_DIRECTION_EXPIRY_STOP_INTERVENTIONS_AUDIT_2026_10_14.md), [контракт](../../market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/selected_research_variant.json). |
| 40F1: захист short після +2R | Захисний стоп +0,25R після +2R: початкова модель +408,15 замість +512,28; зі short-space лишається +671,05 без зміни виходів. +1R також не покращив модель. | Захист не вибрано. [Аудит](SHI_RESET_40F1_SHORT_PROTECTION_2R_AUDIT_2026_10_14.md), [порівняння](../../market_monitor_runs/SHI_RESET_40F1_short_protection_2R_v0/result.md). |
| 40G: сигнали futures, виконання spot | Перевірено 48 офіційних BTCUSDC архівів. 21 угода / +676,37 USDC, квітень–вересень +845,02. | Два ринки розділені назавжди для подальших фінансових прогонів. [Аудит](SHI_RESET_40G_FUTURES_SIGNALS_SPOT_EXECUTION_AUDIT_2026_10_14.md), [спотовий контракт](../../market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/selected_spot_contract.json), [результат](../../market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/result.md). |
| 40H: дельти/час/OI та збиткові входи | 22 full-book trials. Вибрані 24h band4 + long4h>0: 13 угод / 8 виграшів / 5 збитків / +1 090,81; квітень–вересень +1 142,11. Усі 8 старих виграшів лишилися; 9 збитків заблоковано, один новий −39,51 включено. | **Вибрані користувачем правила.** [Аудит](SHI_RESET_40H_LOSS_METRICS_FILTER_STUDY_AUDIT_2026_10_14.md), [результат](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/result.md), [усі 22 trials](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/filter_results.csv). |
| 40I: більше входів | 130 адаптивних trials. Помірна альтернатива: 16 угод за квітень–вересень / +1 150,20 / DD125,27 проти 12 / +1 142,11 / DD74,61. Увесь період 18 / +1 156,80. | Альтернатива збережена, **не вибрана**. Різниця за шість місяців лише +8,10; варіант 24 угоди дає +692,85 / DD398,35. [Аудит](SHI_RESET_40I_ENTRY_FREQUENCY_EXPANSION_AUDIT_2026_10_14.md), [результат](../../market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/result.md), [контракт альтернативи](../../market_monitor_runs/SHI_RESET_40I_entry_frequency_expansion_v0/frequency_alternative_contract.json). |
| 40J: дзеркальна short4h<0 | Прибирає виграш June1 +387,18; не прибирає жодного збитку і не додає угод. Net +703,63 замість +1 090,81. | Додатковий знак 4h для шорта **не вибрано**. [Аудит](SHI_RESET_40J_SHORT_DELTA4_MIRROR_AUDIT_2026_10_15.md), [результат](../../market_monitor_runs/SHI_RESET_40J_short_delta4_mirror_v0/result.md). |
| 40K: оновити з сервера | Завершені futures 13/14 жовтня та офіційний spot додані зі збереженням старих bytes/hashes; 15 жовтня partial виключено. | Нові дані не переписують старі результати. [Аудит](SHI_RESET_40K_DATA_REFRESH_AUDIT_2026_10_15.md), [готовність](../../market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0/data_readiness.json). |
| 40L: прогін до 14 жовтня | 14 завершених / +1 060,91 USDC; 13 старих рядків незмінні, October −29,90. 15 тестів, 14 незалежно перевірених шляхів, реальний prefix і всі джерела звірено. | **Останній журнал і фінансовий результат.** [Аудит](SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md), [результат](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/result.md). |
| 40M: ця передача | Впорядковані рішення, точний контракт, відтворення, стан Git/артефактів і наступні інженерні етапи. Нових угод або налаштувань немає. | [Супровідний індекс](../../market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/handoff_index.json), [інвентар із SHA256](../../market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/handoff_inventory.csv). |

### Ідеї, які не слід мовчки додавати до 40H

- Просте H4 UP-only/NO_DOWN для лонга, половина виходу на 2R і H1-trailing після 2R: перевірені в 40G, не покращили основні +676,37; відповідні результати близько +442,91 / +599,19 / +519,44 / +521,72.
- Native spot stops: окрема sensitivity +676,54 замість +676,37, змінює джерело стопа; основним лишився futures-to-spot mapping.
- Додатна 24h-дельта для лонга, nonnegative OI, заборони годин: втрачали виграшні входи в 40H. Час/OI/liquidations не є додатковими gates вибраної версії.
- Band2 і band6, додаткові breakouts 40I, short-space0,75R, mirror short4h<0, BE/partials/trailing: досліджені окремо й не входять до вибору користувача.
- 16-годинне чи інше скорочення max hold не є прийнятим правилом. Фіксований вихід через 168 годин збережено. Розбір expiry не означає дозвіл змінити горизонт без нового повного replay.

Це висновки на малій, уже дослідженій історії, а не універсальні закони ринку. Для нової гіпотези потрібні окремий manifest, повний one-book replay і збереження всіх trials, пропущених виграшів та нових збитків.

## 4. Точні торгові правила для перенесення

Нижче — опис фактично виконаного research-коду, не готовий біржовий сервіс. Позначення: `t` — щойно закритий H1, усі дані мають бути доступні не пізніше `decision_at`.

### 4.1. H1-признаки та long TREND_RETEST

База — [features.py](../strategy_search/features.py); October-admission і hybrid композиція останнього replay — [40L policy.py](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/policy.py).

- EMA24/72/168 за закриттями H1, `ewm(span=..., adjust=False)`; ATR24 — просте середнє 24 значень true range, не Wilder smoothing.
- `volume_ratio = volume[t] / median(volume[t-24:t])`: у знаменнику попередні 24 H1, без поточної.
- H1 delta fraction `(Buy−Sell)/Volume`; `0.04` означає 4%, не 0,04%.
- LONG: `EMA24>EMA72`, `close>EMA168`, `low<=EMA24`, `close>EMA24`, `close>open`, H1 delta **≥+4%**, volume_ratio **≥1,3**.
- Додатково `abs(close−EMA24)/ATR24<=1,5`, `(high−low)/ATR24<=2`; поточний/попередні 24 usable H1 і попередні 96 usable H1 як у коді.

### 4.2. Short ACCEPTED_BREAK

- `lower48[t]` — мінімум low попередніх 48 H1 без поточного; reference для пари закриттів — `lower48.shift(1)[t]`, тобто відомий до першого з двох закриттів.
- Обидва `close[t−1]` і `close[t]` строго нижчі цього самого reference. Видається перше справдження умови, через `short &= ~short.shift(fill_value=False)` до інших gates; не кожен наступний H1 нижче рівня.
- `close[t]/close[t−24]−1<0`; агрегована H1 rolling24 delta fraction `<0`; delta поточного H1 `<=0`; volume_ratio **≥1,3**; поточний/24h контекст і попередні 48 H1 usable.
- Конфлікт різних сімей одного H1 відкидається за правилами hybrid, без вибору за майбутнім результатом.

### 4.3. Short-space до H4 та дві дельти 40H

[40F interventions.py](../../market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/interventions.py) будує causal inventory: строгі 3-свічкові H4 swings, центр стає відомим після закриття правого H4. Три свічки usable і суміжні; активні рівні не старші 30 днів. Два usable H1 закриття за рівнем із buffer5bps деактивують його. Стан переноситься через всю історію.

Для short знаходиться найближча активна підтримка нижче decision close. Відстань до її верхнього buffer `support×1.0005` ділиться на оцінений початковий short-risk **від уже відомого futures decision close**. Якщо є рівень і простору **<1R**, short відкидається. Майбутня ціна входу не використовується. Відсутність рівня пропускає цю перевірку, але не доводить відсутності інших перешкод. Це обмежений H4 inventory дослідження, не повний promoted Monitor registry.

Далі [40H filters.py](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/filters.py), тільки `L_D4_POS` і `B_D24_BAND4`:

```text
delta_h_percent = 100 × (sum BuyQty − sum SellQty) / sum TotalQty
window = (decision_at − h годин, decision_at]
Для обох напрямів: −4 < delta_24_percent < +4
Додатково для LONG: delta_4_percent > 0
```

Це зважена фактичним обсягом **rolling4h/24h** дельта реальних minute observations; не середнє minute-percent і не календарна H4. Межі строгі: рівно ±4 або рівно 0 для long4h не проходять. Непридатні/відсутні потрібні windows не проходять. Для short **немає додаткової вимоги delta4<0**. Short PRESSURE rolling24 H1 із 4.2 і raw-window delta24 gate тут — різні обчислення; не підміняти одне іншим.

### 4.4. Вхід, стоп, ціль, розмір і витрати

[Spot mapping](../../market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/cross_market.py) використовує останні RAW futures та spot closes не пізніше рішення, кожна котировка не старша хвилини. `basis = spot_BTCUSDC_close / futures_BTCUSDT_close`; допустима технічна область `[0.95,1.05]`. Відомі futures structural references та ATR переводяться в USDC цим зафіксованим ratio.

У replay після рішення `d` запланований вхід — open хвилини `d+1min`. За правими close-labels це рядок `d+2min`. Одиничний пропущений рядок може відкласти вхід ще на хвилину. Ціну входу не використовувати для більш раннього signal/gate рішення. Фактичне live-виконання не може припускати гарантоване отримання цього історичного open.

Позначення: `E` — фактичний spot entry model price; `L6/H6` — minimum/maximum **шести попередніх H1 без сигнального** після spot mapping; `A` — mapped ATR24 на рішенні.

```text
LONG stop  = min(L6 × 0.9995, E − 2.0 × A)
SHORT stop = max(H6 × 1.0005, E + 1.5 × A)
D = abs(E − stop)
Якщо D/E < 0.004 або > 0.04: не відкривати, не обрізати стоп до межі.
LONG target  = E + 10 × D
SHORT target = E −  6 × D
quantity_BTC = 3000 / E
1R_USDC = quantity_BTC × D
gross_USDC = direction × (exit_price − E) × quantity_BTC
commission_USDC = 5 за всю завершену угоду
slippage_USDC = (E + exit_price) × quantity_BTC × 0.0002
net_USDC = gross_USDC − commission_USDC − slippage_USDC
net_R = net_USDC / 1R_USDC
```

`direction=+1` для long, `−1` для short. 0,05% buffer =5bps. Обирається дальший із structural/ATR стопів. Стоп і target **фіксуються при вході**, без BE, захисту після2R, часткових виходів, pyramiding або трейлінгу. 3 000 — notional, не капітал, margin ratio або постійний dollar-risk. Початковий risk при цих межах 12–120 USDC **до** комісії/прослизання/можливого несприятливого gap. Одна повна ціль: 10R long, 6R short; не 6 і 10 одночасних тейків.

Приклад із журналу: October3long, E84856,33; stop84185,711765; D670,618235; risk23,708953USDC; target91562,512345. Stop October7 дав −29,904211USDC після витрат. Ціль10R тут означала б +237,089526USDC gross, а не гарантований прибуток.

### 4.5. Виходи і портфель

- Одна глобальна позиція для всіх сімей/напрямів, без накладання; після виходу cooldown3 хвилини, точна нерівність як у [hybrid.py](../strategy_search/hybrid.py).
- Stop/target перевіряються minute-chronologically. Якщо обидва торкнуті в одній хвилині — stop-first. Несприятливий open gap за стопом виконується за гіршим open, а не гарантованим stop price; target зараховується не краще власної цілі.
- Expiry через **168 фактичних UTC годин від entry**. На expiry-minute спершу перевіряються захисні торкання; якщо їх немає — close. Якщо рівно expiry observation немає, наступний реальний open використовується до перевірки його подальших high/low.
- Відкрита на cutoff позиція не отримує вигаданий вихід або net. `OPEN_AT_CUTOFF`, окремий mark із останнього відомого spot close і гіпотетичний net-if-closed; не додавати його до realized net. Data-censored — окремий статус.
- Портфель перераховується повністю після зміни правил: раніший вихід чи заблокована угода може допустити інший вхід. Суми видалених рядків не є новим результатом портфеля.

## 5. Дані, час і обмеження причинності

Джерела і нормалізація: [feed.py](../own_signal_run/feed.py), [feed contract](../../docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md). Primary і recovered зберігаються роздільно. Відомий outage `2026-04-23 17:05 → 2026-05-06 22:51 UTC`: використовувати recovered provenance; його OI/funding/liquidations не рівноцінні RAW.

Одинична відсутня/синтетична primary minute пропускається в пам'яті: UTC не стискається, active trade і H1/H4 context не обриваються, 24-годинний карантин не створюється. Дві або більше послідовно відсутніх хвилин чи recovered execution не отримують вигаданих fill; у поточному строгому research-контракті відповідний шлях censored. Ця історична логіка не замінює біржовий захисний stop у майбутньому live-сервісі.

Часові labels: історичний futures `Timestamp` трактований дослідженням як close-label; official spot open нормалізований у right-close `open+60s`. H1/H4 формуються з доступних закритих спостережень. На сервері окремо перевірити фактичні часові мітки поточного агрегатора, close event і затримку доставки, не робити додатковий shift із припущення. Live/replay parity має охопити межі години, пропущену хвилину і restart.

40L обмежений спільним `2026-10-14 23:59 UTC`; останній завершений H1 —23:00. Spot рядок October15 00:00 відповідає фінальній хвилині October14, але у **цьому** frozen replay відсічений за спільним cutoff. Не домішувати його без нової задекларованої версії.

Історичні entry exclusions збережені: warmup до March18 14:00; April23 17:05–May10; June22–29; August25–September1. Старий October1–13 guard знято **лише artifact-local у 40L**; старий spec `entry_end=October1` не описує його розширення. `replay_hybrid` сам не застосовує цей `entry_end`: правила календаря й cutoff звіряти з реальною генерацією. Ці відомі історичні вікна не є автоматичною щорічною календарною політикою для live; поведінку при нових gaps треба явно специфікувати перед переносом, зберігши історичну parity.

Усі EMA, ATR, рівні, rolling flows, H4 availability/retirement і позиційний стан відновлюються з попередньої історії. Не запускати лише останній день і не називати це еквівалентом повного стану. Вузьке вікно допускається лише як diagnostic із відновленою передісторією. Frozen40H/40L застосовують обмежені causal features та H4 inventory, а не всю семантику майбутнього stateful Monitor.

## 6. Де лежить логіка і що можна переносити

| Файл / шар | Фактична роль |
|---|---|
| [binance_aggregator_shi.py](../../binance_aggregator_shi.py) | Public BTCUSDT futures collector. Захищений data-lineage asset; не змінювати для зручності replay. |
| [research/own_signal_run](../own_signal_run/README.md) | Feed/contracts, causal preparation, первісна 40B/C sweep-гіпотеза. Не плутати її entry engine з hybrid40H. |
| [features.py](../strategy_search/features.py), [hybrid.py](../strategy_search/hybrid.py), [replay.py](../strategy_search/replay.py) | H1 features, hybrid composition/одна книга, minute fills/stop/target/cash. Історично frozen research-код, не live worker. |
| [40F interventions.py](../../market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0/interventions.py) | Обмежений causal H4 inventory і short-space gate. |
| [40G cross_market.py](../../market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/cross_market.py) | Decision-known futures→spot reference mapping; не приватний API-адаптер. |
| [40H study.py](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/study.py), [filters.py](../../market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0/filters.py) | Відтворення control, raw-window метрики, вибрані два delta gates. |
| [40L run_study.py](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/run_study.py), [policy.py](../../market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/policy.py) | Остання композиція цілого replay, October admission і last-closed-H1 precise-entry adapter. |
| [market_monitor](../../market_monitor) / [39A](SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md) | Reusable descriptive architecture. Snapshot для Executor LLM уже має обмежену promotion; це не вибраний entry/exit policy. |
| [legacy backtester](../../backtester/README.md) | Існує окремо. Вибрані40H/L пройшли research minute replay; активація його старого validation/promotion gate не виконувалась. |

`market_monitor_runs/` містить run scripts, не promoted reusable modules. Перед серверним використанням винести потрібні формули/контракти у явно версіонований модуль із parity-тестами. Не імпортувати вічно live-сервісом випадкові `_build_...py` і не міняти frozen run scripts заради нового live-контракту.

## 7. Відтворення і передача файлів

Поточний базовий Git HEAD на момент документування: `1c18766` (`Record 39a monitor alignment audit and current handoff`), **плюс робоче дерево**. Тільки цей commit не містить усі нові дослідження. `research/strategy_search/`, `research/own_signal_run/`, нові canonicals і покажчики на цей момент не закомічені. `.gitignore` виключає `market_monitor_runs/`, `feed/`, `feed_recovered/`, ZIP. Звичайний clone/pull не переносить пакет відтворення.

[40M handoff_inventory.csv](../../market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/handoff_inventory.csv) фіксує потрібний working-tree snapshot: repo-relative path, SHA256, bytes, роль, Git-tracked/ignored стан. До нього входять наявні Git-tracked файли, нові канонічні документи й research-код,40A–40L research-run files включно з невибраними trials, звіти перевірок та232 frozen raw source files. Python/test caches, тимчасові pytest fixture trees (`*_checks_*`, `test_*` каталоги всередині старої підготовки) і symlinks не входять; вони не є strategy trials. Файли копіюються байт-в-байт: зміна line endings теж змінює hash. Сам інвентар не є архівом або Git commit.

На дату перевірки offline-середовище: Python3.12.0, pandas2.3.0, numpy2.2.6, pytest9.0.2. `requirements.txt` містить лише широкий pandas range і не є повним lock для серверного процесу/колектора. Зафіксувати сумісне середовище окремо на етапі переносу; цей документ нічого не встановлює.

З кореня **повної копії** репозиторію/working snapshot:

```powershell
# Лише читання: документи, посилання, усі inventory SHA256, старі40H/L bindings.
python market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/handoff.py verify

# Цільові історичні контракти: останній записаний результат —15 passed.
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -q market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/test_policy.py tests/test_strategy_search_replay.py
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD

# Повне фінансове відтворення: тільки в окремій повній offline-копії.
# Команда переписує40L generated outputs у цій копії; frozen rules/hashes не редагувати.
python market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/run_study.py
```

Linux: те саме `python ...`; для тестів `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q <ті самі два test-файли>`. Повний canonical regression при зміні reusable коду: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`; наведені раніше 752/762 — історичні результати відповідних завдань, не новий прогін40M.

Критерій відтворення: усі source/code hashes збігаються,13 control rows збережені,59 raw candidates/22 pre-book eligible/14 виконаних входів, net1060.9076400647832USDC. Мала floating serialization tolerance допустима для числової звірки, не для прихованої зміни правил або підміни джерел. Верифікація40L перевірила 14 first-touch/cash paths і старий реальний prefix; це не financial holdout.

Змінені входи/фільтри/витрати/cutoff/нові дані → новий task/run root, новий manifest, control і audit. Не оновлювати manifest чужими поточними hashes лише для обходу помилки відтворення. Історичний frozen feed snapshot треба зберегти перед дописуванням нових днів.

## 8. Дорожня карта серверного запуску й API

Нижче — **майбутні роботи та критерії готовності**, а не реалізовані сервіси. Відомий із40K SSH alias `vps95` і `/opt/aitrader_data/feed/` — лише джерело прочитаних futures-файлів. Шлях розгортання стратегії, service unit, venv/container, runtime account, чинний Executor deployment та приватний API цього checkout не перевірені. Не вгадувати їх із назви alias або старих логів. У корені цього checkout немає пакета `executor/`; інтеграція з іншим Executor потребує перевірки його фактичного контракту.

| Етап | Що зробити | Критерій завершення |
|---|---|---|
| A. Передати immutable snapshot | Зберегти код, канонічні документи, весь inventory/trials і raw inputs; перевірити SHA256 на цілі; зафіксувати release identity/environment. | `handoff.py verify` проходить на копії; offline40L відтворює14угод/+1060,907640. Доступ до сервера/встановлення — у відповідно дозволеному завданні. |
| B. Виділити strategy engine | Версіонований pure evaluator із exact40H rules + явно задекларованою політикою майбутніх дат; розділити features/state, candidate/gates, book і execution adapter. | Кандидати/відмови/часы/SL/TP/гроші збігаються з frozen replay; не активовано legacy Backtester або нову стратегію непомітно. |
| C. Серверний shadow без заявок | Public futures+spot observations, перевірені close clocks, all-history bootstrap, persistent checkpoint і детермінований replay після restart; журнал candidate→gate→book. | Один і той самий закритий H1 дає один ідентичний сигнал після повторної доставки/restart; неповні/застарілі дані не створюють нових входів. Немає ордерів. |
| D. Read-only account adapter | В окремо дозволеній фазі перевірити account/market support, margin режим, balances, pair filters/precision/minimum notional, borrow availability/rates, fees, status/clock/reconciliation. | Account evidence і версія актуального офіційного API зафіксовані; числові припущення не видаються за тарифи. Немає order/borrow calls. |
| E. Paper execution / adapter scenarios | Програти fills, partial/rejected/timeout/retry, rounding, stop/TP protection, expiry, borrow/repay lifecycle та reboot reconciliation без реальних грошей. | Немає дубльованих заявок/позицій, uncovered residual BTC або забутих боргів; quantity/PnL у фактичних валютах і costs звіряються. Історична5USDC модель збережена окремо від фактичних costs. |
| F. Обмежений live-пілот | Лише після окремого явного user scope на live/orders/sizing, готового review і визначених лімітів. Увімкнення іншим завданням, не цією дорожньою картою. | Вибрані account/margin/sizing/limits, аварійна зупинка, біржовий захист, моніторинг і rollback перевірені; actual fills/fees/borrow/repay записуються та звіряються. |

### Контракти, які треба реалізувати на B–E

**Signal envelope** (пропозиція для майбутнього модуля): стабільні `strategy_version`, `signal_id`, symbol/markets, direction/family, `candle_close_at`, `decision_at`, `available_at`, source/checkpoint hashes, delta values/usable flags, H4 reference та його availability, basis із двома quote timestamps, entry deadline/latency, mapped structural anchors/ATR, stop/target rule versions, gate-rejection reasons. При зміні даних/версії ідентичність має бути явною.

**Persistent state**: останній оброблений close/sequence, causal EMA/ATR/flow windows, H4 inventory і retirement counters, processed signal IDs, global position/cooldown, entry/fill timestamps, quantity, initial stop/risk/target, expiry, order identifiers/status/fills, fees і borrow/repay ledger. Після restart спочатку відновити попередній market state та звірити позиції/заявки/борги з біржею, потім обробляти нові входи. Порожній local state не означає відсутність позиції на біржі.

**Execution adapter**: futures лишається джерелом сигналів, усі fills — BTCUSDC Spot Margin; short передбачає фактичну позику BTC, продаж, зворотну купівлю і погашення. Жодних futures orders замість spot і жодного продажу неіснуючого BTC під виглядом звичайного spot. Підтримка інструмента, borrow та типів захисних заявок перевіряється в актуальному account/API на етапі інтеграції; конкретні endpoints/SDK тут не оголошені перевіреними.

Actual entry fills можуть відрізнятися від historical minute open. До live визначити правило для weighted partial fills, допустимого delay/slippage, остаточних SL/TP від фактичного E та rounding, повторної перевірки risk-band і захисту вже заповненої частини. Не зсувати basis/structural context майбутніми даними. Зміна економіки або entry policy потребує версії й paper parity/sensitivity, не мовчазної підстановки.

**Журнал фактичної угоди**: signal ID і часи рішення/відправки/ack/fill, planned/actual prices і quantity, stop/target amendments/status, gross, кожний fee asset/amount і конверсія, actual borrow asset/rate/accrual/repay, net у USDC, close reason, account reconciliation, omission/outage events. Funding futures — signal evidence; не списувати його автоматично як spot financing.

### Що ще потребує конкретного рішення перед live

| Невідоме / межа моделі | Що має з'ясувати наступний агент |
|---|---|
| Spot Margin режим і доступність BTCUSDC для цього рахунку | Підтримуваний account/pair/margin mode; не успадковувати isolated2x з початкового README як погоджену поточну конфігурацію. |
| Капітал і sizing | 3 000USDC — дослідницький notional, не автоматичний live ліміт. Узгодити actual cap, available balance/reserve, BTC quantity rounding, max debt/loss; не підміняти на risk1% без версії. |
| Borrow і costs | Історична доступність/реальна ставка/округлення часу, repay/residual debt, fees/spread/depth. Додати actual costs окремо; не перейменовувати model net у net після всіх live витрат. |
| Прострочені або неповні дані | Межа entry latency/staleness і точний fail-closed/recovery policy при extended gap; біржовий захист відкритої позиції має жити незалежно від signal-feed. |
| Ідентичність live vs replay | Close-label, H4 confirmation clocks, refresh/resume, часткові fills, timezone UTC; DST лише для відображення. Поточний strict replay censor не є інструкцією забути реальну позицію. |
| Доказ прибутковості поза вибіркою | Фіксовані правила на справді наступних даних без відбору порогів; ці14угод не дають гарантії подальшої прибутковості. |

## 9. Завершення40M і правила подальшої передачі

Документ пов'язаний із README/AGENTS/PROJECT_LOG/ACTIVE_DOCS/NEXT_TASK/PROJECT_STATE. [40M verification.json](../../market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/verification.json) фіксує перевірку локальних посилань, inventory hashes, 40H/L rule/result bindings і фінансової таблиці. Новий trading replay або regression suite для документації не запускався; історичні15tests та14paths належать40L. У40M захищені feed assets, frozen code, покажчики40H/L і попередні результати не змінені.

Перший наступний інженерний крок — **відтворити immutable snapshot і підготувати pure strategy engine з parity**, після чого серверний shadow. Кожен етап має власний scope, докази, версію і handoff entry у PROJECT_LOG. Дослідницьку позитивну модель не позначати production-ready, а невибрані варіанти не домішувати до user-selected40H.
