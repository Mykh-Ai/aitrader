from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest, usable_observations

manifest = json.loads((OUT / "execution_manifest_v2.json").read_text())
spec = manifest["baseline_spec"]
feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
raw = usable_observations(feed)
minute = pd.Timedelta(minutes=1)
checked, activated, details = 0, 0, []
for name in ["BASE_TRIGGER_2R", "SHORT_SPACE_TRIGGER_2R"]:
    trades = pd.read_csv(OUT / "variant_ledgers" / f"{name}.csv")
    for field in ["decision_at", "entry_at", "exit_at", "expiry_at", "stop_amendment_decision_at", "stop_amendment_active_at"]:
        trades[field] = pd.to_datetime(trades[field], utc=True)
    for row in trades.itertuples():
        if row.censored:
            continue
        risk = abs(row.stop_price - row.entry_price)
        last = row.exit_at + (minute if row.exit_price_clock == "MINUTE_OPEN" else pd.Timedelta(0))
        path = raw.loc[(raw.Timestamp >= row.entry_at + minute) & (raw.Timestamp <= last)]
        assert path.DataQuality.eq("RAW").all()
        assert path.Timestamp.diff().dropna().le(2 * minute).all()
        effective = np.full(len(path), row.stop_price, dtype=float)
        if pd.notna(row.stop_amendment_decision_at):
            assert row.direction == -1
            observed = path.loc[path.Timestamp <= row.stop_amendment_decision_at]
            crossings = (row.entry_price - observed.LowPrice) / risk >= 2
            assert crossings.any() and observed.loc[crossings].Timestamp.iloc[0] == row.stop_amendment_decision_at
        if pd.notna(row.stop_amendment_active_at):
            assert row.stop_amendment_active_at >= row.stop_amendment_decision_at + minute
            active = path.Timestamp - minute >= row.stop_amendment_active_at
            effective[active] = row.entry_price - .25 * risk
            activated += 1
            details.append({"variant": name, "entry_at": row.entry_at, "activation_at": row.stop_amendment_active_at,
                            "exit_at": row.exit_at, "exit_reason": row.exit_reason, "net_usd": row.net_usd})
        stop_hit = path.LowPrice.to_numpy() <= effective if row.direction > 0 else path.HiPrice.to_numpy() >= effective
        target_hit = path.HiPrice.ge(row.target_price).to_numpy() if row.direction > 0 else path.LowPrice.le(row.target_price).to_numpy()
        hit = stop_hit | target_hit
        if row.exit_price_clock == "MINUTE_OPEN":
            assert not hit[:-1].any()
        elif row.exit_reason.startswith("EXPIRY"):
            assert not hit.any() and row.exit_at == row.expiry_at
            np.testing.assert_allclose(row.exit_price, path.ClosePrice.iloc[-1])
        else:
            assert hit.any() and np.flatnonzero(hit)[0] == len(path) - 1
            if "STOP" in row.exit_reason:
                assert stop_hit[-1]
                if row.exit_reason.endswith("GAP"):
                    np.testing.assert_allclose(row.exit_price, path.OpenPrice.iloc[-1])
                else:
                    np.testing.assert_allclose(row.exit_price, effective[-1])
            elif row.exit_reason == "TARGET":
                assert not stop_hit[-1] and target_hit[-1]
                np.testing.assert_allclose(row.exit_price, row.target_price)
        checked += 1
pd.DataFrame(details).to_csv(OUT / "all_2R_activations.csv", index=False)
verification = {"two_R_closed_paths_independently_checked": checked, "two_R_stop_activations": activated,
                "first_trigger_is_causally_observed_2R": True, "first_terminal_touch_with_amendment_latency_verified": True,
                "source_identity_verified": True,
                "all_prior_artifacts_preserved": all(digest(ROOT / p) == sha for p, sha in manifest["preserved_artifact_hashes"].items())}
assert verification["all_prior_artifacts_preserved"]
(OUT / "independent_verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n")
print(json.dumps(verification))
