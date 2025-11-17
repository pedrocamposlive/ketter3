"""
Test to verify that source folder is preserved after MOVE operation.

When performing MOVE mode on a folder:
- Source folder should remain (not deleted)
- Source folder should be empty (contents deleted)
- Destination folder should contain all files
"""

import os
import shutil
import tempfile
import pytest
from pathlib import Path

from app.core.copy_engine import delete_source_after_move


class TestMoveFolderPreservation:
    """Test that MOVE mode preserves source folder but deletes contents"""

    def test_delete_source_after_move_preserves_folder(self):
        """Verify that folder itself is preserved, only contents deleted"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = os.path.join(tmpdir, "source")
            os.makedirs(source_folder)

            # Create test files inside
            test_file1 = os.path.join(source_folder, "file1.txt")
            test_file2 = os.path.join(source_folder, "file2.txt")
            Path(test_file1).write_text("content1")
            Path(test_file2).write_text("content2")

            # Create a subfolder with files
            subfolder = os.path.join(source_folder, "subfolder")
            os.makedirs(subfolder)
            test_file3 = os.path.join(subfolder, "file3.txt")
            Path(test_file3).write_text("content3")

            # Verify setup
            assert os.path.exists(source_folder)
            assert os.path.exists(test_file1)
            assert os.path.exists(test_file2)
            assert os.path.exists(subfolder)
            assert os.path.exists(test_file3)

            # Call delete_source_after_move with is_folder=True
            delete_source_after_move(source_folder, is_folder=True)

            # Verify folder still exists but is empty
            assert os.path.exists(source_folder), "Source folder should be preserved"
            assert os.path.isdir(source_folder), "Source folder should still be a directory"
            assert len(os.listdir(source_folder)) == 0, "Source folder should be empty"

            # Verify files are deleted
            assert not os.path.exists(test_file1), "File1 should be deleted"
            assert not os.path.exists(test_file2), "File2 should be deleted"
            assert not os.path.exists(subfolder), "Subfolder should be deleted"
            assert not os.path.exists(test_file3), "File3 should be deleted"

    def test_delete_source_after_move_file_mode(self):
        """Verify that file mode deletes the file itself"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = os.path.join(tmpdir, "test.txt")
            Path(source_file).write_text("test content")

            assert os.path.exists(source_file)

            # Call delete_source_after_move with is_folder=False
            delete_source_after_move(source_file, is_folder=False)

            # Verify file is deleted
            assert not os.path.exists(source_file), "File should be deleted"

    def test_delete_source_with_nested_directories(self):
        """Verify nested directory structure is properly cleaned"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_folder = os.path.join(tmpdir, "source")
            os.makedirs(source_folder)

            # Create nested structure
            nested1 = os.path.join(source_folder, "level1")
            nested2 = os.path.join(nested1, "level2")
            nested3 = os.path.join(nested2, "level3")
            os.makedirs(nested3)

            # Add files at different levels
            Path(os.path.join(source_folder, "root.txt")).write_text("root")
            Path(os.path.join(nested1, "level1.txt")).write_text("level1")
            Path(os.path.join(nested2, "level2.txt")).write_text("level2")
            Path(os.path.join(nested3, "level3.txt")).write_text("level3")

            # Verify setup
            assert len(os.listdir(source_folder)) > 0

            # Delete contents
            delete_source_after_move(source_folder, is_folder=True)

            # Verify folder preserved but empty
            assert os.path.exists(source_folder)
            assert len(os.listdir(source_folder)) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
