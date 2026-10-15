from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
H=ROOT/"market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
for p in [ROOT,H,OUT]:
    sys.path.insert(0,str(p))
from study import load,entry_metrics,digest,replay_hybrid,metrics,features,ReplayData,hybrid_signals,h4_inventory,candidate_map
from filters import filtered_directions
from mirror import short_mirror


def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,default=str,allow_nan=False)+"\n",encoding="utf-8")


def freeze():
    paths=[H/"artifact_hashes.json",ROOT/"research/active_own_signal_selection.json"]
    paths +=[H/p for p in json.loads((H/"artifact_hashes.json").read_text())]
    manifest={"task":"SHI_RESET_40J_SHORT_DELTA4_MIRROR","date":"2026-10-15","phase":"TWO_VARIANTS_FIXED_BEFORE_NEW_RETURNS",
        "variants":[{"id":"CONTROL_40H","extra_rule":None},{"id":"SHORT_DELTA4_NEGATIVE","extra_rule":"SHORT requires weighted rolling4h futures delta strictly<0; zero/missing/unusable rejected."}],
        "baseline":"Entire user-selected40H including24h strict band(-4%,+4%), long4h>0, short-space1R and original entry families.",
        "code_hashes":{n:digest(OUT/n) for n in ["mirror.py","run_study.py"]},
        "preserved_hashes":{p.relative_to(ROOT).as_posix():digest(p) for p in paths},
        "unchanged":"Separate BTCUSDT futures signals/BTCUSDC spot execution; full prior chronology/no reset; isolated-minute continuation; old entry/SL/TP/168h/latency/cooldown/one book;3000USDC/5USDC fee/2bps slip.",
        "selection":"Sensitivity only. Keep selected40H pointer unchanged; report any removed winners/losses and newly admitted entries with full portfolio reconciliation.",
        "pristine_holdout":False,"production_promoted":False,"actual_borrowing_in_net":False}
    path=OUT/"study_manifest.json"
    if path.exists():
        assert json.loads(path.read_text())==manifest
    else:
        save(path.name,manifest)
    return manifest


def attribution(old,new,control,mirror,raw_features):
    old=old.set_index("signal_index")
    new=new.set_index("signal_index")
    f=raw_features.set_index("signal_index")
    rows=[]
    for i,r in old.iterrows():
        retained=i in new.index
        if retained:
            np.testing.assert_allclose(r.net_usd,new.loc[i,"net_usd"],atol=1e-8)
        rows.append({"signal_index":i,"direction":r.direction,"entry_at":r.entry_at,"exit_at":r.exit_at,
                     "delta4_pct":f.loc[i,"delta4_pct"],"baseline_net_quote":r.net_usd,
                     "current_net_quote":new.loc[i,"net_usd"] if retained else np.nan,
                     "status":"RETAINED" if retained else "BLOCKED_BY_SHORT_DELTA4" if mirror[i]==0 else "DISPLACED_BY_BOOK"})
    for i,r in new.loc[~new.index.isin(old.index)].iterrows():
        rows.append({"signal_index":i,"direction":r.direction,"entry_at":r.entry_at,"exit_at":r.exit_at,
                     "delta4_pct":f.loc[i,"delta4_pct"],"baseline_net_quote":np.nan,"current_net_quote":r.net_usd,"status":"NEWLY_ADMITTED"})
    a=pd.DataFrame(rows)
    removed=a.loc[a.status.isin(["BLOCKED_BY_SHORT_DELTA4","DISPLACED_BY_BOOK"])]
    added=a.loc[a.status.eq("NEWLY_ADMITTED")]
    lost=removed.loc[removed.baseline_net_quote.gt(0),"baseline_net_quote"].sum()
    saved=-removed.loc[removed.baseline_net_quote.lt(0),"baseline_net_quote"].sum()
    delta=new.net_usd.sum()-old.net_usd.sum()
    np.testing.assert_allclose(delta,saved-lost+added.current_net_quote.sum(),atol=1e-8)
    return a,{"lost_baseline_wins":int(removed.baseline_net_quote.gt(0).sum()),"lost_win_quote":lost,
              "removed_baseline_losses":int(removed.baseline_net_quote.lt(0).sum()),"saved_loss_quote":saved,
              "new_trades":len(added),"new_trade_net_quote":added.current_net_quote.sum(),"net_change_quote":delta}


