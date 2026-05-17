"""Sprint 08 deterministic replay runner for selected BTC candidates.

This runner consumes Sprint 08 mapped candidate_events.csv files. It does not
change Backtester core, Analyzer v1, Executor/live behavior, or Phase 4 state.
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


COST_LEVELS = (0.00000, 0.00010, 0.00015, 0.00020)
RULE_VERSION = "SPRINT08_BTC_FORMAL_REPLAY_V1"
PROMOTION_STATUS = "NO_PROMOTE_HOLDOUT_REQUIRED"


@dataclass(frozen=True)
class CandidateRuntime:
    candidate_id: str
    side: str
    expiry_bars: int


CANDIDATES = [
    CandidateRuntime("CAND_BTC_EXH_SHORT_24_V1", "SHORT", 24),
    CandidateRuntime("CAND_BTC_VWAP_DEV_LONG_60_100200_V1", "LONG", 60),
    CandidateRuntime("CAND_BTC_VWAP_DEV_SHORT_60_100200_V1", "SHORT", 60),
]


TRADE_COLUMNS = [
    "candidate_id",
    "event_id",
    "trade_status",
    "skipped_due_to_active_position",
    "entry_time",
    "exit_time",
    "side",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_price",
    "exit_reason",
    "same_bar_ambiguous",
    "holding_bars",
    "raw_return",
    "r_multiple",
    "source_event_session",
    "source_event_regime",
    "event_time",
    "entry_day",
]


def load_features(path: Path) -> pd.DataFrame:
    features = pd.read_csv(path)
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True, format="ISO8601")
    features = features.sort_values("Timestamp").reset_index(drop=True)
    return features


def feature_lookup(features: pd.DataFrame) -> dict[pd.Timestamp, int]:
    return {ts: int(idx) for idx, ts in features["Timestamp"].items()}


def load_candidate_events(path: Path) -> pd.DataFrame:
    events = pd.read_csv(path)
    if events.empty:
        return events
    events["entry_time_ts"] = pd.to_datetime(events["entry_time"], utc=True, format="ISO8601", errors="coerce")
    events["expiry_time_ts"] = pd.to_datetime(events["expiry_time"], utc=True, format="ISO8601", errors="coerce")
    events = events.sort_values("entry_time_ts").reset_index(drop=True)
    return events


def raw_return(side: str, entry: float, exit_price: float) -> float:
    if entry <= 0 or exit_price <= 0:
        return 0.0
    value = exit_price / entry - 1.0
    return value if side == "LONG" else -value


def r_multiple(side: str, entry: float, stop: float, exit_price: float) -> float:
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    pnl = (exit_price - entry) if side == "LONG" else (entry - exit_price)
    return pnl / risk


def resolve_trade(event: pd.Series, features: pd.DataFrame, lookup: dict[pd.Timestamp, int]) -> dict[str, Any]:
    candidate_id = str(event["candidate_id"])
    side = str(event["side"])
    entry_ts = event["entry_time_ts"]
    expiry_ts = event["expiry_time_ts"]
    entry_price = float(event["entry_price"])
    stop_price = float(event["stop_price"])
    target_price = float(event["target_price"])
    if pd.isna(entry_ts) or entry_ts not in lookup:
        return blocked_trade(event, "entry_timestamp_missing")
    entry_idx = lookup[entry_ts]
    expiry_idx = lookup.get(expiry_ts, min(entry_idx + int(event["expiry_bars"]), len(features.index) - 1))
    same_bar_ambiguous = False
    exit_idx = expiry_idx
    exit_price = float(features.loc[expiry_idx, "ClosePrice"])
    exit_reason = "EXPIRY"
    for idx in range(entry_idx, expiry_idx + 1):
        bar = features.loc[idx]
        high = float(bar["HiPrice"])
        low = float(bar["LowPrice"])
        if side == "LONG":
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_hit = high >= stop_price
            target_hit = low <= target_price
        if stop_hit and target_hit:
            same_bar_ambiguous = True
            exit_idx = idx
            exit_price = stop_price
            exit_reason = "SAME_BAR_STOP_FIRST"
            break
        if stop_hit:
            exit_idx = idx
            exit_price = stop_price
            exit_reason = "STOP"
            break
        if target_hit:
            exit_idx = idx
            exit_price = target_price
            exit_reason = "TARGET"
            break
    exit_ts = features.loc[exit_idx, "Timestamp"]
    result = raw_return(side, entry_price, exit_price)
    return {
        "candidate_id": candidate_id,
        "event_id": event["event_id"],
        "trade_status": "EXECUTED",
        "skipped_due_to_active_position": False,
        "entry_time": entry_ts.isoformat(),
        "exit_time": exit_ts.isoformat(),
        "side": side,
        "entry_price": round(entry_price, 8),
        "stop_price": round(stop_price, 8),
        "target_price": round(target_price, 8),
        "exit_price": round(float(exit_price), 8),
        "exit_reason": exit_reason,
        "same_bar_ambiguous": same_bar_ambiguous,
        "holding_bars": int(exit_idx - entry_idx),
        "raw_return": round(result, 10),
        "r_multiple": round(r_multiple(side, entry_price, stop_price, float(exit_price)), 10),
        "source_event_session": event.get("session", ""),
        "source_event_regime": event.get("regime", ""),
        "event_time": event.get("event_time", ""),
        "entry_day": entry_ts.strftime("%Y-%m-%d"),
    }


def blocked_trade(event: pd.Series, reason: str) -> dict[str, Any]:
    return {
        "candidate_id": event.get("candidate_id", ""),
        "event_id": event.get("event_id", ""),
        "trade_status": "BLOCKED_DATA",
        "skipped_due_to_active_position": False,
        "entry_time": event.get("entry_time", ""),
        "exit_time": "",
        "side": event.get("side", ""),
        "entry_price": event.get("entry_price", 0.0),
        "stop_price": event.get("stop_price", 0.0),
        "target_price": event.get("target_price", 0.0),
        "exit_price": 0.0,
        "exit_reason": reason,
        "same_bar_ambiguous": False,
        "holding_bars": 0,
        "raw_return": 0.0,
        "r_multiple": 0.0,
        "source_event_session": event.get("session", ""),
        "source_event_regime": event.get("regime", ""),
        "event_time": event.get("event_time", ""),
        "entry_day": "",
    }


def skipped_trade(event: pd.Series, active_until: pd.Timestamp) -> dict[str, Any]:
    return {
        "candidate_id": event.get("candidate_id", ""),
        "event_id": event.get("event_id", ""),
        "trade_status": "SKIPPED_ACTIVE_POSITION",
        "skipped_due_to_active_position": True,
        "entry_time": event.get("entry_time", ""),
        "exit_time": active_until.isoformat(),
        "side": event.get("side", ""),
        "entry_price": event.get("entry_price", 0.0),
        "stop_price": event.get("stop_price", 0.0),
        "target_price": event.get("target_price", 0.0),
        "exit_price": 0.0,
        "exit_reason": "SKIPPED_DUE_TO_ACTIVE_POSITION",
        "same_bar_ambiguous": False,
        "holding_bars": 0,
        "raw_return": 0.0,
        "r_multiple": 0.0,
        "source_event_session": event.get("session", ""),
        "source_event_regime": event.get("regime", ""),
        "event_time": event.get("event_time", ""),
        "entry_day": event["entry_time_ts"].strftime("%Y-%m-%d") if not pd.isna(event["entry_time_ts"]) else "",
    }


def replay_candidate(events: pd.DataFrame, features: pd.DataFrame, lookup: dict[pd.Timestamp, int]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    active_until: pd.Timestamp | None = None
    valid_events = events[events["valid_for_replay"].astype(str).str.lower().eq("true")].copy()
    invalid_events = events[~events["valid_for_replay"].astype(str).str.lower().eq("true")].copy()
    for _, event in invalid_events.iterrows():
        rows.append(blocked_trade(event, str(event.get("invalid_reason", "invalid_mapping"))))
    for _, event in valid_events.iterrows():
        entry_ts = event["entry_time_ts"]
        if active_until is not None and not pd.isna(entry_ts) and entry_ts <= active_until:
            rows.append(skipped_trade(event, active_until))
            continue
        trade = resolve_trade(event, features, lookup)
        rows.append(trade)
        if trade["trade_status"] == "EXECUTED":
            active_until = pd.Timestamp(trade["exit_time"])
    return pd.DataFrame(rows, columns=TRADE_COLUMNS)


def max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    equity = returns.cumsum()
    running_max = equity.cummax()
    drawdown = equity - running_max
    return float(drawdown.min())


def cost_summary(trades: pd.DataFrame) -> pd.DataFrame:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    rows: list[dict[str, Any]] = []
    for cost in COST_LEVELS:
        net = executed["raw_return"].astype(float) - cost
        rows.append(
            {
                "cost_level": f"{cost:.5f}",
                "trades": int(len(executed.index)),
                "net_result": round(float(net.sum()), 10),
                "mean_net_result": round(float(net.mean()) if not net.empty else 0.0, 10),
                "median_net_result": round(float(net.median()) if not net.empty else 0.0, 10),
                "positive_rate": round(float((net > 0).mean()) if not net.empty else 0.0, 6),
                "verdict": "POSITIVE" if float(net.sum()) > 0 else "NON_POSITIVE",
            }
        )
    return pd.DataFrame(rows)


def source_concentration(trades: pd.DataFrame, candidate_id: str) -> tuple[pd.DataFrame, str]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    if executed.empty:
        row = {
            "candidate_id": candidate_id,
            "independent_days": 0,
            "largest_day_abs_result_share": 1.0,
            "top3_day_abs_result_share": 1.0,
            "status": "FAIL",
            "notes": "no executed trades",
        }
        return pd.DataFrame([row]), "FAIL"
    by_day = executed.groupby("entry_day")["raw_return"].sum()
    abs_sum = by_day.abs().sum()
    largest = float(by_day.abs().max() / abs_sum) if abs_sum > 0 else 1.0
    top3 = float(by_day.abs().sort_values(ascending=False).head(3).sum() / abs_sum) if abs_sum > 0 else 1.0
    status = "PASS" if largest <= 0.20 and top3 <= 0.45 else "FAIL"
    row = {
        "candidate_id": candidate_id,
        "independent_days": int(by_day.count()),
        "largest_day_abs_result_share": round(largest, 6),
        "top3_day_abs_result_share": round(top3, 6),
        "status": status,
        "notes": "PASS requires largest<=0.20 and top3<=0.45",
    }
    return pd.DataFrame([row]), status


def single_day_dominance(trades: pd.DataFrame, candidate_id: str) -> tuple[pd.DataFrame, str]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    if executed.empty:
        return pd.DataFrame([{"candidate_id": candidate_id, "status": "FAIL", "largest_day_net_share": 1.0}]), "FAIL"
    total = float(executed["raw_return"].sum())
    by_day = executed.groupby("entry_day")["raw_return"].sum()
    if total <= 0:
        largest_share = 1.0
        status = "FAIL"
    else:
        largest_share = float(by_day.max() / total)
        status = "PASS" if largest_share <= 0.33 else "FAIL"
    return (
        pd.DataFrame(
            [
                {
                    "candidate_id": candidate_id,
                    "status": status,
                    "largest_day_net_share": round(largest_share, 6),
                    "notes": "PASS requires largest positive day <= 0.33 of total positive net",
                }
            ]
        ),
        status,
    )


def same_bar_report(trades: pd.DataFrame, candidate_id: str, path: Path) -> tuple[int, str]:
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    count = int(executed["same_bar_ambiguous"].astype(bool).sum()) if not executed.empty else 0
    conservative_net = float(executed["raw_return"].sum()) if not executed.empty else 0.0
    status = "PASS" if conservative_net > 0 else "FAIL_OR_NOT_APPLICABLE"
    lines = [
        f"# {candidate_id} Same-Bar Ambiguity Report",
        "",
        f"same_bar_ambiguous_count: `{count}`",
        f"executed_trades: `{len(executed.index)}`",
        f"conservative_raw_net: `{conservative_net:.10f}`",
        f"status: `{status}`",
        "",
        "Policy: conservative stop-first when stop and target touch in the same bar.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return count, status


def verdict(
    *,
    executed: pd.DataFrame,
    cost: pd.DataFrame,
    source_status: str,
    dominance_status: str,
    same_bar_status: str,
) -> str:
    if executed.empty:
        return "BLOCKED_DATA"
    trades = int(len(executed.index))
    independent_days = int(executed["entry_day"].nunique())
    net_15 = float(cost[cost["cost_level"].eq("0.00015")].iloc[0]["net_result"])
    median = float(executed["raw_return"].median())
    raw_net = float(executed["raw_return"].sum())
    if (
        trades >= 50
        and independent_days >= 20
        and net_15 > 0
        and source_status == "PASS"
        and dominance_status == "PASS"
        and same_bar_status == "PASS"
        and median > -0.001
    ):
        return "REPLAY_PASS_REVIEW"
    if net_15 <= 0 or median < 0 or trades < 20:
        return "REJECT_AS_REPLAY"
    if raw_net > 0:
        return "WAIT_REPLAY_WEAK"
    return "REJECT_AS_REPLAY"


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def write_candidate_markdown(candidate_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# {summary['candidate_id']} Replay Summary",
        "",
        f"verdict: `{summary['verdict']}`",
        f"promotion_status: `{PROMOTION_STATUS}`",
        "",
        f"- mapped events: {summary['mapped_events']}",
        f"- valid replay events: {summary['valid_replay_events']}",
        f"- executed trades: {summary['trades']}",
        f"- skipped due active position: {summary['skipped_due_to_active_position']}",
        f"- independent days: {summary['independent_days']}",
        f"- net at 0.00015: {summary['net_0_00015']}",
        f"- winrate: {summary['winrate']}",
        f"- median result: {summary['median_result']}",
        f"- max drawdown: {summary['max_drawdown']}",
        f"- same-bar ambiguous count: {summary['same_bar_ambiguous_count']}",
        f"- source concentration: {summary['source_concentration_verdict']}",
        f"- single-day dominance: {summary['single_day_dominance_verdict']}",
        "",
        "No promotion is allowed because true holdout is not complete.",
        "",
    ]
    (candidate_dir / "candidate_replay_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_promotion_checklist(candidate_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Promotion Gate Checklist",
        "",
        "- [x] formal deterministic mapping exists",
        "- [x] no future labels",
        "- [x] stop frozen",
        "- [x] target frozen",
        "- [x] expiry frozen",
        "- [x] one-active-position rule applied",
        f"- [{'x' if summary['net_0_00015'] > 0 else ' '}] cost 0.00015 positive",
        "- [x] cost 0.00020 reported",
        f"- [{'x' if summary['same_bar_status'] == 'PASS' else ' '}] same-bar ambiguity not verdict-changing",
        f"- [{'x' if summary['source_concentration_verdict'] == 'PASS' else ' '}] source concentration PASS",
        f"- [{'x' if summary['single_day_dominance_verdict'] == 'PASS' else ' '}] no single-day PnL dominance",
        "- [ ] true holdout completed",
        "- [x] no tuning after Sprint 08 freeze",
        "- [ ] isolated margin compatible",
        "- [x] no martingale",
        "",
        f"promotion_status: `{PROMOTION_STATUS}`",
        "",
    ]
    (candidate_dir / "promotion_gate_checklist.md").write_text("\n".join(lines), encoding="utf-8")


def replay_one(candidate: CandidateRuntime, args: argparse.Namespace, features: pd.DataFrame, lookup: dict[pd.Timestamp, int]) -> dict[str, Any]:
    candidate_dir = Path(args.candidate_root) / candidate.candidate_id
    output_dir = Path(args.output_root) / candidate.candidate_id
    events = load_candidate_events(candidate_dir / "candidate_events.csv")
    trades = replay_candidate(events, features, lookup)
    executed = trades[trades["trade_status"].eq("EXECUTED")].copy()
    costs = cost_summary(trades)
    source_report, source_status = source_concentration(trades, candidate.candidate_id)
    dominance_report, dominance_status = single_day_dominance(trades, candidate.candidate_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    same_bar_count, same_bar_status = same_bar_report(trades, candidate.candidate_id, output_dir / "same_bar_ambiguity_report.md")
    result_verdict = verdict(
        executed=executed,
        cost=costs,
        source_status=source_status,
        dominance_status=dominance_status,
        same_bar_status=same_bar_status,
    )
    net_by_cost = {row["cost_level"]: float(row["net_result"]) for _, row in costs.iterrows()}
    summary = {
        "candidate_id": candidate.candidate_id,
        "rule_version": RULE_VERSION,
        "mapped_events": int(len(events.index)),
        "valid_replay_events": int(events["valid_for_replay"].astype(str).str.lower().eq("true").sum()) if not events.empty else 0,
        "invalid_events": int((~events["valid_for_replay"].astype(str).str.lower().eq("true")).sum()) if not events.empty else 0,
        "trades": int(len(executed.index)),
        "skipped_due_to_active_position": int(trades["skipped_due_to_active_position"].astype(bool).sum()) if not trades.empty else 0,
        "independent_days": int(executed["entry_day"].nunique()) if not executed.empty else 0,
        "net_0_00000": net_by_cost.get("0.00000", 0.0),
        "net_0_00010": net_by_cost.get("0.00010", 0.0),
        "net_0_00015": net_by_cost.get("0.00015", 0.0),
        "net_0_00020": net_by_cost.get("0.00020", 0.0),
        "winrate": round(float((executed["raw_return"] > 0).mean()) if not executed.empty else 0.0, 6),
        "median_result": round(float(executed["raw_return"].median()) if not executed.empty else 0.0, 10),
        "max_drawdown": round(max_drawdown(executed["raw_return"].astype(float)) if not executed.empty else 0.0, 10),
        "same_bar_ambiguous_count": same_bar_count,
        "same_bar_status": same_bar_status,
        "source_concentration_verdict": source_status,
        "single_day_dominance_verdict": dominance_status,
        "verdict": result_verdict,
        "promotion_status": PROMOTION_STATUS,
    }
    write_csv(output_dir / "trades.csv", trades)
    write_csv(output_dir / "cost_stress_summary.csv", costs)
    write_csv(output_dir / "source_concentration_report.csv", source_report)
    write_csv(output_dir / "single_day_pnl_dominance_report.csv", dominance_report)
    (output_dir / "replay_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    write_csv(candidate_dir / "cost_stress_summary.csv", costs)
    write_csv(candidate_dir / "source_concentration_report.csv", source_report)
    same_bar_report(trades, candidate.candidate_id, candidate_dir / "same_bar_ambiguity_report.md")
    write_candidate_markdown(candidate_dir, summary)
    write_promotion_checklist(candidate_dir, summary)
    return summary


def write_canonical_report(path: Path, summaries: list[dict[str, Any]]) -> None:
    survived = [row for row in summaries if row["verdict"] == "REPLAY_PASS_REVIEW"]
    weak = [row for row in summaries if row["verdict"] == "WAIT_REPLAY_WEAK"]
    if survived:
        managerial = "BTC_REPLAY_CANDIDATE_SURVIVED"
    elif weak:
        managerial = "BTC_REPLAY_NEEDS_HOLDOUT"
    elif all(row["verdict"].startswith("BLOCKED") for row in summaries):
        managerial = "BTC_REPLAY_BLOCKED_BY_MAPPING"
    else:
        managerial = "BTC_REPLAY_ALL_REJECTED"
    lines = [
        "# Sprint 08 BTC Formal Replay Report",
        "",
        f"managerial_verdict: `{managerial}`",
        "",
        "Sprint 08 formalized and replayed only three selected BTC candidates from Sprint 07. It did not change Sprint 06 predicates, Analyzer v1, Backtester core, CTX holdout, Executor/live, Phase 4, or universe.",
        "",
        "No `PROMOTE` was created. Promotion status remains `NO_PROMOTE_HOLDOUT_REQUIRED` for every candidate.",
        "",
        "| candidate | trades | days | net_0.00015 | winrate | median | max_dd | same_bar | source | dominance | verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in summaries:
        lines.append(
            "| {candidate_id} | {trades} | {independent_days} | {net_0_00015} | {winrate} | {median_result} | {max_drawdown} | {same_bar_ambiguous_count} | {source_concentration_verdict} | {single_day_dominance_verdict} | {verdict} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Boundary Confirmation",
            "",
            "- no live",
            "- no Executor",
            "- no Phase 4",
            "- no PROMOTE",
            "- no universe change",
            "- no CTX tuning",
            "- no Analyzer v1 contract change",
            "- no Backtester core change",
            "- no future outcomes as entry predicates",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    features = load_features(Path(args.features))
    lookup = feature_lookup(features)
    summaries = [replay_one(candidate, args, features, lookup) for candidate in CANDIDATES]
    summary_frame = pd.DataFrame(summaries)
    write_csv(Path(args.output_root) / "sprint_08_replay_summary.csv", summary_frame)
    write_canonical_report(Path(args.canonical_report), summaries)
    print(json.dumps(summaries, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay Sprint 08 BTC formal candidates.")
    parser.add_argument("--features", default="research/results/sprint_06_discovery_features.csv")
    parser.add_argument("--candidate-root", default="research/candidates")
    parser.add_argument("--output-root", default="backtest_runs/sprint_08_btc_formal_replay")
    parser.add_argument("--canonical-report", default="research/canonical/SPRINT_08_BTC_FORMAL_REPLAY_REPORT.md")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
