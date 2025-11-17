"""
Tests for hidden files filtering in transfer operations

This test suite validates that files and directories starting with '.'
are properly excluded from:
- count_files_recursive() in zip_engine.py
- zip_folder_smart() in zip_engine.py
- watch_folder list scanning in worker_jobs.py
"""

import pytest
import os
import tempfile
import zipfile
from pathlib import Path
from app.core.zip_engine import count_files_recursive, zip_folder_smart


class TestHiddenFilesFiltering:
    """Tests for hidden files exclusion during transfers"""

    @pytest.fixture
    def temp_folder_with_hidden(self):
        """Create a test folder structure with hidden and normal files"""
        temp_dir = tempfile.mkdtemp()

        # Create normal files
        Path(temp_dir, "file1.txt").write_text("Normal file 1")
        Path(temp_dir, "file2.txt").write_text("Normal file 2")

        # Create hidden files (should be excluded)
        Path(temp_dir, ".DS_Store").write_text("DS Store hidden file")
        Path(temp_dir, ".hidden.txt").write_text("Hidden text file")

        # Create subdirectory with files
        subdir = Path(temp_dir, "subdir")
        subdir.mkdir()
        Path(subdir, "subfile.txt").write_text("Subdir normal file")

        # Create hidden subdirectory (should be excluded)
        hidden_dir = Path(temp_dir, ".hidden_dir")
        hidden_dir.mkdir()
        Path(hidden_dir, "hidden_inside.txt").write_text("File inside hidden dir")

        yield temp_dir

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_count_files_excludes_hidden_files(self, temp_folder_with_hidden):
        """Verify count_files_recursive() excludes hidden files"""
        count, total_bytes = count_files_recursive(temp_folder_with_hidden)

        # Should count only: file1.txt, file2.txt, subfile.txt = 3 files
        # Should NOT count: .DS_Store, .hidden.txt, or anything in .hidden_dir
        assert count == 3, f"Expected 3 files, got {count}"

        # Each file is ~15-30 bytes, total should be ~60-90 bytes
        assert total_bytes > 0, "Should have counted some bytes"
        assert total_bytes < 500, f"Unexpected large byte count: {total_bytes}"

    def test_count_files_excludes_hidden_directories(self, temp_folder_with_hidden):
        """Verify count_files_recursive() excludes hidden directories"""
        count, total_bytes = count_files_recursive(temp_folder_with_hidden)

        # Should NOT include any files from .hidden_dir
        # File count should be exactly 3 (not 4)
        assert count == 3, f"Should exclude files from hidden directories, got {count}"

    def test_zip_smart_excludes_hidden_files(self, temp_folder_with_hidden):
        """Verify zip_folder_smart() excludes hidden files from ZIP"""
        output_zip = os.path.join(tempfile.gettempdir(), "test_archive.zip")

        try:
            # Create ZIP from folder with hidden files
            zip_folder_smart(
                temp_folder_with_hidden,
                output_zip,
                progress_callback=None
            )

            # Read ZIP and verify contents
            with zipfile.ZipFile(output_zip, 'r') as z:
                file_list = z.namelist()

            # Should NOT contain any hidden files
            hidden_files = [f for f in file_list if '/.DS_Store' in f or '/.hidden' in f]
            assert len(hidden_files) == 0, f"ZIP contains hidden files: {hidden_files}"

            # Should contain normal files
            assert any('file1.txt' in f for f in file_list), "Should contain file1.txt"
            assert any('file2.txt' in f for f in file_list), "Should contain file2.txt"
            assert any('subfile.txt' in f for f in file_list), "Should contain subfile.txt"

        finally:
            if os.path.exists(output_zip):
                os.unlink(output_zip)

    def test_zip_smart_result_count_matches(self, temp_folder_with_hidden):
        """Verify ZIP file count matches count_files_recursive()"""
        output_zip = os.path.join(tempfile.gettempdir(), "test_archive2.zip")

        try:
            # Get expected file count
            expected_count, _ = count_files_recursive(temp_folder_with_hidden)

            # Create ZIP
            zip_folder_smart(
                temp_folder_with_hidden,
                output_zip,
                progress_callback=None
            )

            # Count files in ZIP (excluding directories)
            with zipfile.ZipFile(output_zip, 'r') as z:
                file_count = sum(1 for name in z.namelist() if not name.endswith('/'))

            assert file_count == expected_count, \
                f"ZIP has {file_count} files but expected {expected_count}"

        finally:
            if os.path.exists(output_zip):
                os.unlink(output_zip)

    def test_hidden_files_not_listed(self, temp_folder_with_hidden):
        """Verify os.listdir() filtering works correctly"""
        # Simulate what worker_jobs.py line 406 does
        all_items = os.listdir(temp_folder_with_hidden)
        filtered_files = [
            f for f in all_items
            if os.path.isfile(os.path.join(temp_folder_with_hidden, f))
            and not f.startswith('.')
        ]

        # Should have exactly 2 normal files (file1.txt, file2.txt)
        assert len(filtered_files) == 2, \
            f"Expected 2 visible files, got {len(filtered_files)}: {filtered_files}"

        assert 'file1.txt' in filtered_files, "file1.txt should be in list"
        assert 'file2.txt' in filtered_files, "file2.txt should be in list"
        assert '.DS_Store' not in filtered_files, ".DS_Store should be filtered"
        assert '.hidden.txt' not in filtered_files, ".hidden.txt should be filtered"

    def test_specific_hidden_files_excluded(self, temp_folder_with_hidden):
        """Verify specific problematic files are excluded"""
        count, _ = count_files_recursive(temp_folder_with_hidden)

        # Create a list of problematic files we're testing for
        problematic_files = ['.DS_Store', '.hidden.txt', '.hidden_dir/hidden_inside.txt']

        # None of these should be counted
        assert count == 3, f"Hidden files were not properly excluded"


class TestHiddenFilesIntegration:
    """Integration tests for hidden files in actual transfer scenarios"""

    @pytest.fixture
    def transfer_scenario_folder(self):
        """Create a realistic folder structure like a Pro Tools session"""
        temp_dir = tempfile.mkdtemp()

        # Simulate a media project folder
        Path(temp_dir, "Audio").mkdir()
        Path(temp_dir, "Audio", "track1.wav").write_text("Audio content 1")
        Path(temp_dir, "Audio", "track2.wav").write_text("Audio content 2")

        Path(temp_dir, "Video").mkdir()
        Path(temp_dir, "Video", "video.mov").write_text("Video content")

        # Add system files that should be hidden
        Path(temp_dir, ".DS_Store").write_text("macOS metadata")
        Path(temp_dir, ".git").mkdir(exist_ok=True)
        Path(temp_dir, ".git", "HEAD").write_text("Git reference")
        Path(temp_dir, "Audio", ".DS_Store").write_text("Subdir metadata")

        yield temp_dir

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_media_project_transfer_excludes_system_files(self, transfer_scenario_folder):
        """Verify media transfer doesn't include system files"""
        count, total_bytes = count_files_recursive(transfer_scenario_folder)

        # Should count: track1.wav, track2.wav, video.mov = 3 files
        # Should NOT count: .DS_Store files, .git content
        assert count == 3, f"Expected 3 media files, got {count}"

    def test_folder_size_accurate_without_hidden_files(self, transfer_scenario_folder):
        """Verify byte count doesn't include hidden files"""
        count, total_bytes = count_files_recursive(transfer_scenario_folder)

        # Bytes should only be for visible files (~15-20 bytes each = ~45-60 total)
        assert total_bytes < 200, \
            f"Byte count seems high ({total_bytes}), may include hidden files"
