#!/bin/bash
# ------------------------------------------------------------
# DKU Run — Deterministic Module Executor
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DKU_DIR="${REPO_ROOT}/dku"
ROLLBACK_DIR="${DKU_DIR}/rollback"
LOG_DIR="${REPO_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/dku_run_$(date '+%Y%m%d_%H%M%S').log"

PATH="/opt/homebrew/bin:/opt/homebrew/sbin:${PATH}"
export PATH

if [[ -e /dev/fd/1 ]]; then
  exec > >(tee "$LOG_FILE") 2>&1
else
  exec > "$LOG_FILE" 2>&1
fi

log() { echo "[DKU-RUN] $1"; }

run_module() {
  local name="$1"
  local script="$2"
  local rollback_script="$3"

  log "Starting module ${name}."
  if ! bash "$script"; then
    log "Module ${name} failed. Triggering rollback."
    if [[ -x "$rollback_script" ]] || [[ -f "$rollback_script" ]]; then
      bash "$rollback_script"
    else
      log "Rollback script not found: ${rollback_script}."
    fi
    exit 1
  fi
  log "Module ${name} completed."
}

MODULES=(
  "00:${DKU_DIR}/00_hardware_check.sh:${ROLLBACK_DIR}/rollback_00.sh"
  "01:${DKU_DIR}/01_system_prep.sh:${ROLLBACK_DIR}/rollback_01.sh"
  "02:${DKU_DIR}/02_install_dependencies.sh:${ROLLBACK_DIR}/rollback_02.sh"
  "03_python:${DKU_DIR}/03_python_setup.sh:${ROLLBACK_DIR}/rollback_03.sh"
  "03b_redis:${DKU_DIR}/03b_redis_setup.sh:${ROLLBACK_DIR}/rollback_03b.sh"
  "04:${DKU_DIR}/04_post_install_validation.sh:${ROLLBACK_DIR}/rollback_04.sh"
  "05:${DKU_DIR}/05_generate_report.sh:${ROLLBACK_DIR}/rollback_05.sh"
)

log "DKU Run initiated with log file at $LOG_FILE."
for module in "${MODULES[@]}"; do
  IFS=':' read -r name script rollback <<< "$module"
  run_module "$name" "$script" "$rollback"
done

log "DKU Run completed successfully."
