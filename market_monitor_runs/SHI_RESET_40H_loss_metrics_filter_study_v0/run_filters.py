from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from study import ROOT, G, load, save, digest, replay_hybrid, metrics
from filters import VARIANTS, filtered_directions, allow_rule


def compare(baseline, current, f, allowed, variant):
    old = baseline.set_index("signal_index")
    new = current.set_index("signal_index")
    allowed_by_index = dict(zip(f.signal_index, allowed))
    records = []
    for i, row in old.iterrows():
        present = i in new.index
        records.append({"variant": variant["id"], "signal_index": i, "direction": row.direction,
                        "baseline_entry_at": row.entry_at, "baseline_exit_at": row.exit_at,
                        "baseline_net_quote": row.net_usd, "baseline_outcome": "WIN" if row.net_usd > 0 else "LOSS",
                        "status": "RETAINED" if present else "BLOCKED_BY_FILTER" if not allowed_by_index[i] else "DISPLACED_BY_BOOK",
                        "failed_rules": ";".join(r for r in variant["rules"] if not bool(allow_rule(f.loc[f.signal_index.eq(i)], r).iloc[0])),
                        "current_net_quote": new.loc[i, "net_usd"] if present else np.nan})
    for i, row in new.loc[~new.index.isin(old.index)].iterrows():
        records.append({"variant": variant["id"], "signal_index": i, "direction": row.direction,
                        "baseline_entry_at": pd.NaT, "baseline_exit_at": pd.NaT, "baseline_net_quote": np.nan,
                        "baseline_outcome": "NOT_IN_BASELINE", "status": "NEWLY_ADMITTED",
                        "failed_rules": "", "current_net_quote": row.net_usd, "current_entry_at": row.entry_at})
    result = pd.DataFrame(records)
    removed = result.loc[result.status.isin(["BLOCKED_BY_FILTER", "DISPLACED_BY_BOOK"])]
    new_rows = result.loc[result.status.eq("NEWLY_ADMITTED")]
    saved_losses = -removed.loc[removed.baseline_outcome.eq("LOSS"), "baseline_net_quote"].sum()
    lost_wins = removed.loc[removed.baseline_outcome.eq("WIN"), "baseline_net_quote"].sum()
    delta = current.net_usd.sum() - baseline.net_usd.sum()
    np.testing.assert_allclose(delta, saved_losses - lost_wins + new_rows.current_net_quote.sum(), atol=1e-8)
    return result, {"removed_losses": int(removed.baseline_outcome.eq("LOSS").sum()), "saved_loss_quote": saved_losses,
                    "removed_wins": int(removed.baseline_outcome.eq("WIN").sum()), "lost_win_quote": lost_wins,
                    "new_trades": len(new_rows), "new_trades_net_quote": new_rows.current_net_quote.sum(), "net_change_quote": delta}


def main():
    scope = {"phase": "ADAPTIVE_FILTERS_FIXED_AFTER_21_TRADE_DIAGNOSIS_BEFORE_FILTER_RETURNS", "variants": VARIANTS,
             "diagnostic_manifest_sha256": digest(OUT / "diagnostic_manifest.json"),
             "diagnostic_trade_csv_sha256": digest(OUT / "baseline_trade_entry_metrics.csv"),
             "candidate_feature_csv_sha256": digest(OUT / "all_candidate_entry_metrics.csv"),
             "rules_code_sha256": digest(OUT / "filters.py"), "runner_code_sha256": digest(Path(__file__)),
             "scope": "22 declared portfolios including control; no exit/cost/target change. All failures/censors retained.",
             "reason": "Test delta4 confirmation, delta24 exhaustion with2/4/6 sensitivity, OI, liquidation, range, volume, funding and coarse UTC windows. Thresholds exploratory on exposed history.",
             "selection": "Cash ranking diagnostic, no production promotion. Prefer mechanistic rule simplicity and threshold stability over fitted calendar exclusions."}
    dest = OUT / "filter_manifest.json"
    if dest.exists():
        assert json.loads(dest.read_text()) == scope
    else:
        save(dest.name, scope)
    feed, spot, bars, fdata, sdata, directions, original, spec, quotes = load()
    f = pd.read_csv(OUT / "all_candidate_entry_metrics.csv")
    baseline = replay_hybrid(sdata, directions, spec["long"], spec["short"])
    summaries, attribution = [], []
    ledgers = OUT / "variant_ledgers"
    ledgers.mkdir(exist_ok=True)
    for v in VARIANTS:
        dirs, allowed = filtered_directions(directions, f, v)
        t = replay_hybrid(sdata, dirs, spec["long"], spec["short"])
        t["trade_id"] = [f"40H-{int(i)}-{int(d)}" for i,d in zip(t.signal_index, t.direction)]
        t["holding_hours"] = (t.exit_at - t.entry_at).dt.total_seconds() / 3600
        t.to_csv(ledgers / f'{v["id"]}.csv', index=False)
        a, changes = compare(baseline, t, f, allowed, v)
        attribution.append(a)
        closed = t.loc[~t.censored]
        core = t.loc[t.entry_at.ge(pd.Timestamp("2026-04-01T00:00Z")) & t.entry_at.lt(pd.Timestamp("2026-10-01T00:00Z"))]
        record = {"variant": v["id"], **metrics(t), **changes, "wins": int(closed.net_usd.gt(0).sum()),
                  "losses": int(closed.net_usd.lt(0).sum()), "stops": int(closed.exit_reason.str.startswith("STOP").sum()),
                  "long_net_quote": closed.loc[closed.direction.gt(0), "net_usd"].sum(),
                  "short_net_quote": closed.loc[closed.direction.lt(0), "net_usd"].sum(),
                  "six_month_net_quote": metrics(core)["net_usd"], "six_month_censored": metrics(core)["censored"],
                  "mean_planned_target_R": t.target_R.mean(), "mean_planned_target_quote": (t.target_R * t.initial_risk_usd).mean(),
                  "max_initial_risk_quote": t.initial_risk_usd.max(), "omitted_minutes": t.omitted_minutes.sum()}
        summaries.append(record)
        print(f'{v["id"]}: {len(t)} trades, {record["wins"]}+/{record["losses"]}-, {record["censored"]} censored, net{record["net_usd"]:.2f}, removed{record["removed_wins"]}wins/{record["removed_losses"]}losses, new{record["new_trades"]}', flush=True)
    pd.DataFrame(summaries).to_csv(OUT / "filter_results.csv", index=False)
    pd.concat(attribution, ignore_index=True).to_csv(OUT / "every_variant_trade_attribution.csv", index=False)
    save("filter_run_verification.json", {"declared_variants": len(VARIANTS), "completed_variants": len(summaries),
          "all_baseline_difference_cash_reconciled": True, "one_global_book_full_replays": True,
          "fixed_original_engine_no_cost_exit_changes": True,
          "all_diagnostic_baseline_hashes_unchanged": all(digest(ROOT / p) == sha for p,sha in json.loads((OUT / "diagnostic_manifest.json").read_text())["baseline_hashes"].items())})


if __name__ == "__main__":
    main()
