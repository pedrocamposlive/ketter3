#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 05 — Final Report
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"

log() { echo "[RB05] $1"; }

log "Deleting final report artifacts."
find "$REPORT_DIR" -maxdepth 1 -type f -name 'dku_report_*' -delete 2>/dev/null || true

log "Final report rollback completed."
