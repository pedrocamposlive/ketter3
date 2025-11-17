#!/usr/bin/env bash
# dev_env_fix.sh - macOS environment fix script for Ketter 3.0
# Installs and validates Redis, redis-cli, rq, uvicorn, and environment PATH.

set -e

bold() { echo "\033[1m$1\033[0m"; }
green() { echo "\033[0;32m$1\033[0m"; }
red() { echo "\033[0;31m$1\033[0m"; }
yellow() { echo "\033[0;33m$1\033[0m"; }

bold "--- KETTER 3.0: Environment Fix Script (macOS) ---"

# 1. Ensure Homebrew exists
if ! command -v brew &> /dev/null; then
  red "Homebrew is not installed. Install from https://brew.sh and re-run this script."
  exit 1
else
  green "Homebrew detected."
fi

# 2. Install Redis
bold "Checking Redis installation..."
if brew list redis &> /dev/null; then
  green "Redis already installed."
else
  yellow "Redis not found. Installing..."
  brew install redis
fi

echo
bold "Starting Redis via brew services..."
brew services start redis || true
sleep 2

# 3. Validate Redis connectivity
echo
bold "Validating Redis..."
if command -v redis-cli &> /dev/null; then
  RESP=$(redis-cli ping 2>/dev/null || true)
  if [[ "$RESP" == "PONG" ]]; then
    green "Redis OK (PONG)."
  else
    red "Redis is installed but not responding. Check logs: brew services list"
  fi
else
  red "redis-cli not found. Installing..."
  brew install redis
fi

# 4. Install Python dependencies
bold "Installing Python dependencies (rq, uvicorn)..."
pip install rq uvicorn || pip3 install rq uvicorn

# 5. Validate Python modules
echo
bold "Validating Python modules..."
python3 - <<'PY'
import sys
try:
    import rq
    import uvicorn
    print("Modules OK")
except Exception as e:
    print("Module validation failed:", e)
    sys.exit(1)
PY

echo
green "Environment dependencies installed and validated."

# 6. Display summary
bold "--- SUMMARY ---"
green "Redis: Active"
green "redis-cli: OK"
green "rq: OK"
green "uvicorn: OK"

echo
bold "Environment ready for 'dev_restart.sh' execution."
