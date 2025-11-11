"""
Ketter 3.0 - Pro Tools Scenario Integration Tests
Week 5: Real-world integration tests for Pro Tools workflows

MRC: Test complete workflows end-to-end
"""

import os
import pytest
import tempfile
import shutil
import time
from pathlib import Path

from app.zip_engine import (
    zip_folder_smart,
    unzip_folder_smart,
    count_files_recursive,
    validate_zip_integrity
)
from app.watch_folder import (
    watch_folder_until_stable,
    get_folder_state
)
from app.copy_engine import calculate_sha256


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing"""
    workspace = tempfile.mkdtemp()
    yield workspace
    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def protools_session_small(temp_workspace):
    """
    Create a small Pro Tools session structure for testing
    Simulates: 10 audio files (1 MB each) + session file
    """
    session_folder = os.path.join(temp_workspace, 'MySession')
    audio_folder = os.path.join(session_folder, 'Audio Files')
    os.makedirs(audio_folder)

    # Create session file
    session_file = os.path.join(session_folder, 'MySession.ptx')
    with open(session_file, 'w') as f:
        f.write('<?xml version="1.0"?>\n<Session>Pro Tools Session</Session>')

    # Create 10 audio files (1 MB each)
    file_size = 1024 * 1024  # 1 MB
    for i in range(10):
        audio_file = os.path.join(audio_folder, f'Audio_{i:03d}.wav')
        with open(audio_file, 'wb') as f:
            f.write(b'0' * file_size)

    return session_folder


@pytest.fixture
def protools_session_large(temp_workspace):
    """
    Create a larger Pro Tools session for performance testing
    Simulates: 100 audio files (1 MB each) + session file
    """
    session_folder = os.path.join(temp_workspace, 'LargeSession')
    audio_folder = os.path.join(session_folder, 'Audio Files')
    os.makedirs(audio_folder)

    # Create session file
    session_file = os.path.join(session_folder, 'LargeSession.ptx')
    with open(session_file, 'w') as f:
        f.write('<?xml version="1.0"?>\n<Session>Pro Tools Large Session</Session>')

    # Create 100 audio files (1 MB each)
    file_size = 1024 * 1024  # 1 MB
    for i in range(100):
        audio_file = os.path.join(audio_folder, f'Audio_{i:03d}.wav')
        with open(audio_file, 'wb') as f:
            f.write(b'0' * file_size)

    return session_folder


class TestProToolsBasicWorkflow:
    """Test basic Pro Tools transfer workflow"""

    def test_zip_protools_session_small(self, protools_session_small, temp_workspace):
        """Test zipping a small Pro Tools session"""
        zip_path = os.path.join(temp_workspace, 'session.zip')

        # Count files before zipping
        file_count, total_size = count_files_recursive(protools_session_small)
        assert file_count == 11  # 10 audio + 1 session file

        # ZIP the session
        result = zip_folder_smart(protools_session_small, zip_path)

        # Verify ZIP was created successfully
        assert os.path.exists(zip_path)
        assert result == zip_path

        # Validate ZIP integrity
        is_valid, message = validate_zip_integrity(zip_path)
        assert is_valid is True

    def test_unzip_protools_session_small(self, protools_session_small, temp_workspace):
        """Test unzipping a Pro Tools session maintains structure"""
        # ZIP the session
        zip_path = os.path.join(temp_workspace, 'session.zip')
        zip_folder_smart(protools_session_small, zip_path)

        # Unzip to new location
        unzip_dest = os.path.join(temp_workspace, 'restored_session')
        unzip_folder_smart(zip_path, unzip_dest)

        # Verify structure is maintained
        assert os.path.exists(os.path.join(unzip_dest, 'MySession.ptx'))
        assert os.path.exists(os.path.join(unzip_dest, 'Audio Files'))

        # Verify all audio files exist
        audio_folder = os.path.join(unzip_dest, 'Audio Files')
        audio_files = os.listdir(audio_folder)
        assert len(audio_files) == 10

    def test_complete_protools_workflow(self, protools_session_small, temp_workspace):
        """Test complete workflow: count -> zip -> validate -> unzip -> verify"""
        # Step 1: Count original files
        original_count, original_size = count_files_recursive(protools_session_small)

        # Step 2: ZIP
        zip_path = os.path.join(temp_workspace, 'session.zip')
        zip_folder_smart(protools_session_small, zip_path)

        # Step 3: Validate ZIP
        is_valid, _ = validate_zip_integrity(zip_path)
        assert is_valid is True

        # Step 4: Unzip
        unzip_dest = os.path.join(temp_workspace, 'restored')
        unzip_folder_smart(zip_path, unzip_dest)

        # Step 5: Verify counts match
        restored_count, restored_size = count_files_recursive(unzip_dest)
        assert restored_count == original_count
        assert restored_size == original_size


class TestProToolsLargeSession:
    """Test larger Pro Tools sessions (performance)"""

    def test_zip_large_session_performance(self, protools_session_large, temp_workspace):
        """Test zipping 100 files completes in reasonable time"""
        zip_path = os.path.join(temp_workspace, 'large_session.zip')

        # Time the operation
        start_time = time.time()
        zip_folder_smart(protools_session_large, zip_path)
        duration = time.time() - start_time

        # 100 files × 1 MB should complete in < 10 seconds with STORE mode
        assert duration < 10

        # Verify it worked
        assert os.path.exists(zip_path)

    def test_unzip_large_session_performance(self, protools_session_large, temp_workspace):
        """Test unzipping 100 files completes in reasonable time"""
        # First create the ZIP
        zip_path = os.path.join(temp_workspace, 'large_session.zip')
        zip_folder_smart(protools_session_large, zip_path)

        # Time the unzip operation
        unzip_dest = os.path.join(temp_workspace, 'restored')
        start_time = time.time()
        unzip_folder_smart(zip_path, unzip_dest)
        duration = time.time() - start_time

        # Unzipping should be even faster (< 8 seconds)
        assert duration < 8

        # Verify it worked
        restored_count, _ = count_files_recursive(unzip_dest)
        assert restored_count == 101  # 100 audio + 1 session


class TestProToolsChecksumVerification:
    """Test checksum verification for Pro Tools transfers"""

    def test_checksum_before_after_zip(self, protools_session_small, temp_workspace):
        """Test that checksums can be calculated on session folder"""
        # Get initial folder state
        initial_state = get_folder_state(protools_session_small)
        assert len(initial_state) == 11  # All files tracked

    def test_zip_checksum_verification(self, protools_session_small, temp_workspace):
        """Test that ZIP file can be checksummed for verification"""
        # ZIP the session
        zip_path = os.path.join(temp_workspace, 'session.zip')
        zip_folder_smart(protools_session_small, zip_path)

        # Calculate checksum of ZIP file
        checksum = calculate_sha256(zip_path)

        # Verify checksum is valid SHA-256 (64 hex characters)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_unzipped_session_integrity(self, protools_session_small, temp_workspace):
        """Test that unzipped session has same file sizes as original"""
        # Get original file sizes
        original_state = get_folder_state(protools_session_small)

        # ZIP and unzip
        zip_path = os.path.join(temp_workspace, 'session.zip')
        zip_folder_smart(protools_session_small, zip_path)

        unzip_dest = os.path.join(temp_workspace, 'restored')
        unzip_folder_smart(zip_path, unzip_dest)

        # Get restored file sizes
        restored_state = get_folder_state(unzip_dest)

        # Compare file counts
        assert len(original_state) == len(restored_state)

        # Compare total sizes
        original_total = sum(size for size, _ in original_state.values())
        restored_total = sum(size for size, _ in restored_state.values())
        assert original_total == restored_total


class TestWatchModeProToolsScenario:
    """Test watch mode with Pro Tools client transfer simulation"""

    def test_watch_mode_waits_for_client_transfer(self, temp_workspace):
        """
        Simulate client transferring Pro Tools session:
        - Client starts copying files
        - Watch mode detects activity and waits
        - Client finishes
        - Watch mode detects stability and triggers transfer
        """
        session_folder = os.path.join(temp_workspace, 'IncomingSession')
        os.makedirs(session_folder)

        # Track progress
        stability_checks = []

        def progress_callback(elapsed, settle_time, state):
            stability_checks.append({
                'elapsed': elapsed,
                'file_count': len(state)
            })

            # Simulate client adding files during first 2 checks
            if len(stability_checks) <= 2:
                new_file = os.path.join(
                    session_folder,
                    f'Audio_{len(stability_checks):03d}.wav'
                )
                with open(new_file, 'wb') as f:
                    f.write(b'0' * (1024 * 1024))  # 1 MB

        # Watch with short settle time for testing
        became_stable = watch_folder_until_stable(
            session_folder,
            settle_time_seconds=2,
            max_wait_seconds=10,
            progress_callback=progress_callback
        )

        # Should eventually stabilize
        assert became_stable is True

        # Should have detected changes and waited
        assert len(stability_checks) > 2

        # Final file count should be > 0
        final_count, _ = count_files_recursive(session_folder)
        assert final_count > 0

    def test_watch_mode_immediate_stability(self, protools_session_small):
        """Test watch mode with already-complete session (immediate stability)"""
        # Session is already complete, should be immediately stable
        became_stable = watch_folder_until_stable(
            protools_session_small,
            settle_time_seconds=1,
            max_wait_seconds=5
        )

        assert became_stable is True


class TestProToolsWorkflowWithoutWatch:
    """Test Pro Tools workflow without watch mode (immediate transfer)"""

    def test_immediate_transfer_workflow(self, protools_session_small, temp_workspace):
        """Test transferring complete Pro Tools session without watch mode"""
        # Simulate transfer workflow:
        # 1. Session is complete
        # 2. ZIP immediately
        # 3. Transfer (simulated by copying ZIP)
        # 4. Unzip at destination

        # Step 1: Count files
        file_count, total_size = count_files_recursive(protools_session_small)
        assert file_count == 11

        # Step 2: ZIP
        zip_path = os.path.join(temp_workspace, 'transfer.zip')
        zip_folder_smart(protools_session_small, zip_path)

        # Step 3: Simulate transfer by "copying" to destination
        dest_zip = os.path.join(temp_workspace, 'transferred.zip')
        shutil.copy2(zip_path, dest_zip)

        # Step 4: Unzip at destination
        final_dest = os.path.join(temp_workspace, 'final_session')
        unzip_folder_smart(dest_zip, final_dest)

        # Step 5: Verify
        final_count, final_size = count_files_recursive(final_dest)
        assert final_count == file_count
        assert final_size == total_size


class TestProToolsEdgeCases:
    """Test edge cases specific to Pro Tools workflows"""

    def test_empty_audio_folder(self, temp_workspace):
        """Test handling Pro Tools session with empty Audio Files folder"""
        session_folder = os.path.join(temp_workspace, 'EmptySession')
        audio_folder = os.path.join(session_folder, 'Audio Files')
        os.makedirs(audio_folder)

        # Just session file, no audio
        session_file = os.path.join(session_folder, 'Empty.ptx')
        with open(session_file, 'w') as f:
            f.write('<Session>Empty</Session>')

        # Should still work
        zip_path = os.path.join(temp_workspace, 'empty.zip')
        zip_folder_smart(session_folder, zip_path)

        assert os.path.exists(zip_path)

        # Unzip and verify structure preserved
        unzip_dest = os.path.join(temp_workspace, 'restored')
        unzip_folder_smart(zip_path, unzip_dest)

        assert os.path.exists(os.path.join(unzip_dest, 'Empty.ptx'))
        assert os.path.exists(os.path.join(unzip_dest, 'Audio Files'))

    def test_nested_subfolder_structure(self, temp_workspace):
        """Test Pro Tools session with nested subfolders"""
        session_folder = os.path.join(temp_workspace, 'ComplexSession')
        audio_folder = os.path.join(session_folder, 'Audio Files')
        takes_folder = os.path.join(audio_folder, 'Takes')
        os.makedirs(takes_folder)

        # Create files at different levels
        with open(os.path.join(session_folder, 'Session.ptx'), 'w') as f:
            f.write('<Session/>')
        with open(os.path.join(audio_folder, 'main.wav'), 'wb') as f:
            f.write(b'0' * 1024)
        with open(os.path.join(takes_folder, 'take1.wav'), 'wb') as f:
            f.write(b'0' * 1024)

        # ZIP and unzip
        zip_path = os.path.join(temp_workspace, 'complex.zip')
        zip_folder_smart(session_folder, zip_path)

        unzip_dest = os.path.join(temp_workspace, 'restored')
        unzip_folder_smart(zip_path, unzip_dest)

        # Verify nested structure preserved
        assert os.path.exists(os.path.join(unzip_dest, 'Session.ptx'))
        assert os.path.exists(os.path.join(unzip_dest, 'Audio Files', 'main.wav'))
        assert os.path.exists(os.path.join(unzip_dest, 'Audio Files', 'Takes', 'take1.wav'))

    def test_large_individual_file(self, temp_workspace):
        """Test session with one very large file (simulating long recording)"""
        session_folder = os.path.join(temp_workspace, 'LongRecording')
        os.makedirs(session_folder)

        # Create 50 MB file (simulating long audio recording)
        large_file = os.path.join(session_folder, 'LongTake.wav')
        chunk_size = 1024 * 1024  # 1 MB chunks
        with open(large_file, 'wb') as f:
            for _ in range(50):  # 50 MB total
                f.write(b'0' * chunk_size)

        # Should handle large file
        zip_path = os.path.join(temp_workspace, 'large.zip')
        zip_folder_smart(session_folder, zip_path)

        # Verify ZIP size is reasonable (STORE mode means ~same size)
        zip_size = os.path.getsize(zip_path)
        original_size = os.path.getsize(large_file)

        # ZIP should be close to original (within 1 MB overhead)
        assert zip_size <= original_size + (1024 * 1024)


class TestProToolsProgressTracking:
    """Test progress tracking during Pro Tools transfers"""

    def test_zip_progress_tracking(self, protools_session_large, temp_workspace):
        """Test that ZIP progress is tracked correctly"""
        zip_path = os.path.join(temp_workspace, 'session.zip')

        progress_updates = []

        def progress_callback(current, total, current_file):
            progress_updates.append({
                'current': current,
                'total': total,
                'percent': (current / total * 100) if total > 0 else 0
            })

        zip_folder_smart(
            protools_session_large,
            zip_path,
            progress_callback=progress_callback
        )

        # Should have progress updates
        assert len(progress_updates) > 0

        # Last update should be 100%
        assert progress_updates[-1]['percent'] == 100

        # Progress should be monotonically increasing
        for i in range(1, len(progress_updates)):
            assert progress_updates[i]['current'] >= progress_updates[i-1]['current']

    def test_unzip_progress_tracking(self, protools_session_large, temp_workspace):
        """Test that unzip progress is tracked correctly"""
        # Create ZIP first
        zip_path = os.path.join(temp_workspace, 'session.zip')
        zip_folder_smart(protools_session_large, zip_path)

        # Unzip with progress tracking
        unzip_dest = os.path.join(temp_workspace, 'restored')
        progress_updates = []

        def progress_callback(current, total, current_file):
            progress_updates.append({
                'current': current,
                'total': total,
                'percent': (current / total * 100) if total > 0 else 0
            })

        unzip_folder_smart(
            zip_path,
            unzip_dest,
            progress_callback=progress_callback
        )

        # Should have progress updates
        assert len(progress_updates) > 0

        # Last update should be 100%
        assert progress_updates[-1]['percent'] == 100
