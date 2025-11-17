#!/bin/bash
#
# Ketter 3.0 - macOS Native Installer (v3 - Refactored)
# Installs Ketter as a native macOS application with full filesystem access.
# This script assumes a distribution package with pre-built .venv and node_modules.
#

# --- Strict Mode & Initial Setup ---
set -euo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Helper Functions ---
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

service_running() {
  brew services list | grep "$1" | grep "started" >/dev/null 2>&1
}

# --- Main Installation Logic ---
main() {
  # --- Phase 1: Pre-flight Checks & Environment Setup ---
  clear
  echo "================================================"
  echo "  Ketter 3.0 - macOS Native Installer (v3)"
  echo "  Production-Grade File Transfer System"
  echo "================================================"
  echo ""

  # Check if running as root
  if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}ERROR: Do not run this script as root/sudo.${NC}"
    echo "Run as normal user: ./install.sh"
    exit 1
  fi

  # Check macOS version
  if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}ERROR: This installer is for macOS only.${NC}"
    exit 1
  fi
  echo " macOS version: $(sw_vers -productVersion)"

  # --- Phase 2: Homebrew & Critical Path Setup ---
  echo ""
  echo " Phase 2: Setting up Homebrew and environment..."
  setup_homebrew_environment
  
  # Define KETTER_DIR (must be done after PATH setup and before any other logic)
  # This ensures KETTER_DIR is always the root of the project
  KETTER_DIR="$(cd "$(dirname "$0")"/../.. && pwd)" || { echo -e "${RED}ERROR: Failed to determine Ketter directory. Ensure script is run from 'installers/mac/'.${NC}"; exit 1; }
  cd "$KETTER_DIR" || { echo -e "${RED}ERROR: Failed to change to Ketter directory: $KETTER_DIR. Ensure the directory exists and has correct permissions.${NC}"; exit 1; }
  echo " Ketter Project Directory: $KETTER_DIR"

  # --- Phase 3: Dependency Verification & Installation ---
  echo ""
  echo " Phase 3: Verifying and installing dependencies..."
  
  # Architecture Check for pre-packaged dependencies
  check_architecture

  # Install Homebrew packages
  install_homebrew_package "Python 3.11" "python@3.11" "python3.11"
  install_homebrew_package "PostgreSQL 15" "postgresql@15" "psql"
  install_homebrew_package "Redis" "redis" "redis-server"
  install_homebrew_package "Node.js 20" "node@20" "node"

  # Resolve binary paths *after* all installations are confirmed
  PYTHON_BIN="$(which python3.11)"
  NPM_BIN="$(which npm)"
  PSQL_BIN="$(which psql)"
  CREATEDB_BIN="$(which createdb)"

  # Verify pre-packaged dependencies
  verify_prepackaged_deps

  # --- Phase 4: Service & Database Configuration ---
  echo ""
  echo "  Phase 4: Configuring services and database..."
  
  # Start/Restart services
  ensure_service_running "PostgreSQL" "postgresql@15"
  ensure_service_running "Redis" "redis"

  # Setup database
  setup_database

  # Create and load macOS services (LaunchAgents)
  create_and_load_services

  # --- Phase 5: Final Verification ---
  echo ""
  echo " Phase 5: Final verification..."
  verify_installation
}

# --- Helper Functions Implementation ---

setup_homebrew_environment() {
  # Try both common Homebrew installation paths
  if [[ $(uname -m) == 'arm64' ]]; then
    HOMEBREW_SHELLENV_PATH="/opt/homebrew/bin/brew"
  else
    HOMEBREW_SHELLENV_PATH="/usr/local/bin/brew"
  fi

  if [ -x "$HOMEBREW_SHELLENV_PATH" ]; then
    eval "$($HOMEBREW_SHELLENV_PATH shellenv)"
  elif [ -x "/usr/local/bin/brew" ]; then # Fallback for Intel
    eval "$(/usr/local/bin/brew shellenv)"
  elif [ -x "/opt/homebrew/bin/brew" ]; then # Fallback for ARM
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi

  if ! command_exists brew; then
    echo -e "${YELLOW}  Homebrew not found. Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # After installation, ensure environment is set again
    if [ -x "$HOMEBREW_SHELLENV_PATH" ]; then
      eval "$($HOMEBREW_SHELLENV_PATH shellenv)"
    fi
  fi

  if ! command_exists brew; then
    echo -e "${RED}ERROR: Homebrew installation failed. Please check your internet connection and permissions.${NC}"
    exit 1
  fi
  echo " Homebrew environment is ready."
}

