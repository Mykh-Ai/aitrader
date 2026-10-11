from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
import pytest

from market_monitor.closed_structure_adapter import ClosedStructureMonitor, minute_frame
from market_monitor.zone_registry import _htf_lifecycle_metrics

T=datetime(2026,3,20,tzinfo=timezone.utc)

def data(hours=8):
    out=[]
    # Strict H1 high centered in hour 2, confirmed at hour 5 close.
    for i in range(hours*60):
        h=[100.,105.,120.,106.,104.,103.,130.,102.][i//60]
        out.append(SimpleNamespace(ts=T+timedelta(minutes=i+1),open=95.,high=h,low=90.,close=95.,
                                   volume=10.,buy_qty=8.,sell_qty=2.,is_synthetic=False))
    return out

def test_reference_not_available_at_confirmation_bar_open_or_partial_close():
    seq=data()
    full=ClosedStructureMonitor(seq)
    refs=[r for r in full.references if r.timeframe=='H1' and r.price==120.]
    assert len(refs)==1 and refs[0].available_at==T+timedelta(hours=5)
    assert not ClosedStructureMonitor(seq[:299]).references
    assert len(ClosedStructureMonitor(seq[:300]).references)==1

def test_reference_inventory_is_prefix_equivalent_and_gap_rejects_fractal():
    seq=data();cutoff=T+timedelta(hours=5)
    prefix=ClosedStructureMonitor(seq[:300])
    full=ClosedStructureMonitor(seq)
    assert [r for r in full.inventory() if pd.Timestamp(r['available_at'])<=cutoff]==prefix.inventory()
    assert not ClosedStructureMonitor(seq[:100]+seq[101:300]).references

def test_lifecycle_cannot_count_incomplete_h1_as_a_close_through():
    seq=data(1)
    for b in seq:b.close=110.;b.high=111.
    frame=minute_frame(seq)
    row={'source_timeframes':'H1','htf_level_type':'H1_SWING_HIGH','side':'BUY_SIDE',
         'first_seen_at':T.isoformat(),'htf_confirmation_timestamp':T.isoformat()}
    partial=_htf_lifecycle_metrics(row,frame.iloc[:59],99.,101.,closed_htf_only=True)
    complete=_htf_lifecycle_metrics(row,frame,99.,101.,closed_htf_only=True)
    assert partial['htf_close_through_count']==0
    assert complete['htf_close_through_count']==1
    missing=_htf_lifecycle_metrics(row,frame.drop(index=20),99.,101.,closed_htf_only=True)
    assert missing['htf_close_through_count']==0

def test_duplicate_minute_fails_closed():
    seq=data(1)
    with pytest.raises(ValueError,match='unique'):
        ClosedStructureMonitor(seq+seq[-1:])


def test_query_scores_and_selection_do_not_depend_on_future_rows():
    seq=data()
    for b in seq:
        b.open*=1000; b.high*=1000; b.low*=1000; b.close*=1000
    for b in seq[360:]:
        b.close=120200.;b.high=max(b.high,120210.)
    cutoff=seq[379].ts
    short=ClosedStructureMonitor(seq[:380])
    full=ClosedStructureMonitor(seq)
    assert short.query(cutoff)==full.query(cutoff)
    _,counts,evidence=full.query(cutoff)
    assert evidence and all(pd.Timestamp(e['available_at'])<cutoff for e in evidence)
    assert all(pd.Timestamp(e['crossed_at'])<=cutoff for e in evidence)
    assert counts['known_references']==1


def test_old_level_below_price_without_recent_cross_cannot_arm():
    seq=data()
    for b in seq:
        b.open*=1000; b.high*=1000; b.low*=1000; b.close*=1000
    for b in seq[300:]:b.close=120200.;b.high=max(b.high,120210.)
    monitor=ClosedStructureMonitor(seq)
    zones,counts,evidence=monitor.query(seq[-1].ts,crossing_lookback_minutes=30)
    assert not zones and not evidence and counts['no_recent_cross']>0
