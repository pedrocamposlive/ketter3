#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 02 v6 — Dependencies Rollback
# PostgreSQL 16 + Redis — macOS ARM Edition
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

echo "[RB02] Starting rollback for dependency module."

PATH="/opt/homebrew/bin:/opt/homebrew/sbin:${PATH}"
export PATH

PG_VERSION="postgresql@16"
PG_PREFIX="/opt/homebrew/opt/${PG_VERSION}"
PG_DATA_DIR="/opt/homebrew/var/${PG_VERSION}"

log() { echo "[RB02] $1"; }

# ------------------------------------------------------------
# 1. Stop PostgreSQL safely
# ------------------------------------------------------------
log "Stopping PostgreSQL service."
if brew services list | grep -q "${PG_VERSION}"; then
  brew services stop "${PG_VERSION}" || true
else
  log "PostgreSQL service not registered."
fi

# ------------------------------------------------------------
# 2. Stop Redis safely
# ------------------------------------------------------------
log "Stopping Redis service."
if brew services list | grep -q "redis"; then
  brew services stop redis || true
else
  log "Redis service not registered."
fi

# ------------------------------------------------------------
# 3. Remove PostgreSQL data directory (if exists)
# ------------------------------------------------------------
if [[ -d "${PG_DATA_DIR}" ]]; then
  log "Removing PostgreSQL data directory at ${PG_DATA_DIR}."
  rm -rf "${PG_DATA_DIR}" || true
else
  log "PostgreSQL data directory missing — nothing to remove."
fi

# ------------------------------------------------------------
# 4. Remove stale Redis dump (optional safety)
# ------------------------------------------------------------
REDIS_DUMP="/opt/homebrew/var/db/redis"
if [[ -d "${REDIS_DUMP}" ]]; then
  log "Removing Redis data directory at ${REDIS_DUMP}."
  rm -rf "${REDIS_DUMP}" || true
else
  log "Redis data directory missing."
fi

# ------------------------------------------------------------
# 5. Kill any orphan processes (safety sweep)
# ------------------------------------------------------------
log "Killing orphan postgres processes (if any)."
pkill -f "postgres" 2>/dev/null || true

log "Killing orphan redis-server processes (if any)."
pkill -f "redis-server" 2>/dev/null || true

# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------
log "Rollback for Dependency Module completed successfully."

