"""Finite, adaptive hypotheses declared after diagnostics, before filter returns."""
import numpy as np


VARIANTS = [
    {"id": "BASELINE", "rules": []},
    {"id": "LONG_DELTA4_POS", "rules": ["L_D4_POS"]},
    {"id": "LONG_DELTA24_LT4", "rules": ["L_D24_LT4"]},
    {"id": "SHORT_DELTA24_GT_NEG4", "rules": ["S_D24_GT_NEG4"]},
    {"id": "BOTH_DELTA24_BAND4", "rules": ["B_D24_BAND4"]},
    {"id": "LONG_DELTA24_POS", "rules": ["L_D24_POS"]},
    {"id": "LONG_DELTA4_POS_DELTA24_LT4", "rules": ["L_D4_POS", "L_D24_LT4"]},
    {"id": "LONG_DELTA4_POS_BOTH_BAND4", "rules": ["L_D4_POS", "B_D24_BAND4"]},
    {"id": "LONG_DELTA4_POS_BOTH_BAND2", "rules": ["L_D4_POS", "B_D24_BAND2"]},
    {"id": "LONG_DELTA4_POS_BOTH_BAND6", "rules": ["L_D4_POS", "B_D24_BAND6"]},
    {"id": "LONG_OI_NONNEG", "rules": ["L_OI_GE0"]},
    {"id": "LONG_OI_GT_NEG2", "rules": ["L_OI_GT_NEG2"]},
    {"id": "SHORT_OI_NONNEG", "rules": ["S_OI_GE0"]},
    {"id": "BOTH_OI_NONNEG", "rules": ["B_OI_GE0"]},
    {"id": "LONG_LIQ_SELL_GE_BUY", "rules": ["L_LIQ_SELL"]},
    {"id": "LONG_RANGE_ATR_GE1_25", "rules": ["L_RANGE_GE1_25"]},
    {"id": "SHORT_VOLUME_LT4", "rules": ["S_VOL_LT4"]},
    {"id": "SHORT_FUNDING_NONNEG", "rules": ["S_FUNDING_GE0"]},
    {"id": "LONG_SKIP_UTC04_08", "rules": ["L_SKIP04_08"]},
    {"id": "LONG_SKIP_UTC16_20", "rules": ["L_SKIP16_20"]},
    {"id": "LONG_SKIP_UTC04_08_AND16_20", "rules": ["L_SKIP04_08", "L_SKIP16_20"]},
    {"id": "BOTH_UTC08_16_ONLY", "rules": ["B_ONLY08_16"]},
]


def allow_rule(f, name):
    long = f.direction.gt(0)
    short = f.direction.lt(0)
    if name == "L_D4_POS":
        return ~long | (f.window4_usable & f.delta4_pct.gt(0))
    if name == "L_D24_LT4":
        return ~long | (f.window24_usable & f.delta24_pct.lt(4))
    if name == "S_D24_GT_NEG4":
        return ~short | (f.window24_usable & f.delta24_pct.gt(-4))
    if name.startswith("B_D24_BAND"):
        bound = float(name.rsplit("BAND", 1)[1])
        return f.window24_usable & f.delta24_pct.abs().lt(bound)
    if name == "L_D24_POS":
        return ~long | (f.window24_usable & f.delta24_pct.gt(0))
    if name in ["L_OI_GE0", "S_OI_GE0", "B_OI_GE0"]:
        applies = long if name.startswith("L_") else short if name.startswith("S_") else long | short
        return ~applies | (f.window24_usable & f.oi24_pct.ge(0))
    if name == "L_OI_GT_NEG2":
        return ~long | (f.window24_usable & f.oi24_pct.gt(-2))
    if name == "L_LIQ_SELL":
        return ~long | (f.liquidation24_available & f.liq_sell24_btc.ge(f.liq_buy24_btc))
    if name == "L_RANGE_GE1_25":
        return ~long | f.range_atr.ge(1.25)
    if name == "S_VOL_LT4":
        return ~short | f.volume_ratio.lt(4)
    if name == "S_FUNDING_GE0":
        return ~short | (f.window24_usable & f.funding_current.ge(0))
    if name == "L_SKIP04_08":
        return ~long | ~f.entry_hour_utc.between(4, 7)
    if name == "L_SKIP16_20":
        return ~long | ~f.entry_hour_utc.between(16, 19)
    if name == "B_ONLY08_16":
        return f.entry_hour_utc.between(8, 15)
    raise ValueError(name)


def filtered_directions(original, f, variant):
    result = original.copy()
    allowed = np.ones(len(f), dtype=bool)
    for rule in variant["rules"]:
        allowed &= allow_rule(f, rule).to_numpy()
    indexes = f.signal_index.to_numpy(dtype=int)
    result[indexes[~allowed]] = 0
    return result, allowed
