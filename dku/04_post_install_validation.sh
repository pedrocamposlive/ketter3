#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — MODULE 04 POST-INSTALL VALIDATION (v8)
# ------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_ROOT/.." && pwd)"

LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"

MODULE_04_LOG="${LOG_DIR}/module_04_validation_$(date '+%Y%m%d_%H%M%S').log"

echo "[DKU-04] Starting Post-Install Validation." | tee "$MODULE_04_LOG"

# ------------------------------------------------------------
# Rodar safe checklist híbrido v8
# ------------------------------------------------------------

echo "[DKU-04] Running hybrid DKU-safe checklist v8..." | tee -a "$MODULE_04_LOG"

if ! bash "$SCRIPT_ROOT/safe_checklist_dku_hybrid.sh" >> "$MODULE_04_LOG" 2>&1; then
    echo "[DKU-04] ERROR: Hybrid checklist reported failure." | tee -a "$MODULE_04_LOG"
    echo "[DKU-04] See log for details: $MODULE_04_LOG" | tee -a "$MODULE_04_LOG"
    exit 1
fi

echo "[DKU-04] Hybrid validation passed." | tee -a "$MODULE_04_LOG"
echo "[DKU-04] Module 04 validation completed successfully." | tee -a "$MODULE_04_LOG"
exit 0
