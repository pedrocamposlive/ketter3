"""
Ketter 3.0 - Watch Folder Intelligence Tests
Week 5: Tests for settle time detection and folder monitoring

MRC: Simple tests for watch folder functionality
"""

import os
import pytest
import tempfile
import shutil
import time
from pathlib import Path

from app.watch_folder import (
    get_folder_state,
    compare_folder_states,
    watch_folder_until_stable,
    get_folder_info,
    format_settle_time,
    estimate_watch_duration
)


@pytest.fixture
def temp_folder():
    """Create a temporary folder for testing"""
    folder = tempfile.mkdtemp()
    yield folder
    shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture
def sample_folder_with_files(temp_folder):
    """Create a folder with sample files"""
    # Create 3 files
    for i in range(3):
        file_path = os.path.join(temp_folder, f'file{i}.txt')
        with open(file_path, 'w') as f:
            f.write(f'Content {i}')

    return temp_folder


class TestGetFolderState:
    """Test folder state snapshot functionality"""

    def test_get_folder_state_empty(self, temp_folder):
        """Test getting state of empty folder"""
        state = get_folder_state(temp_folder)

        assert isinstance(state, dict)
        assert len(state) == 0

    def test_get_folder_state_with_files(self, sample_folder_with_files):
        """Test getting state of folder with files"""
        state = get_folder_state(sample_folder_with_files)

        assert len(state) == 3
        for file_path, (size, mtime) in state.items():
            assert os.path.exists(file_path)
            assert size > 0
            assert mtime > 0

    def test_get_folder_state_nested(self, temp_folder):
        """Test getting state of folder with nested structure"""
        # Create nested structure
        subfolder = os.path.join(temp_folder, 'subfolder')
        os.makedirs(subfolder)

        # Create files at different levels
        with open(os.path.join(temp_folder, 'file1.txt'), 'w') as f:
            f.write('test')
        with open(os.path.join(subfolder, 'file2.txt'), 'w') as f:
            f.write('test')

        state = get_folder_state(temp_folder)

        assert len(state) == 2
        # Verify both files are tracked
        file_paths = list(state.keys())
        assert any('file1.txt' in path for path in file_paths)
        assert any('file2.txt' in path for path in file_paths)

    def test_get_folder_state_tracks_size(self, temp_folder):
        """Test that state tracks file sizes correctly"""
        # Create file with known size
        file_path = os.path.join(temp_folder, 'test.txt')
        content = 'A' * 1000  # 1000 bytes
        with open(file_path, 'w') as f:
            f.write(content)

        state = get_folder_state(temp_folder)

        assert len(state) == 1
        size, _ = state[file_path]
        assert size == 1000

    def test_get_folder_state_tracks_mtime(self, temp_folder):
        """Test that state tracks modification times"""
        file_path = os.path.join(temp_folder, 'test.txt')

        # Create file
        with open(file_path, 'w') as f:
            f.write('initial')

        state1 = get_folder_state(temp_folder)
        _, mtime1 = state1[file_path]

        # Wait a bit and modify file
        time.sleep(0.1)
        with open(file_path, 'w') as f:
            f.write('modified')

        state2 = get_folder_state(temp_folder)
        _, mtime2 = state2[file_path]

        # Modification time should have changed
        assert mtime2 > mtime1


class TestCompareFolderStates:
    """Test folder state comparison"""

    def test_compare_identical_states(self, sample_folder_with_files):
        """Test comparing identical states returns True (stable)"""
        state1 = get_folder_state(sample_folder_with_files)
        state2 = get_folder_state(sample_folder_with_files)

        is_stable = compare_folder_states(state1, state2)

        assert is_stable is True

    def test_compare_states_file_added(self, sample_folder_with_files):
        """Test comparison detects when file is added"""
        state1 = get_folder_state(sample_folder_with_files)

        # Add a new file
        new_file = os.path.join(sample_folder_with_files, 'newfile.txt')
        with open(new_file, 'w') as f:
            f.write('new')

        state2 = get_folder_state(sample_folder_with_files)

        is_stable = compare_folder_states(state1, state2)

        assert is_stable is False

    def test_compare_states_file_removed(self, sample_folder_with_files):
        """Test comparison detects when file is removed"""
        state1 = get_folder_state(sample_folder_with_files)

        # Remove a file
        files = os.listdir(sample_folder_with_files)
        os.remove(os.path.join(sample_folder_with_files, files[0]))

        state2 = get_folder_state(sample_folder_with_files)

        is_stable = compare_folder_states(state1, state2)

        assert is_stable is False

    def test_compare_states_file_modified(self, sample_folder_with_files):
        """Test comparison detects when file is modified"""
        state1 = get_folder_state(sample_folder_with_files)

        # Modify a file
        time.sleep(0.1)  # Ensure mtime changes
        files = os.listdir(sample_folder_with_files)
        file_path = os.path.join(sample_folder_with_files, files[0])
        with open(file_path, 'a') as f:
            f.write(' modified')

        state2 = get_folder_state(sample_folder_with_files)

        is_stable = compare_folder_states(state1, state2)

        assert is_stable is False

    def test_compare_states_size_changed(self, temp_folder):
        """Test comparison detects when file size changes"""
        file_path = os.path.join(temp_folder, 'test.txt')

        # Create file
        with open(file_path, 'w') as f:
            f.write('short')

        state1 = get_folder_state(temp_folder)

        # Change file size
        with open(file_path, 'w') as f:
            f.write('much longer content')

        state2 = get_folder_state(temp_folder)

        is_stable = compare_folder_states(state1, state2)

        assert is_stable is False


