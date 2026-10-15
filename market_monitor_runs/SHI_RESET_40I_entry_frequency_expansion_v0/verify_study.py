"""All-portfolio accounting, independent unique fills and causal-prefix verification."""
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
from study import load,digest,features,entry_metrics,ReplayData,h4_inventory,metrics,G
from conditions import variants,DEFAULT,entry_signals,short_space_mask,apply_flow
from events import event_variants,extra_event_signals,combine_streams
from run_combinations import combinations,build_directions
from run_study import save


def all_streams(b,fd,inventory,f,spec):
    streams={}
    for v in variants():
        p=v["parameters"]
        raw=entry_signals(b,p)
        space,_=short_space_mask(fd,np.flatnonzero(raw<0),spec,inventory,p["short_space_r"])
        raw[(raw<0)&~space]=0
        streams[v["id"]]=apply_flow(raw,f,p)
    core=streams["BASELINE_40H"]
    fm=f.set_index("signal_index")
    for v in event_variants():
        extra=[]
        for e in v["events"]:
            raw=extra_event_signals(b,e)
            space,_=short_space_mask(fd,np.flatnonzero(raw<0),spec,inventory,1.)
            raw[(raw<0)&~space]=0
            s=apply_flow(raw,f,{**DEFAULT,"delta24_bound_pct":v["delta24_bound_pct"]})
            if e["side"]<0 and e["family"]=="TREND_RETEST":
                for i in np.flatnonzero(s):
                    if not(fm.loc[i,"window4_usable"] and fm.loc[i,"delta4_pct"]<0):
                        s[i]=0
            extra.append(s)
        streams[v["id"]]=combine_streams(core,*extra)
    for v in combinations():
        streams[v["id"]]=build_directions(v,b,fd,spec,inventory,f)[0]
    return streams