def verify_path(t,spot,directions,quotes):
    checked=0
    previous=None
    for r in t.itertuples():
        assert not r.censored and directions[r.signal_index]==r.direction
        if previous is not None:
            assert r.entry_at>previous+pd.Timedelta(minutes=3)
        previous=r.exit_at
        for q in [quotes.spot_close_at.iloc[r.signal_index],quotes.futures_close_at.iloc[r.signal_index]]:
            assert q<=r.decision_at and r.decision_at-q<=pd.Timedelta(minutes=1)
        assert r.decision_at<r.entry_at
        open_exit=r.exit_reason=="EXPIRY_NEXT_REAL_OPEN"
        end=r.exit_at+pd.Timedelta(minutes=1) if open_exit else r.exit_at
        path=spot.loc[spot.Timestamp.gt(r.entry_at)&spot.Timestamp.le(end)]
        assert len(path)>0 and path.Timestamp.diff().dropna().le(pd.Timedelta(minutes=2)).all()
        assert path.Timestamp.iloc[0]-pd.Timedelta(minutes=1)==r.entry_at
        np.testing.assert_allclose(r.entry_price,path.OpenPrice.iloc[0],atol=1e-8)
        stop=path.LowPrice.le(r.stop_price) if r.direction>0 else path.HiPrice.ge(r.stop_price)
        target=path.HiPrice.ge(r.target_price) if r.direction>0 else path.LowPrice.le(r.target_price)
        touch=stop|target
        if r.exit_reason=="EXPIRY":
            assert not touch.any() and r.exit_at==r.expiry_at
            expected=path.ClosePrice.iloc[-1]
        elif open_exit:
            assert not touch.iloc[:-1].any()
            expected=path.OpenPrice.iloc[-1]
        else:
            assert touch.any() and np.flatnonzero(touch)[0]==len(path)-1
            if r.exit_reason.startswith("STOP"):
                assert stop.iloc[-1]
                expected=path.OpenPrice.iloc[-1] if r.exit_reason=="STOP_GAP" else r.stop_price
            else:
                assert r.exit_reason=="TARGET" and target.iloc[-1] and not stop.iloc[-1]
                expected=r.target_price
        qty=3000/r.entry_price
        gross=r.direction*(expected-r.entry_price)*qty
        slip=(r.entry_price+expected)*qty*.0002
        risk=abs(r.entry_price-r.stop_price)*qty
        np.testing.assert_allclose([r.exit_price,r.gross_usd,r.slippage_usd,r.net_usd,r.initial_risk_usd,r.net_R],
                                   [expected,gross,slip,gross-5-slip,risk,(gross-5-slip)/risk],atol=1e-8)
        assert r.commission_usd==5
        np.testing.assert_allclose(abs(r.target_price-r.entry_price)*qty,risk*r.target_R,atol=1e-8)
        omitted=int((path.Timestamp.diff().dropna()/pd.Timedelta(minutes=1)-1).sum())
        assert omitted==r.omitted_minutes
        checked+=1
    return checked


