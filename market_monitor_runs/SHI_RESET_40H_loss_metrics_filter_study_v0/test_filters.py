from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from filters import filtered_directions, allow_rule
from study import features, entry_metrics


def test_delta_exhaustion_boundaries_and_direction_scope():
    f = pd.DataFrame({"signal_index": range(6), "direction": [1, 1, -1, -1, 1, -1],
                      "window24_usable": True, "delta24_pct": [4., 3.999, -4., -3.999, -8., 8.]})
    assert allow_rule(f, "B_D24_BAND4").tolist() == [False, True, False, True, False, False]
    assert allow_rule(f, "L_D24_LT4").tolist() == [False, True, True, True, True, True]
    assert allow_rule(f, "S_D24_GT_NEG4").tolist() == [True, True, False, True, True, True]


def test_filter_combination_never_revives_short_space_rejection_or_needs_outcome():
    f = pd.DataFrame({"signal_index": [1, 3, 4, 6], "direction": [1, -1, 1, -1],
                      "window24_usable": True, "window4_usable": True,
                      "delta24_pct": [1., -1., 1., -1.], "delta4_pct": [-1., -4., 4., -4.]})
    original = np.array([0, 1, 0, 0, 1, 0, -1])
    result, allowed = filtered_directions(original, f, {"rules": ["L_D4_POS", "B_D24_BAND4"]})
    np.testing.assert_array_equal(result, [0, 0, 0, 0, 1, 0, -1])
    assert allowed.tolist() == [False, True, True, True]
    np.testing.assert_array_equal(original, [0, 1, 0, 0, 1, 0, -1])


def test_missing_feature_is_rejected_only_for_affected_direction():
    f = pd.DataFrame({"direction": [1, -1, 1], "window4_usable": [False, False, True], "delta4_pct": [np.nan, np.nan, 0.]})
    assert allow_rule(f, "L_D4_POS").tolist() == [False, True, False]


def test_time_window_edges_are_known_planned_entry_hours():
    f = pd.DataFrame({"direction": [1]*6 + [-1], "entry_hour_utc": [3,4,7,8,15,16,5]})
    assert allow_rule(f, "L_SKIP04_08").tolist() == [True,False,False,True,True,True,True]
    assert allow_rule(f, "B_ONLY08_16").tolist() == [False,False,False,True,True,False,False]


def raw_fixture():
    ts = pd.date_range("2026-03-28T00:01Z", periods=36*60, freq="min")
    n = len(ts)
    f = pd.DataFrame({"Timestamp": ts, "OpenPrice": 100., "HiPrice":101., "LowPrice":99., "ClosePrice":100.,
                      "TotalQty":10., "BuyQty":5., "SellQty":5., "OpenInterest":np.arange(n)+1000.,
                      "FundingRate":.0001, "LiqBuyQty":1., "LiqSellQty":2., "LiquidationDataAvailable":True,
                      "DataQuality":"RAW", "IsRecovered":False, "IsSynthetic":0, "InvalidRow":False})
    # A large buy minute makes volume-weighted delta very different from mean percentages.
    f.loc[120, ["TotalQty", "BuyQty", "SellQty"]] = [1000.,1000.,0.]
    return f


SPEC = {"long":{"exit":{"stop_lookback":6,"atr_floor":2.,"target_r":10.,"trail_atr":0.,"hold_hours":168}}}


def test_raw_24h_delta_weighting_clock_and_future_mutation_invariance():
    f = raw_fixture()
    b = features(f)
    i = 24
    directions = np.ones(len(b), dtype=int)
    actual = entry_metrics(f,b,directions,[i],SPEC)
    decision = b.available_at.iloc[i]
    w = f.loc[(f.Timestamp>decision-pd.Timedelta(hours=24)) & (f.Timestamp<=decision)]
    expected = 100*(w.BuyQty.sum()-w.SellQty.sum())/w.TotalQty.sum()
    np.testing.assert_allclose(actual.delta24_pct.iloc[0], expected)
    assert abs(expected - (100*(w.BuyQty-w.SellQty)/w.TotalQty).mean()) > 1
    changed = f.copy()
    changed.loc[changed.Timestamp>decision, ["BuyQty","TotalQty","OpenInterest"]] = 1e12
    changed_bars = features(changed)
    observed = entry_metrics(changed,changed_bars,directions,[i],SPEC)
    pd.testing.assert_frame_equal(actual, observed)
    assert actual.window24_last_observation_at.iloc[0] <= decision
    assert actual.local_utc_offset_hours.iloc[0] == 2 # DST changed that UTC day.


def test_one_omitted_minute_preserves_context_and_next_real_time():
    f = raw_fixture().drop(index=200).reset_index(drop=True)
    b = features(f)
    actual = entry_metrics(f,b,np.ones(len(b),dtype=int),[24],SPEC)
    assert actual.window24_usable.iloc[0]
    assert actual.observed_minutes24.iloc[0] == 1439
    assert actual.window24_last_observation_at.iloc[0] == b.available_at.iloc[24]
