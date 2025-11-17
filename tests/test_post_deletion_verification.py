"""
Ketter 3.0 - Post-Deletion Verification Tests
ENHANCE #4: Verify destination readable before deleting source in MOVE mode

Tests verify that destination files/folders are actually readable
before deleting the source, protecting against:
- Filesystem corruption after copy
- Permission issues at destination
- Failed unzip operations
- Inaccessible mount points
"""

import pytest
import os
import tempfile
from pathlib import Path

from app.core.copy_engine import (
    verify_destination_readable,
    CopyEngineError
)


# ============================================
# TEST 1: File Verification - Success Cases
# ============================================

def test_verify_file_success():
    """
    Verify that a valid destination file passes verification
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test content" * 1000)  # 12KB file
        tmp_path = tmp.name
        file_size = tmp.tell()

    try:
        # Should not raise
        result = verify_destination_readable(tmp_path, is_folder=False, file_size=file_size)
        assert result is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_large_file_success():
    """
    Verify that a large destination file passes verification
    (tests first and last KB read)
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Write 2MB file
        tmp.write(b"A" * (2 * 1024 * 1024))
        tmp_path = tmp.name
        file_size = tmp.tell()

    try:
        result = verify_destination_readable(tmp_path, is_folder=False, file_size=file_size)
        assert result is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================
# TEST 2: Folder Verification - Success Cases
# ============================================

def test_verify_folder_success():
    """
    Verify that a valid destination folder passes verification
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files in folder
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "file2.txt")

        with open(file1, 'w') as f:
            f.write("Content 1")
        with open(file2, 'w') as f:
            f.write("Content 2")

        # Should not raise
        result = verify_destination_readable(tmpdir, is_folder=True, file_size=0)
        assert result is True


def test_verify_folder_with_subdirs():
    """
    Verify folder with subdirectories passes verification
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subfolder with file
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)

        file1 = os.path.join(subdir, "file.txt")
        with open(file1, 'w') as f:
            f.write("Nested content")

        result = verify_destination_readable(tmpdir, is_folder=True, file_size=0)
        assert result is True


# ============================================
# TEST 3: File Verification - Failure Cases
# ============================================

def test_verify_file_not_exists():
    """
    SECURITY: Verify that missing file raises error
    """
    with pytest.raises(CopyEngineError) as exc_info:
        verify_destination_readable("/tmp/nonexistent_file_12345.txt", is_folder=False, file_size=100)

    assert "does not exist" in str(exc_info.value).lower()


def test_verify_file_size_mismatch():
    """
    SECURITY: Verify that file size mismatch raises error
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test content")
        tmp_path = tmp.name
        actual_size = tmp.tell()

    try:
        # Claim file should be larger than it is
        with pytest.raises(CopyEngineError) as exc_info:
            verify_destination_readable(tmp_path, is_folder=False, file_size=actual_size + 1000)

        assert "size mismatch" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_file_is_actually_folder():
    """
    SECURITY: Verify that folder passed as file raises error
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(CopyEngineError) as exc_info:
            verify_destination_readable(tmpdir, is_folder=False, file_size=0)

        assert "not a file" in str(exc_info.value).lower()


# ============================================
# TEST 4: Folder Verification - Failure Cases
# ============================================

def test_verify_folder_not_exists():
    """
    SECURITY: Verify that missing folder raises error
    """
    with pytest.raises(CopyEngineError) as exc_info:
        verify_destination_readable("/tmp/nonexistent_folder_12345", is_folder=True, file_size=0)

    assert "does not exist" in str(exc_info.value).lower()


def test_verify_folder_is_empty():
    """
    SECURITY: Verify that empty folder raises error (unzip failed?)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty folder
        with pytest.raises(CopyEngineError) as exc_info:
            verify_destination_readable(tmpdir, is_folder=True, file_size=0)

        assert "empty" in str(exc_info.value).lower()


def test_verify_folder_is_actually_file():
    """
    SECURITY: Verify that file passed as folder raises error
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test")
        tmp_path = tmp.name

    try:
        with pytest.raises(CopyEngineError) as exc_info:
            verify_destination_readable(tmp_path, is_folder=True, file_size=0)

        assert "not a folder" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================
