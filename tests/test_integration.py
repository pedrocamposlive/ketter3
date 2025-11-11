"""
Ketter 3.0 - End-to-End Integration Tests
Tests complete workflows: API → Worker → Database → PDF

MRC: Test real scenarios that operators will use
"""

import os
import time
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Transfer, Checksum, AuditLog, TransferStatus, ChecksumType


# Test database configuration
TEST_DATABASE_URL = "postgresql://ketter:ketter123@postgres:5432/ketter"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_file():
    """Create a temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/data/transfers', prefix='test_', suffix='.txt') as f:
        f.write("This is integration test content.\n" * 100)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture(scope="function")
def destination_path():
    """Generate destination path"""
    dest = f"/data/transfers/test_dest_{int(time.time())}.txt"
    yield dest

    # Cleanup
    if os.path.exists(dest):
        os.remove(dest)


class TestCompleteTransferWorkflow:
    """Test the complete transfer workflow end-to-end"""

    def test_full_transfer_lifecycle(self, test_file, destination_path):
        """
        Test complete transfer from creation to completion

        Steps:
        1. Create transfer via API
        2. Verify transfer is enqueued
        3. Wait for worker to process
        4. Verify transfer completed
        5. Verify triple SHA-256 checksums
        6. Verify audit trail
        7. Verify destination file exists
        """
        # Step 1: Create transfer
        response = client.post("/transfers", json={
            "source_path": test_file,
            "destination_path": destination_path
        })
        assert response.status_code == 201
        data = response.json()
        transfer_id = data["id"]
        assert data["status"] == "pending"

        # Step 2: Verify transfer in database
        response = client.get(f"/transfers/{transfer_id}")
        assert response.status_code == 200
        assert response.json()["status"] in ["pending", "validating", "copying", "verifying", "completed"]

        # Step 3: Wait for worker to process (max 30 seconds)
        max_wait = 30
        wait_interval = 1
        elapsed = 0

        while elapsed < max_wait:
            response = client.get(f"/transfers/{transfer_id}")
            transfer = response.json()

            if transfer["status"] == "completed":
                break
            elif transfer["status"] == "failed":
                pytest.fail(f"Transfer failed: {transfer.get('error_message')}")

            time.sleep(wait_interval)
            elapsed += wait_interval

        # Step 4: Verify transfer completed
        response = client.get(f"/transfers/{transfer_id}")
        assert response.status_code == 200
        transfer = response.json()
        assert transfer["status"] == "completed"
        assert transfer["progress_percent"] == 100
        assert transfer["bytes_transferred"] > 0
        assert transfer["completed_at"] is not None

        # Step 5: Verify triple SHA-256 checksums
        response = client.get(f"/transfers/{transfer_id}/checksums")
        assert response.status_code == 200
        checksums = response.json()
        assert len(checksums["items"]) == 3  # SOURCE, DESTINATION, FINAL

        # Verify all checksums are present and match
        checksum_types = {c["checksum_type"] for c in checksums["items"]}
        assert checksum_types == {"source", "destination", "final"}

        source_hash = next(c["checksum_value"] for c in checksums["items"] if c["checksum_type"] == "source")
        dest_hash = next(c["checksum_value"] for c in checksums["items"] if c["checksum_type"] == "destination")
        final_hash = next(c["checksum_value"] for c in checksums["items"] if c["checksum_type"] == "final")

        assert source_hash == dest_hash == final_hash
        assert len(source_hash) == 64  # SHA-256 = 64 hex characters

        # Step 6: Verify audit trail
        response = client.get(f"/transfers/{transfer_id}/logs")
        assert response.status_code == 200
        logs = response.json()
        assert logs["total"] >= 10  # At least 10 audit events

        # Verify key events are logged
        event_types = {log["event_type"] for log in logs["items"]}
        assert "transfer_created" in event_types
        assert "transfer_started" in event_types
        assert "checksum_calculated" in event_types
        assert "checksum_verified" in event_types
        assert "transfer_completed" in event_types

        # Step 7: Verify destination file exists and matches source
        assert os.path.exists(destination_path)

        with open(test_file, 'rb') as f1, open(destination_path, 'rb') as f2:
            assert f1.read() == f2.read()

    def test_transfer_with_pdf_report(self, test_file, destination_path):
        """
        Test transfer completion with PDF report generation

        Steps:
        1. Create and complete transfer
        2. Generate PDF report
        3. Verify PDF is valid
        """
        # Step 1: Create transfer
        response = client.post("/transfers", json={
            "source_path": test_file,
            "destination_path": destination_path
        })
        assert response.status_code == 201
        transfer_id = response.json()["id"]

        # Wait for completion
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            response = client.get(f"/transfers/{transfer_id}")
            if response.json()["status"] == "completed":
                break
            time.sleep(1)
            elapsed += 1

        # Step 2: Generate PDF report
        response = client.get(f"/transfers/{transfer_id}/report")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # Step 3: Verify PDF is valid (starts with PDF header)
        pdf_content = response.content
        assert pdf_content.startswith(b"%PDF-1.4")
        assert len(pdf_content) > 1000  # PDF should have content


class TestTransferErrorHandling:
    """Test error handling in transfers"""

    def test_transfer_nonexistent_file(self):
        """Test transfer with non-existent source file"""
        response = client.post("/transfers", json={
            "source_path": "/nonexistent/file.txt",
            "destination_path": "/tmp/dest.txt"
        })
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_transfer_directory_as_source(self, tmp_path):
        """Test transfer with directory as source (should succeed with Week 5 ZIP Smart)"""
        # Create a test directory with files
        test_dir = tmp_path / "source_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        response = client.post("/transfers", json={
            "source_path": str(test_dir),
            "destination_path": str(tmp_path / "dest_dir")
        })
        # Week 5: Directory transfers are now supported via ZIP Smart
        assert response.status_code == 201
        assert "id" in response.json()

    def test_get_nonexistent_transfer(self):
        """Test getting non-existent transfer"""
        response = client.get("/transfers/999999")
        assert response.status_code == 404

    def test_delete_nonexistent_transfer(self):
        """Test deleting non-existent transfer"""
        response = client.delete("/transfers/999999")
        assert response.status_code == 404


class TestTransferHistory:
    """Test transfer history functionality"""

    def test_recent_transfers(self, test_file, destination_path):
        """Test getting recent transfer history"""
        # Create a transfer
        response = client.post("/transfers", json={
            "source_path": test_file,
            "destination_path": destination_path
        })
        assert response.status_code == 201

        # Get recent transfers
        response = client.get("/transfers/history/recent?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

    def test_transfer_deletion(self, test_file, destination_path):
        """Test transfer deletion with cascade"""
        # Create transfer
        response = client.post("/transfers", json={
            "source_path": test_file,
            "destination_path": destination_path
        })
        transfer_id = response.json()["id"]

        # Wait for completion
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            response = client.get(f"/transfers/{transfer_id}")
            if response.json()["status"] in ["completed", "failed"]:
                break
            time.sleep(1)
            elapsed += 1

        # Delete transfer
        response = client.delete(f"/transfers/{transfer_id}")
        assert response.status_code == 204

        # Verify transfer is deleted
        response = client.get(f"/transfers/{transfer_id}")
        assert response.status_code == 404

        # Verify checksums are deleted (cascade)
        response = client.get(f"/transfers/{transfer_id}/checksums")
        assert response.status_code == 404


class TestSystemStatus:
    """Test system health and status"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_status_endpoint(self):
        """Test detailed status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "worker" in data


class TestConcurrentTransfers:
    """Test handling of multiple concurrent transfers"""

    def test_multiple_transfers(self):
        """Test creating multiple transfers simultaneously"""
        transfers = []

        # Create 3 test files and transfers
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/data/transfers',
                                             prefix=f'concurrent_{i}_', suffix='.txt') as f:
                f.write(f"Concurrent test content {i}\n" * 50)
                source = f.name

            dest = f"/data/transfers/concurrent_dest_{i}_{int(time.time())}.txt"

            response = client.post("/transfers", json={
                "source_path": source,
                "destination_path": dest
            })
            assert response.status_code == 201
            transfers.append((response.json()["id"], source, dest))

        # Wait for all transfers to complete
        max_wait = 60
        for transfer_id, source, dest in transfers:
            elapsed = 0
            while elapsed < max_wait:
                response = client.get(f"/transfers/{transfer_id}")
                status = response.json()["status"]
                if status in ["completed", "failed"]:
                    assert status == "completed"
                    break
                time.sleep(1)
                elapsed += 1

            # Cleanup
            if os.path.exists(source):
                os.remove(source)
            if os.path.exists(dest):
                os.remove(dest)


def test_complete_system_integration():
    """
    Final integration test: Verify entire system works together

    This test validates:
    - Database connectivity
    - Redis connectivity
    - Worker functionality
    - API endpoints
    - Copy engine
    - Checksum verification
    - Audit trail
    - PDF generation
    """
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/data/transfers',
                                     prefix='final_test_', suffix='.txt') as f:
        f.write("Final integration test content.\n" * 200)
        source = f.name

    dest = f"/data/transfers/final_dest_{int(time.time())}.txt"

    try:
        # Create transfer
        response = client.post("/transfers", json={
            "source_path": source,
            "destination_path": dest
        })
        assert response.status_code == 201
        transfer_id = response.json()["id"]

        # Wait for completion
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            response = client.get(f"/transfers/{transfer_id}")
            if response.json()["status"] == "completed":
                break
            time.sleep(1)
            elapsed += 1

        # Verify all components
        response = client.get(f"/transfers/{transfer_id}")
        assert response.json()["status"] == "completed"

        response = client.get(f"/transfers/{transfer_id}/checksums")
        assert len(response.json()["items"]) == 3

        response = client.get(f"/transfers/{transfer_id}/logs")
        assert response.json()["total"] >= 10

        response = client.get(f"/transfers/{transfer_id}/report")
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-1.4")

        assert os.path.exists(dest)

    finally:
        # Cleanup
        if os.path.exists(source):
            os.remove(source)
        if os.path.exists(dest):
            os.remove(dest)
