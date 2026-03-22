#!/usr/bin/env python3
"""
research_cycle.py — автоматизований backtester pipeline для routine research.

Сканує analyzer_runs/, знаходить unprocessed runs, прогоняє backtester,
записує _processed.json маркери, запускає slice analysis.
Виводить структурований JSON на stdout — готовий для агента/handoff.

Використання:
    python3 research_cycle.py
    python3 research_cycle.py --runs-dir /opt/aitrader/analyzer_runs
    python3 research_cycle.py --dry-run   # тільки probe, без replay
"""

import argparse
import json
import subprocess
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Заморожені параметри backtester — НЕ МІНЯТИ
# ---------------------------------------------------------------------------
BACKTESTER_PARAMS = dict(
    ruleset_source_formalization_mode="SHORTLIST_FIRST",
    variant_names=("BASE",),
    cost_model_id="COST_MODEL_ZERO_SKELETON_ONLY",
    same_bar_policy_id="SAME_BAR_CONSERVATIVE_V0_1",
    replay_semantics_version="REPLAY_V0_1",
)

# ---------------------------------------------------------------------------
# Шляхи за замовчуванням (сервер)
# ---------------------------------------------------------------------------
DEFAULT_RUNS_DIR = "/opt/aitrader/analyzer_runs"
DEFAULT_BACKTEST_DIR = "/opt/aitrader/backtest_runs"
SLICE_SCRIPT = "research/slice_analysis_reclaim_context.py"

TODAY = str(date.today())
TODAY_COMPACT = date.today().strftime("%Y%m%d")


# ===================================================================
# 1. Знайти unprocessed runs
# ===================================================================

def find_unprocessed(runs_dir: Path) -> list[Path]:
    """Повертає відсортований список run dirs без _processed.json."""
    unprocessed = []
    if not runs_dir.exists():
        return unprocessed
    for d in sorted(runs_dir.iterdir()):
        if d.is_dir() and not (d / "_processed.json").exists():
            unprocessed.append(d)
    return unprocessed


# ===================================================================
# 2. Probe — зчитати артефакти, порахувати метрики
# ===================================================================

def probe_run(run_dir: Path) -> dict:
    """Читає analyzer артефакти, повертає probe summary."""
    run_id = run_dir.name
    result = {
        "run_id": run_id,
        "setups": 0,
        "shortlist_rows": 0,
        "formalization_eligible": 0,
        "missing_artifacts": [],
    }

    # Setups
    setups_path = run_dir / "analyzer_setups.csv"
    if setups_path.exists():
        try:
            df = pd.read_csv(setups_path)
            result["setups"] = len(df)
        except Exception as e:
            result["missing_artifacts"].append(f"analyzer_setups.csv: read error ({e})")
    else:
        result["missing_artifacts"].append("analyzer_setups.csv")

    # Shortlist
    shortlist_path = run_dir / "analyzer_setup_shortlist.csv"
    if shortlist_path.exists():
        try:
            df = pd.read_csv(shortlist_path)
            result["shortlist_rows"] = len(df)
        except Exception as e:
            result["missing_artifacts"].append(f"analyzer_setup_shortlist.csv: read error ({e})")
    else:
        result["missing_artifacts"].append("analyzer_setup_shortlist.csv")

    # Research summary + FormalizationEligible
    rs_path = run_dir / "analyzer_research_summary.csv"
    if rs_path.exists():
        try:
            df = pd.read_csv(rs_path)
            if "FormalizationEligible" in df.columns:
                result["formalization_eligible"] = int(df["FormalizationEligible"].sum())
        except Exception as e:
            result["missing_artifacts"].append(f"analyzer_research_summary.csv: read error ({e})")
    else:
        result["missing_artifacts"].append("analyzer_research_summary.csv")

    return result


# ===================================================================
# 3. Replay — запустити backtester
# ===================================================================

