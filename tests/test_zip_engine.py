"""
Ketter 3.0 - ZIP Smart Engine Tests
Week 5: Tests for folder packaging and unpacking with STORE mode

MRC: Simple, focused tests for ZIP Smart functionality
"""

import os
import pytest
import tempfile
import shutil
import zipfile
from pathlib import Path

from app.zip_engine import (
    is_directory,
    count_files_recursive,
    zip_folder_smart,
    unzip_folder_smart,
    validate_zip_integrity,
    format_file_count,
    estimate_zip_time,
    estimate_unzip_time
)


@pytest.fixture
def temp_folder():
    """Create a temporary folder for testing"""
    folder = tempfile.mkdtemp()
    yield folder
    shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture
def sample_folder_structure(temp_folder):
    """
    Create a sample folder structure for testing:
    /temp_folder/source
      /subfolder1
        file1.wav (1 MB)
        file2.wav (1 MB)
      /subfolder2
        file3.wav (1 MB)
      file4.wav (1 MB)
    Total: 4 files, 4 MB
    """
    # Create source folder inside temp_folder to avoid pollution
    source_folder = os.path.join(temp_folder, 'source')
    os.makedirs(source_folder)

    # Create subfolders
    subfolder1 = os.path.join(source_folder, 'subfolder1')
    subfolder2 = os.path.join(source_folder, 'subfolder2')
    os.makedirs(subfolder1)
    os.makedirs(subfolder2)

    # Create files (1 MB each)
    file_size = 1024 * 1024  # 1 MB
    files = [
        os.path.join(subfolder1, 'file1.wav'),
        os.path.join(subfolder1, 'file2.wav'),
        os.path.join(subfolder2, 'file3.wav'),
        os.path.join(source_folder, 'file4.wav')
    ]

    for file_path in files:
        with open(file_path, 'wb') as f:
            f.write(b'0' * file_size)

    return source_folder


