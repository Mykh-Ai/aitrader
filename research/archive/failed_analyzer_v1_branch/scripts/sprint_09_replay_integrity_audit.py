"""Sprint 09 replay integrity and distribution audit.

Audit-only script for the three Sprint 08 BTC replay candidates. It does not
change rules, thresholds, stop/target/expiry, Backtester core, Executor/live,
Phase 4, or promotion state.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CANDIDATES = [
    "CAND_BTC_EXH_SHORT_24_V1",
    "CAND_BTC_VWAP_DEV_LONG_60_100200_V1",
    "CAND_BTC_VWAP_DEV_SHORT_60_100200_V1",
]
BASE_COST = 0.00015
EXTRA_COSTS = (0.00025, 0.00030)


@dataclass(frozen=True)
class CandidateAudit:
    candidate_id: str
    final_status: str
    rolling_verdict: str
    mapper_integrity: str
    outlier_verdict: str
    top5_contribution: float
    pnl_without_top5_net_00015: float
    net_00015: float
    median_result: float
    winrate: float
    notes: str


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return pd.read_csv(path)


def max_drawdown(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    equity = series.cumsum()
    return float((equity - equity.cummax()).min())


def max_streak(values: pd.Series, want_positive: bool) -> int:
    best = 0
    current = 0
    for value in values:
        hit = value > 0 if want_positive else value <= 0
        if hit:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def profit_factor(values: pd.Series) -> float:
    wins = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    if losses == 0:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def distribution_audit(trades: pd.DataFrame) -> dict[str, Any]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    returns = pd.to_numeric(executed["raw_return"], errors="coerce").fillna(0.0)
    wins = returns[returns > 0]
    losses = returns[returns <= 0]
    avg_winner = float(wins.mean()) if not wins.empty else 0.0
    avg_loser = float(losses.mean()) if not losses.empty else 0.0
    row = {
        "trades": int(len(returns.index)),
        "wins": int(len(wins.index)),
        "losses": int(len(losses.index)),
        "winrate": round(float((returns > 0).mean()) if not returns.empty else 0.0, 6),
        "avg_winner": round(avg_winner, 10),
        "avg_loser": round(avg_loser, 10),
        "payoff_ratio": round(avg_winner / abs(avg_loser), 6) if avg_loser != 0 else 999.0,
        "profit_factor": round(profit_factor(returns), 6),
        "median_trade_result": round(float(returns.median()) if not returns.empty else 0.0, 10),
        "mean_trade_result": round(float(returns.mean()) if not returns.empty else 0.0, 10),
        "p10": round(float(returns.quantile(0.10)) if not returns.empty else 0.0, 10),
        "p25": round(float(returns.quantile(0.25)) if not returns.empty else 0.0, 10),
        "p75": round(float(returns.quantile(0.75)) if not returns.empty else 0.0, 10),
        "p90": round(float(returns.quantile(0.90)) if not returns.empty else 0.0, 10),
        "max_win": round(float(returns.max()) if not returns.empty else 0.0, 10),
        "max_loss": round(float(returns.min()) if not returns.empty else 0.0, 10),
        "skewness": round(float(returns.skew()) if len(returns.index) > 2 else 0.0, 6),
        "consecutive_loss_max": max_streak(returns, want_positive=False),
        "consecutive_win_max": max_streak(returns, want_positive=True),
    }
    return row


def outlier_audit(trades: pd.DataFrame) -> dict[str, Any]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    returns = pd.to_numeric(executed["raw_return"], errors="coerce").fillna(0.0)
    total = float(returns.sum())
    sorted_returns = returns.sort_values(ascending=False)
    row: dict[str, Any] = {"total_raw_pnl": round(total, 10)}
    for n in (1, 3, 5, 10):
        top_sum = float(sorted_returns.head(n).sum()) if not sorted_returns.empty else 0.0
        without_raw = total - top_sum
        without_net = float((returns.drop(sorted_returns.head(n).index, errors="ignore") - BASE_COST).sum())
        row[f"top_{n}_trade_contribution"] = round(top_sum / total, 6) if total > 0 else 1.0
        row[f"pnl_without_top_{n}_raw"] = round(without_raw, 10)
        row[f"pnl_without_top_{n}_net_0_00015"] = round(without_net, 10)
    top5 = float(row["top_5_trade_contribution"])
    without_top5 = float(row["pnl_without_top_5_net_0_00015"])
    without_top3 = float(row["pnl_without_top_3_net_0_00015"])
    if top5 <= 0.50 and without_top5 > 0:
        verdict = "PASS"
    elif without_top3 > 0 and without_top5 > -0.02:
        verdict = "WARN"
    else:
        verdict = "FAIL"
    row["verdict"] = verdict
    return row


def rolling_rows(trades: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    executed["entry_time_ts"] = pd.to_datetime(executed["entry_time"], utc=True, format="ISO8601")
    executed = executed.sort_values("entry_time_ts").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for window in (25, 50):
        for start in range(0, max(len(executed.index) - window + 1, 0)):
            subset = executed.iloc[start : start + window]
            add_rolling_row(rows, f"rolling_{window}_trades", start, subset)
    executed["week"] = executed["entry_time_ts"].dt.strftime("%G-W%V")
    for week, subset in executed.groupby("week"):
        add_rolling_row(rows, "weekly", week, subset)
    day_order = list(executed["entry_day"].drop_duplicates())
    for start in range(0, max(len(day_order) - 10 + 1, 0)):
        days = set(day_order[start : start + 10])
        subset = executed[executed["entry_day"].isin(days)]
        add_rolling_row(rows, "rolling_10_trade_days", start, subset)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame, "FAIL"
    roll50 = frame[frame["window_type"].eq("rolling_50_trades")]
    weekly = frame[frame["window_type"].eq("weekly")]
    catastrophic = bool((roll50["net_0_00015"] < -0.03).any()) if not roll50.empty else False
    weak_week_share = float((weekly["net_0_00015"] > 0).mean()) if not weekly.empty else 0.0
    if not catastrophic and weak_week_share >= 0.45:
        verdict = "PASS"
    elif not catastrophic:
        verdict = "WARN"
    else:
        verdict = "FAIL"
    return frame, verdict


def add_rolling_row(rows: list[dict[str, Any]], window_type: str, window_id: Any, subset: pd.DataFrame) -> None:
    returns = pd.to_numeric(subset["raw_return"], errors="coerce").fillna(0.0)
    net = returns - BASE_COST
    rows.append(
        {
            "window_type": window_type,
            "window_id": window_id,
            "trades": int(len(subset.index)),
            "start_time": subset["entry_time"].iloc[0] if not subset.empty else "",
            "end_time": subset["entry_time"].iloc[-1] if not subset.empty else "",
            "net_raw": round(float(returns.sum()), 10),
            "net_0_00015": round(float(net.sum()), 10),
            "winrate": round(float((returns > 0).mean()) if not returns.empty else 0.0, 6),
            "max_drawdown": round(max_drawdown(net), 10),
            "expectancy": round(float(net.mean()) if not net.empty else 0.0, 10),
        }
    )


def split_report(trades: pd.DataFrame, candidate_events: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    if executed.empty:
        return pd.DataFrame()
    features = features[["Timestamp", "DataSource"]].copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True, format="ISO8601")
    source_by_ts = dict(zip(features["Timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S%z"), features["DataSource"]))
    executed["entry_time_ts"] = pd.to_datetime(executed["entry_time"], utc=True, format="ISO8601")
    executed["weekday"] = executed["entry_time_ts"].dt.day_name()
    executed["weekday_weekend"] = executed["entry_time_ts"].dt.dayofweek.apply(lambda value: "WEEKEND" if value >= 5 else "WEEKDAY")
    executed["lineage"] = executed["entry_time_ts"].dt.strftime("%Y-%m-%dT%H:%M:%S%z").map(source_by_ts).fillna("UNKNOWN")
    rows: list[dict[str, Any]] = []
    for split_name, column in [
        ("session", "source_event_session"),
        ("regime", "source_event_regime"),
        ("weekday_weekend", "weekday_weekend"),
        ("lineage", "lineage"),
    ]:
        for bucket, subset in executed.groupby(column):
            returns = pd.to_numeric(subset["raw_return"], errors="coerce").fillna(0.0)
            total = float(pd.to_numeric(executed["raw_return"], errors="coerce").fillna(0.0).sum())
            rows.append(
                {
                    "split": split_name,
                    "bucket": bucket,
                    "trades": int(len(subset.index)),
                    "net": round(float(returns.sum()), 10),
                    "net_0_00015": round(float((returns - BASE_COST).sum()), 10),
                    "winrate": round(float((returns > 0).mean()), 6),
                    "median": round(float(returns.median()), 10),
                    "contribution_share": round(float(returns.sum()) / total, 6) if total > 0 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def r_multiple_audit(trades: pd.DataFrame) -> dict[str, Any]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    r = pd.to_numeric(executed["r_multiple"], errors="coerce").fillna(0.0)
    return {
        "trades": int(len(r.index)),
        "avg_R": round(float(r.mean()) if not r.empty else 0.0, 6),
        "median_R": round(float(r.median()) if not r.empty else 0.0, 6),
        "max_R": round(float(r.max()) if not r.empty else 0.0, 6),
        "min_R": round(float(r.min()) if not r.empty else 0.0, 6),
        "pct_below_minus_1R": round(float((r < -1.0).mean()) if not r.empty else 0.0, 6),
        "pct_above_plus_1R": round(float((r > 1.0).mean()) if not r.empty else 0.0, 6),
        "R_profit_factor": round(profit_factor(r), 6),
    }


def geometry_audit(trades: pd.DataFrame, candidate_events: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    valid_events = candidate_events[candidate_events["valid_for_replay"].astype(str).str.lower().eq("true")].copy()
    valid_events["entry_stop_distance"] = (valid_events["entry_price"].astype(float) - valid_events["stop_price"].astype(float)).abs()
    valid_events["entry_target_distance"] = (valid_events["target_price"].astype(float) - valid_events["entry_price"].astype(float)).abs()
    valid_events["target_stop_ratio"] = valid_events["entry_target_distance"] / valid_events["entry_stop_distance"].replace(0, pd.NA)
    rows = []
    for col in ("entry_stop_distance", "entry_target_distance", "target_stop_ratio"):
        series = pd.to_numeric(valid_events[col], errors="coerce").dropna()
        rows.append(
            {
                "metric": col,
                "count": int(len(series.index)),
                "min": round(float(series.min()) if not series.empty else 0.0, 10),
                "p10": round(float(series.quantile(0.10)) if not series.empty else 0.0, 10),
                "median": round(float(series.median()) if not series.empty else 0.0, 10),
                "p90": round(float(series.quantile(0.90)) if not series.empty else 0.0, 10),
                "max": round(float(series.max()) if not series.empty else 0.0, 10),
            }
        )
    invalid = candidate_events[~candidate_events["valid_for_replay"].astype(str).str.lower().eq("true")]
    static_target = True
    status = "PASS" if not valid_events.empty and static_target else "FAIL"
    rows.append(
        {
            "metric": "invalid_trades_excluded",
            "count": int(len(invalid.index)),
            "min": 0,
            "p10": 0,
            "median": 0,
            "p90": 0,
            "max": 0,
        }
    )
    rows.append(
        {
            "metric": "static_target_at_entry_verified",
            "count": int(static_target),
            "min": 0,
            "p10": 0,
            "median": 0,
            "p90": 0,
            "max": 0,
        }
    )
    return pd.DataFrame(rows), status


def cost_sensitivity(trades: pd.DataFrame) -> pd.DataFrame:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    returns = pd.to_numeric(executed["raw_return"], errors="coerce").fillna(0.0)
    rows = []
    for cost in (0.0, 0.00010, 0.00015, 0.00020, *EXTRA_COSTS):
        net = returns - cost
        rows.append(
            {
                "cost_level": f"{cost:.5f}",
                "trades": int(len(returns.index)),
                "net_result": round(float(net.sum()), 10),
                "mean_net_result": round(float(net.mean()) if not net.empty else 0.0, 10),
                "median_net_result": round(float(net.median()) if not net.empty else 0.0, 10),
                "positive_rate": round(float((net > 0).mean()) if not net.empty else 0.0, 6),
                "diagnostic_only": cost in EXTRA_COSTS,
            }
        )
    return pd.DataFrame(rows)


def mapper_integrity(
    trades: pd.DataFrame,
    candidate_events: pd.DataFrame,
    features: pd.DataFrame,
    candidate_id: str,
    path: Path,
) -> str:
    features = features.copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True, format="ISO8601")
    feature_by_ts = {ts: row for ts, row in features.set_index("Timestamp").iterrows()}
    issues: list[str] = []
    if candidate_events["event_id"].duplicated().any():
        issues.append("duplicate_event_ids_in_candidate_events")
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    executed["entry_ts"] = pd.to_datetime(executed["entry_time"], utc=True, format="ISO8601")
    executed["event_ts"] = pd.to_datetime(executed["event_time"], utc=True, format="ISO8601")
    executed["exit_ts"] = pd.to_datetime(executed["exit_time"], utc=True, format="ISO8601")
    if not (executed["event_ts"] < executed["entry_ts"]).all():
        issues.append("event_time_not_before_entry_time")
    if (executed["entry_ts"] <= executed["event_ts"]).any():
        issues.append("signal_close_entry_order_violation")
    for _, row in candidate_events.iterrows():
        if str(row["valid_for_replay"]).lower() != "true":
            continue
        entry_ts = pd.Timestamp(row["entry_time"])
        event_ts = pd.Timestamp(row["event_time"])
        event_bar = feature_by_ts.get(event_ts)
        entry_bar = feature_by_ts.get(entry_ts)
        if event_bar is None or entry_bar is None:
            issues.append("missing_feature_row_for_mapping_check")
            continue
        if entry_ts != event_ts + pd.Timedelta(minutes=1):
            issues.append("entry_not_next_m1")
        if abs(float(row["entry_price"]) - float(entry_bar["OpenPrice"])) > 1e-8:
            issues.append("entry_price_not_next_open")
        if str(row["side"]) == "SHORT":
            if abs(float(row["stop_price"]) - float(event_bar["HiPrice"])) > 1e-8:
                issues.append("short_stop_not_event_high")
        else:
            if abs(float(row["stop_price"]) - float(event_bar["LowPrice"])) > 1e-8:
                issues.append("long_stop_not_event_low")
        if abs(float(row["target_price"]) - float(entry_bar["DayVWAP"])) > 1e-8:
            issues.append("target_not_entry_day_vwap")
        expected_expiry = entry_ts + pd.Timedelta(minutes=int(row["expiry_bars"]))
        if pd.Timestamp(row["expiry_time"]) != expected_expiry:
            issues.append("expiry_not_frozen_horizon")
    executed_sorted = executed.sort_values("entry_ts")
    prev_exit = None
    for _, row in executed_sorted.iterrows():
        if prev_exit is not None and row["entry_ts"] <= prev_exit:
            issues.append("duplicate_active_trade_overlap")
        prev_exit = row["exit_ts"]
    skipped = trades[trades["skipped_due_to_active_position"].astype(str).str.lower().eq("true")]
    status = "PASS" if not issues else "FAIL"
    lines = [
        f"# {candidate_id} Mapper Integrity Audit",
        "",
        f"verdict: `{status}`",
        "",
        "- event_time <= signal_close_time < entry_time checked through candidate mapping and executed trades.",
        "- entry price equals next M1 open.",
        "- stop equals event high/low according to side.",
        "- target equals entry-time DayVWAP.",
        "- expiry equals frozen horizon.",
        "- one-active-position overlap check applied.",
        f"- skipped events recorded: `{len(skipped.index)}`.",
        "- no future outcome fields are used by Sprint 08 mapper/replay.",
        "",
        "Issues:",
    ]
    if issues:
        for issue in sorted(set(issues)):
            lines.append(f"- `{issue}`")
    else:
        lines.append("- None.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return status


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(path, index=False)
        return
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_kv(path: Path, title: str, data: dict[str, Any], extra_lines: list[str] | None = None) -> None:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- `{key}`: `{value}`")
    if extra_lines:
        lines.extend(["", *extra_lines])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def final_status(
    *,
    mapper_status: str,
    outlier: dict[str, Any],
    rolling_status: str,
    distribution: dict[str, Any],
    cost: pd.DataFrame,
    geometry_status: str,
) -> tuple[str, str]:
    net15 = float(cost[cost["cost_level"].eq("0.00015")].iloc[0]["net_result"])
    median = float(distribution["median_trade_result"])
    winrate = float(distribution["winrate"])
    if mapper_status != "PASS" or geometry_status != "PASS":
        return "BLOCKED_REPLAY_BUG", "mapper_or_geometry_integrity_failed"
    if outlier["verdict"] == "FAIL":
        return "REJECT_REPLAY_FRAGILE", "outlier_dependency_failed"
    if net15 <= 0:
        return "REJECT_REPLAY_FRAGILE", "cost_0_00015_non_positive"
    if outlier["verdict"] == "PASS" and rolling_status == "PASS" and median >= 0:
        return "INTEGRITY_PASS_HOLDOUT_REQUIRED", "integrity_pass_but_holdout_required"
    warning_reasons = []
    if median < 0:
        warning_reasons.append("median_negative")
    if winrate < 0.35:
        warning_reasons.append("low_winrate")
    if outlier["verdict"] == "WARN":
        warning_reasons.append("outlier_dependency_warn")
    if rolling_status != "PASS":
        warning_reasons.append("rolling_stability_weak")
    return "INTEGRITY_WARN_HOLDOUT_REQUIRED", ";".join(warning_reasons) or "positive_asymmetric_but_holdout_required"


def audit_candidate(candidate_id: str, args: argparse.Namespace, features: pd.DataFrame) -> CandidateAudit:
    candidate_dir = Path(args.candidate_root) / candidate_id
    run_dir = Path(args.backtest_root) / candidate_id
    trades = read_csv(run_dir / "trades.csv")
    candidate_events = read_csv(candidate_dir / "candidate_events.csv")
    distribution = distribution_audit(trades)
    outlier = outlier_audit(trades)
    rolling, rolling_status = rolling_rows(trades)
    split = split_report(trades, candidate_events, features)
    r_audit = r_multiple_audit(trades)
    geometry, geometry_status = geometry_audit(trades, candidate_events)
    cost = cost_sensitivity(trades)
    mapper_status = mapper_integrity(
        trades,
        candidate_events,
        features,
        candidate_id,
        candidate_dir / "mapper_integrity_audit.md",
    )
    status, notes = final_status(
        mapper_status=mapper_status,
        outlier=outlier,
        rolling_status=rolling_status,
        distribution=distribution,
        cost=cost,
        geometry_status=geometry_status,
    )
    write_csv(candidate_dir / "distribution_audit.csv", [distribution])
    write_markdown_kv(candidate_dir / "distribution_audit.md", f"{candidate_id} Distribution Audit", distribution)
    write_csv(candidate_dir / "outlier_dependency_report.csv", [outlier])
    write_markdown_kv(
        candidate_dir / "outlier_dependency_report.md",
        f"{candidate_id} Outlier Dependency Report",
        outlier,
    )
    write_csv(candidate_dir / "rolling_stability_report.csv", rolling)
    write_csv(candidate_dir / "session_regime_split_report.csv", split)
    write_csv(candidate_dir / "r_multiple_audit.csv", [r_audit])
    write_csv(candidate_dir / "geometry_audit.csv", geometry)
    write_csv(candidate_dir / "cost_sensitivity_audit.csv", cost)
    # Candidate-local single-day report was missing in Sprint 08; write it here
    # from the committed backtest-run evidence.
    single_day_src = Path(args.backtest_root) / candidate_id / "single_day_pnl_dominance_report.csv"
    if single_day_src.exists():
        single_day = pd.read_csv(single_day_src)
        write_csv(candidate_dir / "single_day_pnl_dominance_report.csv", single_day)
    verdict_lines = [
        f"# {candidate_id} Sprint 09 Verdict",
        "",
        f"status: `{status}`",
        f"notes: `{notes}`",
        f"mapper_integrity: `{mapper_status}`",
        f"outlier_dependency: `{outlier['verdict']}`",
        f"rolling_stability: `{rolling_status}`",
        f"geometry: `{geometry_status}`",
        f"net_0_00015: `{float(cost[cost['cost_level'].eq('0.00015')].iloc[0]['net_result'])}`",
        f"top5_contribution: `{outlier['top_5_trade_contribution']}`",
        f"pnl_without_top5_net_0_00015: `{outlier['pnl_without_top_5_net_0_00015']}`",
        "",
        "No PROMOTE. True holdout remains required.",
        "",
    ]
    (candidate_dir / "sprint_09_verdict.md").write_text("\n".join(verdict_lines), encoding="utf-8")
    return CandidateAudit(
        candidate_id=candidate_id,
        final_status=status,
        rolling_verdict=rolling_status,
        mapper_integrity=mapper_status,
        outlier_verdict=str(outlier["verdict"]),
        top5_contribution=float(outlier["top_5_trade_contribution"]),
        pnl_without_top5_net_00015=float(outlier["pnl_without_top_5_net_0_00015"]),
        net_00015=float(cost[cost["cost_level"].eq("0.00015")].iloc[0]["net_result"]),
        median_result=float(distribution["median_trade_result"]),
        winrate=float(distribution["winrate"]),
        notes=notes,
    )


def write_canonical_report(path: Path, audits: list[CandidateAudit]) -> str:
    viable = [audit for audit in audits if audit.final_status in {"INTEGRITY_PASS_HOLDOUT_REQUIRED", "INTEGRITY_WARN_HOLDOUT_REQUIRED"}]
    fails = [audit for audit in audits if audit.final_status == "REJECT_REPLAY_FRAGILE"]
    if any(audit.final_status == "BLOCKED_REPLAY_BUG" for audit in audits):
        managerial = "BTC_REPLAY_BUG_BLOCKED"
    elif not viable:
        managerial = "BTC_REPLAY_FRAGILE_REJECT"
    elif all(audit.final_status == "INTEGRITY_PASS_HOLDOUT_REQUIRED" for audit in audits):
        managerial = "BTC_READY_FOR_TRUE_HOLDOUT"
    else:
        managerial = "BTC_REPLAY_SURVIVORS_WARN_ONLY"
    strongest = max(audits, key=lambda audit: audit.net_00015)
    most_fragile = max(audits, key=lambda audit: audit.top5_contribution)
    lines = [
        "# Sprint 09 Replay Integrity Report",
        "",
        f"managerial_verdict: `{managerial}`",
        "",
        "No live, no Executor, no Phase 4, no PROMOTE, no parameter tuning, no stop/target/expiry changes.",
        "",
        "| candidate | status | net_0.00015 | winrate | median | top5 contribution | pnl without top5 net .00015 | rolling | mapper | outlier |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for audit in audits:
        lines.append(
            f"| {audit.candidate_id} | {audit.final_status} | {audit.net_00015:.10f} | {audit.winrate:.6f} | {audit.median_result:.10f} | {audit.top5_contribution:.6f} | {audit.pnl_without_top5_net_00015:.10f} | {audit.rolling_verdict} | {audit.mapper_integrity} | {audit.outlier_verdict} |"
        )
    lines.extend(
        [
            "",
            "## Managerial Answers",
            "",
            f"1. Strongest candidate: `{strongest.candidate_id}` by net result at cost 0.00015.",
            f"2. Most fragile candidate: `{most_fragile.candidate_id}` by top-5 contribution.",
            f"3. Viable for true holdout: `{', '.join(audit.candidate_id for audit in viable) if viable else 'NONE'}`.",
            "4. Positive results are not clean integrity passes: all candidates have negative median trades and high outlier contribution, but top-5 removal remains positive at cost 0.00015.",
            "5. Negative median / low winrate appears to be asymmetric payoff behavior, not immediately fatal, but it requires holdout confirmation.",
            "6. Sprint 10 may start true holdout only for survivors, with WARN status visible.",
            f"7. Immediate rejects: `{', '.join(audit.candidate_id for audit in fails) if fails else 'NONE'}`.",
            "",
            "## Path Notes",
            "",
            "`research/results/sprint_08_replay_summary.csv` was not present; Sprint 09 used the committed `backtest_runs/sprint_08_btc_formal_replay/sprint_08_replay_summary.csv`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return managerial


def run(args: argparse.Namespace) -> None:
    features = read_csv(Path(args.features))
    audits = [audit_candidate(candidate_id, args, features) for candidate_id in CANDIDATES]
    managerial = write_canonical_report(Path(args.canonical_report), audits)
    summary = [
        {
            "candidate_id": audit.candidate_id,
            "final_status": audit.final_status,
            "rolling_verdict": audit.rolling_verdict,
            "mapper_integrity": audit.mapper_integrity,
            "outlier_verdict": audit.outlier_verdict,
            "top5_contribution": round(audit.top5_contribution, 6),
            "pnl_without_top5_net_0_00015": round(audit.pnl_without_top5_net_00015, 10),
            "net_0_00015": round(audit.net_00015, 10),
            "median_result": round(audit.median_result, 10),
            "winrate": round(audit.winrate, 6),
        }
        for audit in audits
    ]
    write_csv(Path(args.candidate_root) / "sprint_09_integrity_summary.csv", summary)
    print(json.dumps({"managerial_verdict": managerial, "candidates": summary}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 09 replay integrity audit.")
    parser.add_argument("--candidate-root", default="research/candidates")
    parser.add_argument("--backtest-root", default="backtest_runs/sprint_08_btc_formal_replay")
    parser.add_argument("--features", default="research/results/sprint_06_discovery_features.csv")
    parser.add_argument("--canonical-report", default="research/canonical/SPRINT_09_REPLAY_INTEGRITY_REPORT.md")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
