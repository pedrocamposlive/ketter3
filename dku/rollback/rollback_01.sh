#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 01 — System Preparation
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

LOG_DIR="${HOME}/Library/Logs/Ketter"

log() { echo "[RB01] $1"; }

log "Removing DKU log directory if present."
if [[ -d "$LOG_DIR" ]]; then
  rm -rf "$LOG_DIR"
  log "Removed $LOG_DIR."
else
  log "Log directory not found; nothing to remove."
fi
