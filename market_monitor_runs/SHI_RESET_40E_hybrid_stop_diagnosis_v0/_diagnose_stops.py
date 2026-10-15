from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import closed_bars, digest, usable_observations
from research.strategy_search.features import features

SRC = ROOT / "market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0"
manifest = json.loads((OUT / "study_manifest.json").read_text())
assert all(digest(SRC / p) == sha for p, sha in manifest["baseline_hashes"].items())
spec = json.loads((SRC / "selected_strategy.json").read_text())
assert all(digest(ROOT / p) == sha for p, sha in spec["code_hashes"].items())
feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
working = usable_observations(feed)
bars = features(feed)
h4 = closed_bars(working, 240)
h4 = h4.loc[h4.completed].reset_index(drop=True)
t = pd.read_csv(SRC / "selected_trade_ledger_usd.csv")
for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
    t[col] = pd.to_datetime(t[col], utc=True)
assert len(t) == 26 and t.exit_reason.eq("STOP").sum() == 16

# Whole prior chronology, confirmed H4 references and accepted-break retirement.
levels, inventory, cursor = [], {}, 0
trade_indexes = set(t.signal_index)
for i, bar in bars.iterrows():
    while cursor < len(h4) and h4.available_at.iloc[cursor] <= bar.available_at:
        if cursor >= 2:
            window = h4.iloc[cursor - 2:cursor + 1]
            if window.usable.all() and window.timestamp.diff().iloc[1:].eq(pd.Timedelta(hours=4)).all():
                center = window.iloc[1]
                for side, value, valid in [(1, center.high, center.high > max(window.high.iloc[0], window.high.iloc[2])),
                                            (-1, center.low, center.low < min(window.low.iloc[0], window.low.iloc[2]))]:
                    if valid:
                        levels.append({"side": side, "price": float(value), "available_at": h4.available_at.iloc[cursor],
                                       "center_at": center.timestamp, "active": True, "beyond": 0})
        cursor += 1
    for level in levels:
        if not level["active"]:
            continue
        beyond = bar.close > level["price"] * 1.0005 if level["side"] == 1 else bar.close < level["price"] * .9995
        level["beyond"] = level["beyond"] + 1 if bar.usable and beyond else 0
        if level["beyond"] >= 2:
            level["active"] = False
    if i in trade_indexes:
        inventory[i] = [dict(x) for x in levels if x["active"] and x["available_at"] <= bar.available_at
                        and bar.available_at - x["available_at"] <= pd.Timedelta(days=30)]