class TestZipEngineBasics:
    """Test basic ZIP engine utilities"""

    def test_is_directory_with_folder(self, sample_folder_structure):
        """Test is_directory returns True for folders"""
        assert is_directory(sample_folder_structure) is True

    def test_is_directory_with_file(self, temp_folder):
        """Test is_directory returns False for files"""
        test_file = os.path.join(temp_folder, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')

        assert is_directory(test_file) is False

    def test_count_files_recursive(self, sample_folder_structure):
        """Test count_files_recursive counts all files and calculates size"""
        file_count, total_size = count_files_recursive(sample_folder_structure)

        assert file_count == 4
        assert total_size == 4 * 1024 * 1024  # 4 MB

    def test_count_files_empty_folder(self, temp_folder):
        """Test count_files_recursive with empty folder"""
        file_count, total_size = count_files_recursive(temp_folder)

        assert file_count == 0
        assert total_size == 0


class TestZipFolderSmart:
    """Test ZIP Smart folder packaging"""

    def test_zip_folder_basic(self, sample_folder_structure, temp_folder):
        """Test basic ZIP creation with STORE mode"""
        zip_path = os.path.join(temp_folder, 'test.zip')

        result = zip_folder_smart(sample_folder_structure, zip_path)

        # Verify ZIP was created
        assert os.path.exists(zip_path)
        assert result == zip_path

        # Verify it's a valid ZIP file
        assert zipfile.is_zipfile(zip_path)

    def test_zip_folder_store_mode(self, sample_folder_structure, temp_folder):
        """Test that ZIP uses STORE mode (no compression)"""
        zip_path = os.path.join(temp_folder, 'test.zip')

        zip_folder_smart(sample_folder_structure, zip_path)

        # Open and verify all files use STORE mode
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for info in zipf.infolist():
                if not info.is_dir():  # Skip directories
                    assert info.compress_type == zipfile.ZIP_STORED

    def test_zip_folder_preserves_structure(self, sample_folder_structure, temp_folder):
        """Test that ZIP preserves folder structure"""
        zip_path = os.path.join(temp_folder, 'test.zip')

        zip_folder_smart(sample_folder_structure, zip_path)

        # Verify all expected files are in ZIP
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            names = zipf.namelist()
            assert 'subfolder1/file1.wav' in names
            assert 'subfolder1/file2.wav' in names
            assert 'subfolder2/file3.wav' in names
            assert 'file4.wav' in names

    def test_zip_folder_progress_callback(self, sample_folder_structure, temp_folder):
        """Test that progress callback is called during zipping"""
        zip_path = os.path.join(temp_folder, 'test.zip')

        progress_calls = []

        def progress_callback(current, total, current_file):
            progress_calls.append({
                'current': current,
                'total': total,
                'file': current_file
            })

        zip_folder_smart(sample_folder_structure, zip_path, progress_callback=progress_callback)

        # Verify progress was tracked
        assert len(progress_calls) > 0
        assert progress_calls[-1]['current'] == progress_calls[-1]['total']  # Completed


class TestUnzipFolderSmart:
    """Test ZIP Smart folder unpacking"""

    def test_unzip_folder_basic(self, sample_folder_structure, temp_folder):
        """Test basic unzip functionality"""
        # Create ZIP first
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        # Unzip to new location
        unzip_dest = os.path.join(temp_folder, 'unzipped')
        result = unzip_folder_smart(zip_path, unzip_dest)

        # Verify unzip was successful
        assert result == unzip_dest
        assert os.path.exists(unzip_dest)

    def test_unzip_folder_preserves_structure(self, sample_folder_structure, temp_folder):
        """Test that unzip preserves folder structure"""
        # Create ZIP
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        # Unzip
        unzip_dest = os.path.join(temp_folder, 'unzipped')
        unzip_folder_smart(zip_path, unzip_dest)

        # Verify all files exist with correct structure
        assert os.path.exists(os.path.join(unzip_dest, 'subfolder1', 'file1.wav'))
        assert os.path.exists(os.path.join(unzip_dest, 'subfolder1', 'file2.wav'))
        assert os.path.exists(os.path.join(unzip_dest, 'subfolder2', 'file3.wav'))
        assert os.path.exists(os.path.join(unzip_dest, 'file4.wav'))

    def test_unzip_folder_file_sizes(self, sample_folder_structure, temp_folder):
        """Test that unzipped files have correct sizes"""
        # Create ZIP
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        # Unzip
        unzip_dest = os.path.join(temp_folder, 'unzipped')
        unzip_folder_smart(zip_path, unzip_dest)

        # Verify file sizes
        expected_size = 1024 * 1024  # 1 MB
        files_to_check = [
            os.path.join(unzip_dest, 'subfolder1', 'file1.wav'),
            os.path.join(unzip_dest, 'subfolder1', 'file2.wav'),
            os.path.join(unzip_dest, 'subfolder2', 'file3.wav'),
            os.path.join(unzip_dest, 'file4.wav')
        ]

        for file_path in files_to_check:
            assert os.path.getsize(file_path) == expected_size

    def test_unzip_folder_progress_callback(self, sample_folder_structure, temp_folder):
        """Test that progress callback is called during unzipping"""
        # Create ZIP
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        # Unzip with progress tracking
        unzip_dest = os.path.join(temp_folder, 'unzipped')
        progress_calls = []

        def progress_callback(current, total, current_file):
            progress_calls.append({
                'current': current,
                'total': total,
                'file': current_file
            })

        unzip_folder_smart(zip_path, unzip_dest, progress_callback=progress_callback)

        # Verify progress was tracked
        assert len(progress_calls) > 0
        assert progress_calls[-1]['current'] == progress_calls[-1]['total']  # Completed


class TestZipValidation:
    """Test ZIP integrity validation"""

    def test_validate_zip_integrity_valid(self, sample_folder_structure, temp_folder):
        """Test validation of a valid ZIP file"""
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        is_valid, message = validate_zip_integrity(zip_path)

        assert is_valid is True
        assert "valid" in message.lower()

    def test_validate_zip_integrity_corrupted(self, temp_folder):
        """Test validation of a corrupted ZIP file"""
        # Create a corrupted "ZIP" file
        zip_path = os.path.join(temp_folder, 'corrupted.zip')
        with open(zip_path, 'wb') as f:
            f.write(b'This is not a valid ZIP file')

        is_valid, message = validate_zip_integrity(zip_path)

        assert is_valid is False
        assert "error" in message.lower() or "invalid" in message.lower()

    def test_validate_zip_integrity_nonexistent(self, temp_folder):
        """Test validation of non-existent ZIP file"""
        zip_path = os.path.join(temp_folder, 'nonexistent.zip')

        is_valid, message = validate_zip_integrity(zip_path)

        assert is_valid is False
        assert "not found" in message.lower() or "does not exist" in message.lower()


class TestZipHelpers:
    """Test ZIP helper functions"""

    def test_format_file_count(self):
        """Test file count formatting"""
        assert format_file_count(1) == "1 file"
        assert format_file_count(10) == "10 files"
        assert format_file_count(1000) == "1,000 files"

    def test_estimate_zip_time(self):
        """Test ZIP time estimation"""
        # 1 GB at ~100 MB/s should take ~10 seconds
        estimated = estimate_zip_time(1024 * 1024 * 1024, 4)
        assert estimated > 0
        assert estimated < 30  # Should be reasonable

    def test_estimate_unzip_time(self):
        """Test unzip time estimation"""
        # 1 GB at ~150 MB/s should take ~7 seconds
        estimated = estimate_unzip_time(1024 * 1024 * 1024, 4)
        assert estimated > 0
        assert estimated < 20  # Should be reasonable


class TestZipEndToEnd:
    """End-to-end tests for complete ZIP Smart workflow"""

    def test_complete_zip_unzip_workflow(self, sample_folder_structure, temp_folder):
        """Test complete workflow: folder -> zip -> unzip -> verify"""
        # Step 1: ZIP folder
        zip_path = os.path.join(temp_folder, 'test.zip')
        zip_folder_smart(sample_folder_structure, zip_path)

        # Step 2: Validate ZIP
        is_valid, _ = validate_zip_integrity(zip_path)
        assert is_valid is True

        # Step 3: Unzip
        unzip_dest = os.path.join(temp_folder, 'unzipped')
        unzip_folder_smart(zip_path, unzip_dest)

        # Step 4: Verify all files match
        original_count, original_size = count_files_recursive(sample_folder_structure)
        unzipped_count, unzipped_size = count_files_recursive(unzip_dest)

        assert original_count == unzipped_count
        assert original_size == unzipped_size
