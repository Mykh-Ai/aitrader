#!/usr/bin/env bash
# Збір даних з VPS для transition analysis
# Запускати з локальної машини: bash research/scripts/collect_transition_data.sh

set -euo pipefail

VPS="95.216.139.172"
REMOTE_BASE="/opt/aitrader/analyzer_runs"
LOCAL_OUT="research/findings/transition_vps_data"

RUNS=(
  "2026-03-15_to_2026-03-15_run_001"
  "2026-03-16_to_2026-03-16_run_001"
  "2026-03-17_to_2026-03-17_run_001"
  "2026-03-18_to_2026-03-18_run_001"
  "2026-03-19_to_2026-03-19_run_001"
  "2026-03-20_to_2026-03-20_run_001"
  "2026-03-21_to_2026-03-21_run_001"
  "2026-03-22_to_2026-03-22_run_001"
  "2026-03-23_to_2026-03-23_run_001"
)

FILES=(
  "analyzer_setups.csv"
  "analyzer_setup_rankings.csv"
  "analyzer_setup_selections.csv"
  "analyzer_setup_shortlist.csv"
  "analyzer_research_summary.csv"
)

mkdir -p "$LOCAL_OUT"

# 1. Перевірити які runs існують на VPS
echo "=== Checking run directories on VPS ==="
ssh "$VPS" "for d in ${RUNS[*]}; do echo \"\$d: \$(ls ${REMOTE_BASE}/\$d/ 2>/dev/null | wc -l) files\"; done"

# 2. Скопіювати потрібні CSV
echo ""
echo "=== Downloading CSV artifacts ==="
for run in "${RUNS[@]}"; do
  run_dir="${LOCAL_OUT}/${run}"
  mkdir -p "$run_dir"
  for f in "${FILES[@]}"; do
    remote_path="${REMOTE_BASE}/${run}/${f}"
    if scp -q "$VPS:$remote_path" "$run_dir/$f" 2>/dev/null; then
      echo "  OK: ${run}/${f}"
    else
      echo "  MISSING: ${run}/${f}"
    fi
  done
done

# 3. Quick summary: setup counts per run
echo ""
echo "=== Setup counts per run ==="
for run in "${RUNS[@]}"; do
  f="${LOCAL_OUT}/${run}/analyzer_setups.csv"
  if [ -f "$f" ]; then
    total=$(($(wc -l < "$f") - 1))
    long=$(awk -F',' 'NR>1 && $3=="LONG"' "$f" | wc -l)
    short=$(awk -F',' 'NR>1 && $3=="SHORT"' "$f" | wc -l)
    echo "  ${run}: total=${total} LONG=${long} SHORT=${short}"
  else
    echo "  ${run}: NO DATA"
  fi
done

echo ""
echo "Done. Data saved to ${LOCAL_OUT}/"
