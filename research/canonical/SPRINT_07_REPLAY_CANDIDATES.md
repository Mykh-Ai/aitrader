# Sprint 07 Replay Candidates

These are replay-spec candidates only. They are not strategies and not promotions.

## CAND_BTC_EXH_SHORT_24_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_12_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_60_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_60_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_6_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_12_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_24_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_3_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_6_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_3_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_100200_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_4560_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_60100_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_24_REJ_STRONGGE045_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_12_REJ_STRONGGE045_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_60_REJ_STRONGGE045_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_6_REJ_STRONGGE045_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_3_REJ_STRONGGE045_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_24_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_12_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_6_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_60_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_SHORT_3_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_12_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_24_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_24_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_60_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_12_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_60_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_6_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_12_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `12` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 12 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_6_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_VOL_Q95PLUS_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_6_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `6` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 6 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_VOL_BELOWQ75_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_24_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `24` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 24 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_60_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `60` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 60 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_EXH_LONG_3_VOL_Q95PLUS_V1

- family: `EXHAUSTION_REVERSAL`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay.
- target candidate idea: VWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_SHORT_3_VOL_Q9095_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `SHORT`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: SHORT replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.

## CAND_BTC_VWAP_DEV_LONG_3_VOL_Q7590_V1

- family: `VWAP_DEVIATION_REVERSION`
- side: `LONG`
- horizon: `3` bars
- observable entry predicates: Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates.
- do not use outcomes as predicates.
- suggested formal replay direction: LONG replay after event close; earliest entry next M1 bar open.
- stop candidate idea: Beyond deviation event extreme or volatility-based hard stop; define before replay.
- target candidate idea: DayVWAP touch or fixed-R target candidate; choose one before replay.
- expiry candidate idea: 3 bars after activation as discovery-derived candidate expiry; freeze before replay.
- known weaknesses: Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.
- required next validation: Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.
