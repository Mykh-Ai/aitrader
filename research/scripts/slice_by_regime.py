"""
Repeat reclaim-context asymmetry analysis stratified by PhaseHeuristicLabel.
==========================================================================

Мета: перевірити чи low-stress / high-stress асиметрія виживає
всередині heuristic phase buckets.

Не змінює setup logic, не чіпає replay.
Read-only analysis over existing analyzer artifacts.

Запуск:
    python research/scripts/slice_by_regime.py
    python research/scripts/slice_by_regime.py --runs-dir analyzer_runs
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import pandas as pd

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.day_regime_report import build_day_regime_report  # noqa: E402

# Повторюємо frozen slice definitions з оригінального скрипта
CONTEXT_BOOLEAN = [
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
]

# Де шукати runs (кілька можливих locations)
_SEARCH_PATHS = [
    REPO_ROOT / "analyzer_runs",
    REPO_ROOT / "research" / "findings" / "transition_local_data",
]


def _find_run_dirs(extra_dirs: list[pathlib.Path] | None = None) -> list[pathlib.Path]:
    """Знаходить всі run directories з повним набором артефактів."""
    search = list(_SEARCH_PATHS)
    if extra_dirs:
        search.extend(extra_dirs)

    required_files = [
        "analyzer_features.csv",
        "analyzer_events.csv",
        "analyzer_setups.csv",
        "analyzer_setup_outcomes.csv",
        "analyzer_setup_shortlist.csv",
        "analyzer_research_summary.csv",
    ]

    found = []
    for base in search:
        if not base.exists():
            continue
        for run_dir in sorted(base.iterdir()):
            if not run_dir.is_dir():
                continue
            if all((run_dir / f).exists() for f in required_files):
                found.append(run_dir)

    return found


def _generate_regime_label(run_dir: pathlib.Path) -> str:
    """Генерує PhaseHeuristicLabel для одного run через build_day_regime_report."""
    features = pd.read_csv(run_dir / "analyzer_features.csv")
    events = pd.read_csv(run_dir / "analyzer_events.csv")
    setups = pd.read_csv(run_dir / "analyzer_setups.csv")
    shortlist = pd.read_csv(run_dir / "analyzer_setup_shortlist.csv")
    research_summary = pd.read_csv(run_dir / "analyzer_research_summary.csv")

    regime = build_day_regime_report(features, events, setups, shortlist, research_summary)
    if regime.empty:
        return "EMPTY"
    return str(regime.iloc[0]["PhaseHeuristicLabel"])


def _load_setups_with_regime(run_dirs: list[pathlib.Path]) -> pd.DataFrame:
    """Завантажує setups+outcomes з усіх runs, додає PhaseHeuristicLabel per run."""
    frames = []
    regime_summary = []

    for run_dir in run_dirs:
        setups_path = run_dir / "analyzer_setups.csv"
        outcomes_path = run_dir / "analyzer_setup_outcomes.csv"

        setups = pd.read_csv(setups_path)
        outcomes = pd.read_csv(outcomes_path)[
            ["SetupId", "MFE_Pct", "MAE_Pct", "CloseReturn_Pct", "OutcomeStatus"]
        ]
        merged = setups.merge(outcomes, on="SetupId", how="inner")

        label = _generate_regime_label(run_dir)
        merged["PhaseHeuristicLabel"] = label
        merged["_run"] = run_dir.name

        regime_summary.append({
            "run": run_dir.name,
            "setups": len(setups),
            "phase": label,
        })

        frames.append(merged)

    if not frames:
        sys.exit("ERROR: No valid runs found")

    df = pd.concat(frames, ignore_index=True)

    # Дедуплікація
    before = len(df)
    df = df.drop_duplicates(subset="SetupId", keep="first").reset_index(drop=True)
    after = len(df)
    if before != after:
        print(f"Deduplicated: {before} -> {after} setups (removed {before - after} duplicates)")

    print(f"Loaded {after} unique setups from {len(frames)} run(s)\n")

    # Regime summary
    print("Run regime labels:")
    for rs in regime_summary:
        print(f"  {rs['run']:<50} setups={rs['setups']:>3}  phase={rs['phase']}")
    print()

    return df


def _stats(df: pd.DataFrame, label: str) -> dict:
    """Базова статистика для зрізу (frozen з оригінального скрипта)."""
    n = len(df)
    if n == 0:
        return {"label": label, "n": 0}
    ret = df["CloseReturn_Pct"]
    return {
        "label": label,
        "n": n,
        "mean_ret": ret.mean(),
        "median_ret": ret.median(),
        "pos_rate": (ret > 0).mean(),
        "mean_mfe": df["MFE_Pct"].mean(),
        "mean_mae": df["MAE_Pct"].mean(),
    }


def _print_stats(s: dict) -> None:
    if s["n"] == 0:
        print(f"    {s['label']:<36}  n=0  (empty slice)")
        return
    print(
        f"    {s['label']:<36}  n={s['n']:>3}  "
        f"pos_rate={s['pos_rate']:.1%}  "
        f"mean_ret={s['mean_ret']:+.3f}%  "
        f"median_ret={s['median_ret']:+.3f}%  "
        f"MFE={s['mean_mfe']:.3f}%  "
        f"MAE={s['mean_mae']:.3f}%"
    )


def _make_slices(sub: pd.DataFrame, direction: str) -> list[tuple[str, pd.DataFrame]]:
    """Frozen slice definitions з оригінального скрипта."""
    slices = [("baseline (all)", sub)]
    if len(sub) == 0:
        return slices

    sub = sub.copy()
    sub["_ctx_spike_count"] = sub[CONTEXT_BOOLEAN].sum(axis=1)

    if direction == "LONG":
        abs_med = sub["AbsorptionScore_v1"].median()
        vol_med = sub["RelVolume_20"].median()
        liq_med = sub["LiqTotalRatio_20"].median()
        low_stress = sub[
            (sub["AbsorptionScore_v1"] <= abs_med)
            & (sub["RelVolume_20"] <= vol_med)
            & (sub["LiqTotalRatio_20"] <= liq_med)
        ]
        high_stress = sub[
            (sub["AbsorptionScore_v1"] > abs_med)
            | (sub["RelVolume_20"] > vol_med)
            | (sub["LiqTotalRatio_20"] > liq_med)
        ]
        slices += [
            ("low-stress (all 3 <= median)", low_stress),
            ("high-stress (any 1 > median)", high_stress),
        ]
    elif direction == "SHORT":
        abs_med = sub["AbsorptionScore_v1"].median()
        vol_med = sub["RelVolume_20"].median()
        delta_med = sub["DeltaAbsRatio_20"].median()
        high_stress = sub[
            (sub["AbsorptionScore_v1"] >= abs_med)
            & (sub["RelVolume_20"] >= vol_med)
            & (sub["DeltaAbsRatio_20"] >= delta_med)
        ]
        low_stress = sub[
            (sub["AbsorptionScore_v1"] < abs_med)
            | (sub["RelVolume_20"] < vol_med)
            | (sub["DeltaAbsRatio_20"] < delta_med)
        ]
        slices += [
            ("high-stress (all 3 >= median)", high_stress),
            ("low-stress (any 1 < median)", low_stress),
        ]

    return slices


def _analyze_bucket(df: pd.DataFrame, bucket_label: str) -> list[dict]:
    """Аналізує один phase bucket для обох directions."""
    rows = []
    sep = "-" * 70
    print(f"\n{sep}")
    print(f"PHASE BUCKET: {bucket_label}  (n={len(df)})")
    print(sep)

    for direction in ["LONG", "SHORT"]:
        sub = df[df["Direction"] == direction]
        print(f"\n  DIRECTION: {direction} (n={len(sub)})")
        if len(sub) == 0:
            print("    (no setups)")
            continue

        slices = _make_slices(sub, direction)
        for label, slice_df in slices:
            s = _stats(slice_df, label)
            _print_stats(s)
            rows.append({
                "phase": bucket_label,
                "direction": direction,
                "slice": label,
                **s,
            })

    return rows


def run_analysis(run_dirs: list[pathlib.Path]) -> None:
    print("=" * 70)
    print("REGIME-STRATIFIED RECLAIM CONTEXT ASYMMETRY ANALYSIS")
    print("=" * 70)
    print(f"Script: research/scripts/slice_by_regime.py")
    print(f"Methodology: frozen from research/findings/2026-03_reclaim_context_asymmetry.md")
    print(f"New dimension: PhaseHeuristicLabel from analyzer/day_regime_report.py")
    print()

    df = _load_setups_with_regime(run_dirs)

    total_long = (df["Direction"] == "LONG").sum()
    total_short = (df["Direction"] == "SHORT").sum()
    print(f"Total setups: LONG={total_long}, SHORT={total_short}, ALL={len(df)}")

    phases = sorted(df["PhaseHeuristicLabel"].unique())
    print(f"Phase buckets found: {phases}")

    # Спочатку ALL (unstratified baseline для порівняння)
    all_rows = _analyze_bucket(df, "ALL_PHASES")

    # Потім per-phase
    phase_rows = []
    for phase in phases:
        phase_df = df[df["PhaseHeuristicLabel"] == phase]
        phase_rows.extend(_analyze_bucket(phase_df, phase))

    # Summary comparison table
    print("\n")
    print("=" * 70)
    print("SUMMARY: ASYMMETRY SURVIVAL BY PHASE")
    print("=" * 70)
    print()

    # LONG hypothesis: low-stress pos_rate > baseline pos_rate
    print("LONG hypothesis: low-stress slice pos_rate > baseline")
    print(f"  {'phase':<20} {'baseline_n':>10} {'baseline_pr':>12} {'lowstress_n':>12} {'lowstress_pr':>13} {'delta_pp':>9} {'verdict'}")
    print("  " + "-" * 90)

    for bucket_label in ["ALL_PHASES"] + phases:
        rows = all_rows if bucket_label == "ALL_PHASES" else phase_rows
        long_rows = [r for r in rows if r["phase"] == bucket_label and r["direction"] == "LONG"]
        baseline = next((r for r in long_rows if r["slice"] == "baseline (all)"), None)
        low = next((r for r in long_rows if "low-stress" in r["slice"]), None)
        if baseline and baseline["n"] > 0 and low and low["n"] > 0:
            delta = (low["pos_rate"] - baseline["pos_rate"]) * 100
            verdict = "SUPPORTED" if delta > 0 else "NOT SUPPORTED"
            print(
                f"  {bucket_label:<20} {baseline['n']:>10} {baseline['pos_rate']:>11.1%} "
                f"{low['n']:>12} {low['pos_rate']:>12.1%} {delta:>+8.1f}pp  {verdict}"
            )
        elif baseline and baseline["n"] > 0:
            print(f"  {bucket_label:<20} {baseline['n']:>10} {baseline['pos_rate']:>11.1%}  {'n/a':>12} {'n/a':>12}      n/a  INSUFFICIENT")
        else:
            print(f"  {bucket_label:<20}        n/a          n/a           n/a           n/a      n/a  NO DATA")

    print()
    print("SHORT hypothesis: high-stress slice pos_rate > baseline")
    print(f"  {'phase':<20} {'baseline_n':>10} {'baseline_pr':>12} {'highstress_n':>12} {'highstress_pr':>14} {'delta_pp':>9} {'verdict'}")
    print("  " + "-" * 92)

    for bucket_label in ["ALL_PHASES"] + phases:
        rows = all_rows if bucket_label == "ALL_PHASES" else phase_rows
        short_rows = [r for r in rows if r["phase"] == bucket_label and r["direction"] == "SHORT"]
        baseline = next((r for r in short_rows if r["slice"] == "baseline (all)"), None)
        high = next((r for r in short_rows if "high-stress" in r["slice"]), None)
        if baseline and baseline["n"] > 0 and high and high["n"] > 0:
            delta = (high["pos_rate"] - baseline["pos_rate"]) * 100
            verdict = "SUPPORTED" if delta > 0 else "NOT SUPPORTED"
            print(
                f"  {bucket_label:<20} {baseline['n']:>10} {baseline['pos_rate']:>11.1%} "
                f"{high['n']:>12} {high['pos_rate']:>13.1%} {delta:>+8.1f}pp  {verdict}"
            )
        elif baseline and baseline["n"] > 0:
            print(f"  {bucket_label:<20} {baseline['n']:>10} {baseline['pos_rate']:>11.1%}  {'n/a':>12} {'n/a':>13}      n/a  INSUFFICIENT")
        else:
            print(f"  {bucket_label:<20}        n/a          n/a           n/a            n/a      n/a  NO DATA")

    # Phase distribution
    print()
    print("=" * 70)
    print("PHASE DISTRIBUTION")
    print("=" * 70)
    phase_dist = df.groupby("PhaseHeuristicLabel").agg(
        total=("SetupId", "count"),
        long=("Direction", lambda x: (x == "LONG").sum()),
        short=("Direction", lambda x: (x == "SHORT").sum()),
        runs=("_run", "nunique"),
    ).reset_index()
    print(f"\n  {'phase':<20} {'total':>6} {'long':>6} {'short':>6} {'runs':>6}")
    print("  " + "-" * 50)
    for _, row in phase_dist.iterrows():
        print(f"  {row['PhaseHeuristicLabel']:<20} {row['total']:>6} {row['long']:>6} {row['short']:>6} {row['runs']:>6}")

    print()
    print("=" * 70)
    print("SAMPLE SIZE WARNING")
    print("=" * 70)
    print("  All results: preliminary evidence only, NOT actionable signal.")
    print("  Phase stratification further reduces already-small sample sizes.")
    print("  Methodology: frozen from 2026-03_reclaim_context_asymmetry.md")
    print("  New dimension only: PhaseHeuristicLabel (no slice logic change).")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regime-stratified reclaim context asymmetry analysis"
    )
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        action="append",
        default=None,
        help="Additional run directories to scan (can repeat)",
    )
    args = parser.parse_args()

    run_dirs = _find_run_dirs(args.runs_dir)
    if not run_dirs:
        sys.exit("ERROR: No valid analyzer runs found")

    print(f"Found {len(run_dirs)} run(s) with complete artifacts\n")
    run_analysis(run_dirs)


if __name__ == "__main__":
    main()
