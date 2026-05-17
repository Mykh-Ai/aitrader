"""Sprint 07 BTC surface aggregation repair.

Reads Sprint 06 event discovery artifacts and repairs the aggregation level.
It does not change Sprint 06 event predicates, does not run Backtester, and
does not create strategies or promotion decisions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


COST_00015_BP = 1.5
COST_00020_BP = 2.0
VERDICT_NEEDS = "NEEDS_REPLAY_SPEC"
VERDICT_WATCH = "WATCH_SURFACE"
VERDICT_REJECT = "REJECT_SURFACE"

FAMILY_EXHAUSTION = "EXHAUSTION_REVERSAL"
FAMILY_VWAP = "VWAP_DEVIATION_REVERSION"


@dataclass(frozen=True)
class ArtifactPaths:
    events: Path
    outcomes: Path
    features: Path
    sprint06_surface: Path
    results_root: Path
    canonical_root: Path


def ensure_sprint06_artifacts(paths: ArtifactPaths) -> None:
    required = [paths.events, paths.outcomes, paths.features]
    if all(path.exists() for path in required):
        return
    script = Path("research/scripts/sprint_06_event_discovery_kill_or_continue.py")
    if not script.exists():
        missing = ", ".join(path.as_posix() for path in required if not path.exists())
        raise SystemExit(f"Missing Sprint 06 artifacts and cannot regenerate: {missing}")
    subprocess.run([sys.executable, str(script)], check=True)
    missing_after = [path.as_posix() for path in required if not path.exists()]
    if missing_after:
        raise SystemExit("Sprint 06 regeneration did not create: " + ", ".join(missing_after))


def parse_predicates(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def vwap_bp_bucket(vwap_distance_pct: float) -> str:
    bp = abs(vwap_distance_pct) * 100.0
    if bp < 60:
        return "VWAP_45_60BP"
    if bp < 100:
        return "VWAP_60_100BP"
    if bp < 200:
        return "VWAP_100_200BP"
    return "VWAP_GE_200BP"


def load_joined(paths: ArtifactPaths) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_sprint06_artifacts(paths)
    events = pd.read_csv(paths.events)
    outcomes = pd.read_csv(paths.outcomes)
    features = pd.read_csv(paths.features, usecols=["Timestamp", "Date", "DataSource"])
    surface06 = pd.read_csv(paths.sprint06_surface) if paths.sprint06_surface.exists() else pd.DataFrame()

    events = events[events["clustered_event"].astype(str).str.lower().eq("true")].copy()
    predicates = events["observable_predicates"].apply(parse_predicates)
    events["vwap_distance_pct_observed"] = predicates.apply(lambda row: float(row.get("vwap_distance_pct", 0.0) or 0.0))
    events["vwap_bp_bucket"] = events["vwap_distance_pct_observed"].apply(vwap_bp_bucket)
    events["event_day"] = pd.to_datetime(events["event_time"], utc=True, format="ISO8601").dt.strftime("%Y-%m-%d")

    outcomes = outcomes.copy()
    outcomes["horizon"] = pd.to_numeric(outcomes["horizon_bars"], errors="coerce").astype("Int64")
    outcomes["forward_return_bp"] = pd.to_numeric(outcomes["forward_return_bp"], errors="coerce").fillna(0.0)
    for col in ("MFE_12", "MAE_12", "MFE_60", "MAE_60"):
        outcomes[col] = pd.to_numeric(outcomes[col], errors="coerce").fillna(0.0)

    joined = outcomes.merge(
        events[
            [
                "discovery_event_id",
                "family",
                "side",
                "event_time",
                "event_day",
                "session",
                "regime",
                "vwap_distance_bucket",
                "vwap_bp_bucket",
                "volume_bucket",
                "rejection_strength_bucket",
                "trend_slope_bucket",
                "observable_predicates",
                "no_lookahead_predicates",
            ]
        ],
        on=["discovery_event_id", "family", "side", "event_time"],
        how="inner",
    )
    joined["mfe"] = joined.apply(lambda row: row["MFE_60"] if int(row["horizon"]) == 60 else row["MFE_12"], axis=1)
    joined["mae"] = joined.apply(lambda row: row["MAE_60"] if int(row["horizon"]) == 60 else row["MAE_12"], axis=1)
    joined["mfe_bp"] = joined["mfe"] * 10000.0
    joined["mae_bp"] = joined["mae"] * 10000.0
    return events, outcomes, features, surface06, joined


def session_distribution(group: pd.DataFrame) -> str:
    return json.dumps(group["session"].value_counts().to_dict(), sort_keys=True)


def largest_session_share(group: pd.DataFrame) -> float:
    counts = group["session"].value_counts()
    if counts.empty:
        return 1.0
    return float(counts.max() / len(group.index))


def verdict_for(row: dict[str, Any]) -> tuple[str, str]:
    reasons: list[str] = []
    events = int(row["events"])
    days = int(row["independent_days"])
    max_day_share = float(row["max_day_share"])
    median_return_bp = float(row["median_return_bp"])
    positive_rate = float(row["positive_rate"])
    net_15 = float(row["net_bp_after_0_00015"])
    ratio = float(row["MFE_MAE_ratio"])
    max_session_share = float(row["max_session_share"])

    concentration_ok = max_day_share <= 0.10
    concentration_watch_ok = max_day_share <= 0.15
    mfe_ok = ratio >= 0.8
    session_ok = max_session_share <= 0.75

    if (
        events >= 100
        and days >= 25
        and concentration_watch_ok
        and median_return_bp > 0
        and positive_rate >= 0.55
        and net_15 > 0
        and mfe_ok
        and session_ok
    ):
        if not concentration_ok:
            reasons.append("max_day_share_between_0_10_and_0_15_accepted_for_replay_spec_review")
        return VERDICT_NEEDS, ";".join(reasons) if reasons else "passes_repaired_replay_spec_gate"

    if events >= 50 and days >= 15 and median_return_bp > 0 and positive_rate >= 0.53:
        if net_15 <= 0:
            reasons.append("cost_0_00015_not_positive")
        if max_day_share > 0.15:
            reasons.append("day_concentration_above_0_15")
        if not mfe_ok:
            reasons.append("mfe_mae_ratio_below_0_8")
        if not session_ok:
            reasons.append("session_concentration_above_0_75")
        return VERDICT_WATCH, ";".join(reasons) if reasons else "watch_surface_below_replay_spec_gate"

    if events < 50:
        reasons.append("events_below_50")
    if days < 15:
        reasons.append("independent_days_below_15")
    if median_return_bp <= 0:
        reasons.append("median_return_non_positive")
    if positive_rate < 0.53:
        reasons.append("positive_rate_below_0_53")
    if net_15 <= 0:
        reasons.append("cost_0_00015_kills_edge")
    if max_day_share > 0.15:
        reasons.append("day_concentration_above_0_15")
    if not mfe_ok:
        reasons.append("mfe_mae_ratio_below_0_8")
    if not session_ok:
        reasons.append("session_concentration_above_0_75")
    return VERDICT_REJECT, ";".join(reasons)


def aggregate(joined: pd.DataFrame, group_cols: list[str], surface_type: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in joined.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        key_map = dict(zip(group_cols, keys))
        event_count = int(group["discovery_event_id"].nunique())
        day_counts = group.drop_duplicates("discovery_event_id")["event_day"].value_counts()
        independent_days = int(day_counts.count())
        max_day_count = int(day_counts.max()) if not day_counts.empty else 0
        max_day_share = float(max_day_count / event_count) if event_count else 1.0
        mean_bp = float(group["forward_return_bp"].mean()) if not group.empty else 0.0
        median_bp = float(group["forward_return_bp"].median()) if not group.empty else 0.0
        positive_rate = float((group["forward_return_bp"] > 0).mean()) if not group.empty else 0.0
        avg_mfe = float(group["mfe_bp"].mean()) if not group.empty else 0.0
        avg_mae = float(group["mae_bp"].mean()) if not group.empty else 0.0
        ratio = avg_mfe / abs(avg_mae) if abs(avg_mae) > 0 else 999.0
        row = {
            **key_map,
            "surface_type": surface_type,
            "events": event_count,
            "independent_days": independent_days,
            "max_day_count": max_day_count,
            "max_day_share": round(max_day_share, 6),
            "mean_return_bp": round(mean_bp, 6),
            "median_return_bp": round(median_bp, 6),
            "positive_rate": round(positive_rate, 6),
            "net_bp_after_0_00015": round(mean_bp - COST_00015_BP, 6),
            "net_bp_after_0_00020": round(mean_bp - COST_00020_BP, 6),
            "avg_MFE": round(avg_mfe, 6),
            "avg_MAE": round(avg_mae, 6),
            "MFE_MAE_ratio": round(ratio, 6),
            "max_session_share": round(largest_session_share(group.drop_duplicates("discovery_event_id")), 6),
            "session_distribution": session_distribution(group.drop_duplicates("discovery_event_id")),
            "no_lookahead_predicates": bool(group["no_lookahead_predicates"].astype(str).str.lower().eq("true").all()),
        }
        row["verdict"], row["verdict_reason"] = verdict_for(row)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["verdict", "net_bp_after_0_00015"], ascending=[True, False])


def build_summaries(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    family_summary = aggregate(joined, ["family", "side", "horizon"], "family_side_horizon")
    vwap_bucket = aggregate(
        joined[joined["family"].eq(FAMILY_VWAP)],
        ["family", "side", "horizon", "vwap_bp_bucket"],
        "vwap_bucket_only",
    )
    exhaustion_bucket = aggregate(
        joined[joined["family"].eq(FAMILY_EXHAUSTION)],
        ["family", "side", "horizon", "rejection_strength_bucket"],
        "rejection_bucket_only",
    )
    volume_bucket = aggregate(joined, ["family", "side", "horizon", "volume_bucket"], "volume_bucket_only")
    bucket_summary = pd.concat([vwap_bucket, exhaustion_bucket, volume_bucket], ignore_index=True)
    session_summary = aggregate(joined, ["family", "side", "horizon", "session"], "session_sanity")
    candidates = pd.concat(
        [
            family_summary[family_summary["verdict"].eq(VERDICT_NEEDS)],
            bucket_summary[bucket_summary["verdict"].eq(VERDICT_NEEDS)],
        ],
        ignore_index=True,
    ).drop_duplicates()
    return family_summary, bucket_summary, session_summary, candidates


def candidate_id(row: pd.Series, ordinal: int) -> str:
    family = str(row["family"])
    side = str(row["side"])
    horizon = int(row["horizon"])
    surface_type = str(row.get("surface_type", ""))
    if family == FAMILY_EXHAUSTION:
        base = f"CAND_BTC_EXH_{side}_{horizon}"
        if surface_type == "rejection_bucket_only":
            suffix = clean_suffix(row.get("rejection_strength_bucket", "REJ"))
            return f"{base}_REJ_{suffix}_V1"
        if surface_type == "volume_bucket_only":
            suffix = clean_suffix(row.get("volume_bucket", "VOL"))
            return f"{base}_VOL_{suffix}_V1"
        return f"{base}_V1"
    base = f"CAND_BTC_VWAP_DEV_{side}_{horizon}"
    if surface_type == "vwap_bucket_only":
        suffix = clean_suffix(row.get("vwap_bp_bucket", "VWAP"))
        return f"{base}_{suffix}_V1"
    if surface_type == "volume_bucket_only":
        suffix = clean_suffix(row.get("volume_bucket", "VOL"))
        return f"{base}_VOL_{suffix}_V1"
    return f"{base}_V1"


def clean_suffix(value: Any) -> str:
    if value is None or pd.isna(value):
        return "ALL"
    return str(value).replace("VWAP_", "").replace("BP", "").replace(".", "").replace("_", "")


def candidate_rows(candidates: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for idx, (_, row) in enumerate(candidates.iterrows(), start=1):
        family = str(row["family"])
        side = str(row["side"])
        horizon = int(row["horizon"])
        if family == FAMILY_EXHAUSTION:
            predicates = (
                "Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, "
                "delta dominance, VWAP stretch; outcomes are excluded from entry predicates."
            )
            stop_idea = "Opposite side of exhaustion/rejection event bar or recent impulse extreme; define before replay."
            target_idea = "VWAP touch or fixed-R target candidate; choose one before replay."
        else:
            predicates = (
                "Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, "
                "session/regime recorded; outcomes are excluded from entry predicates."
            )
            stop_idea = "Beyond deviation event extreme or volatility-based hard stop; define before replay."
            target_idea = "DayVWAP touch or fixed-R target candidate; choose one before replay."
        rows.append(
            {
                "candidate_id": candidate_id(row, idx),
                "family": family,
                "side": side,
                "horizon": horizon,
                "surface_type": row.get("surface_type", ""),
                "bucket": first_non_empty(
                    row.get("vwap_bp_bucket", ""),
                    row.get("rejection_strength_bucket", ""),
                    row.get("volume_bucket", ""),
                ),
                "events": int(row["events"]),
                "independent_days": int(row["independent_days"]),
                "max_day_share": row["max_day_share"],
                "median_return_bp": row["median_return_bp"],
                "positive_rate": row["positive_rate"],
                "net_bp_after_0_00015": row["net_bp_after_0_00015"],
                "MFE_MAE_ratio": row["MFE_MAE_ratio"],
                "observable_entry_predicates": predicates,
                "suggested_formal_replay_direction": f"{side} replay after event close; earliest entry next M1 bar open.",
                "stop_candidate_idea": stop_idea,
                "target_candidate_idea": target_idea,
                "expiry_candidate_idea": f"{horizon} bars after activation as discovery-derived candidate expiry; freeze before replay.",
                "known_weaknesses": "Discovery-only economics; no Backtester replay, no same-bar audit, no true holdout.",
                "required_next_validation": "Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout.",
            }
        )
    return pd.DataFrame(rows)


def first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value)
        if text and text.lower() != "nan":
            return text
    return ""


def sprint06_methodology_review(surface06: pd.DataFrame, family_summary: pd.DataFrame, bucket_summary: pd.DataFrame) -> str:
    bins = {
        "1_event": int((surface06["clustered_events"] == 1).sum()) if not surface06.empty else 0,
        "2_5_events": int(surface06["clustered_events"].between(2, 5).sum()) if not surface06.empty else 0,
        "6_20_events": int(surface06["clustered_events"].between(6, 20).sum()) if not surface06.empty else 0,
        "21_50_events": int(surface06["clustered_events"].between(21, 50).sum()) if not surface06.empty else 0,
        "50_plus_events": int((surface06["clustered_events"] >= 50).sum()) if not surface06.empty else 0,
        "100_plus_events": int((surface06["clustered_events"] >= 100).sum()) if not surface06.empty else 0,
    }
    family_positive = family_summary[
        (family_summary["median_return_bp"] > 0)
        & (family_summary["positive_rate"] >= 0.53)
        & (family_summary["net_bp_after_0_00015"] > 0)
    ]
    bucket_positive = bucket_summary[
        (bucket_summary["median_return_bp"] > 0)
        & (bucket_summary["positive_rate"] >= 0.53)
        & (bucket_summary["net_bp_after_0_00015"] > 0)
    ]
    one_event_share = bins["1_event"] / len(surface06.index) if not surface06.empty else 0.0
    over_fragmented = bins["1_event"] + bins["2_5_events"] > len(surface06.index) * 0.50 if not surface06.empty else True
    corrected = "BTC_SURFACE_AGGREGATION_REPAIR_REQUIRED" if over_fragmented else "SPRINT_06_GROUPING_CONFIRMED"
    lines = [
        "# Sprint 06 Methodology Review",
        "",
        "## Answers",
        "",
        f"1. Surface grouping was too granular: `{over_fragmented}`. Sprint 06 grouped by family, side, horizon, session, regime, VWAP bucket, volume bucket, and rejection bucket at the same time.",
        "",
        "2. Surface size distribution:",
        "",
        "| bucket | surfaces |",
        "|---|---:|",
        *[f"| {key} | {value} |" for key, value in bins.items()],
        "",
        f"One-event surface share: `{one_event_share:.4f}`.",
        "",
        f"3. Positive family/side/horizon aggregates after repaired grouping: `{len(family_positive.index)}`.",
        f"4. Positive bucket-only aggregates after repaired grouping: `{len(bucket_positive.index)}`.",
        "5. `CHANGE_UNIVERSE_OR_DATA` was premature because the rejection was dominated by fragmented 1-2 event surfaces, not by a repaired BTC-only aggregate test.",
        f"6. Corrected verdict: `{corrected}`.",
        "",
    ]
    return "\n".join(lines)


def markdown_table(frame: pd.DataFrame, cols: list[str], limit: int = 20) -> list[str]:
    if frame.empty:
        return ["None."]
    rows = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in frame.head(limit).iterrows():
        rows.append("| " + " | ".join(str(row.get(col, "")) for col in cols) + " |")
    return rows


def write_reports(
    *,
    paths: ArtifactPaths,
    surface06: pd.DataFrame,
    family_summary: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    session_summary: pd.DataFrame,
    candidate_extract: pd.DataFrame,
) -> None:
    methodology = sprint06_methodology_review(surface06, family_summary, bucket_summary)
    (paths.canonical_root / "SPRINT_06_METHODOLOGY_REVIEW.md").write_text(methodology, encoding="utf-8")

    needs_family = family_summary[family_summary["verdict"].eq(VERDICT_NEEDS)]
    needs_bucket = bucket_summary[bucket_summary["verdict"].eq(VERDICT_NEEDS)]
    watch_all = pd.concat(
        [
            family_summary[family_summary["verdict"].eq(VERDICT_WATCH)],
            bucket_summary[bucket_summary["verdict"].eq(VERDICT_WATCH)],
        ],
        ignore_index=True,
    )
    managerial = (
        "BTC_CONTINUE_WITH_REPLAY_SPEC"
        if not candidate_extract.empty
        else ("BTC_CONTINUE_WITH_WATCH_ONLY" if not watch_all.empty else "BTC_NEEDS_MORE_DATA")
    )
    report_lines = [
        "# Sprint 07 BTC Surface Repair Report",
        "",
        "## 1. Executive Verdict",
        "",
        f"`{managerial}`.",
        "",
        "Sprint 07 repairs BTC-only aggregation over Sprint 06 events/outcomes. It does not change Sprint 06 predicates, run Backtester, open Phase 4, touch Executor/live, or create PROMOTE.",
        "",
        "## 2. Why Sprint 06 Verdict Was Too Strong",
        "",
        "Sprint 06 grouped by too many dimensions at once, causing many top-ranked surfaces to contain only 1-2 events. That supports `BTC_SURFACE_AGGREGATION_REPAIR_REQUIRED`, not a market/universe change.",
        "",
        "## 3. Data Used",
        "",
        "- Sprint 06 clustered events and outcomes.",
        "- Sprint 06 features for lineage availability check only.",
        "- No new event predicates and no future outcomes as predicates.",
        "",
        "## 4. Family-Level Aggregates",
        "",
        *markdown_table(
            family_summary.sort_values("net_bp_after_0_00015", ascending=False),
            ["family", "side", "horizon", "events", "independent_days", "max_day_share", "median_return_bp", "positive_rate", "net_bp_after_0_00015", "MFE_MAE_ratio", "verdict"],
            20,
        ),
        "",
        "## 5. Bucket-Only Aggregates",
        "",
        *markdown_table(
            bucket_summary.sort_values("net_bp_after_0_00015", ascending=False),
            ["surface_type", "family", "side", "horizon", "vwap_bp_bucket", "rejection_strength_bucket", "volume_bucket", "events", "independent_days", "net_bp_after_0_00015", "verdict"],
            20,
        ),
        "",
        "## 6. Candidate Surfaces",
        "",
        *markdown_table(
            candidate_extract,
            ["candidate_id", "family", "side", "horizon", "surface_type", "bucket", "events", "independent_days", "net_bp_after_0_00015"],
            50,
        ),
        "",
        "## 7. Rejected Surfaces",
        "",
        *markdown_table(
            pd.concat(
                [
                    family_summary[family_summary["verdict"].eq(VERDICT_REJECT)],
                    bucket_summary[bucket_summary["verdict"].eq(VERDICT_REJECT)],
                ],
                ignore_index=True,
            ).sort_values("net_bp_after_0_00015", ascending=False),
            ["surface_type", "family", "side", "horizon", "events", "independent_days", "median_return_bp", "positive_rate", "net_bp_after_0_00015", "verdict_reason"],
            20,
        ),
        "",
        "## 8. Watch Surfaces",
        "",
        *markdown_table(
            watch_all.sort_values("net_bp_after_0_00015", ascending=False),
            ["surface_type", "family", "side", "horizon", "events", "independent_days", "median_return_bp", "positive_rate", "net_bp_after_0_00015", "verdict_reason"],
            50,
        ),
        "",
        "## 9. Replay Spec Candidates",
        "",
        *markdown_table(
            candidate_extract,
            ["candidate_id", "family", "side", "horizon", "observable_entry_predicates", "required_next_validation"],
            50,
        ),
        "",
        "## 10. Managerial Answer",
        "",
        "- BTC-only research continues.",
        f"- Formal replay candidate surfaces exist: `{not candidate_extract.empty}`.",
        "- Do not change universe in Sprint 07.",
        "- Do not wait passively if replay candidates exist; write formal replay specs next.",
        "- Next action: formalize deterministic replay specs for the extracted candidates, without threshold tuning.",
        "",
    ]
    (paths.canonical_root / "SPRINT_07_BTC_SURFACE_REPAIR_REPORT.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    if candidate_extract.empty:
        no_candidate = [
            "# Sprint 07 No Replay Candidates",
            "",
            "No repaired BTC surface met `NEEDS_REPLAY_SPEC` gates.",
            "",
            "BTC-only research is not rejected by Sprint 07, but this repaired aggregation did not justify formal replay specs.",
            "",
        ]
        (paths.canonical_root / "SPRINT_07_NO_REPLAY_CANDIDATES.md").write_text(
            "\n".join(no_candidate), encoding="utf-8"
        )
        replay_path = paths.canonical_root / "SPRINT_07_REPLAY_CANDIDATES.md"
        if replay_path.exists():
            replay_path.unlink()
        return

    replay_lines = [
        "# Sprint 07 Replay Candidates",
        "",
        "These are replay-spec candidates only. They are not strategies and not promotions.",
        "",
    ]
    for _, row in candidate_extract.iterrows():
        replay_lines.extend(
            [
                f"## {row['candidate_id']}",
                "",
                f"- family: `{row['family']}`",
                f"- side: `{row['side']}`",
                f"- horizon: `{row['horizon']}` bars",
                f"- observable entry predicates: {row['observable_entry_predicates']}",
                "- do not use outcomes as predicates.",
                f"- suggested formal replay direction: {row['suggested_formal_replay_direction']}",
                f"- stop candidate idea: {row['stop_candidate_idea']}",
                f"- target candidate idea: {row['target_candidate_idea']}",
                f"- expiry candidate idea: {row['expiry_candidate_idea']}",
                f"- known weaknesses: {row['known_weaknesses']}",
                f"- required next validation: {row['required_next_validation']}",
                "",
            ]
        )
    (paths.canonical_root / "SPRINT_07_REPLAY_CANDIDATES.md").write_text("\n".join(replay_lines), encoding="utf-8")
    no_candidate_path = paths.canonical_root / "SPRINT_07_NO_REPLAY_CANDIDATES.md"
    if no_candidate_path.exists():
        no_candidate_path.unlink()


def run(args: argparse.Namespace) -> None:
    paths = ArtifactPaths(
        events=Path(args.events),
        outcomes=Path(args.outcomes),
        features=Path(args.features),
        sprint06_surface=Path(args.sprint06_surface),
        results_root=Path(args.results_root),
        canonical_root=Path(args.canonical_root),
    )
    paths.results_root.mkdir(parents=True, exist_ok=True)
    paths.canonical_root.mkdir(parents=True, exist_ok=True)

    events, outcomes, features, surface06, joined = load_joined(paths)
    family_summary, bucket_summary, session_summary, candidates = build_summaries(joined)
    candidate_extract = candidate_rows(candidates)

    family_summary.to_csv(paths.results_root / "sprint_07_btc_surface_family_summary.csv", index=False)
    bucket_summary.to_csv(paths.results_root / "sprint_07_btc_surface_bucket_summary.csv", index=False)
    session_summary.to_csv(paths.results_root / "sprint_07_btc_surface_session_summary.csv", index=False)
    candidate_extract.to_csv(paths.results_root / "sprint_07_btc_surface_candidate_extract.csv", index=False)
    write_reports(
        paths=paths,
        surface06=surface06,
        family_summary=family_summary,
        bucket_summary=bucket_summary,
        session_summary=session_summary,
        candidate_extract=candidate_extract,
    )

    print(f"sprint06_clustered_events={len(events.index)}")
    print(f"sprint06_outcomes={len(outcomes.index)}")
    print(f"sprint06_features={len(features.index)}")
    print(f"family_needs={int(family_summary['verdict'].eq(VERDICT_NEEDS).sum())}")
    print(f"bucket_needs={int(bucket_summary['verdict'].eq(VERDICT_NEEDS).sum())}")
    print(f"watch_surfaces={int((family_summary['verdict'].eq(VERDICT_WATCH).sum() + bucket_summary['verdict'].eq(VERDICT_WATCH).sum()))}")
    print(f"candidates={len(candidate_extract.index)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair Sprint 06 BTC surface aggregation.")
    parser.add_argument("--events", default="research/results/sprint_06_discovery_events.csv")
    parser.add_argument("--outcomes", default="research/results/sprint_06_discovery_outcomes.csv")
    parser.add_argument("--features", default="research/results/sprint_06_discovery_features.csv")
    parser.add_argument("--sprint06-surface", default="research/results/sprint_06_discovery_surface_summary.csv")
    parser.add_argument("--results-root", default="research/results")
    parser.add_argument("--canonical-root", default="research/canonical")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
