"""Independent fixed-exit path/cash checks, real-history prefix and freeze."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from study import ROOT, G, F, save, digest, load, entry_metrics, features, ReplayData, ExitRules, initial_stop, h4_inventory, candidate_map, hybrid_signals
from filters import VARIANTS, filtered_directions


def write_selected_lineage(selected, quotes):
    """Attach independently known prices/metrics without changing replay fields."""
    fields=["delta4_pct","delta24_pct","oi24_pct","volume_ratio","entry_4h_utc","entry_4h_budapest"]
    f=pd.read_csv(OUT / "all_candidate_entry_metrics.csv").set_index("signal_index")
    t=selected.copy()
    t["signal_market"]="BTCUSDT_PERPETUAL_FUTURES"
    t["execution_market"]="BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL"
    t["quote_currency"]="USDC"
    t["notional_quote"]=3000.
    t["quantity_btc"]=3000./t.entry_price
    t["actual_borrowing_in_net"]=False
    for col in ["basis_ratio","spot_close_at","futures_close_at"]:
        t[col+"_at_decision" if col=="basis_ratio" else col]=[quotes[col].iloc[int(i)] for i in t.signal_index]
    for col in fields:
        t[col]=[f.loc[int(i),col] for i in t.signal_index]
    decisions=pd.to_datetime(t.decision_at,utc=True)
    for col in ["spot_close_at","futures_close_at"]:
        known=pd.to_datetime(t[col],utc=True)
        assert (known<=decisions).all() and ((decisions-known)<=pd.Timedelta(minutes=1)).all()
    assert t.delta24_pct.abs().lt(4).all() and t.loc[t.direction.gt(0),"delta4_pct"].gt(0).all()
    pd.testing.assert_frame_equal(t[selected.columns],selected)
    t.to_csv(OUT / "selected_trade_ledger_usdc.csv",index=False)


def main():
    feed, spot, bars, fdata, sdata, directions, original, spec, quotes = load()
    full = entry_metrics(feed, bars, original, np.flatnonzero(original), spec)
    cutoff = pd.Timestamp("2026-07-22T17:30Z")
    prefix_feed = feed.loc[feed.Timestamp.le(cutoff)].copy()
    prefix_bars = features(prefix_feed)
    prefix_original = hybrid_signals(prefix_bars, spec["long"], spec["short"])
    prefix_data = ReplayData(prefix_feed,prefix_bars)
    pmap,_ = candidate_map(prefix_data,prefix_original,spec,{"short_space_1r":True},h4_inventory(prefix_feed,prefix_bars))
    prefix_directions = np.zeros_like(prefix_original)
    for i,c in pmap.items():
        prefix_directions[i]=c["side"]
    np.testing.assert_array_equal(prefix_directions,directions[:len(prefix_directions)])
    prefix = entry_metrics(prefix_feed,prefix_bars,prefix_original,np.flatnonzero(prefix_original),spec)
    expected = full.loc[full.decision_at.le(cutoff)].reset_index(drop=True)
    pd.testing.assert_frame_equal(prefix.drop(columns="h4_regime"),expected.drop(columns="h4_regime"))
    f = pd.read_csv(OUT / "all_candidate_entry_metrics.csv")
    for v in VARIANTS:
        pdirections,_ = filtered_directions(prefix_directions,prefix,v)
        fdirections,_ = filtered_directions(directions,full,v)
        np.testing.assert_array_equal(pdirections,fdirections[:len(pdirections)])
    for row in full.itertuples():
        i,side=row.signal_index,row.direction
        rules=ExitRules(**spec["long" if side>0 else "short"]["exit"])
        decision_price=bars.close.iloc[i]
        expected_risk=side*(decision_price-initial_stop(fdata,i,side,decision_price,rules))/decision_price*3000
        np.testing.assert_allclose(row.estimated_risk_quote,expected_risk,atol=1e-8)
    print("All22 filtered signal streams invariant to future append; risk estimates use decision closes",flush=True)
    monthly,paths,unique,omissions=[],0,set(),0
    for v in VARIANTS:
        t=pd.read_csv(OUT / "variant_ledgers" / f'{v["id"]}.csv')
        for col in ["decision_at","entry_at","exit_at","expiry_at"]:
            t[col]=pd.to_datetime(t[col],utc=True)
        dirs,_=filtered_directions(directions,f,v)
        previous=None
        for row in t.itertuples():
            assert not row.censored and dirs[row.signal_index]==row.direction
            assert row.decision_at < row.entry_at
            assert quotes.spot_close_at.iloc[row.signal_index]<=row.decision_at
            assert quotes.futures_close_at.iloc[row.signal_index]<=row.decision_at
            if previous is not None:
                assert row.entry_at > previous+pd.Timedelta(minutes=3)
            previous=row.exit_at
            opening_exit=row.exit_reason=="EXPIRY_NEXT_REAL_OPEN"
            end=row.exit_at+pd.Timedelta(minutes=1) if opening_exit else row.exit_at
            path=spot.loc[spot.Timestamp.gt(row.entry_at) & spot.Timestamp.le(end)]
            assert len(path)>0 and path.Timestamp.diff().dropna().le(pd.Timedelta(minutes=2)).all()
            np.testing.assert_allclose(row.entry_price,path.OpenPrice.iloc[0],atol=1e-8)
            assert path.Timestamp.iloc[0]-pd.Timedelta(minutes=1)==row.entry_at
            stop=path.LowPrice.le(row.stop_price) if row.direction>0 else path.HiPrice.ge(row.stop_price)
            target=path.HiPrice.ge(row.target_price) if row.direction>0 else path.LowPrice.le(row.target_price)
            touch=stop|target
            if row.exit_reason=="EXPIRY":
                assert not touch.any() and row.exit_at==row.expiry_at
                expected_price=path.ClosePrice.iloc[-1]
            elif opening_exit:
                assert not touch.iloc[:-1].any()
                expected_price=path.OpenPrice.iloc[-1]
            else:
                assert touch.any() and np.flatnonzero(touch)[0]==len(path)-1
                if row.exit_reason.startswith("STOP"):
                    assert stop.iloc[-1]
                    expected_price=path.OpenPrice.iloc[-1] if row.exit_reason=="STOP_GAP" else row.stop_price
                else:
                    assert row.exit_reason=="TARGET" and target.iloc[-1] and not stop.iloc[-1]
                    expected_price=row.target_price
            qty=3000/row.entry_price
            gross=row.direction*(expected_price-row.entry_price)*qty
            slip=(row.entry_price+expected_price)*qty*.0002
            risk=abs(row.entry_price-row.stop_price)*qty
            np.testing.assert_allclose([row.exit_price,row.gross_usd,row.slippage_usd,row.net_usd,row.initial_risk_usd,row.net_R],
                                       [expected_price,gross,slip,gross-5-slip,risk,(gross-5-slip)/risk],atol=1e-8)
            assert row.commission_usd==5
            expected_omissions=int((path.Timestamp.diff().dropna()/pd.Timedelta(minutes=1)-1).sum())
            np.testing.assert_allclose(row.omitted_minutes,expected_omissions)
            paths+=1
            omissions+=row.omitted_minutes
            unique.add((row.signal_index,row.direction))
        for month,g in t.groupby(t.entry_at.dt.strftime("%Y-%m")):
            monthly.append({"variant":v["id"],"entry_month":month,"trades":len(g),"wins":int(g.net_usd.gt(0).sum()),
                            "losses":int(g.net_usd.lt(0).sum()),"net_quote":g.net_usd.sum()})
    pd.DataFrame(monthly).to_csv(OUT / "monthly_results.csv",index=False)
    frozen=json.loads((OUT / "diagnostic_manifest.json").read_text())
    assert all(digest(ROOT/p)==sha for p,sha in frozen["baseline_hashes"].items())
    assert digest(OUT / "study.py")==frozen["code_hash"]
    manifest=json.loads((OUT / "filter_manifest.json").read_text())
    assert digest(OUT / "filters.py")==manifest["rules_code_sha256"]
    assert digest(OUT / "run_filters.py")==manifest["runner_code_sha256"]
    winner="LONG_DELTA4_POS_BOTH_BAND4"
    result=pd.read_csv(OUT / "filter_results.csv").set_index("variant").loc[winner].to_dict()
    baseline_contract=json.loads((G / "selected_spot_contract.json").read_text())
    save("selected_research_contract.json",{"version":"SHI_RESET_40H_DELTA_FILTER_RESEARCH_V1","baseline_contract":baseline_contract,
        "new_rules":["All directions: -4% < weighted rolling24h futures delta < +4%.","Long only: weighted rolling4h futures delta >0%."],
        "feature_availability":"actual UTC closed observations in (decision-hours,decision]; never future entry prices/outcomes",
        "filter_manifest_sha256":digest(OUT / "filter_manifest.json"),"rules_sha256":digest(OUT / "filters.py"),
        "candidate_feature_sha256":digest(OUT / "all_candidate_entry_metrics.csv"),
        "historically_adaptive":True,"pristine_holdout":False,"production_promoted":False,"actual_borrowing_in_net":False,
        "market_state_reset":False,"structure_levels_reset":False,"liquidity_zones_reset":False,"qualified_h1_state_reset":False,"setup_context_reset":False,
        "continuity_scope":"Existing40D/40F causal historical state retained, no technical reset; these flags do not claim full Monitor lifecycle promotion.",
        "selected_variant":winner})
    selected=pd.read_csv(OUT / "variant_ledgers" / f'{winner}.csv')
    write_selected_lineage(selected,quotes)
    save("selected_result.json",result)
    a=pd.read_csv(OUT / "every_variant_trade_attribution.csv")
    a.loc[a.variant.eq(winner)].to_csv(OUT / "selected_trade_attribution.csv",index=False)
    checks={"all_declared_portfolios":len(VARIANTS),"independent_paths_checked":paths,"unique_entry_paths_checked":len(unique),
            "no_censored_paths_in_any_variant":True,"all_first_stop_target_expiry_touches_verified":True,
            "independent_dollar_cost_risk_and_R_arithmetic":True,"all_global_books_and_filter_decisions_verified":True,
            "all_entry_metrics_and_22_signal_streams_real_prefix_invariant":True,"prefix_cutoff":cutoff,
            "decision_close_risk_estimates_verified_all52_candidates":True,"all_frozen_baseline_and_source_identities_unchanged":True,
            "full_source_identity_revalidated_by_40B_loader":True,"all_study_code_and_rules_identities_unchanged":True,
            "isolated_omissions_preserved_and_verified":int(omissions),"not_pristine_holdout":True}
    save("independent_verification.json",checks)
    hashes={p.relative_to(OUT).as_posix():digest(p) for p in sorted(OUT.rglob("*"))
            if p.is_file() and p.suffix in [".py",".csv",".json"] and p.name!="artifact_hashes.json" and "__pycache__" not in str(p)}
    save("artifact_hashes.json",hashes)
    print(json.dumps(checks,default=str,indent=2),flush=True)


if __name__=="__main__":
    main()
