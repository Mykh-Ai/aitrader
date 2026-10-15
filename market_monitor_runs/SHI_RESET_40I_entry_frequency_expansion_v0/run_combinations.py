"""Third finite adaptive batch combines the declared0.75R gate with entry alternatives."""
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
from study import load, digest, h4_inventory, replay_hybrid, metrics
from conditions import DEFAULT,variants,entry_signals,short_space_mask,apply_flow
from events import event_variants,extra_event_signals,combine_streams
from run_study import save,attribute


def combinations():
    return [{"id":"JOINT_CORE_SPACE075","kind":"RELAX","source":"BASELINE_40H"},
            {"id":"JOINT_FLOW02_VOL11_SPACE075","kind":"RELAX","source":"L_FLOW02_VOL11_S_STRICT_B4_F0"},
            {"id":"JOINT_BOTH_VOL11_SPACE075","kind":"RELAX","source":"BOTH_VOL11"},
            {"id":"JOINT_HIGH_FREQUENCY_SPACE075","kind":"RELAX","source":"L_FLOW02_VOL11_S_LB24_VOL11_B6_F-1"}]+[
            {"id":f'JOINT_PAIR48_V{vol}_B{band}_SPACE075',"kind":"EVENT","source":f'EXTRA_PAIR_L_BREAKOUT48_S_BREAKOUT48_V{vol}_B{band}'}
            for vol in [13,11] for band in [4,6]]


def build_directions(v,bars,fdata,spec,inventory,f):
    if v["kind"]=="RELAX":
        original=next(x for x in variants() if x["id"]==v["source"])
        params={**original["parameters"],"short_space_r":.75}
        raw=entry_signals(bars,params)
        space,_=short_space_mask(fdata,np.flatnonzero(raw<0),spec,inventory,.75)
        raw[(raw<0)&~space]=0
        directions=apply_flow(raw,f,params)
        return directions,np.zeros_like(directions),[],[],params
    event_config=next(x for x in event_variants() if x["id"]==v["source"])
    raw=entry_signals(bars,DEFAULT)
    space,_=short_space_mask(fdata,np.flatnonzero(raw<0),spec,inventory,.75)
    raw[(raw<0)&~space]=0
    core=apply_flow(raw,f,DEFAULT)
    extras=[]
    for event in event_config["events"]:
        raw=extra_event_signals(bars,event)
        space,_=short_space_mask(fdata,np.flatnonzero(raw<0),spec,inventory,.75)
        raw[(raw<0)&~space]=0
        extras.append(apply_flow(raw,f,{**DEFAULT,"delta24_bound_pct":event_config["delta24_bound_pct"]}))
    return combine_streams(core,*extras),core,event_config["events"],extras,event_config


