# Pro Tools Testing Guide
**Week 5: ZIP Smart + Watch Folder Intelligence**

## Overview

This guide provides comprehensive testing procedures for Ketter 3.0's Pro Tools session transfer capabilities, introduced in Week 5.

## Features Being Tested

1. **ZIP Smart Engine** - Automatic folder packaging with STORE mode (no compression)
2. **Watch Folder Intelligence** - Settle time detection for ongoing client transfers
3. **Triple SHA-256 Verification** - Applied to ZIP file (validates all internal files)
4. **Progress Tracking** - Real-time updates during ZIP/unzip operations
5. **Structure Preservation** - Maintains complete folder hierarchy

## Test Environments

### Automated Tests

Run automated tests to verify core functionality:

```bash
# Unit tests - ZIP Engine (8 tests)
docker-compose exec api pytest tests/test_zip_engine.py -v

# Unit tests - Watch Folder (13 tests)
docker-compose exec api pytest tests/test_watch_folder.py -v

# Integration tests - Pro Tools Scenarios (15+ tests)
docker-compose exec api pytest tests/test_protools_scenario.py -v

# All Week 5 tests
docker-compose exec api pytest tests/test_zip_engine.py tests/test_watch_folder.py tests/test_protools_scenario.py -v

# Expected result: All tests PASSED
```

### Manual Testing Scenarios

#### Scenario 1: Small Pro Tools Session (Quick Test)

**Purpose:** Verify basic ZIP Smart functionality

**Setup:**
```bash
# Create test session (10 audio files)
mkdir -p /data/transfers/test_session/Audio_Files
for i in {1..10}; do
  dd if=/dev/zero of=/data/transfers/test_session/Audio_Files/Audio_$(printf "%03d" $i).wav bs=1M count=1
done
echo '<?xml version="1.0"?><Session>Test</Session>' > /data/transfers/test_session/TestSession.ptx
```

**Test Steps:**
1. Open Ketter 3.0 web UI
2. Enter source: `/data/transfers/test_session`
3. Enter destination: `/data/transfers/restored_session`
4. **Do NOT** enable Watch Mode
5. Click "Create Transfer"

**Expected Results:**
- Transfer status: PENDING → COPYING → VERIFYING → COMPLETED
- Destination folder exists with same structure
- All 10 audio files + session file present
- Transfer shows " Folder (11 files)" badge
- Triple SHA-256 checksums all match
- PDF report includes ZIP Smart details

**Timing:**
- Expected duration: < 30 seconds for 10 MB

---

#### Scenario 2: Watch Mode with Simulated Client Transfer

**Purpose:** Test watch folder intelligence with ongoing transfer

**Setup:**
```bash
# Create empty destination folder
mkdir -p /data/transfers/incoming_session
```

**Test Steps:**
1. Open Ketter 3.0 web UI
2. Enter source: `/data/transfers/incoming_session`
3. Enter destination: `/data/transfers/final_session`
4. **Enable Watch Mode** 
5. Set settle time: 30 seconds
6. Click "Create Transfer"
7. Transfer status shows " Watching"

**While watching, simulate client transfer:**
```bash
# Simulate client copying files gradually
mkdir -p /data/transfers/incoming_session/Audio_Files

for i in {1..20}; do
  dd if=/dev/zero of=/data/transfers/incoming_session/Audio_Files/Audio_$(printf "%03d" $i).wav bs=1M count=1
  echo "Added file $i/20"
  sleep 2  # Simulate copy time
done

echo '<?xml version="1.0"?><Session>Incoming</Session>' > /data/transfers/incoming_session/Session.ptx
echo "Client transfer complete. Waiting for settle time..."
```

**Expected Results:**
- While files are being added: Status stays "PENDING" or "Watching"
- Audit logs show: "Waiting for folder stability"
- After 30 seconds of no changes: Watch mode triggers transfer
- Status changes: PENDING → COPYING → VERIFYING → COMPLETED
- Destination has all 20 files + session file
- Audit log shows watch duration

**Timing:**
- Watch duration: ~40-60 seconds (files + settle time)
- Transfer duration: < 1 minute

---

#### Scenario 3: Large Pro Tools Session (Performance Test)

**Purpose:** Test performance with realistic Pro Tools session size

**Setup:**
```bash
# Create realistic session (1000 files, 1 GB total)
mkdir -p /data/transfers/large_session/Audio_Files

echo "Creating 1000 audio files (1 MB each)..."
for i in {1..1000}; do
  dd if=/dev/zero of=/data/transfers/large_session/Audio_Files/Audio_$(printf "%04d" $i).wav bs=1M count=1 2>/dev/null
  if [ $((i % 100)) -eq 0 ]; then
    echo "Created $i/1000 files"
  fi
done

echo '<?xml version="1.0"?><Session>Large Session</Session>' > /data/transfers/large_session/LargeSession.ptx
echo "Session created: 1000 files, ~1 GB"
```

