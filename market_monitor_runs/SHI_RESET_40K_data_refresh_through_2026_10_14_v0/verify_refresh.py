"""Read-only post-refresh validation of source identity and chronology."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(OUT))
from research.own_signal_run.feed import read_sources,closed_bars,usable_observations
from refresh import sha,save,frozen_identity,G,DAYS


def main():
    original=frozen_identity()
    before=json.loads((ROOT/"market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/preparation_manifest.json").read_text())
    refreshed,inventory=read_sources(ROOT,"2026-03-11T13:45:00Z","2026-10-14T23:59:00Z")
    prefix=refreshed.loc[refreshed.Timestamp.le(pd.Timestamp("2026-10-12T23:59Z"))]
    assert len(prefix)==before["selected_rows"]
    assert len(refreshed)==before["selected_rows"]+2880
    new=refreshed.loc[refreshed.Timestamp.gt(pd.Timestamp("2026-10-12T23:59Z"))]
    expected=pd.date_range("2026-10-13T00:00Z","2026-10-14T23:59Z",freq="min")
    assert np.array_equal(new.Timestamp.to_numpy(),expected.to_numpy())
    assert new.DataQuality.eq("RAW").all() and not new.Timestamp.duplicated().any()
    inventory.to_csv(OUT/"updated_futures_source_inventory.csv",index=False)
    backup=OUT/"before_refresh/feed/2026-10-13.csv"
    local=ROOT/"feed/2026-10-13.csv"
    assert local.read_bytes().startswith(backup.read_bytes())
    assert len(pd.read_csv(backup))==480 and len(pd.read_csv(local))==1440
    s=json.loads((OUT/"server_acquisition.json").read_text())
    for r in s["files"]:
        assert sha(ROOT/"feed"/(r["day"]+".csv"))==r["remote_sha256"]
    old_spot=pd.read_csv(G/"spot_BTCUSDC/spot_minutes.csv")
    new_spot=pd.read_csv(OUT/"spot_BTCUSDC/spot_minutes.csv")
    assert (OUT/"spot_BTCUSDC/spot_minutes.csv").read_bytes().startswith((G/"spot_BTCUSDC/spot_minutes.csv").read_bytes())
    pd.testing.assert_frame_equal(new_spot.iloc[:len(old_spot)].reset_index(drop=True),old_spot,check_exact=True)
    new_spot.Timestamp=pd.to_datetime(new_spot.Timestamp,utc=True)
    new_minutes=new_spot.iloc[len(old_spot):]
    assert len(new_minutes)==2880 and new_minutes.DataQuality.eq("RAW").all()
    assert new_spot.Timestamp.diff().dropna().eq(pd.Timedelta(minutes=1)).all()
    assert np.array_equal(new_minutes.Timestamp.to_numpy(),pd.date_range("2026-10-13T00:01Z","2026-10-15T00:00Z",freq="min").to_numpy())
    shared_spot=new_spot.loc[new_spot.Timestamp.between(refreshed.Timestamp.min(),refreshed.Timestamp.max())]
    assert shared_spot.Timestamp.max()==refreshed.Timestamp.max()
    h1=closed_bars(usable_observations(refreshed),60)
    assert h1.loc[h1.completed,"timestamp"].max()==pd.Timestamp("2026-10-14T23:00Z")
    updates={"futures_available_first_close":refreshed.Timestamp.min(),"futures_available_last_close":refreshed.Timestamp.max(),
        "selected_source_rows":len(refreshed),"prior_frozen_source_rows":len(prefix),"new_full_days_rows":len(new),
        "last_complete_H1_close":h1.loc[h1.completed,"timestamp"].max(),"source_inventory_files":int(inventory.status.eq("READ").sum()),
        "new_futures_days_complete_RAW_no_missing_duplicates":True,"local_days_equal_server_hashes":True,
        "old13_partial480rows_preserved_as_exact_prefix_and_backup":True,"all230_frozen_source_files_and_code_unchanged":True,
        "spot_available_rows":len(new_spot),"spot_available_last_right_close":new_spot.Timestamp.max(),
        "spot_day14_last_open":"2026-10-14T23:59:00Z","spot_right_close_midnight_is_complete14_day":True,
        "spot_new_rows":len(new_minutes),"spot_new_no_trade_minutes":int(new_minutes.DataQuality.ne("RAW").sum()),
        "all_old_spot_rows_unchanged_and_new_minutes_contiguous":True,"prior_spot_CSV_bytes_preserved_as_exact_prefix":True,"shared_signal_execution_cutoff":shared_spot.Timestamp.max(),
        "October15_partial_not_imported":True,"new_financial_replay_performed":False,
        "old_contract_cutoff_and_entry_end_unchanged":True,"note":"October1entry exclusion remains in frozen strategy; a separately declared extended replay is still required."}
    save("data_readiness.json",updates)
    assert all(sha(ROOT/name)==value for name,value in original.items())
    print(json.dumps(updates,indent=2,default=str),flush=True)


if __name__=="__main__":
    main()
