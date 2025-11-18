#!/bin/bash
# ------------------------------------------------------------
# DKU Hybrid Safe Checklist v9 — baseado na estrutura REAL do projeto
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/checklist_hybrid_$(date '+%Y%m%d_%H%M%S').log"

log() { echo "[SAFE-HYBRID] $1" | tee -a "$LOG_FILE"; }

log "Starting DKU hybrid checklist v9"

# ------------------------------------------------------------
# 1. Validar estrutura do backend
# ------------------------------------------------------------
log "Validating backend folder structure..."

REQUIRED_FILES=(
  "app/main.py"
  "app/models.py"
  "app/schemas.py"
  "app/database.py"
)

REQUIRED_DIRS=(
  "app/core"
  "app/routers"
  "app/services"
  "app/security"
  "app/utils"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "${REPO_ROOT}/${f}" ]]; then
    log "ERROR: Required file missing: $f"
    exit 1
  fi
done

for d in "${REQUIRED_DIRS[@]}"; do
  if [[ ! -d "${REPO_ROOT}/${d}" ]]; then
    log "ERROR: Required directory missing: $d"
    exit 1
  fi
done

log "Backend file structure OK."

# ------------------------------------------------------------
# 2. Virtualenv
# ------------------------------------------------------------
VENV_PATH="${REPO_ROOT}/dku/.venv"

log "Checking virtualenv..."
if [[ ! -d "$VENV_PATH" ]]; then
  log "ERROR: venv missing at $VENV_PATH"
  exit 1
fi

source "$VENV_PATH/bin/activate"
log "Virtualenv activated."

# ------------------------------------------------------------
# 3. PostgreSQL readiness
# ------------------------------------------------------------
PG_ISREADY="/opt/homebrew/opt/postgresql@16/bin/pg_isready"

log "Checking PostgreSQL readiness..."
if ! "$PG_ISREADY" -h 127.0.0.1 -p 5432 >>"$LOG_FILE" 2>&1; then
  log "ERROR: PostgreSQL is not responding."
  exit 1
fi
log "PostgreSQL OK."

# ------------------------------------------------------------
# 4. Redis
# ------------------------------------------------------------
REDIS_CLI="/opt/homebrew/bin/redis-cli"

log "Checking Redis connectivity..."
if ! "$REDIS_CLI" ping >>"$LOG_FILE" 2>&1; then
  log "ERROR: Redis is not responding."
  exit 1
fi
log "Redis OK."

# ------------------------------------------------------------
# 5. Alembic
# ------------------------------------------------------------
log "Checking alembic import..."
if ! python - << 'EOF'
import alembic
EOF
then
  log "ERROR: alembic import failed."
  exit 1
fi
log "Alembic import OK."

# ------------------------------------------------------------
# 6. Backend import
# ------------------------------------------------------------
log "Checking backend import (app.main)..."

if ! python - << 'EOF'
import app.main
EOF
then
  log "ERROR: Failed to import app.main"
  exit 1
fi

log "Backend import OK."

# ------------------------------------------------------------
log "HYBRID CHECKLIST COMPLETED SUCCESSFULLY."
exit 0