rows = []
for trade in t.to_dict("records"):
    i, side = trade["signal_index"], trade["direction"]
    bar = bars.iloc[i]
    entry, risk = trade["entry_price"], abs(trade["entry_price"] - trade["stop_price"])
    quantity = 3000 / entry
    path = working.loc[(working.Timestamp >= trade["entry_at"] + pd.Timedelta(minutes=1)) & (working.Timestamp <= trade["exit_at"])]
    before_terminal = path.loc[path.Timestamp < trade["exit_at"]]
    favorable = (before_terminal.HiPrice - entry) / risk if side == 1 else (entry - before_terminal.LowPrice) / risk
    adverse = (entry - before_terminal.LowPrice) / risk if side == 1 else (before_terminal.HiPrice - entry) / risk
    favorable_including_terminal = (path.HiPrice - entry) / risk if side == 1 else (entry - path.LowPrice) / risk
    mfe = max(0.0, float(favorable.max())) if len(favorable) else 0.0
    mae = max(0.0, float(adverse.max())) if len(adverse) else 0.0
    past = working.loc[(working.Timestamp > trade["decision_at"] - pd.Timedelta(hours=24)) & (working.Timestamp <= trade["decision_at"])]
    raw_past = past.DataQuality.eq("RAW").all()
    oi_change = 100 * (past.OpenInterest.iloc[-1] / past.OpenInterest.iloc[0] - 1) if raw_past and past.OpenInterest.iloc[0] else None
    structural = bar.lower6 * .9995 if side == 1 else bar.upper6 * 1.0005
    atr_stop = entry - side * spec["long" if side == 1 else "short"]["exit"]["atr_floor"] * bar.atr
    anchor = "ATR_FLOOR" if (atr_stop < structural if side == 1 else atr_stop > structural) else "PRIOR_6H_STRUCTURE"
    trend_efficiency = abs(bar.close - bars.close.iloc[i - 24]) / bars.close.diff().abs().iloc[i - 23:i + 1].sum()
    opposite = [x for x in inventory[i] if x["side"] == side and (x["price"] * .9995 > entry if side == 1 else x["price"] * 1.0005 < entry)]
    blocker = min(opposite, key=lambda x: abs(x["price"] - entry), default=None)
    barrier = blocker["price"] * (.9995 if side == 1 else 1.0005) if blocker else None
    barrier_r = side * (barrier - entry) / risk if barrier is not None else None
    next_closed = bars.loc[(bars.available_at > trade["entry_at"]) & (bars.available_at <= trade["exit_at"])
                           & (bars.available_at <= trade["decision_at"] + pd.Timedelta(hours=3)) & bars.usable]
    reference = float(bar.ema24) if side == 1 else float(bars.lower48.iloc[i - 1])
    invalidation = next_closed.close.lt(reference * .9995) if side == 1 else next_closed.close.gt(reference * 1.0005)
    first_invalidation = next_closed.loc[invalidation].available_at.min() if invalidation.any() else pd.NaT
    after_stop = working.loc[(working.Timestamp > trade["exit_at"]) & (working.Timestamp <= trade["expiry_at"])]
    post_complete = len(after_stop) > 0 and after_stop.DataQuality.eq("RAW").all()
    if len(after_stop):
        post_complete &= after_stop.Timestamp.iloc[0] - trade["exit_at"] <= pd.Timedelta(minutes=2)
        post_complete &= trade["expiry_at"] - after_stop.Timestamp.iloc[-1] <= pd.Timedelta(minutes=1)
    if len(after_stop) > 1:
        post_complete &= after_stop.Timestamp.diff().iloc[1:].le(pd.Timedelta(minutes=2)).all()
    if len(after_stop):
        post_mfe = float(((after_stop.HiPrice - entry) / risk if side == 1 else (entry - after_stop.LowPrice) / risk).max())
    else:
        post_mfe = None
    record = {**trade, "side": "LONG" if side == 1 else "SHORT", "stopped": trade["exit_reason"] == "STOP",
              "mfe_before_terminal_R": mfe, "mfe_terminal_minute_upper_bound_R": max(0.0, float(favorable_including_terminal.max())),
              "mae_before_terminal_R": mae, "mfe_before_terminal_usd": mfe * risk * quantity,
              "risk_atr": risk / bar.atr, "stop_anchor": anchor,
              "entry_delta_signed": side * bar.delta, "entry_delta24_signed": side * bar.delta24,
              "entry_volume_ratio": float(bar.volume_ratio), "entry_range_atr": (bar.high - bar.low) / bar.atr,
              "entry_ema24_distance_atr_signed": side * (bar.close - bar.ema24) / bar.atr,
              "entry_ema24_72_separation_atr_signed": side * (bar.ema24 - bar.ema72) / bar.atr,
              "entry_ema168_slope24_atr_signed": side * (bar.ema168 - bars.ema168.iloc[i - 24]) / bar.atr,
              "entry_change24_signed_pct": side * bar.change24 * 100,
              "entry_trend_efficiency24": float(trend_efficiency), "entry_oi24_change_pct": oi_change,
              "entry_liq_buy24_qty": float(past.LiqBuyQty.sum()), "entry_liq_sell24_qty": float(past.LiqSellQty.sum()),
              "opposing_h4_barrier_price": barrier, "opposing_h4_barrier_R": barrier_r,
              "opposing_h4_available_at": blocker["available_at"] if blocker else pd.NaT,
              "first_frozen_reference_invalidation_at": first_invalidation,
              "early_reference_failure_within3h_before_exit": pd.notna(first_invalidation),
              "post_stop_path_complete_raw": bool(post_complete),
              "post_stop_mfe_through_original_expiry_R": post_mfe if trade["exit_reason"] == "STOP" and post_complete else None}
    for threshold in [.5, 1, 2, 3, 4, 6, 8, 10]:
        record[f"reached_{str(threshold).replace('.', '_')}R_before_terminal"] = bool(mfe >= threshold)
    rows.append(record)

details = pd.DataFrame(rows)
details.to_csv(OUT / "all_trade_diagnostics.csv", index=False)
for side in ["LONG", "SHORT"]:
    details.loc[details.side.eq(side)].to_csv(OUT / f"{side.lower()}_trade_diagnostics.csv", index=False)
    details.loc[details.side.eq(side) & details.stopped].to_csv(OUT / f"{side.lower()}_stop_cases.csv", index=False)
