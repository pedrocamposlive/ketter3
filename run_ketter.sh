#!/bin/bash

# Ketter 3.0 - Complete System Startup & Management
# Safe, reliable script for development and testing
# No breaking changes to existing code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default command
COMMAND="${1:-start}"

# Helper functions
print_header() {
  echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
}

print_success() {
  echo -e "${GREEN} $1${NC}"
}

print_error() {
  echo -e "${RED} $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW} $1${NC}"
}

# Check if docker-compose is installed
check_docker() {
  if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
  fi
  print_success "docker-compose found"
}

# Check if we're in the right directory
check_directory() {
  if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Are you in Ketter_Repo directory?"
    exit 1
  fi
  print_success "Running from correct directory"
}

# Start all services
start_services() {
  print_header "Starting Ketter 3.0 Services"

  check_docker
  check_directory

  print_info "Building and starting containers..."
  docker-compose up -d

  print_success "Containers started"

  print_info "Waiting for services to be ready (15 seconds)..."
  sleep 15

  print_header "Service Status"
  docker-compose ps

  print_header "Access Points"
  echo -e "${GREEN}Frontend:${NC}     http://localhost:3000"
  echo -e "${GREEN}API:${NC}          http://localhost:8000"
  echo -e "${GREEN}API Docs:${NC}     http://localhost:8000/docs"
  echo -e "${GREEN}Database:${NC}     localhost:5432 (user: ketter)"
  echo -e "${GREEN}Redis:${NC}        localhost:6379"
  echo ""

  print_success "Ketter 3.0 is ready to use!"
}

# Stop all services
stop_services() {
  print_header "Stopping Ketter 3.0 Services"

  check_docker
  check_directory

  print_info "Stopping containers..."
  docker-compose stop

  print_success "All services stopped"
}

# Restart frontend only (for UI changes)
restart_frontend() {
  print_header "Restarting Frontend Service"

  check_docker
  check_directory

  print_info "Restarting frontend container..."
  docker-compose restart frontend

  print_info "Waiting for frontend to be ready (5 seconds)..."
  sleep 5

  print_success "Frontend restarted"
  print_info "Access at: http://localhost:3000"
}

# Restart all services
restart_all() {
  print_header "Restarting All Ketter 3.0 Services"

  check_docker
  check_directory

  print_info "Restarting all containers..."
  docker-compose restart

  print_info "Waiting for services to be ready (10 seconds)..."
  sleep 10

  print_header "Service Status"
  docker-compose ps

  print_success "All services restarted"
}

# Check status
status() {
  print_header "Ketter 3.0 Service Status"

  check_docker
  check_directory

  docker-compose ps

  echo ""
  print_info "Service URLs:"
  echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
  echo -e "  API: ${GREEN}http://localhost:8000${NC}"
  echo ""
}

# View logs
logs() {
  check_docker
  check_directory

  SERVICE="${2:-all}"

  if [ "$SERVICE" = "all" ]; then
    print_info "Showing logs from all services (Ctrl+C to exit)..."
    docker-compose logs -f
  else
    print_info "Showing logs from $SERVICE service (Ctrl+C to exit)..."
    docker-compose logs -f "$SERVICE"
  fi
}

# Full cleanup and reset
reset() {
  print_header "Full Reset of Ketter 3.0"

  print_warning "This will:"
  echo "  - Stop all containers"
  echo "  - Remove all containers"
  echo "  - Remove all volumes (database data will be lost)"
  echo ""

  read -p "Are you sure? (yes/no): " CONFIRM

  if [ "$CONFIRM" != "yes" ]; then
    print_info "Reset cancelled"
    return
  fi

  check_docker
  check_directory

  print_info "Stopping and removing containers..."
  docker-compose down -v

  print_success "Reset complete"
  print_info "Run: ./run_ketter.sh start"
}

# Show help
show_help() {
  cat << EOF

${BLUE}Ketter 3.0 - Docker Management Script${NC}

${GREEN}Usage:${NC}
  ./run_ketter.sh [COMMAND] [OPTIONS]

${GREEN}Commands:${NC}
  start              Start all Ketter services
  stop               Stop all services
  restart            Restart all services
  restart-frontend   Restart only frontend (for UI changes)
  status             Show service status
  logs [SERVICE]     View service logs
  reset              Full reset (removes all data)
  help               Show this help message

${GREEN}Examples:${NC}
  ./run_ketter.sh start
  ./run_ketter.sh restart-frontend
  ./run_ketter.sh logs api
  ./run_ketter.sh status

${GREEN}Default:${NC}
  If no command specified, runs 'start'

${YELLOW}Safety:${NC}
  - No code is modified
  - No permanent data loss (except 'reset')
  - Safe to run multiple times

EOF
}

# Main execution
case $COMMAND in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    restart_all
    ;;
  restart-frontend)
    restart_frontend
    ;;
  status)
    status
    ;;
  logs)
    logs "$@"
    ;;
  reset)
    reset
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    print_error "Unknown command: $COMMAND"
    echo ""
    show_help
    exit 1
    ;;
esac
