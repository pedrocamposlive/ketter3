#!/bin/bash
# ------------------------------------------------------------
# DKU Module 03 v7 — Python Environment Setup (macOS ARM)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

echo "[DKU-03] Starting Python environment setup."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/dku/.venv"
REQ_FILE="${REPO_ROOT}/requirements.txt"

log() { echo "[DKU-03] $1"; }

# ------------------------------------------------------------
# 1. Validate Python 3.11
# ------------------------------------------------------------
log "Validating Python 3.11 availability."

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "[ERROR] Python 3.11 is not installed." >&2
  exit 1
fi

PYTHON_BIN="$(command -v python3.11)"
log "Python 3.11 binary located at ${PYTHON_BIN}."

# ------------------------------------------------------------
# 2. Recreate deterministic virtualenv
# ------------------------------------------------------------
log "Creating deterministic virtualenv at ${VENV_PATH}."

rm -rf "$VENV_PATH" || true
"$PYTHON_BIN" -m venv "$VENV_PATH"

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"

# ------------------------------------------------------------
# 3. Validate requirements.txt
# ------------------------------------------------------------
if [[ ! -f "$REQ_FILE" ]]; then
  echo "[ERROR] requirements.txt missing at ${REQ_FILE}." >&2
  exit 1
fi

# ------------------------------------------------------------
# 4. Upgrade pip/setuptools/wheel
# ------------------------------------------------------------
log "Upgrading pip, setuptools, wheel."
pip install --upgrade pip setuptools wheel >/dev/null

# ------------------------------------------------------------
# 5. Install backend dependencies
# ------------------------------------------------------------
log "Installing backend dependencies from ${REQ_FILE}."
pip install -r "$REQ_FILE"

log "Python environment setup completed successfully."