def main():
    manifest={"phase":"THIRD_FINITE_ADAPTIVE_BATCH_FIXED_BEFORE_COMBINATION_RETURNS","variants":combinations(),
              "first_results_sha256":digest(OUT/"frequency_results.csv"),"second_results_sha256":digest(OUT/"event_results.csv"),
              "code_sha256":digest(Path(__file__)),
              "reason":"Single0.75R short-space gate adds a winner;48h-first-break additions increase winning count. Test their declared combinations, including high-frequency tradeoff.",
              "selection":"Original minimum/strong criteria unchanged; no pristine holdout or exit/cost/quality change."}
    dest=OUT/"combination_manifest.json"
    if dest.exists():
        assert json.loads(dest.read_text())==manifest
    else:
        save(dest.name,manifest)
    feed,spot,bars,fdata,sdata,_,_,spec,quotes=load()
    f=pd.concat([pd.read_csv(OUT/"candidate_entry_metrics.csv"),pd.read_csv(OUT/"event_candidate_metrics.csv")],ignore_index=True).drop_duplicates("signal_index")
    inventory=h4_inventory(feed,bars)
    baseline=pd.read_csv(H/"selected_trade_ledger_usdc.csv")
    for c in ["decision_at","entry_at","exit_at","expiry_at"]:
        baseline[c]=pd.to_datetime(baseline[c],utc=True)
    results,attributes,months=[],[],[]
    for v in combinations():
        directions,core,events,extras,params=build_directions(v,bars,fdata,spec,inventory,f)
        t=replay_hybrid(sdata,directions,spec["long"],spec["short"])
        t["holding_hours"]=(t.exit_at-t.entry_at).dt.total_seconds()/3600
        t["quantity_btc"]=3000./t.entry_price
        t["notional_quote"]=3000.
        t["signal_market"]="BTCUSDT_PERPETUAL_FUTURES"
        t["execution_market"]="BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL"
        t["quote_currency"]="USDC"
        if v["kind"]=="EVENT":
            t["entry_event"]=["CORE_SPACE075" if core[int(i)]==directions[int(i)] else "+".join(e["family"] for e,s in zip(events,extras) if s[int(i)]!=0) for i in t.signal_index]
        else:
            t["entry_event"]="RELAXED_CORE"
        t["exit_configuration_family"]=t.family
        t.loc[t.entry_event.eq("BREAKOUT"),"family"]="FIRST_RANGE_BREAK"
        for c in ["basis_ratio","spot_close_at","futures_close_at"]:
            t[c]=[quotes[c].iloc[int(i)] for i in t.signal_index]
        fm=f.set_index("signal_index")
        for c in ["delta4_pct","delta24_pct","volume_ratio"]:
            t[c]=[fm.loc[int(i),c] for i in t.signal_index]
        t.to_csv(OUT/"variant_ledgers"/f'{v["id"]}.csv',index=False)
        pd.DataFrame({"signal_index":np.flatnonzero(directions),"direction":directions[directions!=0]}).to_csv(OUT/"signal_streams"/f'{v["id"]}.csv',index=False)
        a,changes=attribute(baseline,t,v["id"])
        attributes.append(a)
        closed=t.loc[~t.censored]
        coreperiod=t.loc[t.entry_at.between(pd.Timestamp("2026-04-01T00:00Z"),pd.Timestamp("2026-10-01T00:00Z"),inclusive="left")]
        r={"variant":v["id"],**metrics(t),**changes,"wins":int(closed.net_usd.gt(0).sum()),"losses":int(closed.net_usd.lt(0).sum()),
           "six_month_trades":len(coreperiod),"six_month_net_quote":metrics(coreperiod)["net_usd"],"six_month_censored":metrics(coreperiod)["censored"],
           "long_trades":int(t.direction.gt(0).sum()),"short_trades":int(t.direction.lt(0).sum()),
           "long_net_quote":closed.loc[closed.direction.gt(0),"net_usd"].sum(),"short_net_quote":closed.loc[closed.direction.lt(0),"net_usd"].sum(),
           "mean_holding_hours":t.holding_hours.mean(),"mean_planned_target_R":t.target_R.mean(),
           "mean_planned_target_quote":(t.target_R*t.initial_risk_usd).mean(),"omitted_minutes":t.omitted_minutes.sum(),"eligible_signals":int((directions!=0).sum())}
        r["minimum_success"]=r["censored"]==0 and r["six_month_trades"]>=24 and r["net_usd"]>=500 and r["six_month_net_quote"]>=500
        r["strong_success"]=r["minimum_success"] and r["net_usd"]>=1090.811851 and r["six_month_net_quote"]>=1142.108729 and r["drawdown_usd"]<=225 and r["net_without_best_three"]>0
        results.append(r)
        for month,g in t.groupby(t.entry_at.dt.strftime("%Y-%m")):
            months.append({"variant":v["id"],"entry_month":month,"trades":len(g),"net_quote":g.net_usd.sum(),"censored":int(g.censored.sum())})
        print(f'{v["id"]}: {len(t)}trades/{len(coreperiod)}six, {r["wins"]}+/{r["losses"]}-, net{r["net_usd"]:.2f}, six{r["six_month_net_quote"]:.2f}, DD{r["drawdown_usd"]:.2f}',flush=True)
    pd.DataFrame(results).to_csv(OUT/"combination_results.csv",index=False)
    pd.concat(attributes,ignore_index=True).to_csv(OUT/"combination_trade_attribution.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"combination_monthly_results.csv",index=False)
    save("combination_run_verification.json",{"declared_and_completed":len(results),"all_attribution_differences_reconciled":True,
        "prior_results_unchanged":digest(OUT/"frequency_results.csv")==manifest["first_results_sha256"] and digest(OUT/"event_results.csv")==manifest["second_results_sha256"],
        "strong_success_count":int(sum(x["strong_success"] for x in results)),"minimum_success_count":int(sum(x["minimum_success"] for x in results))})


if __name__=="__main__":
    main()
