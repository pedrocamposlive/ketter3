#!/usr/bin/env python3
"""
 Ketter 3.0 - Watch Mode Contínuo Integration Test

Tests Watch Mode Contínuo with two operational profiles:
1. COPY Mode: Transfer files, keep originals at source
2. MOVE Mode: Transfer files, delete originals after verification

This script:
- Creates two transfer profiles via API
- Tests file detection and transfer
- Verifies checksum integrity
- Tests pause/resume functionality
- Validates operational differences (COPY vs MOVE)

Date: 2025-11-11
Status: Integration Testing - FASE 4
"""

import os
import sys
import json
import time
import shutil
import hashlib
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================
# Configuration
# ============================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 10
POLL_INTERVAL = 2
MAX_POLLS = 30  # 60 seconds max wait

# Test data directories (use /tmp inside container, accessible across platforms)
TEST_BASE_DIR = "/tmp/ketter_watch_mode_test"
COPY_MODE_SOURCE = f"{TEST_BASE_DIR}/copy_mode/source"
COPY_MODE_DEST = f"{TEST_BASE_DIR}/copy_mode/dest"
MOVE_MODE_SOURCE = f"{TEST_BASE_DIR}/move_mode/source"
MOVE_MODE_DEST = f"{TEST_BASE_DIR}/move_mode/dest"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# ============================================
# Utility Functions
# ============================================

def log_info(msg: str):
    """Log info message"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def log_success(msg: str):
    """Log success message"""
    print(f"{Colors.GREEN} {msg}{Colors.RESET}")

def log_error(msg: str):
    """Log error message"""
    print(f"{Colors.RED} {msg}{Colors.RESET}")

def log_warning(msg: str):
    """Log warning message"""
    print(f"{Colors.YELLOW} {msg}{Colors.RESET}")

def log_header(msg: str):
    """Log section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def log_subheader(msg: str):
    """Log subsection header"""
    print(f"\n{Colors.CYAN}→ {msg}{Colors.RESET}")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def setup_test_directories():
    """Create and prepare test directories"""
    log_subheader("Setting up test directories")

    # Clean up old test data
    if os.path.exists(TEST_BASE_DIR):
        shutil.rmtree(TEST_BASE_DIR)
        log_info("Cleaned old test data")

    # Create directories
    for path in [COPY_MODE_SOURCE, COPY_MODE_DEST, MOVE_MODE_SOURCE, MOVE_MODE_DEST]:
        os.makedirs(path, exist_ok=True)

    log_success(f"Test directories created in {TEST_BASE_DIR}")

