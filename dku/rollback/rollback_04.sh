#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 04 — Post-Install Validation
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"

log() { echo "[RB04] $1"; }

log "Removing post-install validation artifacts."
find "$REPORT_DIR" -maxdepth 1 -type f -name 'post_install_validation_*.txt' -delete 2>/dev/null || true
find "$REPORT_DIR" -maxdepth 1 -type f -name 'checklist_dku_*.txt' -delete 2>/dev/null || true

log "Post-install validation rollback completed."
