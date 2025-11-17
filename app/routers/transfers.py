"""
Ketter 3.0 - Transfers API Endpoints
REST API for file transfer operations

MRC Principles:
- Simple, clear endpoints
- Proper HTTP status codes
- Complete error handling
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from rq import Queue
from redis import Redis

from app.database import get_db
from app.models import Transfer, Checksum, AuditLog, TransferStatus, AuditEventType, WatchFile
from app.schemas import (
    TransferCreate, TransferResponse, TransferListResponse,
    ChecksumResponse, ChecksumListResponse,
    AuditLogResponse, AuditLogListResponse,
    WatchFileResponse, WatchHistoryResponse,
    ErrorResponse
)
from app.services.worker_jobs import (
    transfer_file_job,
    watch_and_transfer_job,
    TRANSFER_JOB_CONFIG,
    WATCH_TRANSFER_JOB_CONFIG,
)
from app.utils.pdf_generator import generate_transfer_report, get_transfer_report_filename

# Redis/RQ setup
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
transfer_queue = Queue("default", connection=redis_conn)

# Router configuration
router = APIRouter(
    prefix="/transfers",
    tags=["transfers"],
    responses={404: {"model": ErrorResponse}},
)


@router.post("", response_model=TransferResponse, status_code=201)
def create_transfer(
    transfer: TransferCreate,
    db: Session = Depends(get_db)
):
    """
    Cria uma nova transferência de arquivo ou pasta

    **Week 5: Supports ZIP Smart + Watch Mode**
    - Aceita arquivo ou pasta
    - Se pasta: será zipado automaticamente (STORE mode)
    - Se watch_mode: aguarda estabilidade antes de transferir
    - Calcula file_size
    - Extrai file_name
    - Cria registro no database
    - Cria audit log inicial

    Returns:
        TransferResponse: Transferência criada com status PENDING
    """
    # Check if source exists
    if not os.path.exists(transfer.source_path):
        raise HTTPException(
            status_code=400,
            detail=f"Source path does not exist: {transfer.source_path}"
        )

    # Detectar se é arquivo ou pasta (Week 5: ZIP Smart)
    is_file = os.path.isfile(transfer.source_path)
    is_directory = os.path.isdir(transfer.source_path)

    if not is_file and not is_directory:
        raise HTTPException(
            status_code=400,
            detail=f"Source path is neither file nor directory: {transfer.source_path}"
        )

    # Obter informações
    if is_file:
        file_size = os.path.getsize(transfer.source_path)
        file_name = os.path.basename(transfer.source_path)
    else:
        # É pasta - file_size será calculado pelo ZIP Engine
        # Por enquanto, colocamos 0 (será atualizado)
        file_size = 0
        file_name = os.path.basename(transfer.source_path.rstrip('/'))

    # Criar transferência
    db_transfer = Transfer(
        source_path=transfer.source_path,
        destination_path=transfer.destination_path,
        file_size=file_size,
        file_name=file_name,
        status=TransferStatus.PENDING,
        # Week 5: Watch Mode fields
        watch_mode_enabled=1 if transfer.watch_mode_enabled else 0,
        settle_time_seconds=transfer.settle_time_seconds,
        # Week 6: Continuous Watch Mode (NEW)
        watch_continuous=1 if transfer.watch_continuous else 0,
        # Week 6: Operation Mode (NEW) - COPY vs MOVE
        operation_mode=transfer.operation_mode
    )
    db.add(db_transfer)
    db.commit()
    db.refresh(db_transfer)

    # Criar audit log inicial
    audit_log = AuditLog(
        transfer_id=db_transfer.id,
        event_type=AuditEventType.TRANSFER_CREATED,
        message=f"Transfer created: {file_name} ({file_size} bytes)",
        event_metadata={
            "source": transfer.source_path,
            "destination": transfer.destination_path,
            "file_size": file_size
        }
    )
    db.add(audit_log)
    db.commit()

    # Enfileirar job RQ para processar transferência
    # Week 5: Use watch_and_transfer_job if watch mode is enabled
    # Week 6: Use watcher_continuous_job if continuous watch mode is enabled
    try:
        if transfer.watch_continuous:
            # Continuous watch mode (Week 6): enqueue watcher_continuous_job
            from app.services.worker_jobs import watcher_continuous_job, WATCH_CONTINUOUS_JOB_CONFIG

            job = transfer_queue.enqueue(
                watcher_continuous_job,
                db_transfer.id,
                job_timeout=WATCH_CONTINUOUS_JOB_CONFIG.get("timeout", 86400),
                result_ttl=WATCH_CONTINUOUS_JOB_CONFIG.get("result_ttl", 500),
                failure_ttl=WATCH_CONTINUOUS_JOB_CONFIG.get("failure_ttl", 86400)
            )

            # Atualizar transfer com job ID e timestamps
            db_transfer.watch_job_id = job.id
            db_transfer.watch_started_at = datetime.now(timezone.utc)
            db.flush()  # Flush to sync object state

            # Log job enqueued
            job_log = AuditLog(
                transfer_id=db_transfer.id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Continuous watch job enqueued: {job.id} (settle time: {transfer.settle_time_seconds}s)",
                event_metadata={
                    "job_id": job.id,
                    "queue": "default",
                    "watch_mode": True,
                    "watch_continuous": True,
                    "settle_time": transfer.settle_time_seconds
                }
            )
            db.add(job_log)
            db.commit()

        elif transfer.watch_mode_enabled:
            # Watch mode (settle-time once): enqueue watch_and_transfer_job
            job = transfer_queue.enqueue(
                watch_and_transfer_job,
                db_transfer.id,
                job_timeout=WATCH_TRANSFER_JOB_CONFIG["timeout"],
                result_ttl=WATCH_TRANSFER_JOB_CONFIG["result_ttl"],
                failure_ttl=WATCH_TRANSFER_JOB_CONFIG["failure_ttl"]
            )

            # Log job enqueued
            job_log = AuditLog(
                transfer_id=db_transfer.id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Watch + Transfer job enqueued: {job.id} (settle time: {transfer.settle_time_seconds}s)",
                event_metadata={
                    "job_id": job.id,
                    "queue": "default",
                    "watch_mode": True,
                    "settle_time": transfer.settle_time_seconds
                }
            )
            db.add(job_log)
            db.commit()
        else:
            # Normal mode: enqueue transfer_file_job
            job = transfer_queue.enqueue(
                transfer_file_job,
                db_transfer.id,
                job_timeout=TRANSFER_JOB_CONFIG["timeout"],
                result_ttl=TRANSFER_JOB_CONFIG["result_ttl"],
                failure_ttl=TRANSFER_JOB_CONFIG["failure_ttl"]
            )

            # Log job enqueued
            job_log = AuditLog(
                transfer_id=db_transfer.id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Transfer job enqueued: {job.id}",
                event_metadata={"job_id": job.id, "queue": "default"}
            )
            db.add(job_log)
            db.commit()

    except Exception as e:
        # Se falhar ao enfileirar, marca como failed
        db_transfer.status = TransferStatus.FAILED
        db_transfer.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue transfer job: {str(e)}"
        )

    return db_transfer


@router.get("", response_model=TransferListResponse)
def list_transfers(
    status: Optional[TransferStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as transferências

    **Filtros:**
    - status: Filtra por status (PENDING, COPYING, COMPLETED, etc.)
    - limit: Número máximo de resultados (default: 100, max: 1000)
    - offset: Paginação (default: 0)

    **Ordenação:** Por created_at DESC (mais recentes primeiro)

    Returns:
        TransferListResponse: Lista de transferências
    """
    # Query base
    query = db.query(Transfer)

    # Aplicar filtro de status se fornecido
    if status:
        query = query.filter(Transfer.status == status)

    # Contar total (antes de limit/offset)
    total = query.count()

    # Aplicar ordenação e paginação
    transfers = query.order_by(Transfer.created_at.desc()).limit(limit).offset(offset).all()

    return TransferListResponse(total=total, items=transfers)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de uma transferência específica

    Args:
        transfer_id: ID da transferência

    Returns:
        TransferResponse: Detalhes da transferência

    Raises:
        HTTPException 404: Se transferência não existe
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    return transfer


