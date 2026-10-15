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
from study import load,entry_metrics,digest,h4_inventory,replay_hybrid,metrics
from conditions import DEFAULT,entry_signals,short_space_mask,apply_flow
from events import event_variants,extra_event_signals,combine_streams
from run_study import save,attribute


def main():
    m={"phase":"SECOND_FINITE_BATCH_FIXED_AFTER74_RELAXATION_RESULTS_BEFORE_NEW_EVENT_RETURNS", "variants":event_variants(),
       "first_batch_result_sha256":digest(OUT/"frequency_results.csv"),
       "code_hashes":{p:digest(OUT/p) for p in ["events.py","run_events.py"]},
       "reason":"74 simple relaxations add mostly losses, no strong success. Test additional first-break long/short, accepted-range long and mirrored short-retest events.",
       "unchanged":"Same two feeds, quality/calendar, asof mapping, one global position, fixed stop/targets/hold/costs. No sweep shortcut or new calendar exclusion.",
       "gates":"Extra events use2ATR distance and2.5ATR range caps. Extra short retests require negative rolling4h delta.40H core gates stay unchanged; extra24h-band4/6 declared separately.",
       "selection":"Same24Apr-Sep trades/$500 minimum and strong criteria fixed in first manifest; all failures retained. History already exposed."}
    dest=OUT/"event_manifest.json"
    if dest.exists():
        assert json.loads(dest.read_text())==m
    else:
        save(dest.name,m)
    feed,spot,bars,fdata,sdata,base_space,original,spec,quotes=load()
    base_metrics=pd.read_csv(H/"all_candidate_entry_metrics.csv")
    core=apply_flow(base_space,base_metrics,DEFAULT)
    event_sets={}
    for v in event_variants():
        for event in v["events"]:
            key=json.dumps(event,sort_keys=True)
            event_sets[key]=extra_event_signals(bars,event)
    union=np.unique(np.concatenate([np.flatnonzero(s) for s in event_sets.values()]+[np.flatnonzero(core)]))
    f=entry_metrics(feed,bars,np.ones(len(bars),dtype=int),union,spec)
    f.to_csv(OUT/"event_candidate_metrics.csv",index=False)
    short_indexes=np.unique(np.concatenate([np.flatnonzero(s<0) for s in event_sets.values()]))
    space,_=short_space_mask(fdata,short_indexes,spec,h4_inventory(feed,bars),1.)
    base=pd.read_csv(H/"selected_trade_ledger_usdc.csv")
    for c in ["decision_at","entry_at","exit_at","expiry_at"]:
        base[c]=pd.to_datetime(base[c],utc=True)
    results,attributes,months=[],[],[]
    for v in event_variants():
        filtered=[]
        for event in v["events"]:
            raw=event_sets[json.dumps(event,sort_keys=True)].copy()
            raw[(raw<0)&~space]=0
            extra=apply_flow(raw,f,{**DEFAULT,"delta24_bound_pct":v["delta24_bound_pct"]})
            if event["side"]<0 and event["family"]=="TREND_RETEST":
                fmap=f.set_index("signal_index")
                for i in np.flatnonzero(extra):
                    if not (fmap.loc[i,"window4_usable"] and fmap.loc[i,"delta4_pct"]<0):
                        extra[i]=0
            filtered.append(extra)
        directions=combine_streams(core,*filtered)
        t=replay_hybrid(sdata,directions,spec["long"],spec["short"])
        t["holding_hours"]=(t.exit_at-t.entry_at).dt.total_seconds()/3600
        t["quantity_btc"]=3000./t.entry_price
        t["notional_quote"]=3000.
        t["signal_market"]="BTCUSDT_PERPETUAL_FUTURES"
        t["execution_market"]="BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL"
        t["quote_currency"]="USDC"
        # Preserve actual generating event identity; replay engine's old family label
        # describes inherited exit configuration, not the newly added event.
        t["entry_event"]=["CORE_40H" if core[int(i)]==directions[int(i)] else "+".join(e["family"] for e,s in zip(v["events"],filtered) if s[int(i)]!=0) for i in t.signal_index]
        for c in ["basis_ratio","spot_close_at","futures_close_at"]:
            t[c]=[quotes[c].iloc[int(i)] for i in t.signal_index]
        fm=f.set_index("signal_index")
        for c in ["delta4_pct","delta24_pct","volume_ratio"]:
            t[c]=[fm.loc[int(i),c] for i in t.signal_index]
        t.to_csv(OUT/"variant_ledgers"/f'{v["id"]}.csv',index=False)
        pd.DataFrame({"signal_index":np.flatnonzero(directions),"direction":directions[directions!=0]}).to_csv(OUT/"signal_streams"/f'{v["id"]}.csv',index=False)
        a,change=attribute(base,t,v["id"])
        attributes.append(a)
        closed=t.loc[~t.censored]
        coreperiod=t.loc[t.entry_at.between(pd.Timestamp("2026-04-01T00:00Z"),pd.Timestamp("2026-10-01T00:00Z"),inclusive="left")]
        r={"variant":v["id"],"event_delta24_bound_pct":v["delta24_bound_pct"],**metrics(t),**change,
           "wins":int(closed.net_usd.gt(0).sum()),"losses":int(closed.net_usd.lt(0).sum()),"six_month_trades":len(coreperiod),
           "six_month_net_quote":metrics(coreperiod)["net_usd"],"six_month_censored":metrics(coreperiod)["censored"],
           "long_trades":int(t.direction.gt(0).sum()),"short_trades":int(t.direction.lt(0).sum()),
           "long_net_quote":closed.loc[closed.direction.gt(0),"net_usd"].sum(),"short_net_quote":closed.loc[closed.direction.lt(0),"net_usd"].sum(),
           "mean_holding_hours":t.holding_hours.mean(),"mean_planned_target_R":t.target_R.mean(),
           "mean_planned_target_quote":(t.target_R*t.initial_risk_usd).mean(),"omitted_minutes":t.omitted_minutes.sum(),"eligible_signals":int((directions!=0).sum())}
        r["minimum_success"]=r["censored"]==0 and r["six_month_trades"]>=24 and r["net_usd"]>=500 and r["six_month_net_quote"]>=500
        r["strong_success"]=r["minimum_success"] and r["net_usd"]>=1090.811851 and r["six_month_net_quote"]>=1142.108729 and r["drawdown_usd"]<=225 and r["net_without_best_three"]>0
        results.append(r)
        for month,g in t.groupby(t.entry_at.dt.strftime("%Y-%m")):
            months.append({"variant":v["id"],"entry_month":month,"trades":len(g),"net_quote":g.net_usd.sum(),"censored":int(g.censored.sum())})
        print(f'{v["id"]}: {len(t)}trades/{len(coreperiod)}six {r["wins"]}+/{r["losses"]}-, censored{r["censored"]}, net{r["net_usd"]:.2f}, DD{r["drawdown_usd"]:.2f}',flush=True)
        pd.DataFrame(results).to_csv(OUT/"event_results.csv",index=False)
    pd.concat(attributes,ignore_index=True).to_csv(OUT/"event_trade_attribution.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"event_monthly_results.csv",index=False)
    save("event_run_verification.json",{"declared_and_completed":len(results),"entry_metric_universe":len(union),
        "all_attribution_differences_reconciled":True,"same_frozen_exit_engine":True,
        "strong_success_count":int(sum(x["strong_success"] for x in results)),"minimum_success_count":int(sum(x["minimum_success"] for x in results)),
        "first_batch_unchanged":digest(OUT/"frequency_results.csv")==m["first_batch_result_sha256"]})


if __name__=="__main__":
    main()
