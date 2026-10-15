"""Dollar accounting and an independent chronological first-touch verifier."""
import numpy as np
import pandas as pd


def metrics(trades):
    closed = trades.loc[trades.status_at_cutoff.eq("CLOSED")].sort_values("exit_at")
    net = closed.net_usd.to_numpy(dtype=float)
    gains, losses = net[net > 0].sum(), -net[net < 0].sum()
    curve = np.r_[0., net.cumsum()]
    ranked = np.sort(net)[::-1]
    average = lambda values: float(values.mean()) if len(values) else None
    result = {
        "entered_trades": len(trades), "completed_trades": len(closed),
        "open_at_cutoff": int(trades.status_at_cutoff.eq("OPEN_AT_CUTOFF").sum()),
        "data_censored": int(trades.status_at_cutoff.eq("CENSORED_DATA").sum()),
        "LONG_count": int(trades.direction.gt(0).sum()), "SHORT_count": int(trades.direction.lt(0).sum()),
        "wins": int((net > 0).sum()), "losses": int((net < 0).sum()), "flat": int((net == 0).sum()),
        "expiries": int(closed.exit_reason.str.startswith("EXPIRY").sum()),
        "targets": int(closed.exit_reason.eq("TARGET").sum()), "stops": int(closed.exit_reason.str.startswith("STOP").sum()),
        "gross_usd": float(closed.gross_usd.sum()), "commission_usd": float(closed.commission_usd.sum()),
        "modeled_slippage_usd": float(closed.slippage_usd.sum()), "net_usd": float(net.sum()),
        "profit_factor": float(gains / losses) if losses else "INFINITE" if gains else 0.,
        "average_trade_usd": average(closed.net_usd),
        "median_trade_usd": float(np.median(net)) if len(net) else None,
        "max_closed_trade_drawdown_usd": float((np.maximum.accumulate(curve) - curve).max()),
        "best_trade_usd": float(ranked[0]) if len(ranked) else None,
        "worst_trade_usd": float(ranked[-1]) if len(ranked) else None,
        "LONG_net_usd": float(closed.loc[closed.direction.gt(0), "net_usd"].sum()),
        "SHORT_net_usd": float(closed.loc[closed.direction.lt(0), "net_usd"].sum()),
        "average_initial_risk_usd": average(closed.initial_risk_usd),
        "average_initial_risk_distance_pct": average(closed.initial_risk_usd / 3000 * 100),
        "average_initial_risk_distance_price": average((closed.entry_price - closed.stop_price).abs()),
        "average_target_R": average(closed.target_R), "average_net_R": average(closed.net_R),
        "average_target_distance_pct": average((closed.target_price / closed.entry_price - 1).abs() * 100),
        "notional_per_trade_usd_equivalent": 3000, "commission_per_completed_trade": 5,
        "slippage_bps_per_fill": 2, "execution_market": "FUTURES_PRICE_PROXY",
        "funding_charged": False, "borrow_interest_charged": False,
    }
    for count in [1, 2, 3]:
        best = float(ranked[:count].sum())
        result[f"best_{count}_contribution_usd"] = best
        result[f"net_excluding_best_{count}_usd"] = float(net.sum() - best)
    if len(net):
        result["net_R_quantiles"] = {str(q): float(closed.net_R.quantile(q)) for q in [0, .25, .5, .75, 1]}
    else:
        result["net_R_quantiles"] = {}
    return result


def at_cutoff(trades, cutoff):
    result = trades.loc[trades.entry_at.le(cutoff)].copy()
    future_exit = result.exit_at.gt(cutoff)
    failure_at = pd.to_datetime(result.get("censor_detected_at", pd.Series(pd.NaT, index=result.index)), utc=True)
    later_unresolved = result.censored & result.expiry_at.gt(cutoff) & (
        result.status_at_cutoff.eq("OPEN_AT_CUTOFF") | failure_at.gt(cutoff))
    result.loc[future_exit | later_unresolved, "status_at_cutoff"] = "OPEN_AT_CUTOFF"
    # Never expose later exit amounts in the earlier-period ledger.
    later = future_exit | later_unresolved
    for col in ["exit_at", "exit_price", "gross_usd", "commission_usd", "slippage_usd", "net_usd", "net_R"]:
        result.loc[later, col] = pd.NaT if col == "exit_at" else np.nan
    result.loc[later, "exit_reason"] = "OPEN_AT_EARLIER_CUTOFF"
    result.loc[later, "censored"] = True
    if "censor_detected_at" in result:
        result.loc[later, "censor_detected_at"] = pd.NaT
    return result


