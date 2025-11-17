#!/usr/bin/env bash
# Ketter 3.0 - macOS development restart helper

set -euo pipefail

PORT=${PORT:-8000}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_BIN="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin}"

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ $1${NC}"; }
log_success() { echo -e "${GREEN}✔ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
log_error() { echo -e "${RED}✖ $1${NC}"; }

ensure_path() {
  local extra_paths=("/opt/homebrew/bin" "/usr/local/bin")
  for path in "${extra_paths[@]}"; do
    if [[ ":$PATH:" != *":$path:"* ]] && [[ -d "$path" ]]; then
      export PATH="$path:$PATH"
    fi
  done
  if [[ -n "${VENV_BIN:-}" && -d "$VENV_BIN" ]]; then
    export PATH="$VENV_BIN:$PATH"
  fi
}

ensure_redis_cli() {
  if command -v redis-cli >/dev/null 2>&1; then
    return
  fi
  local redis_paths=("/opt/homebrew/opt/redis/bin" "/usr/local/opt/redis/bin")
  for path in "${redis_paths[@]}"; do
    if [[ -x "$path/redis-cli" ]]; then
      export PATH="$path:$PATH"
      return
    fi
  done
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log_error "Missing required command: $1"
    exit 1
  fi
}

kill_port() {
  log_info "Ensuring nothing is bound to port $PORT..."
  local pids
  pids=$(lsof -t -i :"$PORT" || true)
  if [[ -z "$pids" ]]; then
    log_success "Port $PORT already free"
    return
  fi
  log_warn "Processes detected on port $PORT: $pids"
  if kill -9 $pids 2>/dev/null; then
    log_success "Killed processes $pids"
    return
  fi
  log_warn "Normal kill failed, attempting sudo kill..."
  if sudo kill -9 $pids; then
    log_success "sudo kill succeeded for $pids"
  else
    log_error "Unable to free port $PORT"
    exit 1
  fi
}

start_redis() {
  if command -v docker >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
    log_info "Starting Redis via docker compose..."
    (cd "$PROJECT_ROOT" && docker compose up -d redis)
    return
  fi
  require_cmd brew
  if ! brew list redis >/dev/null 2>&1; then
    log_warn "Redis not installed. Install via: brew install redis"
    exit 1
  fi
  log_info "Starting Redis via brew services..."
  brew services start redis >/dev/null 2>&1 || true
}

wait_for_redis() {
  log_info "Waiting for Redis (localhost:6379)..."
  for _ in {1..10}; do
    if redis-cli ping >/dev/null 2>&1; then
      log_success "Redis responded to PING"
      return
    fi
    sleep 1
  done
  log_error "Redis is not responding"
  exit 1
}

start_backend() {
  log_info "Starting FastAPI (uvicorn) on port $PORT..."
  local uvicorn_cmd
  if command -v uvicorn >/dev/null 2>&1; then
    uvicorn_cmd=("uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "$PORT" "--reload")
  else
    uvicorn_cmd=("python3" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "$PORT" "--reload")
  fi

  (cd "$PROJECT_ROOT" && nohup "${uvicorn_cmd[@]}" >/tmp/ketter_uvicorn.log 2>&1 &) && BACKEND_PID=$!
  sleep 2
  if ! ps -p "${BACKEND_PID:-0}" >/dev/null 2>&1; then
    log_error "Failed to start uvicorn. Check /tmp/ketter_uvicorn.log"
    exit 1
  fi
  log_success "uvicorn started (PID $BACKEND_PID)"
}

wait_for_backend() {
  log_info "Waiting for backend health..."
  for _ in {1..20}; do
    if curl -fs "http://localhost:$PORT/health" >/dev/null 2>&1; then
      log_success "Backend responded on /health"
      return
    fi
    sleep 1
  done
  log_error "Backend did not respond on /health"
  exit 1
}

start_worker() {
  log_info "Starting RQ worker..."
  local worker_cmd
  if command -v rq >/dev/null 2>&1; then
    worker_cmd=("rq" "worker" "default")
  else
    worker_cmd=("python3" "-m" "rq" "worker" "default")
  fi

  # Use docker-compose worker if available
  if command -v docker >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
    (cd "$PROJECT_ROOT" && docker compose up -d worker)
    log_success "Docker worker container started"
    return
  fi

  (cd "$PROJECT_ROOT" && nohup "${worker_cmd[@]}" >/tmp/ketter_worker.log 2>&1 &) && WORKER_PID=$!
  sleep 2
  if ! ps -p "${WORKER_PID:-0}" >/dev/null 2>&1; then
    log_error "Worker failed to start. Check /tmp/ketter_worker.log"
    exit 1
  fi
  log_success "RQ worker started (PID $WORKER_PID)"
}

validate_worker() {
  log_info "Validating worker queue..."
  if command -v rq >/dev/null 2>&1; then
    rq info >/tmp/ketter_rq_info.log 2>&1 || log_warn "rq info failed (worker may be in Docker)"
  else
    log_warn "rq command unavailable for validation"
  fi
}

main() {
  ensure_path
  ensure_redis_cli
  require_cmd lsof
  require_cmd curl
  require_cmd python3
  require_cmd redis-cli

  kill_port
  start_redis
  wait_for_redis

  start_backend
  wait_for_backend

  start_worker
  validate_worker

  log_success "Environment ready. Logs:"
  log_info "  Backend log: /tmp/ketter_uvicorn.log"
  log_info "  Worker log:  /tmp/ketter_worker.log"
}

main "$@"