check_architecture() {
  CURRENT_ARCH=$(uname -m)
  # IMPORTANT: Set EXPECTED_ARCH to the architecture of the machine where the .venv and node_modules were pre-built.
  EXPECTED_ARCH="arm64" # For Apple Silicon (M1/M2/etc.). Use 'x86_64' for Intel Macs.

  if [ "$CURRENT_ARCH" != "$EXPECTED_ARCH" ]; then
    echo -e "${YELLOW}WARNING: Architecture mismatch detected!${NC}"
    echo -e "${YELLOW}This installer expects pre-packaged dependencies for '$EXPECTED_ARCH', but the current system is '$CURRENT_ARCH'.${NC}"
    echo -e "${YELLOW}Pre-packaged Python virtual environment and Node.js modules might be incompatible.${NC}"
    echo -e "${RED}Installation aborted. Please rebuild the distribution package on a '$CURRENT_ARCH' machine.${NC}"
    exit 1
  fi
  echo " System architecture ($CURRENT_ARCH) matches expected architecture ($EXPECTED_ARCH)."
}

install_homebrew_package() {
  local name="$1"
  local package="$2"
  local command_to_check="$3"

  if ! command_exists "$command_to_check"; then
    echo -e "${YELLOW}   -> Dependency '$name' not found. Installing via Homebrew...${NC}"
    brew install "$package"
    if ! command_exists "$command_to_check"; then
      echo -e "${RED}ERROR: '$name' installation failed. Please check Homebrew logs.${NC}"
      exit 1
    fi
  fi
  echo "    Dependency '$name' is installed."
}

ensure_service_running() {
  local name="$1"
  local service="$2"

  if ! service_running "$service"; then
    echo "   -> Starting '$name' service..."
    brew services start "$service"
    sleep 3 # Give it some time to start
    if ! service_running "$service"; then
      echo -e "${RED}ERROR: '$name' service failed to start. Check 'brew services list' and logs.${NC}"
      exit 1
    fi
  else
    echo "   -> '$name' service already running. Restarting for a clean state..."
    brew services restart "$service"
    sleep 3 # Give it some time to restart
  fi
  echo "    '$name' service is running."
}

verify_prepackaged_deps() {
  echo "   -> Verifying pre-packaged Python dependencies..."
  VENV_DIR="$KETTER_DIR/.venv"
  if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}ERROR: Pre-packaged Python virtual environment not found at $VENV_DIR.${NC}"
    exit 1
  fi
  PYTHON_BIN_VENV="$VENV_DIR/bin/python"
  if ! command_exists "$PYTHON_BIN_VENV"; then
    echo -e "${RED}ERROR: Python executable not found in pre-packaged venv: $PYTHON_BIN_VENV.${NC}"
    exit 1
  fi
  echo "       Python venv found."

  echo "   -> Verifying pre-packaged frontend dependencies..."
  if [ ! -d "$KETTER_DIR/frontend/node_modules" ]; then
    echo -e "${RED}ERROR: Pre-packaged frontend dependencies (node_modules) not found.${NC}"
    exit 1
  fi
  echo "       node_modules found."
}

setup_database() {
  echo "   -> Setting up 'ketter' database..."
  if ! "$PSQL_BIN" -lqt | cut -d \| -f 1 | grep -qw ketter; then
    echo "      Creating 'ketter' database..."
    "$CREATEDB_BIN" ketter || { echo -e "${RED}ERROR: Failed to create 'ketter' database.${NC}"; exit 1; }
    echo "       Database created."
  else
    echo "       Database 'ketter' already exists."
  fi

  echo "   -> Running database migrations..."
  # Use the Python from the venv to run alembic
  "$KETTER_DIR/.venv/bin/alembic" upgrade head || { echo -e "${RED}ERROR: Failed to run database migrations.${NC}"; exit 1; }
  echo "    Migrations complete."
}