# TEST 5: Permission/Readability Tests
# ============================================

@pytest.mark.skipif(os.name == 'nt', reason="Permission tests not reliable on Windows")
def test_verify_file_unreadable():
    """
    SECURITY: Verify that unreadable file raises error
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Secret content")
        tmp_path = tmp.name
        file_size = tmp.tell()

    try:
        # Remove read permission
        os.chmod(tmp_path, 0o000)

        with pytest.raises(CopyEngineError) as exc_info:
            verify_destination_readable(tmp_path, is_folder=False, file_size=file_size)

        assert "cannot read" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()
    finally:
        # Restore permission and cleanup
        os.chmod(tmp_path, 0o644)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.skipif(os.name == 'nt', reason="Permission tests not reliable on Windows")
def test_verify_folder_unreadable():
    """
    SECURITY: Verify that unreadable folder raises error
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file inside
        file1 = os.path.join(tmpdir, "file.txt")
        with open(file1, 'w') as f:
            f.write("Content")

        try:
            # Remove read permission from folder
            os.chmod(tmpdir, 0o000)

            with pytest.raises(CopyEngineError) as exc_info:
                verify_destination_readable(tmpdir, is_folder=True, file_size=0)

            assert "permission" in str(exc_info.value).lower() or "cannot read" in str(exc_info.value).lower()
        finally:
            # Restore permission
            os.chmod(tmpdir, 0o755)


# ============================================
# TEST 6: Edge Cases
# ============================================

def test_verify_small_file():
    """
    Verify that files smaller than 1KB are handled correctly
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Small")  # 5 bytes
        tmp_path = tmp.name
        file_size = tmp.tell()

    try:
        # Should not crash trying to read last 1KB of 5-byte file
        result = verify_destination_readable(tmp_path, is_folder=False, file_size=file_size)
        assert result is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_exactly_1kb_file():
    """
    Verify that exactly 1KB file is handled correctly
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"X" * 1024)  # Exactly 1KB
        tmp_path = tmp.name
        file_size = tmp.tell()

    try:
        result = verify_destination_readable(tmp_path, is_folder=False, file_size=file_size)
        assert result is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_folder_with_only_subdirs():
    """
    Verify folder that contains only subdirectories (no files at root level)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subdirectory (but no files at root)
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)

        # Put file inside subdir
        file1 = os.path.join(subdir, "file.txt")
        with open(file1, 'w') as f:
            f.write("Nested")

        # Should still pass (has contents, even if just subdirs)
        result = verify_destination_readable(tmpdir, is_folder=True, file_size=0)
        assert result is True


# ============================================
# TEST 7: Integration Test
# ============================================

def test_verify_destination_before_delete_workflow():
    """
    Integration test: Simulate MOVE mode workflow
    1. Create source file
    2. Copy to destination
    3. Verify destination readable
    4. Delete source (simulated)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source
        source = os.path.join(tmpdir, "source.txt")
        with open(source, 'w') as f:
            f.write("Original data")

        source_size = os.path.getsize(source)

        # Copy to destination
        dest = os.path.join(tmpdir, "dest.txt")
        with open(source, 'rb') as src, open(dest, 'wb') as dst:
            dst.write(src.read())

        # Verify destination is readable (ENHANCE #4)
        result = verify_destination_readable(dest, is_folder=False, file_size=source_size)
        assert result is True

        # Now safe to delete source
        os.remove(source)

        # Verify source deleted and dest still readable
        assert not os.path.exists(source)
        assert os.path.exists(dest)


if __name__ == "__main__":
    # Run with: pytest tests/test_post_deletion_verification.py -v
    pytest.main([__file__, "-v", "-s"])
