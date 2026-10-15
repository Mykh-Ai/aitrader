"""User-authorized read-only remote acquisition and verified local feed refresh."""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json
import subprocess
import sys
import urllib.request
import zipfile

import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
G=ROOT/"market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0"
DAYS=("2026-10-13","2026-10-14")
REQUIRED=["Timestamp","Open","High","Low","Close","Volume","AggTrades","BuyQty","SellQty","VWAP","OpenInterest","FundingRate","LiqBuyQty","LiqSellQty","IsSynthetic"]
FIELDS=["open_time","OpenPrice","HiPrice","LowPrice","ClosePrice","TotalQty","close_time","QuoteQty","Trades","BuyQty","BuyQuoteQty","ignore"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,default=str,allow_nan=False)+"\n",encoding="utf-8")


def frozen_identity():
    prep=json.loads((ROOT/"market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/preparation_manifest.json").read_text())
    identities={**prep["source_hashes"],**prep["code_hashes"]}
    for name,expected in identities.items():
        assert sha(ROOT/name)==expected,f'Frozen input changed:{name}'
    for folder in [ROOT/"market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0",G]:
        hashes=json.loads((folder/"artifact_hashes.json").read_text())
        assert all(sha(folder/name)==expected for name,expected in hashes.items())
    return identities


def quality(payload,day):
    f=pd.read_csv(io.BytesIO(payload))
    assert all(c in f for c in REQUIRED),f'Missing raw columns:{day}'
    ts=pd.to_datetime(f.Timestamp,utc=True)
    expected=pd.date_range(f'{day}T00:00Z',periods=1440,freq="min")
    assert len(f)==1440 and np.array_equal(ts.to_numpy(),expected.to_numpy()),f'Incomplete/unordered source day:{day}'
    for col in REQUIRED[1:]:
        assert np.isfinite(pd.to_numeric(f[col],errors="raise")).all()
    assert f[["Open","High","Low","Close"]].gt(0).all().all()
    assert f.High.ge(f[["Open","Close","Low"]].max(axis=1)).all()
    assert f.Low.le(f[["Open","Close","High"]].min(axis=1)).all()
    assert f[["Volume","AggTrades","BuyQty","SellQty","OpenInterest","LiqBuyQty","LiqSellQty"]].ge(0).all().all()
    parity=np.abs(f.BuyQty+f.SellQty-f.Volume)
    assert np.allclose(f.BuyQty+f.SellQty,f.Volume,rtol=1e-7,atol=1e-7)
    return {"day":day,"rows":len(f),"first_close":ts.iloc[0],"last_close":ts.iloc[-1],"missing_minutes":0,
            "duplicate_timestamps":int(ts.duplicated().sum()),"synthetic_rows":int(f.IsSynthetic.ne(0).sum()),
            "max_buy_sell_volume_parity_error":float(parity.max())}


REMOTE = r'''
from pathlib import Path
import base64,datetime,hashlib,json
root=Path('/opt/aitrader_data/feed')
out={'server_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_root':str(root),'files':[]}
for day in ('2026-10-13','2026-10-14'):
 p=root/(day+'.csv')
 raw=p.read_bytes()
 if len(raw)>2000000: raise ValueError('Unexpected source size')
 checksum=hashlib.sha256(raw).hexdigest()
 if hashlib.sha256(p.read_bytes()).hexdigest()!=checksum: raise ValueError('Source changed while reading')
 out['files'].append({'day':day,'sha256':checksum,'bytes':len(raw),'payload':base64.b64encode(raw).decode('ascii')})
p=root/'2026-10-15.csv'
if p.exists():
 raw=p.read_bytes()
 lines=raw.splitlines()
 out['current_day_metadata_only']={'day':'2026-10-15','rows':max(0,len(lines)-1),'last_timestamp':lines[-1].split(b',',1)[0].decode('ascii') if len(lines)>1 else None,'not_downloaded':True}
print(json.dumps(out))
'''


