"""Forward watchlist snapshot for IMPULSE_FADE_RECLAIM_LONG_V1.

This is a research-only sidecar over the entry-observable feature table
produced by impulse_fade_long_entry_observable_proxy_scan.py. It freezes two
long-side watch selectors and writes window-namespaced outputs. Existing
outputs are not overwritten unless --overwrite is passed.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


WINDOW_RE = re.compile(r"(\d{4}-\d{2}-\d{2}_to_\d{4}-\d{2}-\d{2})")

CLUSTER_WINDOWS_MINUTES = [0, 30, 60, 120, 240, 480, 1440]

DETAIL_COLUMNS = [
    "WatchSelectorId",
    "WatchSelector",
    "Date",
    "Period",
    "SetupId",
    "EntryTs",
    "EntrySignalTs",
    "EntryActivationTs",
    "ExitTs",
    "ExitReason",
    "ExitReasonCategory",
    "TradePnl",
    "TradeReturnPct",
    "Win",
    "H2_Post12Label_v1",
    "FullFade",
    "PartialFade",
    "NoFade",
    "EntryHourUTC",
    "SetupBarTs",
    "ReferenceEventTs",
    "ReferenceLevel",
    "SetupCloseLocationInImpulseRange",
    "ReclaimDepthToImpulseRange",
    "ReclaimDepthToSetupRange",
    "Setup_BodyToRange",
    "Setup_CloseLocation",
    "Setup_LowerWickToRange",
    "Setup_UpperWickToRange",
    "Impulse_BodyToRange",
    "Impulse_CloseLocation",
    "Impulse_LowerWickToRange",
    "Impulse_UpperWickToRange",
    "Impulse_ImpulseRangeRatio_20_v1",
    "Impulse_ImpulseVolumeRatio_v1",
    "Impulse_ImpulseDeltaRatio_v1",
    "Impulse_ImpulseOIRatio_v1",
    "Impulse_PreCompression_6v20_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
    "SpikeCount",
    "SpikeSignature",
]


@dataclass(frozen=True)
class WatchSelector:
    selector_id: str
    selector: str

    def mask(self, df: pd.DataFrame) -> pd.Series:
        if self.selector_id == "LONG_LATE_US_STRUCTURAL_WATCH":
            return (
                (num(df, "SetupCloseLocationInImpulseRange") >= 0.75)
                & num(df, "EntryHourUTC").between(16, 23, inclusive="both")
                & (num(df, "Impulse_BodyToRange") > 0.75)
            ).fillna(False)
        if self.selector_id == "LONG_LATE_US_LOW_STRESS_DEPTH_CHILD":
            low_stress = (
                (num(df, "RelVolume_20") <= 1.5)
                & (num(df, "DeltaAbsRatio_20") <= 2.0)
                & (num(df, "OIChangeAbsRatio_20") <= 5.0)
                & (num(df, "SpikeCount") <= 2)
            )
            return (
                low_stress
                & (num(df, "ReclaimDepthToImpulseRange") > 0.3)
                & num(df, "EntryHourUTC").between(16, 23, inclusive="both")
            ).fillna(False)
        raise ValueError(f"Unknown selector_id: {self.selector_id}")


WATCH_SELECTORS = [
    WatchSelector(
        "LONG_LATE_US_STRUCTURAL_WATCH",
        "SetupCloseLocationInImpulseRange >= 0.75 & entry_hour_16_23 & Impulse_BodyToRange > 0.75",
    ),
    WatchSelector(
        "LONG_LATE_US_LOW_STRESS_DEPTH_CHILD",
        "low_stress_long & ReclaimDepthToImpulseRange > 0.3 & entry_hour_16_23",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument(
        "--features-csv",
        default=None,
        type=Path,
        help="Entry-observable long feature CSV. Defaults to latest matching research/results file.",
    )
    parser.add_argument("--results-dir", default="research/results", type=Path)
    parser.add_argument("--findings-dir", default="research/findings", type=Path)
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing watchlist outputs.")
    return parser.parse_args()


def num(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(float("nan"), index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    values = df[column]
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False).astype(bool)
    return values.fillna("").astype(str).str.lower().isin({"true", "1", "yes", "y"})


def infer_latest_features_csv(results_dir: Path) -> Path:
    candidates = sorted(results_dir.glob("impulse_fade_long_entry_observable_features_*.csv"))
    if not candidates:
        raise FileNotFoundError("No impulse_fade_long_entry_observable_features_*.csv file found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def infer_window(path: Path, df: pd.DataFrame) -> str:
    match = WINDOW_RE.search(path.name)
    if match:
        return match.group(1)
    if "Date" not in df.columns or df.empty:
        raise ValueError("Cannot infer window from filename or Date column.")
    return f"{df['Date'].min()}_to_{df['Date'].max()}"


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in [
        "TradePnl",
        "TradeReturnPct",
        "EntryHourUTC",
        "SetupCloseLocationInImpulseRange",
        "ReclaimDepthToImpulseRange",
        "ReclaimDepthToSetupRange",
        "Setup_BodyToRange",
        "Setup_CloseLocation",
        "Setup_LowerWickToRange",
        "Setup_UpperWickToRange",
        "Impulse_BodyToRange",
        "Impulse_CloseLocation",
        "Impulse_LowerWickToRange",
        "Impulse_UpperWickToRange",
        "Impulse_ImpulseRangeRatio_20_v1",
        "Impulse_ImpulseVolumeRatio_v1",
        "Impulse_ImpulseDeltaRatio_v1",
        "Impulse_ImpulseOIRatio_v1",
        "Impulse_PreCompression_6v20_v1",
        "RelVolume_20",
        "DeltaAbsRatio_20",
        "OIChangeAbsRatio_20",
        "LiqTotalRatio_20",
        "SpikeCount",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "EntryTs" in df.columns:
        df["EntryTs"] = pd.to_datetime(df["EntryTs"], utc=True)
    elif "EntrySignalTs" in df.columns:
        df["EntryTs"] = pd.to_datetime(df["EntrySignalTs"], utc=True)
    else:
        raise ValueError("Expected EntryTs or EntrySignalTs in feature table.")

    df["Win"] = bool_series(df, "Win")
    df["FullFade"] = bool_series(df, "FullFade")
    df["NoFade"] = bool_series(df, "NoFade")
    if "PartialFade" not in df.columns:
        df["PartialFade"] = df.get("H2_Post12Label_v1", "").fillna("").astype(str).eq("PARTIAL_FADE")
    else:
        df["PartialFade"] = bool_series(df, "PartialFade")
    return df


def build_watch_trades(features: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for selector in WATCH_SELECTORS:
        subset = features.loc[selector.mask(features)].copy()
        subset["WatchSelectorId"] = selector.selector_id
        subset["WatchSelector"] = selector.selector
        frames.append(subset)
    if not frames:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    trades = pd.concat(frames, ignore_index=True)
    trades = trades.sort_values(["WatchSelectorId", "EntryTs", "SetupId"]).reset_index(drop=True)
    return trades.loc[:, [column for column in DETAIL_COLUMNS if column in trades.columns]]


def metrics_for(df: pd.DataFrame, selector_id: str, selector: str) -> dict[str, Any]:
    trades = len(df.index)
    pre = df.loc[df["Period"].eq("pre_gap")].copy() if "Period" in df.columns else pd.DataFrame()
    post = df.loc[df["Period"].eq("post_recovery")].copy() if "Period" in df.columns else pd.DataFrame()
    day = day_split(df)
    top1 = top_n_winners(df, 1)
    total_pnl = float(num(df, "TradePnl").fillna(0.0).sum())
    return {
        "WatchSelectorId": selector_id,
        "WatchSelector": selector,
        "Trades": trades,
        "Wins": int(df["Win"].sum()) if trades and "Win" in df.columns else 0,
        "WinRate": rate(df, "Win"),
        "FullFadeRate": rate(df, "FullFade"),
        "NoFadeRate": rate(df, "NoFade"),
        "PartialFadeRate": rate(df, "PartialFade"),
        "Pnl": total_pnl,
        "AvgPnl": total_pnl / trades if trades else math.nan,
        "MaxDrawdownPnl": max_drawdown_pnl(df),
        "TradeDays": int(df["Date"].nunique()) if trades and "Date" in df.columns else 0,
        "PositiveTradeDays": day["PositiveTradeDays"],
        "NegativeTradeDays": day["NegativeTradeDays"],
        "FlatTradeDays": day["FlatTradeDays"],
        "PreTrades": len(pre.index),
        "PreTradeDays": int(pre["Date"].nunique()) if not pre.empty and "Date" in pre.columns else 0,
        "PrePnl": float(num(pre, "TradePnl").fillna(0.0).sum()) if not pre.empty else 0.0,
        "PrePositiveTradeDays": positive_day_count(pre),
        "PostTrades": len(post.index),
        "PostTradeDays": int(post["Date"].nunique()) if not post.empty and "Date" in post.columns else 0,
        "PostPnl": float(num(post, "TradePnl").fillna(0.0).sum()) if not post.empty else 0.0,
        "PostPositiveTradeDays": positive_day_count(post),
        "Top1WinnerPnl": top1,
        "Top1WinnerShareOfTotal": top1 / total_pnl if total_pnl else math.nan,
        "PromotionGateStatus": promotion_gate_status(df),
    }


def rate(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return math.nan
    return float(df[column].fillna(False).astype(bool).mean())


def max_drawdown_pnl(df: pd.DataFrame) -> float:
    if df.empty:
        return math.nan
    ordered = df.sort_values("EntryTs")
    equity = num(ordered, "TradePnl").fillna(0.0).cumsum()
    drawdown = equity - equity.cummax()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def top_n_winners(df: pd.DataFrame, n: int) -> float:
    pnl = num(df, "TradePnl").dropna()
    winners = pnl.loc[pnl > 0].sort_values(ascending=False).head(n)
    return float(winners.sum()) if not winners.empty else 0.0


def bottom_n_losers(df: pd.DataFrame, n: int) -> float:
    pnl = num(df, "TradePnl").dropna()
    losers = pnl.loc[pnl < 0].sort_values(ascending=True).head(n)
    return float(losers.sum()) if not losers.empty else 0.0


def positive_day_count(df: pd.DataFrame) -> int:
    if df.empty or "Date" not in df.columns:
        return 0
    grouped = df.groupby("Date")["TradePnl"].sum()
    return int((grouped > 0).sum())


def day_split(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "Date" not in df.columns:
        return {"PositiveTradeDays": 0, "NegativeTradeDays": 0, "FlatTradeDays": 0}
    grouped = df.groupby("Date")["TradePnl"].sum()
    return {
        "PositiveTradeDays": int((grouped > 0).sum()),
        "NegativeTradeDays": int((grouped < 0).sum()),
        "FlatTradeDays": int((grouped == 0).sum()),
    }


def promotion_gate_status(df: pd.DataFrame) -> str:
    if df.empty:
        return "NO_TRADES"
    post = df.loc[df["Period"].eq("post_recovery")].copy()
    if int(post["Date"].nunique()) < 10:
        return "WATCH_ONLY_POST_DAYS_LT_10"
    if len(post.index) < 25:
        return "WATCH_ONLY_POST_TRADES_LT_25"
    if float(num(post, "TradePnl").fillna(0.0).sum()) <= 0:
        return "WATCH_ONLY_POST_PNL_NOT_POSITIVE"
    return "WATCH_READY_FOR_RULESET_REVIEW"


def build_summary(features: pd.DataFrame, watch_trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    baseline_selector = "baseline_all_long_completed_trades"
    rows.append(metrics_for(features, "BASELINE_LONG", baseline_selector))
    for selector in WATCH_SELECTORS:
        subset = watch_trades.loc[watch_trades["WatchSelectorId"].eq(selector.selector_id)].copy()
        rows.append(metrics_for(subset, selector.selector_id, selector.selector))
    return pd.DataFrame(rows)


def build_day_split(watch_trades: pd.DataFrame) -> pd.DataFrame:
    if watch_trades.empty:
        return pd.DataFrame()
    grouped = (
        watch_trades.groupby(["WatchSelectorId", "WatchSelector", "Date", "Period"], dropna=False)
        .agg(
            Trades=("SetupId", "count"),
            Wins=("Win", "sum"),
            FullFade=("FullFade", "sum"),
            NoFade=("NoFade", "sum"),
            Pnl=("TradePnl", "sum"),
        )
        .reset_index()
    )
    grouped["WinRate"] = grouped["Wins"] / grouped["Trades"]
    grouped["FullFadeRate"] = grouped["FullFade"] / grouped["Trades"]
    grouped["NoFadeRate"] = grouped["NoFade"] / grouped["Trades"]
    grouped["PositiveDay"] = grouped["Pnl"] > 0
    return grouped.sort_values(["WatchSelectorId", "Date"]).reset_index(drop=True)


def cluster_first(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes == 0 or df.empty:
        return df.copy()
    ordered = df.sort_values("EntryTs")
    keep_indices: list[Any] = []
    last_kept: pd.Timestamp | None = None
    for idx, row in ordered.iterrows():
        ts = row["EntryTs"]
        if pd.isna(ts):
            continue
        if last_kept is None or (ts - last_kept).total_seconds() >= minutes * 60:
            keep_indices.append(idx)
            last_kept = ts
    return ordered.loc[keep_indices].copy()


def build_cluster_summary(watch_trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for selector in WATCH_SELECTORS:
        raw = watch_trades.loc[watch_trades["WatchSelectorId"].eq(selector.selector_id)].copy()
        for window in CLUSTER_WINDOWS_MINUTES:
            clustered = cluster_first(raw, window)
            row = metrics_for(clustered, selector.selector_id, selector.selector)
            row["ClusterWindowMinutes"] = window
            row["RawTradesBeforeCluster"] = len(raw.index)
            row["DroppedDuplicates"] = len(raw.index) - len(clustered.index)
            rows.append(row)
    return pd.DataFrame(rows)


def build_pnl_concentration(watch_trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for selector in WATCH_SELECTORS:
        subset = watch_trades.loc[watch_trades["WatchSelectorId"].eq(selector.selector_id)].copy()
        total_pnl = float(num(subset, "TradePnl").fillna(0.0).sum())
        gross_loss = float(abs(num(subset, "TradePnl").loc[num(subset, "TradePnl") < 0].sum()))
        for n in (1, 2, 3):
            top_winners = top_n_winners(subset, n)
            bottom_losers = bottom_n_losers(subset, n)
            rows.append(
                {
                    "WatchSelectorId": selector.selector_id,
                    "WatchSelector": selector.selector,
                    "TopN": n,
                    "Trades": len(subset.index),
                    "TopNWinnerPnl": top_winners,
                    "TopNLoserPnl": bottom_losers,
                    "TotalPnl": total_pnl,
                    "TopWinnerShareOfTotal": top_winners / total_pnl if total_pnl else math.nan,
                    "BottomLoserShareOfGrossLoss": abs(bottom_losers) / gross_loss if gross_loss else math.nan,
                }
            )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, [column for column in columns if column in df.columns]].copy()
    for column in view.columns:
        if pd.api.types.is_float_dtype(view[column]):
            view[column] = view[column].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in view.columns) + " |")
    return "\n".join(lines)


def write_finding(
    *,
    path: Path,
    window: str,
    features_path: Path,
    trades_path: Path,
    summary_path: Path,
    day_split_path: Path,
    cluster_path: Path,
    concentration_path: Path,
    summary: pd.DataFrame,
    day_split: pd.DataFrame,
    cluster: pd.DataFrame,
    concentration: pd.DataFrame,
) -> None:
    primary_day = day_split.loc[day_split["WatchSelectorId"].eq("LONG_LATE_US_STRUCTURAL_WATCH")].copy()
    child_day = day_split.loc[day_split["WatchSelectorId"].eq("LONG_LATE_US_LOW_STRESS_DEPTH_CHILD")].copy()
    text = f"""# IMPULSE_FADE_RECLAIM_LONG_V1 Forward Watchlist

