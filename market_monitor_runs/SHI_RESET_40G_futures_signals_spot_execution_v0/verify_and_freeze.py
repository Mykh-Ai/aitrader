from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / "market_monitor_runs/SHI_RESET_40F_direction_expiry_stop_interventions_v0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
sys.path.insert(0, str(PRIOR))
from research.own_signal_run.__main__ import verified_inputs
from research.own_signal_run.feed import digest, usable_observations
from research.strategy_search.features import features
from research.strategy_search.hybrid import hybrid_signals, replay_hybrid
from research.strategy_search.replay import ReplayData, metrics
from interventions import h4_inventory, candidate_map
from cross_market import execution_references

manifest = json.loads((OUT / "execution_manifest_v1.json").read_text())
spec = manifest["baseline_spec"]
feed, _ = verified_inputs(ROOT, ROOT / spec["source_preparation"])
spot_all = pd.read_csv(OUT / "spot_BTCUSDC/spot_minutes.csv", parse_dates=["Timestamp"])
spot_all.Timestamp = pd.to_datetime(spot_all.Timestamp, utc=True)
spot_all = spot_all.loc[spot_all.Timestamp.between(feed.Timestamp.min(), feed.Timestamp.max())].reset_index(drop=True)
spot = spot_all.loc[spot_all.DataQuality.eq("RAW")].copy().reset_index(drop=True)
future_raw = usable_observations(feed)
checked, partials, amendments = 0, 0, 0
for variant in manifest["variants"]:
    ledger = pd.read_csv(OUT / "variant_ledgers" / f'{variant["id"]}.csv')
    for field in ["entry_at", "exit_at", "decision_at", "expiry_at"]:
        ledger[field] = pd.to_datetime(ledger[field], utc=True)
    raw = future_raw if variant["market"] == "FUTURES_PROXY" else spot
    for row in ledger.itertuples():
        assert not row.censored
        minute = pd.Timedelta(minutes=1)
        end = row.exit_at + (minute if row.exit_reason == "EXPIRY_NEXT_REAL_OPEN" else pd.Timedelta(0))
        path = raw.loc[(raw.Timestamp >= row.entry_at + minute) & (raw.Timestamp <= end)]
        assert path.DataQuality.eq("RAW").all()
        assert path.Timestamp.diff().dropna().le(2 * minute).all()
        np.testing.assert_allclose(row.entry_price, path.OpenPrice.iloc[0])
        effective = np.full(len(path), row.stop_price)
        actions = json.loads(row.amendments_json)
        for action in actions:
            assert action["reference_at"] <= action["decision_at"]
            assert action["eligible_at"] >= action["decision_at"] + 60_000_000_000
            if action["active_at"] is not None:
                assert action["active_at"] >= action["eligible_at"]
                active = path.Timestamp.sub(minute).ge(pd.Timestamp(action["active_at"], tz="UTC"))
                effective[active] = np.maximum(effective[active], action["price"])
                decision = pd.Timestamp(action["decision_at"], tz="UTC")
                known_price = raw.loc[raw.Timestamp.le(decision), "ClosePrice"].iloc[-1]
                assert action["price"] < known_price
                amendments += 1
        stop_hits = path.LowPrice.to_numpy() <= effective if row.direction > 0 else path.HiPrice.to_numpy() >= effective
        target_hits = path.HiPrice.ge(row.target_price).to_numpy() if row.direction > 0 else path.LowPrice.le(row.target_price).to_numpy()
        terminal = stop_hits | target_hits
        if row.exit_reason == "EXPIRY_NEXT_REAL_OPEN":
            assert not terminal[:-1].any()
            np.testing.assert_allclose(row.exit_price, path.OpenPrice.iloc[-1])
        elif row.exit_reason == "EXPIRY":
            assert not terminal.any() and row.exit_at == row.expiry_at
            np.testing.assert_allclose(row.exit_price, path.ClosePrice.iloc[-1])
        else:
            assert terminal.any() and np.flatnonzero(terminal)[0] == len(path) - 1
            if "STOP" in row.exit_reason:
                assert stop_hits[-1]
                expected = path.OpenPrice.iloc[-1] if row.exit_reason.endswith("GAP") else effective[-1]
                np.testing.assert_allclose(row.exit_price, expected)
            else:
                assert row.exit_reason == "TARGET" and target_hits[-1] and not stop_hits[-1]
                np.testing.assert_allclose(row.exit_price, row.target_price)
        fills = json.loads(row.fills_json)
        risk = abs(row.stop_price - row.entry_price)
        if row.partial_filled:
            first = fills[0]
            assert first["fraction"] == .5 and first["reason"] == "PARTIAL_2R" and row.direction > 0
            np.testing.assert_allclose(first["price"], row.entry_price + 2 * risk)
            hit = path.HiPrice.ge(first["price"]).to_numpy()
            p = np.flatnonzero(hit)[0]
            assert path.Timestamp.iloc[p].value == first["at"] and not stop_hits[p]
            partials += 1
        quantity = 3000 / row.entry_price
        assert abs(sum(x["fraction"] for x in fills) - 1) < 1e-12
        gross = sum(row.direction * (x["price"] - row.entry_price) * x["fraction"] * quantity for x in fills)
        slippage = (row.entry_price + sum(x["price"] * x["fraction"] for x in fills)) * quantity * .0002
        np.testing.assert_allclose([row.gross_usd, row.slippage_usd, row.net_usd], [gross, slippage, gross - 5 - slippage], atol=1e-8)
        checked += 1
