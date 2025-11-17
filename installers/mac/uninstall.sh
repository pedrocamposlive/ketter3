#!/bin/bash
#
# Ketter 3.0 - Uninstaller for macOS
# Removes Ketter services and stops all processes
#

echo "️  Uninstalling Ketter 3.0..."
echo ""

# Stop and remove LaunchAgents
echo "Stopping services..."
launchctl unload ~/Library/LaunchAgents/com.ketter.api.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.ketter.worker.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.ketter.frontend.plist 2>/dev/null

echo "Removing service files..."
rm -f ~/Library/LaunchAgents/com.ketter.api.plist
rm -f ~/Library/LaunchAgents/com.ketter.worker.plist
rm -f ~/Library/LaunchAgents/com.ketter.frontend.plist

echo "Removing log files..."
rm -f ~/Library/Logs/ketter-*.log

echo ""
echo " Ketter services removed"
echo ""
echo "Note: This does not remove:"
echo "  - PostgreSQL database 'ketter' (run: dropdb ketter)"
echo "  - Python packages (run: pip3 uninstall -r requirements.txt)"
echo "  - Ketter source code directory"
echo "  - PostgreSQL, Redis, Node.js (brew uninstall if needed)"
echo ""