def fetch_server():
    identities=frozen_identity()
    before={day:sha(ROOT/"feed"/(day+".csv")) if (ROOT/"feed"/(day+".csv")).exists() else None for day in DAYS}
    command=["ssh","-o","BatchMode=yes","-o","ConnectTimeout=15","vps95","python3 -"]
    result=subprocess.run(command,input=REMOTE,text=True,capture_output=True,timeout=60)
    if result.returncode:
        raise RuntimeError(f'SSH read failed:{result.stderr.strip()[:700]}')
    if len(result.stdout)>6000000:
        raise ValueError('Unexpected remote response size')
    response=json.loads(result.stdout)
    assert response["source_root"]=="/opt/aitrader_data/feed"
    assert [r["day"] for r in response["files"]]==list(DAYS)
    dest=OUT/"server_download"
    dest.mkdir(exist_ok=True)
    rows=[]
    for record in response["files"]:
        payload=base64.b64decode(record["payload"],validate=True)
        assert len(payload)==record["bytes"] and len(payload)<=2000000
        assert hashlib.sha256(payload).hexdigest()==record["sha256"]
        details=quality(payload,record["day"])
        old=ROOT/"feed"/(record["day"]+".csv")
        append_only=True
        if old.exists():
            append_only=payload.startswith(old.read_bytes())
            assert append_only,f'Existing rows differ;do not overwrite:{old.name}'
        (dest/(record["day"]+".csv")).write_bytes(payload)
        rows.append({**details,"remote_sha256":record["sha256"],"local_before_sha256":before[record["day"]],
                     "old_rows_preserved_as_exact_byte_prefix":append_only,"download_sha256":sha(dest/(record["day"]+".csv"))})
    save("server_acquisition.json",{"ssh_alias":"vps95","server_source_root":response["source_root"],"server_utc":response["server_utc"],
        "files":rows,"current_day_metadata_only":response.get("current_day_metadata_only"),"local_before":before,
        "frozen230_source_and_code_hashes":identities,"remote_mutation":False,"local_feed_updated":False})
    print(json.dumps({"server_utc":response["server_utc"],"days":rows,"current_day_metadata_only":response.get("current_day_metadata_only")},default=str,indent=2),flush=True)


def fetch(url,target):
    assert url.startswith("https://data.binance.vision/data/spot/daily/klines/BTCUSDC/1m/")
    with urllib.request.urlopen(url,timeout=25) as response:
        assert response.status==200
        data=response.read(2000001)
    assert len(data)<=2000000
    target.write_bytes(data)


def fetch_spot():
    raw=OUT/"spot_BTCUSDC/raw"
    raw.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((G/"source_manifest.json").read_text()) if (G/"source_manifest.json").exists() else None
    prior_expected=json.loads((G/"selected_spot_contract.json").read_text())["spot_csv_sha256"]
    prior_csv=G/"spot_BTCUSDC/spot_minutes.csv"
    assert sha(prior_csv)==prior_expected
    prior=pd.read_csv(prior_csv)
    prior.Timestamp=pd.to_datetime(prior.Timestamp,utc=True)
    frames=[prior]
    rows=[]
    for day in DAYS:
        name=f'BTCUSDC-1m-{day}.zip'
        url=f'https://data.binance.vision/data/spot/daily/klines/BTCUSDC/1m/{name}'
        archive,checksum=raw/name,raw/(name+".CHECKSUM")
        if not checksum.exists(): fetch(url+".CHECKSUM",checksum)
        if not archive.exists(): fetch(url,archive)
        assert sha(archive)==checksum.read_text().split()[0],f'Official checksum mismatch:{day}'
        with zipfile.ZipFile(archive) as z:
            assert z.namelist()==[name[:-4]+".csv"]
            frame=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),names=FIELDS)
        expected=pd.date_range(f'{day}T00:00Z',periods=1440,freq="min")
        opens=pd.to_datetime(frame.open_time,unit="us",utc=True)
        assert len(frame)==1440 and np.array_equal(opens.to_numpy(),expected.to_numpy())
        assert (frame.close_time-frame.open_time).eq(59999999).all()
        frame["Timestamp"]=opens+pd.Timedelta(minutes=1)
        frame["Market"],frame["Symbol"],frame["SourceArchive"]="BINANCE_SPOT","BTCUSDC",name
        assert frame.HiPrice.ge(frame[["OpenPrice","ClosePrice","LowPrice"]].max(axis=1)).all()
        assert frame.LowPrice.le(frame[["OpenPrice","ClosePrice","HiPrice"]].min(axis=1)).all()
        assert frame.LowPrice.gt(0).all() and frame.TotalQty.ge(0).all()
        traded=frame.TotalQty.gt(0)&frame.Trades.gt(0)
        frame["DataQuality"]=np.where(traded,"RAW","SPOT_NO_OBSERVED_TRADES")
        frame["IsSynthetic"],frame["IsRecovered"],frame["InvalidRow"]=0,False,False
        frame["SellQty"]=frame.TotalQty-frame.BuyQty
        frames.append(frame[prior.columns])
        rows.append({"day":day,"url":url,"sha256":sha(archive),"checksum_sha256":sha(checksum),"rows":len(frame),
                     "first_close":frame.Timestamp.iloc[0],"last_close":frame.Timestamp.iloc[-1],"no_trade_minutes":int((~traded).sum())})
    combined=pd.concat(frames,ignore_index=True)
    assert combined.Timestamp.is_monotonic_increasing and not combined.Timestamp.duplicated().any()
    pd.testing.assert_frame_equal(combined.iloc[:len(prior)].reset_index(drop=True),prior,check_dtype=False)
    target=OUT/"spot_BTCUSDC/spot_minutes.csv"
    prior_bytes=prior_csv.read_bytes()
    assert prior_bytes.endswith(b"\n")
    tail=pd.concat(frames[1:],ignore_index=True)
    target.write_bytes(prior_bytes+tail.to_csv(index=False,header=False).encode("utf-8"))
    assert target.read_bytes().startswith(prior_bytes)
    save("spot_acquisition.json",{"market":"BINANCE_SPOT_BTCUSDC","prior_frozen_csv":prior_csv.relative_to(ROOT).as_posix(),
        "prior_csv_sha256":prior_expected,"new_daily_archives":rows,"combined_rows":len(combined),
        "combined_first_close":combined.Timestamp.iloc[0],"combined_last_close":combined.Timestamp.iloc[-1],
        "combined_csv_sha256":sha(target),"prior_rows_preserved":True,"prior_CSV_bytes_preserved_as_exact_prefix":True,"frozen40G_not_modified":True})
    print(json.dumps({"new_spot_archives":rows,"combined_rows":len(combined),"last_close":combined.Timestamp.iloc[-1]},default=str,indent=2),flush=True)


