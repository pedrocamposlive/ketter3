#!/bin/bash

# Script para testar MOVE mode com pastas
# Verifica que a pasta origem é preservada

set -e

SOURCE="/Users/pedroc.ampos/Desktop/OUT"
DEST="/Users/pedroc.ampos/Desktop/IN"

echo "=========================================="
echo "MOVE Mode Folder Test"
echo "=========================================="
echo ""

# Cleanup
echo "[1/5] Cleaning up test folders..."
rm -rf "$SOURCE"/*
rm -rf "$DEST"/*
echo " Folders cleaned"

# Create test files in source
echo ""
echo "[2/5] Creating test files in source folder..."
mkdir -p "$SOURCE"
echo "File 1 content" > "$SOURCE/file1.txt"
echo "File 2 content" > "$SOURCE/file2.txt"
echo "File 3 content" > "$SOURCE/file3.txt"
mkdir -p "$SOURCE/subfolder"
echo "Nested file content" > "$SOURCE/subfolder/nested.txt"
ls -la "$SOURCE"
echo " Test files created"

# Count files in source
echo ""
echo "[3/5] Counting files before transfer..."
SOURCE_COUNT=$(find "$SOURCE" -type f | wc -l)
echo "Files in source: $SOURCE_COUNT"

# Instructions for manual testing
echo ""
echo "[4/5] Manual testing via UI..."
echo "=========================================="
echo "NOW DO THIS IN THE UI (http://localhost:3000):"
echo "=========================================="
echo "1. Click 'Create New Transfer'"
echo "2. Source Path: $SOURCE"
echo "3. Destination Path: $DEST"
echo "4. Mode: MOVE (select radio button)"
echo "5. Click 'START TRANSFER'"
echo "6. Wait for completion"
echo ""
echo "Press ENTER when transfer is complete..."
read

# Verify results
echo ""
echo "[5/5] Verifying results..."
echo "=========================================="

# Check if source folder exists
if [ -d "$SOURCE" ]; then
    echo " Source folder EXISTS (as expected)"
else
    echo " FAIL: Source folder was deleted (should be preserved!)"
    exit 1
fi

# Check if source is empty
SOURCE_REMAINING=$(find "$SOURCE" -type f 2>/dev/null | wc -l || echo 0)
if [ $SOURCE_REMAINING -eq 0 ]; then
    echo " Source folder is EMPTY (contents moved)"
else
    echo " FAIL: Source folder still has $SOURCE_REMAINING files"
    exit 1
fi

# Check if destination has files
DEST_COUNT=$(find "$DEST" -type f 2>/dev/null | wc -l || echo 0)
if [ $DEST_COUNT -eq $SOURCE_COUNT ]; then
    echo " Destination has all files ($DEST_COUNT files)"
else
    echo " FAIL: Expected $SOURCE_COUNT files in destination, found $DEST_COUNT"
    exit 1
fi

echo ""
echo "=========================================="
echo "SUCCESS: MOVE mode works correctly!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Source folder: PRESERVED (empty)"
echo "- Source files: MOVED to destination"
echo "- Destination: Complete ($DEST_COUNT files)"
echo ""
