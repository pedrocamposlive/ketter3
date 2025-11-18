#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — QUICKSTART v3
# ------------------------------------------------------------
# Executa:
# 1. rollback_ketter_mac_v4.sh
# 2. dku_run.sh
# 3. inicia serviços essenciais
# 4. ativa venv e roda um smoke test do backend
# ------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { echo "[QS] $1"; }

ROLLBACK="${REPO_ROOT}/scripts/rollback_ketter_mac_v4.sh"
DKU_RUN="${REPO_ROOT}/dku_run.sh"

log "Running rollback..."
bash "$ROLLBACK"

log "Running DKU pipeline..."
bash "$DKU_RUN"

log "Starting essential services..."
brew services start postgresql@16
brew services start redis

log "Locating virtualenv..."

# auto-detecção
if [[ -d "${REPO_ROOT}/dku/.venv" ]]; then
  VENV_PATH="${REPO_ROOT}/dku/.venv"
elif [[ -d "${REPO_ROOT}/.venv" ]]; then
  VENV_PATH="${REPO_ROOT}/.venv"
else
  echo "[QS] ERROR: Could not find virtualenv."
  exit 1
fi

# shellcheck disable=SC1091
source "${VENV_PATH}/bin/activate"

log "Virtualenv activated: $VENV_PATH"

log "Running backend smoke test (import check)..."

python - << 'EOF'
import app.main
print("Smoke test OK: backend imported.")
EOF

log "Quickstart completed successfully."
exit 0