print(f"Independently verified {checked} complete trade paths", flush=True)

bars = features(feed)
execution_bars, known = execution_references(feed, spot, bars)
future_data, data = ReplayData(feed, bars), ReplayData(spot, execution_bars)
original = hybrid_signals(bars, spec["long"], spec["short"])
candidates, _ = candidate_map(future_data, original, spec, {"short_space_1r": True}, h4_inventory(feed, bars))
direction = np.zeros_like(original)
for i, row in candidates.items():
    direction[i] = row["side"]
reference = replay_hybrid(data, direction, spec["long"], spec["short"])
selected = pd.read_csv(OUT / "variant_ledgers/SPOT_40F_FIXED.csv")
for field in ["decision_at", "entry_at", "exit_at", "expiry_at", "basis_spot_close_at", "basis_futures_close_at"]:
    selected[field] = pd.to_datetime(selected[field], utc=True)
pd.testing.assert_frame_equal(selected[reference.columns], reference, check_exact=False, rtol=1e-10, atol=1e-10)
for row in selected.itertuples():
    i = int(row.signal_index)
    quote = known.iloc[i]
    assert quote.spot_close_at <= row.decision_at and quote.futures_close_at <= row.decision_at
    assert row.decision_at - quote.spot_close_at <= pd.Timedelta(minutes=1)
    assert row.decision_at - quote.futures_close_at <= pd.Timedelta(minutes=1)
    ratio = quote.spot_close / quote.futures_close
    np.testing.assert_allclose(row.basis_ratio_at_decision, ratio)
    config = spec["long" if row.direction > 0 else "short"]["exit"]
    stop = min(bars.lower6.iloc[i] * .9995 * ratio, row.entry_price - bars.atr.iloc[i] * config["atr_floor"] * ratio) if row.direction > 0 else max(
        bars.upper6.iloc[i] * 1.0005 * ratio, row.entry_price + bars.atr.iloc[i] * config["atr_floor"] * ratio)
    np.testing.assert_allclose([row.stop_price, row.target_price], [stop, row.entry_price + row.direction * config["target_r"] * abs(row.entry_price - stop)])
selected["trade_id"] = [hashlib.sha256(f"40G|{r.family}|{r.decision_at}|{r.direction}".encode()).hexdigest()[:24] for r in selected.itertuples()]
selected["planned_target_profit_quote"] = selected.initial_risk_usd * selected.target_R
selected.to_csv(OUT / "selected_spot_trade_ledger.csv", index=False)
core = selected.loc[selected.entry_at.between(pd.Timestamp("2026-04-01T00:00:00Z"), pd.Timestamp("2026-10-01T00:00:00Z"), inclusive="left")]
short = selected.loc[selected.direction.lt(0)]
borrow_base = float((short.quantity_btc * short.exit_price * short.holding_hours / 24).sum())
borrow = [{"assumed_daily_short_BTC_borrow_percent": rate * 100, "prorated_interest_quote": rate * borrow_base,
           "net_after_hypothetical_short_borrow_quote": float(selected.net_usd.sum()) - rate * borrow_base}
          for rate in [0., .0001, .0003, .001]]
