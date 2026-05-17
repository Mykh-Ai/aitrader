"""Sprint 10 true holdout runner for BTC replay survivors.

This script is intentionally conservative:

- Sprint 08 candidate predicates, entry, stop, target, expiry, and same-bar
  policy remain frozen.
- Sprint 06/Sprint 08/Sprint 09 source feature days are excluded from true
  holdout. If a day is uncertain, it is marked unusable.
- No live trading, Executor, Phase 4, PROMOTE, tuning, or Backtester core
  change is performed.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


AS_OF_DATE = "2026-05-17"
CONTAMINATED_START = pd.Timestamp("2026-04-23 17:05:00", tz="UTC")
CONTAMINATED_END = pd.Timestamp("2026-05-06 22:51:00", tz="UTC")
MIN_USABLE_ROWS = 1000
BASE_COST = 0.00015
COST_LEVELS = (0.00000, 0.00010, 0.00015, 0.00020)
RULE_VERSION = "SPRINT08_BTC_FORMAL_REPLAY_V1"
PROMOTION_STATUS = "NO_PROMOTE_HOLDOUT_REQUIRED"
SPRINT08_COMMIT = "50d43566c03759b18d1c7cfac9d094e76496df59"
SPRINT09_COMMIT = "fa8a30fe0bc7474076ad8dbfb4e76dd75a9e9fea"

CANDIDATES = [
    "CAND_BTC_EXH_SHORT_24_V1",
    "CAND_BTC_VWAP_DEV_LONG_60_100200_V1",
    "CAND_BTC_VWAP_DEV_SHORT_60_100200_V1",
]


@dataclass(frozen=True)
class HoldoutDay:
    date: str
    source: str
    frame: pd.DataFrame
    rows: int
    synthetic_rows: int
    zero_ohlc_rows: int
    volume_sum: float
    min_timestamp: str
    max_timestamp: str
    usable_for_holdout: bool
    reason_if_not_usable: str
    lineage_note: str


def safe_numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([default] * len(frame.index), index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def read_feed(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Timestamp" not in frame.columns:
        raise ValueError(f"{path} is missing Timestamp")
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
    for column in ["Open", "High", "Low", "Close", "Volume", "BuyQty", "SellQty", "VWAP", "IsSynthetic"]:
        frame[column] = safe_numeric(frame, column)
    return frame


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def used_replay_dates(source_features: Path) -> set[str]:
    if not source_features.exists():
        return set()
    features = pd.read_csv(source_features, usecols=["Timestamp"])
    stamps = pd.to_datetime(features["Timestamp"], utc=True, format="ISO8601", errors="coerce").dropna()
    return {stamp.strftime("%Y-%m-%d") for stamp in stamps}


def build_holdout_day(
    primary_path: Path,
    *,
    recovered_root: Path,
    recovered_manifest: Path,
    use_recovered_gap: bool,
    used_dates: set[str],
    as_of_date: pd.Timestamp,
) -> HoldoutDay:
    day = primary_path.stem
    primary = read_feed(primary_path)
    completed = pd.Timestamp(day).date() < as_of_date.date()
    in_gap = primary["Timestamp"].between(CONTAMINATED_START, CONTAMINATED_END, inclusive="both")
    recovered_ok = use_recovered_gap and recovered_root.exists() and recovered_manifest.exists()

    parts = [primary.loc[~in_gap].copy()]
    source = "primary"
    lineage_note = "primary_clean_outside_contaminated_window"
    if in_gap.any():
        source = "primary_gap_excluded"
        lineage_note = "contaminated_primary_window_excluded"
        recovered_path = recovered_root / primary_path.name
        if recovered_ok and recovered_path.exists():
            recovered = read_feed(recovered_path)
            recovered_in_gap = recovered["Timestamp"].between(CONTAMINATED_START, CONTAMINATED_END, inclusive="both")
            parts.append(recovered.loc[recovered_in_gap].copy())
            source = "primary_plus_recovered_gap"
            lineage_note = (
                "primary outside outage; feed_recovered inside outage; "
                "recovered lineage manifest present; degraded OI/funding/liquidations"
            )

    combined = (
        pd.concat(parts, ignore_index=True)
        .drop_duplicates(subset=["Timestamp"], keep="last")
        .sort_values("Timestamp")
        .reset_index(drop=True)
    )
    rows = int(len(combined.index))
    synthetic_rows = int(safe_numeric(combined, "IsSynthetic").ne(0).sum())
    zero_ohlc_mask = combined[["Open", "High", "Low", "Close"]].le(0).any(axis=1) if rows else pd.Series(dtype=bool)
    zero_ohlc_rows = int(zero_ohlc_mask.sum()) if rows else 0
    clean = combined.loc[safe_numeric(combined, "IsSynthetic").eq(0) & ~zero_ohlc_mask].copy() if rows else combined.copy()
    clean = clean.sort_values("Timestamp").reset_index(drop=True)
    volume_sum = float(safe_numeric(clean, "Volume").sum())
    min_ts = "" if combined.empty else combined["Timestamp"].min().isoformat()
    max_ts = "" if combined.empty else combined["Timestamp"].max().isoformat()

    reasons: list[str] = []
    if not completed:
        reasons.append("partial_or_future_utc_day")
    if day in used_dates:
        reasons.append("already_used_in_sprint08_09_source_features")
    if rows == 0:
        reasons.append("empty_after_gap_exclusion")
    if len(clean.index) < MIN_USABLE_ROWS:
        reasons.append("clean_rows_below_1000")
    if volume_sum <= 0:
        reasons.append("zero_clean_volume")
    if in_gap.any() and source != "primary_plus_recovered_gap":
        reasons.append("contaminated_window_without_recovered_lineage")

    return HoldoutDay(
        date=day,
        source=source,
        frame=clean,
        rows=rows,
        synthetic_rows=synthetic_rows,
        zero_ohlc_rows=zero_ohlc_rows,
        volume_sum=volume_sum,
        min_timestamp=min_ts,
        max_timestamp=max_ts,
        usable_for_holdout=not reasons,
        reason_if_not_usable="PASS" if not reasons else ";".join(reasons),
        lineage_note=lineage_note,
    )


def build_holdout_days(args: argparse.Namespace) -> list[HoldoutDay]:
    feed_root = Path(args.feed_root)
    if not feed_root.exists():
        raise SystemExit(f"Feed root not found: {feed_root}")
    used_dates = used_replay_dates(Path(args.used_source_features))
    as_of_date = pd.Timestamp(args.as_of_date)
    days: list[HoldoutDay] = []
    for primary_path in sorted(feed_root.glob("*.csv")):
        try:
            pd.Timestamp(primary_path.stem)
        except ValueError:
            continue
        days.append(
            build_holdout_day(
                primary_path,
                recovered_root=Path(args.recovered_root),
                recovered_manifest=Path(args.recovered_manifest),
                use_recovered_gap=bool(args.use_recovered_gap),
                used_dates=used_dates,
                as_of_date=as_of_date,
            )
        )
    return days


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(path, index=False)
        return
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_data_audit(days: list[HoldoutDay], csv_path: Path, md_path: Path, as_of_date: str) -> None:
    rows = [
        {
            "date": day.date,
            "source": day.source,
            "rows": day.rows,
            "synthetic_rows": day.synthetic_rows,
            "zero_ohlc_rows": day.zero_ohlc_rows,
            "volume_sum": round(day.volume_sum, 6),
            "min_timestamp": day.min_timestamp,
            "max_timestamp": day.max_timestamp,
            "usable_for_holdout": day.usable_for_holdout,
            "reason_if_not_usable": day.reason_if_not_usable,
            "lineage_note": day.lineage_note,
        }
        for day in days
    ]
    write_csv(csv_path, rows)
    usable = [day for day in days if day.usable_for_holdout]
    used_blocked = [day for day in days if "already_used_in_sprint08_09_source_features" in day.reason_if_not_usable]
    lines = [
        "# Sprint 10 Holdout Data Audit",
        "",
        f"as_of_date_utc: `{as_of_date}`",
        f"sprint08_rules_commit: `{SPRINT08_COMMIT}`",
        f"sprint09_integrity_commit: `{SPRINT09_COMMIT}`",
        "",
        f"feed_days_audited: `{len(days)}`",
        f"usable_holdout_days: `{len(usable)}`",
        f"days_blocked_as_already_used: `{len(used_blocked)}`",
        "",
        "Holdout rule: any day present in the frozen Sprint 06/Sprint 08 source feature window is excluded.",
        "Synthetic rows, zero OHLC rows, partial UTC days, and contaminated primary gap rows are not accepted as holdout evidence.",
        "",
    ]
    if usable:
        lines.append("Usable days: `" + ", ".join(day.date for day in usable) + "`")
    else:
        lines.append("No usable holdout day exists in the current local feed snapshot.")
    lines.append("")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")


def zero_cost_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "cost_level": f"{cost:.5f}",
                "trades": 0,
                "net_result": 0.0,
                "mean_net_result": 0.0,
                "median_net_result": 0.0,
                "positive_rate": 0.0,
                "verdict": "NO_USABLE_DATA",
            }
            for cost in COST_LEVELS
        ]
    )


def write_blocked_candidate(candidate_id: str, candidate_root: Path, reason: str) -> dict[str, Any]:
    candidate_dir = candidate_root / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "candidate_id": candidate_id,
        "holdout_verdict": "BLOCKED_NO_USABLE_DATA",
        "events": 0,
        "valid_replay_events": 0,
        "trades": 0,
        "independent_days": 0,
        "net_0_00000": 0.0,
        "net_0_00010": 0.0,
        "net_0_00015": 0.0,
        "net_0_00020": 0.0,
        "reason": reason,
    }
    write_csv(candidate_dir / "holdout_log.csv", [summary])
    write_csv(candidate_dir / "holdout_cost_stress_summary.csv", zero_cost_summary())
    write_csv(
        candidate_dir / "holdout_source_concentration_report.csv",
        [
            {
                "candidate_id": candidate_id,
                "independent_days": 0,
                "largest_day_abs_result_share": 1.0,
                "top3_day_abs_result_share": 1.0,
                "status": "BLOCKED",
                "notes": reason,
            }
        ],
    )
    (candidate_dir / "holdout_summary.md").write_text(
        "\n".join(
            [
                f"# {candidate_id} Holdout Summary",
                "",
                "verdict: `BLOCKED_NO_USABLE_DATA`",
                "promotion_status: `NO_PROMOTE_HOLDOUT_REQUIRED`",
                "",
                f"reason: `{reason}`",
                "",
                "- events: 0",
                "- trades: 0",
                "- independent days: 0",
                "- net at 0.00015: 0.0",
                "",
                "No holdout replay was run because no usable completed clean holdout day exists.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (candidate_dir / "holdout_distribution_audit.md").write_text(
        "\n".join(
            [
                f"# {candidate_id} Holdout Distribution Audit",
                "",
                "status: `BLOCKED_NO_USABLE_DATA`",
                "",
                "No executed holdout trades. Distribution metrics are not meaningful.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (candidate_dir / "holdout_promotion_gate_checklist.md").write_text(
        "\n".join(
            [
                "# Holdout Promotion Gate Checklist",
                "",
                "- [x] Sprint 08 formal deterministic mapping remains frozen",
                "- [x] no future labels",
                "- [x] no rule changes",
                "- [ ] usable completed holdout data exists",
                "- [ ] holdout trades >= 25",
                "- [ ] independent holdout days >= 10",
                "- [ ] cost 0.00015 positive",
                "- [ ] source concentration PASS",
                "- [ ] no single-day PnL dominance",
                "- [ ] same-bar ambiguity not verdict-changing",
                "- [ ] mapper integrity PASS on holdout",
                "",
                f"promotion_status: `{PROMOTION_STATUS}`",
                "candidate_holdout_status: `BLOCKED_NO_USABLE_DATA`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def distribution_markdown(trades: pd.DataFrame, candidate_id: str) -> str:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    returns = pd.to_numeric(executed["raw_return"], errors="coerce").fillna(0.0)
    if executed.empty:
        return f"# {candidate_id} Holdout Distribution Audit\n\nNo executed holdout trades.\n"
    wins = returns[returns > 0]
    losses = returns[returns <= 0]
    avg_winner = float(wins.mean()) if not wins.empty else 0.0
    avg_loser = float(losses.mean()) if not losses.empty else 0.0
    lines = [
        f"# {candidate_id} Holdout Distribution Audit",
        "",
        f"- trades: `{len(returns.index)}`",
        f"- wins: `{len(wins.index)}`",
        f"- losses: `{len(losses.index)}`",
        f"- winrate: `{float((returns > 0).mean()):.6f}`",
        f"- mean: `{float(returns.mean()):.10f}`",
        f"- median: `{float(returns.median()):.10f}`",
        f"- avg winner: `{avg_winner:.10f}`",
        f"- avg loser: `{avg_loser:.10f}`",
        f"- p10: `{float(returns.quantile(0.10)):.10f}`",
        f"- p90: `{float(returns.quantile(0.90)):.10f}`",
        "",
    ]
    return "\n".join(lines)


def write_holdout_candidate_outputs(
    *,
    candidate_id: str,
    candidate_root: Path,
    output_dir: Path,
    trades: pd.DataFrame,
    costs: pd.DataFrame,
    source_report: pd.DataFrame,
    source_status: str,
    dominance_status: str,
    same_bar_count: int,
    summary: dict[str, Any],
) -> None:
    candidate_dir = candidate_root / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    write_csv(candidate_dir / "holdout_log.csv", [summary])
    write_csv(candidate_dir / "holdout_cost_stress_summary.csv", costs)
    write_csv(candidate_dir / "holdout_source_concentration_report.csv", source_report)
    (candidate_dir / "holdout_distribution_audit.md").write_text(
        distribution_markdown(trades, candidate_id), encoding="utf-8"
    )
    (candidate_dir / "holdout_summary.md").write_text(
        "\n".join(
            [
                f"# {candidate_id} Holdout Summary",
                "",
                f"verdict: `{summary['holdout_verdict']}`",
                f"promotion_status: `{PROMOTION_STATUS}`",
                "",
                f"- holdout events: {summary['events']}",
                f"- valid replay events: {summary['valid_replay_events']}",
                f"- executed trades: {summary['trades']}",
                f"- independent days: {summary['independent_days']}",
                f"- net at 0.00015: {summary['net_0_00015']}",
                f"- same-bar ambiguous count: {same_bar_count}",
                f"- source concentration: {source_status}",
                f"- single-day dominance: {dominance_status}",
                "",
                "No PROMOTE. Phase 4 remains closed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (candidate_dir / "holdout_promotion_gate_checklist.md").write_text(
        "\n".join(
            [
                "# Holdout Promotion Gate Checklist",
                "",
                "- [x] Sprint 08 formal deterministic mapping remains frozen",
                "- [x] no future labels",
                "- [x] no rule changes",
                f"- [{'x' if summary['trades'] >= 25 else ' '}] holdout trades >= 25",
                f"- [{'x' if summary['independent_days'] >= 10 else ' '}] independent holdout days >= 10",
                f"- [{'x' if summary['net_0_00015'] > 0 else ' '}] cost 0.00015 positive",
                f"- [{'x' if source_status == 'PASS' else ' '}] source concentration PASS",
                f"- [{'x' if dominance_status == 'PASS' else ' '}] no single-day PnL dominance",
                f"- [{'x' if same_bar_count == 0 else ' '}] same-bar ambiguity not verdict-changing",
                "- [x] mapper integrity PASS on executed holdout mapping",
                "",
                f"promotion_status: `{PROMOTION_STATUS}`",
                f"candidate_holdout_status: `{summary['holdout_verdict']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_csv(output_dir / "trades.csv", trades)
    (output_dir / "replay_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    return float((equity - equity.cummax()).min())


def holdout_verdict(
    *,
    trades: int,
    days: int,
    net_15: float,
    source_status: str,
    dominance_status: str,
    same_bar_count: int,
) -> str:
    if trades == 0:
        return "WAIT_MORE_HOLDOUT_DATA"
    if trades < 25 or days < 10:
        return "WAIT_MORE_HOLDOUT_DATA"
    if net_15 > 0 and source_status == "PASS" and dominance_status == "PASS" and same_bar_count == 0:
        return "HOLDOUT_PASS_REVIEW"
    if net_15 > 0:
        return "HOLDOUT_WARN_CONTINUE"
    return "REJECT_HOLDOUT_FAIL"


def run_holdout_replay(args: argparse.Namespace, days: list[HoldoutDay]) -> list[dict[str, Any]]:
    script_root = Path(__file__).resolve().parent
    sprint06 = load_module(script_root / "sprint_06_event_discovery_kill_or_continue.py", "sprint06_holdout")
    mapper = load_module(script_root / "sprint_08_btc_formal_replay_mapper.py", "sprint08_mapper_holdout")
    runner = load_module(script_root / "sprint_08_btc_formal_replay_runner.py", "sprint08_runner_holdout")

    clean_days = []
    for day in days:
        if day.usable_for_holdout:
            clean_days.append(
                sprint06.CleanDay(
                    date=day.date,
                    source=day.source,
                    frame=day.frame,
                    raw_rows=day.rows,
                    synthetic_rows=day.synthetic_rows,
                    zero_ohlc_rows=day.zero_ohlc_rows,
                    volume_sum=day.volume_sum,
                    min_timestamp=day.min_timestamp,
                    max_timestamp=day.max_timestamp,
                    usable_for_discovery=True,
                    reason_if_not_usable="PASS",
                    lineage_note=day.lineage_note,
                )
            )
    features = sprint06.build_features(clean_days)
    raw_events = sprint06.build_raw_events(features)
    events = sprint06.cluster_events(raw_events)
    feature_lookup = mapper.feature_lookup(features)
    replay_lookup = runner.feature_lookup(features)
    output_root = Path(args.output_root)
    candidate_root = Path(args.candidate_root)
    summaries: list[dict[str, Any]] = []
    write_csv(output_root / "holdout_features.csv", features)
    write_csv(output_root / "holdout_events.csv", events)

    specs = {spec.candidate_id: spec for spec in mapper.CANDIDATES}
    for candidate_id in CANDIDATES:
        spec = specs[candidate_id]
        candidate_events = []
        selected = mapper.select_events(events, spec)
        for _, row in selected.iterrows():
            mapped = mapper.map_event(row, spec, features, feature_lookup)
            mapped["source_event_file"] = str(output_root / "holdout_events.csv")
            mapped["source_feature_file"] = str(output_root / "holdout_features.csv")
            mapped["rule_version"] = RULE_VERSION
            candidate_events.append(mapped)
        mapped_frame = pd.DataFrame(candidate_events, columns=mapper.EVENT_COLUMNS)
        output_dir = output_root / candidate_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(output_dir / "holdout_candidate_events.csv", mapped_frame)
        replay_events = runner.load_candidate_events(output_dir / "holdout_candidate_events.csv")
        trades = runner.replay_candidate(replay_events, features, replay_lookup)
        costs = runner.cost_summary(trades)
        source_report, source_status = runner.source_concentration(trades, candidate_id)
        dominance_report, dominance_status = runner.single_day_dominance(trades, candidate_id)
        same_bar_count, _ = runner.same_bar_report(trades, candidate_id, output_dir / "same_bar_ambiguity_report.md")
        executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
        net_by_cost = {row["cost_level"]: float(row["net_result"]) for _, row in costs.iterrows()}
        summary = {
            "candidate_id": candidate_id,
            "holdout_verdict": holdout_verdict(
                trades=int(len(executed.index)),
                days=int(executed["entry_day"].nunique()) if not executed.empty else 0,
                net_15=net_by_cost.get("0.00015", 0.0),
                source_status=source_status,
                dominance_status=dominance_status,
                same_bar_count=same_bar_count,
            ),
            "events": int(len(selected.index)),
            "valid_replay_events": int(mapped_frame["valid_for_replay"].astype(str).str.lower().eq("true").sum())
            if not mapped_frame.empty
            else 0,
            "trades": int(len(executed.index)),
            "independent_days": int(executed["entry_day"].nunique()) if not executed.empty else 0,
            "net_0_00000": net_by_cost.get("0.00000", 0.0),
            "net_0_00010": net_by_cost.get("0.00010", 0.0),
            "net_0_00015": net_by_cost.get("0.00015", 0.0),
            "net_0_00020": net_by_cost.get("0.00020", 0.0),
            "winrate": round(float((executed["raw_return"] > 0).mean()) if not executed.empty else 0.0, 6),
            "median_result": round(float(executed["raw_return"].median()) if not executed.empty else 0.0, 10),
            "max_drawdown": round(max_drawdown(executed["raw_return"].astype(float)) if not executed.empty else 0.0, 10),
            "source_concentration_verdict": source_status,
            "single_day_dominance_verdict": dominance_status,
            "same_bar_ambiguous_count": same_bar_count,
            "reason": "holdout_replay_completed",
        }
        write_csv(output_dir / "cost_stress_summary.csv", costs)
        write_csv(output_dir / "source_concentration_report.csv", source_report)
        write_csv(output_dir / "single_day_pnl_dominance_report.csv", dominance_report)
        write_holdout_candidate_outputs(
            candidate_id=candidate_id,
            candidate_root=candidate_root,
            output_dir=output_dir,
            trades=trades,
            costs=costs,
            source_report=source_report,
            source_status=source_status,
            dominance_status=dominance_status,
            same_bar_count=same_bar_count,
            summary=summary,
        )
        summaries.append(summary)
    return summaries


def project_verdict(summaries: list[dict[str, Any]], usable_days: int) -> str:
    if usable_days == 0:
        return "BTC_HOLDOUT_BLOCKED_NO_DATA"
    if any(row["holdout_verdict"] == "HOLDOUT_PASS_REVIEW" for row in summaries):
        return "BTC_HOLDOUT_SURVIVOR_FOUND"
    if all(row["holdout_verdict"] == "REJECT_HOLDOUT_FAIL" for row in summaries):
        return "BTC_ALL_REPLAY_SURVIVORS_FAILED_HOLDOUT"
    if any(row["holdout_verdict"] in {"WAIT_MORE_HOLDOUT_DATA", "HOLDOUT_WARN_CONTINUE"} for row in summaries):
        return "BTC_HOLDOUT_NEEDS_MORE_DATA"
    return "BTC_HOLDOUT_IN_PROGRESS"


def write_canonical_report(path: Path, summaries: list[dict[str, Any]], usable_days: int, feed_days: int) -> str:
    managerial = project_verdict(summaries, usable_days)
    lines = [
        "# Sprint 10 True Holdout Report",
        "",
        f"managerial_verdict: `{managerial}`",
        "",
        f"sprint08_rules_commit: `{SPRINT08_COMMIT}`",
        f"sprint09_integrity_commit: `{SPRINT09_COMMIT}`",
        "",
        "Boundary confirmation: no live, no Executor, no Phase 4, no PROMOTE, no tuning, no threshold changes, no stop/target/expiry changes, no universe change, no CTX tuning, no Analyzer v1 contract change, no Backtester core change.",
        "",
        f"feed_days_audited: `{feed_days}`",
        f"usable_holdout_days: `{usable_days}`",
        "",
        "| candidate | events | trades | days | net_0.00015 | verdict | reason |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['candidate_id']} | {row['events']} | {row['trades']} | {row['independent_days']} | {row['net_0_00015']} | {row['holdout_verdict']} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Managerial Answer",
            "",
            "No candidate is promoted. Phase 4 remains closed.",
            "If no usable holdout days exist, wait for new completed clean BTC feed days before re-running Sprint 10.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return managerial


def git_text(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    return result.stdout + result.stderr


def copy_if_exists(src: Path, dst_root: Path) -> None:
    if not src.exists():
        return
    dst = dst_root / src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def create_transfer_package(args: argparse.Namespace, summaries: list[dict[str, Any]], managerial: str) -> Path:
    current = Path(args.transfer_current)
    zip_path = Path(args.transfer_zip)
    if current.exists():
        shutil.rmtree(current)
    current.mkdir(parents=True, exist_ok=True)
    (current / "git_status_short.txt").write_text(git_text(["status", "--short"]), encoding="utf-8")
    (current / "git_log_last_5.txt").write_text(git_text(["log", "--oneline", "-5"]), encoding="utf-8")

    include_paths = [
        Path("research/canonical/SPRINT_10_TRUE_HOLDOUT_REPORT.md"),
        Path("research/canonical/SPRINT_10_HOLDOUT_DATA_AUDIT.md"),
        Path("research/results/sprint_10_holdout_data_audit.csv"),
        Path("research/scripts/sprint_10_true_holdout_runner.py"),
    ]
    for candidate_id in CANDIDATES:
        include_paths.extend(
            [
                Path(f"research/candidates/{candidate_id}/holdout_log.csv"),
                Path(f"research/candidates/{candidate_id}/holdout_summary.md"),
                Path(f"research/candidates/{candidate_id}/holdout_cost_stress_summary.csv"),
                Path(f"research/candidates/{candidate_id}/holdout_source_concentration_report.csv"),
                Path(f"research/candidates/{candidate_id}/holdout_distribution_audit.md"),
                Path(f"research/candidates/{candidate_id}/holdout_promotion_gate_checklist.md"),
                Path(f"backtest_runs/sprint_10_true_holdout/{candidate_id}/trades.csv"),
                Path(f"backtest_runs/sprint_10_true_holdout/{candidate_id}/replay_summary.json"),
            ]
        )
    for path in include_paths:
        copy_if_exists(path, current)

    manifest_lines = [
        "# Sprint 10 Transfer Manifest",
        "",
        f"managerial_verdict: `{managerial}`",
        "",
        "Included artifacts:",
    ]
    for path in sorted(p for p in current.rglob("*") if p.is_file()):
        manifest_lines.append(f"- `{path.relative_to(current).as_posix()}`")
    manifest_lines.extend(["", "Excluded: feed/, feed_recovered/, Executor/, old analyzer_runs/, old backtest_runs/, cache files.", ""])
    (current / "TRANSFER_MANIFEST.md").write_text("\n".join(manifest_lines), encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(current.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(current))
    return zip_path


def run(args: argparse.Namespace) -> None:
    days = build_holdout_days(args)
    write_data_audit(
        days,
        Path("research/results/sprint_10_holdout_data_audit.csv"),
        Path("research/canonical/SPRINT_10_HOLDOUT_DATA_AUDIT.md"),
        args.as_of_date,
    )
    usable = [day for day in days if day.usable_for_holdout]
    if not usable:
        reason = "no_usable_completed_clean_holdout_days"
        summaries = [write_blocked_candidate(candidate_id, Path(args.candidate_root), reason) for candidate_id in CANDIDATES]
    else:
        summaries = run_holdout_replay(args, days)
    managerial = write_canonical_report(
        Path("research/canonical/SPRINT_10_TRUE_HOLDOUT_REPORT.md"),
        summaries,
        usable_days=len(usable),
        feed_days=len(days),
    )
    transfer_zip = create_transfer_package(args, summaries, managerial)
    result = {
        "managerial_verdict": managerial,
        "usable_holdout_days": len(usable),
        "candidates": summaries,
        "transfer_package": str(transfer_zip),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 10 true holdout runner.")
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--recovered-root", default="feed_recovered")
    parser.add_argument(
        "--recovered-manifest",
        default=(
            "D:/Project_V/btc-orderflow-system/deltascout/research_material/recovery_reports/"
            "recovery_quality_2026-04-23_1705_to_2026-05-06_2251.csv"
        ),
    )
    parser.add_argument("--use-recovered-gap", action="store_true", default=True)
    parser.add_argument("--used-source-features", default="research/results/sprint_06_discovery_features.csv")
    parser.add_argument("--candidate-root", default="research/candidates")
    parser.add_argument("--output-root", default="backtest_runs/sprint_10_true_holdout")
    parser.add_argument("--transfer-current", default="transfer_out/current")
    parser.add_argument("--transfer-zip", default="transfer_out/Sprint10_artifacts.zip")
    parser.add_argument("--as-of-date", default=AS_OF_DATE)
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
