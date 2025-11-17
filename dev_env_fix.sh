#!/usr/bin/env bash
# Ketter 3.0 - macOS environment fix script

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}ℹ $1${NC}"; }
success() { echo -e "${GREEN}✔ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✖ $1${NC}"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    error "Missing required command: $1"
    exit 1
  fi
}

ensure_homebrew() {
  if ! command -v brew >/dev/null 2>&1; then
    error "Homebrew is required. Install from https://brew.sh/"
    exit 1
  fi
}

install_redis() {
  ensure_homebrew
  if brew list redis >/dev/null 2>&1; then
    success "Redis already installed"
  else
    log "Installing Redis via brew..."
    brew install redis
  fi
}

start_redis() {
  log "Starting Redis via brew services..."
  brew services start redis
}

ensure_redis_cli() {
  if command -v redis-cli >/dev/null 2>&1; then
    success "redis-cli available in PATH"
    return
  fi
  local redis_paths=("/opt/homebrew/opt/redis/bin" "/usr/local/opt/redis/bin")
  for path in "${redis_paths[@]}"; do
    if [[ -x "$path/redis-cli" ]]; then
      export PATH="$path:$PATH"
      success "Added $path to PATH for redis-cli"
      return
    fi
  done
  warn "redis-cli still missing; verify Redis install"
}

install_python_package() {
  local package="$1"
  if python3 - <<PY >/dev/null 2>&1
import importlib
import sys
sys.exit(0 if importlib.util.find_spec("$package") else 1)
PY
  then
    success "Python package '$package' already installed"
  else
    log "Installing Python package '$package'..."
    pip3 install "$package"
  fi
}

validate_dependencies() {
  log "Validating redis-cli..."
  redis-cli ping
  success "redis-cli ping OK"

  log "Validating Python imports..."
  python3 - <<'PY'
import rq, uvicorn
print("rq import ok")
print("uvicorn import ok")
PY
  success "Python validation complete"
}

main() {
  install_redis
  start_redis
  ensure_redis_cli
  install_python_package "rq"
  install_python_package "uvicorn"
  validate_dependencies
  success "dev_env_fix completed successfully"
}

main "$@"
