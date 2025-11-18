#!/bin/bash
# ------------------------------------------------------------
# DKU Module 05 — Final Report Generation
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
FINAL_REPORT="${REPORT_DIR}/dku_report_${TIMESTAMP}.md"

PG_ISREADY="/opt/homebrew/opt/postgresql@16/bin/pg_isready"
REDIS_CLI="/opt/homebrew/bin/redis-cli"
PYTHON_BIN="$(command -v python3.11 || echo 'python3.11 not installed')"
BREW_BIN="$(command -v brew || echo 'brew not installed')"

mkdir -p "$REPORT_DIR"

log() { echo "[DKU-05] $1"; }
log "Collecting data for final report."

OS_NAME="$(uname -s)"
OS_ARCH="$(uname -m)"
OS_VER="$(sw_vers -productVersion || echo "N/A")"
RAM_GB="$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))"
FREE_DISK="$(df -H / | awk 'NR==2 {print $4}')"

POSTGRES_STATUS="$($PG_ISREADY 2>&1 || echo 'PostgreSQL status unavailable')"
REDIS_STATUS="$($REDIS_CLI -h 127.0.0.1 -p 6379 ping 2>&1 || echo 'Redis status unavailable')"

BREW_VER="$($BREW_BIN --version 2>/dev/null | head -n 1 || echo 'brew not installed')"
PY_VER="$($PYTHON_BIN --version 2>/dev/null || echo 'python3.11 not installed')"

cat > "$FINAL_REPORT" <<REPORT
# Ketter DKU — Final Report

**Generated:** $TIMESTAMP

## System
- OS: $OS_NAME
- Architecture: $OS_ARCH
- macOS Version: $OS_VER
- RAM: ${RAM_GB} GB
- Free Disk Space: $FREE_DISK

## Homebrew
- Binary: $BREW_BIN
- Version: $BREW_VER

## Python
- Binary: $PYTHON_BIN
- Version: $PY_VER

## Services
### PostgreSQL

```
$POSTGRES_STATUS
```

### Redis

```
$REDIS_STATUS
```

## DKU Modules Executed
- 00_hardware_check.sh
- 01_system_prep.sh
- 02_install_dependencies.sh
- 03_python_setup.sh
- 03b_redis_setup.sh
- 04_post_install_validation.sh
- 05_generate_report.sh

## Logs
- DKU reports directory: $REPORT_DIR

## Notes
- Logs directory: $REPORT_DIR
REPORT

echo "[DKU-05] Final report generated at $FINAL_REPORT."
