from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
H=ROOT/"market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(H))
sys.path.insert(0,str(OUT))
from study import load, entry_metrics, digest, h4_inventory, hybrid_signals, replay_hybrid, metrics, G
from conditions import variants, DEFAULT, entry_signals, long_components, short_space_mask, apply_flow


def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,default=str,allow_nan=False)+"\n",encoding="utf-8")


def freeze():
    prior=json.loads((H/"artifact_hashes.json").read_text())
    assert all(digest(H/p)==sha for p,sha in prior.items())
    paths=[H/p for p in prior]+[H/"artifact_hashes.json"]
    m={"task":"SHI_RESET_40I_ENTRY_FREQUENCY_EXPANSION","phase":"FINITE_SCOPE_FIXED_BEFORE_NEW_FINANCIAL_RETURNS",
       "variants":variants(),"variant_count":len(variants()),
       "code_hashes":{name:digest(OUT/name) for name in ["conditions.py","run_study.py"]},
       "preserved_40H_hashes":{p.relative_to(ROOT).as_posix():digest(p) for p in paths},
       "baseline":"40H13trades/+1090.811851USDC;12April-September/+1142.108729",
       "objective":"More executable trades in same frozen history; not raw candidate count or overlapping positions.",
       "bounds":"Long delta1 min4/2/0%, volume1.3/1.1/1.0, retest tolerance0/.15/.30ATR, maturity1.5/2ATR, impulse2/2.5ATR; short volume1.3/1.1/1.0, accepted-break24/48h, H4 space1/.75R; delta24 band4/6%, longdelta4 floor0/-1%.",
       "unchanged":["full prior history; no reset","same quality/calendar/exclusions/isolated-minute handling", "two acceptance closes for short",
                    "EMA trend test for long; negative24h price/flow short", "same spot mapping/entry latency/one global book/cooldown",
                    "3000USDC notional,5USDC total fee,2bps/fill slip", "6H stop anchors/ATR floors/6R-short/10R-long/168h expiry"],
       "selection":{"frequency_goal_six_month_trades":24,"minimum_full_and_six_month_net_quote":500,
                    "strong_success":"at least24Apr-Sep trades; fullnet>=1090.811851, sixnet>=1142.108729, closedDD<=225, no censor, withoutbest3>0",
                    "fallback":"Retain Pareto frontier/tradeoffs. Do not silently lower strong criterion or replace40H if unmet.",
                    "ranking":"Among strong successes, highest six-month net; ties prefer fewer changed parameters. Show frequency/cash/risk tradeoffs."},
       "pristine_holdout":False,"actual_borrowing_or_orderbook_validated":False,"production_promoted":False}
    path=OUT/"study_manifest.json"
    if path.exists():
        assert json.loads(path.read_text())==m
    else:
        save(path.name,m)
    return m


def attribute(baseline,current,variant):
    old=baseline.set_index("signal_index")
    new=current.set_index("signal_index")
    rows=[]
    for i,r in old.iterrows():
        keep=i in new.index
        if keep:
            np.testing.assert_allclose(r.net_usd,new.loc[i,"net_usd"],atol=1e-8)
        rows.append({"variant":variant,"signal_index":i,"direction":r.direction,"entry_at":r.entry_at,
                     "status":"RETAINED" if keep else "LOST_BASELINE_ENTRY","baseline_net_quote":r.net_usd,
                     "current_net_quote":new.loc[i,"net_usd"] if keep else np.nan})
    for i,r in new.loc[~new.index.isin(old.index)].iterrows():
        rows.append({"variant":variant,"signal_index":i,"direction":r.direction,"entry_at":r.entry_at,
                     "status":"NEWLY_ADMITTED","baseline_net_quote":np.nan,"current_net_quote":r.net_usd})
    a=pd.DataFrame(rows)
    lost=a.loc[a.status.eq("LOST_BASELINE_ENTRY")]
    added=a.loc[a.status.eq("NEWLY_ADMITTED")]
    delta=current.net_usd.sum()-baseline.net_usd.sum()
    np.testing.assert_allclose(delta,added.current_net_quote.sum()-lost.baseline_net_quote.sum(),atol=1e-8)
    return a,{"lost_baseline_wins":int(lost.baseline_net_quote.gt(0).sum()),"lost_baseline_win_quote":lost.loc[lost.baseline_net_quote.gt(0),"baseline_net_quote"].sum(),
              "lost_baseline_losses":int(lost.baseline_net_quote.lt(0).sum()),"saved_baseline_losses_quote":-lost.loc[lost.baseline_net_quote.lt(0),"baseline_net_quote"].sum(),
              "new_trades":len(added),"new_wins":int(added.current_net_quote.gt(0).sum()),"new_losses":int(added.current_net_quote.lt(0).sum()),
              "new_trade_net_quote":added.current_net_quote.sum(),"net_change_quote":delta}


