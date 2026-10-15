from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parents[1]))
sys.path.insert(0,str(OUT))
from conditions import DEFAULT,entry_signals,short_space_mask,apply_flow
from events import combine_streams,extra_event_signals
from research.strategy_search.hybrid import hybrid_signals


def bars_fixture():
    n=150
    ts=pd.date_range("2026-07-01T00:00Z",periods=n,freq="h")
    b=pd.DataFrame({"timestamp":ts,"available_at":ts,"usable":True,"context_usable":True,
        "open":100.,"close":101.,"high":102.,"low":100.,"ema24":100.2,"ema72":99.,"ema168":98.,"atr":2.,
        "delta":.05,"delta24":.01,"change24":.01,"volume_ratio":1.5})
    for h in [6,24,48,96]:
        b[f"upper{h}"]=110.
        b[f"lower{h}"]=90.
    return b


def test_default_reproduces_original_generator_and_does_not_mutate_bars():
    b=bars_fixture()
    saved=b.copy(deep=True)
    long={"family":"TREND_RETEST","lookback":96,"flow":.04,"volume":1.3,"trend":"EMA","maturity":1.5,"impulse":2.}
    short={"family":"ACCEPTED_BREAK","lookback":48,"flow":0.,"volume":1.3,"trend":"PRESSURE"}
    np.testing.assert_array_equal(entry_signals(b,DEFAULT),hybrid_signals(b,long,short))
    pd.testing.assert_frame_equal(b,saved)


def test_near_ema_accepts_only_declared_tolerance_with_green_close_above_ema():
    b=bars_fixture()
    b["low"]=100.4
    assert not (entry_signals(b,DEFAULT)>0).any()
    relaxed={**DEFAULT,"touch_atr":.15}
    assert entry_signals(b,relaxed)[100]==1
    b.loc[100,"low"]=100.51
    assert entry_signals(b,relaxed)[100]==0
    b.loc[100,["low","close"]]=[100.4,100.1]
    assert entry_signals(b,relaxed)[100]==0


def test_relaxation_preserves_recovered_context_and_calendar_exclusions():
    b=bars_fixture()
    b.loc[90,"usable"]=False
    assert entry_signals(b,{**DEFAULT,"long_flow":0.,"long_volume":1.,"touch_atr":.3})[100]==0
    b=bars_fixture()
    b.loc[100,["timestamp","available_at"]]=pd.Timestamp("2026-06-23T01:00Z")
    assert entry_signals(b,{**DEFAULT,"long_flow":0.,"long_volume":1.})[100]==0


def test_space_threshold_uses_known_decision_risk_and_confirmed_reference():
    when=pd.Timestamp("2026-07-01T00:00Z")
    b=pd.DataFrame({"close":[100.,100.],"upper6":[101.,101.],"available_at":[when,when]})
    data=SimpleNamespace(bars=b,atr=np.array([2.,2.]))
    inventory={i:[{"side":-1,"price":(100-space*3)/1.0005,"available_at":when-pd.Timedelta(hours=4)}] for i,space in enumerate([.8,.7])}
    spec={"short":{"exit":{"stop_lookback":6,"atr_floor":1.5,"target_r":6.,"trail_atr":0.,"hold_hours":168}}}
    allowed,rows=short_space_mask(data,[0,1],spec,inventory,.75)
    assert allowed.tolist()==[True,False]
    np.testing.assert_allclose([x["opposing_h4_space_r"] for x in rows],[.8,.7])


def test_combination_conflict_is_suppressed_before_outcomes():
    np.testing.assert_array_equal(combine_streams(np.array([1,1,0,-1]),np.array([-1,1,1,-1])),[0,1,1,-1])


def test_first_break_emits_new_episode_once_with_prefix_invariance():
    b=bars_fixture()
    b[["open","close","high","low","ema24"]]=[92.,91.,93.,88.,92.]
    b[["delta","delta24","change24"]]=[-.05,-.01,-.01]
    b.loc[[99,100,102],"close"]=[89.,88.5,89.]
    config={"side":-1,"family":"BREAKOUT","lookback":48,"volume":1.3,"flow":.04}
    s=extra_event_signals(b,config)
    assert s[99]==-1 and s[100]==0 and s[102]==-1
    np.testing.assert_array_equal(s[:101],extra_event_signals(b.iloc[:101],config))


def test_flow_relaxation_does_not_promote_unusable_windows():
    f=pd.DataFrame({"signal_index":[0,1,2],"window24_usable":[True,True,False],"delta24_pct":[5.,2.,0.],
                    "window4_usable":[True,False,True],"delta4_pct":[-.5,1.,1.]})
    np.testing.assert_array_equal(apply_flow(np.array([1,1,-1]),f,{**DEFAULT,"delta24_bound_pct":6.,"long_delta4_floor_pct":-1.}),[1,0,0])
