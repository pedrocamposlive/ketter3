#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 03 v7 — Python Environment Cleanup
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/dku/.venv"
REQUIREMENTS_CACHE="${REPO_ROOT}/dku/requirements_cache"
LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"

log() { echo "[RB03] $1"; }

log "Starting rollback for Python environment (Module 03)."

# ------------------------------------------------------------
# 1. Remove virtual environment
# ------------------------------------------------------------
if [[ -d "$VENV_PATH" ]]; then
  log "Removing virtual environment at $VENV_PATH."
  rm -rf "$VENV_PATH"
else
  log "No virtualenv found — skipping removal."
fi

# ------------------------------------------------------------
# 2. Remove temporary build caches
# ------------------------------------------------------------
log "Cleaning Python build/temp caches."

find "$REPO_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true

# ------------------------------------------------------------
# 3. Optional: clear requirements cached temp folder
# ------------------------------------------------------------
if [[ -d "$REQUIREMENTS_CACHE" ]]; then
  log "Removing requirements cache at $REQUIREMENTS_CACHE."
  rm -rf "$REQUIREMENTS_CACHE"
fi

# ------------------------------------------------------------
# 4. Cleanup any partial alembic installs
# ------------------------------------------------------------
log "Cleaning Alembic temp artifacts."

find "$REPO_ROOT" -type f -name "alembic.ini.tmp" -delete 2>/dev/null || true

# ------------------------------------------------------------
# 5. Finalization
# ------------------------------------------------------------
log "Python environment rollback completed successfully."
