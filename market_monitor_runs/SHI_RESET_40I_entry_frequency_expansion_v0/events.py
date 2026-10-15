"""Second adaptive batch: complementary causal entry events, same fixed exits."""
import numpy as np

from research.strategy_search.features import signals


def event_variants():
    patterns=[]
    for side,family in [(1,"ACCEPTED_BREAK"),(1,"BREAKOUT"),(-1,"BREAKOUT")]:
        for lookback in [24,48]:
            for volume in [1.3,1.1]:
                patterns.append({"id":f'{"L" if side>0 else "S"}_{family}_{lookback}_V{int(volume*10)}',
                                 "events":[{"side":side,"family":family,"lookback":lookback,"volume":volume,"flow":.04}]})
    for volume in [1.3,1.1]:
        patterns.append({"id":f'S_RETEST_V{int(volume*10)}',"events":[{"side":-1,"family":"TREND_RETEST","lookback":96,"volume":volume,"flow":.04}]})
    pairs=[("ACCEPTED_BREAK",48,"TREND_RETEST",96),("ACCEPTED_BREAK",24,"TREND_RETEST",96),
           ("BREAKOUT",48,"BREAKOUT",48),("ACCEPTED_BREAK",48,"BREAKOUT",48),("ACCEPTED_BREAK",24,"BREAKOUT",24)]
    for lf,ll,sf,sl in pairs:
        for vol,flow in [(1.3,.04),(1.1,.02)]:
            patterns.append({"id":f'PAIR_L_{lf}{ll}_S_{sf}{sl}_V{int(vol*10)}',"events":[
                {"side":1,"family":lf,"lookback":ll,"volume":vol,"flow":flow},
                {"side":-1,"family":sf,"lookback":sl,"volume":vol,"flow":flow}]})
    return [{"id":f'EXTRA_{p["id"]}_B{int(bound)}',"events":p["events"],"delta24_bound_pct":bound} for p in patterns for bound in [4.,6.]]


def extra_event_signals(b,config):
    side=config["side"]
    trend="PRESSURE" if side<0 and config["family"]=="BREAKOUT" else "EMA"
    raw=signals(b,config["family"],config["lookback"],config["flow"],config["volume"],trend)
    keep=raw==side
    if config["family"]=="BREAKOUT":
        # One newly closed first crossing of the moving prior range per episode.
        # No repeated signal for every later close in the same breakout episode.
        previous=np.r_[False,keep[:-1]]
        keep &=~previous
    keep &= ((b.close-b.ema24).abs()/b.atr).le(2.).to_numpy()
    keep &= ((b.high-b.low)/b.atr).le(2.5).to_numpy()
    return np.where(keep,side,0)


def combine_streams(*streams):
    long=np.logical_or.reduce([x>0 for x in streams])
    short=np.logical_or.reduce([x<0 for x in streams])
    return np.where(long&~short,1,np.where(short&~long,-1,0))