def create_test_file(path: str, size_kb: int = 10) -> str:
    """
    Create a test file with specific size
    Returns: file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(os.urandom(size_kb * 1024))
    return path

def get_files_in_directory(directory: str) -> set:
    """Get set of file paths in a directory"""
    if not os.path.exists(directory):
        return set()
    return set(os.path.basename(f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)))


# ============================================
# API Helper Functions
# ============================================

class APIClient:
    """Simple HTTP client for Ketter API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def post(self, endpoint: str, data: Dict) -> Tuple[int, Dict]:
        """POST request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            return response.status_code, response.json()
        except Exception as e:
            log_error(f"API POST error: {e}")
            return 0, {"error": str(e)}

    def get(self, endpoint: str) -> Tuple[int, Dict]:
        """GET request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            return response.status_code, response.json()
        except Exception as e:
            log_error(f"API GET error: {e}")
            return 0, {"error": str(e)}

    def patch(self, endpoint: str, data: Dict) -> Tuple[int, Dict]:
        """PATCH request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.patch(url, json=data, timeout=TIMEOUT)
            return response.status_code, response.json()
        except Exception as e:
            log_error(f"API PATCH error: {e}")
            return 0, {"error": str(e)}


# ============================================
# Test Profiles
# ============================================

class TransferTestProfile:
    """Represents a transfer test scenario"""

    def __init__(self, name: str, source: str, dest: str, operation_mode: str = "copy"):
        self.name = name
        self.source_path = source
        self.dest_path = dest
        self.operation_mode = operation_mode  # "copy" or "move"
        self.transfer_id: Optional[int] = None
        self.watch_job_id: Optional[str] = None
        self.test_files: List[str] = []
        self.checksums: Dict[str, str] = {}
        self.client = APIClient()

        # Ensure source and dest directories exist
        os.makedirs(self.source_path, exist_ok=True)
        os.makedirs(self.dest_path, exist_ok=True)

    def create_transfer(self) -> bool:
        """Create a watch mode transfer via API"""
        log_subheader(f"Creating {self.operation_mode.upper()} mode transfer: {self.name}")

        payload = {
            "source_path": self.source_path,
            "destination_path": self.dest_path,
            "watch_mode_enabled": True,
            "settle_time_seconds": 5,  # Short settle time for testing (minimum required)
            "watch_continuous": True,
            "operation_mode": self.operation_mode  # Custom field for COPY/MOVE
        }

        log_info(f"Creating transfer with payload:")
        log_info(f"  Source: {self.source_path}")
        log_info(f"  Dest: {self.dest_path}")
        log_info(f"  Mode: {self.operation_mode.upper()}")
        log_info(f"  Watch: continuous")

        status, response = self.client.post("/transfers", payload)

        if status == 201:
            self.transfer_id = response.get("id")
            self.watch_job_id = response.get("watch_job_id")
            log_success(f"Transfer created: ID={self.transfer_id}, Job={self.watch_job_id}")
            return True
        else:
            log_error(f"Failed to create transfer: {status} - {response}")
            return False

    def get_transfer_status(self) -> Dict:
        """Get current transfer status from API"""
        if not self.transfer_id:
            return {}
        status, response = self.client.get(f"/transfers/{self.transfer_id}")
        if status == 200:
            return response
        return {}

    def get_watch_history(self) -> Dict:
        """Get watch file history"""
        if not self.transfer_id:
            return {}
        status, response = self.client.get(f"/transfers/{self.transfer_id}/watch-history")
        if status == 200:
            return response
        return {}

    def pause_watch(self) -> bool:
        """Pause watch mode"""
        if not self.transfer_id:
            return False
        log_subheader(f"Pausing watch mode for transfer {self.transfer_id}")
        status, response = self.client.post(f"/transfers/{self.transfer_id}/pause-watch", {})
        if status == 200:
            log_success("Watch mode paused")
            return True
        else:
            log_error(f"Failed to pause: {status} - {response}")
            return False

    def resume_watch(self) -> bool:
        """Resume watch mode"""
        if not self.transfer_id:
            return False
        log_subheader(f"Resuming watch mode for transfer {self.transfer_id}")
        status, response = self.client.post(f"/transfers/{self.transfer_id}/resume-watch", {})
        if status == 200:
            log_success("Watch mode resumed")
            return True
        else:
            log_error(f"Failed to resume: {status} - {response}")
            return False

    def add_test_files(self, count: int = 3, size_kb: int = 50) -> List[str]:
        """Add test files to source directory"""
        log_subheader(f"Adding {count} test files to {self.name}")

        files = []
        for i in range(count):
            filename = f"test_file_{i+1:02d}_{datetime.now().strftime('%s')}.dat"
            filepath = os.path.join(self.source_path, filename)
            create_test_file(filepath, size_kb)
            files.append(filename)
            self.checksums[filename] = calculate_sha256(filepath)
            log_info(f"  Created: {filename} ({size_kb}KB)")

        self.test_files.extend(files)
        return files

    def wait_for_detection(self, expected_files: int = None, timeout: int = 60) -> bool:
        """Wait for files to be detected by watch mode"""
        if expected_files is None:
            expected_files = len(self.test_files)

        log_subheader(f"Waiting for {expected_files} files to be detected (timeout: {timeout}s)")

        start_time = time.time()
        polls = 0

        while time.time() - start_time < timeout:
            history = self.get_watch_history()
            detected_count = history.get("total_files_detected", 0)
            completed_count = history.get("total_files_completed", 0)

            log_info(f"  Poll #{polls+1}: Detected={detected_count}, Completed={completed_count}")

            if completed_count >= expected_files:
                log_success(f"All {expected_files} files detected and transferred!")
                return True

            polls += 1
            time.sleep(POLL_INTERVAL)

        log_error(f"Timeout waiting for file detection")
        return False

    def verify_files_transferred(self) -> bool:
        """Verify files were transferred to destination"""
        log_subheader(f"Verifying file transfers for {self.name}")

        if not os.path.exists(self.dest_path):
            log_error(f"Destination path does not exist: {self.dest_path}")
            return False

        dest_files = get_files_in_directory(self.dest_path)

        if len(dest_files) == 0:
            log_error("No files found in destination")
            return False

        all_verified = True
        for filename in self.test_files:
            if filename in dest_files:
                log_success(f"   {filename} transferred")
            else:
                log_error(f"   {filename} NOT in destination")
                all_verified = False

        return all_verified

    def verify_source_files(self, should_exist: bool) -> bool:
        """
        Verify source files exist or don't exist
        should_exist=True for COPY mode, False for MOVE mode
        """
        log_subheader(f"Verifying source files for {self.operation_mode.upper()} mode")

        source_files = get_files_in_directory(self.source_path)

        all_verified = True
        for filename in self.test_files:
            exists = filename in source_files

            if should_exist and exists:
                log_success(f"   {filename} still in source (COPY mode)")
            elif should_exist and not exists:
                log_error(f"   {filename} missing from source (should exist in COPY mode)")
                all_verified = False
            elif not should_exist and not exists:
                log_success(f"   {filename} deleted from source (MOVE mode)")
            elif not should_exist and exists:
                log_error(f"   {filename} still in source (should be deleted in MOVE mode)")
                all_verified = False

        return all_verified

    def verify_checksums(self) -> bool:
        """Verify checksums match between source and destination"""
        log_subheader(f"Verifying checksums for {self.name}")

        all_match = True
        for filename in self.test_files:
            dest_filepath = os.path.join(self.dest_path, filename)

            if not os.path.exists(dest_filepath):
                log_error(f"   {filename} not found in destination")
                all_match = False
                continue

            dest_checksum = calculate_sha256(dest_filepath)
            source_checksum = self.checksums.get(filename, "unknown")

            if source_checksum == dest_checksum:
                log_success(f"   {filename} checksum verified")
            else:
                log_error(f"   {filename} checksum mismatch!")
                log_error(f"    Source: {source_checksum}")
                log_error(f"    Dest:   {dest_checksum}")
                all_match = False

        return all_match

    def get_watch_cycle_count(self) -> int:
        """Get current watch cycle count"""
        transfer = self.get_transfer_status()
        return transfer.get("watch_cycle_count", 0)


# ============================================
# Test Scenarios
# ============================================

def test_api_health(client: APIClient) -> bool:
    """Verify API is running and healthy"""
    log_subheader("Checking API health")

    status, response = client.get("/health")
    if status == 200:
        log_success("API is healthy and running")
        return True
    else:
        log_error(f"API is not responding: {status}")
        return False

def test_copy_mode() -> bool:
    """Test COPY mode: files stay at source after transfer"""
    log_header("TEST SCENARIO 1: COPY MODE")
    log_info("Files transferred to destination, originals remain at source")

    profile = TransferTestProfile(
        name="COPY Mode Profile",
        source=COPY_MODE_SOURCE,
        dest=COPY_MODE_DEST,
        operation_mode="copy"
    )

    # Create transfer
    if not profile.create_transfer():
        return False

    time.sleep(2)  # Let watch job start

    # Add test files
    profile.add_test_files(count=3, size_kb=50)

    # Wait for detection and transfer
    if not profile.wait_for_detection(expected_files=3, timeout=60):
        return False

    time.sleep(5)  # Allow transfer to complete

    # Verify transfers
    if not profile.verify_files_transferred():
        return False

    # Verify source files STILL EXIST (COPY mode)
    if not profile.verify_source_files(should_exist=True):
        return False

    # Verify checksums
    if not profile.verify_checksums():
        return False

    log_success(" COPY MODE TEST PASSED")
    return True

def test_move_mode() -> bool:
    """Test MOVE mode: files deleted from source after transfer"""
    log_header("TEST SCENARIO 2: MOVE MODE")
    log_info("Files transferred to destination, originals deleted from source")

    profile = TransferTestProfile(
        name="MOVE Mode Profile",
        source=MOVE_MODE_SOURCE,
        dest=MOVE_MODE_DEST,
        operation_mode="move"
    )

    # Create transfer
    if not profile.create_transfer():
        return False

    time.sleep(2)  # Let watch job start

    # Add test files
    profile.add_test_files(count=3, size_kb=50)

    # Wait for detection and transfer
    if not profile.wait_for_detection(expected_files=3, timeout=60):
        return False

    time.sleep(5)  # Allow transfer to complete and cleanup

    # Verify transfers
    if not profile.verify_files_transferred():
        return False

    # Verify source files ARE DELETED (MOVE mode)
    if not profile.verify_source_files(should_exist=False):
        return False

    # Verify checksums (compare from destination only)
    if not profile.verify_checksums():
        return False

    log_success(" MOVE MODE TEST PASSED")
    return True

def test_pause_resume() -> bool:
    """Test pause and resume functionality"""
    log_header("TEST SCENARIO 3: PAUSE/RESUME")
    log_info("Test pause watch mode, add files (not detected), resume, verify detection")

    profile = TransferTestProfile(
        name="Pause/Resume Profile",
        source=f"{TEST_BASE_DIR}/pause_resume/source",
        dest=f"{TEST_BASE_DIR}/pause_resume/dest",
        operation_mode="copy"
    )

    # Create transfer
    if not profile.create_transfer():
        return False

    time.sleep(2)

    # Add initial files
    initial_files = profile.add_test_files(count=2, size_kb=30)

    # Wait for initial detection
    if not profile.wait_for_detection(expected_files=2, timeout=30):
        return False

    initial_cycle_count = profile.get_watch_cycle_count()
    log_info(f"Initial watch cycles: {initial_cycle_count}")

    # Pause watch
    if not profile.pause_watch():
        return False

    time.sleep(3)

    # Add files while paused (should NOT be detected)
    profile.add_test_files(count=2, size_kb=30)
    time.sleep(5)

    paused_count = len(get_files_in_directory(profile.dest_path))
    log_info(f"Files in dest while paused: {paused_count}")

    if paused_count != 2:
        log_error(f"Files were detected during pause! Expected 2, got {paused_count}")
        return False
    else:
        log_success(" Files NOT detected while paused (correct)")

    # Resume watch
    if not profile.resume_watch():
        return False

    time.sleep(2)

    # Now the files should be detected
    if not profile.wait_for_detection(expected_files=4, timeout=30):
        return False

    log_success(" PAUSE/RESUME TEST PASSED")
    return True


# ============================================
# Main Test Runner
# ============================================

def main():
    """Run all integration tests"""

    log_header(" KETTER 3.0 - WATCH MODE CONTÍNUO INTEGRATION TEST")
    log_info(f"Test Base Directory: {TEST_BASE_DIR}")
    log_info(f"API Base URL: {API_BASE_URL}")
    log_info(f"Timestamp: {datetime.now().isoformat()}\n")

    # Setup
    setup_test_directories()

    # Initialize API client
    client = APIClient()

    # Test 0: API Health
    if not test_api_health(client):
        log_error("API is not ready. Cannot proceed with tests.")
        return 1

    # Run test scenarios
    results = {
        "API Health": True,
        "COPY Mode": False,
        "MOVE Mode": False,
        "Pause/Resume": False
    }

    try:
        results["COPY Mode"] = test_copy_mode()
        results["MOVE Mode"] = test_move_mode()
        results["Pause/Resume"] = test_pause_resume()
    except Exception as e:
        log_error(f"Test execution error: {e}")
        import traceback
        traceback.print_exc()

    # Report results
    log_header(" TEST RESULTS SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN} PASSED{Colors.RESET}" if result else f"{Colors.RED} FAILED{Colors.RESET}"
        print(f"  {test_name:.<40} {status}")

    print(f"\n  Total: {Colors.BOLD}{passed}/{total} tests passed{Colors.RESET}")

    # Cleanup summary
    log_header(" TEST DATA")
    log_info(f"Test data stored in: {TEST_BASE_DIR}")
    log_info("Data will be available for inspection. Use --cleanup to remove.")

    # Final status
    if passed == total:
        log_success("\n ALL TESTS PASSED! Watch Mode Contínuo is working correctly!")
        return 0
    else:
        log_error(f"\n {total - passed} test(s) failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