def replay_run(run_dir: Path, backtest_dir: Path) -> dict:
    """Запускає backtester, повертає результат."""
    run_id = run_dir.name
    output_dir = backtest_dir / f"{run_id}_routine_{TODAY_COMPACT}"

    try:
        from backtester.orchestrator import run_backtester

        run_backtester(
            artifact_dir=str(run_dir),
            output_dir=str(output_dir),
            **BACKTESTER_PARAMS,
        )
        return {
            "status": "OK",
            "output_dir": str(output_dir),
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "output_dir": str(output_dir),
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# ===================================================================
# 4. Читати promotion decisions
# ===================================================================

def read_promotions(output_dir: Path) -> list[dict]:
    """Читає promotion decisions з backtest output (включно з fan-out)."""
    results = []
    out = Path(output_dir)

    # Fan-out (derived_run_*)
    derived = sorted(out.glob("derived_run_*"))
    if derived:
        for child in derived:
            dec_file = child / "backtest_promotion_decisions.csv"
            if dec_file.exists():
                try:
                    df = pd.read_csv(dec_file)
                    for _, row in df.iterrows():
                        results.append({
                            "derived_run": child.name,
                            "scope": str(row.get("scope", "")),
                            "promotion_decision": str(row.get("promotion_decision", "")),
                            "validation_status": str(row.get("validation_status", "")),
                            "robustness_status": str(row.get("robustness_status", "")),
                        })
                except Exception:
                    results.append({"derived_run": child.name, "error": "read failed"})
    else:
        # Single ruleset
        dec_file = out / "backtest_promotion_decisions.csv"
        if dec_file.exists():
            try:
                df = pd.read_csv(dec_file)
                for _, row in df.iterrows():
                    results.append({
                        "derived_run": "single",
                        "scope": str(row.get("scope", "")),
                        "promotion_decision": str(row.get("promotion_decision", "")),
                        "validation_status": str(row.get("validation_status", "")),
                        "robustness_status": str(row.get("robustness_status", "")),
                    })
            except Exception:
                results.append({"derived_run": "single", "error": "read failed"})

    return results


def classify_outcome(promotions: list[dict]) -> str:
    """Визначає outcome state за promotion decisions."""
    decisions = [p.get("promotion_decision", "") for p in promotions if "error" not in p]
    if not decisions:
        return "BACKTESTED_REJECT"
    if any(d == "PROMOTE" for d in decisions):
        return "BACKTESTED_PROMOTE"
    if any(d == "REVIEW" for d in decisions):
        return "BACKTESTED_REVIEW"
    return "BACKTESTED_REJECT"


# ===================================================================
# 5. Записати _processed.json маркер
# ===================================================================

def write_marker(run_dir: Path, routine_status: str, backtest_output: str,
                 promotion_outcome: str, notes: str) -> None:
    """Записує _processed.json маркер в run directory."""
    marker = {
        "processed_at": TODAY,
        "routine_status": routine_status,
        "backtest_output": backtest_output,
        "promotion_outcome": promotion_outcome,
        "notes": notes,
    }
    (run_dir / "_processed.json").write_text(json.dumps(marker, indent=2))


# ===================================================================
# 6. Slice analysis
# ===================================================================

def run_slice_analysis(runs_dir: Path) -> str:
    """Запускає slice analysis, повертає stdout."""
    script = Path(__file__).parent / SLICE_SCRIPT
    if not script.exists():
        return f"ERROR: slice script not found at {script}"

    try:
        result = subprocess.run(
            [sys.executable, str(script), "--runs-dir", str(runs_dir)],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "ERROR: slice analysis timeout (120s)"
    except Exception as e:
        return f"ERROR: {e}"


# ===================================================================
# 7. Діагностика якості даних
# ===================================================================

def run_diagnostics(runs_dir: Path, feed_dir: Path | None) -> dict:
    """Перевіряє повноту та якість даних."""
    diag: dict = {}

    # --- Feed coverage ---
    if feed_dir and feed_dir.exists():
        feed_files = sorted(feed_dir.glob("*.csv"))
        feed_dates = []
        for f in feed_files:
            name = f.stem
            # Очікуємо YYYY-MM-DD
            if len(name) == 10 and name[4] == "-" and name[7] == "-":
                feed_dates.append(name)
        if feed_dates:
            # Знайти пропущені дні
            from datetime import timedelta
            first = datetime.strptime(feed_dates[0], "%Y-%m-%d").date()
            last = datetime.strptime(feed_dates[-1], "%Y-%m-%d").date()
            all_days = set()
            d = first
            while d <= last:
                all_days.add(d.strftime("%Y-%m-%d"))
                d += timedelta(days=1)
            missing = sorted(all_days - set(feed_dates))
            diag["feed_coverage"] = {
                "first": feed_dates[0],
                "last": feed_dates[-1],
                "total_files": len(feed_dates),
                "missing_days": missing,
            }

    # --- Analyzer runs coverage ---
    all_runs = sorted([d.name for d in runs_dir.iterdir() if d.is_dir()])
    processed = [d for d in runs_dir.iterdir()
                 if d.is_dir() and (d / "_processed.json").exists()]
    diag["analyzer_coverage"] = {
        "runs_total": len(all_runs),
        "runs_processed": len(processed),
        "runs_unprocessed": len(all_runs) - len(processed),
    }

    # --- Артефакти в unprocessed runs ---
    anomalies = []
    for d in runs_dir.iterdir():
        if not d.is_dir():
            continue
        if (d / "_processed.json").exists():
            continue
        expected = ["analyzer_setups.csv", "analyzer_setup_shortlist.csv",
                     "analyzer_research_summary.csv"]
        for f in expected:
            fp = d / f
            if not fp.exists():
                anomalies.append(f"{d.name}: {f} MISSING")
            elif fp.stat().st_size == 0:
                anomalies.append(f"{d.name}: {f} EMPTY (0 bytes)")
    diag["unprocessed_anomalies"] = anomalies

    # --- Патерни в даних ---
    flags = []
    # Перевіряємо consecutive FE=0
    consecutive_zero = 0
    max_consecutive_zero = 0
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        rs_path = d / "analyzer_research_summary.csv"
        if rs_path.exists():
            try:
                df = pd.read_csv(rs_path)
                fe = int(df["FormalizationEligible"].sum()) if "FormalizationEligible" in df.columns else 0
                if fe == 0:
                    consecutive_zero += 1
                    max_consecutive_zero = max(max_consecutive_zero, consecutive_zero)
                else:
                    consecutive_zero = 0
            except Exception:
                pass
    if max_consecutive_zero >= 3:
        flags.append(f"{max_consecutive_zero} consecutive runs with FormalizationEligible=0")

    diag["data_quality_flags"] = flags

    return diag


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="Research cycle: probe → replay → record")
    parser.add_argument("--runs-dir", default=DEFAULT_RUNS_DIR,
                        help="Шлях до analyzer_runs/")
    parser.add_argument("--backtest-dir", default=DEFAULT_BACKTEST_DIR,
                        help="Шлях до backtest_runs/")
    parser.add_argument("--feed-dir", default=None,
                        help="Шлях до feed/ (для діагностики)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Тільки probe + діагностика, без replay")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    backtest_dir = Path(args.backtest_dir)
    feed_dir = Path(args.feed_dir) if args.feed_dir else (runs_dir.parent / "feed")

    output = {
        "cycle_date": TODAY,
        "dry_run": args.dry_run,
        "runs_dir": str(runs_dir),
        "results": [],
        "slice_output": "",
        "diagnostics": {},
    }

    # --- Крок 1: знайти unprocessed ---
    unprocessed = find_unprocessed(runs_dir)
    output["runs_found"] = len(unprocessed)
    output["runs_ids"] = [d.name for d in unprocessed]

    if not unprocessed:
        # Навіть якщо нових runs немає — діагностика корисна
        output["diagnostics"] = run_diagnostics(runs_dir, feed_dir)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # --- Крок 2: probe + decide + replay + record ---
    for run_dir in unprocessed:
        run_id = run_dir.name
        probe = probe_run(run_dir)
        fe = probe["formalization_eligible"]

        run_result = {
            "run_id": run_id,
            "probe": probe,
            "replay_status": None,
            "promotion_details": [],
            "promotion_outcome": None,
            "routine_status": None,
        }

        if fe == 0:
            # NO_REPLAYABLE_RULESETS
            run_result["replay_status"] = "SKIPPED"
            run_result["promotion_outcome"] = "N/A"
            run_result["routine_status"] = "NO_REPLAYABLE_RULESETS"

            if not args.dry_run:
                write_marker(
                    run_dir,
                    routine_status="NO_REPLAYABLE_RULESETS",
                    backtest_output="N/A",
                    promotion_outcome="N/A",
                    notes=f"routine cycle {TODAY}; FE=0",
                )
        else:
            # Replay
            if args.dry_run:
                run_result["replay_status"] = "DRY_RUN_SKIPPED"
                run_result["routine_status"] = "DRY_RUN"
            else:
                replay = replay_run(run_dir, backtest_dir)
                run_result["replay_status"] = replay["status"]

                if replay["status"] == "OK":
                    promotions = read_promotions(Path(replay["output_dir"]))
                    outcome = classify_outcome(promotions)

                    run_result["promotion_details"] = promotions
                    run_result["promotion_outcome"] = outcome.replace("BACKTESTED_", "")
                    run_result["routine_status"] = outcome

                    write_marker(
                        run_dir,
                        routine_status=outcome,
                        backtest_output=replay["output_dir"],
                        promotion_outcome=run_result["promotion_outcome"],
                        notes=f"routine cycle {TODAY}; FE={fe}",
                    )
                else:
                    run_result["promotion_outcome"] = "N/A"
                    run_result["routine_status"] = "REPLAY_FAILED"
                    run_result["replay_error"] = replay.get("error", "unknown")

                    write_marker(
                        run_dir,
                        routine_status="REPLAY_FAILED",
                        backtest_output=replay.get("output_dir", "N/A"),
                        promotion_outcome="N/A",
                        notes=f"routine cycle {TODAY}; FAILED: {replay.get('error', '')}",
                    )

        output["results"].append(run_result)

    # --- Крок 3: slice analysis ---
    output["slice_output"] = run_slice_analysis(runs_dir)

    # --- Крок 4: діагностика ---
    output["diagnostics"] = run_diagnostics(runs_dir, feed_dir)

    # --- Вивід ---
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
