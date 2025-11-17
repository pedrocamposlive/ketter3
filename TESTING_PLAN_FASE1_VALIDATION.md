# Ketter 3.0 - FASE 1 Validation Testing Plan

## Overview

This document outlines the comprehensive testing strategy to validate all FASE 1 enhancements work correctly in real transfer scenarios.

## Test Environment Setup

### Prerequisites
- Docker Compose running (PostgreSQL, Redis, API, Worker)
- All FASE 1 enhancements deployed
- 116 unit tests passing
- Test data prepared

### Data Preparation
```bash
# Create test directories
mkdir -p /tmp/ketter-test/{source,dest,corrupt}

# Prepare test files
dd if=/dev/zero of=/tmp/ketter-test/source/file_1mb.bin bs=1M count=1
dd if=/dev/zero of=/tmp/ketter-test/source/file_10mb.bin bs=1M count=10
mkdir -p /tmp/ketter-test/source/test_folder
touch /tmp/ketter-test/source/test_folder/file1.txt
touch /tmp/ketter-test/source/test_folder/file2.txt
```

---

## Test Categories

### 1. BASIC FUNCTIONALITY TESTS (Sanity Check)

#### Test 1.1: Simple File Copy
```
Scenario: User copies single 1MB file
Expected:
   File copied to destination
   SHA-256 checksums match (source = dest = final)
   Transfer status = COMPLETED
   Audit log shows all events
   No temp files left behind
Duration: ~1-2 seconds
```

#### Test 1.2: Simple File Move
```
Scenario: User moves single 1MB file
Expected:
   File copied to destination
   Source file DELETED
   Destination readable and accessible
   All checksums verify
   Transfer status = COMPLETED
Duration: ~1-2 seconds
```

#### Test 1.3: Folder Copy
```
Scenario: User copies folder with multiple files
Expected:
   ZIP created automatically
   Transferred and verified
   Unzipped at destination
   All files present
   Folder structure preserved
Duration: ~2-3 seconds
```

---

### 2. SECURITY VALIDATION TESTS (ENHANCE #1)

#### Test 2.1: Path Traversal Attack Blocked
```
Scenario: API call with path traversal: /tmp/../etc/passwd
Expected:
   Request rejected with 422 Unprocessable Entity
   Error message: "Path traversal detected"
   No transfer created
   Audit logged: SECURITY_VIOLATION
Result: PASS = Attack blocked
```

#### Test 2.2: Symlink Attack Blocked
```
Scenario: Create symlink to /etc/passwd, try to transfer
Expected:
   Transfer validation blocks symlink
   Error: "Symlinks not allowed for destination"
   No data transferred
Result: PASS = Attack blocked
```

#### Test 2.3: Unauthorized Volume Access
```
Scenario: Try to access /root or /home
Expected:
   Request rejected
   Error: "Path outside allowed volumes"
   No transfer processed
Result: PASS = Access denied
```

---

### 3. CONCURRENCY TESTS (ENHANCE #2)

#### Test 3.1: Concurrent COPY Operations
```
Scenario: Two jobs copying different files simultaneously
Expected:
   Both transfers proceed in parallel
   Both complete successfully
   No locks (COPY mode is lock-free)
   Checksums match for both
Duration: ~2 seconds (parallel, not 4)
```

#### Test 3.2: Concurrent MOVE Operations (Same File)
```
Scenario: Two jobs try to MOVE same file
Expected:
   Job 1 acquires exclusive lock
   Job 2 waits for lock (max 30s)
   Job 1 completes, releases lock
   Job 2 times out: "Could not acquire lock"
   Job 2 marked FAILED
Result: PASS = Only one processes, clear error
```

#### Test 3.3: Lock Timeout Protection
```
Scenario: Transfer takes >30s, another MOVE on same file
Expected:
   Job 2 times out after 30s
   Error logged with timeout reason
   No data corruption
Result: PASS = Lock timeout prevents hanging
```

---

### 4. ERROR HANDLING & ROLLBACK TESTS (ENHANCE #3)

#### Test 4.1: Checksum Mismatch Rollback
```
Scenario: Checksum fails during copy
Expected:
   Database transaction rolled back
   Transfer marked FAILED
   No temp files left behind
   Error message logged
   Retry count incremented
Duration: ~1-2 seconds
```

#### Test 4.2: Insufficient Disk Space Rollback
```
Scenario: Disk fills up during copy
Expected:
   Copy operation fails
   All changes rolled back
   Destination file removed
   Transfer status = FAILED
   Clean state for retry
```

#### Test 4.3: Permission Error Cleanup
```
Scenario: Destination directory becomes read-only mid-transfer
Expected:
   Transfer fails gracefully
   Temp files cleaned up
   Database rolled back
   Clear error message
Result: PASS = Atomic failure
```

---

### 5. POST-DELETION VERIFICATION TESTS (ENHANCE #4)

#### Test 5.1: Destination Verified Before Deletion
```
Scenario: MOVE mode, destination might be corrupted
Expected:
   Before deleting source, verify destination:
    - Exists
    - Correct size
    - Readable (first + last 1KB)
   If verification fails: rollback, don't delete source
   Source remains for recovery
Result: PASS = Source safe
```

#### Test 5.2: Corrupted File Detection
```
Scenario: Destination file truncated to 50%
Expected:
   Verification detects size mismatch
   Source NOT deleted
   Transfer marked FAILED
   User can retry
Result: PASS = Data loss prevented
```

---

