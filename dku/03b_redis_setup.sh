#!/bin/bash
# ------------------------------------------------------------
# DKU Module 03b — Redis Setup (macOS Apple Silicon)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

BREW_PREFIX="/opt/homebrew"
REDIS_FORMULA="redis"
REDIS_DATA_DIR="${BREW_PREFIX}/var/redis"
REDIS_CLI="${BREW_PREFIX}/bin/redis-cli"

log() { echo "[DKU-03b] $1"; }

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: $cmd" >&2
    exit 1
  fi
}

log "Ensuring Redis is installed."
require_command brew
brew list --versions "$REDIS_FORMULA" >/dev/null 2>&1 || brew install "$REDIS_FORMULA"

if [[ ! -x "$REDIS_CLI" ]]; then
  echo "[ERROR] redis-cli not found at ${REDIS_CLI}." >&2
  exit 1
fi

log "Stopping Redis service and resetting data directory."
brew services stop "$REDIS_FORMULA" >/dev/null 2>&1 || true
rm -rf "$REDIS_DATA_DIR"
mkdir -p "$REDIS_DATA_DIR"

log "Starting Redis service."
brew services start "$REDIS_FORMULA" >/dev/null 2>&1

log "Waiting for Redis to respond to ping."
attempts=20
until "$REDIS_CLI" -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; do
  if (( attempts == 0 )); then
    echo "[ERROR] Redis did not respond to ping." >&2
    exit 1
  fi
  attempts=$((attempts - 1))
  sleep 1
done

log "Redis setup completed successfully."