**Test Steps:**
1. Open Ketter 3.0 web UI
2. Enter source: `/data/transfers/large_session`
3. Enter destination: `/data/transfers/restored_large`
4. **Do NOT** enable Watch Mode (session is complete)
5. Click "Create Transfer"
6. Monitor progress bar

**Expected Results:**
- Badge shows " Folder (1001 files)"
- Progress tracking shows:
  - 0-50%: Zipping folder
  - 50-100%: Unzipping at destination
- Status: PENDING → COPYING → VERIFYING → COMPLETED
- Triple SHA-256 verification completes successfully
- Destination folder has 1001 files
- All file sizes match original

**Performance Benchmarks:**
- ZIP creation (STORE mode): ~10-15 seconds (100-200 MB/s)
- Triple SHA-256 calculation: ~10-20 seconds (depends on disk I/O)
- Unzip at destination: ~8-12 seconds (150-200 MB/s)
- **Total time: < 5 minutes** (including verification)

**Comparison to Manual Copy:**
- Manual copy of 1000 individual files: 30-60 minutes
- Ketter 3.0 with ZIP Smart: < 5 minutes
- **Speed improvement: 6-12x faster**

---

#### Scenario 4: Watch Mode Timeout Test

**Purpose:** Verify timeout handling when folder never stabilizes

**Setup:**
```bash
mkdir -p /data/transfers/unstable_folder
```

**Test Steps:**
1. Create transfer with Watch Mode enabled
2. Set settle time: 30 seconds
3. While watching, keep adding files continuously:

```bash
# Keep adding files every 10 seconds
for i in {1..100}; do
  dd if=/dev/zero of=/data/transfers/unstable_folder/file_$i.dat bs=1M count=1
  sleep 10
done
```

**Expected Results:**
- Transfer waits and logs "folder still changing"
- After max_wait_seconds (default 1 hour): timeout occurs
- Status: FAILED
- Error message: "Watch mode timeout - folder did not stabilize"
- Audit logs show all watch attempts

---

#### Scenario 5: Verify ZIP Integrity

**Purpose:** Ensure ZIP files can be validated and are bit-perfect

**Test Steps:**
1. Transfer a Pro Tools session using ZIP Smart
2. Manually extract ZIP file:

```bash
# Get ZIP file path from audit logs
ZIP_PATH="/tmp/ketter_temp_123_session.zip"

# Validate ZIP integrity
unzip -t $ZIP_PATH

# Expected output: "No errors detected in compressed data"
```

3. Compare checksums:

```bash
# Original folder
find /data/transfers/original_session -type f -exec sha256sum {} \; | sort > /tmp/original.txt

# Restored folder
find /data/transfers/restored_session -type f -exec sha256sum {} \; | sort > /tmp/restored.txt

# Compare
diff /tmp/original.txt /tmp/restored.txt

# Expected: No differences
```

---

## Performance Benchmarks

| Session Size | File Count | ZIP Time | Unzip Time | Verify Time | Total Time |
|--------------|------------|----------|------------|-------------|------------|
| 10 MB        | 10 files   | 0.5s     | 0.3s       | 2s          | ~10s       |
| 100 MB       | 100 files  | 1.5s     | 1s         | 5s          | ~30s       |
| 1 GB         | 1000 files | 12s      | 8s         | 20s         | ~4min      |
| 10 GB        | 10000 files| 120s     | 80s        | 200s        | ~30min     |

**Notes:**
- All times are approximate and depend on disk I/O performance
- ZIP Smart (STORE mode) is 3-5x faster than compression modes
- Triple SHA-256 is the slowest part for very large transfers

---

## Common Issues and Solutions

### Issue: "Folder is still receiving files" (Watch Mode)

**Cause:** Client transfer is ongoing

**Solution:** Wait for settle time to elapse. Check audit logs for progress.

```bash
# Check if files are still being added
watch -n 1 'ls -lh /data/transfers/incoming_session/Audio_Files | tail -5'
```

### Issue: "ZIP file too large"

**Cause:** Session exceeds available temp disk space

**Solution:** Ensure temp directory has enough space (same as session size)

```bash
# Check temp space
df -h /tmp

# If needed, change temp directory
export TMPDIR=/data/large_temp
```

### Issue: "Checksum mismatch after unzip"

**Cause:** Possible disk corruption or bug

**Solution:** Re-run transfer, check disk health

```bash
# Verify disk health
sudo smartctl -a /dev/sda

# Re-run with verbose logging
docker-compose exec api pytest tests/test_protools_scenario.py::TestProToolsChecksumVerification -v
```

### Issue: "Progress stuck at 50%"

**Cause:** Large unzip operation in progress

**Explanation:** Progress shows 0-50% for ZIP, 50-100% for unzip. If stuck at 50%, unzip is running but may take time for large sessions.

