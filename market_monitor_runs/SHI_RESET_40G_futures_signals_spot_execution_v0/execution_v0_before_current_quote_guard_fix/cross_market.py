"""Futures-only decisions and separately clocked BTCUSDC spot price execution."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from research.own_signal_run.feed import closed_bars, usable_observations, window_is_usable
from research.strategy_search.replay import ExitRules, initial_stop


def execution_references(futures, spot, bars, native=False):
    future_raw = usable_observations(futures)
    future_raw = future_raw.loc[future_raw.DataQuality.eq("RAW"), ["Timestamp", "ClosePrice"]]
    spot_raw = spot.loc[spot.DataQuality.eq("RAW")]
    known = bars[["available_at"]].copy()
    known = pd.merge_asof(known, future_raw.rename(columns={"Timestamp": "futures_close_at", "ClosePrice": "futures_close"}),
                          left_on="available_at", right_on="futures_close_at", tolerance=pd.Timedelta(minutes=1), direction="backward")
    known = pd.merge_asof(known, spot_raw[["Timestamp", "ClosePrice"]].rename(columns={"Timestamp": "spot_close_at", "ClosePrice": "spot_close"}),
                          left_on="available_at", right_on="spot_close_at", tolerance=pd.Timedelta(minutes=1), direction="backward")
    known["basis_ratio"] = known.spot_close / known.futures_close
    valid = known.basis_ratio.between(.95, 1.05)
    out = bars.copy()
    for field in ["open", "high", "low", "close", "atr", "lower6", "upper6", "confirmed_swing_low", "confirmed_swing_high"]:
        if field in out:
            out[field] = out[field] * known.basis_ratio.where(valid)
    out["usable"] &= valid
    if native:
        records = []
        for end, group in spot_raw.groupby(spot_raw.Timestamp.dt.ceil("60min"), sort=True):
            records.append({"timestamp": end, "high": group.HiPrice.max(), "low": group.LowPrice.min(), "close": group.ClosePrice.iloc[-1],
                            "usable": window_is_usable(group, end - pd.Timedelta(minutes=59), end)})
        s = pd.DataFrame(records)
        previous = s.close.shift()
        tr = pd.concat([s.high - s.low, (s.high - previous).abs(), (s.low - previous).abs()], axis=1).max(axis=1)
        s["atr"] = tr.rolling(24, min_periods=24).mean()
        s["lower6"] = s.low.shift().rolling(6, min_periods=6).min()
        s["upper6"] = s.high.shift().rolling(6, min_periods=6).max()
        aligned = bars[["timestamp"]].merge(s, on="timestamp", how="left")
        for field in ["atr", "lower6", "upper6"]:
            out[field] = aligned[field]
        out["usable"] &= aligned.usable.fillna(False)
    return out, known


def h4_regimes(futures, bars):
    h4 = closed_bars(usable_observations(futures), 240)
    h4 = h4.loc[h4.completed].reset_index(drop=True)
    highs, lows, cursor, records = [], [], 0, []
    for _, bar in bars.iterrows():
        while cursor < len(h4) and h4.available_at.iloc[cursor] <= bar.available_at:
            if cursor >= 2:
                window = h4.iloc[cursor - 2:cursor + 1]
                if window.usable.all() and window.timestamp.diff().iloc[1:].eq(pd.Timedelta(hours=4)).all():
                    center = window.iloc[1]
                    if center.high > max(window.high.iloc[0], window.high.iloc[2]):
                        highs.append((float(center.high), h4.available_at.iloc[cursor]))
                    if center.low < min(window.low.iloc[0], window.low.iloc[2]):
                        lows.append((float(center.low), h4.available_at.iloc[cursor]))
            cursor += 1
        recent = highs[-2:] + lows[-2:]
        ready = len(highs) >= 2 and len(lows) >= 2 and all(bar.available_at - x[1] <= pd.Timedelta(days=30) for x in recent)
        regime = "UNKNOWN"
        if ready:
            up = highs[-1][0] > highs[-2][0] and lows[-1][0] > lows[-2][0]
            down = highs[-1][0] < highs[-2][0] and lows[-1][0] < lows[-2][0]
            regime = "UP" if up else "DOWN" if down else "MIXED"
        records.append({"available_at": bar.available_at, "h4_regime": regime,
                        "last_high": highs[-1][0] if highs else None, "previous_high": highs[-2][0] if len(highs) > 1 else None,
                        "last_low": lows[-1][0] if lows else None, "previous_low": lows[-2][0] if len(lows) > 1 else None,
                        "newest_reference_available_at": max(x[1] for x in recent) if recent else pd.NaT})
    return pd.DataFrame(records)


def apply_long_regime(direction, regimes, mode):
    result = direction.copy()
    if mode == "NO_DOWN":
        result[(result > 0) & regimes.h4_regime.eq("DOWN").to_numpy()] = 0
    elif mode == "UP_ONLY":
        result[(result > 0) & regimes.h4_regime.ne("UP").to_numpy()] = 0
    elif mode != "NONE":
        raise ValueError(mode)
    return result


def trade(data, i, side, rules, management="FIXED"):
    item = data.entry(i)
    if item is None:
        return None
    p, entry_ts, entry, _, _, _ = item
    stop = initial_stop(data, i, side, entry, rules)
    risk = side * (entry - stop)
    if not np.isfinite(risk) or risk <= 0 or not .004 <= risk / entry <= .04:
        return None
    initial, target = stop, entry + side * rules.target_r * risk
    expiry = entry_ts + rules.hold_hours * data.hour
    partial_mode, trail_mode = side > 0 and management == "PARTIAL_HALF_2R", side > 0 and management == "TRAIL_H1_AFTER_2R"
    remaining, fills, amendments = 1., [], []
    previous, omissions, collision = entry_ts, 0, False
    status, exit_ts, exit_price = "OPEN", None, None
    armed, reviewed, pending, trail_active = False, -1, [], False
    for m in range(p, len(data.minute_ts)):
        ts, opening_ts = data.minute_ts[m], data.minute_ts[m] - data.minute
        omitted = int((ts - previous) // data.minute) - 1
        if omitted > 1 or not data.raw[m]:
            status = "CENSORED_DATA"
            break
        previous, omissions = ts, omissions + omitted
        if ts > expiry:
            status, exit_price, exit_ts = "EXPIRY_NEXT_REAL_OPEN", data.mo[m], opening_ts
            break
        while pending and pending[0]["eligible_at"] <= opening_ts:
            action = pending.pop(0)
            stop = max(stop, action["price"])
            trail_active = True
            action["active_at"] = int(opening_ts)
        gap_stop = data.mo[m] <= stop if side > 0 else data.mo[m] >= stop
        hit_stop = data.ml[m] <= stop if side > 0 else data.mh[m] >= stop
        hit_target = data.mh[m] >= target if side > 0 else data.ml[m] <= target
        if gap_stop or hit_stop:
            status = ("TRAIL_STOP_GAP" if gap_stop else "TRAIL_STOP") if trail_active else ("STOP_GAP" if gap_stop else "STOP")
            exit_price, exit_ts, collision = data.mo[m] if gap_stop else stop, ts, bool(hit_target and not gap_stop)
            break
        # The half-size 2R limit is standing from entry. Original protective stop
        # wins any OHLC collision; favorable gaps do not improve its fill price.
        if partial_mode and remaining == 1 and data.mh[m] >= entry + 2 * risk:
            fills.append({"fraction": .5, "price": float(entry + 2 * risk), "at": int(ts), "reason": "PARTIAL_2R"})
            remaining = .5
        if hit_target:
            status, exit_price, exit_ts = "TARGET", target, ts
            break
        if ts == expiry:
            status, exit_price, exit_ts = "EXPIRY", data.mc[m], ts
            break
        if trail_mode:
            if (data.mh[m] - entry) / risk >= 2:
                armed = True
            j = int(np.searchsorted(data.available, ts, side="right")) - 1
            if armed and j > reviewed:
                reviewed = j
                level = data.bars.confirmed_swing_low.iloc[j] * .9995
                current = data.bars.close.iloc[j]
                highest = max([stop] + [x["price"] for x in pending])
                if data.usable[j] and np.isfinite(level) and highest < level < current:
                    action = {"decision_at": int(ts), "reference_at": int(data.available[j]), "eligible_at": int(ts + data.minute), "price": float(level), "active_at": None}
                    pending.append(action)
                    amendments.append(action)
    if exit_price is None and status == "OPEN":
        status = "CENSORED_TAIL"
    quantity = 3000 / entry
    if exit_price is not None:
        fills.append({"fraction": remaining, "price": float(exit_price), "at": int(exit_ts), "reason": status})
        assert abs(sum(x["fraction"] for x in fills) - 1) < 1e-12
        weighted_exit = sum(x["fraction"] * x["price"] for x in fills)
        gross = side * (weighted_exit - entry) * quantity
        slippage = (entry + weighted_exit) * quantity * .0002
        net = gross - 5 - slippage
    else:
        weighted_exit, gross, slippage, net = None, None, None, None
    utc = lambda t: pd.Timestamp(t, tz="UTC") if t is not None else pd.NaT
    return {"signal_index": i, "direction": side, "decision_at": utc(data.available[i]), "entry_at": utc(entry_ts), "entry_price": entry,
            "stop_price": initial, "target_price": target, "initial_risk_usd": quantity * risk, "target_R": rules.target_r,
            "exit_at": utc(exit_ts), "exit_price": exit_price, "exit_reason": status, "gross_usd": gross,
            "commission_usd": 5 if exit_price is not None else None, "slippage_usd": slippage, "net_usd": net,
            "net_R": net / (quantity * risk) if net is not None else None, "same_bar_collision": collision,
            "omitted_minutes": omissions, "precise_minute_replay": True, "censored": exit_price is None,
            "short_gap_conservative_mark": False, "gap_policy": "CENSOR", "expiry_at": utc(expiry),
            "weighted_exit_price": weighted_exit, "partial_filled": len(fills) > 1,
            "fills_json": json.dumps(fills, sort_keys=True), "amendments_json": json.dumps(amendments, sort_keys=True), "final_stop_price": stop}


def portfolio(data, directions, spec, management="FIXED"):
    rows, busy = [], -1
    for i in np.flatnonzero(directions):
        if data.available[i] + data.minute <= busy:
            continue
        side = int(directions[i])
        config = spec["long" if side > 0 else "short"]
        result = trade(data, int(i), side, ExitRules(**config["exit"]), management)
        if result is None:
            continue
        result["family"] = config["family"]
        rows.append(result)
        end = result["expiry_at"] if result["censored"] else result["exit_at"]
        busy = end.value + 3 * data.minute
    return pd.DataFrame(rows)
