"""Execute byte-exact historical modules from the0862342 reproduction only."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SNAP = OUT / "frozen_snapshot"
H = SNAP / "market_monitor_runs/SHI_RESET_40H_loss_metrics_filter_study_v0"
F = SNAP / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0"
for folder in [SNAP, F, H]:
    sys.path.insert(0, str(folder))
from study import load, entry_metrics
from filters import filtered_directions
from research.own_signal_run.feed import read_sources, usable_observations, window_is_usable
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, initial_stop, ExitRules
from interventions import h4_inventory, candidate_map

RULES = {"rules": ["L_D4_POS", "B_D24_BAND4"]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity():
    for module in [features, hybrid_signals, replay_hybrid, read_sources, filtered_directions, h4_inventory, candidate_map, initial_stop]:
        path = Path(sys.modules[module.__module__].__file__).resolve()
        assert path.is_relative_to(SNAP), f"Current modified implementation substituted: {path}"
    selected = json.loads((H / "selected_research_contract.json").read_text())
    assert sha(H / "filters.py") == selected["rules_sha256"] == "ee30c96985677283176bdab15b1ce853b12bb0cd04b7cc95377376670da4c6f4"
    assert sha(H / "filter_manifest.json") == selected["filter_manifest_sha256"] == "32ff407d64201aeeae83f2bfbccb080f350822d15f7add37ebaa8ecef7cd0c56"
    return selected


def executed_hashes():
    return {Path(m.__file__).resolve().relative_to(SNAP).as_posix(): sha(Path(m.__file__))
            for m in list(sys.modules.values()) if getattr(m, "__file__", None)
            and Path(m.__file__).resolve().is_relative_to(SNAP) and Path(m.__file__).suffix == ".py"}


def reproduce_known_control():
    selected = identity()
    feed, spot, bars, _, data, space, original, spec, _ = load()
    known = entry_metrics(feed, bars, original, np.flatnonzero(original), spec)
    final, _ = filtered_directions(space, known, RULES)
    control = replay_hybrid(data, final, spec["long"], spec["short"])
    saved = pd.read_csv(H / "selected_trade_ledger_usdc.csv")
    for name in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        saved[name] = pd.to_datetime(saved[name], utc=True)
    pd.testing.assert_frame_equal(control, saved[control.columns], check_exact=False, rtol=1e-10, atol=1e-10)
    assert len(control) == 13 and abs(control.net_usd.sum() - 1090.8118508490645) < 1e-8
    result = {"status": "FROZEN40H_EXACT_CONTROL_REPRODUCED", "selected_variant": selected["selected_variant"],
              "original_control_trades": len(control), "original_control_net_usdc": float(control.net_usd.sum()),
              "rules_sha256": selected["rules_sha256"], "filter_manifest_sha256": selected["filter_manifest_sha256"],
              "executed_frozen_code_hashes": executed_hashes(), "OOS_return_read": False}
    (OUT / "frozen_identity_verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("Frozen40H13-row selected spot control exactly reproduced; no OOS execution", flush=True)
    return spec


def rolling_inputs(feed, bars, original):
    raw = usable_observations(feed)
    timestamps = pd.DatetimeIndex(raw.Timestamp).asi8
    rows = []
    for i, b in bars.iterrows():
        decision = b.available_at
        right = timestamps.searchsorted(decision.value, side="right")
        row = {"signal_index": i, "direction": int(original[i]), "decision_at": decision}
        for hours in [4, 24]:
            left = timestamps.searchsorted((decision - pd.Timedelta(hours=hours)).value, side="right")
            w = raw.iloc[left:right]
            valid = window_is_usable(w, decision - pd.Timedelta(hours=hours) + pd.Timedelta(minutes=1), decision)
            volume = w.TotalQty.sum()
            row[f"window{hours}_usable"] = valid
            row[f"delta{hours}_pct"] = 100 * (w.BuyQty.sum() - w.SellQty.sum()) / volume if valid and volume > 0 else np.nan
            row[f"window{hours}_last_observation_at"] = w.Timestamp.iloc[-1] if len(w) else pd.NaT
        rows.append(row)
    return pd.DataFrame(rows)


def build_state(feed, spec):
    identity()
    bars = features(feed)
    raw = hybrid_signals(bars, spec["long"], spec["short"])
    data = ReplayData(feed, bars)
    inventory = h4_inventory(feed, bars)
    cands, rejected = candidate_map(data, raw, spec, {"short_space_1r": True}, inventory)
    space = np.zeros_like(raw)
    for i, c in cands.items():
        space[i] = c["side"]
    f = rolling_inputs(feed, bars, raw)
    final, allowed = filtered_directions(space, f, RULES)
    bars = bars.copy()
    for col in ["delta4_pct", "delta24_pct", "window4_usable", "window24_usable"]:
        bars[col] = f[col]
    bars["long_stop_estimate"] = [initial_stop(data, i, 1, b.close, ExitRules(**spec["long"]["exit"])) for i, b in bars.iterrows()]
    bars["short_stop_estimate"] = [initial_stop(data, i, -1, b.close, ExitRules(**spec["short"]["exit"])) for i, b in bars.iterrows()]
    bars["raw_direction"] = raw
    bars["final_direction"] = final
    bars["h4_inventory_hash"] = [hashlib.sha256(json.dumps(inventory[i], sort_keys=True, default=str).encode()).hexdigest() for i in range(len(bars))]
    reasons = []
    rejection = {r["signal_index"]: r["reason"] for r in rejected}
    for i in range(len(bars)):
        reason = []
        if not raw[i]:
            reason.append("NO_RAW_CANDIDATE")
        else:
            if not space[i]:
                reason.append(rejection.get(i, "H4_SPACE_REJECTED"))
            if not f.window24_usable.iloc[i]:
                reason.append("DELTA24_UNUSABLE")
            elif not abs(f.delta24_pct.iloc[i]) < 4:
                reason.append("DELTA24_OUTSIDE_STRICT_BAND4")
            if raw[i] > 0:
                if not f.window4_usable.iloc[i]:
                    reason.append("DELTA4_UNUSABLE")
                elif not f.delta4_pct.iloc[i] > 0:
                    reason.append("LONG_DELTA4_NOT_POSITIVE")
        reasons.append("|".join(reason) if reason else "ALLOWED_PRE_BOOK")
    bars["blocker_reasons"] = reasons
    for h in [4, 24]:
        assert (f[f"window{h}_last_observation_at"] <= f.decision_at).all()
    return bars, inventory, cands, rejected, f


if __name__ == "__main__":
    reproduce_known_control()
