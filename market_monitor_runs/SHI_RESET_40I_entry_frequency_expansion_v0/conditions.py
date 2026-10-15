"""Bounded entry-frequency hypotheses; unchanged exit and feed contracts."""
import itertools
import numpy as np
import pandas as pd

from research.strategy_search.features import signals
from research.strategy_search.replay import ExitRules, initial_stop


DEFAULT = {"long_flow": .04, "long_volume": 1.3, "touch_atr": 0., "maturity_atr": 1.5, "impulse_atr": 2.,
           "short_volume": 1.3, "short_lookback": 48, "short_space_r": 1., "delta24_bound_pct": 4., "long_delta4_floor_pct": 0.}


def variants():
    rows, seen = [], set()
    def add(name, **changes):
        config = {**DEFAULT, **changes}
        key = tuple(config.items())
        if key not in seen:
            seen.add(key)
            rows.append({"id": name, "parameters": config, "changed_parameters": sum(config[k] != DEFAULT[k] for k in DEFAULT)})
    add("BASELINE_40H")
    for name,changes in [
        ("L_FLOW02", {"long_flow":.02}), ("L_FLOW00", {"long_flow":0.}),
        ("L_VOL11", {"long_volume":1.1}), ("L_VOL10", {"long_volume":1.}),
        ("S_VOL11", {"short_volume":1.1}), ("S_VOL10", {"short_volume":1.}),
        ("BOTH_VOL11", {"long_volume":1.1,"short_volume":1.1}),
        ("BOTH_VOL10", {"long_volume":1.,"short_volume":1.}),
        ("L_TOUCH015", {"touch_atr":.15}), ("L_TOUCH030", {"touch_atr":.30}),
        ("L_MATURITY2", {"maturity_atr":2.}), ("L_IMPULSE25", {"impulse_atr":2.5}),
        ("L_MATURITY2_IMPULSE25", {"maturity_atr":2.,"impulse_atr":2.5}),
        ("S_LOOKBACK24", {"short_lookback":24}), ("S_SPACE075", {"short_space_r":.75}),
        ("DELTA24_BAND6", {"delta24_bound_pct":6.}), ("LONG_DELTA4_GT_NEG1", {"long_delta4_floor_pct":-1.}),
    ]:
        add(name,**changes)
    longs = [
        ("STRICT",{}),
        ("FLOW02_VOL11",{"long_flow":.02,"long_volume":1.1}),
        ("FLOW00_VOL10",{"long_flow":0.,"long_volume":1.}),
        ("NEAR015",{"long_flow":.02,"long_volume":1.1,"touch_atr":.15}),
        ("NEAR030",{"long_flow":0.,"long_volume":1.,"touch_atr":.30,"maturity_atr":2.,"impulse_atr":2.5}),
    ]
    shorts = [("STRICT",{}),("VOL11",{"short_volume":1.1}),("LB24_VOL11",{"short_lookback":24,"short_volume":1.1})]
    for (ln,lc),(sn,sc),bound,floor in itertools.product(longs,shorts,[4.,6.],[0.,-1.]):
        add(f"L_{ln}_S_{sn}_B{int(bound)}_F{int(floor)}",**lc,**sc,delta24_bound_pct=bound,long_delta4_floor_pct=floor)
    return rows


def long_components(b, p):
    # Exactly the inherited data/calendar requirements; no exclusion relaxed.
    quality = b.usable & b.context_usable
    quality &= b.usable.shift().rolling(96,min_periods=96).sum().eq(96)
    quality &= b.timestamp.ge(pd.Timestamp("2026-03-18T14:00Z"))
    for start,end in [("2026-04-23T17:05","2026-05-10"),("2026-06-22","2026-06-29"),
                      ("2026-08-25","2026-09-01"),("2026-10-01","2026-10-13")]:
        quality &= ~b.timestamp.between(pd.Timestamp(start,tz="UTC"),pd.Timestamp(end,tz="UTC"),inclusive="left")
    stages = {"quality_calendar":quality,
              "trend": b.ema24.gt(b.ema72) & b.close.gt(b.ema168),
              "retest":b.low.le(b.ema24+p["touch_atr"]*b.atr) & b.close.gt(b.ema24) & b.close.gt(b.open),
              "hour_flow":b.delta.ge(p["long_flow"]),"volume":b.volume_ratio.ge(p["long_volume"]),
              "maturity_impulse":((b.close-b.ema24).abs()/b.atr).le(p["maturity_atr"]) & ((b.high-b.low)/b.atr).le(p["impulse_atr"])}
    return stages


def entry_signals(b,p):
    components = long_components(b,p)
    long = np.logical_and.reduce([x.to_numpy() for x in components.values()])
    short = signals(b,"ACCEPTED_BREAK",p["short_lookback"],0.,p["short_volume"],"PRESSURE") < 0
    return np.where(long & ~short,1,np.where(short & ~long,-1,0))


def short_space_mask(fdata, indexes, spec, inventory, threshold):
    allowed = np.ones(len(fdata.bars),dtype=bool)
    rows=[]
    rules=ExitRules(**spec["short"]["exit"])
    for i in indexes:
        b=fdata.bars.iloc[i]
        risk=initial_stop(fdata,int(i),-1,b.close,rules)-b.close
        levels=[x for x in inventory[i] if x["side"]==-1 and x["price"]*1.0005 < b.close]
        nearest=max(levels,key=lambda x:x["price"],default=None)
        space=(b.close-nearest["price"]*1.0005)/risk if nearest and risk>0 else np.nan
        if nearest:
            assert nearest["available_at"]<=b.available_at
        allowed[i]=not(np.isfinite(space) and space<threshold)
        rows.append({"signal_index":int(i),"threshold":threshold,"opposing_h4_space_r":space,"allowed":bool(allowed[i]),
                     "reference_available_at":nearest["available_at"] if nearest else pd.NaT})
    return allowed,rows


def apply_flow(directions,metrics,p):
    result=directions.copy()
    f=metrics.set_index("signal_index")
    for i in np.flatnonzero(result):
        row=f.loc[i]
        ok=bool(row.window24_usable and abs(row.delta24_pct)<p["delta24_bound_pct"])
        if result[i]>0:
            ok &= bool(row.window4_usable and row.delta4_pct>p["long_delta4_floor_pct"])
        if not ok:
            result[i]=0
    return result
