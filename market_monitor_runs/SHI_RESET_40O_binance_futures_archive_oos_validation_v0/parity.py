"""Known2026 raw/features/decisions only. This program has no OOS replay call."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

from archive_source import OUT, read_kline_zip, save, sha
from phase_policy import decisions_equal, verify_hashes
from research_kernel import SNAP, H, RULES, identity, executed_hashes, read_sources, build_state, ReplayData, initial_stop, ExitRules

ROOT = OUT.parents[1]
START = pd.Timestamp("2026-03-11T13:45:00Z")
END = pd.Timestamp("2026-09-30T23:59:00Z")
WINDOWS = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in json.loads((OUT / "run_manifest.json").read_text())["source_validation_windows"]]


def in_windows(stamps):
    mask = np.zeros(len(stamps), dtype=bool)
    for start, end in WINDOWS:
        mask |= stamps.between(start, end).to_numpy()
    return mask


def archive_feed():
    manifest = json.loads((OUT / "source_manifest.json").read_text())
    assert len(manifest["archives"]) == 27 and all(r["status"] == "CHECKSUM_VERIFIED" for r in manifest["archives"])
    parts = []
    for record in manifest["archives"]:
        path = OUT / record["archive_path"]
        assert sha(path) == record["local_sha256"] == record["binance_checksum_sha256"]
        part = read_kline_zip(path)
        part["SourceFile"] = record["archive_path"]
        parts.append(part)
    feed = pd.concat(parts, ignore_index=True).sort_values("Timestamp").reset_index(drop=True)
    assert not feed.Timestamp.duplicated().any()
    feed = feed.loc[feed.Timestamp.between(START, END)].reset_index(drop=True)
    assert feed.Timestamp.iloc[0] == START and feed.Timestamp.iloc[-1] == END
    folder = OUT / "normalized_futures_feed"
    folder.mkdir(exist_ok=True)
    for day, group in feed.groupby(feed.Timestamp.dt.strftime("%Y-%m-%d")):
        group.to_csv(folder / (day + ".csv"), index=False)
    save("normalization_manifest.json", {"rows": len(feed), "first": feed.Timestamp.min(), "last": feed.Timestamp.max(),
         "clock": "exchange open+60s; exchange close clock preserved separately", "prices_decimals": 2, "base_quantity_decimals": 6,
         "rounding": "Decimal ROUND_HALF_EVEN; sell derived from unrounded total-buy before6dec quantization",
         "unused_context": "OI/funding/liquidations zero schema placeholders with availability=false; not evidence or filters",
         "files": {p.name: sha(p) for p in sorted(folder.glob("*.csv"))}})
    return feed


def raw_parity(shi, archive):
    shi = shi.loc[in_windows(shi.Timestamp)].copy()
    archive = archive.loc[in_windows(archive.Timestamp)].copy()
    shi["Traded"] = shi.Trades.gt(0) & shi.TotalQty.gt(0) & shi.IsSynthetic.eq(0) & shi.DataQuality.eq("RAW")
    fields = ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice", "TotalQty", "BuyQty", "SellQty"]
    joined = shi[["Timestamp", "Traded", *fields]].merge(archive[["Timestamp", "Traded", *fields]], on="Timestamp", how="outer", suffixes=("_shi", "_archive"), indicator=True)
    real = joined.Traded_shi.eq(True) & joined.Traded_archive.eq(True) & joined._merge.eq("both")
    mismatch = joined._merge.ne("both") | joined.Traded_shi.ne(joined.Traded_archive)
    summaries = []
    for start, end in WINDOWS:
        group = joined.loc[joined.Timestamp.between(start, end)]
        real_group = real.loc[group.index]
        metrics = {}
        for field in fields:
            tolerance = 1e-8 if field.endswith("Price") else 1.0001e-6
            diff = (joined[field + "_shi"] - joined[field + "_archive"]).abs()
            joined[field + "_abs_diff"] = diff
            bad = real & diff.gt(tolerance)
            mismatch |= bad
            metrics[field] = {"compared_real_minutes": int(real_group.sum()), "mismatches": int(bad.loc[group.index].sum()),
                              "maximum_absolute_deviation": float(diff.loc[group.index][real_group].max()), "tolerance": tolerance}
        summaries.append({"start": start, "end": end, "timestamps": len(group), "missing_or_extra_timestamps": int(group._merge.ne("both").sum()),
                          "traded_status_mismatches": int(group.Traded_shi.ne(group.Traded_archive).sum()), "fields": metrics})
    joined.loc[mismatch].to_csv(OUT / "raw_parity_mismatches.csv", index=False)
    result = {"windows": summaries, "total_aligned_rows": len(joined), "minutes_with_any_mismatch": int(mismatch.sum()),
              "Trades_exact_count_is_strategy_relevant": False, "Trades_count_equality_required": False,
              "traded_semantics_compared": True, "numeric_comparison_only_for_mutually_real_traded_minutes": True,
              "quantity_tolerance_reason": "Each SHI quantity rounded independently at6dec; allow1e-6 combined quantization tolerance. Price2dec exact within1e-8."}
    save("raw_parity_summary.json", result)
    return result


def decision_states(bars):
    return pd.DataFrame({"long_ema_order": bars.ema24.gt(bars.ema72), "long_above_ema168": bars.close.gt(bars.ema168),
        "long_retest_green_reclaim": bars.low.le(bars.ema24) & bars.close.gt(bars.ema24) & bars.close.gt(bars.open),
        "long_flow4pct": bars.delta.ge(.04), "volume1_3": bars.volume_ratio.ge(1.3),
        "long_maturity1_5": ((bars.close-bars.ema24).abs()/bars.atr).le(1.5), "long_impulse2": ((bars.high-bars.low)/bars.atr).le(2),
        "short_negative_pressure": bars.change24.lt(0) & bars.delta24.lt(0), "short_flow_nonpositive": bars.delta.le(0),
        "raw24_band4": bars.window24_usable & bars.delta24_pct.abs().lt(4), "long_raw4_positive": bars.window4_usable & bars.delta4_pct.gt(0),
        "h1_usable": bars.usable, "context_usable": bars.context_usable})


def compare_features(shi, archive):
    a = shi.loc[in_windows(shi.timestamp)].set_index("timestamp")
    b = archive.loc[in_windows(archive.timestamp)].set_index("timestamp")
    assert a.index.equals(b.index), "Completed H1 timestamp mismatch"
    numeric = ["open", "high", "low", "close", "volume", "delta", "delta24", "change24", "ema24", "ema72", "ema168", "atr", "volume_ratio",
               "lower6", "upper6", "lower48", "upper48", "lower96", "upper96", "delta4_pct", "delta24_pct", "long_stop_estimate", "short_stop_estimate"]
    parts = []
    for field in numeric:
        tolerance = 1.0001e-6 if field == "volume" else 1e-8 if field in ["open", "high", "low", "close", "ema24", "ema72", "ema168", "atr", "lower6", "upper6", "lower48", "upper48", "lower96", "upper96", "long_stop_estimate", "short_stop_estimate"] else 1e-10
        parts.append(pd.DataFrame({"timestamp": a.index, "field": field, "shi": a[field].to_numpy(), "archive": b[field].to_numpy(),
                                  "absolute_deviation": (a[field]-b[field]).abs().to_numpy(), "tolerance": tolerance,
                                  "equal": np.isclose(a[field], b[field], rtol=0, atol=tolerance, equal_nan=True)}))
    for field in ["available_at", "usable", "context_usable", "window4_usable", "window24_usable", "h4_inventory_hash"]:
        parts.append(pd.DataFrame({"timestamp": a.index, "field": field, "shi": a[field].astype(str).to_numpy(), "archive": b[field].astype(str).to_numpy(),
                                  "absolute_deviation": np.nan, "tolerance": 0, "equal": a[field].eq(b[field]).to_numpy()}))
    astates, bstates = decision_states(a), decision_states(b)
    for field in astates:
        parts.append(pd.DataFrame({"timestamp": a.index, "field": field, "shi": astates[field].to_numpy(), "archive": bstates[field].to_numpy(),
                                  "absolute_deviation": np.nan, "tolerance": 0, "equal": astates[field].eq(bstates[field]).to_numpy()}))
    result = pd.concat(parts, ignore_index=True)
    result.to_csv(OUT / "feature_parity.csv", index=False)
    save("feature_parity_summary.json", {"comparisons": len(result), "mismatches": int((~result.equal).sum()),
         "by_field_mismatches": result.loc[~result.equal].groupby("field").size().to_dict(),
         "tolerance_rule": "Only numeric rounding/float tolerances; no threshold/level/gate mismatch accepted."})
    return result


def compare_candidates(shi, archive):
    fields = ["timestamp", "raw_direction", "final_direction", "blocker_reasons", "h4_inventory_hash"]
    a = shi.loc[in_windows(shi.timestamp), fields]
    b = archive.loc[in_windows(archive.timestamp), fields]
    equal = decisions_equal(a, b)
    joined = a.merge(b, on="timestamp", how="outer", suffixes=("_shi", "_archive"))
    joined["raw_candidate_equal"] = joined.raw_direction_shi.eq(joined.raw_direction_archive)
    joined["final_direction_equal"] = joined.final_direction_shi.eq(joined.final_direction_archive)
    joined["blocker_reasons_equal"] = joined.blocker_reasons_shi.eq(joined.blocker_reasons_archive)
    joined["decision_equal"] = equal.reindex(pd.DatetimeIndex(joined.timestamp)).to_numpy()
    joined.to_csv(OUT / "candidate_parity.csv", index=False)
    report = []
    for start, end in WINDOWS:
        part = joined.loc[joined.timestamp.between(start, end)]
        union = part.raw_direction_shi.ne(0) | part.raw_direction_archive.ne(0)
        report.append({"start": start, "end": end, "H1_rows": len(part), "shi_raw_candidates": int(part.raw_direction_shi.ne(0).sum()),
                       "archive_raw_candidates": int(part.raw_direction_archive.ne(0).sum()), "union_raw_candidates": int(union.sum()),
                       "raw_candidate_mismatches": int((~part.raw_candidate_equal).sum()), "final_direction_mismatches": int((~part.final_direction_equal).sum()),
                       "blocker_reason_mismatches": int((~part.blocker_reasons_equal).sum()),
                       "full_candidate_gate_decision_parity_pct": float(part.decision_equal.mean()*100),
                       "final_allowed_direction_parity_pct": float(part.final_direction_equal.mean()*100),
                       "union_candidate_decision_parity_pct": float(part.loc[union, "decision_equal"].mean()*100) if union.any() else 100.})
    save("candidate_parity_summary.json", {"windows": report, "decision_mismatches": int((~joined.decision_equal).sum()),
         "final_gate_decision_parity_pct": float(joined.final_direction_equal.mean()*100),
         "full_candidate_gate_decision_parity_pct": float(joined.decision_equal.mean()*100)})
    return joined, report


def causality(shi_feed, archive_feed, spec, shi_full, archive_full):
    cutoff = pd.Timestamp("2026-07-15T12:30:00Z")
    results = []
    for label, feed, full in [("SHI", shi_feed, shi_full), ("BINANCE_KLINES", archive_feed, archive_full)]:
        prefix, _, _, _, _ = build_state(feed.loc[feed.Timestamp.le(cutoff)].reset_index(drop=True), spec)
        expected = full.loc[full.available_at.le(cutoff)].reset_index(drop=True)
        pd.testing.assert_frame_equal(prefix, expected)
        results.append({"source": label, "prefix_cutoff": cutoff, "closed_H1_steps": len(prefix), "all_features_H4_candidates_filters_identical": True})
    report = {"status": "PASS", "clock": "Original SHI receipt/flush right-close labels versus archive exchange open+60s right-close labels; no fitted shift",
              "rolling_window": "(decision-h,decision]", "real_prefix_results": results,
              "no_future_entry_used_in_H4_gate": True, "OOS_observations_or_returns_accessed": False}
    save("causality_checks.json", report)
    return report


def main():
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    verify_hashes(ROOT, manifest["immutable_source_and_strategy_hashes"])
    assert json.loads((OUT / "frozen_identity_verification.json").read_text())["status"] == "FROZEN40H_EXACT_CONTROL_REPRODUCED"
    code = {p.name: sha(p) for p in sorted(OUT.glob("*.py"))}
    save("parity_execution_manifest.json", {"phase": "FROZEN_BEFORE_KNOWN_SOURCE_PARITY_DECISIONS", "task_code_hashes": code,
         "frozen_executed_code_hashes": executed_hashes(), "variants": 1, "OOS_access": False})
    selected = identity()
    spec = selected["baseline_contract"]["futures_signal_baseline"]
    shi_feed, source_inventory = read_sources(SNAP, str(START), str(END))
    source_inventory.to_csv(OUT / "preserved_SHI_source_inventory.csv", index=False)
    arc_feed = archive_feed()
    raw = raw_parity(shi_feed, arc_feed)
    print("Known2026 raw parity recorded; reconstructing both frozen whole-history states", flush=True)
    shi, _, _, _, _ = build_state(shi_feed, spec)
    print("Original SHI chronological state complete", flush=True)
    archive, _, _, _, _ = build_state(arc_feed, spec)
    print("Archive chronological state complete; comparing decisions and references", flush=True)
    feature = compare_features(shi, archive)
    candidate, windows = compare_candidates(shi, archive)
    causality(shi_feed, arc_feed, spec, shi, archive)
    accepted = bool(candidate.decision_equal.all() and feature.equal.all())
    gate = {"status": "ACCEPTED_100_PERCENT_DECISION_PARITY" if accepted else "BINANCE_KLINE_SURROGATE_PARITY_FAILED",
            "accepted": accepted, "raw_minutes_with_any_mismatch": raw["minutes_with_any_mismatch"],
            "feature_mismatches": int((~feature.equal).sum()), "candidate_decision_mismatches": int((~candidate.decision_equal).sum()),
            "final_direction_mismatches": int((~candidate.final_direction_equal).sum()),
            "full_candidate_gate_decision_parity_pct": float(candidate.decision_equal.mean()*100),
            "final_allowed_direction_parity_pct": float(candidate.final_direction_equal.mean()*100),
            "OOS_execution_allowed": accepted, "OOS_downloaded": False, "OOS_outcomes_read": False,
            "task_code_hashes": code, "frozen_executed_code_hashes": executed_hashes()}
    save("parity_gate.json", gate)
    if accepted:
        save("parity_acceptance.json", {**gate, "status": "ACCEPTED_100_PERCENT_DECISION_PARITY", "candidate_parity_sha256": sha(OUT / "candidate_parity.csv")})
    lines = ["#40O — known2026 Binance futures kline parity", "", f"Verdict: **{gate['status']}**.",
             "", "Raw archive → rounded right-close minutes → independent whole-history H1/H4 → unchanged features → unchanged hybrid candidates →40F H4-space →40H delta gates. No OOS financial result accessed.",
             "", f"Raw mismatching minutes: {gate['raw_minutes_with_any_mismatch']}; feature comparisons failing declared tolerance/state equality: {gate['feature_mismatches']}.",
             f"Full candidate/gate decision mismatches: {gate['candidate_decision_mismatches']}; final allowed-direction mismatches: {gate['final_direction_mismatches']}.",
             "", "|Window|SHI raw candidates|Archive raw candidates|Final direction mismatches|Full decision parity|", "|---|---:|---:|---:|---:|"]
    for w in windows:
        lines.append(f"|{w['start']}–{w['end']}|{w['shi_raw_candidates']}|{w['archive_raw_candidates']}|{w['final_direction_mismatches']}|{w['full_candidate_gate_decision_parity_pct']:.6f}%|")
    lines += ["", "See every raw mismatch in raw_parity_mismatches.csv, every compared feature in feature_parity.csv, and every H1 candidate/gate/blocker in candidate_parity.csv. Real-prefix checks reconstruct prior state; no technical reset.",
              "", "OI/funding/liquidations are unavailable placeholders and do not participate in selected gates. Trades exact count is not required; traded/non-traded semantics are compared."]
    (OUT / "parity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(gate, indent=2), flush=True)


if __name__ == "__main__":
    main()
