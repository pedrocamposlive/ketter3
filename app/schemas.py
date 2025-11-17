"""
Ketter 3.0 - Pydantic Schemas
Request/Response validation schemas

MRC: Simple, explicit validation
ENHANCE #1: Path sanitization and security validation
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models import TransferStatus, ChecksumType, AuditEventType
from app.security.path_security import sanitize_path, validate_path_pair, PathSecurityError


# ============================================
# Transfer Schemas
# ============================================

class TransferCreate(BaseModel):
    """
    Schema para criar uma transferência
    Request: POST /transfers

    Week 5: Supports folder transfers with ZIP Smart + Watch Mode
    Week 6: Continuous watch mode support (NEW)
    """
    source_path: str = Field(..., min_length=1, max_length=4096, description="Caminho do arquivo/pasta original")
    destination_path: str = Field(..., min_length=1, max_length=4096, description="Caminho de destino")

    # Week 5: Watch Mode (one-time settle)
    watch_mode_enabled: bool = Field(default=False, description="Aguardar pasta estabilizar antes de transferir")
    settle_time_seconds: int = Field(default=30, ge=5, le=300, description="Segundos sem mudanças = estável")

    # Week 6: Continuous Watch Mode (NEW) 
    watch_continuous: bool = Field(default=False, description="Continuous monitoring - detect and transfer files indefinitely")

    # Week 6: Operation Mode (NEW) - COPY vs MOVE
    operation_mode: str = Field(default="copy", description="'copy' keeps originals, 'move' deletes after verification", pattern="^(copy|move)$")

    @field_validator('source_path')
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        """
        SECURITY VALIDATION: Sanitize source path

        Protects against:
        - Path traversal attacks (../)
        - Symlinks pointing outside volumes
        - Access to unauthorized directories

        ENHANCE #1: Path security validation
        """
        try:
            # Sanitize and validate (allow symlinks for source)
            safe_path = sanitize_path(v, allow_symlinks=True)
            return safe_path
        except PathSecurityError as e:
            raise ValueError(f"Invalid source path: {e}")

    @field_validator('destination_path')
    @classmethod
    def validate_destination_path(cls, v: str) -> str:
        """
        SECURITY VALIDATION: Sanitize destination path

        Protects against:
        - Path traversal attacks (../)
        - Symlinks (not allowed for destination)
        - Access to unauthorized directories

        ENHANCE #1: Path security validation
        """
        try:
            # Sanitize and validate (no symlinks for destination)
            safe_path = sanitize_path(v, allow_symlinks=False)
            return safe_path
        except PathSecurityError as e:
            raise ValueError(f"Invalid destination path: {e}")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_path": "/media/protools_session/",
                "destination_path": "/backup/protools_session/",
                "watch_mode_enabled": True,
                "settle_time_seconds": 30,
                "watch_continuous": True,
                "operation_mode": "copy"
            }
        }
    )


class TransferUpdate(BaseModel):
    """
    Schema para atualizar status de uma transferência
    Request: PATCH /transfers/{id}
    """
    status: Optional[TransferStatus] = None
    bytes_transferred: Optional[int] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None


class TransferResponse(BaseModel):
    """
    Schema de resposta de uma transferência
    Response: GET /transfers, GET /transfers/{id}, POST /transfers

    Week 5: Includes folder and watch mode fields
    """
    id: int
    source_path: str
    destination_path: str
    file_size: int
    file_name: str
    status: TransferStatus
    bytes_transferred: int
    progress_percent: int
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime

    # Week 5: ZIP Smart fields
    is_folder_transfer: bool = False
    original_folder_path: Optional[str] = None
    zip_file_path: Optional[str] = None
    file_count: Optional[int] = None
    unzip_completed: bool = False

    # Week 5: Watch Mode fields
    watch_mode_enabled: bool = False
    settle_time_seconds: int = 30
    watch_started_at: Optional[datetime] = None
    watch_triggered_at: Optional[datetime] = None

    # Week 6: Continuous Watch Mode fields (NEW) 
    watch_continuous: bool = False
    watch_job_id: Optional[str] = None
    last_files_processed: Optional[str] = None
    watch_cycle_count: int = 0

    # Week 6: Operation Mode fields (NEW) - COPY vs MOVE 
    operation_mode: str = "copy"

    model_config = ConfigDict(from_attributes=True)


class TransferListResponse(BaseModel):
    """
    Schema de resposta para lista de transferências
    Response: GET /transfers
    """
    total: int
    items: List[TransferResponse]


# ============================================
# Checksum Schemas
# ============================================

class ChecksumResponse(BaseModel):
    """
    Schema de resposta de checksum
    Response: GET /transfers/{id}/checksums
    """
    id: int
    transfer_id: int
    checksum_type: ChecksumType
    checksum_value: str
    calculated_at: datetime
    calculation_duration_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ChecksumListResponse(BaseModel):
    """
    Schema de resposta para lista de checksums
    Response: GET /transfers/{id}/checksums
    """
    transfer_id: int
    items: List[ChecksumResponse]


# ============================================
# AuditLog Schemas
# ============================================

class AuditLogResponse(BaseModel):
    """
    Schema de resposta de audit log
    Response: GET /transfers/{id}/logs
    """
    id: int
    transfer_id: int
    event_type: AuditEventType
    message: str
    event_metadata: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """
    Schema de resposta para lista de audit logs
    Response: GET /transfers/{id}/logs
    """
    transfer_id: int
    total: int
    items: List[AuditLogResponse]


# ============================================
# Health & Status Schemas
# ============================================

class HealthResponse(BaseModel):
    """
    Schema de resposta de health check
    Response: GET /health
    """
    status: str
    service: str
    version: str
    timestamp: datetime
    environment: str
    database: bool = False
    redis: bool = False


class StatusResponse(BaseModel):
    """
    Schema de resposta de status detalhado
    Response: GET /status
    """
    api: str
    database: str
    redis: str
    worker: str
    version: str
    timestamp: datetime


# ============================================
# WatchFile Schemas (NEW - Week 6) 
# ============================================

class WatchFileResponse(BaseModel):
    """
    Schema de resposta de arquivo detectado por watch mode
    Response: GET /transfers/{id}/watch-history
    """
    id: int
    transfer_id: int
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    transfer_job_id: Optional[str] = None
    status: TransferStatus
    source_checksum: Optional[str] = None
    destination_checksum: Optional[str] = None
    checksum_match: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    detected_at: datetime
    transfer_started_at: Optional[datetime] = None
    transfer_completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WatchHistoryResponse(BaseModel):
    """
    Schema de resposta para histórico de watch mode
    Response: GET /transfers/{id}/watch-history
    """
    transfer_id: int
    total_files_detected: int
    total_files_completed: int
    total_files_failed: int
    last_detection: Optional[datetime] = None
    watch_started_at: Optional[datetime] = None
    files: List[WatchFileResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Error Schemas
# ============================================

class ErrorResponse(BaseModel):
    """
    Schema padrão para respostas de erro
    """
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Transfer not found",
                "detail": "Transfer with ID 123 does not exist",
                "timestamp": "2025-11-04T22:30:00"
            }
        }
    )
