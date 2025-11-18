#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 03b — Redis
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

BREW_PREFIX="/opt/homebrew"
REDIS_FORMULA="redis"
REDIS_DATA_DIR="${BREW_PREFIX}/var/redis"

log() { echo "[RB03b] $1"; }

if command -v brew >/dev/null 2>&1; then
  log "Stopping Redis service."
  brew services stop "$REDIS_FORMULA" >/dev/null 2>&1 || true
else
  log "Homebrew missing; skipping Redis service stop."
fi

if [[ -d "$REDIS_DATA_DIR" ]]; then
  log "Removing Redis data directory at $REDIS_DATA_DIR."
  rm -rf "$REDIS_DATA_DIR"
else
  log "Redis data directory missing."
fi

log "Redis rollback completed."
