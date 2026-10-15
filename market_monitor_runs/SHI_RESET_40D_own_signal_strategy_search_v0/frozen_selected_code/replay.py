from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.own_signal_run.feed import usable_observations


@dataclass(frozen=True)
class ExitRules:
    stop_lookback: int
    atr_floor: float
    target_r: float
    trail_atr: float
    hold_hours: int


class ReplayData:
    def __init__(self, feed: pd.DataFrame, bars: pd.DataFrame):
        self.feed = usable_observations(feed)
        self.bars = bars
        self.minute_ts = pd.DatetimeIndex(self.feed.Timestamp).asi8
        self.times = pd.DatetimeIndex(bars.timestamp).asi8
        self.available = pd.DatetimeIndex(bars.available_at).asi8
        self.open = bars.open.to_numpy()
        self.high = bars.high.to_numpy()
        self.low = bars.low.to_numpy()
        self.close = bars.close.to_numpy()
        self.atr = bars.atr.to_numpy()
        self.usable = bars.usable.to_numpy()
        self.raw = self.feed.DataQuality.eq("RAW").to_numpy()
        self.mo = self.feed.OpenPrice.to_numpy()
        self.mh = self.feed.HiPrice.to_numpy()
        self.ml = self.feed.LowPrice.to_numpy()
        self.mc = self.feed.ClosePrice.to_numpy()
        self.entries: dict[int, tuple] = {}
        self.minute = 60_000_000_000
        self.hour = 60 * self.minute

    def entry(self, i: int) -> tuple | None:
        if i in self.entries:
            return self.entries[i]
        planned = self.available[i] + 2 * self.minute
        p = int(np.searchsorted(self.minute_ts, planned))
        if p >= len(self.minute_ts) or self.minute_ts[p] - planned > self.minute or not self.raw[p]:
            self.entries[i] = None
            return None
        if i + 1 >= len(self.times):
            return None
        end = int(np.searchsorted(self.minute_ts, self.times[i + 1], side="right"))
        stamps = np.r_[self.minute_ts[p] - self.minute, self.minute_ts[p:end]]
        quality = bool(self.raw[p:end].all() and len(stamps) > 1 and np.diff(stamps).max() <= 2 * self.minute)
        item = (p, self.minute_ts[p] - self.minute, self.mo[p], self.mh[p:end].max(), self.ml[p:end].min(), quality)
        self.entries[i] = item
        return item


def initial_stop(data: ReplayData, i: int, side: int, entry: float, rules: ExitRules) -> float:
    bars = data.bars
    field = f"lower{rules.stop_lookback}" if side == 1 else f"upper{rules.stop_lookback}"
    structural = float(bars.iloc[i][field])
    if side == 1:
        return min(structural * 0.9995, entry - data.atr[i] * rules.atr_floor)
    return max(structural * 1.0005, entry + data.atr[i] * rules.atr_floor)


