"""Chronological entry point for the existing canonical Monitor pipeline.

All structure, registry, events, scoring, flow, state, setup and snapshot work
is delegated to the shared production implementations. Frozen decisions are
never regenerated from the final registry or a later selected-zone table.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from market_monitor.structure import StructureState, _observation_feed, aggregate_timeframe
from market_monitor.outputs import write_outputs
from market_monitor.significant_zone_selector import INPUT_TABLES, select_zones_at
from market_monitor import market_structure_state as state_builder
from market_monitor import hidden_flow_research as flow
from market_monitor import setup_builder
from market_monitor.snapshot_builder_v39a import build_market_monitor_snapshot_v39a


class ChronologicalMonitor:
    def __init__(self, *, max_visible_zones=7):
        self.max_visible_zones = max_visible_zones
        self.structure = StructureState()
        self.registry = None
        self.cutoff = None
        self.decisions = {}
        self.flow_rows = []
        self.previous_states = []
        self.events = pd.DataFrame()
        self.completed_observations = pd.DataFrame()
        self.market_moves = pd.DataFrame()
        self.taxonomy = pd.DataFrame()
        self.review_windows = pd.DataFrame()
        self.setup_context = []
        self.decision_count = 0

    def update(self, feed: pd.DataFrame, cutoff):
        cutoff = pd.Timestamp(cutoff)
        cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
        if cutoff != cutoff.floor("h"):
            raise ValueError("Monitor updates require a completed UTC H1 close")
        if self.cutoff is not None and cutoff < self.cutoff:
            raise ValueError("cannot rewind market state; reconstruct a fresh prefix")
        key = cutoff.isoformat()
        if self.cutoff == cutoff:
            return self.decisions[key]
        raw_prefix = feed.loc[feed.Timestamp.le(cutoff)]
        prefix = _observation_feed(raw_prefix)
        if prefix.empty or prefix.Timestamp.max() < cutoff - pd.Timedelta(minutes=1):
            raise ValueError("no observed H1 closing boundary")
        progression = raw_prefix if self.cutoff is None else raw_prefix.loc[raw_prefix.Timestamp.gt(self.cutoff)]
        frames = write_outputs(progression, Path("."), run_timestamp=key, input_files=[],
                               calculation_feed=raw_prefix, registry_state=self.registry,
                               structure_state=self.structure, persist=False,
                               event_state=self.events, observation_state=self.completed_observations,
                               decision_cutoff=cutoff, market_move_state=self.market_moves, taxonomy_state=self.taxonomy)
        self.registry = frames["liquidity_zone_registry.csv"]
        self.events = frames["event_log.csv"]
        self.completed_observations = frames["post_sweep_observation.csv"]
        self.market_moves = frames["market_move_groups.csv"]
        self.taxonomy = frames["sweep_label_taxonomy.csv"]
        loaded = {}
        for name in INPUT_TABLES:
            table = frames.get(name, pd.DataFrame()).copy()
            table["_source_day"] = cutoff.date().isoformat()
            loaded[name] = table
        selected = select_zones_at(loaded, cutoff, max_visible_zones=self.max_visible_zones)
        # Existing hidden-flow formulas on exact observed trailing windows.
        normalized = prefix.rename(columns={"Timestamp": "timestamp", "Trades": "trades", "TotalQty": "total_qty",
            "BuyQty": "buy_qty", "SellQty": "sell_qty", "ClosePrice": "close_price", "HiPrice": "high_price",
            "LowPrice": "low_price", "OpenInterest": "open_interest", "FundingRate": "funding_rate"})
        first_new_window = len(self.flow_rows)
        for duration in (60, 120, 240, 1440):
            window = normalized.loc[normalized.timestamp.gt(cutoff - pd.Timedelta(minutes=duration))]
            if len(window) < duration - 1:
                continue
            prior = flow._prior_trend_context(normalized, int(window.index[0]), duration)
            raw = flow._score_window(window, selected, duration, len(self.flow_rows) + 1,
                                     flow._missing_flags(normalized, selected), prior)
            self.flow_rows.append(raw)
        windows = pd.DataFrame(self.flow_rows)
        if not windows.empty:
            relative = flow._add_relative_metrics(windows)
            new_ids = {row["window_id"] for row in self.flow_rows[first_new_window:]}
            current = relative.loc[relative.window_id.isin(new_ids)]
            windows = pd.DataFrame([flow._finalize_window(row) for _, row in current.iterrows()])
        parts = [part for part in [self.review_windows, windows] if not part.empty]
        if parts:
            windows = pd.concat(parts, ignore_index=True)
            ends = pd.to_datetime(windows.end_timestamp, utc=True)
            windows = windows.loc[ends.ge(cutoff - pd.Timedelta(hours=1)) & ends.le(cutoff)].reset_index(drop=True)
        levels = state_builder._build_level_bands(self.registry, current_price=float(prefix.ClosePrice.iloc[-1]), merge_gap_bps=50.)
        metrics = state_builder._window_metrics(prefix.loc[prefix.Timestamp.gt(cutoff - pd.Timedelta(hours=1))])
        h1 = aggregate_timeframe(prefix.loc[prefix.Timestamp.gt(cutoff - pd.Timedelta(hours=1))], "H1", as_of=cutoff)
        h1_status = "PARTIAL" if h1.empty else h1.iloc[-1].completion_status
        support = state_builder._nearest_band_for_price(levels, "SUPPORT", metrics["close"])
        resistance = state_builder._nearest_band_for_price(levels, "RESISTANCE", metrics["close"])
        label, confidence, bias, strength, evidence = state_builder._classify_state(
            metrics=metrics, support=support, resistance=resistance, previous_states=self.previous_states)
        decision_index = self.decision_count + 1
        state = pd.DataFrame([{"start_timestamp": (cutoff - pd.Timedelta(hours=1)).isoformat(), "end_timestamp": key,
            "latest_consumed_evidence_at_utc": key, "market_state": label, "confidence_tier": confidence,
            "h1_observation_status": h1_status,
            "candidate_bias": bias, "candidate_strength": strength, "price_close": metrics["close"],
            "state_id": f"state_{decision_index:06d}",
            "active_support_band_id": str(support.get("band_id", "")),
            "active_support_price_lower": support.get("price_lower", ""),
            "active_support_price_upper": support.get("price_upper", ""),
            "active_resistance_band_id": str(resistance.get("band_id", "")),
            "active_resistance_price_lower": resistance.get("price_lower", ""),
            "active_resistance_price_upper": resistance.get("price_upper", ""),
            "next_zone_in_front_of_price": state_builder._next_zone_text(resistance),
            "oi_context": state_builder._oi_context(metrics),
            "price_open": metrics["open"], "price_high": metrics["high"], "price_low": metrics["low"],
            "price_change_pct": metrics["price_change_pct"], "range_pct": metrics["range_pct"],
            "close_position": metrics["close_position"], "delta_pct": metrics["delta_pct"],
            "open_interest_change": metrics["open_interest_change"], "evidence_summary": evidence}])
        prepared_windows = setup_builder._prepare_windows(windows)
        setups = setup_builder._build_rows(states=state, windows=prepared_windows, zones=selected,
                                           hidden_candidates=pd.DataFrame())
        for index, row in enumerate(setups, start=len(self.setup_context) + 1):
            row["setup_id"] = f"setup_{index:06d}"
        snapshot = build_market_monitor_snapshot_v39a(raw_prefix, cutoff_ts=cutoff, persist_state=False, symbol="BTCUSDT",
            allow_isolated_close_omission=True,
            base_snapshot={"cutoff_ts": key, "significant_market_zones": selected.to_dict("records"),
                           "liquidity_zones": self.registry.to_dict("records"), "market_structure_state": state.iloc[0].to_dict()})
        decision = {"frames": frames, "selected_zones": selected, "state": state,
                    "hidden_flow_windows": windows, "setups": setups, "snapshot": snapshot}
        self.decisions = {key: decision}  # caller persists frozen decisions; do not retain every full registry in RAM
        self.review_windows = windows.copy()
        self.setup_context.extend(setups)
        self.decision_count = decision_index
        if h1_status != "PARTIAL":
            self.previous_states.append(label)
        self.cutoff = cutoff
        return decision
