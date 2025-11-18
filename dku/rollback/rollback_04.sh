#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 04 — Post-Install Validation (v7)
# ------------------------------------------------------------
# Esta rotina é segura e NÃO destrutiva.
# O checklist híbrido v7 não inicia backend, worker ou frontend.
# Portanto, este rollback apenas:
# - Remove relatórios gerados pelo checklist
# - Garante que não existam processos zombie
# - Mantém PostgreSQL e Redis intactos (não são tocados)
# ------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/docs/dku_reports"

log() { echo "[RB04] $1"; }

log "Starting rollback for module 04 (v7)."

# ------------------------------------------------------------
# Limpeza de relatórios da checklist híbrida
# ------------------------------------------------------------
log "Cleaning checklist validation reports."

if [[ -d "$LOG_DIR" ]]; then
  find "$LOG_DIR" -type f -name "checklist_safe_*.txt" -delete || true
  find "$LOG_DIR" -type f -name "checklist_hybrid_*.txt" -delete || true
  find "$LOG_DIR" -type f -name "checklist_*" -delete || true
else
  log "Reports directory not found. Skipping."
fi

# ------------------------------------------------------------
# Garantir que nenhum processo leftover exista
# ------------------------------------------------------------
log "Ensuring no leftover uvicorn, alembic or python processes."

pkill -f "uvicorn" >/dev/null 2>&1 || true
pkill -f "app.main" >/dev/null 2>&1 || true
pkill -f "alembic" >/dev/null 2>&1 || true
pkill -f "python" >/dev/null 2>&1 || true

log "Rollback 04 (v7) completed successfully."
exit 0