def main():
    manifest=freeze()
    feed,spot,bars,fdata,sdata,directions,original,spec,quotes=load()
    f=entry_metrics(feed,bars,original,np.flatnonzero(original),spec)
    cached=pd.read_csv(H/"all_candidate_entry_metrics.csv")
    np.testing.assert_allclose(f.delta4_pct,cached.delta4_pct,atol=1e-10,equal_nan=True)
    np.testing.assert_allclose(f.delta24_pct,cached.delta24_pct,atol=1e-10,equal_nan=True)
    control,_=filtered_directions(directions,f,{"rules":["L_D4_POS","B_D24_BAND4"]})
    mirror=short_mirror(control,f)
    f["control_candidate_allowed"]=control[f.signal_index.to_numpy(dtype=int)]!=0
    f["mirror_candidate_allowed"]=mirror[f.signal_index.to_numpy(dtype=int)]!=0
    f.to_csv(OUT/"all_candidate_filter_evidence.csv",index=False)
    f.loc[f.direction.lt(0)].to_csv(OUT/"all_short_candidate_filter_evidence.csv",index=False)
    base=pd.read_csv(H/"selected_trade_ledger_usdc.csv")
    for c in ["decision_at","entry_at","exit_at","expiry_at"]:
        base[c]=pd.to_datetime(base[c],utc=True)
    summaries,ledgers={},{}
    checked=0
    for name,stream in [("CONTROL_40H",control),("SHORT_DELTA4_NEGATIVE",mirror)]:
        t=replay_hybrid(sdata,stream,spec["long"],spec["short"])
        if name=="CONTROL_40H":
            pd.testing.assert_frame_equal(t,base[t.columns],check_exact=False,rtol=1e-10,atol=1e-10)
        t["holding_hours"]=(t.exit_at-t.entry_at).dt.total_seconds()/3600
        t["signal_market"]="BTCUSDT_PERPETUAL_FUTURES"
        t["execution_market"]="BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL"
        t["quote_currency"]="USDC"
        t["quantity_btc"]=3000./t.entry_price
        t["notional_quote"]=3000.
        for c in ["basis_ratio","spot_close_at","futures_close_at"]:
            t[c]=[quotes[c].iloc[int(i)] for i in t.signal_index]
        fm=f.set_index("signal_index")
        t["delta4_pct"]=[fm.loc[int(i),"delta4_pct"] for i in t.signal_index]
        t["delta24_pct"]=[fm.loc[int(i),"delta24_pct"] for i in t.signal_index]
        t.to_csv(OUT/f'{name}_trade_ledger_usdc.csv',index=False)
        ledgers[name]=t
        closed=t.loc[~t.censored]
        core=t.loc[t.entry_at.between(pd.Timestamp("2026-04-01T00:00Z"),pd.Timestamp("2026-10-01T00:00Z"),inclusive="left")]
        summaries[name]={"variant":name,**metrics(t),"wins":int(closed.net_usd.gt(0).sum()),"losses":int(closed.net_usd.lt(0).sum()),
            "six_month_trades":len(core),"six_month_wins":int(core.net_usd.gt(0).sum()),"six_month_losses":int(core.net_usd.lt(0).sum()),
            "six_month_net_quote":metrics(core)["net_usd"],"six_month_censored":metrics(core)["censored"],
            "long_trades":int(t.direction.gt(0).sum()),"long_net_quote":closed.loc[closed.direction.gt(0),"net_usd"].sum(),
            "short_trades":int(t.direction.lt(0).sum()),"short_net_quote":closed.loc[closed.direction.lt(0),"net_usd"].sum(),
            "omitted_minutes":int(t.omitted_minutes.sum())}
        checked+=verify_path(t,spot,stream,quotes)
        print(json.dumps(summaries[name],indent=2),flush=True)
    a,changes=attribution(ledgers["CONTROL_40H"],ledgers["SHORT_DELTA4_NEGATIVE"],control,mirror,f)
    a.to_csv(OUT/"trade_attribution.csv",index=False)
    save("mirror_result.json",{**summaries["SHORT_DELTA4_NEGATIVE"],**changes})
    pd.DataFrame(summaries.values()).to_csv(OUT/"comparison.csv",index=False)
    # Full causal prefix reconstruction with inherited H4 state, not an outcome split.
    cutoff=pd.Timestamp("2026-07-22T17:30Z")
    pf=feed.loc[feed.Timestamp.le(cutoff)].copy()
    pb=features(pf)
    po=hybrid_signals(pb,spec["long"],spec["short"])
    pdirections=np.zeros_like(po)
    cmap,_=candidate_map(ReplayData(pf,pb),po,spec,{"short_space_1r":True},h4_inventory(pf,pb))
    for i,c in cmap.items():
        pdirections[i]=c["side"]
    pmetrics=entry_metrics(pf,pb,po,np.flatnonzero(po),spec)
    pcontrol,_=filtered_directions(pdirections,pmetrics,{"rules":["L_D4_POS","B_D24_BAND4"]})
    np.testing.assert_array_equal(pcontrol,control[:len(pb)])
    np.testing.assert_array_equal(short_mirror(pcontrol,pmetrics),mirror[:len(pb)])
    expected=f.loc[f.decision_at.le(cutoff)].reset_index(drop=True)
    pd.testing.assert_frame_equal(pmetrics.drop(columns="h4_regime"),expected[pmetrics.columns].drop(columns="h4_regime"))
    assert all(digest(ROOT/p)==sha for p,sha in manifest["preserved_hashes"].items())
    assert all(digest(OUT/p)==sha for p,sha in manifest["code_hashes"].items())
    save("verification.json",{"declared_variants":2,"baseline13rows_exactly_reproduced":True,"independent_trade_paths_checked":checked,
        "all_first_touches_cash_cost_risk_target_and_global_books_checked":True,"all_candidate_delta_metrics_match_frozen40H":True,
        "both_streams_and_metrics_real_prefix_invariant":True,"prefix_cutoff":cutoff,"all_inputs_and_selected40H_pointer_unchanged":True,
        "isolated_minutes_continue_with_actual_UTC":True,"all_market_state_reset_flags":False,"production_promoted":False})
    print('Attribution',json.dumps(changes,indent=2),flush=True)
    print(a.loc[a.status.ne("RETAINED")].to_string(index=False),flush=True)


if __name__=="__main__":
    main()
