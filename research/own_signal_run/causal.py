"""Three frozen research hypotheses using causal structure and 37E/38M primitives.

This is a new bounded experiment, not regeneration/promotion of 38V or 38S.
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd

from market_monitor.market_structure_state import _classify_state, _window_metrics
from market_monitor.qualified_h1_sweep_reclaim import evaluate_qualified_h1_sweep_reclaim_at
from .feed import closed_bars, usable_observations, window_is_usable


def identity(values: object) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()[:24]


def band(level: dict | None) -> pd.Series:
    if level is None:
        return pd.Series(dtype=object)
    return pd.Series({"price_lower": level["lower"], "price_upper": level["upper"], "strength_score": level["strength"]})


class CausalSignalEngine:
    """One instance per chronology; chunk calls retain all memory and emitted ids."""

    def __init__(self, feed: pd.DataFrame, contract: dict):
        if feed.empty or feed.Timestamp.duplicated().any() or not feed.Timestamp.is_monotonic_increasing:
            raise ValueError("Chronological unique nonempty feed required")
        self.history_start = feed.Timestamp.iloc[0]
        self.feed, self.contract = usable_observations(feed), contract
        if self.feed.empty:
            raise ValueError("No usable observations")
        self.h1, self.h4 = closed_bars(self.feed, 60), closed_bars(self.feed, 240)
        self.levels: dict[str, dict] = {}
        self.pending: list[dict] = []
        self.previous_states: list[str] = []
        self.seen: set[tuple] = set()
        self.decisions: list[dict] = []
        self.timeline: list[dict] = []
        self.cursor, self.h4_cursor = 0, 0

    def _confirm(self, bars: pd.DataFrame, index: int, timeframe: str, radius: int) -> None:
        if index < 2 * radius:
            return
        window = bars.iloc[index - 2 * radius:index + 1]
        hours = 1 if timeframe == "H1" else 4
        if not window.usable.all() or not window.timestamp.diff().iloc[1:].eq(pd.Timedelta(hours=hours)).all():
            return
        center = window.iloc[radius]
        other = window.drop(window.index[radius])
        for side, field, valid in [
            ("BUY_SIDE", "high", center.high > other.high.max()),
            ("SELL_SIDE", "low", center.low < other.low.min()),
        ]:
            if not valid:
                continue
            price, available = float(center[field]), bars.iloc[index].available_at
            key = identity([timeframe, side, center.timestamp, price])
            width = self.contract["zone_half_width_bps"] / 10000
            self.levels.setdefault(key, {"id": key, "side": side, "timeframe": timeframe, "price": price,
                                        "lower": price * (1 - width), "upper": price * (1 + width),
                                        "center_at": center.timestamp, "available_at": available,
                                        "strength": 75 if timeframe == "H4" else 65,
                                        "status": "ACTIVE", "beyond_closes": 0})

    def _inventory(self, ts: pd.Timestamp) -> list[dict]:
        return [x for x in self.levels.values() if x["status"] == "ACTIVE" and x["available_at"] <= ts
                and ts - x["available_at"] <= pd.Timedelta(days=self.contract["level_max_age_days"])]

    @staticmethod
    def _nearest(levels: list[dict], price: float, side: str) -> dict | None:
        eligible = [x for x in levels if x["side"] == side and
                    (x["upper"] < price if side == "SELL_SIDE" else x["lower"] > price)]
        return min(eligible, key=lambda x: (abs(x["price"] - price), x["id"]), default=None)

    def _context(self, recent: pd.DataFrame, levels: list[dict], source: dict | None = None) -> tuple:
        metrics = _window_metrics(recent)
        support = self._nearest(levels, metrics["close"], "SELL_SIDE")
        resistance = self._nearest(levels, metrics["close"], "BUY_SIDE")
        if source is not None:
            if source["side"] == "SELL_SIDE":
                support = source
            else:
                resistance = source
        result = _classify_state(metrics=metrics, support=band(support), resistance=band(resistance), previous_states=self.previous_states)
        scores = {}
        for part in result[4].split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                try:
                    scores[k] = float(v)
                except ValueError:
                    scores[k] = v
        return result, scores

    def _evaluate_sweep(self, prefix: pd.DataFrame, level: dict, sweep_ts: pd.Timestamp) -> dict:
        return evaluate_qualified_h1_sweep_reclaim_at(
            h1_bars=prefix, reference_level=level["price"], reference_type=f"{level['timeframe']}_SWING_{'HIGH' if level['side'] == 'BUY_SIDE' else 'LOW'}",
            direction="BEARISH" if level["side"] == "BUY_SIDE" else "BULLISH",
            confirmed_at=level["available_at"].isoformat(), swing_center_timestamp=level["center_at"].isoformat(),
            sweep_h1_close_ts=sweep_ts.isoformat(), reference_id=level["id"], reclaim_window_h1_bars=self.contract["reclaim_window_hours"],
        )

    def _candidate(self, *, family: str, level: dict, ts: pd.Timestamp, bar: pd.Series, stop: float,
                   levels: list[dict], context: tuple, flow: dict, common_reasons: list[str], sequence: dict | None = None) -> None:
        direction = "LONG" if family == "DEMAND_SWEEP_RECLAIM_UP" else "SHORT"
        decision_price = flow["decision_price"]
        target_level = self._nearest(levels, decision_price, "BUY_SIDE" if direction == "LONG" else "SELL_SIDE")
        target = (target_level["lower"] if direction == "LONG" else target_level["upper"]) if target_level else None
        risk = abs(decision_price - stop)
        reasons = list(common_reasons)
        if target is None:
            reasons.append("NO_DIRECTIONAL_STRUCTURAL_TARGET")
        if (direction == "LONG" and stop >= decision_price) or (direction == "SHORT" and stop <= decision_price):
            reasons.append("INVALID_STOP_DIRECTION")
        atr = flow["atr"]
        if pd.isna(atr) or risk < atr * self.contract["minimum_risk_atr_fraction"]:
            reasons.append("INSUFFICIENT_STRUCTURAL_RISK")
        if target is not None and (risk <= 0 or abs(target - decision_price) / risk < self.contract["minimum_target_r"]):
            reasons.append("NEAREST_BLOCKER_BELOW_MINIMUM_R")
        if flow["volume_ratio"] < self.contract["minimum_volume_ratio"]:
            reasons.append("NO_VOLUME_EXPANSION")
        signed_delta = flow["delta_fraction"] * (1 if direction == "LONG" else -1)
        if signed_delta < self.contract["minimum_directional_delta_fraction"]:
            reasons.append("NO_DIRECTIONAL_DELTA_CONFIRMATION")
        dedup = (family, level["id"], ts.strftime("%Y-%m-%d"))
        if dedup in self.seen:
            reasons.append("DUPLICATE_FAMILY_LEVEL_UTC_DAY")
        available = max(ts, level["available_at"], target_level["available_at"] if target_level else ts)
        if available > ts:
            raise ValueError("Future evidence entered candidate")
        sequence_ts = sequence["sweep_ts"] if sequence else None
        key = identity([self.contract["version"], family, ts, level["id"], sequence_ts])
        if not reasons:
            self.seen.add(dedup)
        self.decisions.append({"candidate_id": key, "contract_version": self.contract["version"], "family": family,
                               "direction": direction, "available_at": available.isoformat(), "decision_at": ts.isoformat(),
                               "entry_open_at": (ts + pd.Timedelta(minutes=self.contract["entry_latency_minutes"])).isoformat(),
                               "state_end": ts.isoformat(), "flow_end": ts.isoformat(), "source_level_id": level["id"],
                               "source_level_available_at": level["available_at"].isoformat(),
                               "target_level_id": target_level["id"] if target_level else "",
                               "target_level_available_at": target_level["available_at"].isoformat() if target_level else "",
                               "decision_price": decision_price, "stop_price": stop, "target_price": target,
                               "h1_close_at": bar.timestamp.isoformat(), "h1_available_at": bar.available_at.isoformat(),
                               "h1_omitted_minutes": int(bar.omitted_minutes), "context_omitted_minutes": flow["context_omitted_minutes"],
                               "sweep_at": sequence_ts.isoformat() if sequence_ts else "",
                               "sweep_high": sequence["high"] if sequence else None, "sweep_low": sequence["low"] if sequence else None,
                               "volume_ratio": flow["volume_ratio"], "delta_fraction": flow["delta_fraction"],
                               "oi_change": float(bar.oi_change), "liq_buy": float(bar.liq_buy), "liq_sell": float(bar.liq_sell),
                               "market_state": context[0], "state_evidence": context[4],
                               "accepted": not reasons, "rejection_reasons": "|".join(sorted(set(reasons)))})

    def advance_until(self, cutoff: str | pd.Timestamp) -> None:
        cutoff = pd.Timestamp(cutoff)
        while self.cursor < len(self.h1) and pd.notna(self.h1.iloc[self.cursor].available_at) and self.h1.iloc[self.cursor].available_at <= cutoff:
            i, bar = self.cursor, self.h1.iloc[self.cursor]
            ts = bar.available_at
            prefix = self.h1.iloc[:i + 1]
            self._confirm(self.h1, i, "H1", self.contract["h1_swing_left_right"])
            while self.h4_cursor < len(self.h4) and pd.notna(self.h4.iloc[self.h4_cursor].available_at) and self.h4.iloc[self.h4_cursor].available_at <= ts:
                self._confirm(self.h4, self.h4_cursor, "H4", self.contract["h4_swing_left_right"])
                self.h4_cursor += 1
            end = self.feed.Timestamp.searchsorted(ts, side="right")
            window_start = ts - pd.Timedelta(minutes=self.contract["state_window_minutes"] - 1)
            start = self.feed.Timestamp.searchsorted(window_start, side="left")
            recent = self.feed.iloc[start:end]
            levels = self._inventory(ts)
            context, scores = self._context(recent, levels)
            self.previous_states.append(context[0])
            local_usable = window_is_usable(recent, window_start, ts)
            common = []
            if not local_usable or not bar.usable:
                common.append("EXTENDED_GAP_OR_RECOVERED_24H_CONTEXT")
            if ts - self.history_start < pd.Timedelta(hours=self.contract["warmup_hours"]):
                common.append("WARMUP_ONLY")
            for excluded in self.contract["entry_exclusions"]:
                if pd.Timestamp(excluded["start"]) <= ts < pd.Timestamp(excluded["end"]):
                    common.append(excluded["reason"])
            periods = [x["name"] for x in self.contract["periods"] if pd.Timestamp(x["start"]) <= ts < pd.Timestamp(x["end"])]
            if not periods or any("CONTEXT_ONLY" in x for x in periods):
                common.append("OUTSIDE_ENTRY_EVALUATION_PERIOD")
            prior = prefix.iloc[max(0, i - self.contract["volume_median_bars"]):i]
            median = float(prior.volume.median()) if len(prior) == self.contract["volume_median_bars"] and prior.usable.all() else 0
            tr = pd.concat([prefix.high - prefix.low, (prefix.high - prefix.close.shift()).abs(), (prefix.low - prefix.close.shift()).abs()], axis=1).max(axis=1)
            flow = {"volume_ratio": float(bar.volume) / median if median > 0 else 0,
                    "delta_fraction": (bar.buy - bar.sell) / bar.volume if bar.volume > 0 else 0,
                    "atr": float(tr.iloc[-14:].mean()) if len(prefix) >= 15 else float("nan"),
                    "decision_price": float(recent.ClosePrice.iloc[-1]),
                    "context_omitted_minutes": self.contract["state_window_minutes"] - len(recent)}
            ready = []
            keep = []
            for item in self.pending:
                age = (bar.timestamp - item["sweep_ts"]).total_seconds() / 3600
                if age <= 0 or age > self.contract["reclaim_window_hours"]:
                    continue
                event = self._evaluate_sweep(prefix, item["level"], item["sweep_ts"])
                if event["qualified_h1_failed_reclaim"] == "true" and pd.Timestamp(event["entry_candidate_ts"]) == bar.timestamp:
                    ready.append((item, event))
                else:
                    keep.append(item)
            self.pending = keep
            # A qualifying new penetration is stored; it cannot trigger on its own bar.
            if bar.usable and local_usable:
                for level in levels:
                    if any(x["level"]["id"] == level["id"] for x in self.pending):
                        continue
                    cross = bar.high > level["price"] if level["side"] == "BUY_SIDE" else bar.low < level["price"]
                    if not cross:
                        continue
                    event = self._evaluate_sweep(prefix, level, bar.timestamp)
                    if event["qualified_h1_sweep"] == "true":
                        self.pending.append({"level": level.copy(), "sweep_ts": bar.timestamp, "high": float(bar.high), "low": float(bar.low)})
            sides = {x[0]["level"]["side"] for x in ready}
            for item, event in ready:
                level = item["level"]
                forced_context, forced_scores = self._context(recent, levels, level)
                family = "SUPPLY_SWEEP_RECLAIM_DOWN" if level["side"] == "BUY_SIDE" else "DEMAND_SWEEP_RECLAIM_UP"
                reasons = list(common)
                if len(sides) > 1 or any(x["level"]["side"] != level["side"] and x["sweep_ts"] >= item["sweep_ts"] for x in self.pending):
                    reasons.append("COUNTER_SWEEP_CONFLICT")
                if self.levels[level["id"]]["status"] != "ACTIVE":
                    reasons.append("LEVEL_ACCEPTED_BREAK_OR_INACTIVE")
                if family == "SUPPLY_SWEEP_RECLAIM_DOWN" and (forced_scores.get("overhead_supply_score", 0) < 70 or forced_scores.get("seller_pressure_score", 0) < 50):
                    reasons.append("SUPPLY_PRESSURE_CONTEXT_FAILED")
                if family == "DEMAND_SWEEP_RECLAIM_UP" and forced_scores.get("underlying_demand_score", 0) < 55 and forced_scores.get("buyer_response_score", 0) < 25:
                    reasons.append("DEMAND_RESPONSE_CONTEXT_FAILED")
                stop = float(event["stop_candidate_price"])
                self._candidate(family=family, level=level, ts=ts, bar=bar, stop=stop, levels=levels,
                                context=forced_context, flow=flow, common_reasons=reasons, sequence=item)
            for level in levels:
                if level["side"] != "BUY_SIDE" or not (bar.high >= level["lower"] and bar.close < level["lower"] and bar.close < bar.open):
                    continue
                forced_context, forced_scores = self._context(recent, levels, level)
                reasons = list(common)
                if any(x["level"]["side"] == "SELL_SIDE" for x in self.pending) or any(x[0]["level"]["side"] == "SELL_SIDE" for x in ready):
                    reasons.append("COUNTER_SWEEP_CONFLICT")
                if forced_scores.get("dominant_side") != "SELLER" or forced_scores.get("seller_pressure_score", 0) < 70 or forced_scores.get("buyer_response_score", 0) > 35:
                    reasons.append("SELLER_DOMINANCE_CONTEXT_FAILED")
                stop = max(float(bar.high), level["upper"]) * (1 + self.contract["stop_buffer_bps"] / 10000)
                self._candidate(family="SELLER_DOMINANCE_RETEST_DOWN", level=level, ts=ts, bar=bar, stop=stop,
                                levels=levels, context=forced_context, flow=flow, common_reasons=reasons)
            if bar.usable:
                for level in levels:
                    beyond = bar.close > level["upper"] if level["side"] == "BUY_SIDE" else bar.close < level["lower"]
                    level["beyond_closes"] = level["beyond_closes"] + 1 if beyond else 0
                    if level["beyond_closes"] >= self.contract["accepted_break_closes"]:
                        level["status"] = "ACCEPTED_BREAK"
            else:
                for level in levels:
                    level["beyond_closes"] = 0
            self.timeline.append({"decision_at": ts.isoformat(), "prefix_rows": end, "prefix_last_close": self.feed.Timestamp.iloc[end - 1].isoformat(),
                                  "market_state": context[0], "active_levels": len(levels), "pending_sequences": len(self.pending),
                                  "h1_close_at": bar.timestamp.isoformat(), "h1_complete_raw": bool(bar.raw),
                                  "h1_usable": bool(bar.usable), "entry_context_usable": bool(local_usable),
                                  "h1_omitted_minutes": int(bar.omitted_minutes), "context_omitted_minutes": self.contract["state_window_minutes"] - len(recent),
                                  "market_state_reset": False, "structure_levels_reset": False, "liquidity_zones_reset": False,
                                  "qualified_h1_state_reset": False, "setup_context_reset": False})
            self.cursor += 1

    def frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(self.decisions), pd.DataFrame(self.timeline)