create_and_load_services() {
  echo "   -> Creating and loading macOS services (LaunchAgents)..."
  mkdir -p ~/Library/LaunchAgents || { echo -e "${RED}ERROR: Failed to create LaunchAgents directory.${NC}"; exit 1; }

  # Define paths for executables within the plists
  local python_in_venv="$KETTER_DIR/.venv/bin/python"
  local npm_in_path="$NPM_BIN"

  # Create Ketter API service
  cat > ~/Library/LaunchAgents/com.ketter.api.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ketter.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>$python_in_venv</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>app.main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$KETTER_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ketter-api.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ketter-api-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DATABASE_URL</key>
        <string>postgresql://$(whoami)@localhost:5432/ketter</string>
        <key>REDIS_URL</key>
        <string>redis://localhost:6379/0</string>
    </dict>
</dict>
</plist>
EOF

  # Create Ketter Worker service
  cat > ~/Library/LaunchAgents/com.ketter.worker.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ketter.worker</string>
    <key>ProgramArguments</key>
    <array>
        <string>$python_in_venv</string>
        <string>-m</string>
        <string>rq</string>
        <string>worker</string>
        <string>--url</string>
        <string>redis://localhost:6379/0</string>
        <string>default</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$KETTER_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ketter-worker.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ketter-worker-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DATABASE_URL</key>
        <string>postgresql://$(whoami)@localhost:5432/ketter</string>
        <key>REDIS_URL</key>
        <string>redis://localhost:6379/0</string>
    </dict>
</dict>
</plist>
EOF

  # Create Ketter Frontend service
  cat > ~/Library/LaunchAgents/com.ketter.frontend.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ketter.frontend</string>
    <key>ProgramArguments</key>
    <array>
        <string>$npm_in_path</string>
        <string>run</string>
        <string>dev</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$KETTER_DIR/frontend</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ketter-frontend.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ketter-frontend-error.log</string>
</dict>
</plist>
EOF

  echo "       Service files created."

  # Load services
  launchctl unload ~/Library/LaunchAgents/com.ketter.api.plist 2>/dev/null || true
  launchctl load ~/Library/LaunchAgents/com.ketter.api.plist || { echo -e "${RED}ERROR: Failed to load com.ketter.api.plist.${NC}"; exit 1; }

  launchctl unload ~/Library/LaunchAgents/com.ketter.worker.plist 2>/dev/null || true
  launchctl load ~/Library/LaunchAgents/com.ketter.worker.plist || { echo -e "${RED}ERROR: Failed to load com.ketter.worker.plist.${NC}"; exit 1; }

  launchctl unload ~/Library/LaunchAgents/com.ketter.frontend.plist 2>/dev/null || true
  launchctl load ~/Library/LaunchAgents/com.ketter.frontend.plist || { echo -e "${RED}ERROR: Failed to load com.ketter.frontend.plist.${NC}"; exit 1; }

  echo "    Services loaded."
}

verify_installation() {
  echo "   -> Waiting for services to initialize (15 seconds)..."
  sleep 15

  if ! command_exists curl; then
    echo -e "${YELLOW}WARNING: 'curl' command not found. Cannot verify service status automatically.${NC}"
  else
    API_STATUS=" API not responding"
    FRONTEND_STATUS=" Frontend not responding"

    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
      API_STATUS=" API running on http://localhost:8000"
    fi
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
      FRONTEND_STATUS=" Frontend running on http://localhost:3000"
    fi
    echo "   $API_STATUS"
    echo "   $FRONTEND_STATUS"
  fi

  echo ""
  echo "================================================"
  echo -e "${GREEN} Ketter 3.0 Installation Complete!${NC}"
  echo "================================================"
  echo ""
  echo " Access Ketter at: http://localhost:3000"
  echo ""
  echo " Useful commands:"
  echo "   View API logs:      tail -f ~/Library/Logs/ketter-api.log"
  echo "   View worker logs:   tail -f ~/Library/Logs/ketter-worker.log"
  echo "   View frontend logs: tail -f ~/Library/Logs/ketter-frontend.log"
  echo ""
  echo "   Restart services:   $KETTER_DIR/installers/mac/restart.sh"
  echo ""
  echo " Configuration file: $KETTER_DIR/ketter.config.yml"
  echo ""
}

# --- Script Entry Point ---
main "$@"