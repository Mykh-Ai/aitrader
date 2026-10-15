"""Explain failed parity only; no source fitting, OOS access or return calculation."""
import json
import numpy as np
import pandas as pd

from archive_source import OUT, save
from research_kernel import SNAP, H, read_sources, features, hybrid_signals, ReplayData, initial_stop, ExitRules, h4_inventory, candidate_map


def main():
    gate = json.loads((OUT / "parity_gate.json").read_text())
    assert gate["status"] == "BINANCE_KLINE_SURROGATE_PARITY_FAILED"
    selected = json.loads((H / "selected_research_contract.json").read_text())
    spec = selected["baseline_contract"]["futures_signal_baseline"]
    shi, _ = read_sources(SNAP, "2026-03-11T13:45Z", "2026-09-30T23:59Z")
    archive = pd.concat([pd.read_csv(p) for p in sorted((OUT / "normalized_futures_feed").glob("*.csv"))], ignore_index=True)
    archive.Timestamp = pd.to_datetime(archive.Timestamp, utc=True)
    target = pd.Timestamp("2026-07-05T08:00Z")
    rows, h4_rows, space_rows, entry_rows, details = [], [], [], [], {}
    for source, feed in [("SHI", shi), ("BINANCE_KLINES", archive)]:
        bars = features(feed)
        raw = hybrid_signals(bars, spec["long"], spec["short"])
        data = ReplayData(feed, bars)
        inventory = h4_inventory(feed, bars)
        cands, rejected = candidate_map(data, raw, spec, {"short_space_1r": True}, inventory)
        reject = {r["signal_index"]: r for r in rejected}
        prior48 = bars.usable.shift().rolling(48, min_periods=48).sum().eq(48)
        prior96 = bars.usable.shift().rolling(96, min_periods=96).sum().eq(96)
        fixed = bars.lower48.shift()
        chosen = ((bars.timestamp >= pd.Timestamp("2026-07-01", tz="UTC")) & (bars.timestamp < pd.Timestamp("2026-08-01", tz="UTC"))) | ((bars.timestamp >= pd.Timestamp("2026-09-01", tz="UTC")) & (bars.timestamp < pd.Timestamp("2026-10-01", tz="UTC")))
        for i in np.flatnonzero(chosen):
            row = bars.iloc[i]
            rows.append({"source": source, "timestamp": row.timestamp, "prior48_usable": bool(prior48.iloc[i]), "prior96_usable": bool(prior96.iloc[i]),
                         "short_frozen_reference": fixed.iloc[i], "raw_direction": int(raw[i]), "H4_level_count": len(inventory[i])})
            for level in inventory[i]:
                h4_rows.append({"source": source, "decision_at": row.available_at, **level})
            if raw[i]:
                c = cands.get(i, reject.get(i, {}))
                space_rows.append({"source": source, "decision_at": row.available_at, "direction": int(raw[i]),
                                   "H4_space_allowed": i in cands, "space_R": c.get("space_R"), "reference_price": c.get("reference_price"),
                                   "reference_available_at": c.get("reference_available_at"), "reason": c.get("reason", "H4_SPACE_ALLOWED")})
                item = data.entry(int(i))
                if item is not None:
                    _, ts, entry, _, _, _ = item
                    side = int(raw[i])
                    rules = ExitRules(**spec["long" if side > 0 else "short"]["exit"])
                    stop = initial_stop(data, int(i), side, entry, rules)
                    distance = side * (entry - stop)
                    entry_rows.append({"source": source, "decision_at": row.available_at, "direction": side,
                        "declared_entry_at": pd.Timestamp(ts, tz="UTC"), "entry_price": entry,
                        "initial_stop": stop, "initial_target": entry + side * rules.target_r * distance,
                        "initial_risk_fraction": distance / entry, "risk_band_allowed": .004 <= distance / entry <= .04,
                        "returns_or_exits_evaluated": False})
        i = int(np.flatnonzero(bars.timestamp.eq(target))[0])
        previous = bars.iloc[i-96:i]
        details[source] = {"raw_direction": int(raw[i]), "prior96_usable": bool(prior96.iloc[i]), "prior48_usable": bool(prior48.iloc[i]),
                           "unusable_prior96_H1": previous.loc[~previous.usable, ["timestamp", "available_at", "omitted_minutes", "complete_observations", "source_start", "source_end"]].to_dict("records")}
    pd.DataFrame(rows).to_csv(OUT / "prior_history_and_reference_parity.csv", index=False)
    pd.DataFrame(h4_rows).to_csv(OUT / "H4_inventory_evidence.csv", index=False)
    pd.DataFrame(space_rows).to_csv(OUT / "H4_space_evidence.csv", index=False)
    pd.DataFrame(entry_rows).to_csv(OUT / "known_candidate_stop_target_preview.csv", index=False)
    result = {"decisive_mismatch_at": target, "source_details": details,
              "direct_evidence": "Prior-history quality, H4 references, OHLC and volume/flow differ; not a pure trade-count or quantity-rounding issue.",
              "collector_clock_fact": "CandleBuffer consumes received callbacks without exchange timestamp bucketing; flush_candle stamps current UTC minute and resets received buffer.",
              "root_cause_limit": "Archive/event-time versus collector receipt/flush semantics are a mechanism consistent with evidence. Individual historical packet loss/arrival delays are not provable without raw receipt logs.",
              "optional_aggTrades_fallback": "NOT_ATTEMPTED",
              "fallback_reason": "Failure is not limited to taker-buy/sell reconstruction: observed OHLC, prior-history usable status and H4 inventory differ. Optional aggTrades source was not tested and is not claimed to fail or pass.",
              "normalization_or_trading_rules_changed_after_failure": False, "OOS_touched": False}
    save("source_semantics_diagnosis.json", result)
    print(json.dumps(result, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