details.loc[details.stopped].to_csv(OUT / "all_16_stop_cases.csv", index=False)

summaries = []
for side in ["LONG", "SHORT"]:
    group = details.loc[details.side.eq(side)]
    stop = group.loc[group.stopped]
    summaries.append({"side": side, "total_trades": len(group), "stops": len(stop), "stop_rate": len(stop) / len(group),
                      "stop_gross_loss_usd": float(stop.gross_usd.sum()), "stop_net_loss_usd": float(stop.net_usd.sum()),
                      "total_net_usd": float(group.net_usd.sum()), "median_hours_to_stop": float(stop.holding_hours.median()),
                      "median_stop_mfe_R": float(stop.mfe_before_terminal_R.median()),
                      "stop_no_0_5R": int(stop.mfe_before_terminal_R.lt(.5).sum()),
                      "stop_reached_1R": int(stop.mfe_before_terminal_R.ge(1).sum()),
                      "stop_reached_2R": int(stop.mfe_before_terminal_R.ge(2).sum()),
                      "stop_reached_3R": int(stop.mfe_before_terminal_R.ge(3).sum()),
                      "early_reference_failure_stops": int(stop.early_reference_failure_within3h_before_exit.sum()),
                      "early_reference_failure_nonstops": int(group.loc[~group.stopped].early_reference_failure_within3h_before_exit.sum()),
                      "atr_anchored_stops": int(stop.stop_anchor.eq("ATR_FLOOR").sum()),
                      "structure_anchored_stops": int(stop.stop_anchor.eq("PRIOR_6H_STRUCTURE").sum()),
                      "stop_opposing_h4_within1R": int(stop.opposing_h4_barrier_R.le(1).sum()),
                      "nonstop_opposing_h4_within1R": int(group.loc[~group.stopped].opposing_h4_barrier_R.le(1).sum())})
pd.DataFrame(summaries).to_csv(OUT / "direction_summary.csv", index=False)
feature_columns = ["entry_delta_signed", "entry_delta24_signed", "entry_volume_ratio", "entry_change24_signed_pct",
                   "entry_trend_efficiency24", "entry_ema24_72_separation_atr_signed", "entry_ema168_slope24_atr_signed",
                   "entry_oi24_change_pct", "risk_atr", "opposing_h4_barrier_R"]
comparison = details.groupby(["side", "stopped"])[feature_columns].median().reset_index()
comparison.to_csv(OUT / "entry_feature_medians_by_outcome.csv", index=False)
verification = {"baseline_hashes_unchanged": all(digest(SRC / p) == sha for p, sha in manifest["baseline_hashes"].items()),
                "all_26_trades_accounted": len(details) == 26, "all_16_stops_accounted": int(details.stopped.sum()) == 16,
                "observed_pre_terminal_mfe_excludes_stop_minute_order_ambiguity": True,
                "h4_references_causal": bool((details.opposing_h4_available_at.dropna() <= details.loc[details.opposing_h4_available_at.notna(), "decision_at"]).all()),
                "stop_1R_2R_counts_independent_of_terminal_minute_order": bool(
                    all(details.loc[details.stopped, "mfe_before_terminal_R"].ge(x).equals(
                        details.loc[details.stopped, "mfe_terminal_minute_upper_bound_R"].ge(x)) for x in [1, 2])),
                "source_code_identity_verified": True, "no_rule_promoted_or_feed_changed": True,
                "script_sha256": digest(Path(__file__))}
(OUT / "diagnostic_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")
assert all(verification[k] for k in ["baseline_hashes_unchanged", "all_26_trades_accounted", "all_16_stops_accounted", "h4_references_causal", "stop_1R_2R_counts_independent_of_terminal_minute_order"])
print(pd.DataFrame(summaries).to_string(index=False))
print(comparison.to_string(index=False))
print(details.loc[details.stopped, ["side", "entry_at", "holding_hours", "mfe_before_terminal_R", "initial_risk_usd", "entry_delta24_signed", "entry_oi24_change_pct", "early_reference_failure_within3h_before_exit", "opposing_h4_barrier_R", "post_stop_mfe_through_original_expiry_R"]].to_string(index=False))
