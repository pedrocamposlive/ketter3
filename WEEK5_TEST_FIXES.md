# Week 5 Test Fixes - Action Plan

**Date:** 2025-11-05
**Status:**  13/57 tests failing (77.2% passing)
**Target:**  57/57 tests passing (100%)

---

## Summary

**Current Test Results:**
-  ZIP Engine Tests: 14/19 passed (5 failures)
-  Watch Folder Tests: 18/22 passed (4 failures)
-  Pro Tools Scenario Tests: 12/16 passed (4 failures)
- **Total: 44/57 passed (77.2%)**

**Root Cause Analysis:**
All failures are related to **missing or incorrectly implemented helper functions** in the main modules (`zip_engine.py` and `watch_folder.py`). The tests expect these functions to exist, but they either:
1. Don't exist yet
2. Have wrong signatures
3. Return wrong data structures

---

## Failed Tests Breakdown

### 1. ZIP Engine Tests (5 failures)

#### Test: `test_zip_folder_progress_callback`
- **File:** `tests/test_zip_engine.py:159`
- **Error:** `AssertionError`
- **Issue:** Progress callback not being called correctly or not receiving expected parameters
- **Fix Required:** Check progress callback implementation in `zip_folder_smart()`

#### Test: `test_validate_zip_integrity_valid`
- **File:** `tests/test_zip_engine.py:249`
- **Error:** `TypeError`
- **Issue:** `validate_zip_integrity()` function missing or has wrong signature
- **Fix Required:** Implement/fix `validate_zip_integrity()` in `app/zip_engine.py`

#### Test: `test_validate_zip_integrity_corrupted`
- **File:** `tests/test_zip_engine.py:261`
- **Error:** `TypeError`
- **Issue:** Same as above - `validate_zip_integrity()` function issue
- **Fix Required:** Same as above

#### Test: `test_validate_zip_integrity_nonexistent`
- **File:** `tests/test_zip_engine.py:270`
- **Error:** Generic error (likely FileNotFoundError handling)
- **Issue:** `validate_zip_integrity()` doesn't handle non-existent files
- **Fix Required:** Add error handling for non-existent ZIP files

#### Test: `test_complete_zip_unzip_workflow`
- **File:** `tests/test_zip_engine.py:310`
- **Error:** `TypeError`
- **Issue:** Cascading failure from `validate_zip_integrity()`
- **Fix Required:** Fix `validate_zip_integrity()` function

---

### 2. Watch Folder Tests (4 failures)

#### Test: `test_watch_folder_timeout`
- **File:** `tests/test_watch_folder.py:273`
- **Error:** `AssertionError`
- **Issue:** Timeout behavior not working as expected
- **Fix Required:** Check timeout logic in `watch_folder_until_stable()`

#### Test: `test_get_folder_info_empty`
- **File:** `tests/test_watch_folder.py:296`
- **Error:** `KeyError`
- **Issue:** `get_folder_info()` function missing or returns wrong dict structure
- **Fix Required:** Implement `get_folder_info()` in `app/watch_folder.py`

#### Test: `test_get_folder_info_with_files`
- **File:** `tests/test_watch_folder.py:304`
- **Error:** `KeyError`
- **Issue:** Same as above - `get_folder_info()` function
- **Fix Required:** Same as above

#### Test: `test_format_settle_time`
- **File:** `tests/test_watch_folder.py:330`
- **Error:** `AssertionError`
- **Issue:** `format_settle_time()` helper function missing or returns wrong format
- **Fix Required:** Implement `format_settle_time()` helper in `app/watch_folder.py`

---

### 3. Pro Tools Scenario Tests (4 failures)

#### Test: `test_zip_protools_session_small`
- **File:** `tests/test_protools_scenario.py:105`
- **Error:** `TypeError`
- **Issue:** Cascading from `validate_zip_integrity()` in zip_engine
- **Fix Required:** Fix zip_engine functions (see section 1)

#### Test: `test_complete_protools_workflow`
- **File:** `tests/test_protools_scenario.py:137`
- **Error:** `TypeError`
- **Issue:** Cascading from `validate_zip_integrity()` in zip_engine
- **Fix Required:** Fix zip_engine functions (see section 1)

#### Test: `test_watch_mode_waits_for_client_transfer`
- **File:** `tests/test_protools_scenario.py:267`
- **Error:** `TypeError` (line 254)
- **Issue:** Problem with watch_folder_until_stable() callback
- **Fix Required:** Check callback signature in watch_folder.py

#### Test: `test_empty_audio_folder`
- **File:** `tests/test_protools_scenario.py:354`
- **Error:** `AssertionError`
- **Issue:** Empty folder handling not working as expected
- **Fix Required:** Improve empty folder handling in zip_folder_smart()

---

## Action Plan (Priority Order)

### Phase 1: Fix ZIP Engine (HIGH PRIORITY)
**Estimated Time:** 30-45 minutes
**Impact:** Fixes 5 zip_engine tests + 2 protools tests (7 total)

1.  **Implement `validate_zip_integrity()` function**
   - Location: `app/zip_engine.py`
   - Signature: `validate_zip_integrity(zip_path: str) -> Tuple[bool, str]`
   - Returns: `(True, "ZIP is valid")` or `(False, "Error message")`
   - Must handle:
     - Non-existent files → `(False, "File not found")`
     - Corrupted ZIPs → `(False, "ZIP corrupted")`
     - Valid ZIPs → `(True, "OK")`

