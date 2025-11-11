"""
Ketter 3.0 - Model Tests
Testes unitários para Transfer, Checksum, AuditLog

MRC: TDD desde Day 1
"""

import pytest
from datetime import datetime
from app.models import (
    Transfer, Checksum, AuditLog,
    TransferStatus, ChecksumType, AuditEventType
)


class TestTransferModel:
    """Testes para o modelo Transfer"""

    def test_create_transfer(self, db_session):
        """Testa criação de uma transferência"""
        transfer = Transfer(
            source_path="/source/video.mp4",
            destination_path="/dest/video.mp4",
            file_size=1024 * 1024 * 500,  # 500 MB
            file_name="video.mp4"
        )
        db_session.add(transfer)
        db_session.commit()

        assert transfer.id is not None
        assert transfer.status == TransferStatus.PENDING
        assert transfer.progress_percent == 0
        assert transfer.bytes_transferred == 0
        assert transfer.created_at is not None

    def test_transfer_status_enum(self, db_session):
        """Testa todos os status possíveis de transferência"""
        statuses = [
            TransferStatus.PENDING,
            TransferStatus.VALIDATING,
            TransferStatus.COPYING,
            TransferStatus.VERIFYING,
            TransferStatus.COMPLETED,
            TransferStatus.FAILED,
            TransferStatus.CANCELLED,
        ]

        for status in statuses:
            transfer = Transfer(
                source_path=f"/source/file_{status.value}.mp4",
                destination_path=f"/dest/file_{status.value}.mp4",
                file_size=1024,
                file_name=f"file_{status.value}.mp4",
                status=status
            )
            db_session.add(transfer)
            db_session.commit()
            assert transfer.status == status

    def test_transfer_relationship_checksums(self, db_session, sample_transfer):
        """Testa relacionamento Transfer -> Checksums"""
        # Adiciona checksums
        checksum1 = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value="a" * 64
        )
        checksum2 = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.DESTINATION,
            checksum_value="b" * 64
        )
        db_session.add_all([checksum1, checksum2])
        db_session.commit()

        # Verifica relacionamento
        db_session.refresh(sample_transfer)
        assert len(sample_transfer.checksums) == 2
        assert sample_transfer.checksums[0].checksum_type in [ChecksumType.SOURCE, ChecksumType.DESTINATION]

    def test_transfer_relationship_audit_logs(self, db_session, sample_transfer):
        """Testa relacionamento Transfer -> AuditLogs"""
        # Adiciona logs
        log1 = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Transfer created"
        )
        log2 = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_STARTED,
            message="Transfer started"
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        # Verifica relacionamento
        db_session.refresh(sample_transfer)
        assert len(sample_transfer.audit_logs) == 2

    def test_transfer_repr(self, sample_transfer):
        """Testa representação string do Transfer"""
        repr_str = repr(sample_transfer)
        assert "Transfer" in repr_str
        assert str(sample_transfer.id) in repr_str
        assert sample_transfer.file_name in repr_str


class TestChecksumModel:
    """Testes para o modelo Checksum"""

    def test_create_checksum(self, db_session, sample_transfer):
        """Testa criação de checksum"""
        checksum = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value="a1b2c3d4" * 8,  # 64 chars
            calculation_duration_seconds=10
        )
        db_session.add(checksum)
        db_session.commit()

        assert checksum.id is not None
        assert checksum.checksum_value == "a1b2c3d4" * 8
        assert checksum.calculated_at is not None
        assert checksum.calculation_duration_seconds == 10

    def test_checksum_types(self, db_session, sample_transfer):
        """Testa todos os tipos de checksum (triplo)"""
        types = [
            ChecksumType.SOURCE,
            ChecksumType.DESTINATION,
            ChecksumType.FINAL
        ]

        for checksum_type in types:
            checksum = Checksum(
                transfer_id=sample_transfer.id,
                checksum_type=checksum_type,
                checksum_value="x" * 64
            )
            db_session.add(checksum)
            db_session.commit()
            assert checksum.checksum_type == checksum_type

    def test_checksum_sha256_length(self, db_session, sample_transfer):
        """Testa que checksum aceita SHA-256 (64 hex chars)"""
        valid_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        checksum = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value=valid_sha256
        )
        db_session.add(checksum)
        db_session.commit()

        assert len(checksum.checksum_value) == 64
        assert checksum.checksum_value == valid_sha256

    def test_checksum_repr(self, db_session, sample_transfer):
        """Testa representação string do Checksum"""
        checksum = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value="a" * 64
        )
        db_session.add(checksum)
        db_session.commit()

        repr_str = repr(checksum)
        assert "Checksum" in repr_str
        assert "SOURCE" in repr_str


