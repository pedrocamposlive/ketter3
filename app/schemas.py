"""
Ketter 3.0 - Pydantic Schemas
Request/Response validation schemas

MRC: Simple, explicit validation
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models import TransferStatus, ChecksumType, AuditEventType


# ============================================
# Transfer Schemas
# ============================================

class TransferCreate(BaseModel):
    """
    Schema para criar uma transferência
    Request: POST /transfers

    Week 5: Supports folder transfers with ZIP Smart + Watch Mode
    """
    source_path: str = Field(..., min_length=1, max_length=4096, description="Caminho do arquivo/pasta original")
    destination_path: str = Field(..., min_length=1, max_length=4096, description="Caminho de destino")

    # Week 5: Watch Mode
    watch_mode_enabled: bool = Field(default=False, description="Aguardar pasta estabilizar antes de transferir")
    settle_time_seconds: int = Field(default=30, ge=5, le=300, description="Segundos sem mudanças = estável")

    # Week 5: Operation Mode
    operation_mode: str = Field(default='copy', description="Modo de transferência: 'copy' ou 'move'")

    # Week 6: Continuous Watch Mode
    is_continuous_watch: bool = Field(default=False, description="Ativar monitoramento contínuo - a cada novo arquivo na origem, transferir automaticamente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_path": "/media/protools_session/",
                "destination_path": "/backup/protools_session/",
                "watch_mode_enabled": True,
                "settle_time_seconds": 30,
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

    # Week 5: Operation Mode field
    operation_mode: str = 'copy'

    # Week 6: Continuous Watch Mode fields
    is_continuous_watch: bool = False
    last_watch_check_at: Optional[datetime] = None
    continuous_files_transferred: int = 0

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
# Error Schemas
# ============================================

class ErrorResponse(BaseModel):
    """
    Schema padrão para respostas de erro
    """
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Transfer not found",
                "detail": "Transfer with ID 123 does not exist",
                "timestamp": "2025-11-04T22:30:00"
            }
        }
    )
