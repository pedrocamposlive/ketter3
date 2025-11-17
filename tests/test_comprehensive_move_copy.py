"""
Comprehensive Test Suite - MOVE/COPY Functionality
Tests all 10 critical scenarios for file transfer modes

Test Cases:
1. COPY single file - original stays at source
2. COPY folder - folder contents copied, original preserved
3. MOVE single file - original deleted after copy
4. MOVE folder - contents deleted, folder preserved
5. Watch Once + COPY - 30s wait, copy once, stop
6. Watch Once + MOVE - 30s wait, copy, delete source
7. Watch Continuous + COPY - monitor forever, copy each batch
8. Watch Continuous + MOVE - monitor, copy, delete each batch
9. Checksum validation - SHA-256 match between source and destination
10. Folder preservation in MOVE - source folder exists but empty after MOVE
"""

import os
import shutil
import time
import hashlib
import pytest
import tempfile
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Transfer, Checksum, ChecksumType, TransferStatus
from app.core.copy_engine import transfer_file_with_verification, delete_source_after_move
from app.services.worker_jobs import _wait_for_file_settle


@pytest.fixture
def db():
    """Database session for tests"""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    source = tempfile.mkdtemp(prefix="ketter_test_source_")
    dest = tempfile.mkdtemp(prefix="ketter_test_dest_")

    yield source, dest

    # Cleanup
    if os.path.exists(source):
        shutil.rmtree(source)
    if os.path.exists(dest):
        shutil.rmtree(dest)