Date: {datetime.now(timezone.utc).date().isoformat()}

Status: forward watchlist diagnostic only. No Analyzer grammar change, no Backtester ruleset change, no promotion.

## Window

`{window}`

## Frozen Watch Selectors

- `LONG_LATE_US_STRUCTURAL_WATCH`: `SetupCloseLocationInImpulseRange >= 0.75 & entry_hour_16_23 & Impulse_BodyToRange > 0.75`
- `LONG_LATE_US_LOW_STRESS_DEPTH_CHILD`: `low_stress_long & ReclaimDepthToImpulseRange > 0.3 & entry_hour_16_23`

`H2_Post12Label_v1` is used only as target labeling in metrics, not as an entry predicate.

## Outputs

- Source feature table: `{features_path.as_posix()}`
- Watch trades: `{trades_path.as_posix()}`
- Watch summary: `{summary_path.as_posix()}`
- Day split: `{day_split_path.as_posix()}`
- Cluster-first summary: `{cluster_path.as_posix()}`
- PnL concentration: `{concentration_path.as_posix()}`

## Summary

{markdown_table(summary, ['WatchSelectorId', 'Trades', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'MaxDrawdownPnl', 'TradeDays', 'PositiveTradeDays', 'NegativeTradeDays', 'PreTrades', 'PreTradeDays', 'PrePnl', 'PostTrades', 'PostTradeDays', 'PostPnl', 'PromotionGateStatus'])}