**Solution:** Check audit logs for current operation:

```bash
# Get transfer logs
curl http://localhost:8000/transfers/{transfer_id}/logs
```

---

## API Testing

Test ZIP Smart via API directly:

### Create Folder Transfer

```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/data/transfers/my_session",
    "destination_path": "/data/transfers/restored",
    "watch_mode_enabled": false,
    "settle_time_seconds": 30
  }'
```

### Create Transfer with Watch Mode

```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/data/transfers/incoming_session",
    "destination_path": "/data/transfers/final",
    "watch_mode_enabled": true,
    "settle_time_seconds": 60
  }'
```

### Check Transfer Status

```bash
curl http://localhost:8000/transfers/1 | jq
```

**Expected fields in response:**
```json
{
  "id": 1,
  "is_folder_transfer": true,
  "file_count": 1000,
  "watch_mode_enabled": false,
  "settle_time_seconds": 30,
  "watch_started_at": null,
  "watch_triggered_at": null,
  "status": "completed"
}
```

---

## Validation Checklist

Use this checklist to verify Week 5 functionality:

- [ ] **Unit Tests Pass**
  - [ ] test_zip_engine.py (8/8 tests)
  - [ ] test_watch_folder.py (13/13 tests)
  - [ ] test_protools_scenario.py (15/15 tests)

- [ ] **Frontend Features Work**
  - [ ] Watch Mode checkbox appears in FilePicker
  - [ ] Settle Time input shows when Watch Mode enabled
  - [ ] Folder transfers show " Folder (X files)" badge
  - [ ] Watch transfers show " Watching (Xs)" badge
  - [ ] Progress bar updates during transfer
  - [ ] History shows watch duration if applicable

- [ ] **Backend Features Work**
  - [ ] Folders are detected automatically (no user flag)
  - [ ] ZIP Smart uses STORE mode (no compression)
  - [ ] Triple SHA-256 calculated on ZIP file
  - [ ] Unzip maintains folder structure
  - [ ] Temporary ZIPs are cleaned up
  - [ ] Watch mode waits for stability
  - [ ] Watch mode respects settle time

- [ ] **API Endpoints Work**
  - [ ] POST /transfers accepts folder paths
  - [ ] POST /transfers accepts watch_mode_enabled
  - [ ] Response includes is_folder_transfer
  - [ ] Response includes file_count
  - [ ] Response includes watch fields
  - [ ] Audit logs include watch metadata

- [ ] **Database Schema Updated**
  - [ ] Migration 002 applied (folder fields)
  - [ ] Migration 003 applied (watch fields)
  - [ ] All 9 new columns exist
  - [ ] Default values work correctly

- [ ] **Performance Acceptable**
  - [ ] 10 files: < 30 seconds
  - [ ] 100 files: < 2 minutes
  - [ ] 1000 files: < 5 minutes

- [ ] **Documentation Complete**
  - [ ] WEEK5_PLAN.md finalized
  - [ ] WEEK5_PROGRESS.md updated
  - [ ] PROTOOLS_TESTING.md (this file)
  - [ ] state.md reflects 89% completion

---

## Real-World Production Testing

Before deploying to production:

1. **Test with actual Pro Tools sessions** from real projects
2. **Verify with dubbing studio workflow** - have operators test the UI
3. **Monitor system resources** during large transfers (CPU, RAM, disk I/O)
4. **Test network interruptions** - what happens if transfer is interrupted?
5. **Test disk space exhaustion** - graceful handling of full disk
6. **Measure time savings** - compare to manual copy workflows

---

## Success Criteria

Week 5 is complete when:

1.  All 36 automated tests pass (8 + 13 + 15)
2.  Manual testing scenarios 1-3 work correctly
3.  1000-file Pro Tools session transfers in < 5 minutes
4.  Watch mode correctly detects settle time
5.  Frontend UI shows all Week 5 features
6.  Database migrations applied successfully
7.  Documentation complete and accurate

---

## Troubleshooting Commands

```bash
# View all transfers
curl http://localhost:8000/transfers | jq

# View specific transfer with full details
curl http://localhost:8000/transfers/1 | jq

# View audit logs for transfer
curl http://localhost:8000/transfers/1/logs | jq

# View checksums
curl http://localhost:8000/transfers/1/checksums | jq

# Check database schema
docker-compose exec db psql -U ketter -d ketter -c "\d transfers"

# View Alembic migration history
docker-compose exec api alembic history

# Check current migration version
docker-compose exec api alembic current

# View RQ job queue
docker-compose exec api rq info

# View worker logs
docker-compose logs -f worker

# Check disk space
docker-compose exec api df -h

# Monitor temp folder
watch -n 1 'du -sh /tmp/ketter_temp_*'
```

---

**Last Updated:** 2025-11-05
**Document Version:** 1.0
**Week 5 Status:** Complete (pending final validation)