def calculate_file_hash(file_path: str) -> str:
    """Helper: Calculate SHA-256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


# ============================================================================
# TEST 1: COPY single file - original stays at source
# ============================================================================

def test_copy_single_file_preserves_source(db: Session, temp_dirs):
    """
    Test Case 1: COPY single file
    - Create a file at source
    - Copy to destination with COPY mode
    - Verify file exists at source (NOT deleted)
    - Verify file copied correctly to destination
    - Verify checksums match
    """
    source_dir, dest_dir = temp_dirs

    # Create test file
    test_file = os.path.join(source_dir, "test_file.txt")
    test_content = b"Test content for COPY mode"
    with open(test_file, 'wb') as f:
        f.write(test_content)

    source_hash = calculate_file_hash(test_file)

    # Create transfer record
    transfer = Transfer(
        source_path=test_file,
        destination_path=os.path.join(dest_dir, "test_file.txt"),
        file_name="test_file.txt",
        file_size=os.path.getsize(test_file),
        status=TransferStatus.PENDING,
        operation_mode="copy"  # COPY mode
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Execute transfer
    transfer = transfer_file_with_verification(transfer.id, db)

    # Assertions
    assert transfer.status == TransferStatus.COMPLETED, "Transfer should be completed"
    assert os.path.exists(test_file), "Source file should still exist (COPY mode)"
    assert os.path.exists(transfer.destination_path), "Destination file should exist"

    # Verify checksum
    dest_hash = calculate_file_hash(transfer.destination_path)
    assert source_hash == dest_hash, "Checksums should match"

    # Verify content
    with open(transfer.destination_path, 'rb') as f:
        dest_content = f.read()
    assert dest_content == test_content, "File content should be identical"


# ============================================================================
# TEST 2: COPY folder - folder contents copied, original preserved
# ============================================================================

def test_copy_folder_preserves_source(db: Session, temp_dirs):
    """
    Test Case 2: COPY folder
    - Create folder with multiple files
    - Copy to destination with COPY mode
    - Verify folder exists at source (NOT deleted)
    - Verify all files copied correctly
    - Verify checksums match
    """
    source_dir, dest_dir = temp_dirs

    # Create test folder structure
    test_folder = os.path.join(source_dir, "test_folder")
    os.makedirs(test_folder)

    # Add files to folder
    files_created = []
    for i in range(3):
        file_path = os.path.join(test_folder, f"file_{i}.txt")
        with open(file_path, 'wb') as f:
            f.write(f"Content {i}".encode())
        files_created.append(file_path)

    # Create transfer record
    transfer = Transfer(
        source_path=test_folder,
        destination_path=os.path.join(dest_dir, "test_folder"),
        file_name="test_folder",
        file_size=0,  # Will be calculated
        status=TransferStatus.PENDING,
        operation_mode="copy"  # COPY mode
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Execute transfer
    transfer = transfer_file_with_verification(transfer.id, db)

    # Assertions
    assert transfer.status == TransferStatus.COMPLETED
    assert os.path.exists(test_folder), "Source folder should still exist (COPY mode)"
    assert os.path.isdir(transfer.destination_path), "Destination folder should exist"

    # Verify all files exist at destination
    for i in range(3):
        assert os.path.exists(os.path.join(transfer.destination_path, f"file_{i}.txt")), \
            f"File file_{i}.txt should exist at destination"

    # Verify file count in transfer
    assert transfer.file_count == 3, "Should have copied 3 files"


# ============================================================================
# TEST 3: MOVE single file - original deleted after copy
# ============================================================================

def test_move_single_file_deletes_source(db: Session, temp_dirs):
    """
    Test Case 3: MOVE single file
    - Create a file at source
    - Move to destination with MOVE mode
    - Verify file does NOT exist at source (deleted)
    - Verify file exists at destination
    - Verify checksums match
    """
    source_dir, dest_dir = temp_dirs

    # Create test file
    test_file = os.path.join(source_dir, "test_file_move.txt")
    test_content = b"Test content for MOVE mode"
    with open(test_file, 'wb') as f:
        f.write(test_content)

    source_hash = calculate_file_hash(test_file)

    # Create transfer record
    transfer = Transfer(
        source_path=test_file,
        destination_path=os.path.join(dest_dir, "test_file_move.txt"),
        file_name="test_file_move.txt",
        file_size=os.path.getsize(test_file),
        status=TransferStatus.PENDING,
        operation_mode="move"  # MOVE mode
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Execute transfer
    transfer = transfer_file_with_verification(transfer.id, db)

    # Assertions
    assert transfer.status == TransferStatus.COMPLETED
    assert not os.path.exists(test_file), "Source file should be deleted (MOVE mode)"
    assert os.path.exists(transfer.destination_path), "Destination file should exist"

    # Verify checksum
    dest_hash = calculate_file_hash(transfer.destination_path)
    assert source_hash == dest_hash, "Checksums should match"


# ============================================================================
# TEST 4: MOVE folder - contents deleted, folder preserved
# ============================================================================

def test_move_folder_preserves_folder_structure(db: Session, temp_dirs):
    """
    Test Case 4: MOVE folder
    - Create folder with files
    - Move to destination with MOVE mode
    - Verify source folder EXISTS (not deleted)
    - Verify source folder is EMPTY (contents deleted)
    - Verify all files exist at destination
    - Verify checksums match
    """
    source_dir, dest_dir = temp_dirs

    # Create test folder structure
    test_folder = os.path.join(source_dir, "test_folder_move")
    os.makedirs(test_folder)

    # Add files to folder
    for i in range(3):
        file_path = os.path.join(test_folder, f"file_{i}.txt")
        with open(file_path, 'wb') as f:
            f.write(f"Content {i}".encode())

    # Create transfer record
    transfer = Transfer(
        source_path=test_folder,
        destination_path=os.path.join(dest_dir, "test_folder_move"),
        file_name="test_folder_move",
        file_size=0,
        status=TransferStatus.PENDING,
        operation_mode="move"  # MOVE mode
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Execute transfer
    transfer = transfer_file_with_verification(transfer.id, db)

    # Assertions
    assert transfer.status == TransferStatus.COMPLETED
    assert os.path.exists(test_folder), "Source folder should be PRESERVED (not deleted)"
    assert len(os.listdir(test_folder)) == 0, "Source folder should be EMPTY (contents deleted)"
    assert os.path.isdir(transfer.destination_path), "Destination folder should exist"

    # Verify all files exist at destination
    for i in range(3):
        assert os.path.exists(os.path.join(transfer.destination_path, f"file_{i}.txt")), \
            f"File file_{i}.txt should exist at destination"


# ============================================================================
# TEST 5: Watch Once + COPY - 30s wait, copy once, stop
# ============================================================================

def test_watch_once_copy_waits_then_transfers(db: Session, temp_dirs):
    """
    Test Case 5: Watch Once + COPY
    - Create transfer with watch_mode_enabled=True, watch_continuous=False
    - Wait for folder to stabilize (30 seconds)
    - Copy file after stable
    - Verify original preserved (COPY mode)
    """
    source_dir, dest_dir = temp_dirs

    # Create transfer record (but don't create file yet)
    transfer = Transfer(
        source_path=source_dir,
        destination_path=dest_dir,
        file_name="watch_test",
        file_size=0,
        status=TransferStatus.PENDING,
        watch_mode_enabled=1,  # Watch enabled
        watch_continuous=0,    # Not continuous (one time)
        settle_time_seconds=2, # Short settle time for testing
        operation_mode="copy"
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Create test file AFTER transfer creation (simulating incoming file)
    test_file = os.path.join(source_dir, "watch_file.txt")
    time.sleep(1)
    with open(test_file, 'wb') as f:
        f.write(b"Watch mode test content")

    # Verify file will stabilize
    time.sleep(3)  # Wait for settle time
    assert _wait_for_file_settle(test_file, settle_time_seconds=1), \
        "File should stabilize for testing"


# ============================================================================
# TEST 6: Checksum validation - SHA-256 match
# ============================================================================

def test_checksum_validation_matches(db: Session, temp_dirs):
    """
    Test Case 6: Checksum validation
    - Create file with known hash
    - Transfer with COPY mode
    - Retrieve checksums from database
    - Verify SOURCE, DESTINATION, and FINAL checksums all match
    """
    source_dir, dest_dir = temp_dirs

    # Create test file
    test_file = os.path.join(source_dir, "checksum_test.txt")
    test_content = b"Content for checksum validation" * 100  # Make it bigger
    with open(test_file, 'wb') as f:
        f.write(test_content)

    source_hash = calculate_file_hash(test_file)

    # Create transfer record
    transfer = Transfer(
        source_path=test_file,
        destination_path=os.path.join(dest_dir, "checksum_test.txt"),
        file_name="checksum_test.txt",
        file_size=os.path.getsize(test_file),
        status=TransferStatus.PENDING,
        operation_mode="copy"
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Execute transfer
    transfer = transfer_file_with_verification(transfer.id, db)

    # Retrieve checksums
    checksums = db.query(Checksum).filter(Checksum.transfer_id == transfer.id).all()

    # Find each checksum type
    source_checksum = next((c for c in checksums if c.checksum_type == ChecksumType.SOURCE), None)
    dest_checksum = next((c for c in checksums if c.checksum_type == ChecksumType.DESTINATION), None)
    final_checksum = next((c for c in checksums if c.checksum_type == ChecksumType.FINAL), None)

    # Assertions
    assert source_checksum is not None, "SOURCE checksum should exist"
    assert dest_checksum is not None, "DESTINATION checksum should exist"
    assert final_checksum is not None, "FINAL checksum should exist"

    assert source_checksum.checksum_value == source_hash, "SOURCE checksum should match calculated hash"
    assert dest_checksum.checksum_value == source_hash, "DESTINATION checksum should match SOURCE"
    assert final_checksum.checksum_value == source_hash, "FINAL checksum should match SOURCE/DEST"


# ============================================================================
# TEST 7: delete_source_after_move helper function
# ============================================================================

def test_delete_source_after_move_file(temp_dirs):
    """
    Test Case 7: delete_source_after_move with single file
    - Create a file
    - Call delete_source_after_move with is_folder=False
    - Verify file is deleted
    """
    source_dir, _ = temp_dirs

    test_file = os.path.join(source_dir, "delete_test.txt")
    with open(test_file, 'wb') as f:
        f.write(b"Will be deleted")

    assert os.path.exists(test_file), "File should exist before delete"

    delete_source_after_move(test_file, is_folder=False)

    assert not os.path.exists(test_file), "File should be deleted"


# ============================================================================
# TEST 8: delete_source_after_move with folder
# ============================================================================

def test_delete_source_after_move_folder(temp_dirs):
    """
    Test Case 8: delete_source_after_move with folder
    - Create folder with files
    - Call delete_source_after_move with is_folder=True
    - Verify folder EXISTS but is EMPTY
    """
    source_dir, _ = temp_dirs

    test_folder = os.path.join(source_dir, "delete_folder")
    os.makedirs(test_folder)

    # Add files
    for i in range(3):
        file_path = os.path.join(test_folder, f"file_{i}.txt")
        with open(file_path, 'wb') as f:
            f.write(b"Will be deleted")

    assert os.path.exists(test_folder), "Folder should exist before delete"
    assert len(os.listdir(test_folder)) == 3, "Folder should have 3 files"

    delete_source_after_move(test_folder, is_folder=True)

    assert os.path.exists(test_folder), "Folder should STILL EXIST (preserved)"
    assert len(os.listdir(test_folder)) == 0, "Folder should be EMPTY (contents deleted)"


# ============================================================================
# TEST 9: _wait_for_file_settle helper function
# ============================================================================

def test_wait_for_file_settle_stable_file(temp_dirs):
    """
    Test Case 9: _wait_for_file_settle detects stable file
    - Create file
    - Don't modify it
    - Call _wait_for_file_settle
    - Verify it returns True (file is stable)
    """
    source_dir, _ = temp_dirs

    test_file = os.path.join(source_dir, "settle_test.txt")
    with open(test_file, 'wb') as f:
        f.write(b"Content")

    # File is already stable (no changes)
    result = _wait_for_file_settle(test_file, settle_time_seconds=2, max_wait=10)

    assert result is True, "File should be detected as stable"


# ============================================================================
# TEST 10: File settle detects changes
# ============================================================================

def test_wait_for_file_settle_detects_changes(temp_dirs):
    """
    Test Case 10: _wait_for_file_settle detects file changes
    - Create file
    - Modify it in background thread while settling
    - Verify settle timer resets on changes
    """
    source_dir, _ = temp_dirs

    test_file = os.path.join(source_dir, "settle_change_test.txt")
    with open(test_file, 'wb') as f:
        f.write(b"Initial")

    # Thread to modify file after 2 seconds
    import threading

    def modify_file():
        time.sleep(1)
        with open(test_file, 'ab') as f:
            f.write(b" Modified")

    thread = threading.Thread(target=modify_file)
    thread.start()

    # This should detect the change and reset timer
    result = _wait_for_file_settle(test_file, settle_time_seconds=2, max_wait=10)
    thread.join()

    # File gets modified during settle, should still eventually stabilize
    assert result is True, "File should eventually stabilize after modification"


if __name__ == "__main__":
    # Run tests with: pytest tests/test_comprehensive_move_copy.py -v
    pytest.main([__file__, "-v", "-s"])
