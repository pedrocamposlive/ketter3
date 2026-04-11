import os
import time
import tempfile
import pytest
from app.core.watch_folder import (
    get_folder_info,
    format_settle_time,
    watch_folder_until_stable,
    FolderNotFoundError
)

class TestWatchFolderInfo:
    def test_get_folder_info_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            for i in range(3):
                with open(os.path.join(tmpdir, f"file{i}.txt"), "w") as f:
                    f.write("test")
            
            info = get_folder_info(tmpdir)
            assert info['file_count'] == 3
            assert info['total_size'] == 12  # 3 files * 4 bytes
            assert 'path' in info or 'folder_path' in info

    def test_get_folder_info_invalid(self):
        info = get_folder_info("/nonexistent/path")
        assert info['file_count'] == 0
        assert info['total_size'] == 0

class TestFormatSettleTime:
    def test_format_settle_time_seconds(self):
        assert "30" in format_settle_time(30)
        assert "s" in format_settle_time(30).lower()

    def test_format_settle_time_minutes(self):
        assert "1" in format_settle_time(60)
        assert "m" in format_settle_time(60).lower()

    def test_format_settle_time_hours(self):
        assert "1" in format_settle_time(3600)
        assert "h" in format_settle_time(3600).lower()

class TestWatchFolderBehavior:
    def test_watch_folder_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should timeout immediately if max_wait is 0
            result = watch_folder_until_stable(
                tmpdir, 
                settle_time_seconds=1, 
                max_wait_seconds=0
            )
            assert result is False

    def test_watch_folder_stable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should return True if folder is stable
            result = watch_folder_until_stable(
                tmpdir, 
                settle_time_seconds=1, 
                max_wait_seconds=5
            )
            assert result is True
