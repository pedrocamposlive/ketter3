#!/bin/bash
# ------------------------------------------------------------
# DKU Module 04 — Post-Install Validation (macOS Apple Silicon)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/.venv"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"
CHECKLIST_SCRIPT="${REPO_ROOT}/scripts/safe_checklist_dku.sh"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT_FILE="${REPORT_DIR}/post_install_validation_${TIMESTAMP}.txt"

PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
PG_ISREADY="${PG_BIN}/pg_isready"
PSQL="${PG_BIN}/psql"
REDIS_CLI="/opt/homebrew/bin/redis-cli"

mkdir -p "$REPORT_DIR"

log() {
  echo "[DKU-04] $1" | tee -a "$REPORT_FILE"
}

log "Starting post-install validation."

if [[ ! -d "$VENV_PATH" ]]; then
  echo "[ERROR] Virtualenv missing at $VENV_PATH" | tee -a "$REPORT_FILE"
  exit 1
fi

source "$VENV_PATH/bin/activate"
log "Virtualenv activated."

if [[ ! -x "$PG_ISREADY" ]]; then
  echo "[ERROR] pg_isready not found at $PG_ISREADY" | tee -a "$REPORT_FILE"
  exit 1
fi

log "Verifying PostgreSQL responsiveness."
if ! "$PG_ISREADY" -h 127.0.0.1 -p 5432 >> "$REPORT_FILE" 2>&1; then
  echo "[ERROR] PostgreSQL readiness probe failed." | tee -a "$REPORT_FILE"
  exit 1
fi
log "PostgreSQL is responsive."

log "Validating PostgreSQL roles and database."
if ! PGPASSWORD="ketter_user_pass" "$PSQL" -h 127.0.0.1 -U ketter_user -d ketter -c '\dt' >> "$REPORT_FILE" 2>&1; then
  echo "[ERROR] Cannot list tables from ketter database." | tee -a "$REPORT_FILE"
  exit 1
fi
log "Database access OK."

if [[ ! -x "$REDIS_CLI" ]]; then
  echo "[ERROR] redis-cli not found at $REDIS_CLI" | tee -a "$REPORT_FILE"
  exit 1
fi

log "Pinging Redis service."
if ! "$REDIS_CLI" -h 127.0.0.1 -p 6379 ping >> "$REPORT_FILE" 2>&1; then
  echo "[ERROR] Redis ping failed." | tee -a "$REPORT_FILE"
  exit 1
fi
log "Redis responded to ping."

if [[ ! -x "$CHECKLIST_SCRIPT" ]]; then
  echo "[ERROR] Checklist script missing or not executable: $CHECKLIST_SCRIPT" | tee -a "$REPORT_FILE"
  exit 1
fi

log "Running DKU-safe checklist."
bash "$CHECKLIST_SCRIPT" >> "$REPORT_FILE" 2>&1
log "Checklist completed."

log "Post-install validation finished successfully."
