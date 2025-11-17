#!/bin/bash
#
# Ketter 3.0 - Restart Services
# Quick restart of all Ketter services
#

echo " Restarting Ketter services..."

# Unload services
launchctl unload ~/Library/LaunchAgents/com.ketter.api.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.ketter.worker.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.ketter.frontend.plist 2>/dev/null

sleep 2

# Load services
launchctl load ~/Library/LaunchAgents/com.ketter.api.plist
launchctl load ~/Library/LaunchAgents/com.ketter.worker.plist
launchctl load ~/Library/LaunchAgents/com.ketter.frontend.plist

echo " Services restarted"
echo "⏳ Waiting 5 seconds for services to initialize..."
sleep 5

echo ""
echo "Access Ketter at: http://localhost:3000"
