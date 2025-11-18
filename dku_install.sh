#!/bin/bash
# ------------------------------------------------------------
# KETTER DKU — INSTALLER v2 (macOS Compatible)
# Robust logging without /dev/fd substitutions
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}" && pwd)"
cd "$REPO_ROOT"

LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/dku_install_$(date '+%Y%m%d_%H%M%S').log"

# ------------------------------------------------------------
# Logging (macOS-safe)
# ------------------------------------------------------------
# If process substitution works → use tee
if [[ -e /dev/fd/1 ]]; then
  exec > >(tee "$LOG_FILE") 2>&1
else
  # Fallback: no process substitution
  exec > "$LOG_FILE" 2>&1
fi

log() {
  echo "[DKU-INSTALL] $1"
}

# ------------------------------------------------------------
# 1. Validate folder structure
# ------------------------------------------------------------
log "Validating DKU folder structure"
if [[ ! -d "dku" ]]; then
  log "ERROR: dku/ folder missing. Aborting."
  exit 1
fi

# ------------------------------------------------------------
# 2. Make all DKU modules executable
# ------------------------------------------------------------
log "Setting execution flags on DKU modules"
chmod +x dku/*.sh || true
chmod +x dku/rollback/*.sh || true

# ------------------------------------------------------------
# 3. Confirm with user
# ------------------------------------------------------------
log "Requesting user confirmation"
echo "This will install the DKU system. Continue? (y/n)"
read -r ans
if [[ "$ans" != "y" ]]; then
  log "User aborted."
  exit 0
fi

# ------------------------------------------------------------
# 4. Run preparation modules (00 and 01)
# ------------------------------------------------------------
log "Running 00_hardware_check.sh"
./dku/00_hardware_check.sh || { log "FAILED at hardware check"; exit 1; }

log "Running 01_system_prep.sh"
./dku/01_system_prep.sh || { log "FAILED at system prep"; exit 1; }

# ------------------------------------------------------------
# 5. Installer finished
# ------------------------------------------------------------
log "DKU Installer v2 finished successfully."
log "Log saved at: $LOG_FILE"

