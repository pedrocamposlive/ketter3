"""
Ketter 3.0 - Database Models
SQLAlchemy models for transfers, checksums, and audit logs

MRC Principles:
- Simple schema design
- ACID compliance via PostgreSQL
- Complete audit trail
- Explicit status tracking
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime,
    Text, ForeignKey, Index, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


# Enums para status e tipos
class TransferStatus(str, Enum):
    """Status possíveis de uma transferência"""
    PENDING = "pending"           # Aguardando início
    VALIDATING = "validating"     # Validando espaço/permissões
    COPYING = "copying"           # Copiando arquivo
    VERIFYING = "verifying"       # Verificando checksums
    COMPLETED = "completed"       # Concluído com sucesso
    FAILED = "failed"             # Falhou
    CANCELLED = "cancelled"       # Cancelado pelo operador


class ChecksumType(str, Enum):
    """Tipos de checksum no fluxo triplo SHA-256"""
    SOURCE = "source"             # Checksum do arquivo original
    DESTINATION = "destination"   # Checksum do arquivo copiado
    FINAL = "final"               # Verificação final após cópia


class AuditEventType(str, Enum):
    """Tipos de eventos de auditoria"""
    TRANSFER_CREATED = "transfer_created"
    TRANSFER_STARTED = "transfer_started"
    TRANSFER_PROGRESS = "transfer_progress"
    CHECKSUM_CALCULATED = "checksum_calculated"
    CHECKSUM_VERIFIED = "checksum_verified"
    TRANSFER_COMPLETED = "transfer_completed"
    TRANSFER_FAILED = "transfer_failed"
    TRANSFER_CANCELLED = "transfer_cancelled"
    ERROR = "error"


def now_utc() -> datetime:
    """Return current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


