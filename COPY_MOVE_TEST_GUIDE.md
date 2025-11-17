# COPY vs MOVE Mode Testing Guide

## Quick Setup

Run these commands to create test folders:

```bash
# Create source with 3 files
mkdir -p /tmp/ketter_move_test_source
echo "File A content" > /tmp/ketter_move_test_source/file_a.txt
echo "File B content" > /tmp/ketter_move_test_source/file_b.txt
echo "File C content" > /tmp/ketter_move_test_source/file_c.txt

# Create destination (empty)
mkdir -p /tmp/ketter_move_test_dest

# List files before
echo "=== BEFORE TRANSFER ==="
ls -la /tmp/ketter_move_test_source/
```

## Test 1: COPY Mode (Files Should Stay at Source)

### Setup
```bash
# Use paths from above
SOURCE: /tmp/ketter_move_test_source
DEST: /tmp/ketter_move_test_dest
```

### Steps in UI:
1. Open http://localhost:3000
2. In "New Transfer" section:
   - Source Path: `/tmp/ketter_move_test_source`
   - Destination Path: `/tmp/ketter_move_test_dest`
   - Check "Watch Mode (wait for folder to stabilize)"
   - Select "COPY (keep originals at source)"
   - Click "CREATE TRANSFER"

3. Wait for transfer to complete (watch Active Transfers section)
4. Once "Status: COMPLETED", verify in terminal:

```bash
echo "=== AFTER COPY ==="
echo "Source files (should STILL exist):"
ls -la /tmp/ketter_move_test_source/
echo ""
echo "Destination files (should exist):"
ls -la /tmp/ketter_move_test_dest/
```

**Expected Result:** Both folders have files

---

## Test 2: MOVE Mode (Files Should Be Deleted from Source)

### Setup
```bash
# Create fresh source for MOVE test
mkdir -p /tmp/ketter_move_test_source_2
echo "File X content" > /tmp/ketter_move_test_source_2/file_x.txt
echo "File Y content" > /tmp/ketter_move_test_source_2/file_y.txt
echo "File Z content" > /tmp/ketter_move_test_source_2/file_z.txt

# Create destination
mkdir -p /tmp/ketter_move_test_dest_2

# List files before
echo "=== BEFORE TRANSFER ==="
ls -la /tmp/ketter_move_test_source_2/
```

### Steps in UI:
1. In "New Transfer" section:
   - Source Path: `/tmp/ketter_move_test_source_2`
   - Destination Path: `/tmp/ketter_move_test_dest_2`
   - Check "Watch Mode (wait for folder to stabilize)"
   - Select "MOVE (delete originals after transfer)"
   - Click "CREATE TRANSFER"

2. Wait for transfer to complete
3. Once "Status: COMPLETED", verify in terminal:

```bash
echo "=== AFTER MOVE ==="
echo "Source files (should be GONE):"
ls -la /tmp/ketter_move_test_source_2/ 2>&1 || echo "Folder deleted!"
echo ""
echo "Destination files (should exist):"
ls -la /tmp/ketter_move_test_dest_2/
```

**Expected Result:** Source deleted, files only in destination

---

## Validation Checklist

### COPY Mode Test:
- [ ] Transfer completes with "COMPLETED" status
- [ ] All files appear in destination folder
- [ ] All files STILL appear in source folder
- [ ] Audit trail shows "Processed file" for each file
- [ ] Audit trail does NOT show "Source deleted"

### MOVE Mode Test:
- [ ] Transfer completes with "COMPLETED" status
- [ ] All files appear in destination folder
- [ ] Source folder is GONE (or empty if couldn't delete folder)
- [ ] Audit trail shows "Processed file" for each file
- [ ] Audit trail DOES show "Source deleted successfully"

---

## View Audit Trail

After each transfer:
1. Go to "Transfer History" section
2. Click on the completed transfer
3. Click "View Audit Trail"
4. Look for events like:
   - For COPY: No "Source deleted" message
   - For MOVE: "Source deleted successfully (MOVE mode)"

---

## Troubleshooting

If MOVE doesn't work:
- Check application logs: `docker-compose logs api`
- Check for errors in browser console (F12)
- Verify permissions: `chmod 777 /tmp/ketter_move_test_source_2`
- Check if operation_mode is being sent: Browser Network tab → POST /transfers

---

## Files for This Test

Source folder structure:
```
/tmp/ketter_move_test_source/
├── file_a.txt
├── file_b.txt
└── file_c.txt

/tmp/ketter_move_test_source_2/
├── file_x.txt
├── file_y.txt
└── file_z.txt
```