@router.get("/{transfer_id}/checksums", response_model=ChecksumListResponse)
def get_transfer_checksums(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém todos os checksums de uma transferência

    **Triple SHA-256 Verification:**
    - SOURCE: Checksum do arquivo original
    - DESTINATION: Checksum do arquivo copiado
    - FINAL: Verificação final (comparação)

    Args:
        transfer_id: ID da transferência

    Returns:
        ChecksumListResponse: Lista de checksums

    Raises:
        HTTPException 404: Se transferência não existe
    """
    # Verifica se transfer existe
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Busca checksums
    checksums = db.query(Checksum).filter(Checksum.transfer_id == transfer_id).order_by(Checksum.calculated_at).all()

    return ChecksumListResponse(transfer_id=transfer_id, items=checksums)


@router.get("/{transfer_id}/logs", response_model=AuditLogListResponse)
def get_transfer_logs(
    transfer_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db)
):
    """
    Obtém audit trail completo de uma transferência

    **MRC: Transparência total - todos os eventos são logados**

    Eventos incluem:
    - TRANSFER_CREATED
    - TRANSFER_STARTED
    - TRANSFER_PROGRESS
    - CHECKSUM_CALCULATED
    - CHECKSUM_VERIFIED
    - TRANSFER_COMPLETED / FAILED / CANCELLED
    - ERROR

    Args:
        transfer_id: ID da transferência
        limit: Número máximo de logs (default: 100, max: 1000)
        offset: Paginação (default: 0)

    Returns:
        AuditLogListResponse: Lista de audit logs

    Raises:
        HTTPException 404: Se transferência não existe
    """
    # Verifica se transfer existe
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Query logs
    query = db.query(AuditLog).filter(AuditLog.transfer_id == transfer_id)
    total = query.count()

    # Ordenar por created_at (cronológico) e aplicar paginação
    logs = query.order_by(AuditLog.created_at).limit(limit).offset(offset).all()

    return AuditLogListResponse(transfer_id=transfer_id, total=total, items=logs)


@router.delete("/{transfer_id}", status_code=204)
def delete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Deleta uma transferência

    **CASCADE DELETE:**
    - Deleta transfer
    - Deleta automaticamente todos os checksums associados
    - Deleta automaticamente todos os audit logs associados

    Args:
        transfer_id: ID da transferência

    Returns:
        204 No Content: Transferência deletada com sucesso

    Raises:
        HTTPException 404: Se transferência não existe
        HTTPException 400: Se transferência está em andamento
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Validação: não permitir deletar transfer em andamento
    if transfer.status in [TransferStatus.COPYING, TransferStatus.VERIFYING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete transfer in progress (status: {transfer.status})"
        )

    # Delete (cascade irá deletar checksums e logs automaticamente)
    db.delete(transfer)
    db.commit()

    return None


@router.get("/{transfer_id}/report")
def get_transfer_report(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Gera e retorna relatório PDF profissional da transferência

    **Conteúdo do Relatório:**
    - Resumo da transferência (ID, status, tamanhos, datas)
    - Caminhos de origem e destino
    - Triple SHA-256 verification completa
    - Status de verificação (PASS/FAIL)
    - Audit trail completo com todos os eventos
    - Informações de erro (se houver)

    Args:
        transfer_id: ID da transferência

    Returns:
        PDF file: Relatório profissional em PDF

    Raises:
        HTTPException 404: Se transferência não existe
    """
    # Verifica se transfer existe
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Busca checksums (triple SHA-256)
    checksums = db.query(Checksum).filter(
        Checksum.transfer_id == transfer_id
    ).order_by(Checksum.calculated_at).all()

    # Busca audit logs (complete trail)
    audit_logs = db.query(AuditLog).filter(
        AuditLog.transfer_id == transfer_id
    ).order_by(AuditLog.created_at).all()

    # Gera PDF
    try:
        pdf_buffer = generate_transfer_report(transfer, checksums, audit_logs)
        pdf_content = pdf_buffer.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

    # Retorna PDF como download
    filename = get_transfer_report_filename(transfer)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/history/recent", response_model=TransferListResponse)
def get_recent_transfers(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Obtém histórico de transferências recentes

    **MVP Requirement:** Manter histórico de 30 dias

    Args:
        days: Número de dias para retornar (default: 30, max: 365)

    Returns:
        TransferListResponse: Transferências dos últimos N dias
    """
    from datetime import timedelta

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    transfers = db.query(Transfer).filter(
        Transfer.created_at >= cutoff_date
    ).order_by(Transfer.created_at.desc()).all()

    return TransferListResponse(total=len(transfers), items=transfers)


# ============================================
# Watch Mode Continuous Endpoints (Week 6)
# ============================================

@router.post("/{transfer_id}/pause-watch", status_code=200)
def pause_watch_mode(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Pausa o monitoramento contínuo de uma transferência (Watch Mode Contínuo)

    **Behavior:**
    - Marca watch_continuous como False
    - Cancela RQ job associado (watch_job_id)
    - Registra evento de auditoria
    - Transferências em progresso continuam até completar
    - Novas detecções não serão processadas

    Args:
        transfer_id: ID da transferência em watch mode

    Returns:
        TransferResponse: Transferência atualizada com watch_continuous=False

    Raises:
        HTTPException 404: Se transferência não existe
        HTTPException 400: Se transferência não está em watch mode contínuo
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Validar que está em watch mode contínuo
    if not transfer.watch_continuous:
        raise HTTPException(
            status_code=400,
            detail=f"Transfer {transfer_id} is not in continuous watch mode"
        )

    # Cancelar RQ job se existe
    if transfer.watch_job_id:
        try:
            from rq.job import Job
            job = Job.fetch(transfer.watch_job_id, connection=redis_conn)
            job.cancel()
        except Exception as e:
            # Log silenciosamente se job não existir mais
            pass

    # Atualizar status
    transfer.watch_continuous = 0
    transfer.watch_job_id = None

    # Registrar auditoria
    audit_log = AuditLog(
        transfer_id=transfer_id,
        event_type=AuditEventType.TRANSFER_PROGRESS,
        message=f"Continuous watch mode paused",
        event_metadata={
            "action": "pause_watch",
            "watch_cycle_count": transfer.watch_cycle_count,
            "job_id": transfer.watch_job_id
        }
    )
    db.add(audit_log)
    db.commit()
    db.refresh(transfer)

    return transfer


@router.post("/{transfer_id}/resume-watch", status_code=200)
def resume_watch_mode(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Retoma o monitoramento contínuo de uma transferência pausada (Watch Mode Contínuo)

    **Behavior:**
    - Marca watch_continuous como True
    - Enfileira novo RQ job (watcher_continuous_job)
    - Registra evento de auditoria
    - Volta a detectar e transferir novos arquivos
    - watch_cycle_count é mantido (não é resetado)

    Args:
        transfer_id: ID da transferência

    Returns:
        TransferResponse: Transferência atualizada com novo watch_job_id

    Raises:
        HTTPException 404: Se transferência não existe
        HTTPException 400: Se transferência não está pausada
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Validar que está pausada ou que é uma transferência watch-enabled
    if transfer.watch_continuous:
        raise HTTPException(
            status_code=400,
            detail=f"Transfer {transfer_id} is already in continuous watch mode"
        )

    if not transfer.watch_mode_enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Transfer {transfer_id} does not have watch mode enabled"
        )

    # Enfileirar novo watcher_continuous_job
    # NOTA: watcher_continuous_job será implementado em FASE 3
    try:
        # Import aqui para evitar erro circular se job não existir yet
        try:
            from app.services.worker_jobs import watcher_continuous_job, WATCH_CONTINUOUS_JOB_CONFIG
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Continuous watch job implementation not ready yet (FASE 3)"
            )

        job = transfer_queue.enqueue(
            watcher_continuous_job,
            transfer_id,
            job_timeout=WATCH_CONTINUOUS_JOB_CONFIG.get("timeout", 86400),
            result_ttl=WATCH_CONTINUOUS_JOB_CONFIG.get("result_ttl", 500),
            failure_ttl=WATCH_CONTINUOUS_JOB_CONFIG.get("failure_ttl", 86400)
        )

        # Atualizar transfer
        transfer.watch_continuous = 1
        transfer.watch_job_id = job.id

        # Registrar auditoria
        audit_log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message=f"Continuous watch mode resumed with job {job.id}",
            event_metadata={
                "action": "resume_watch",
                "job_id": job.id,
                "watch_cycle_count": transfer.watch_cycle_count
            }
        )
        db.add(audit_log)
        db.commit()
        db.refresh(transfer)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume watch mode: {str(e)}"
        )

    return transfer


@router.get("/{transfer_id}/watch-history", response_model=WatchHistoryResponse)
def get_watch_history(
    transfer_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of files"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    db: Session = Depends(get_db)
):
    """
    Obtém histórico completo de arquivos detectados pelo Watch Mode Contínuo

    **Week 6: Watch Mode Continuous History**

    **Response:**
    - transfer_id: ID da transferência watch
    - total_files_detected: Total de arquivos detectados desde o início
    - total_files_completed: Total completado com sucesso
    - total_files_failed: Total que falhou
    - last_detection: Último arquivo detectado (timestamp)
    - watch_started_at: Quando começou a monitorar
    - files[]: Listagem de WatchFile (paginada)

    **Cada WatchFile contém:**
    - file_name, file_path: Identificação do arquivo
    - status: pending, copying, verifying, completed, failed
    - detected_at: Quando foi detectado
    - transfer_started_at, transfer_completed_at: Timeline de transferência
    - source_checksum, destination_checksum, checksum_match: Verificação
    - error_message, retry_count: Se falhou

    Args:
        transfer_id: ID da transferência watch
        limit: Máximo de arquivos para retornar (default: 100, max: 1000)
        offset: Paginação (default: 0)

    Returns:
        WatchHistoryResponse: Histórico estruturado de detecções e transferências

    Raises:
        HTTPException 404: Se transferência não existe
    """
    # Verifica se transfer existe
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Validar que é uma transferência com watch mode
    if not transfer.watch_mode_enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Transfer {transfer_id} does not have watch mode enabled"
        )

    # Query watch_files
    query = db.query(WatchFile).filter(WatchFile.transfer_id == transfer_id)

    # Contar totais
    total_detected = query.count()
    total_completed = query.filter(WatchFile.status == TransferStatus.COMPLETED).count()
    total_failed = query.filter(WatchFile.status == TransferStatus.FAILED).count()

    # Buscar última detecção
    last_detection = query.order_by(WatchFile.detected_at.desc()).first()
    last_detection_at = last_detection.detected_at if last_detection else None

    # Aplicar paginação
    files = query.order_by(WatchFile.detected_at.desc()).limit(limit).offset(offset).all()

    return WatchHistoryResponse(
        transfer_id=transfer_id,
        total_files_detected=total_detected,
        total_files_completed=total_completed,
        total_files_failed=total_failed,
        last_detection=last_detection_at,
        watch_started_at=transfer.watch_started_at,
        files=files
    )


@router.post("/{transfer_id}/cancel", status_code=200)
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an active transfer

    Transfers can be cancelled in any active state:
    - pending: Not yet started
    - validating: Pre-transfer checks
    - copying: File copy in progress
    - verifying: Checksum verification

    Completed and failed transfers cannot be cancelled.
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail=f"Transfer {transfer_id} not found")

    active_statuses = ["pending", "validating", "copying", "verifying"]
    transfer_status = transfer.status.value if hasattr(transfer.status, 'value') else str(transfer.status).lower()

    if transfer_status not in active_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel transfer with status '{transfer_status}'. Only active transfers (pending, validating, copying, verifying) can be cancelled."
        )

    try:
        # Update transfer status to FAILED with cancellation message
        old_status = transfer.status
        transfer.status = TransferStatus.FAILED
        transfer.error_message = "Transfer cancelled by user"
        transfer.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Log cancellation with previous status
        from app.models import AuditLog
        audit_log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.ERROR,
            message=f"Transfer cancelled by user (was {old_status})",
            metadata={"previous_status": old_status, "cancelled_by": "user"}
        )
        db.add(audit_log)
        db.commit()

        return {
            "success": True,
            "message": f"Transfer {transfer_id} cancelled successfully (was {old_status})",
            "transfer_id": transfer_id,
            "status": transfer.status,
            "previous_status": old_status
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel transfer: {str(e)}"
        )