class Transfer(Base):
    """
    Tabela principal de transferências

    Armazena informações sobre cada operação de cópia de arquivo.
    Princípios MRC:
    - Campos essenciais apenas
    - Status explícito
    - Timestamps para auditoria
    - Relacionamento com checksums
    """
    __tablename__ = "transfers"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # File information
    source_path = Column(String(4096), nullable=False)
    destination_path = Column(String(4096), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Bytes (suporta até ~9 exabytes)
    file_name = Column(String(512), nullable=False)

    # Transfer status
    status = Column(
        SQLEnum(TransferStatus),
        nullable=False,
        default=TransferStatus.PENDING,
        index=True
    )

    # Progress tracking
    bytes_transferred = Column(BigInteger, default=0)
    progress_percent = Column(Integer, default=0)  # 0-100

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=now_utc, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    # Week 5: ZIP Smart + Folder Support
    is_folder_transfer = Column(Integer, default=0)  # 0=file, 1=folder (SQLite compat)
    original_folder_path = Column(String(4096), nullable=True)  # Original folder path (if folder transfer)
    zip_file_path = Column(String(4096), nullable=True)  # Temp ZIP file path
    file_count = Column(Integer, nullable=True)  # Number of files in folder
    unzip_completed = Column(Integer, default=0)  # 0=no, 1=yes (destination unzipped)

    # Week 5: Watch Folder Intelligence
    watch_mode_enabled = Column(Integer, default=0)  # 0=no watch, 1=watch mode enabled
    settle_time_seconds = Column(Integer, default=30)  # Seconds to wait without changes
    watch_started_at = Column(DateTime, nullable=True)  # When watch monitoring began
    watch_triggered_at = Column(DateTime, nullable=True)  # When folder became stable

    # Week 6: Continuous Watch Mode (NEW) 
    watch_continuous = Column(Integer, default=0)  # 0=one-time, 1=continuous monitoring
    watch_job_id = Column(String(100), nullable=True)  # RQ job ID for watcher_continuous_job
    last_files_processed = Column(Text, nullable=True)  # JSON list of processed files
    watch_cycle_count = Column(Integer, default=0)  # Number of watch cycles completed

    # Week 6: Operation Mode (NEW) - COPY vs MOVE 
    operation_mode = Column(String(10), default="copy")  # "copy"=keep originals, "move"=delete after verification

    # Relationships
    checksums = relationship("Checksum", back_populates="transfer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="transfer", cascade="all, delete-orphan")
    watch_files = relationship("WatchFile", back_populates="transfer", cascade="all, delete-orphan")

    # Indexes para queries comuns
    __table_args__ = (
        Index('idx_transfer_status_created', 'status', 'created_at'),
        Index('idx_transfer_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Transfer(id={self.id}, file={self.file_name}, status={self.status})>"


class Checksum(Base):
    """
    Tabela de checksums SHA-256

    Implementa verificação tripla:
    1. SOURCE: Hash do arquivo original antes da cópia
    2. DESTINATION: Hash do arquivo copiado após a cópia
    3. FINAL: Verificação final comparando source e destination

    MRC: Simplicidade com tripla verificação para confiabilidade máxima
    """
    __tablename__ = "checksums"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, index=True)

    # Checksum data
    checksum_type = Column(SQLEnum(ChecksumType), nullable=False)
    checksum_value = Column(String(64), nullable=False)  # SHA-256 = 64 hex chars

    # Metadata
    calculated_at = Column(DateTime, nullable=False, default=now_utc)
    calculation_duration_seconds = Column(Integer, nullable=True)  # Tempo para calcular

    # Relationship
    transfer = relationship("Transfer", back_populates="checksums")

    # Indexes
    __table_args__ = (
        Index('idx_checksum_transfer_type', 'transfer_id', 'checksum_type'),
    )

    def __repr__(self):
        return f"<Checksum(id={self.id}, type={self.checksum_type}, value={self.checksum_value[:8]}...)>"


class AuditLog(Base):
    """
    Tabela de logs de auditoria

    Registra todos os eventos importantes de cada transferência.
    MRC: Transparência total - tudo é logado para rastreabilidade.

    Retenção: 30 dias conforme requisito MVP
    """
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False, index=True)

    # Event data
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Metadata flexível (JSON para dados adicionais)
    # Renamed from 'metadata' which is reserved by SQLAlchemy
    event_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=now_utc, index=True)

    # Relationship
    transfer = relationship("Transfer", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index('idx_audit_transfer_created', 'transfer_id', 'created_at'),
        Index('idx_audit_event_created', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, transfer_id={self.transfer_id}, event={self.event_type})>"


class WatchFile(Base):
    """
    Tabela de arquivos detectados por Watch Mode contínuo (NOVO - Week 6)

    Registra cada arquivo/pasta detectado pelo watcher_continuous_job.
    MRC: Rastreamento completo de cada detecção e transferência.

    Relacionamento:
    - Cada WatchFile está vinculado a um Transfer (1:N)
    - Cada WatchFile pode ter um transfer_job_id (RQ job que processou)
    """
    __tablename__ = "watch_files"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    transfer_id = Column(Integer, ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True)

    # File information
    file_name = Column(String(512), nullable=False)  # Just the filename (e.g., "drums.wav")
    file_path = Column(String(4096), nullable=False)  # Full path (e.g., "/sessoes/drums.wav")
    file_size = Column(BigInteger, nullable=True)  # Size in bytes (if available)

    # Transfer tracking
    transfer_job_id = Column(String(100), nullable=True)  # RQ job ID that processed this file
    status = Column(
        SQLEnum(TransferStatus),
        nullable=False,
        default=TransferStatus.PENDING,
        index=True
    )  # pending, copying, verifying, completed, failed

    # Checksum tracking
    source_checksum = Column(String(64), nullable=True)  # SHA-256 of source
    destination_checksum = Column(String(64), nullable=True)  # SHA-256 of destination
    checksum_match = Column(Integer, default=0)  # 0=no/unknown, 1=yes

    # Error tracking
    error_message = Column(Text, nullable=True)  # Error details if failed
    retry_count = Column(Integer, default=0)  # Number of retries

    # Timestamps
    detected_at = Column(DateTime, nullable=False, default=now_utc, index=True)  # When watcher found it
    transfer_started_at = Column(DateTime, nullable=True)  # When transfer started
    transfer_completed_at = Column(DateTime, nullable=True)  # When transfer completed

    # Relationship
    transfer = relationship("Transfer", back_populates="watch_files")

    # Indexes
    __table_args__ = (
        Index('idx_watch_file_transfer_detected', 'transfer_id', 'detected_at'),
        Index('idx_watch_file_status_transfer', 'status', 'transfer_id'),
    )

    def __repr__(self):
        return f"<WatchFile(id={self.id}, transfer_id={self.transfer_id}, file={self.file_name}, status={self.status})>"
