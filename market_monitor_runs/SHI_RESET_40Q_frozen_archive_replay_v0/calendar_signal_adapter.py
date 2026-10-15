def signals(bars: pd.DataFrame, family: str, lookback: int, flow: float, volume: float, trend: str) -> np.ndarray:
    upper, lower = (bars[f'upper{lookback}'], bars[f'lower{lookback}'])
    if family == 'ACCEPTED_BREAK':
        upper_fixed, lower_fixed = (upper.shift(1), lower.shift(1))
        long = bars.close.gt(upper_fixed) & bars.close.shift().gt(upper_fixed)
        short = bars.close.lt(lower_fixed) & bars.close.shift().lt(lower_fixed)
        long &= ~long.shift(fill_value=False)
        short &= ~short.shift(fill_value=False)
    elif family == 'BREAKOUT':
        long, short = (bars.close.gt(upper), bars.close.lt(lower))
    elif family == 'TREND_RETEST':
        long = bars.low.le(bars.ema24) & bars.close.gt(bars.ema24) & bars.close.gt(bars.open)
        short = bars.high.ge(bars.ema24) & bars.close.lt(bars.ema24) & bars.close.lt(bars.open)
    elif family == 'SWEEP_RECLAIM':
        long = bars.low.shift().lt(lower.shift()) & bars.close.gt(lower.shift()) & bars.close.gt(bars.open)
        short = bars.high.shift().gt(upper.shift()) & bars.close.lt(upper.shift()) & bars.close.lt(bars.open)
    else:
        raise ValueError(family)
    if trend == 'EMA':
        long &= bars.ema24.gt(bars.ema72) & bars.close.gt(bars.ema168)
        short &= bars.ema24.lt(bars.ema72) & bars.close.lt(bars.ema168)
    elif trend == 'PRESSURE':
        long &= bars.change24.gt(0) & bars.delta24.gt(0)
        short &= bars.change24.lt(0) & bars.delta24.lt(0)
    elif trend != 'NONE':
        raise ValueError(trend)
    long &= bars.delta.ge(flow)
    short &= bars.delta.le(-flow)
    quality = bars.context_usable & bars.usable & bars.volume_ratio.ge(volume)
    quality &= bars.usable.shift().rolling(lookback, min_periods=lookback).sum().eq(lookback)
    return np.where(quality & long & ~short, 1, np.where(quality & short & ~long, -1, 0))
