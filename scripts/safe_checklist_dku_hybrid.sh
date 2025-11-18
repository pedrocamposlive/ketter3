#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — SAFE CHECKLIST HYBRID v8
# ------------------------------------------------------------
# Checagens seguras:
# - Estrutura mínima do repositório
# - venv
# - PostgreSQL readiness
# - Redis ping
# - Alembic import
# - Backend import (app.main)
# ------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/dku/.venv"

LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"

LOG_FILE="${LOG_DIR}/checklist_safe_hybrid_$(date '+%Y%m%d_%H%M%S').log"

log() { echo "[SAFE-HYBRID] $1" | tee -a "$LOG_FILE"; }

log "Starting DKU hybrid checklist v8"

# ------------------------------------------------------------
# 1. Estrutura mínima (não rígida)
# ------------------------------------------------------------
log "Validating minimal folder structure."

MUST_EXIST=(
  "app"
  "scripts"
  "dku"
)

for dir in "${MUST_EXIST[@]}"; do
  if [[ ! -d "$REPO_ROOT/$dir" ]]; then
    log "ERROR: Missing required folder: $dir"
    exit 1
  fi
done

OPTIONAL_DIRS=("app/models" "app/schemas")
for od in "${OPTIONAL_DIRS[@]}"; do
  if [[ -d "$REPO_ROOT/$od" ]]; then
    log "Optional folder detected: $od"
  else
    log "Optional folder missing (ignored): $od"
  fi
done

# ------------------------------------------------------------
# 2. Virtualenv
# ------------------------------------------------------------
log "Checking virtual environment at: $VENV_PATH"

if [[ ! -d "$VENV_PATH" ]]; then
  log "ERROR: Virtualenv missing at $VENV_PATH"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"
log "Virtualenv activated."

# ------------------------------------------------------------
# 3. PostgreSQL readiness
# ------------------------------------------------------------
PG_ISREADY="/opt/homebrew/opt/postgresql@16/bin/pg_isready"

if [[ ! -x "$PG_ISREADY" ]]; then
  log "ERROR: pg_isready missing at $PG_ISREADY"
  exit 1
fi

log "Checking PostgreSQL readiness..."
if ! "$PG_ISREADY" -h 127.0.0.1 -p 5432 >> "$LOG_FILE" 2>&1; then
  log "ERROR: PostgreSQL not responding"
  exit 1
fi

log "PostgreSQL OK."

# ------------------------------------------------------------
# 4. Redis
# ------------------------------------------------------------
REDIS_CLI="/opt/homebrew/bin/redis-cli"

if [[ ! -x "$REDIS_CLI" ]]; then
  log "ERROR: redis-cli missing at $REDIS_CLI"
  exit 1
fi

log "Checking Redis ping..."
if ! "$REDIS_CLI" ping >> "$LOG_FILE" 2>&1; then
  log "ERROR: Redis did not respond"
  exit 1
fi

log "Redis OK."

# ------------------------------------------------------------
# 5. Alembic import
# ------------------------------------------------------------
log "Checking alembic import."

if ! python - << 'EOF'
import alembic
EOF
then
  log "ERROR: Alembic not importable"
  exit 1
fi
log "Alembic OK."

# ------------------------------------------------------------
# 6. Backend import
# ------------------------------------------------------------
log "Checking backend import: app.main"

if ! python - << 'EOF'
import app.main
EOF
then
  log "ERROR: Could not import app.main"
  exit 1
fi

log "Backend import OK."

# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------
log "SAFE CHECKLIST COMPLETED SUCCESSFULLY."
exit 0
