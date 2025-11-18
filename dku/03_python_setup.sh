#!/bin/bash
# ------------------------------------------------------------
# DKU Module 03 — Python Environment Preparation
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${REPO_ROOT}/.venv"
REQ_FILE="${REPO_ROOT}/requirements.txt"

log() { echo "[DKU-03] $1"; }

log "Validating Python 3.11 availability."
PYTHON_BIN="$(command -v python3.11 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "[ERROR] python3.11 not found in PATH. Install via Homebrew at /opt/homebrew." >&2
  exit 1
fi
log "Python 3.11 binary located at $PYTHON_BIN."

if [[ -d "$VENV_PATH" ]]; then
  log "Removing existing virtualenv for deterministic recreation."
  rm -rf "$VENV_PATH"
fi

log "Creating deterministic virtualenv at $VENV_PATH."
"$PYTHON_BIN" -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

log "Upgrading pip, setuptools, wheel."
pip install --upgrade pip setuptools wheel

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[ERROR] requirements.txt missing at $REQ_FILE." >&2
  exit 1
fi

log "Installing python dependencies from requirements.txt."
pip install -r "$REQ_FILE"

if ! command -v alembic >/dev/null 2>&1; then
  echo "[ERROR] alembic binary not available after dependency installation." >&2
  exit 1
fi

log "Python environment prepared successfully."
