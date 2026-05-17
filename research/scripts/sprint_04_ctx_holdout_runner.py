"""Sprint 04 CTX-only holdout runner.

This wrapper runs only the frozen Sprint 03 CTX short ruleset on feed-audited
true holdout days. It never tunes parameters and never mixes Sprint 03 pooled
replay outputs with Sprint 04 holdout outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import sprint_03_formal_candidate_rulesets as s3
from sprint_04_holdout_feed_audit import read_freeze_context


CANDIDATE_ID = s3.CTX_SPEC.candidate_id
RULE_VERSION = s3.CTX_SPEC.rule_version
DEFAULT_CANDIDATE_DIR = Path("research/candidates") / CANDIDATE_ID
DEFAULT_OUTPUT_ROOT = Path("backtest_runs/sprint_04_ctx_holdout")
HOLDOUT_LOG_COLUMNS = [
    "date",
    "new_events",
    "new_trade_days",
    "cost_0_net",
    "cost_00010_net",
    "cost_00015_net",
    "cost_00020_net",
    "same_bar_count",
    "same_bar_pct",
    "source_concentration_status",
    "single_day_dominance_status",
    "verdict_after_batch",
    "notes",
]


def ensure_holdout_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=HOLDOUT_LOG_COLUMNS)
        writer.writeheader()


def load_usable_days(audit_csv: Path) -> list[str]:
    if not audit_csv.exists():
        return []
    audit = pd.read_csv(audit_csv)
    if audit.empty or "usable_for_holdout" not in audit.columns:
        return []
    usable = audit[audit["usable_for_holdout"].astype(str).str.lower().eq("true")]
    return sorted(usable["date"].astype(str).tolist())


def source_dirs_for_days(days: list[str], analyzer_runs_root: Path) -> list[Path]:
    dirs: list[Path] = []
    missing: list[str] = []
    for day in days:
        path = analyzer_runs_root / f"{day}_to_{day}_run_001"
        if path.exists() and (path / "analyzer_setups.csv").exists():
            dirs.append(path)
        else:
            missing.append(path.as_posix())
    if missing:
        raise SystemExit("Missing Analyzer run dirs for usable holdout days: " + ", ".join(missing))
    return dirs


def cost_net(cost_report: pd.DataFrame, cost_level: str) -> float:
    row = cost_report[cost_report["cost_level"].astype(str).eq(cost_level)]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["net_result"])


def append_holdout_log(
    *,
    path: Path,
    date_label: str,
    events: pd.DataFrame,
    cost_report: pd.DataFrame,
    source_report: pd.DataFrame,
    same_bar: dict[str, Any],
    verdict: str,
) -> None:
    ensure_holdout_log(path)
    source_row = source_report.iloc[0].to_dict() if not source_report.empty else {}
    largest_share = float(source_row.get("largest_day_abs_result_share", 1.0) or 0.0)
    single_day_status = "PASS" if largest_share <= 0.33 else "FAIL"
    new_trade_days = int(source_row.get("independent_trade_days", 0) or 0)
    row = {
        "date": date_label,
        "new_events": int(len(events.index)),
        "new_trade_days": new_trade_days,
        "cost_0_net": cost_net(cost_report, "0.00000"),
        "cost_00010_net": cost_net(cost_report, "0.00010"),
        "cost_00015_net": cost_net(cost_report, "0.00015"),
        "cost_00020_net": cost_net(cost_report, "0.00020"),
        "same_bar_count": int(same_bar.get("ambiguous_trades", 0)),
        "same_bar_pct": round(float(same_bar.get("same_bar_pct", 0.0)), 6),
        "source_concentration_status": str(source_row.get("pass_fail", "FAIL")),
        "single_day_dominance_status": single_day_status,
        "verdict_after_batch": verdict,
        "notes": "Sprint 04 frozen CTX holdout replay; no tuning",
    }
    with path.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=HOLDOUT_LOG_COLUMNS)
        writer.writerow(row)


def holdout_verdict(
    *,
    events: pd.DataFrame,
    cost_report: pd.DataFrame,
    source_report: pd.DataFrame,
    same_bar: dict[str, Any],
    no_lookahead: dict[str, Any],
) -> str:
    if no_lookahead["status"] != "PASS":
        return "BLOCKED"
    hard = cost_report[cost_report["cost_level"].astype(str).eq("0.00015")]
    if hard.empty or str(hard.iloc[0]["pass_fail"]) != "PASS":
        return "REJECT_COST_FAIL"
    source_row = source_report.iloc[0].to_dict() if not source_report.empty else {}
    trade_days = int(source_row.get("independent_trade_days", 0) or 0)
    if int(len(events.index)) < 25 or trade_days < 10:
        return "WAIT_HOLDOUT_IN_PROGRESS"
    if str(source_row.get("pass_fail", "FAIL")) != "PASS":
        return "WAIT_HOLDOUT_IN_PROGRESS"
    if str(same_bar.get("verdict", "WAIT")) != "PASS":
        return "WAIT_SAME_BAR_NOT_CLEARED"
    return "WAIT_HOLDOUT_IN_PROGRESS"


def no_data_summary(output_root: Path, holdout_log: Path, reason: str) -> dict[str, Any]:
    ensure_holdout_log(holdout_log)
    output_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "candidate_id": CANDIDATE_ID,
        "rule_version": RULE_VERSION,
        "verdict": "WAIT_NO_HOLDOUT_DATA",
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_root / "holdout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_dir = Path(args.candidate_dir)
    output_root = Path(args.output_root)
    audit_csv = Path(args.audit_csv)
    holdout_log = candidate_dir / "holdout_log.csv"
    usable_days = load_usable_days(audit_csv)
    if not usable_days:
        return no_data_summary(output_root, holdout_log, "no feed-audited usable post-freeze UTC day")

    freeze = read_freeze_context(Path(args.protocol_path))
    source_dirs = source_dirs_for_days(usable_days, Path(args.analyzer_runs_root))
    raw_days = [pd.Timestamp(day).date() for day in usable_days]
    raw = s3.load_raw_window(raw_days, Path(args.feed_root), Path(args.feed_recovered_root))
    if raw.empty:
        return no_data_summary(output_root, holdout_log, "no raw rows loaded for usable holdout days")

    events = s3.build_ctx_candidate_events(source_dirs, raw)
    output_root.mkdir(parents=True, exist_ok=True)
    events_path = output_root / "candidate_events.csv"
    events.to_csv(events_path, index=False)

    reports_dir = output_root / "reports" / CANDIDATE_ID
    reports_dir.mkdir(parents=True, exist_ok=True)
    no_lookahead = s3.no_lookahead_check(events, reports_dir)
    artifact_dir = output_root / "artifacts" / CANDIDATE_ID
    s3.write_artifact_bundle(
        artifact_dir=artifact_dir,
        spec=s3.CTX_SPEC,
        events=events,
        raw=raw,
        candidate_events_path=events_path,
        freeze_timestamp=freeze.timestamp.isoformat(),
    )
    output_dirs = s3.run_candidate_replays(artifact_dir=artifact_dir, spec=s3.CTX_SPEC, output_root=output_root)
    cost_report = s3.build_cost_report(s3.CTX_SPEC, output_dirs, reports_dir)
    source_report = s3.build_source_concentration_report(s3.CTX_SPEC, output_dirs, reports_dir)
    same_bar = s3.write_same_bar_report(s3.CTX_SPEC, output_dirs, reports_dir)
    verdict = holdout_verdict(
        events=events,
        cost_report=cost_report,
        source_report=source_report,
        same_bar=same_bar,
        no_lookahead=no_lookahead,
    )
    date_label = usable_days[0] if len(usable_days) == 1 else f"{usable_days[0]}..{usable_days[-1]}"
    append_holdout_log(
        path=holdout_log,
        date_label=date_label,
        events=events,
        cost_report=cost_report,
        source_report=source_report,
        same_bar=same_bar,
        verdict=verdict,
    )
    summary = {
        "candidate_id": CANDIDATE_ID,
        "rule_version": RULE_VERSION,
        "usable_days": usable_days,
        "candidate_events": str(events_path),
        "event_count": int(len(events.index)),
        "output_root": str(output_root),
        "verdict": verdict,
        "no_lookahead": no_lookahead,
        "same_bar": same_bar,
    }
    (output_root / "holdout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen Sprint 03 CTX candidate on Sprint 04 holdout days.")
    parser.add_argument("--protocol-path", default="research/canonical/HOLDOUT_PROTOCOL.md")
    parser.add_argument("--audit-csv", default=str(DEFAULT_CANDIDATE_DIR / "holdout_feed_audit.csv"))
    parser.add_argument("--analyzer-runs-root", default="analyzer_runs")
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--feed-recovered-root", default="feed_recovered")
    parser.add_argument("--candidate-dir", default=str(DEFAULT_CANDIDATE_DIR))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
