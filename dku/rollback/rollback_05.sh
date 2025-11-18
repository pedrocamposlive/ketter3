#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 05 v3 — Final Report Generator Rollback
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

echo "[RB05] Starting rollback for Module 05."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"

log() { echo "[RB05] $1"; }

log "Removing incomplete DKU final reports."
rm -f "${REPORT_DIR}/DKU_FINAL_REPORT_"*.txt || true

log "Rollback 05 Completed Successfully."

