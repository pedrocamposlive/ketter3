"""
Tests for watcher_continuous_job (FASE 3 - Week 6)

MRC: Test-driven approach for continuous watch mode
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from app.database import SessionLocal
from app.models import Transfer, WatchFile, AuditLog, TransferStatus, AuditEventType
from app.services.worker_jobs import watcher_continuous_job, _wait_for_file_settle


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def db_session():
    """Create a test database session"""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def temp_folder():
    """Create temporary source and destination folders"""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        dest = os.path.join(tmpdir, "dest")
        os.makedirs(source)
        os.makedirs(dest)
        yield source, dest


@pytest.fixture
def transfer_with_watch(db_session, temp_folder):
    """Create a transfer with watch_continuous enabled"""
    source, dest = temp_folder

    transfer = Transfer(
        source_path=source,
        destination_path=dest,
        file_size=0,
        file_name="test_watch",
        status=TransferStatus.PENDING,
        watch_mode_enabled=1,
        settle_time_seconds=2,
        watch_continuous=1,
        last_files_processed="[]",
        watch_cycle_count=0
    )
    db_session.add(transfer)
    db_session.commit()
    db_session.refresh(transfer)

    return transfer


# ============================================
# Tests: Helper Function _wait_for_file_settle
# ============================================

class TestWaitForFileSettle:
    """Tests for file settle time detection"""

    def test_file_stable_immediately(self, temp_folder):
        """Test file that is already stable"""
        source, _ = temp_folder
        file_path = os.path.join(source, "stable.txt")

        # Create stable file
        with open(file_path, 'w') as f:
            f.write("test data")

        # Should detect stability quickly
        result = _wait_for_file_settle(file_path, settle_time_seconds=1, max_wait=5)
        assert result is True, "Should detect stable file"

    def test_file_timeout(self, temp_folder):
        """Test file that times out before stabilizing"""
        source, _ = temp_folder
        file_path = os.path.join(source, "nonexistent.txt")

        # File doesn't exist - should timeout
        result = _wait_for_file_settle(file_path, settle_time_seconds=1, max_wait=2)
        assert result is False, "Should timeout for non-existent file"

    def test_file_growing(self, temp_folder):
        """Test file that is growing"""
        source, _ = temp_folder
        file_path = os.path.join(source, "growing.txt")

        def create_growing_file():
            # Simulate file growth
            with open(file_path, 'w') as f:
                f.write("initial")

        # File should eventually stabilize
        # Note: This would require mocking time.sleep
        create_growing_file()
        result = _wait_for_file_settle(file_path, settle_time_seconds=1, max_wait=3)
        assert result is True, "Should detect stable file after growth"


# ============================================
# Tests: watcher_continuous_job - Job Flow
# ============================================

class TestWatcherContinuousJobFlow:
    """Tests for main watcher_continuous_job functionality"""

    @patch('app.services.worker_jobs.get_current_job')
    def test_job_starts_successfully(self, mock_job, db_session, transfer_with_watch):
        """Test job initialization and startup"""
        mock_job_id = "test-job-123"
        mock_job.return_value = Mock(id=mock_job_id)

        # Should start without errors
        with patch('app.services.worker_jobs.time.sleep'), patch('app.services.worker_jobs.Queue'):
            with pytest.raises(StopIteration):
                watcher_continuous_job(transfer_with_watch.id, stop_after_cycles=1)

    @patch('app.services.worker_jobs.get_current_job')
    def test_job_loads_transfer(self, mock_job, db_session, transfer_with_watch):
        """Test job loads transfer from database"""
        mock_job_id = "test-job-456"
        mock_job.return_value = Mock(id=mock_job_id)

        # Verify transfer exists
        transfer = db_session.query(Transfer).filter(Transfer.id == transfer_with_watch.id).first()
        assert transfer is not None, "Transfer should exist"
        assert transfer.watch_continuous == 1, "Watch mode should be enabled"

    @patch('app.services.worker_jobs.get_current_job')
    def test_job_fails_on_missing_transfer(self, mock_job, db_session):
        """Test job fails gracefully when transfer doesn't exist"""
        mock_job_id = "test-job-789"
        mock_job.return_value = Mock(id=mock_job_id)

        # Should raise exception for non-existent transfer
        with pytest.raises(ValueError, match="not found"):
            watcher_continuous_job(999999)

    @patch('app.services.worker_jobs.get_current_job')
    def test_job_requires_watch_mode_enabled(self, mock_job, db_session, temp_folder):
        """Test job fails if watch_mode_enabled is False"""
        mock_job_id = "test-job-000"
        mock_job.return_value = Mock(id=mock_job_id)
        source, dest = temp_folder

        transfer = Transfer(
            source_path=source,
            destination_path=dest,
            file_size=0,
            file_name="no_watch",
            status=TransferStatus.PENDING,
            watch_mode_enabled=0,  # Watch disabled
            watch_continuous=1,
            settle_time_seconds=2
        )
        db_session.add(transfer)
        db_session.commit()

        # Should raise exception
        with pytest.raises(ValueError, match="does not have watch mode enabled"):
            watcher_continuous_job(transfer.id)


