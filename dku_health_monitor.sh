#!/bin/bash
# ------------------------------------------------------------
# KETTER DKU — HEALTH MONITOR
# Performs continuous health checks for DB, Redis, Backend, Worker
# ------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PATH="${REPO_ROOT}/.venv"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
REPORT_FILE="${REPORT_DIR}/health_report_${TIMESTAMP}.md"

mkdir -p "$REPORT_DIR"

# Activate venv
if [[ -d "$VENV_PATH" ]]; then
  source "$VENV_PATH/bin/activate"
else
  echo "Virtualenv not found at $VENV_PATH" >&2
  exit 1
fi

echo "Generating DKU Health Report..."

# Collect basic info
OS_NAME=$(uname -s)
OS_ARCH=$(uname -m)
OS_VER=$(sw_vers -productVersion || echo "N/A")

# Service checks
PG_STATUS=$(pg_isready 2>&1 || true)
REDIS_STATUS=$(redis-cli ping 2>&1 || true)
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9001 || true)
WORKER_STATUS=$(ps aux | grep rq | grep -v grep || true)

cat > "$REPORT_FILE" <<EOF
# Ketter DKU — Health Report
Generated: $TIMESTAMP

## System
- OS: $OS_NAME
- Architecture: $OS_ARCH
- macOS: $OS_VER

## PostgreSQL
\`\`\`
$PG_STATUS
\`\`\`

## Redis
\`\`\`
$REDIS_STATUS
\`\`\`

## Backend (Uvicorn)
HTTP Code: $BACKEND_STATUS

## Worker (RQ)
\`\`\`
$WORKER_STATUS
\`\`\`

EOF

echo "Health report saved to $REPORT_FILE"

