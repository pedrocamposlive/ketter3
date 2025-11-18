#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 03 — Python Environment
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/.venv"

log() { echo "[RB03] $1"; }

if [[ -d "$VENV_PATH" ]]; then
  log "Removing virtual environment at $VENV_PATH."
  rm -rf "$VENV_PATH"
else
  log "Virtual environment not present; nothing to remove."
fi

log "Python environment rollback completed."
