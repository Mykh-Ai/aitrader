#!/usr/bin/env bash
# Щоденний cron-wrapper для Analyzer pipeline.
# Обробляє вчорашній (UTC) завершений feed CSV.
#
# Cron:  5 0 * * * /opt/aitrader/scripts/run_analyzer_daily.sh >> /opt/aitrader/logs/analyzer_daily.log 2>&1
#
# Потребує: Python venv з pandas у /opt/aitrader/.venv
# Не змінює aggregator, не запускає backtester.

set -euo pipefail

# --- Конфігурація (абсолютні шляхи) ---
PROJECT_DIR="/opt/aitrader"
FEED_DIR="${PROJECT_DIR}/feed"
RUNS_DIR="${PROJECT_DIR}/analyzer_runs"
VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"

# Канонічний header з analyzer/schema.py REQUIRED_RAW_COLUMNS
EXPECTED_HEADER="Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic"

# --- Обчислення дат (UTC) ---
TODAY_UTC=$(date -u +%Y-%m-%d)
YESTERDAY_UTC=$(date -u -d "yesterday" +%Y-%m-%d)

YESTERDAY_FILE="${FEED_DIR}/${YESTERDAY_UTC}.csv"
TODAY_FILE="${FEED_DIR}/${TODAY_UTC}.csv"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

die() {
    log "FAIL: $*"
    exit 1
}

# --- Guardrails ---

log "Analyzer daily run: input=${YESTERDAY_UTC}"

# 1. Вчорашній файл існує
[ -f "${YESTERDAY_FILE}" ] || die "Yesterday file missing: ${YESTERDAY_FILE}"

# 2. Сьогоднішній файл існує (aggregator вже пише новий день)
[ -f "${TODAY_FILE}" ] || die "Today file missing: ${TODAY_FILE} — aggregator may not have rotated yet"

# 3. Вчорашній файл не порожній
[ -s "${YESTERDAY_FILE}" ] || die "Yesterday file is empty: ${YESTERDAY_FILE}"

# 4. Перевірка header
ACTUAL_HEADER=$(head -1 "${YESTERDAY_FILE}" | tr -d '\r')
if [ "${ACTUAL_HEADER}" != "${EXPECTED_HEADER}" ]; then
    die "Header mismatch in ${YESTERDAY_FILE}. Expected: ${EXPECTED_HEADER}. Got: ${ACTUAL_HEADER}"
fi

# 5. Python venv існує
[ -x "${VENV_PYTHON}" ] || die "Python venv not found: ${VENV_PYTHON}"

# --- Запуск Analyzer ---

log "Launching: ${VENV_PYTHON} -m analyzer.run_daily ${YESTERDAY_FILE} --runs-root ${RUNS_DIR}"

cd "${PROJECT_DIR}"
"${VENV_PYTHON}" -m analyzer.run_daily "${YESTERDAY_FILE}" --runs-root "${RUNS_DIR}"
EXIT_CODE=$?

if [ ${EXIT_CODE} -eq 0 ]; then
    log "SUCCESS: Analyzer daily run completed for ${YESTERDAY_UTC}"
else
    die "Analyzer exited with code ${EXIT_CODE}"
fi