def main():
    manifest=freeze()
    feed,spot,bars,fdata,sdata,base_space,original,spec,quotes=load()
    signal_sets={v["id"]:entry_signals(bars,v["parameters"]) for v in variants()}
    np.testing.assert_array_equal(signal_sets["BASELINE_40H"],original)
    universe=np.unique(np.concatenate([np.flatnonzero(s) for s in signal_sets.values()]))
    # Metrics are independent of candidate side: signed diagnostics use a fixed+1;
    # gating only uses unsigned raw delta4/24. Each variant supplies its direction.
    universe_metrics=entry_metrics(feed,bars,np.ones(len(bars),dtype=int),universe,spec)
    universe_metrics.to_csv(OUT/"candidate_entry_metrics.csv",index=False)
    quotes.to_csv(OUT/"decision_basis_quotes.csv",index=False)
    inventory=h4_inventory(feed,bars)
    short_indexes=np.unique(np.concatenate([np.flatnonzero(s<0) for s in signal_sets.values()]))
    masks,space_rows={},[]
    for threshold in [1.,.75]:
        masks[threshold],rows=short_space_mask(fdata,short_indexes,spec,inventory,threshold)
        space_rows+=rows
    pd.DataFrame(space_rows).to_csv(OUT/"short_h4_space.csv",index=False)
    print(f'{len(variants())} variants frozen, union{len(universe)} candidate decisions prepared',flush=True)
    base=pd.read_csv(H/"selected_trade_ledger_usdc.csv")
    for c in ["decision_at","entry_at","exit_at","expiry_at"]:
        base[c]=pd.to_datetime(base[c],utc=True)
    results,attributes,months,funnels=[],[],[],[]
    ledgers=OUT/"variant_ledgers"
    streams=OUT/"signal_streams"
    ledgers.mkdir(exist_ok=True)
    streams.mkdir(exist_ok=True)
    for v in variants():
        p=v["parameters"]
        raw=signal_sets[v["id"]]
        spaced=raw.copy()
        spaced[(raw<0)&~masks[p["short_space_r"]]]=0
        filtered=apply_flow(spaced,universe_metrics,p)
        pd.DataFrame({"signal_index":np.flatnonzero(raw),"direction":raw[raw!=0],
                      "short_space_allowed":spaced[raw!=0]!=0,"flow_allowed":filtered[raw!=0]!=0}).to_csv(streams/f'{v["id"]}.csv',index=False)
        t=replay_hybrid(sdata,filtered,spec["long"],spec["short"])
        if v["id"]=="BASELINE_40H":
            pd.testing.assert_frame_equal(t,base[t.columns],check_exact=False,rtol=1e-10,atol=1e-10)
        if v["id"]=="DELTA24_BAND6":
            old=pd.read_csv(H/"variant_ledgers/LONG_DELTA4_POS_BOTH_BAND6.csv")
            for c in ["decision_at","entry_at","exit_at","expiry_at"]:
                old[c]=pd.to_datetime(old[c],utc=True)
            pd.testing.assert_frame_equal(t,old[t.columns],check_exact=False,rtol=1e-10,atol=1e-10)
        t["holding_hours"]=(t.exit_at-t.entry_at).dt.total_seconds()/3600
        t["notional_quote"]=3000.
        t["quantity_btc"]=3000./t.entry_price
        t["signal_market"]="BTCUSDT_PERPETUAL_FUTURES"
        t["execution_market"]="BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL"
        t["quote_currency"]="USDC"
        for col in ["basis_ratio","spot_close_at","futures_close_at"]:
            t[col]=[quotes[col].iloc[int(i)] for i in t.signal_index]
        for col in ["delta4_pct","delta24_pct","volume_ratio"]:
            f=universe_metrics.set_index("signal_index")
            t[col]=[f.loc[int(i),col] for i in t.signal_index]
        t.to_csv(ledgers/f'{v["id"]}.csv',index=False)
        a,changes=attribute(base,t,v["id"])
        attributes.append(a)
        closed=t.loc[~t.censored]
        core=t.loc[t.entry_at.between(pd.Timestamp("2026-04-01T00:00Z"),pd.Timestamp("2026-10-01T00:00Z"),inclusive="left")]
        # Reconstruct book occupancy from accepted rows, without another fill engine.
        accepted=t.set_index("signal_index")
        busy=-1
        counts={"busy":0,"entry_unavailable_or_risk_invalid":0}
        for i in np.flatnonzero(filtered):
            if sdata.available[i]+sdata.minute<=busy:
                counts["busy"]+=1
                assert i not in accepted.index
            elif i in accepted.index:
                row=accepted.loc[i]
                busy=(row.expiry_at if row.censored else row.exit_at).value+3*sdata.minute
            else:
                counts["entry_unavailable_or_risk_invalid"]+=1
        components=long_components(bars,p)
        cum=np.ones(len(bars),dtype=bool)
        funnel={"variant":v["id"]}
        for name,mask in components.items():
            cum &=mask.to_numpy()
            funnel[name]=int(cum.sum())
        funnel.update({"raw_long":int((raw>0).sum()),"raw_short":int((raw<0).sum()),"post_space":int((spaced!=0).sum()),
                       "post_delta":int((filtered!=0).sum()),"accepted":len(t),**counts})
        funnels.append(funnel)
        result={"variant":v["id"],"changed_parameters":v["changed_parameters"],**p,**metrics(t),**changes,
                "wins":int(closed.net_usd.gt(0).sum()),"losses":int(closed.net_usd.lt(0).sum()),
                "six_month_trades":len(core),"six_month_net_quote":metrics(core)["net_usd"],"six_month_censored":metrics(core)["censored"],
                "long_trades":int(t.direction.gt(0).sum()),"short_trades":int(t.direction.lt(0).sum()),
                "long_net_quote":closed.loc[closed.direction.gt(0),"net_usd"].sum(),"short_net_quote":closed.loc[closed.direction.lt(0),"net_usd"].sum(),
                "mean_holding_hours":t.holding_hours.mean(),"mean_planned_target_R":t.target_R.mean(),
                "mean_planned_target_quote":(t.target_R*t.initial_risk_usd).mean(),"omitted_minutes":t.omitted_minutes.sum(),
                "raw_signals":int((raw!=0).sum()),"eligible_signals":int((filtered!=0).sum()),"busy_signals":counts["busy"]}
        result["minimum_success"]=(result["censored"]==0 and result["six_month_trades"]>=24 and result["net_usd"]>=500 and result["six_month_net_quote"]>=500)
        result["strong_success"]=(result["minimum_success"] and result["net_usd"]>=1090.811851 and result["six_month_net_quote"]>=1142.108729 and result["drawdown_usd"]<=225 and result["net_without_best_three"]>0)
        results.append(result)
        for month,g in t.groupby(t.entry_at.dt.strftime("%Y-%m")):
            months.append({"variant":v["id"],"entry_month":month,"trades":len(g),"net_quote":g.net_usd.sum(),"censored":int(g.censored.sum())})
        print(f'{v["id"]}: {len(t)} trades/{len(core)}six, {result["wins"]}+/{result["losses"]}-, censored{result["censored"]}, net{result["net_usd"]:.2f}, DD{result["drawdown_usd"]:.2f}',flush=True)
        pd.DataFrame(results).to_csv(OUT/"frequency_results.csv",index=False)
    pd.concat(attributes,ignore_index=True).to_csv(OUT/"all_trade_attribution.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"monthly_results.csv",index=False)
    pd.DataFrame(funnels).to_csv(OUT/"entry_funnels.csv",index=False)
    r=pd.DataFrame(results)
    strong=r.loc[r.strong_success].sort_values(["six_month_net_quote","changed_parameters"],ascending=[False,True])
    frontier=[]
    valid=r.loc[r.censored.eq(0)&r.minimum_success]
    for i,row in valid.iterrows():
        dominated=((valid.six_month_trades>=row.six_month_trades)&(valid.six_month_net_quote>=row.six_month_net_quote)&
                   ((valid.six_month_trades>row.six_month_trades)|(valid.six_month_net_quote>row.six_month_net_quote))).any()
        if not dominated:
            frontier.append(row.to_dict())
    pd.DataFrame(frontier).to_csv(OUT/"frequency_cash_frontier.csv",index=False)
    save("run_verification.json",{"variants_declared_and_completed":len(results),"union_candidate_decisions":len(universe),
         "baseline_40H_exactly_reproduced":True,"40H_band6_sensitivity_exactly_reproduced":True,
         "all_attribution_dollar_differences_reconciled":True,"unchanged_exit_engine":True,
         "all_original_40H_artifacts_unchanged":all(digest(ROOT/p)==sha for p,sha in manifest["preserved_40H_hashes"].items()),
         "strong_success_count":len(strong),"minimum_success_count":int(r.minimum_success.sum()),
         "selected_frequency_variant":strong.iloc[0].variant if len(strong) else None})
    print('Strong successes',len(strong),'minimum frequency/cash successes',int(r.minimum_success.sum()),flush=True)


if __name__=="__main__":
    main()
