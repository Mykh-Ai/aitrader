"""40H: entry-known loss diagnostics and bounded spot filter replays, research only."""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
G = ROOT / "market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0"
F = ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0"
for path in [ROOT, G, F]:
    sys.path.insert(0, str(path))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest, usable_observations, window_is_usable
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, ExitRules, initial_stop, metrics
from market_monitor.market_structure_state import _window_metrics
from interventions import h4_inventory, candidate_map
from cross_market import execution_references


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n", encoding="utf-8")


def freeze():
    paths = [G / x for x in ["selected_spot_contract.json", "selected_spot_trade_ledger.csv", "selected_spot_result.json",
                              "execution_manifest_v1.json", "cross_market.py", "spot_BTCUSDC/spot_minutes.csv"]]
    paths += [F / "interventions.py", ROOT / "market_monitor/market_structure_state.py"]
    paths += list((ROOT / "research/strategy_search").glob("*.py"))
    record = {
        "task": "SHI_RESET_40H_LOSS_METRICS_FILTER_STUDY",
        "phase": "DIAGNOSTIC_DEFINITIONS_FROZEN_BEFORE_GROUP_RESULTS",
        "baseline_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
        "code_hash": digest(Path(__file__)),
        "clock": "Closed futures observations <= decision; planned entry decision+1m. Real UTC and Europe/Budapest DST. No outcome feature in entry filters.",
        "metrics": ["H1/H4/H24/H72 weighted delta", "24h raw delta BTC", "prior-volume ratio", "24h OI percent/quantity change",
                    "current/24h-mean funding", "24h liquidations and ratio", "24h Monitor range/close-position/price change",
                    "EMA24/72 separation, EMA168 slope, distance to EMA24, 24h efficiency", "decision-close stop-risk estimate",
                    "entry hour, four-hour/eight-hour UTC/local buckets, weekday/weekend", "confirmed H4 regime"],
        "units": "delta percent=100*(sumBuy-sumSell)/sumVolume, NOT mean minute percentages; OI pct=100*(last/first-1).",
        "monitor_scope": "Reuse actual _window_metrics for closed (decision-24h,decision] observations; additional explicit raw aggregates. No full Monitor lifecycle replay or historical snapshot joins.",
        "bins": {"delta24_pct": ["< -4", "[-4,0)", "[0,4)", "[4,8)", ">=8"],
                 "volume_ratio": ["[1.3,2)", "[2,3)", "[3,4)", ">=4"],
                 "oi24_pct": ["negative", "zero", "positive"],
                 "UTC_and_Budapest_hours": "4h:00-04,04-08,08-12,12-16,16-20,20-24; 8h:00-08,08-16,16-24",
                 "range_position24": ["[0,.25)", "[.25,.5)", "[.5,.75)", "[.75,1]"]},
        "limitations": ["Previously selected history, only21 baseline trades; adaptive filters are exploratory, not pristine holdout.",
                        "Fixed3000USDC notional,5USDC/trade fee,2bps/fill slip; actual borrowing/orderbook unverified.",
                        "Full causal candidate stream and global book must be rerun; do not sum row-deleted baseline as new portfolio."]}
    dest = OUT / "diagnostic_manifest.json"
    if dest.exists():
        existing = json.loads(dest.read_text())
        assert existing == record, "Frozen diagnostic changed; use a versioned successor"
    else:
        save(dest.name, record)


def load():
    m = json.loads((G / "execution_manifest_v1.json").read_text())
    spec = m["baseline_spec"]
    assert all(digest(ROOT / p) == sha for p, sha in m["preserved_hashes"].items())
    assert all(digest(G / p) == sha for p, sha in m["study_code_hashes"].items())
    assert digest(G / "spot_BTCUSDC/spot_minutes.csv") == m["spot_csv_sha256"]
    feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
    spot = pd.read_csv(G / "spot_BTCUSDC/spot_minutes.csv")
    spot.Timestamp = pd.to_datetime(spot.Timestamp, utc=True)
    spot = spot.loc[spot.Timestamp.between(feed.Timestamp.min(), feed.Timestamp.max()) & spot.DataQuality.eq("RAW")].reset_index(drop=True)
    bars = features(feed)
    fdata = ReplayData(feed, bars)
    ebars, quotes = execution_references(feed, spot, bars)
    sdata = ReplayData(spot, ebars)
    original = hybrid_signals(bars, spec["long"], spec["short"])
    cands, rejected = candidate_map(fdata, original, spec, {"short_space_1r": True}, h4_inventory(feed, bars))
    directions = np.zeros_like(original)
    for i, c in cands.items():
        directions[i] = c["side"]
    return feed, spot, bars, fdata, sdata, directions, original, spec, quotes


