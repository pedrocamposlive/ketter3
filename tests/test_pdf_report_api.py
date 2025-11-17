"""
Integration test that mimics the UI "Download Report" button by calling
`GET /transfers/{id}/report` and validating the returned PDF structure.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session

from app.database import reset_db, SessionLocal
from app.main import app
from app.models import (
    Transfer,
    Checksum,
    ChecksumType,
    AuditLog,
    AuditEventType,
    TransferStatus,
)


@pytest.fixture(autouse=True)
def prepare_database():
    """Ensure a clean database for each test case."""
    reset_db()
    yield


def _seed_transfer(db_session: Session) -> Transfer:
    """Creates a completed transfer with checksums and audit logs."""
    now = datetime.now(timezone.utc)
    transfer = Transfer(
        source_path="/tmp/source.bin",
        destination_path="/tmp/dest.bin",
        file_size=1024 * 1024,
        file_name="source.bin",
        status=TransferStatus.COMPLETED,
        bytes_transferred=1024 * 1024,
        progress_percent=100,
        started_at=now - timedelta(seconds=120),
        completed_at=now,
        created_at=now - timedelta(seconds=180),
        updated_at=now,
        operation_mode="copy",
    )
    db_session.add(transfer)
    db_session.commit()
    db_session.refresh(transfer)

    base_hash = "b" * 64
    checksums = [
        Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value=base_hash,
            calculated_at=now - timedelta(seconds=90),
        ),
        Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.DESTINATION,
            checksum_value=base_hash,
            calculated_at=now - timedelta(seconds=60),
        ),
        Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.FINAL,
            checksum_value=base_hash,
            calculated_at=now - timedelta(seconds=30),
        ),
    ]
    db_session.add_all(checksums)

    audit_logs = [
        AuditLog(
            transfer_id=transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Transfer created via integration test",
            created_at=now - timedelta(seconds=170),
        ),
        AuditLog(
            transfer_id=transfer.id,
            event_type=AuditEventType.CHECKSUM_VERIFIED,
            message="Checksums verified",
            created_at=now - timedelta(seconds=80),
        ),
        AuditLog(
            transfer_id=transfer.id,
            event_type=AuditEventType.TRANSFER_COMPLETED,
            message="Transfer completed successfully",
            created_at=now - timedelta(seconds=10),
        ),
    ]
    db_session.add_all(audit_logs)
    db_session.commit()
    return transfer


def test_download_report_endpoint_returns_three_page_pdf_with_audit():
    """Simulates the UI download flow and validates the generated PDF."""
    db = SessionLocal()
    transfer = _seed_transfer(db)
    client = TestClient(app)

    response = client.get(f"/transfers/{transfer.id}/report")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    content = response.content
    assert content.startswith(b"%PDF-1.4")
    assert content.count(b"/Type /Page") >= 3
    assert len(content) > 4000, "PDF appears too small for a three-section report"
    disposition = response.headers.get("content-disposition", "")
    assert disposition.startswith("attachment; filename=\"ketter_report_")

    db.close()
