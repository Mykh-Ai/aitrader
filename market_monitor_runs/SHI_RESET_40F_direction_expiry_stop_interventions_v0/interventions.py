"""Isolated causal exit/entry interventions; no production policy authority."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.own_signal_run.feed import closed_bars, usable_observations
from research.strategy_search.replay import ExitRules, initial_stop


def h4_inventory(feed: pd.DataFrame, bars: pd.DataFrame) -> dict:
    h4 = closed_bars(usable_observations(feed), 240)
    h4 = h4.loc[h4.completed].reset_index(drop=True)
    levels, inventory, cursor = [], {}, 0
    for i, bar in bars.iterrows():
        while cursor < len(h4) and h4.available_at.iloc[cursor] <= bar.available_at:
            if cursor >= 2:
                window = h4.iloc[cursor - 2:cursor + 1]
                if window.usable.all() and window.timestamp.diff().iloc[1:].eq(pd.Timedelta(hours=4)).all():
                    center = window.iloc[1]
                    for side, value, valid in [
                        (1, center.high, center.high > max(window.high.iloc[0], window.high.iloc[2])),
                        (-1, center.low, center.low < min(window.low.iloc[0], window.low.iloc[2])),
                    ]:
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
        inventory[i] = [dict(x) for x in levels if x["active"] and x["available_at"] <= bar.available_at
                        and bar.available_at - x["available_at"] <= pd.Timedelta(days=30)]
    return inventory


def candidate_map(data, original: np.ndarray, spec: dict, variant: dict, inventory: dict) -> tuple[dict, list]:
    candidates, rejected = {}, []
    for source_i in np.flatnonzero(original):
        side = int(original[source_i])
        if variant.get("side") == "LONG_ONLY" and side < 0 or variant.get("side") == "SHORT_ONLY" and side > 0:
            continue
        i = int(source_i)
        if side == 1 and variant.get("long_confirm_1h"):
            i += 1
            if i >= len(original):
                continue
            bar = data.bars.iloc[i]
            previous = data.bars.iloc[source_i]
            # Newly closed H1 confirmation becomes a NEW decision; no backdating.
            forbidden = previous.available_at >= pd.Timestamp("2026-10-01T00:00:00Z") or bar.available_at >= pd.Timestamp("2026-10-01T00:00:00Z")
            if forbidden or not bar.usable or not bar.context_usable or data.available[i] - data.available[source_i] != data.hour:
                rejected.append({"source_index": int(source_i), "signal_index": i, "side": side, "reason": "CONFIRMATION_UNUSABLE"})
                continue
            if not bar.close > previous.ema24 * 1.0005:
                rejected.append({"source_index": int(source_i), "signal_index": i, "side": side, "reason": "LONG_NEXT_H1_NOT_HELD"})
                continue
            # Preserve all calendar restrictions at the new decision, not only the original.
            stamp = bar.timestamp
            excluded = any(pd.Timestamp(a, tz="UTC") <= stamp < pd.Timestamp(b, tz="UTC") for a, b in [
                ("2026-04-23T17:05", "2026-05-10"), ("2026-06-22", "2026-06-29"), ("2026-08-25", "2026-09-01")])
            if excluded:
                rejected.append({"source_index": int(source_i), "signal_index": i, "side": side, "reason": "CONFIRMATION_EXCLUDED_DATE"})
                continue
        bar = data.bars.iloc[i]
        use_space = variant.get("short_space_1r") and side == -1 or variant.get("long_space_1r") and side == 1
        blocker, space = None, None
        if use_space:
            # Filter uses the already known H1 CLOSE, not the future entry open.
            rules = ExitRules(**spec["long" if side > 0 else "short"]["exit"])
            estimated_stop = initial_stop(data, i, side, bar.close, rules)
            risk = side * (bar.close - estimated_stop)
            levels = [x for x in inventory[i] if x["side"] == side and side * (x["price"] * (.9995 if side > 0 else 1.0005) - bar.close) > 0]
            blocker = min(levels, key=lambda x: abs(x["price"] - bar.close), default=None)
            if blocker and risk > 0:
                space = side * (blocker["price"] * (.9995 if side > 0 else 1.0005) - bar.close) / risk
                assert blocker["available_at"] <= bar.available_at
            if space is not None and space < 1:
                rejected.append({"source_index": int(source_i), "signal_index": i, "side": side, "reason": "OPPOSING_H4_WITHIN_1R", "space_R": space,
                                 "reference_price": blocker["price"], "reference_available_at": blocker["available_at"], "decision_at": bar.available_at})
                continue
        candidate = {"source_index": int(source_i), "side": side, "decision_at": bar.available_at, "space_R": space,
                     "reference_price": blocker["price"] if blocker else None,
                     "reference_available_at": blocker["available_at"] if blocker else pd.NaT}
        if i in candidates and candidates[i]["side"] != side:
            candidates[i] = {"side": 0}
        elif i not in candidates:
            candidates[i] = candidate
    return {i: row for i, row in candidates.items() if row["side"]}, rejected


def intervention_path(data, i: int, side: int, rules: ExitRules, early_reference_hours: int = 0,
                      lock_trigger_r: float = 0.0, lock_stop_r: float = .25) -> dict | None:
    item = data.entry(i)
    if item is None:
        return None
    p, entry_ts, entry, _, _, _ = item
    stop = initial_stop(data, i, side, entry, rules)
    risk = side * (entry - stop)
    if not np.isfinite(risk) or risk <= 0 or not .004 <= risk / entry <= .04:
        return None
    initial = stop
    target = entry + side * rules.target_r * risk
    expiry = entry_ts + rules.hold_hours * data.hour
    reference = float(data.bars.ema24.iloc[i]) if side == 1 else float(data.bars.lower48.iloc[i - 1])
    status, exit_price, exit_ts, exit_clock = "OPEN", None, None, "MINUTE_CLOSE"
    omissions, collision, previous, h1_cursor = 0, False, entry_ts, i + 1
    pending_exit, pending_stop, lock_armed, lock_active = None, None, False, False
    exit_decision, amendment_decision, amendment_active = None, None, None
    for m in range(p, len(data.minute_ts)):
        ts, opening_ts = data.minute_ts[m], data.minute_ts[m] - data.minute
        omitted = int((ts - previous) // data.minute) - 1
        if omitted > 1 or not data.raw[m]:
            status = "CENSORED_DATA"
            break
        omissions += omitted
        previous = ts
        if ts > expiry:
            status, exit_price, exit_ts, exit_clock = "EXPIRY_NEXT_REAL_OPEN", data.mo[m], opening_ts, "MINUTE_OPEN"
            break
        if pending_stop is not None and opening_ts >= pending_stop[0]:
            desired = pending_stop[1]
            stop = max(stop, desired) if side > 0 else min(stop, desired)
            lock_active, amendment_active, pending_stop = True, opening_ts, None
        gap_stop = data.mo[m] <= stop if side > 0 else data.mo[m] >= stop
        gap_target = data.mo[m] >= target if side > 0 else data.mo[m] <= target
        if pending_exit is not None and opening_ts >= pending_exit:
            # Only open prices are known at a scheduled market exit. Do not use
            # later high/low of that minute to force an earlier protective fill.
            if gap_stop:
                status, exit_price = ("LOCK_STOP_GAP" if lock_active else "STOP_GAP"), data.mo[m]
            elif gap_target:
                status, exit_price = "TARGET", target
            else:
                status, exit_price = "REFERENCE_INVALIDATION", data.mo[m]
            exit_ts, exit_clock = opening_ts, "MINUTE_OPEN"
            break
        hit_stop = data.ml[m] <= stop if side > 0 else data.mh[m] >= stop
        hit_target = data.mh[m] >= target if side > 0 else data.ml[m] <= target
        if gap_stop:
            status, exit_price = ("LOCK_STOP_GAP" if lock_active else "STOP_GAP"), data.mo[m]
        elif hit_stop:
            status, exit_price, collision = ("LOCK_STOP" if lock_active else "STOP"), stop, bool(hit_target)
        elif hit_target:
            status, exit_price = "TARGET", target
        if exit_price is not None:
            exit_ts = ts
            break
        if ts == expiry:
            status, exit_price, exit_ts = "EXPIRY", data.mc[m], ts
            break
        # A favorable minute is evidence only at its close. Amendment is active
        # at the next real open no earlier than close+one minute, never same-bar.
        favorable = side * ((data.mh[m] if side > 0 else data.ml[m]) - entry) / risk
        if lock_trigger_r and not lock_armed and favorable >= lock_trigger_r:
            pending_stop = (ts + data.minute, entry + side * lock_stop_r * risk)
            lock_armed, amendment_decision = True, ts
        while h1_cursor < len(data.times) and data.available[h1_cursor] <= ts:
            when = data.available[h1_cursor]
            if early_reference_hours and when <= data.available[i] + early_reference_hours * data.hour and data.usable[h1_cursor]:
                invalid = data.close[h1_cursor] < reference * .9995 if side > 0 else data.close[h1_cursor] > reference * 1.0005
                if invalid and pending_exit is None:
                    pending_exit, exit_decision = when + data.minute, when
            h1_cursor += 1
    if exit_price is None and status == "OPEN":
        status = "CENSORED_TAIL"
    quantity = 3000 / entry
    gross = side * (exit_price - entry) * quantity if exit_price is not None else None
    slippage = (entry + exit_price) * quantity * .0002 if exit_price is not None else None
    net = gross - 5 - slippage if gross is not None else None
    utc = lambda value: pd.Timestamp(value, tz="UTC") if value is not None else pd.NaT
    return {"signal_index": i, "direction": side, "decision_at": utc(data.available[i]), "entry_at": utc(entry_ts),
            "entry_price": entry, "stop_price": initial, "target_price": target, "initial_risk_usd": risk * quantity,
            "target_R": rules.target_r, "exit_at": utc(exit_ts), "exit_price": exit_price, "exit_reason": status,
            "gross_usd": gross, "commission_usd": 5 if gross is not None else None, "slippage_usd": slippage,
            "net_usd": net, "net_R": net / (risk * quantity) if net is not None else None,
            "same_bar_collision": collision, "omitted_minutes": omissions, "precise_minute_replay": True,
            "censored": exit_price is None, "short_gap_conservative_mark": False, "gap_policy": "CENSOR", "expiry_at": utc(expiry),
            "exit_price_clock": exit_clock, "exit_decision_at": utc(exit_decision), "stop_amendment_decision_at": utc(amendment_decision),
            "stop_amendment_active_at": utc(amendment_active), "final_stop_price": stop, "lock_armed": lock_armed, "lock_active": lock_active}


def portfolio(data, original, spec, variant, inventory):
    candidates, rejected = candidate_map(data, original, spec, variant, inventory)
    rows, busy = [], -1
    for i, candidate in sorted(candidates.items()):
        side = candidate["side"]
        if data.available[i] + data.minute <= busy:
            continue
        config = spec["long" if side > 0 else "short"]
        exits = dict(config["exit"])
        exits["hold_hours"] = variant.get("hold_hours", exits["hold_hours"])
        early = 3 if variant.get("long_invalidate_3h") and side > 0 or variant.get("short_invalidate_3h") and side < 0 else 0
        trigger = 1 if variant.get("short_lock") and side < 0 else 0
        trade = intervention_path(data, i, side, ExitRules(**exits), early, trigger)
        if trade is None:
            continue
        trade.update({"family": config["family"], "variant": variant["id"], **{k: v for k, v in candidate.items() if k not in ["side", "decision_at"]}})
        rows.append(trade)
        end = trade["expiry_at"] if trade["censored"] else trade["exit_at"]
        busy = end.value + 3 * data.minute
    return pd.DataFrame(rows), pd.DataFrame(rejected)