def entry_metrics(feed, bars, directions, indexes, spec):
    """No reads after decision. Isolated minute omissions remain time-preserving."""
    raw = usable_observations(feed)
    timestamps = pd.DatetimeIndex(raw.Timestamp).asi8
    efficiency = (bars.close - bars.close.shift(24)).abs() / bars.close.diff().abs().rolling(24).sum()
    regimes = pd.read_csv(G / "futures_h4_regimes.csv").h4_regime if len(bars) == len(pd.read_csv(G / "futures_h4_regimes.csv")) else None
    rows = []
    for i in indexes:
        b = bars.iloc[i]
        side = int(directions[i])
        decision = b.available_at
        right = timestamps.searchsorted(decision.value, side="right")
        record = {"signal_index": int(i), "direction": side, "decision_at": decision,
                  "planned_entry_at": decision + pd.Timedelta(minutes=1)}
        for hours in [1, 4, 24, 72]:
            left = timestamps.searchsorted((decision - pd.Timedelta(hours=hours)).value, side="right")
            w = raw.iloc[left:right]
            usable = window_is_usable(w, decision - pd.Timedelta(hours=hours) + pd.Timedelta(minutes=1), decision)
            volume = w.TotalQty.sum()
            record[f"window{hours}_usable"] = usable
            record[f"window{hours}_last_observation_at"] = w.Timestamp.iloc[-1] if len(w) else pd.NaT
            record[f"delta{hours}_pct"] = 100 * (w.BuyQty.sum() - w.SellQty.sum()) / volume if usable and volume > 0 else np.nan
            if hours == 24:
                m = _window_metrics(w) if usable else {}
                for k in ["delta_pct", "price_change_pct", "range_pct", "close_position", "open_interest_change"]:
                    record[f"monitor24_{k}"] = m.get(k, np.nan)
                record["delta24_btc"] = float(w.BuyQty.sum() - w.SellQty.sum()) if usable else np.nan
                record["oi24_pct"] = 100 * (w.OpenInterest.iloc[-1] / w.OpenInterest.iloc[0] - 1) if usable and w.OpenInterest.iloc[0] else np.nan
                record["funding_current"] = float(w.FundingRate.iloc[-1]) if usable else np.nan
                record["funding_mean24"] = float(w.FundingRate.mean()) if usable else np.nan
                liq_valid = usable and w.LiquidationDataAvailable.all()
                record["liquidation24_available"] = bool(liq_valid)
                record["liq_buy24_btc"] = float(w.LiqBuyQty.sum()) if liq_valid else np.nan
                record["liq_sell24_btc"] = float(w.LiqSellQty.sum()) if liq_valid else np.nan
                total_liq = record["liq_buy24_btc"] + record["liq_sell24_btc"]
                record["liq_buy_share24"] = record["liq_buy24_btc"] / total_liq if total_liq > 0 else np.nan
                record["observed_minutes24"] = len(w)
        record.update({"bar_delta24_pct": 100 * b.delta24, "volume_ratio": b.volume_ratio,
                       "range_atr": (b.high - b.low) / b.atr,
                       "ema24_distance_atr_signed": side * (b.close - b.ema24) / b.atr,
                       "ema24_72_separation_atr_signed": side * (b.ema24 - b.ema72) / b.atr,
                       "ema168_slope24_atr_signed": side * (b.ema168 - bars.ema168.iloc[i-24]) / b.atr,
                       "trend_efficiency24": efficiency.iloc[i],
                       "change24_signed_pct": side * b.change24 * 100})
        rules = ExitRules(**spec["long" if side > 0 else "short"]["exit"])
        # Future spot entry price is deliberately unavailable to this estimate.
        structural = b.lower6 * .9995 if side > 0 else b.upper6 * 1.0005
        estimated_stop = min(structural, b.close - rules.atr_floor * b.atr) if side > 0 else max(structural, b.close + rules.atr_floor * b.atr)
        record["estimated_risk_pct"] = side * (b.close - estimated_stop) / b.close * 100
        record["estimated_risk_quote"] = record["estimated_risk_pct"] * 30
        record["h4_regime"] = regimes.iloc[i] if regimes is not None else "NOT_JOINED"
        local = record["planned_entry_at"].tz_convert("Europe/Budapest")
        for tz, stamp in [("utc", record["planned_entry_at"]), ("budapest", local)]:
            record[f"entry_hour_{tz}"] = stamp.hour
            for size in [4, 8]:
                start = stamp.hour // size * size
                record[f"entry_{size}h_{tz}"] = f"{start:02}-{start+size:02}"
        record["entry_weekday_utc"] = record["planned_entry_at"].day_name()
        record["weekend_utc"] = record["planned_entry_at"].dayofweek >= 5
        record["local_utc_offset_hours"] = local.utcoffset().total_seconds() / 3600
        for hours in [1, 4, 24, 72]:
            record[f"delta{hours}_signed_pct"] = side * record[f"delta{hours}_pct"]
        rows.append(record)
    return pd.DataFrame(rows)


