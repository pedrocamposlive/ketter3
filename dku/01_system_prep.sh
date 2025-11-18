#!/bin/bash
# ------------------------------------------------------------
# DKU Module 01 — System Preparation (macOS Apple Silicon)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREW_PREFIX="/opt/homebrew"
LOG_DIR="${HOME}/Library/Logs/Ketter"

PATH="${BREW_PREFIX}/bin:${BREW_PREFIX}/sbin:${PATH}"
export PATH

log() { echo "[DKU-01] $1"; }

log "Ensuring system prerequisites."

mkdir -p "$LOG_DIR"
echo "Logs directory ensured at $LOG_DIR"

require_tool() {
  local tool="$1"
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[ERROR] Required tool '$tool' is missing." >&2
    exit 1
  fi
  echo "Tool available: $tool"
}

require_tool curl
require_tool git
require_tool brew

if ! command -v xcode-select >/dev/null 2>&1 || ! xcode-select -p >/dev/null 2>&1; then
  echo "[ERROR] Xcode Command Line Tools missing. Install them with 'xcode-select --install'." >&2
  exit 1
fi

log "System preparation completed successfully."