def apply():
    identities=frozen_identity()
    m=json.loads((OUT/"server_acquisition.json").read_text())
    planned=[]
    for record in m["files"]:
        day=record["day"]
        assert day in DAYS
        source=OUT/"server_download"/(day+".csv")
        destination=(ROOT/"feed"/(day+".csv")).resolve()
        assert destination.parent==(ROOT/"feed").resolve()
        assert sha(source)==record["remote_sha256"]
        quality(source.read_bytes(),day)
        current=sha(destination) if destination.exists() else None
        assert current==m["local_before"][day],f'Local file changed after preflight:{day}'
        planned.append((source,destination,record))
    applied=[]
    for source,destination,record in planned:
        if destination.exists():
            backup=OUT/"before_refresh/feed"/destination.name
            backup.parent.mkdir(parents=True,exist_ok=True)
            assert not backup.exists()
            backup.write_bytes(destination.read_bytes())
            assert sha(backup)==record["local_before_sha256"]
        temporary=OUT/(destination.name+".verified")
        temporary.write_bytes(source.read_bytes())
        assert sha(temporary)==record["remote_sha256"]
        temporary.replace(destination)
        assert sha(destination)==record["remote_sha256"]
        applied.append({"day":record["day"],"path":destination.relative_to(ROOT).as_posix(),"sha256":sha(destination),
                        "before_sha256":record["local_before_sha256"],**quality(destination.read_bytes(),record["day"])})
    assert all(sha(ROOT/n)==h for n,h in identities.items())
    save("feed_refresh_verification.json",{"complete_UTC_days_applied":applied,"all230_original_frozen_source_files_unchanged":True,
        "prior_partial13_preserved":True,"server_files_match_exact_bytes":True,"feed_recovered_unchanged":True,
        "aggregator_and_strategy_code_unchanged":True,"October15_not_imported":True,"new_replay_performed":False,
        "source_cutoff_available":"2026-10-14T23:59:00Z"})
    print(json.dumps({"applied":applied,"all_old_frozen_identities_unchanged":True},default=str,indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["fetch-server","fetch-spot","apply"])
    args=parser.parse_args()
    {"fetch-server":fetch_server,"fetch-spot":fetch_spot,"apply":apply}[args.mode]()