def trade_path(data: ReplayData, i: int, side: int, rules: ExitRules, precise: bool = False, gap_policy: str = "CENSOR") -> dict | None:
    if gap_policy not in {"CENSOR", "STOP_BOUND_PRIMARY_SHORT_GAP"}:
        raise ValueError("Undeclared gap scenario")
    item = data.entry(i)
    if item is None:
        return None
    p, entry_ts, entry, first_high, first_low, first_quality = item
    stop = initial_stop(data, i, side, entry, rules)
    risk = side * (entry - stop)
    if not np.isfinite(risk) or risk <= 0 or not 0.004 <= risk / entry <= 0.04:
        return None
    target = entry + side * rules.target_r * risk if rules.target_r else None
    initial = stop
    expiry = entry_ts + rules.hold_hours * data.hour
    status, exit_price, exit_ts, omissions, collision = "OPEN", None, None, 0, False

    def touch(open_price, high, low):
        nonlocal status, exit_price, collision
        gap_stop = open_price <= stop if side == 1 else open_price >= stop
        hit_stop = low <= stop if side == 1 else high >= stop
        hit_target = target is not None and (high >= target if side == 1 else low <= target)
        if gap_stop:
            status, exit_price = "STOP_GAP", open_price
        elif hit_stop:
            status, exit_price, collision = "STOP", stop, bool(hit_target)
        elif hit_target:
            status, exit_price = "TARGET", target

    if precise:
        previous = entry_ts
        h1_cursor = i + 1
        for m in range(p, len(data.minute_ts)):
            ts = data.minute_ts[m]
            omitted = int((ts - previous) // data.minute) - 1
            if omitted > 1 or not data.raw[m]:
                if gap_policy == "STOP_BOUND_PRIMARY_SHORT_GAP" and 2 <= omitted <= 5 and data.raw[m]:
                    # Stress mark, NOT evidence that the unobserved stop was filled.
                    # Debit the worse of known protective stop and next observed open.
                    status = "CONSERVATIVE_SHORT_GAP_STOP_BOUND"
                    exit_price = min(stop, data.mo[m]) if side == 1 else max(stop, data.mo[m])
                    exit_ts = ts - data.minute
                    omissions += omitted
                    break
                status = "CENSORED_DATA"
                break
            omissions += omitted
            previous = ts
            if ts > expiry:
                status, exit_price, exit_ts = "EXPIRY_NEXT_REAL_OPEN", data.mo[m], ts - data.minute
                break
            touch(data.mo[m], data.mh[m], data.ml[m])
            if exit_price is not None:
                exit_ts = ts
                break
            if ts == expiry:
                status, exit_price, exit_ts = "EXPIRY", data.mc[m], ts
                break
            # An H1-derived trailing amendment starts only AFTER that close.
            while h1_cursor < len(data.times) and data.available[h1_cursor] <= ts:
                if rules.trail_atr and data.usable[h1_cursor]:
                    desired = data.close[h1_cursor] - side * rules.trail_atr * data.atr[h1_cursor]
                    stop = max(stop, desired) if side == 1 else min(stop, desired)
                h1_cursor += 1
    else:
        for j in range(i + 1, min(len(data.times), i + rules.hold_hours + 1)):
            good = first_quality if j == i + 1 else data.usable[j]
            if not good:
                status = "CENSORED_DATA"
                break
            high, low = (first_high, first_low) if j == i + 1 else (data.high[j], data.low[j])
            touch(entry if j == i + 1 else data.open[j], high, low)
            if exit_price is not None:
                exit_ts = data.available[j]
                break
            if rules.trail_atr:
                desired = data.close[j] - side * rules.trail_atr * data.atr[j]
                stop = max(stop, desired) if side == 1 else min(stop, desired)
        if exit_price is None and status == "OPEN":
            final = int(np.searchsorted(data.minute_ts, expiry))
            if final >= len(data.minute_ts):
                status = "CENSORED_TAIL"
            elif data.minute_ts[final] - expiry > data.minute or not data.raw[final]:
                status = "CENSORED_DATA"
            else:
                if data.minute_ts[final] == expiry:
                    touch(data.mo[final], data.mh[final], data.ml[final])
                    if exit_price is None:
                        status, exit_price = "EXPIRY", data.mc[final]
                    exit_ts = expiry
                else:
                    status, exit_price, exit_ts = "EXPIRY_NEXT_REAL_OPEN", data.mo[final], data.minute_ts[final] - data.minute
    quantity = 3000 / entry
    gross = side * (exit_price - entry) * quantity if exit_price is not None else None
    slippage = (entry + exit_price) * quantity * 0.0002 if exit_price is not None else None
    net = gross - 5 - slippage if exit_price is not None else None
    return {"signal_index": i, "direction": side, "decision_at": pd.Timestamp(data.available[i], tz="UTC"),
            "entry_at": pd.Timestamp(entry_ts, tz="UTC"), "entry_price": entry,
            "stop_price": initial, "target_price": target, "initial_risk_usd": quantity * risk,
            "target_R": rules.target_r if target is not None else None,
            "exit_at": pd.Timestamp(exit_ts, tz="UTC") if exit_ts is not None else pd.NaT,
            "exit_price": exit_price, "exit_reason": status, "gross_usd": gross,
            "commission_usd": 5 if gross is not None else None, "slippage_usd": slippage,
            "net_usd": net, "net_R": net / (quantity * risk) if net is not None else None,
            "same_bar_collision": collision, "omitted_minutes": omissions,
            "precise_minute_replay": precise, "censored": exit_price is None,
            "short_gap_conservative_mark": status == "CONSERVATIVE_SHORT_GAP_STOP_BOUND",
            "gap_policy": gap_policy,
            "expiry_at": pd.Timestamp(expiry, tz="UTC")}


def replay(data: ReplayData, direction: np.ndarray, rules: ExitRules, precise: bool = False, cutoff: str | None = None, gap_policy: str = "CENSOR") -> pd.DataFrame:
    rows, busy = [], -1
    maximum = pd.Timestamp(cutoff).value if cutoff else data.times[-1]
    for i in np.flatnonzero(direction):
        if data.available[i] > maximum or data.available[i] + data.minute <= busy:
            continue
        trade = trade_path(data, int(i), int(direction[i]), rules, precise, gap_policy)
        if trade is None:
            continue
        rows.append(trade)
        # A censored result is retained and fails finalist qualification.
        end = trade["expiry_at"] if trade["censored"] else trade["exit_at"]
        busy = end.value + 3 * data.minute
    return pd.DataFrame(rows)


def metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"trades": 0, "censored": 0, "net_usd": 0.0, "profit_factor": 0.0, "drawdown_usd": 0.0}
    closed = trades.loc[~trades.censored].sort_values("exit_at")
    net = closed.net_usd.to_numpy()
    losses = -net[net < 0].sum()
    curve = np.r_[0, net.cumsum()]
    return {"trades": len(trades), "resolved": len(closed), "censored": int(trades.censored.sum()),
            "gross_usd": float(closed.gross_usd.sum()), "commission_usd": float(closed.commission_usd.sum()),
            "slippage_usd": float(closed.slippage_usd.sum()), "net_usd": float(net.sum()),
            "profit_factor": float(net[net > 0].sum() / losses) if losses else None,
            "drawdown_usd": float((np.maximum.accumulate(curve) - curve).max()),
            "net_without_best_three": float(net.sum() - np.sort(net)[-3:].sum()),
            "mean_net_usd": float(net.mean()) if len(net) else None,
            "mean_initial_risk_usd": float(closed.initial_risk_usd.mean()),
            "mean_net_R": float(closed.net_R.mean())}