## Primary Day Split

{markdown_table(primary_day, ['Date', 'Period', 'Trades', 'Pnl', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'PositiveDay'])}

## Child Day Split

{markdown_table(child_day, ['Date', 'Period', 'Trades', 'Pnl', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'PositiveDay'])}

## Cluster-First

{markdown_table(cluster, ['WatchSelectorId', 'ClusterWindowMinutes', 'Trades', 'DroppedDuplicates', 'WinRate', 'FullFadeRate', 'NoFadeRate', 'Pnl', 'MaxDrawdownPnl', 'PreTrades', 'PostTrades'])}

## PnL Concentration

{markdown_table(concentration, ['WatchSelectorId', 'TopN', 'Trades', 'TopNWinnerPnl', 'TopNLoserPnl', 'TotalPnl', 'TopWinnerShareOfTotal', 'BottomLoserShareOfGrossLoss'])}

## Read

Both selectors remain watch-only. The gate is intentionally strict: at least 10 post-recovery trade-days, at least 25 post-recovery trades, positive post-recovery PnL, and positive cluster-first behavior before any ruleset review.
"""
    path.write_text(text, encoding="utf-8")


def assert_can_write(paths: list[Path], overwrite: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        names = "\n".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing watchlist outputs:\n{names}\nPass --overwrite to replace them.")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    results_dir = (repo_root / args.results_dir).resolve()
    findings_dir = (repo_root / args.findings_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    findings_dir.mkdir(parents=True, exist_ok=True)

    features_path = (repo_root / args.features_csv).resolve() if args.features_csv else infer_latest_features_csv(results_dir)
    features = prepare_features(pd.read_csv(features_path))
    window = infer_window(features_path, features)

    trades_path = results_dir / f"impulse_fade_long_watchlist_trades_{window}.csv"
    summary_path = results_dir / f"impulse_fade_long_watchlist_summary_{window}.csv"
    day_split_path = results_dir / f"impulse_fade_long_watchlist_day_split_{window}.csv"
    cluster_path = results_dir / f"impulse_fade_long_watchlist_cluster_summary_{window}.csv"
    concentration_path = results_dir / f"impulse_fade_long_watchlist_pnl_concentration_{window}.csv"
    finding_path = findings_dir / f"IMPULSE_FADE_LONG_FORWARD_WATCHLIST_{window}.md"
    outputs = [trades_path, summary_path, day_split_path, cluster_path, concentration_path, finding_path]
    assert_can_write(outputs, args.overwrite)

    watch_trades = build_watch_trades(features)
    summary = build_summary(features, watch_trades)
    day_split = build_day_split(watch_trades)
    cluster = build_cluster_summary(watch_trades)
    concentration = build_pnl_concentration(watch_trades)

    watch_trades.to_csv(trades_path, index=False)
    summary.to_csv(summary_path, index=False)
    day_split.to_csv(day_split_path, index=False)
    cluster.to_csv(cluster_path, index=False)
    concentration.to_csv(concentration_path, index=False)
    write_finding(
        path=finding_path,
        window=window,
        features_path=features_path.relative_to(repo_root),
        trades_path=trades_path.relative_to(repo_root),
        summary_path=summary_path.relative_to(repo_root),
        day_split_path=day_split_path.relative_to(repo_root),
        cluster_path=cluster_path.relative_to(repo_root),
        concentration_path=concentration_path.relative_to(repo_root),
        summary=summary,
        day_split=day_split,
        cluster=cluster,
        concentration=concentration,
    )

    print(
        {
            "window": window,
            "source_features": str(features_path.relative_to(repo_root)),
            "watch_trade_rows": int(len(watch_trades.index)),
            "summary_rows": int(len(summary.index)),
            "day_split_rows": int(len(day_split.index)),
            "cluster_rows": int(len(cluster.index)),
            "concentration_rows": int(len(concentration.index)),
            "finding": str(finding_path.relative_to(repo_root)),
        }
    )


if __name__ == "__main__":
    main()