### 6. CORS SECURITY TESTS (ENHANCE #5)

#### Test 6.1: Authorized Origin Allowed
```
Scenario: Request from http://localhost:3000
Expected:
   Request accepted
   CORS headers present
   Transfer proceeds normally
Result: PASS = Auth origin works
```

#### Test 6.2: Unauthorized Origin Blocked
```
Scenario: Request from http://evil.com
Expected:
   CORS error (no CORS headers)
   Browser blocks request
   No transfer initiated
Result: PASS = CORS whitelist enforced
```

#### Test 6.3: No Wildcard Vulnerability
```
Scenario: Try to access with allow_origins=['*']
Expected:
   Config has whitelist, not wildcard
   Verify .env or docker-compose.yml
   No vulnerabilities present
Result: PASS = Secure CORS config
```

---

### 7. WATCH MODE CIRCUIT BREAKER TESTS (ENHANCE #6)

#### Test 7.1: Max Cycles Limit
```
Scenario: Watch mode runs for 10,001 cycles
Expected:
   Stops at 10,000 cycles
   Logged: "Circuit breaker: Max cycles reached"
   Job exits gracefully
Duration: ~14 hours (simulated with small MAX_CYCLES for testing)
Alternative: Test with MAX_CYCLES=10 for quick validation
```

#### Test 7.2: Error Rate Threshold
```
Scenario: 8/10 recent cycles have errors (80% error rate)
Expected:
   Circuit breaker triggers
   Logged: "High error rate (80% >= 50%)"
   Watch mode stops
   Transfer marked for manual review
Result: PASS = Runaway watch prevented
```

#### Test 7.3: Max Duration Limit
```
Scenario: Watch mode running for >24 hours
Expected:
   Stops after 24 hours
   Logged: "Max duration exceeded"
   Status updated
Result: PASS = Long-running job protected
```

---

## Test Execution Order

### Phase 1: Setup & Sanity (10 minutes)
1. Verify Docker containers running
2. Run basic COPY test
3. Run basic MOVE test
4. Check logs are clean

### Phase 2: Security (15 minutes)
1. Test path traversal blocks
2. Test symlink protection
3. Test volume whitelist

### Phase 3: Concurrency (20 minutes)
1. Test concurrent COPY (should be fast)
2. Test concurrent MOVE on same file (should serialize)
3. Test lock timeout

### Phase 4: Error Handling (15 minutes)
1. Test checksum mismatch
2. Test disk space error
3. Test permission error

### Phase 5: Verification (10 minutes)
1. Test post-deletion verification
2. Test corrupted file detection

### Phase 6: Configuration (5 minutes)
1. Test CORS whitelist
2. Test watch circuit breaker

**Total Time:** ~75 minutes

---

## Success Criteria

### All Tests Must Pass
-  No security vulnerabilities exploitable
-  No data loss or corruption
-  Proper error recovery
-  Audit trails complete
-  No orphaned files
-  Concurrent operations safe

### Performance Targets
- Single file COPY: <5 seconds
- Single file MOVE: <5 seconds
- Folder transfer: <10 seconds
- Concurrent COPY: Linear scaling

### No Regressions
- All existing functionality still works
- No new warnings or errors
- Database clean state after each test
- Logs show expected events

---

## Tools & Commands

### Start Test Environment
```bash
# Ensure clean state
docker-compose down -v
docker-compose up -d

# Wait for services
sleep 10

# Verify health
curl -s http://localhost:8000/health | jq
```

### Run Unit Tests
```bash
# All 116 tests
python -m pytest tests/ -v

# Specific category
python -m pytest tests/test_path_security.py -v
python -m pytest tests/test_concurrent_lock.py -v
python -m pytest tests/test_transaction_rollback.py -v
```

### Test Individual Transfers
```bash
# Via API
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/file_1mb.bin",
    "destination_path": "/tmp/ketter-test/dest/file_1mb.bin",
    "operation_mode": "copy"
  }'

# Check status
curl http://localhost:8000/transfers/1

# Get audit logs
curl http://localhost:8000/transfers/1/logs
```

### Cleanup Test Data
```bash
rm -rf /tmp/ketter-test
docker-compose down -v
```

---

## Troubleshooting

### Test Fails: "Path not in allowed volumes"
- Check VOLUMES config in app/config.py
- Ensure /tmp is configured
- Verify volume paths are absolute

### Test Fails: "Could not acquire lock"
- May be normal for concurrent MOVE test
- Check if previous transfer still running
- Clear any stuck transfers in DB

### Test Fails: "Checksum mismatch"
- Check disk space
- Verify source file exists
- Check file permissions

### Test Fails: "Permission denied"
- Check /tmp/ketter-test directory permissions
- Ensure Docker container can write
- Verify destination directory exists

---

## Post-Test Validation

After all tests pass:

1. **Database State:** No orphaned records
2. **File System:** No temp files left behind
3. **Logs:** All events logged correctly
4. **Performance:** No degradation from baseline
5. **Security:** All protections verified

---

## Sign-Off Checklist

- [ ] All basic functionality tests passed
- [ ] All security tests passed
- [ ] All concurrency tests passed
- [ ] All error handling tests passed
- [ ] All verification tests passed
- [ ] CORS configuration validated
- [ ] Watch mode circuit breaker validated
- [ ] No regressions found
- [ ] Performance meets targets
- [ ] Ready for production deployment

---

**Document Version:** 1.0
**Created:** November 12, 2025
**Status:** READY FOR EXECUTION
