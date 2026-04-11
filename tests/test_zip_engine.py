import os
import tempfile
import zipfile
import pytest
from app.core.zip_engine import (
    zip_folder_smart,
    unzip_folder_smart,
    validate_zip_integrity,
    get_zip_info,
    count_files_recursive,
    InvalidPathError,
    ZipEngineError
)

class TestZipValidation:
    def test_validate_zip_integrity_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid zip
            zip_path = os.path.join(tmpdir, "test.zip")
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("test.txt", "hello")
            
            is_valid, msg = validate_zip_integrity(zip_path)
            assert is_valid is True
            assert "valid" in msg.lower()

    def test_validate_zip_integrity_invalid_path(self):
        is_valid, msg = validate_zip_integrity("/nonexistent/path.zip")
        assert is_valid is False
        assert "not found" in msg.lower()

    def test_validate_zip_integrity_corrupted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a corrupted zip (just a text file)
            zip_path = os.path.join(tmpdir, "corrupted.zip")
            with open(zip_path, 'w') as f:
                f.write("This is not a zip file")
            
            is_valid, msg = validate_zip_integrity(zip_path)
            assert is_valid is False
            assert "invalid" in msg.lower() or "corrupted" in msg.lower() or "error" in msg.lower()

class TestZipEngine:
    def test_zip_folder_smart_progress_callback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = os.path.join(tmpdir, "source")
            os.makedirs(source)
            for i in range(3):
                with open(os.path.join(source, f"file{i}.txt"), "w") as f:
                    f.write(f"content {i}")
            
            zip_path = os.path.join(tmpdir, "output.zip")
            
            calls = []
            def progress(processed, total, current):
                calls.append((processed, total, current))
                
            zip_folder_smart(source, zip_path, progress_callback=progress)
            
            assert len(calls) == 3
            assert calls[-1][0] == 3
            assert calls[-1][1] == 3

    def test_unzip_folder_smart_progress_callback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = os.path.join(tmpdir, "source")
            os.makedirs(source)
            for i in range(3):
                with open(os.path.join(source, f"file{i}.txt"), "w") as f:
                    f.write(f"content {i}")
            
            zip_path = os.path.join(tmpdir, "output.zip")
            zip_folder_smart(source, zip_path)
            
            dest = os.path.join(tmpdir, "dest")
            os.makedirs(dest)
            
            calls = []
            def progress(processed, total, current):
                calls.append((processed, total, current))
                
            unzip_folder_smart(zip_path, dest, progress_callback=progress)
            
            assert len(calls) == 3
            assert calls[-1][0] == 3
            assert calls[-1][1] == 3
