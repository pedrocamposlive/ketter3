#!/bin/bash
# ------------------------------------------------------------
# DKU Module 02 — PostgreSQL 16 Install & Configuration
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

BREW_PREFIX="/opt/homebrew"
PG_FORMULA="postgresql@16"
PG_PREFIX="${BREW_PREFIX}/opt/${PG_FORMULA}"
PG_BIN="${PG_PREFIX}/bin"
PG_DATA_DIR="${BREW_PREFIX}/var/${PG_FORMULA}"

export PATH="${PG_BIN}:${PATH}"

log() { echo "[DKU-02] $1"; }
require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: $cmd" >&2
    exit 1
  fi
}

log "Installing and configuring PostgreSQL 16."
require_command brew
log "Installing ${PG_FORMULA} via Homebrew if needed."
brew list --versions "$PG_FORMULA" >/dev/null 2>&1 || brew install "$PG_FORMULA"

require_command pg_ctl
require_command initdb

log "Stopping PostgreSQL service before recreating data."
brew services stop "$PG_FORMULA" >/dev/null 2>&1 || true

log "Resetting data directory at ${PG_DATA_DIR}."
rm -rf "$PG_DATA_DIR"
mkdir -p "$PG_DATA_DIR"

log "Initializing PostgreSQL cluster."
"${PG_BIN}/initdb" --locale=C --encoding=UTF8 -D "$PG_DATA_DIR"

log "Starting PostgreSQL service."
brew services start "$PG_FORMULA" >/dev/null 2>&1

log "Waiting for PostgreSQL readiness."
PG_ISREADY="${PG_BIN}/pg_isready"
attempts=20
until "$PG_ISREADY" -h 127.0.0.1 -p 5432 >/dev/null 2>&1; do
  if (( attempts == 0 )); then
    echo "[ERROR] PostgreSQL did not become ready." >&2
    exit 1
  fi
  attempts=$((attempts - 1))
  sleep 1
done

log "Ensuring application roles and database."
PSQL="${PG_BIN}/psql"
KETTER_DB="ketter"
KETTER_USER="ketter_user"
KETTER_USER_PASS="ketter_user_pass"
KETTER_ADMIN="ketter_admin"
KETTER_ADMIN_PASS="ketter_admin_pass"

run_sql() {
  local sql="$1"
  "${PSQL}" -h 127.0.0.1 -U postgres -d postgres -c "$sql"
}

run_sql "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${KETTER_ADMIN}') THEN CREATE ROLE ${KETTER_ADMIN} WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD '${KETTER_ADMIN_PASS}'; ELSE ALTER ROLE ${KETTER_ADMIN} WITH PASSWORD '${KETTER_ADMIN_PASS}' SUPERUSER CREATEDB CREATEROLE; END IF; END $$;"
run_sql "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${KETTER_USER}') THEN CREATE ROLE ${KETTER_USER} WITH LOGIN PASSWORD '${KETTER_USER_PASS}'; ELSE ALTER ROLE ${KETTER_USER} WITH PASSWORD '${KETTER_USER_PASS}'; END IF; END $$;"

EXISTS_DB=$("${PSQL}" -h 127.0.0.1 -U postgres -Atqc "SELECT 1 FROM pg_database WHERE datname='${KETTER_DB}'" || true)
if [[ "$EXISTS_DB" == "1" ]]; then
  log "Database ${KETTER_DB} exists—reassigning owner to ${KETTER_USER}."
  "${PSQL}" -h 127.0.0.1 -U postgres -c "ALTER DATABASE ${KETTER_DB} OWNER TO ${KETTER_USER};"
else
  log "Creating database ${KETTER_DB}."
  "${PSQL}" -h 127.0.0.1 -U postgres -c "CREATE DATABASE ${KETTER_DB} OWNER ${KETTER_USER};"
fi

log "PostgreSQL 16 setup completed successfully."