def bucket_tables(t):
    t = t.copy()
    t["delta24_bin"] = pd.cut(t.delta24_pct, [-np.inf, -4, 0, 4, 8, np.inf], right=False).astype(str)
    t["delta24_signed_bin"] = pd.cut(t.delta24_signed_pct, [-np.inf, 0, 4, 8, np.inf], right=False).astype(str)
    t["volume_bin"] = pd.cut(t.volume_ratio, [0, 2, 3, 4, np.inf], right=False).astype(str)
    t["oi24_sign"] = np.select([t.oi24_pct < 0, t.oi24_pct > 0], ["NEGATIVE", "POSITIVE"], default="ZERO_OR_MISSING")
    t["range_position24_bin"] = pd.cut(t.monitor24_close_position, [0, .25, .5, .75, 1.00001], right=False).astype(str)
    t["direction_label"] = np.where(t.direction > 0, "LONG", "SHORT")
    rows = []
    fields = ["entry_hour_utc", "entry_4h_utc", "entry_8h_utc", "entry_4h_budapest", "entry_8h_budapest", "entry_weekday_utc",
              "weekend_utc", "delta24_bin", "delta24_signed_bin", "volume_bin", "oi24_sign", "range_position24_bin", "h4_regime"]
    for direction in ["ALL", "LONG", "SHORT"]:
        part = t if direction == "ALL" else t.loc[t.direction_label.eq(direction)]
        for field in fields:
            for value, g in part.groupby(field, dropna=False, observed=True):
                rows.append({"direction": direction, "metric": field, "bucket": value, "trades": len(g),
                             "wins": int(g.net_usd.gt(0).sum()), "losses": int(g.net_usd.lt(0).sum()),
                             "winner_profit_quote": g.loc[g.net_usd.gt(0), "net_usd"].sum(),
                             "loser_loss_quote": g.loc[g.net_usd.lt(0), "net_usd"].sum(), "net_quote": g.net_usd.sum()})
    return pd.DataFrame(rows)


def diagnose():
    freeze()
    feed, spot, bars, fdata, sdata, directions, original, spec, quotes = load()
    print("Immutable two-feed sources verified; computing entry-known metrics", flush=True)
    indexes = np.flatnonzero(original)
    f = entry_metrics(feed, bars, original, indexes, spec)
    f["baseline_candidate_allowed"] = directions[indexes] != 0
    f.to_csv(OUT / "all_candidate_entry_metrics.csv", index=False)
    baseline = replay_hybrid(sdata, directions, spec["long"], spec["short"])
    saved = pd.read_csv(G / "selected_spot_trade_ledger.csv")
    for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        saved[col] = pd.to_datetime(saved[col], utc=True)
    pd.testing.assert_frame_equal(baseline, saved[baseline.columns], check_exact=False, rtol=1e-10, atol=1e-10)
    t = saved.merge(f.drop(columns=["direction", "decision_at", "h4_regime"]), on="signal_index", validate="one_to_one")
    t["outcome"] = np.where(t.net_usd < 0, "LOSS", "WIN")
    t.to_csv(OUT / "baseline_trade_entry_metrics.csv", index=False)
    t.loc[t.net_usd.lt(0)].to_csv(OUT / "all_13_losing_trades.csv", index=False)
    numeric = [c for c in f.select_dtypes(include="number").columns if c not in ["signal_index", "direction"]]
    medians = t.groupby(["direction", "outcome"])[numeric].median()
    medians.to_csv(OUT / "feature_medians_by_direction_outcome.csv")
    bucket_tables(t).to_csv(OUT / "diagnostic_buckets.csv", index=False)
    save("diagnostic_verification.json", {"baseline_21_rows_exactly_reproduced": len(t) == 21,
          "baseline_losses": int(t.net_usd.lt(0).sum()), "baseline_wins": int(t.net_usd.gt(0).sum()),
          "candidate_rows": len(f), "short_space_candidates": int(f.baseline_candidate_allowed.sum()),
          "monitor_delta24_matches_weighted_raw": bool(np.allclose(f.monitor24_delta_pct, f.delta24_pct, equal_nan=True, atol=0.00000051)),
          "max_observation_not_after_decision": bool(all((f[f"window{h}_last_observation_at"] <= f.decision_at).all() for h in [1,4,24,72])),
          "no_protected_source_change": True, "baseline_metrics": metrics(baseline)})
    print(medians[["delta24_pct", "delta24_signed_pct", "oi24_pct", "volume_ratio", "range_atr", "trend_efficiency24", "monitor24_close_position"]].to_string(), flush=True)
    buckets = pd.read_csv(OUT / "diagnostic_buckets.csv")
    print(buckets.loc[buckets.metric.isin(["delta24_bin", "entry_4h_utc", "oi24_sign"])].to_string(index=False), flush=True)


if __name__ == "__main__":
    diagnose()