def main():
    feed,spot,bars,fdata,sdata,_,_,spec,quotes=load()
    stored=pd.concat([pd.read_csv(OUT/"candidate_entry_metrics.csv"),pd.read_csv(OUT/"event_candidate_metrics.csv")],ignore_index=True)
    for _,g in stored.groupby("signal_index"):
        if len(g)>1:
            np.testing.assert_allclose(g.delta24_pct,g.delta24_pct.iloc[0],atol=1e-10)
            np.testing.assert_allclose(g.delta4_pct,g.delta4_pct.iloc[0],atol=1e-10)
    stored=stored.drop_duplicates("signal_index").sort_values("signal_index").reset_index(drop=True)
    f=entry_metrics(feed,bars,np.ones(len(bars),dtype=int),stored.signal_index.to_numpy(),spec)
    np.testing.assert_allclose(f.delta24_pct,stored.delta24_pct,atol=1e-10,equal_nan=True)
    np.testing.assert_allclose(f.delta4_pct,stored.delta4_pct,atol=1e-10,equal_nan=True)
    cutoff=pd.Timestamp("2026-08-20T23:59Z")
    prefix_feed=feed.loc[feed.Timestamp.le(cutoff)].copy()
    pb=features(prefix_feed)
    pf=entry_metrics(prefix_feed,pb,np.ones(len(pb),dtype=int),f.loc[f.decision_at.le(cutoff),"signal_index"].to_numpy(),spec)
    pd.testing.assert_frame_equal(pf.drop(columns="h4_regime"),f.loc[f.decision_at.le(cutoff)].reset_index(drop=True).drop(columns="h4_regime"))
    full=all_streams(bars,fdata,h4_inventory(feed,bars),f,spec)
    prefix=all_streams(pb,ReplayData(prefix_feed,pb),h4_inventory(prefix_feed,pb),pf,spec)
    assert len(full)==130 and set(full)==set(prefix)
    for name,d in full.items():
        np.testing.assert_array_equal(prefix[name],d[:len(pb)])
        saved=pd.read_csv(OUT/"signal_streams"/f'{name}.csv')
        if "flow_allowed" in saved:
            saved=saved.loc[saved.flow_allowed]
        expected=np.zeros(len(bars),dtype=int)
        expected[saved.signal_index.to_numpy(dtype=int)]=saved.direction.to_numpy(dtype=int)
        np.testing.assert_array_equal(d,expected)
    print('All130 complete signal streams and new entry metrics prefix-invariant, no future changes',flush=True)
    unique,paths,omissions={},0,0
    for name,directions in full.items():
        t=pd.read_csv(OUT/"variant_ledgers"/f'{name}.csv')
        for c in ["decision_at","entry_at","exit_at","expiry_at","spot_close_at","futures_close_at"]:
            t[c]=pd.to_datetime(t[c],utc=True)
        previous=None
        for r in t.itertuples():
            assert not r.censored and directions[r.signal_index]==r.direction
            if previous is not None:
                assert r.entry_at>previous+pd.Timedelta(minutes=3)
            previous=r.exit_at
            assert r.spot_close_at<=r.decision_at and r.futures_close_at<=r.decision_at<r.entry_at
            assert r.decision_at-r.spot_close_at<=pd.Timedelta(minutes=1)
            assert r.decision_at-r.futures_close_at<=pd.Timedelta(minutes=1)
            np.testing.assert_allclose(r.basis_ratio,quotes.basis_ratio.iloc[r.signal_index],atol=1e-12)
            key=(r.signal_index,r.direction)
            numeric=np.array([r.entry_price,r.stop_price,r.target_price,r.exit_price,r.net_usd,r.initial_risk_usd])
            if key in unique:
                np.testing.assert_allclose(numeric,unique[key],atol=1e-8)
            else:
                unique[key]=numeric
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
                np.testing.assert_allclose(r.exit_price,expected,atol=1e-8)
                skipped=int((path.Timestamp.diff().dropna()/pd.Timedelta(minutes=1)-1).sum())
                assert skipped==r.omitted_minutes
            qty=3000/r.entry_price
            gross=r.direction*(r.exit_price-r.entry_price)*qty
            slip=(r.entry_price+r.exit_price)*qty*.0002
            risk=abs(r.entry_price-r.stop_price)*qty
            np.testing.assert_allclose([r.gross_usd,r.slippage_usd,r.net_usd,r.initial_risk_usd,r.net_R],
                                       [gross,slip,gross-5-slip,risk,(gross-5-slip)/risk],atol=1e-8)
            assert r.commission_usd==5 and .004<=risk/3000<=.04
            np.testing.assert_allclose(abs(r.target_price-r.entry_price)*qty,r.target_R*risk,atol=1e-8)
            paths+=1
            omissions+=r.omitted_minutes
    results=pd.concat([pd.read_csv(OUT/p) for p in ["frequency_results.csv","event_results.csv","combination_results.csv"]],ignore_index=True)
    assert len(results)==130 and results.censored.sum()==0
    save("independent_verification.json",{"portfolios":130,"trade_paths_accounted":paths,"independent_unique_first_touch_paths":len(unique),
         "all_unique_first_stop_target_expiry_touches_verified":True,"all_duplicate_entry_paths_match":True,
         "every_cash_fee_slippage_risk_R_and_target_verified":True,"every_global_book_and_known_basis_verified":True,
         "all130_signal_streams_and_metrics_real_prefix_invariant":True,"prefix_cutoff":cutoff,
         "all_outcomes_observed_no_censor_or_inferred_gap_fill":True,"isolated_omissions_all_portfolio_rows":int(omissions),
         "full_control_source_identity_reverified_by_original_loader":True,"primary_40H_is_preserved":True})
    selected="JOINT_PAIR48_V13_B6_SPACE075"
    alt=pd.read_csv(OUT/"variant_ledgers"/f'{selected}.csv')
    alt["trade_id"]=[f'40I-{int(i)}-{int(s)}' for i,s in zip(alt.signal_index,alt.direction)]
    alt["actual_borrowing_in_net"]=False
    alt.to_csv(OUT/"frequency_alternative_trade_ledger_usdc.csv",index=False)
    selected_result=results.set_index("variant").loc[selected].dropna().to_dict()
    save("frequency_alternative_result.json",selected_result)
    all_attribution=pd.concat([pd.read_csv(OUT/p) for p in ["all_trade_attribution.csv","event_trade_attribution.csv","combination_trade_attribution.csv"]],ignore_index=True)
    all_attribution.loc[all_attribution.variant.eq(selected)].to_csv(OUT/"frequency_alternative_attribution.csv",index=False)
    comparisons=[]
    for name in ["BASELINE_40H",selected,"JOINT_PAIR48_V11_B6_SPACE075","L_FLOW02_VOL11_S_LB24_VOL11_B6_F-1"]:
        t=pd.read_csv(OUT/"variant_ledgers"/f'{name}.csv')
        for c in ["entry_at","exit_at"]:
            t[c]=pd.to_datetime(t[c],utc=True)
        core=t.loc[t.entry_at.between(pd.Timestamp("2026-04-01T00:00Z"),pd.Timestamp("2026-10-01T00:00Z"),inclusive="left")]
        comparisons.append({"variant":name,"full_trades":len(t),"full_net_quote":t.net_usd.sum(),"six_month_trades":len(core),
            "six_month_wins":int(core.net_usd.gt(0).sum()),"six_month_losses":int(core.net_usd.lt(0).sum()),
            "six_month_net_quote":core.net_usd.sum(),"six_month_drawdown_quote":metrics(core)["drawdown_usd"],
            "full_drawdown_quote":metrics(t)["drawdown_usd"],"six_month_mean_net_quote":core.net_usd.mean()})
    pd.DataFrame(comparisons).to_csv(OUT/"user_comparison.csv",index=False)
    save("frequency_alternative_contract.json",{"version":"SHI_RESET_40I_FREQUENCY_ALTERNATIVE_V1","selected_variant":selected,
         "baseline_contract_sha256":digest(H/"selected_research_contract.json"),"baseline_control_remains":"40H",
         "selection_status":"Frequency/cash tradeoff alternative; original strong24-trade criterion unmet, not silently relaxed.",
         "original_40H_rules":"Core delta24 strict(-4%,+4%); longdelta4>0; oldfamilies/quality/exits unchanged except shortspace0.75R.",
         "additional_entries":"First newly closed break of prior48H1 high/low; repeated same-episode break signals suppressed; long EMAtrend, short negative24h price/delta pressure; directional H1delta>=4%, volume>=1.3prior-median; distanceEMA24<=2ATR, range<=2.5ATR; longdelta4>0, extra |delta24|<6%; shortspace>=0.75R when known opposing reference exists.",
         "conflicts":"Opposite candidates at same H1 suppressed before replay; core and extra same-side merged; one global book/cooldown3min.",
         "source_preparation":spec["source_preparation"],"spot_csv_sha256":digest(G/"spot_BTCUSDC/spot_minutes.csv"),
         "signal_market":"BTCUSDT_PERPETUAL_FUTURES","execution_market":"BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL",
         "notional_quote":3000,"fee_per_completed_trade_quote":5,"slippage_bps_per_fill":2,
         "exit_rules":{"long":spec["long"]["exit"],"short":spec["short"]["exit"]},
         "study_manifest_sha256":digest(OUT/"study_manifest.json"),"event_manifest_sha256":digest(OUT/"event_manifest.json"),
         "combination_manifest_sha256":digest(OUT/"combination_manifest.json"),"code_sha256":{n:digest(OUT/n) for n in ["conditions.py","events.py","run_combinations.py"]},
         "history_selected":True,"pristine_holdout":False,"production_promoted":False,"actual_borrowing_in_net":False,
         "market_state_reset":False,"structure_levels_reset":False,"liquidity_zones_reset":False,"qualified_h1_state_reset":False,"setup_context_reset":False,
         "continuity_scope":"Original history/features/causal H4 inventory carried forward. No claim of implementing the full Monitor lifecycle."})
    manifest=json.loads((OUT/"study_manifest.json").read_text())
    assert all(digest(ROOT/p)==sha for p,sha in manifest["preserved_40H_hashes"].items())
    assert all(digest(OUT/p)==sha for p,sha in manifest["code_hashes"].items())
    em=json.loads((OUT/"event_manifest.json").read_text())
    assert all(digest(OUT/p)==sha for p,sha in em["code_hashes"].items())
    cm=json.loads((OUT/"combination_manifest.json").read_text())
    assert digest(OUT/"run_combinations.py")==cm["code_sha256"]
    save("final_source_code_identity.json",{"all47_40H_artifacts_and_original_inputs_unchanged":True,"all_three_batch_rule_code_hashes_unchanged":True,
         "total_variants":130,"strong_success_count":int(results.strong_success.sum()),"minimum_success_count":int(results.minimum_success.sum()),
         "selected_alternative_has_no_lost_baseline_winners":selected_result["lost_baseline_wins"]==0})
    print(json.dumps(json.loads((OUT/"independent_verification.json").read_text()),indent=2),flush=True)
    print(pd.DataFrame(comparisons).to_string(index=False),flush=True)


if __name__=="__main__":
    main()
