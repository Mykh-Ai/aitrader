"""Isolated, fixed-exit research replay. Never imports or enables live execution."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .contracts import validate_signal
from .feed import usable_observations

LEDGER_COLUMNS = ["candidate_id", "family", "entry_open_at", "direction", "decision_at", "entry_raw_close_label",
                  "entry_price_raw", "stop_price", "target_price", "risk_price_distance", "expiry_at", "exit_at",
                  "exit_price_raw", "exit_reason", "same_minute_collision", "censored", "period", "cost_scenario",
                  "execution_market", "gross_R", "fee_R", "slippage_R", "assumed_carry_R", "net_R",
                  "entry_price_effective", "exit_price_effective"]
LEDGER_COLUMNS += ["planned_entry_open_at", "entry_omitted_minutes", "trade_omitted_minutes"]
ADMISSION_COLUMNS = ["candidate_id", "family", "entry_open_at", "planned_entry_open_at", "entry_omitted_minutes", "admitted", "reason"]


def apply_costs(entry: float, exit_price: float, risk: float, direction: str, hours: float, cost: dict) -> dict:
    sign = 1 if direction == "LONG" else -1
    slip = cost["slippage_bps_per_fill"] / 10000
    entry_effective, exit_effective = entry * (1 + sign * slip), exit_price * (1 - sign * slip)
    fees = (entry_effective + exit_effective) * cost["fee_bps_per_fill"] / 10000
    slippage = (entry + exit_price) * slip
    carry = entry * hours * cost["adverse_carry_bps_per_hour"] / 10000
    gross = sign * (exit_price - entry)
    return {"gross_R": gross / risk, "fee_R": fees / risk, "slippage_R": slippage / risk,
            "assumed_carry_R": carry / risk, "net_R": (gross - fees - slippage - carry) / risk,
            "entry_price_effective": entry_effective, "exit_price_effective": exit_effective}


def replay_signals(feed: pd.DataFrame, decisions: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    if feed.Timestamp.duplicated().any() or not feed.Timestamp.is_monotonic_increasing:
        raise ValueError("Replay requires ordered unique feed")
    feed = usable_observations(feed)
    if decisions.empty:
        return pd.DataFrame(columns=LEDGER_COLUMNS), pd.DataFrame(columns=ADMISSION_COLUMNS)
    accepted = decisions[decisions.accepted.astype(str).str.lower().eq("true")].copy()
    if accepted.candidate_id.duplicated().any():
        raise ValueError("Duplicate candidate identity")
    accepted = accepted.sort_values(["entry_open_at", "family", "candidate_id"], kind="stable")
    busy: dict[str, pd.Timestamp] = {}
    ledger, admission = [], []
    index = pd.Index(feed.Timestamp)
    for signal in accepted.to_dict("records"):
        validate_signal(signal, config)
        planned_entry = pd.Timestamp(signal["entry_open_at"])
        entry_ts = planned_entry
        family = signal["family"]
        base = {"candidate_id": signal["candidate_id"], "family": family, "entry_open_at": entry_ts.isoformat(),
                "planned_entry_open_at": planned_entry.isoformat(), "entry_omitted_minutes": 0}
        raw_label = entry_ts + pd.Timedelta(minutes=1)
        position = index.searchsorted(raw_label, side="left")
        if position >= len(feed) or feed.Timestamp.iloc[position] - raw_label > pd.Timedelta(minutes=1):
            admission.append({**base, "admitted": False, "reason": "MISSING_EXACT_ENTRY_MINUTE"})
            continue
        first = feed.iloc[position]
        if first.DataQuality != "RAW":
            admission.append({**base, "admitted": False, "reason": "DEGRADED_ENTRY_MINUTE"})
            continue
        entry_omissions = int((first.Timestamp - raw_label).total_seconds() / 60)
        raw_label, entry_ts = first.Timestamp, first.Timestamp - pd.Timedelta(minutes=1)
        base.update(entry_open_at=entry_ts.isoformat(), entry_omitted_minutes=entry_omissions)
        if family in busy and entry_ts <= busy[family]:
            admission.append({**base, "admitted": False, "reason": "FAMILY_POSITION_ALREADY_OPEN"})
            continue
        entry, stop, target = float(first.OpenPrice), float(signal["stop_price"]), float(signal["target_price"])
        risk = abs(entry - stop)
        geometry = stop < entry < target if signal["direction"] == "LONG" else target < entry < stop
        if not geometry or risk <= 0 or abs(target - entry) / risk < config["minimum_target_r"]:
            admission.append({**base, "admitted": False, "reason": "ENTRY_GEOMETRY_FAILED"})
            continue
        expiry = entry_ts + pd.Timedelta(hours=config["expiry_hours"])
        previous_close = entry_ts
        trade_omissions = 0
        exit_ts, exit_price, status, collision, censored = None, None, "OPEN", False, False
        for j in range(position, len(feed)):
            bar = feed.iloc[j]
            omitted = int((bar.Timestamp - previous_close).total_seconds() / 60) - 1
            if omitted > 1 or bar.DataQuality != "RAW":
                status, censored = "UNRESOLVED_DATA_GAP_OR_DEGRADED", True
                break
            trade_omissions += omitted
            previous_close = bar.Timestamp
            long = signal["direction"] == "LONG"
            gap_stop = bar.OpenPrice <= stop if long else bar.OpenPrice >= stop
            hit_stop = bar.LowPrice <= stop if long else bar.HiPrice >= stop
            hit_target = bar.HiPrice >= target if long else bar.LowPrice <= target
            if bar.Timestamp > expiry:
                exit_price, status = float(bar.OpenPrice), "EXPIRY_AFTER_SINGLE_MINUTE_SKIP"
                exit_ts = bar.Timestamp - pd.Timedelta(minutes=1)
            elif gap_stop:
                exit_price, status = float(bar.OpenPrice), "STOP_GAP_AT_OPEN"
            elif hit_stop:
                exit_price, status, collision = stop, "STOP", bool(hit_target)
            elif hit_target:
                exit_price, status = target, "TARGET"
            elif bar.Timestamp >= expiry:
                exit_price, status = float(bar.ClosePrice), "EXPIRY"
            if exit_price is not None:
                if exit_ts is None:
                    exit_ts = bar.Timestamp
                break
        if exit_ts is None:
            censored = True
            if status == "OPEN":
                status = "UNRESOLVED_END_OF_FEED"
            busy[family] = feed.Timestamp.max() + pd.Timedelta(minutes=1)
        else:
            busy[family] = exit_ts
        admission.append({**base, "admitted": True, "reason": ""})
        period = next((x["name"] for x in config["periods"] if pd.Timestamp(x["start"]) <= pd.Timestamp(signal["decision_at"]) < pd.Timestamp(x["end"])), "OUTSIDE_PERIOD")
        for cost in config["cost_scenarios"]:
            values = apply_costs(entry, exit_price, risk, signal["direction"], (exit_ts - entry_ts).total_seconds() / 3600, cost) if exit_ts is not None else {}
            ledger.append({**base, "direction": signal["direction"], "decision_at": signal["decision_at"],
                           "entry_raw_close_label": raw_label.isoformat(), "entry_price_raw": entry,
                           "stop_price": stop, "target_price": target, "risk_price_distance": risk,
                           "expiry_at": expiry.isoformat(), "exit_at": exit_ts.isoformat() if exit_ts is not None else "",
                           "exit_price_raw": exit_price, "exit_reason": status, "same_minute_collision": collision,
                           "censored": censored, "period": period, "cost_scenario": cost["id"],
                           "execution_market": config["execution_market"], "trade_omitted_minutes": trade_omissions, **values})
    return pd.DataFrame(ledger, columns=LEDGER_COLUMNS), pd.DataFrame(admission, columns=ADMISSION_COLUMNS)


def summarize(ledger: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    if ledger.empty and config is None:
        return pd.DataFrame()
    rows = []
    for (family, cost, period), group in ledger.groupby(["family", "cost_scenario", "period"], sort=True):
        closed = group[~group.censored].sort_values(["exit_at", "candidate_id"], kind="stable")
        net = closed.net_R.astype(float) if not closed.empty else pd.Series(dtype=float)
        curve = np.r_[0.0, net.cumsum().to_numpy()]
        gains, losses = net[net > 0].sum(), -net[net < 0].sum()
        top = net.sort_values(ascending=False).head(3).sum()
        rows.append({"family": family, "cost_scenario": cost, "period": period, "admitted": len(group),
                     "resolved": len(closed), "censored": int(group.censored.sum()),
                     "net_R_sum": float(net.sum()) if len(net) else None,
                     "net_R_mean": float(net.mean()) if len(net) else None,
                     "profit_factor": float(gains / losses) if losses > 0 else None,
                     "max_drawdown_R": float((np.maximum.accumulate(curve) - curve).max()),
                     "net_R_without_best_three": float(net.sum() - top) if len(net) else None,
                     "sample_status": "INSUFFICIENT_SAMPLE" if len(net) < 30 else "DESCRIPTIVE_ONLY_NO_EDGE_PROMOTION",
                     "single_minute_omissions": int(group.trade_omitted_minutes.sum() + group.entry_omitted_minutes.sum()),
                     "data_complete": bool(group.censored.sum() == 0 and group.trade_omitted_minutes.sum() == 0 and group.entry_omitted_minutes.sum() == 0),
                     "interpretation": "INDEPENDENT_FAMILY_R_BOOK_NOT_ACCOUNT_EQUITY"})
    if config is not None:
        present = {(x["family"], x["cost_scenario"], x["period"]) for x in rows}
        for family in config["families"]:
            for cost in config["cost_scenarios"]:
                for period in config["periods"]:
                    key = family, cost["id"], period["name"]
                    if "CONTEXT_ONLY" in period["name"] or key in present:
                        continue
                    rows.append({"family": family, "cost_scenario": cost["id"], "period": period["name"],
                                 "admitted": 0, "resolved": 0, "censored": 0, "net_R_sum": 0.0,
                                 "net_R_mean": None, "profit_factor": None, "max_drawdown_R": 0.0,
                                 "net_R_without_best_three": None, "sample_status": "NO_TRADES",
                                 "single_minute_omissions": 0, "data_complete": True, "interpretation": "INDEPENDENT_FAMILY_R_BOOK_NOT_ACCOUNT_EQUITY"})
    return pd.DataFrame(rows)