class TestWatchFolderUntilStable:
    """Test watch folder monitoring"""

    def test_watch_folder_already_stable(self, sample_folder_with_files):
        """Test watch folder when folder is already stable"""
        # Use very short settle time since folder is stable
        became_stable = watch_folder_until_stable(
            sample_folder_with_files,
            settle_time_seconds=1,
            max_wait_seconds=5
        )

        assert became_stable is True

    def test_watch_folder_detects_changes(self, temp_folder):
        """Test watch folder detects changes and waits for stability"""
        # Create initial file
        file_path = os.path.join(temp_folder, 'test.txt')
        with open(file_path, 'w') as f:
            f.write('initial')

        # Track progress
        progress_calls = []

        def progress_callback(elapsed, settle_time, state):
            progress_calls.append({
                'elapsed': elapsed,
                'settle_time': settle_time,
                'state': state
            })

            # Simulate adding a file after first check
            if len(progress_calls) == 1:
                new_file = os.path.join(temp_folder, 'added.txt')
                with open(new_file, 'w') as f:
                    f.write('added during watch')

        # Watch with short times for testing
        became_stable = watch_folder_until_stable(
            temp_folder,
            settle_time_seconds=2,
            max_wait_seconds=10,
            progress_callback=progress_callback
        )

        # Should eventually stabilize
        assert became_stable is True
        # Should have made progress callbacks
        assert len(progress_calls) > 0

    def test_watch_folder_timeout(self, temp_folder):
        """Test watch folder respects max wait time"""
        # Track progress
        check_count = [0]

        def progress_callback(elapsed, settle_time, state):
            check_count[0] += 1
            # Keep adding files to prevent stability
            if check_count[0] < 5:  # Only for first few checks
                new_file = os.path.join(temp_folder, f'file_{check_count[0]}.txt')
                with open(new_file, 'w') as f:
                    f.write(f'content {check_count[0]}')

        # Watch with short max wait - should timeout
        became_stable = watch_folder_until_stable(
            temp_folder,
            settle_time_seconds=2,
            max_wait_seconds=6,  # Short timeout
            progress_callback=progress_callback
        )

        # Should timeout and return False
        assert became_stable is False

    def test_watch_folder_handles_empty_folder(self, temp_folder):
        """Test watch folder works with empty folder"""
        became_stable = watch_folder_until_stable(
            temp_folder,
            settle_time_seconds=1,
            max_wait_seconds=5
        )

        # Empty folder is immediately stable
        assert became_stable is True


class TestGetFolderInfo:
    """Test folder information utility"""

    def test_get_folder_info_empty(self, temp_folder):
        """Test getting info of empty folder"""
        info = get_folder_info(temp_folder)

        assert info['file_count'] == 0
        assert info['total_size'] == 0
        assert info['path'] == temp_folder

    def test_get_folder_info_with_files(self, sample_folder_with_files):
        """Test getting info of folder with files"""
        info = get_folder_info(sample_folder_with_files)

        assert info['file_count'] == 3
        assert info['total_size'] > 0
        assert info['path'] == sample_folder_with_files

    def test_get_folder_info_nested(self, temp_folder):
        """Test getting info of nested folder structure"""
        # Create nested structure
        subfolder = os.path.join(temp_folder, 'subfolder')
        os.makedirs(subfolder)

        # Create files at different levels
        with open(os.path.join(temp_folder, 'file1.txt'), 'w') as f:
            f.write('A' * 100)
        with open(os.path.join(subfolder, 'file2.txt'), 'w') as f:
            f.write('B' * 200)

        info = get_folder_info(temp_folder)

        assert info['file_count'] == 2
        assert info['total_size'] == 300  # 100 + 200


class TestWatchHelpers:
    """Test watch folder helper functions"""

    def test_format_settle_time(self):
        """Test settle time formatting"""
        assert format_settle_time(30) == "30 seconds"
        assert format_settle_time(60) == "1 minute"
        assert format_settle_time(90) == "1.5 minutes"
        assert format_settle_time(300) == "5 minutes"

    def test_estimate_watch_duration(self):
        """Test watch duration estimation"""
        # Simple file count should give reasonable estimate
        estimated = estimate_watch_duration(100, 30)

        # Should be at least the settle time
        assert estimated >= 30
        # Should be reasonable (not hours)
        assert estimated < 600


class TestWatchFolderEdgeCases:
    """Test edge cases and error handling"""

    def test_watch_nonexistent_folder(self):
        """Test watching non-existent folder fails gracefully"""
        nonexistent = "/path/that/does/not/exist"

        with pytest.raises(Exception):
            watch_folder_until_stable(nonexistent, settle_time_seconds=1)

    def test_watch_folder_minimal_settle_time(self, temp_folder):
        """Test with very short settle time (edge case)"""
        became_stable = watch_folder_until_stable(
            temp_folder,
            settle_time_seconds=1,
            max_wait_seconds=5
        )

        assert became_stable is True

    def test_get_folder_state_permission_issues(self):
        """Test folder state handles permission issues gracefully"""
        # This test is OS-dependent, but tests graceful handling
        # On some systems, /root may not be accessible
        restricted_path = "/root"

        if os.path.exists(restricted_path):
            try:
                state = get_folder_state(restricted_path)
                # If we can read it, state should be a dict
                assert isinstance(state, dict)
            except PermissionError:
                # Expected on restricted paths
                pass
