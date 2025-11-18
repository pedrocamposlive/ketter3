#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 02 — Dependencies
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BREW_PREFIX="/opt/homebrew"
PG_FORMULA="postgresql@16"
PG_DATA_DIR="${BREW_PREFIX}/var/${PG_FORMULA}"
REDIS_FORMULA="redis"
REDIS_DATA_DIR="${BREW_PREFIX}/var/redis"

log() { echo "[RB02] $1"; }

if command -v brew >/dev/null 2>&1; then
  log "Stopping PostgreSQL service."
  brew services stop "$PG_FORMULA" >/dev/null 2>&1 || true
  log "Stopping Redis service."
  brew services stop "$REDIS_FORMULA" >/dev/null 2>&1 || true
else
  log "Homebrew missing; skipping service shutdown."
fi

if [[ -d "$PG_DATA_DIR" ]]; then
  log "Removing PostgreSQL data directory."
  rm -rf "$PG_DATA_DIR"
else
  log "PostgreSQL data directory missing."
fi

if [[ -d "$REDIS_DATA_DIR" ]]; then
  log "Removing Redis data directory."
  rm -rf "$REDIS_DATA_DIR"
else
  log "Redis data directory missing."
fi

log "Dependency rollback completed."
