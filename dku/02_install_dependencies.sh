#!/bin/bash
# ------------------------------------------------------------
# DKU Module 02 v6 — Install Core Dependencies (macOS ARM)
# PostgreSQL 16 + Redis with deterministic initialization
# Locale-safe version (fixes initdb invalid locale)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

echo "[DKU-02] Starting dependency installation."

REPO_ROOT="$(pwd)"
PATH="/opt/homebrew/bin:/opt/homebrew/sbin:${PATH}"
export PATH

# Force safe locale for macOS (fix initdb bug)
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"

PG_VERSION="postgresql@16"
PG_PREFIX="/opt/homebrew/opt/${PG_VERSION}"
PG_BIN="${PG_PREFIX}/bin"
PG_DATA_DIR="/opt/homebrew/var/${PG_VERSION}"
PG_CTL="${PG_BIN}/pg_ctl"
CREATEUSER="${PG_BIN}/createuser"
CREATEDB="${PG_BIN}/createdb"
INITDB="${PG_BIN}/initdb"

log() { echo "[DKU-02] $1"; }

# ------------------------------------------------------------
# 1. PostgreSQL Installation
# ------------------------------------------------------------
log "Checking PostgreSQL installation."

if ! brew list --versions "${PG_VERSION}" >/dev/null 2>&1; then
  log "PostgreSQL 16 not found — installing..."
  brew install "${PG_VERSION}"
else
  log "PostgreSQL 16 already installed."
fi

# ------------------------------------------------------------
# 2. Initialize PostgreSQL with forced locale and user
# ------------------------------------------------------------
log "Ensuring PostgreSQL data directory."

if [[ -d "${PG_DATA_DIR}" ]]; then
  log "Existing PostgreSQL data directory detected — removing for clean init."
  brew services stop "${PG_VERSION}" || true
  rm -rf "${PG_DATA_DIR}"
fi

log "Initializing PostgreSQL cluster with enforced UTF-8 locale."
log "Using LANG=$LANG LC_ALL=$LC_ALL LC_CTYPE=$LC_CTYPE"

"${INITDB}" \
  --locale=en_US.UTF-8 \
  -E UTF8 \
  -U postgres \
  -A trust \
  "${PG_DATA_DIR}"

log "PostgreSQL initdb completed successfully."

# ------------------------------------------------------------
# 3. Start PostgreSQL and wait for readiness
# ------------------------------------------------------------
log "Starting PostgreSQL service."
brew services start "${PG_VERSION}" || true

log "Waiting for PostgreSQL readiness..."
for i in {1..20}; do
  if "${PG_BIN}/pg_isready" >/dev/null 2>&1; then
    log "PostgreSQL is ready."
    break
  fi
  sleep 1
done

if ! "${PG_BIN}/pg_isready" >/dev/null 2>&1; then
  echo "[ERROR] PostgreSQL did not become ready." >&2
  exit 1
fi

# ------------------------------------------------------------
# 4. Create roles and database
# ------------------------------------------------------------
log "Ensuring application roles and database."

"${CREATEUSER}" -s postgres 2>/dev/null || true
"${CREATEUSER}" -s ketter_admin 2>/dev/null || true
"${CREATEUSER}" ketter_user 2>/dev/null || true

"${CREATEDB}" -O ketter_admin ketter 2>/dev/null || true

log "Roles and database created successfully."

# ------------------------------------------------------------
# 5. Install Redis
# ------------------------------------------------------------
log "Checking Redis installation."

if ! brew list --versions redis >/dev/null 2>&1; then
  log "Redis not installed — installing..."
  brew install redis
else
  log "Redis already installed."
fi

log "Starting Redis service."
brew services start redis || true
sleep 2

# ------------------------------------------------------------
# 6. Validate Redis
# ------------------------------------------------------------
log "Checking Redis connectivity."

if ! /opt/homebrew/bin/redis-cli ping >/dev/null 2>&1; then
  echo "[ERROR] Redis did not respond." >&2
  exit 1
fi

log "Redis is operational."

# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------
log "Dependency installation completed successfully."