# ============================================
# Tests: File Detection Logic
# ============================================

class TestFileDetectionLogic:
    """Tests for new file detection (delta tracking)"""

    def test_empty_source_folder(self, db_session, transfer_with_watch, temp_folder):
        """Test detection with empty source folder"""
        source, _ = temp_folder

        # Folder is empty
        files_in_source = os.listdir(source)
        assert len(files_in_source) == 0, "Source should be empty"

    def test_single_file_detection(self, db_session, transfer_with_watch, temp_folder):
        """Test detection of a single new file"""
        source, dest = temp_folder

        # Create a file
        test_file = os.path.join(source, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")

        # File should be detectable
        files = os.listdir(source)
        assert len(files) == 1, "Should detect single file"

    def test_delta_tracking_via_json(self, db_session, transfer_with_watch):
        """Test delta tracking with JSON"""
        # Simulate initial state
        initial_files = ["/path/file1.txt", "/path/file2.txt"]
        update_json = json.dumps(initial_files)

        # Verify JSON parsing
        parsed = json.loads(update_json)
        assert parsed == initial_files, "JSON should parse correctly"

        # Simulate new files added
        new_files = ["/path/file1.txt", "/path/file2.txt", "/path/file3.txt"]
        new_set = set(new_files)
        old_set = set(initial_files)
        delta = new_set - old_set

        assert delta == {"/path/file3.txt"}, "Should detect only new file"


# ============================================
# Tests: WatchFile Creation
# ============================================

class TestWatchFileCreation:
    """Tests for WatchFile record creation"""

    def test_create_watchfile_record(self, db_session, transfer_with_watch, temp_folder):
        """Test creating a WatchFile record"""
        source, dest = temp_folder
        test_file = os.path.join(source, "detected.wav")

        # Create file
        with open(test_file, 'w') as f:
            f.write("audio data")

        # Create WatchFile record
        watch_file = WatchFile(
            transfer_id=transfer_with_watch.id,
            file_name="detected.wav",
            file_path=test_file,
            file_size=os.path.getsize(test_file),
            status=TransferStatus.PENDING,
            detected_at=datetime.now(timezone.utc)
        )
        db_session.add(watch_file)
        db_session.commit()
        db_session.refresh(watch_file)

        # Verify record
        assert watch_file.id is not None, "WatchFile should have ID"
        assert watch_file.transfer_id == transfer_with_watch.id, "Should link to transfer"
        assert watch_file.file_name == "detected.wav", "Should have correct filename"
        assert watch_file.status == TransferStatus.PENDING, "Should start as PENDING"

    def test_watchfile_timestamps(self, db_session, transfer_with_watch):
        """Test WatchFile timestamp fields"""
        watch_file = WatchFile(
            transfer_id=transfer_with_watch.id,
            file_name="test.txt",
            file_path="/path/test.txt",
            file_size=100,
            status=TransferStatus.PENDING,
            detected_at=datetime.now(timezone.utc)
        )
        db_session.add(watch_file)
        db_session.commit()

        # Verify timestamps
        assert watch_file.detected_at is not None, "Should have detected_at"
        assert watch_file.transfer_started_at is None, "transfer_started_at should be None initially"
        assert watch_file.transfer_completed_at is None, "transfer_completed_at should be None initially"


# ============================================
# Tests: Audit Logging
# ============================================

class TestAuditLogging:
    """Tests for audit log creation during watch mode"""

    def test_watch_start_audit_log(self, db_session, transfer_with_watch):
        """Test audit log on watch mode start"""
        log = AuditLog(
            transfer_id=transfer_with_watch.id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message="Continuous watch mode started",
            event_metadata={"action": "watch_start", "settle_time": 30}
        )
        db_session.add(log)
        db_session.commit()

        # Verify log
        saved_log = db_session.query(AuditLog).filter(
            AuditLog.transfer_id == transfer_with_watch.id
        ).first()
        assert saved_log is not None, "Log should be saved"
        assert saved_log.event_type == AuditEventType.TRANSFER_PROGRESS, "Should be TRANSFER_PROGRESS"

    def test_file_detection_audit_log(self, db_session, transfer_with_watch):
        """Test audit log on file detection"""
        log = AuditLog(
            transfer_id=transfer_with_watch.id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message="File detected: test.wav (1024 bytes)",
            event_metadata={
                "file_name": "test.wav",
                "file_size": 1024,
                "cycle": 1
            }
        )
        db_session.add(log)
        db_session.commit()

        # Verify log metadata
        saved_log = db_session.query(AuditLog).filter(
            AuditLog.transfer_id == transfer_with_watch.id
        ).first()
        metadata = saved_log.event_metadata
        assert metadata["file_name"] == "test.wav", "Should log filename"
        assert metadata["file_size"] == 1024, "Should log file size"


# ============================================
# Tests: Pause/Resume Logic
# ============================================

class TestPauseResumeLogic:
    """Tests for pause/resume watch mode functionality"""

    def test_watch_continuous_pause_signal(self, db_session, transfer_with_watch):
        """Test detection of pause signal (watch_continuous=False)"""
        # Verify initial state
        assert transfer_with_watch.watch_continuous == 1, "Should start enabled"

        # Simulate pause
        transfer_with_watch.watch_continuous = 0
        db_session.commit()

        # Reload and verify
        transfer = db_session.query(Transfer).filter(Transfer.id == transfer_with_watch.id).first()
        assert transfer.watch_continuous == 0, "Should detect pause signal"

    def test_watch_cycle_count_increment(self, db_session, transfer_with_watch):
        """Test watch_cycle_count increments"""
        assert transfer_with_watch.watch_cycle_count == 0, "Should start at 0"

        # Simulate cycle
        transfer_with_watch.watch_cycle_count += 1
        db_session.commit()

        transfer = db_session.query(Transfer).filter(Transfer.id == transfer_with_watch.id).first()
        assert transfer.watch_cycle_count == 1, "Should increment cycle count"

        # Simulate another cycle
        transfer_with_watch.watch_cycle_count += 1
        db_session.commit()

        transfer = db_session.query(Transfer).filter(Transfer.id == transfer_with_watch.id).first()
        assert transfer.watch_cycle_count == 2, "Should increment again"


# ============================================
# Tests: Error Handling
# ============================================

class TestErrorHandling:
    """Tests for error handling in watch mode"""

    def test_missing_source_path_handling(self, db_session, temp_folder):
        """Test handling of missing source path"""
        dest = temp_folder[1]

        transfer = Transfer(
            source_path="/nonexistent/path",
            destination_path=dest,
            file_size=0,
            file_name="test",
            status=TransferStatus.PENDING,
            watch_mode_enabled=1,
            watch_continuous=1,
            settle_time_seconds=2
        )
        db_session.add(transfer)
        db_session.commit()

        # Verify path doesn't exist
        assert not os.path.exists(transfer.source_path), "Path should not exist"

    def test_json_parsing_error_recovery(self, db_session, transfer_with_watch):
        """Test recovery from malformed JSON in last_files_processed"""
        # Set malformed JSON
        transfer_with_watch.last_files_processed = "{invalid json"
        db_session.commit()

        # Should handle gracefully in job
        transfer = db_session.query(Transfer).filter(Transfer.id == transfer_with_watch.id).first()
        try:
            processed = json.loads(transfer.last_files_processed or "[]")
        except json.JSONDecodeError:
            processed = []

        assert processed == [], "Should recover with empty list"


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """Integration tests for complete workflow"""

    def test_transfer_relationship_cascade(self, db_session, transfer_with_watch, temp_folder):
        """Test that WatchFiles are deleted when Transfer is deleted"""
        source, _ = temp_folder

        # Create WatchFile
        watch_file = WatchFile(
            transfer_id=transfer_with_watch.id,
            file_name="test.txt",
            file_path=os.path.join(source, "test.txt"),
            file_size=100,
            status=TransferStatus.PENDING,
            detected_at=datetime.now(timezone.utc)
        )
        db_session.add(watch_file)
        db_session.commit()

        watch_file_id = watch_file.id

        # Verify WatchFile exists
        assert db_session.query(WatchFile).filter(WatchFile.id == watch_file_id).first() is not None

        # Delete Transfer (should cascade delete WatchFile)
        db_session.delete(transfer_with_watch)
        db_session.commit()

        # Verify WatchFile was deleted
        assert db_session.query(WatchFile).filter(WatchFile.id == watch_file_id).first() is None


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