2.  **Fix progress callback in `zip_folder_smart()`**
   - Ensure callback is called with correct signature: `(current, total, current_file)`
   - Verify it's called during ZIP operation

3.  **Improve empty folder handling**
   - Handle case where folder has 0 files
   - Should still create valid ZIP structure

---

### Phase 2: Fix Watch Folder (MEDIUM PRIORITY)
**Estimated Time:** 20-30 minutes
**Impact:** Fixes 4 watch_folder tests + 1 protools test (5 total)

1.  **Implement `get_folder_info()` function**
   - Location: `app/watch_folder.py`
   - Signature: `get_folder_info(folder_path: str) -> dict`
   - Returns:
     ```python
     {
         'file_count': int,
         'total_size': int,
         'folder_path': str
     }
     ```

2.  **Implement `format_settle_time()` helper**
   - Location: `app/watch_folder.py`
   - Signature: `format_settle_time(seconds: int) -> str`
   - Returns: Human-readable format (e.g., "30s", "2m", "1h 30m")

3.  **Fix timeout behavior in `watch_folder_until_stable()`**
   - Ensure function returns `False` when timeout is reached
   - Test expects timeout to work correctly

4.  **Fix progress callback signature**
   - Ensure callback works with watch mode tests
   - Check signature matches test expectations

---

### Phase 3: Verify All Tests Pass
**Estimated Time:** 10-15 minutes
**Impact:** Final validation

1.  **Run validation script**
   ```bash
   ./validate_week5_tests.sh
   ```
   - Target: 57/57 tests passing (100%)

2.  **Update documentation**
   - Update `state.md` with 100% test pass rate
   - Update `WEEK5_COMPLETE_SUMMARY.md`

3.  **Commit changes**
   - All tests passing
   - System 100% complete

---

## Detailed Fix Checklist

### File: `app/zip_engine.py`

```python
# ADD THESE FUNCTIONS:

def validate_zip_integrity(zip_path: str) -> Tuple[bool, str]:
    """
    Validate that a ZIP file exists and is not corrupted.

    Args:
        zip_path: Path to ZIP file

    Returns:
        Tuple of (is_valid, message)
        - (True, "ZIP is valid") if file exists and is readable
        - (False, "Error message") otherwise
    """
    import zipfile
    import os

    # Check if file exists
    if not os.path.exists(zip_path):
        return (False, f"ZIP file not found: {zip_path}")

    # Check if file is a valid ZIP
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Test ZIP integrity
            bad_file = zipf.testzip()
            if bad_file is not None:
                return (False, f"ZIP corrupted at file: {bad_file}")
            return (True, "ZIP is valid")
    except zipfile.BadZipFile:
        return (False, "File is not a valid ZIP archive")
    except Exception as e:
        return (False, f"Error validating ZIP: {str(e)}")


# FIX THIS FUNCTION - ensure progress callback is called:
def zip_folder_smart(
    source_folder: str,
    zip_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> str:
    # ... existing code ...

    # ENSURE THIS LOOP CALLS THE CALLBACK:
    for i, (root, _, files) in enumerate(os.walk(source_folder)):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source_folder)
            zipf.write(file_path, arcname)

            files_processed += 1

            # CALL CALLBACK HERE:
            if progress_callback:
                progress_callback(files_processed, total_files, arcname)

    # ... rest of code ...
```

---

### File: `app/watch_folder.py`

```python
# ADD THESE FUNCTIONS:

def get_folder_info(folder_path: str) -> dict:
    """
    Get information about a folder.

    Args:
        folder_path: Path to folder

    Returns:
        Dictionary with folder information:
        {
            'file_count': int,
            'total_size': int,
            'folder_path': str
        }
    """
    import os

    file_count = 0
    total_size = 0

    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)

    return {
        'file_count': file_count,
        'total_size': total_size,
        'folder_path': folder_path
    }


def format_settle_time(seconds: int) -> str:
    """
    Format settle time in human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "30s", "2m 30s", "1h 30m")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"


# FIX TIMEOUT BEHAVIOR:
def watch_folder_until_stable(
    folder_path: str,
    settle_time_seconds: int = 30,
    max_wait_seconds: int = 3600,
    progress_callback: Optional[Callable[[int, int, Dict], None]] = None
) -> bool:
    # ... existing code ...

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time

        # CHECK TIMEOUT FIRST:
        if elapsed >= max_wait_seconds:
            return False  # RETURN FALSE ON TIMEOUT

        # ... rest of logic ...
```

---

## Expected Results After Fixes

```
=== Week 5 Test Results ===

ZIP_ENGINE: 19/19 
WATCH_FOLDER: 22/22 
PROTOOLS: 16/16 

Total Week 5 Tests: 57/57 passed (100.0%)

 ALL WEEK 5 TESTS PASSED! 

Week 5 is fully validated and ready for production!
```

---

## Time Estimate

| Phase | Task | Time |
|-------|------|------|
| 1 | Fix ZIP Engine | 30-45 min |
| 2 | Fix Watch Folder | 20-30 min |
| 3 | Verify & Document | 10-15 min |
| **Total** | **All fixes** | **60-90 min** |

---

## Success Criteria

-  All 57 Week 5 tests passing (100%)
-  No TypeError or KeyError exceptions
-  Progress callbacks working correctly
-  Timeout behavior correct
-  Empty folder handling robust
-  Validation script shows 57/57 

---

**Next Step:** Start Phase 1 (Fix ZIP Engine) immediately.
