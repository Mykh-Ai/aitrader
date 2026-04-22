"""
Offline slice analysis: FAILED_BREAK_RECLAIM context hypothesis
================================================================

Гіпотеза:
- LONG winners → lower-stress reclaim context
- SHORT winners → higher-stress reclaim context

Джерела даних: analyzer_runs/*/analyzer_setups.csv + analyzer_setup_outcomes.csv
НЕ торкається production logic. Read-only analysis.

Запуск:
    # default: analyzer_runs/ поруч з repo root
    python research/slice_analysis_reclaim_context.py

    # вказати директорію явно (напр. на сервері)
    python research/slice_analysis_reclaim_context.py --runs-dir analyzer_runs

    # з фільтром по даті (включно з обома кінцями)
    python research/slice_analysis_reclaim_context.py --runs-dir analyzer_runs \\
        --date-from 2026-03-12 --date-to 2026-03-17

METHODOLOGY FREEZE — не змінювати slice logic між runs.
Зафіксована методологія: research/findings/2026-03_reclaim_context_asymmetry.md
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_RUNS_DIR = REPO_ROOT / "analyzer_runs"

CONTEXT_CONTINUOUS = [
    "AbsorptionScore_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
]
CONTEXT_BOOLEAN = [
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all_runs(
    runs_dir: pathlib.Path,
    date_from: str | None = None,
    date_to: str | None = None,
) -> pd.DataFrame:
    """Завантажує і об'єднує setups + outcomes з наявних analyzer runs.

    Args:
        runs_dir:   коренева директорія з run-піддиректоріями.
        date_from:  опціональний нижній фільтр по імені run (YYYY-MM-DD prefix, включно).
        date_to:    опціональний верхній фільтр по імені run (YYYY-MM-DD prefix, включно).
    """
    run_dirs = sorted(runs_dir.glob("*")) if runs_dir.exists() else []
    if date_from:
        run_dirs = [d for d in run_dirs if d.name >= date_from]
    if date_to:
        # run names start with YYYY-MM-DD, порівняння рядків достатньо
        run_dirs = [d for d in run_dirs if d.name[:10] <= date_to]
    if not run_dirs:
        sys.exit(f"ERROR: No analyzer runs found under {runs_dir} (date_from={date_from}, date_to={date_to})")

    frames = []
    for run_dir in run_dirs:
        setups_path = run_dir / "analyzer_setups.csv"
        outcomes_path = run_dir / "analyzer_setup_outcomes.csv"
        if not setups_path.exists() or not outcomes_path.exists():
            continue
        setups = pd.read_csv(setups_path)
        outcomes = pd.read_csv(outcomes_path)[
            ["SetupId", "MFE_Pct", "MAE_Pct", "CloseReturn_Pct", "OutcomeStatus"]
        ]
        merged = setups.merge(outcomes, on="SetupId", how="inner")
        merged["_run"] = run_dir.name
        frames.append(merged)

    if not frames:
        sys.exit("ERROR: No valid (setups + outcomes) pairs found")

    df = pd.concat(frames, ignore_index=True)

    # Дедуплікація: одна дата може мати кілька runs (re-runs того ж дня).
    # SetupId — детерміністичний, однакові SetupId = однаковий setup.
    # Залишаємо перший (найраніший run по алфавіту, бо sorted вище).
    before = len(df)
    df = df.drop_duplicates(subset="SetupId", keep="first").reset_index(drop=True)
    after = len(df)
    if before != after:
        print(f"Deduplicated: {before} → {after} setups (removed {before - after} duplicate SetupIds)")

    print(f"Loaded {after} unique setups from {len(frames)} run(s)")
    return df


# ---------------------------------------------------------------------------
# Slice helpers
# ---------------------------------------------------------------------------

def _stats(df: pd.DataFrame, label: str) -> dict:
    """Обчислює базову статистику для зрізу."""
    n = len(df)
    if n == 0:
        return {"label": label, "n": 0}
    ret = df["CloseReturn_Pct"]
    pos_rate = (ret > 0).mean()
    # груба expectancy proxy: mean(return_pct)
    return {
        "label": label,
        "n": n,
        "mean_ret": ret.mean(),
        "median_ret": ret.median(),
        "pos_rate": pos_rate,
        "mean_mfe": df["MFE_Pct"].mean(),
        "mean_mae": df["MAE_Pct"].mean(),
        "expectancy_proxy": ret.mean(),  # E[R] без нормування на R
    }


def _print_stats(s: dict) -> None:
    if s["n"] == 0:
        print(f"  {s['label']:<30}  n=0  (empty slice)")
        return
    print(
        f"  {s['label']:<30}  n={s['n']:>3}  "
        f"mean_ret={s['mean_ret']:+.3f}%  "
        f"median_ret={s['median_ret']:+.3f}%  "
        f"pos_rate={s['pos_rate']:.1%}  "
        f"MFE={s['mean_mfe']:.3f}%  "
        f"MAE={s['mean_mae']:.3f}%"
    )


# ---------------------------------------------------------------------------
# Slice definitions
# ---------------------------------------------------------------------------

def make_slices(df: pd.DataFrame, direction: str) -> list[tuple[str, pd.DataFrame]]:
    """
    Повертає список (label, dataframe) зрізів для вказаного напрямку.

    Методологія розбивки:
    - Median split в межах кожного напрямку окремо.
      Уникаємо cross-direction contamination при виборі порогів.
    - Для LOW-stress (LONG): AbsorptionScore_v1 <= median,
      RelVolume_20 <= median, LiqTotalRatio_20 <= median (всі 3 разом).
    - Для HIGH-stress (SHORT): AbsorptionScore_v1 >= median,
      RelVolume_20 >= median, DeltaAbsRatio_20 >= median (всі 3 разом).
    - Додатково: ctx_spike_count — кількість активних boolean ctx флагів.
    Вибір 3 з 5 continuous полів — мінімально достатній набір,
    що покриває гіпотезу без overfit на малій вибірці.
    """
    sub = df[df["Direction"] == direction].copy()
    slices = [("baseline (all)", sub)]

    if len(sub) == 0:
        return slices

    # Кількість активних boolean ctx флагів
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
        zero_spikes = sub[sub["_ctx_spike_count"] == 0]

        print(f"\n  [LONG medians used for split]")
        print(f"    AbsorptionScore_v1 median = {abs_med:.3f}")
        print(f"    RelVolume_20       median = {vol_med:.3f}")
        print(f"    LiqTotalRatio_20   median = {liq_med:.3f}")

        slices += [
            ("low-stress (all 3 <= median)", low_stress),
            ("high-stress (any 1 > median)", high_stress),
            ("zero ctx spikes", zero_spikes),
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
        has_spikes = sub[sub["_ctx_spike_count"] >= 2]

        print(f"\n  [SHORT medians used for split]")
        print(f"    AbsorptionScore_v1 median = {abs_med:.3f}")
        print(f"    RelVolume_20       median = {vol_med:.3f}")
        print(f"    DeltaAbsRatio_20   median = {delta_med:.3f}")

        slices += [
            ("high-stress (all 3 >= median)", high_stress),
            ("low-stress (any 1 < median)", low_stress),
            (">=2 ctx spikes active", has_spikes),
        ]

    return slices


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def run_analysis(
    runs_dir: pathlib.Path,
    date_from: str | None = None,
    date_to: str | None = None,
) -> None:
    print("=" * 70)
    print("OFFLINE SLICE ANALYSIS — FAILED_BREAK_RECLAIM CONTEXT HYPOTHESIS")
    print("=" * 70)
    print(f"runs_dir  : {runs_dir}")
    if date_from or date_to:
        print(f"date range: {date_from or '*'} → {date_to or '*'}")

    df = load_all_runs(runs_dir, date_from=date_from, date_to=date_to)

    total_long = (df["Direction"] == "LONG").sum()
    total_short = (df["Direction"] == "SHORT").sum()
    print(f"\nTotal setups: LONG={total_long}, SHORT={total_short}, ALL={len(df)}")

    separator = "-" * 70

    for direction in ["LONG", "SHORT"]:
        print(f"\n{separator}")
        print(f"DIRECTION: {direction}")
        print(separator)

        slices = make_slices(df, direction)
        print()
        for label, subset in slices:
            s = _stats(subset, label)
            _print_stats(s)

    # --- Context distribution compare
    print(f"\n{separator}")
    print("CONTEXT FIELD MEANS — LONG vs SHORT (full population)")
    print(separator)
    cols = CONTEXT_CONTINUOUS + ["_ctx_spike_count_proxy"]
    long_sub = df[df["Direction"] == "LONG"].copy()
    short_sub = df[df["Direction"] == "SHORT"].copy()
    long_sub["_ctx_spike_count_proxy"] = long_sub[CONTEXT_BOOLEAN].sum(axis=1)
    short_sub["_ctx_spike_count_proxy"] = short_sub[CONTEXT_BOOLEAN].sum(axis=1)

    print(f"\n  {'Field':<28}  {'LONG mean':>12}  {'SHORT mean':>12}  {'direction':>12}")
    all_cols = CONTEXT_CONTINUOUS + ["_ctx_spike_count_proxy"]
    for col in all_cols:
        lm = long_sub[col].mean() if col in long_sub else float("nan")
        sm = short_sub[col].mean() if col in short_sub else float("nan")
        direction_hint = "L>S" if lm > sm else ("S>L" if sm > lm else "equal")
        print(f"  {col:<28}  {lm:>12.4f}  {sm:>12.4f}  {direction_hint:>12}")

    # --- Winners in slices
    print(f"\n{separator}")
    print("WINNER RATE IN HYPOTHESIS SLICES (CloseReturn_Pct > 0)")
    print(separator)
    print()
    print("  LONG hypothesis: low-stress slice should have HIGHER win rate than baseline")
    _compare_hypothesis(df, "LONG", "low")
    print()
    print("  SHORT hypothesis: high-stress slice should have HIGHER win rate than baseline")
    _compare_hypothesis(df, "SHORT", "high")

    print(f"\n{separator}")
    print("SAMPLE SIZE WARNING")
    print(separator)
    print(f"  LONG n={total_long} — дуже мала вибірка, висновки попередні")
    print(f"  SHORT n={total_short} — більша вибірка, але все одно обмежена")
    print(f"  Всі результати: preliminary evidence only, NOT actionable signal")
    print()


def _compare_hypothesis(df: pd.DataFrame, direction: str, stress_type: str) -> None:
    sub = df[df["Direction"] == direction].copy()
    if len(sub) == 0:
        print(f"  No data for {direction}")
        return

    sub["_ctx_spike_count"] = sub[CONTEXT_BOOLEAN].sum(axis=1)
    baseline_pos = (sub["CloseReturn_Pct"] > 0).mean()
    baseline_mean = sub["CloseReturn_Pct"].mean()

    if direction == "LONG":
        abs_med = sub["AbsorptionScore_v1"].median()
        vol_med = sub["RelVolume_20"].median()
        liq_med = sub["LiqTotalRatio_20"].median()
        slice_df = sub[
            (sub["AbsorptionScore_v1"] <= abs_med)
            & (sub["RelVolume_20"] <= vol_med)
            & (sub["LiqTotalRatio_20"] <= liq_med)
        ]
    else:
        abs_med = sub["AbsorptionScore_v1"].median()
        vol_med = sub["RelVolume_20"].median()
        delta_med = sub["DeltaAbsRatio_20"].median()
        slice_df = sub[
            (sub["AbsorptionScore_v1"] >= abs_med)
            & (sub["RelVolume_20"] >= vol_med)
            & (sub["DeltaAbsRatio_20"] >= delta_med)
        ]

    slice_pos = (slice_df["CloseReturn_Pct"] > 0).mean() if len(slice_df) else float("nan")
    slice_mean = slice_df["CloseReturn_Pct"].mean() if len(slice_df) else float("nan")

    supported = (slice_pos > baseline_pos) if not pd.isna(slice_pos) else False

    print(f"    baseline   n={len(sub):>3}  pos_rate={baseline_pos:.1%}  mean_ret={baseline_mean:+.3f}%")
    print(f"    hyp_slice  n={len(slice_df):>3}  pos_rate={slice_pos:.1%}  mean_ret={slice_mean:+.3f}%  "
          f"-> {'SUPPORTED' if supported else 'NOT SUPPORTED'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Offline slice analysis: FAILED_BREAK_RECLAIM context hypothesis"
    )
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        default=_DEFAULT_RUNS_DIR,
        help=f"Root directory containing analyzer run subdirectories (default: {_DEFAULT_RUNS_DIR})",
    )
    parser.add_argument(
        "--date-from",
        default=None,
        metavar="YYYY-MM-DD",
        help="Include only runs on or after this date (matched against run directory name prefix)",
    )
    parser.add_argument(
        "--date-to",
        default=None,
        metavar="YYYY-MM-DD",
        help="Include only runs on or before this date (matched against run directory name prefix)",
    )
    args = parser.parse_args()
    run_analysis(runs_dir=args.runs_dir, date_from=args.date_from, date_to=args.date_to)
