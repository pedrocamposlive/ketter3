#!/bin/bash
# ------------------------------------------------------------
# DKU Rollback 00 — Hardware Check
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

log() { echo "[RB00] $1"; }

log "Hardware check is non-destructive. Nothing to rollback."