def monthly(trades, start, end):
    records = []
    entry_month = trades.entry_at.dt.strftime("%Y-%m")
    for stamp in pd.date_range(pd.Timestamp(start).normalize().replace(day=1),
                               pd.Timestamp(end).normalize().replace(day=1), freq="MS"):
        name = stamp.strftime("%Y-%m")
        group = trades.loc[entry_month.eq(name)]
        m = metrics(group)
        records.append({"entry_month_utc": name, **{key: m[key] for key in [
            "entered_trades", "completed_trades", "wins", "losses", "open_at_cutoff", "data_censored",
            "LONG_count", "SHORT_count", "gross_usd", "commission_usd", "modeled_slippage_usd", "net_usd",
            "LONG_net_usd", "SHORT_net_usd", "targets", "stops", "expiries"]}})
    return pd.DataFrame(records)


def verify_paths(trades, data, final):
    """Independent first-event vectors; no second strategy/financial replay."""
    verified = []
    previous_exit = None
    for r in trades.itertuples():
        assert final[r.signal_index] == r.direction
        assert r.entry_at > r.decision_at
        if previous_exit is not None:
            assert r.entry_at > previous_exit + pd.Timedelta(minutes=3)
        previous_exit = r.expiry_at if r.censored else r.exit_at
        p = int(np.searchsorted(data.minute_ts, r.decision_at.value + 2 * data.minute))
        assert pd.Timestamp(data.minute_ts[p] - data.minute, tz="UTC") == r.entry_at
        assert data.mo[p] == r.entry_price
        end = min(len(data.minute_ts), int(np.searchsorted(data.minute_ts, r.expiry_at.value, side="right")) + 1)
        stamps = data.minute_ts[p:end]
        op, hi, lo, cl = data.mo[p:end], data.mh[p:end], data.ml[p:end], data.mc[p:end]
        gaps = np.diff(np.r_[r.entry_at.value, stamps]) > 2 * data.minute
        gaps |= ~data.raw[p:end]
        stop = lo <= r.stop_price if r.direction > 0 else hi >= r.stop_price
        target = hi >= r.target_price if r.direction > 0 else lo <= r.target_price
        events = np.flatnonzero(gaps | stop | target | (stamps >= r.expiry_at.value))
        price, when = None, None
        reason = "OPEN"
        if len(events):
            j = int(events[0])
            if gaps[j]:
                reason = "CENSORED_DATA"
            elif stamps[j] > r.expiry_at.value:
                reason, price, when = "EXPIRY_NEXT_REAL_OPEN", op[j], stamps[j] - data.minute
            elif (op[j] <= r.stop_price if r.direction > 0 else op[j] >= r.stop_price):
                reason, price, when = "STOP_GAP", op[j], stamps[j]
            elif stop[j]:
                reason, price, when = "STOP", r.stop_price, stamps[j]
            elif target[j]:
                reason, price, when = "TARGET", r.target_price, stamps[j]
            else:
                reason, price, when = "EXPIRY", cl[j], stamps[j]
        assert reason == r.exit_reason, (r.signal_index, reason, r.exit_reason)
        if price is None:
            assert r.censored and pd.isna(r.net_usd)
        else:
            assert abs(price - r.exit_price) < 1e-8
            assert pd.Timestamp(when, tz="UTC") == r.exit_at
            qty = 3000 / r.entry_price
            gross = r.direction * (price - r.entry_price) * qty
            slip = (r.entry_price + price) * qty * .0002
            assert abs(gross - r.gross_usd) < 1e-8
            assert abs(slip - r.slippage_usd) < 1e-8
            assert abs(gross - 5 - slip - r.net_usd) < 1e-8
        risk = r.direction * (r.entry_price - r.stop_price)
        assert .004 <= risk / r.entry_price <= .04
        assert abs(r.initial_risk_usd - 3000 / r.entry_price * risk) < 1e-8
        assert abs(r.target_price - (r.entry_price + r.direction * r.target_R * risk)) < 1e-8
        verified.append({"signal_index": r.signal_index, "exit_reason": reason, "first_touch_and_cash_verified": True,
                         "censor_detected_at": pd.Timestamp(stamps[int(events[0])], tz="UTC") if reason == "CENSORED_DATA" else None})
    return verified


def markdown(frame):
    def display(value):
        return f"{value:.2f}" if isinstance(value, (float, np.floating)) else str(value)
    header = "| " + " | ".join(map(str, frame.columns)) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = ["| " + " | ".join(display(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *rows])