summary = {"version": "SHI_RESET_40G_SPOT_PRICE_REPLAY_V1", "primary_variant": "SPOT_40F_FIXED",
           "signal_market": "BTCUSDT_PERPETUAL_FUTURES", "execution_market": "BINANCE_SPOT_MARGIN_BTCUSDC_PRICE_MODEL",
           "reporting_currency": "USDC", "USDC_USD_parity_for_dollar_display_assumed": True,
           "full_history": metrics(selected), "six_month_entry_cohort": metrics(core),
           "long": metrics(selected.loc[selected.direction.gt(0)]), "short": metrics(short),
           "positive_trades": int(selected.net_usd.gt(0).sum()), "negative_trades": int(selected.net_usd.lt(0).sum()),
           "mean_planned_target_R": float(selected.target_R.mean()), "mean_planned_target_profit_quote": float(selected.planned_target_profit_quote.mean()),
           "net_R_sum": float(selected.net_R.sum()), "mean_holding_hours": float(selected.holding_hours.mean()),
           "isolated_no_trade_spot_minutes_skipped_in_selected_paths": int(selected.omitted_minutes.sum()),
           "old_futures_proxy_full_net": 671.0501074032345,
           "hypothetical_borrow_sensitivity": borrow, "borrow_rates_are_assumed_not_account_tariffs": True,
           "borrow_model_is_prorated_not_verified_exchange_charging": True,
           "historical_borrow_availability_orderbook_and_actual_fills_unverified": True,
           "primary_selected_to_preserve_frozen_stop_source_contract": True,
           "native_spot_stop_sensitivity_is_a_different_reference_contract": True,
           "pristine_holdout": False, "production_promoted": False}
(OUT / "selected_spot_result.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
contract = {"version": summary["version"], "futures_signal_baseline": spec, "futures_short_space_gate": "40F unchanged; decision-close risk space1R",
            "spot_stop_mapping": manifest["price_reference_mapping"], "execution_market": summary["execution_market"],
            "management": "FIXED_INITIAL_STOP_FULL_TARGET_10R_LONG_6R_SHORT_168H_EXPIRY", "notional_quote": 3000,
            "round_trip_fee_quote": 5, "slippage_bps_per_fill": 2, "study_code_hashes": manifest["study_code_hashes"],
            "spot_csv_sha256": manifest["spot_csv_sha256"], "source_preparation": spec["source_preparation"],
            "separate_signal_and_execution_feeds": True, "pristine_holdout": False, "production_promoted": False}
(OUT / "selected_spot_contract.json").write_text(json.dumps(contract, sort_keys=True, indent=2) + "\n")
sources = json.loads((OUT / "spot_BTCUSDC/source_manifest.json").read_text())
assert all(digest(OUT / "spot_BTCUSDC/raw" / r["name"]) == r["sha256"] for r in sources["archives"])
verification = {"independently_checked_trade_paths": checked, "partial_paths_checked": partials, "active_trail_amendments_checked": amendments,
                "all_13_variants_observed_first_terminal_touches_cash_and_clocks": True,
                "selected_matches_unchanged_original_replay_engine": True, "asof_reference_translation_geometry_verified": True,
                "all_48_official_archives_unchanged": True, "source_identity_verified": True,
                "old_baselines_and_original_code_preserved": all(digest(ROOT / p) == sha for p, sha in manifest["preserved_hashes"].items()),
                "study_code_identity_verified": all(digest(OUT / p) == sha for p, sha in manifest["study_code_hashes"].items())}
assert verification["old_baselines_and_original_code_preserved"] and verification["study_code_identity_verified"]
(OUT / "independent_verification.json").write_text(json.dumps(verification, sort_keys=True, indent=2) + "\n")
print(json.dumps({"primary_spot_net_USDC": summary["full_history"]["net_usd"], "six_month_net_USDC": summary["six_month_entry_cohort"]["net_usd"],
                  "trades": len(selected), "independent_engine_reproduction": True, "prorated_short_borrow_sensitivities": borrow}))
