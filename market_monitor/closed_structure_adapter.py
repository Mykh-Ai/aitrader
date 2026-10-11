"""Research-only, as-of H1/H4 structural inventory over completed minute feed.

Reuses canonical swing geometry, zone construction, lifecycle and significance.
This is NOT the complete v39A snapshot: it excludes M15/session/pattern/merged
zones and event/post-sweep score bonuses. References retain immutable identities.
Full available history is retained; no daily reset or visible-seven restriction.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd

from market_monitor.structure import _confirmed_swing_levels
from market_monitor.liquidity_zones import build_liquidity_map
from market_monitor.zone_registry import _current_zones_to_registry, _update_lifecycle, REGISTRY_COLUMNS
from market_monitor.significant_zone_selector import _score_zone, HIDDEN_STATUSES

ADAPTER_VERSION = "CLOSED_H1_H4_IMMUTABLE_REFERENCES_V1"


@dataclass(frozen=True)
class Reference:
    zone_id: str
    available_at: pd.Timestamp
    timeframe: str
    price: float
    lower: float
    upper: float
    level: dict


def minute_frame(bars) -> pd.DataFrame:
    """Replay FeedBar.ts is availability/close time; native structure uses OPEN labels."""
    frame = pd.DataFrame({
        "Timestamp": [b.ts for b in bars],
        "OpenPrice": [b.open for b in bars], "HiPrice": [b.high for b in bars],
        "LowPrice": [b.low for b in bars], "ClosePrice": [b.close for b in bars],
        "TotalQty": [b.volume for b in bars], "Trades": 0,
        "BuyQty": [b.buy_qty for b in bars], "SellQty": [b.sell_qty for b in bars],
        # Unavailable derivatives context is not a fabricated zero observation.
        # These compatibility columns do not participate in this adapter's scores.
        "OpenInterest": 0., "FundingRate": 0.,
        "DataQuality": ["INVALID" if b.is_synthetic else "RAW" for b in bars],
    })
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True) - pd.Timedelta(minutes=1)
    if frame.empty or frame.Timestamp.duplicated().any() or not frame.Timestamp.is_monotonic_increasing:
        raise ValueError("minute feed must be nonempty, unique and chronological")
    return frame


class ClosedStructureMonitor:
    """Lazy deterministic lifecycle reconstruction, always restricted to an as-of prefix.

    Swing discovery can be precomputed because each reference is published only
    at its final confirmation bar CLOSE. Prefix-equivalence is a required test.
    Lifecycle state is reconstructed from its complete past, never a recent slice.
    """
    def __init__(self, bars):
        self.bars = bars
        self.frame = minute_frame(bars)
        self.times = pd.DatetimeIndex([b.ts for b in bars])
        self.closes = self.frame.ClosePrice.to_numpy()
        self.highs = self.frame.HiPrice.to_numpy()
        bad = np.array([b.is_synthetic or b.volume <= 0 for b in bars])
        gaps = np.r_[False, np.diff(self.times.asi8) != 60_000_000_000]
        self.bad_prefix = np.r_[0, np.cumsum(bad | gaps)]
        self.references = self._discover_references()
        self._base_registry = {}
        self.last_query = None

    def _discover_references(self):
        references = []
        for tf, minutes, lr in (("H1", 60, 2), ("H4", 240, 1)):
            duration = pd.Timedelta(minutes=minutes)
            for row in _confirmed_swing_levels(self.frame, tf, lr):
                if row["side"] != "BUY_SIDE":
                    continue
                confirm_open = pd.Timestamp(row["created_at"])
                window_start = confirm_open - 2 * lr * duration
                available = confirm_open + duration
                first = self.times.searchsorted(window_start + pd.Timedelta(minutes=1))
                stop = self.times.searchsorted(available, side="right")
                expected = (2 * lr + 1) * minutes
                if stop - first != expected:
                    continue
                # Ignore a preceding gap, but never a gap inside the confirming window.
                window = self.bars[first:stop]
                if any(b.is_synthetic or b.volume <= 0 for b in window):
                    continue
                if np.any(np.diff(self.times.asi8[first:stop]) != 60_000_000_000):
                    continue
                if self.times[first] != window_start + pd.Timedelta(minutes=1) or self.times[stop-1] != available:
                    continue
                identity = f"{tf}|{row['level_timestamp']}|{row['price']}|{available.isoformat()}"
                zone_id = "HZONE_" + hashlib.sha256(identity.encode()).hexdigest()[:20]
                row = dict(row, level_id=zone_id, source_level_ids=zone_id,
                           created_at=available.isoformat(), htf_confirmation_timestamp=available.isoformat())
                # Exactly the canonical single-reference band (not a fitted parameter).
                band = max(abs(float(row["price"])) * .0005, 10.)
                references.append(Reference(zone_id, available, tf, float(row["price"]),
                                            float(row["price"])-band, float(row["price"])+band, row))
        return sorted(references, key=lambda r: (r.available_at, r.zone_id))

    def _registry_for(self, ref):
        if ref.zone_id not in self._base_registry:
            zones = build_liquidity_map(pd.DataFrame([ref.level]), ref.price)
            if len(zones) != 1:
                raise ValueError(f"single structural reference did not produce one zone: {ref.zone_id}")
            registry = _current_zones_to_registry(zones, pd.DataFrame(columns=REGISTRY_COLUMNS))
            registry["zone_id"] = ref.zone_id
            self._base_registry[ref.zone_id] = registry
        return self._base_registry[ref.zone_id].copy(deep=True)

    def query(self, ts, *, crossing_lookback_minutes=240):
        ts = pd.Timestamp(ts)
        if self.last_query is not None and ts < self.last_query:
            raise ValueError("monitor queries must be chronological")
        self.last_query = ts
        i = self.times.get_indexer([ts])[0]
        if i < 0:
            raise ValueError("missing exact monitor minute")
        price = self.closes[i]
        available = [r for r in self.references if r.available_at < ts]
        counts = {"known_references": len(available), "price_not_above": 0,
                  "no_recent_cross": 0, "gap_or_invalid_since_cross": 0,
                  "inactive_or_insignificant": 0, "incomplete_level_history": 0}
        eligible, evidence = [], []
        for ref in available:
            if price <= ref.upper:
                counts["price_not_above"] += 1
                continue
            first = int(self.times.searchsorted(max(ref.available_at, ts-pd.Timedelta(minutes=crossing_lookback_minutes+1))))
            before = np.flatnonzero(self.closes[first:i] <= ref.upper)
            if len(before) == 0:
                counts["no_recent_cross"] += 1
                continue
            k = first + int(before[-1]) + 1
            crossed_at = self.times[k]
            if crossed_at <= ref.available_at or ts-crossed_at > pd.Timedelta(minutes=crossing_lookback_minutes):
                counts["no_recent_cross"] += 1
                continue
            # Include the bar immediately before crossing to rule out a gap jump.
            if self.bad_prefix[i+1] - self.bad_prefix[max(0,k-1)] != 0:
                counts["gap_or_invalid_since_cross"] += 1
                continue
            # Native lifecycle only consumes observations since first_seen_at.
            # Retain that WHOLE interval, not a sliding recent-history window.
            history_start = int(self.times.searchsorted(ref.available_at + pd.Timedelta(minutes=1)))
            if self.bad_prefix[i+1] - self.bad_prefix[history_start] != 0:
                counts["incomplete_level_history"] += 1
                continue
            history = self.frame.iloc[history_start:i+1]
            registry = _update_lifecycle(self._registry_for(ref), history, closed_htf_only=True)
            row = registry.iloc[0].copy()
            row["distance_from_close_pct"] = (ref.price-price)/price*100
            score = _score_zone(row, pd.DataFrame(), pd.DataFrame())
            decision = "ELIGIBLE"
            if (score["bucket"] not in {"MAJOR", "PRIMARY"}
                or str(row["status"]) in HIDDEN_STATUSES
                or str(row["consumption_status"]) in HIDDEN_STATUSES):
                counts["inactive_or_insignificant"] += 1
                decision = "INACTIVE_OR_INSIGNIFICANT"
            sweep_hour_start = (crossed_at-pd.Timedelta(minutes=1)).floor("h") + pd.Timedelta(minutes=1)
            sweep_first = int(self.times.searchsorted(sweep_hour_start))
            if self.times[sweep_first] != sweep_hour_start or self.bad_prefix[i+1]-self.bad_prefix[sweep_first+1] != 0:
                decision = "INCOMPLETE_SWEEP_HOUR"
            item = {**score, "available_at": ref.available_at.isoformat(), "asof_ts": ts.isoformat(),
                    "crossed_at": crossed_at.isoformat(), "sweep_start_ts": sweep_hour_start.isoformat(),
                    "sweep_high": float(self.highs[sweep_first:i+1].max()),
                    "consumption_status": str(row["consumption_status"]), "decision": decision,
                    "adapter_version": ADAPTER_VERSION,
                    "market_state_reset": False, "structure_levels_reset": False,
                    "future_data_used": False}
            evidence.append(item)
            if decision == "ELIGIBLE":
                eligible.append(item)
        eligible.sort(key=lambda r: (price-float(r["price_upper"]), -r["significance_score"], r["zone_id"]))
        return eligible, counts, evidence

    def inventory(self):
        return [{"zone_id": r.zone_id, "available_at": r.available_at.isoformat(),
                 "timeframe": r.timeframe, "price": r.price, "lower": r.lower, "upper": r.upper,
                 "level": json.dumps(r.level, sort_keys=True)} for r in self.references]