class TestAuditLogModel:
    """Testes para o modelo AuditLog"""

    def test_create_audit_log(self, db_session, sample_transfer):
        """Testa criação de audit log"""
        log = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Transfer created successfully",
            event_metadata={"user": "operator1", "source": "web_ui"}
        )
        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.event_type == AuditEventType.TRANSFER_CREATED
        assert log.message == "Transfer created successfully"
        assert log.event_metadata["user"] == "operator1"
        assert log.created_at is not None

    def test_audit_event_types(self, db_session, sample_transfer):
        """Testa todos os tipos de eventos de auditoria"""
        events = [
            AuditEventType.TRANSFER_CREATED,
            AuditEventType.TRANSFER_STARTED,
            AuditEventType.TRANSFER_PROGRESS,
            AuditEventType.CHECKSUM_CALCULATED,
            AuditEventType.CHECKSUM_VERIFIED,
            AuditEventType.TRANSFER_COMPLETED,
            AuditEventType.TRANSFER_FAILED,
            AuditEventType.TRANSFER_CANCELLED,
            AuditEventType.ERROR,
        ]

        for event in events:
            log = AuditLog(
                transfer_id=sample_transfer.id,
                event_type=event,
                message=f"Event: {event.value}"
            )
            db_session.add(log)
            db_session.commit()
            assert log.event_type == event

    def test_audit_log_metadata_json(self, db_session, sample_transfer):
        """Testa que event_metadata aceita JSON complexo"""
        complex_metadata = {
            "user": "admin",
            "ip": "192.168.1.100",
            "timestamp": "2025-11-04T22:00:00",
            "details": {
                "bytes": 1024,
                "duration": 10.5
            }
        }

        log = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message="Progress update",
            event_metadata=complex_metadata
        )
        db_session.add(log)
        db_session.commit()

        assert log.event_metadata["user"] == "admin"
        assert log.event_metadata["details"]["bytes"] == 1024
        assert log.event_metadata["details"]["duration"] == 10.5

    def test_audit_log_repr(self, db_session, sample_transfer):
        """Testa representação string do AuditLog"""
        log = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Test log"
        )
        db_session.add(log)
        db_session.commit()

        repr_str = repr(log)
        assert "AuditLog" in repr_str
        assert str(sample_transfer.id) in repr_str


class TestModelIntegration:
    """Testes de integração entre modelos"""

    def test_complete_transfer_workflow(self, db_session):
        """
        Testa fluxo completo de transferência:
        1. Cria transfer
        2. Adiciona checksums (source, destination, final)
        3. Adiciona audit logs
        4. Completa transfer
        """
        # 1. Criar transfer
        transfer = Transfer(
            source_path="/media/original/video.mp4",
            destination_path="/backup/video.mp4",
            file_size=1024 * 1024 * 1024,  # 1 GB
            file_name="video.mp4"
        )
        db_session.add(transfer)
        db_session.commit()

        # 2. Log criação
        log1 = AuditLog(
            transfer_id=transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Transfer created"
        )
        db_session.add(log1)
        db_session.commit()

        # 3. Calcular checksum source
        checksum_source = Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value="abc123" * 10 + "abcd",  # 64 chars
            calculation_duration_seconds=15
        )
        db_session.add(checksum_source)
        db_session.commit()

        # 4. Iniciar transfer
        transfer.status = TransferStatus.COPYING
        transfer.started_at = datetime.utcnow()
        db_session.commit()

        # 5. Calcular checksum destination
        checksum_dest = Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.DESTINATION,
            checksum_value="abc123" * 10 + "abcd",  # Mesmo hash
            calculation_duration_seconds=15
        )
        db_session.add(checksum_dest)
        db_session.commit()

        # 6. Verificação final
        checksum_final = Checksum(
            transfer_id=transfer.id,
            checksum_type=ChecksumType.FINAL,
            checksum_value="abc123" * 10 + "abcd",
            calculation_duration_seconds=1
        )
        db_session.add(checksum_final)
        db_session.commit()

        # 7. Completar
        transfer.status = TransferStatus.COMPLETED
        transfer.completed_at = datetime.utcnow()
        transfer.progress_percent = 100
        transfer.bytes_transferred = transfer.file_size
        db_session.commit()

        # 8. Log conclusão
        log2 = AuditLog(
            transfer_id=transfer.id,
            event_type=AuditEventType.TRANSFER_COMPLETED,
            message="Transfer completed successfully",
            event_metadata={"duration_seconds": 30}
        )
        db_session.add(log2)
        db_session.commit()

        # Verificações finais
        db_session.refresh(transfer)
        assert transfer.status == TransferStatus.COMPLETED
        assert len(transfer.checksums) == 3
        assert len(transfer.audit_logs) == 2
        assert all(c.checksum_value == "abc123" * 10 + "abcd" for c in transfer.checksums)

    def test_cascade_delete(self, db_session, sample_transfer):
        """
        Testa que ao deletar Transfer, checksums e logs são deletados (CASCADE)
        """
        # Adiciona checksums e logs
        checksum = Checksum(
            transfer_id=sample_transfer.id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value="x" * 64
        )
        log = AuditLog(
            transfer_id=sample_transfer.id,
            event_type=AuditEventType.TRANSFER_CREATED,
            message="Test"
        )
        db_session.add_all([checksum, log])
        db_session.commit()

        # Confirma que existem
        assert db_session.query(Checksum).filter_by(transfer_id=sample_transfer.id).count() == 1
        assert db_session.query(AuditLog).filter_by(transfer_id=sample_transfer.id).count() == 1

        # Deleta transfer
        db_session.delete(sample_transfer)
        db_session.commit()

        # Verifica cascade delete
        assert db_session.query(Checksum).filter_by(transfer_id=sample_transfer.id).count() == 0
        assert db_session.query(AuditLog).filter_by(transfer_id=sample_transfer.id).count() == 0
