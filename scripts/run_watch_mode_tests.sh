#!/bin/bash

################################################################################
#
#  Ketter 3.0 - Watch Mode Contínuo Test Launcher
#
# This script:
# 1. Checks prerequisites (Docker, API)
# 2. Runs database migrations (if needed)
# 3. Executes the integration test suite
# 4. Generates a test report
#
# Usage:
#   ./scripts/run_watch_mode_tests.sh
#   ./scripts/run_watch_mode_tests.sh --no-setup  (skip migrations)
#   ./scripts/run_watch_mode_tests.sh --api-url http://192.168.1.100:8000
#
################################################################################

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
API_URL="${API_BASE_URL:-http://localhost:8000}"
SKIP_SETUP=false
DOCKER_COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${CYAN}${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${CYAN}${1}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN} ${1}${NC}"
}

print_error() {
    echo -e "${RED} ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW} ${1}${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-setup)
            SKIP_SETUP=true
            shift
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_header " KETTER 3.0 - WATCH MODE CONTÍNUO TEST LAUNCHER"

# Check prerequisites
print_info "Checking prerequisites..."

# 1. Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_success "Docker found: $(docker --version)"

# 2. Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_success "Docker Compose found: $(docker-compose --version)"

# 3. Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

# 4. Check requests library
if ! python3 -c "import requests" 2>/dev/null; then
    print_warning "requests library not found, installing..."
    pip install requests --quiet
    print_success "requests library installed"
fi

# 5. Check if docker-compose.yml exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
    exit 1
fi
print_success "docker-compose.yml found"

# Check Docker containers
print_info "Checking Docker containers..."

if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
    print_warning "Some containers are not running"
    print_info "Starting Docker containers..."
    cd "$REPO_ROOT"
    docker-compose up -d
    sleep 10
    print_success "Containers started"
else
    print_success "Docker containers are running"
fi

# Check API health
print_info "Checking API health at $API_URL..."

if curl -s "$API_URL/health" | grep -q "ok" 2>/dev/null; then
    print_success "API is healthy"
else
    print_warning "API not responding, waiting for startup (30 seconds)..."
    for i in {1..30}; do
        if curl -s "$API_URL/health" | grep -q "ok" 2>/dev/null; then
            print_success "API is now healthy"
            break
        fi
        sleep 1
    done

    if ! curl -s "$API_URL/health" | grep -q "ok" 2>/dev/null; then
        print_error "API did not respond after 30 seconds"
        print_info "Check Docker logs: docker-compose logs api"
        exit 1
    fi
fi

# Run migrations (unless skipped)
if [ "$SKIP_SETUP" = false ]; then
    print_info "Running database migrations..."

    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T api alembic upgrade head 2>&1 | grep -q "done"; then
        print_success "Database migrations completed"
    else
        print_warning "Migrations may have already been applied"
    fi
else
    print_info "Skipping database migrations (--no-setup)"
fi

# Run the test script
print_header " RUNNING INTEGRATION TESTS"

cd "$REPO_ROOT"
export API_BASE_URL="$API_URL"

if python3 scripts/test_watch_mode_integration.py; then
    print_header " ALL TESTS PASSED!"
    print_success "Watch Mode Contínuo is working correctly"
    print_info "Test data available at: /tmp/ketter_watch_mode_test/"
    print_info "To clean up test data: rm -rf /tmp/ketter_watch_mode_test/"
    exit 0
else
    print_header " TESTS FAILED"
    print_error "See details above for failures"
    print_info "Test data available at: /tmp/ketter_watch_mode_test/"
    print_info "Check Docker logs: docker-compose logs -f api worker"
    exit 1
fi
