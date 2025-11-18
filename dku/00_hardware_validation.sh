#!/bin/bash
# ------------------------------------------------------------
# DKU Module 00 — Hardware Check (macOS Apple Silicon)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

BREW_PREFIX="/opt/homebrew"
MIN_RAM_GB=8
MIN_DISK_GB=3

log() { echo "[DKU-00] $1"; }

log "Starting hardware validation."

# ------------------------------------------------------------
# CPU architecture
# ------------------------------------------------------------
ARCH=$(uname -m)
log "Architecture reported: $ARCH"
if [[ "$ARCH" != "arm64" ]]; then
  echo "[ERROR] Unsupported architecture: $ARCH. Apple Silicon (arm64) required." >&2
  exit 1
fi

# ------------------------------------------------------------
# CPU identification
# ------------------------------------------------------------
CPU_MODEL=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown CPU")
echo "CPU Model: $CPU_MODEL"

# ------------------------------------------------------------
# RAM validation
# ------------------------------------------------------------
if ! command -v sysctl >/dev/null 2>&1; then
  echo "[ERROR] sysctl is not available." >&2
  exit 1
fi

MEM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
RAM_GB=$(( MEM_BYTES / 1024 / 1024 / 1024 ))
if (( RAM_GB == 0 )); then
  echo "[ERROR] Unable to read RAM size." >&2
  exit 1
fi

echo "System RAM: ${RAM_GB} GB"
if (( RAM_GB < MIN_RAM_GB )); then
  echo "[ERROR] Minimum memory requirement is ${MIN_RAM_GB} GB." >&2
  exit 1
fi

# ------------------------------------------------------------
# Disk validation
# ------------------------------------------------------------
if ! command -v df >/dev/null 2>&1; then
  echo "[ERROR] df is not available." >&2
  exit 1
fi

DISK_AVAILABLE_GB=$(df -g / | awk 'NR==2 {print $4}' || echo 0)
if (( DISK_AVAILABLE_GB < MIN_DISK_GB )); then
  echo "[ERROR] At least ${MIN_DISK_GB} GB of free disk space is required." >&2
  exit 1
fi

echo "Disk Available: ${DISK_AVAILABLE_GB} GB"

# ------------------------------------------------------------
# Homebrew prefix validation
# ------------------------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  echo "[ERROR] Homebrew must be installed at ${BREW_PREFIX}." >&2
  exit 1
fi

BREW_REAL_PREFIX=$(brew --prefix 2>/dev/null || echo "")
if [[ "$BREW_REAL_PREFIX" != "$BREW_PREFIX" ]]; then
  echo "[ERROR] Homebrew prefix mismatch: expected ${BREW_PREFIX}, found ${BREW_REAL_PREFIX}." >&2
  exit 1
fi

log "Hardware check completed successfully."
