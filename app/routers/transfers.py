"""
Ketter 3.0 - Transfers API Endpoints
REST API for file transfer operations

MRC Principles:
- Simple, clear endpoints
- Proper HTTP status codes
- Complete error handling
"""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from rq import Queue
from redis import Redis

from app.database import get_db
from app.models import Transfer, Checksum, AuditLog, TransferStatus, AuditEventType
from app.schemas import (
    TransferCreate, TransferResponse, TransferListResponse,
    ChecksumResponse, ChecksumListResponse,
    AuditLogResponse, AuditLogListResponse,
    ErrorResponse
)
from app.worker_jobs import transfer_file_job, watch_and_transfer_job, TRANSFER_JOB_CONFIG, WATCH_TRANSFER_JOB_CONFIG
from app.pdf_generator import generate_transfer_report, get_transfer_report_filename

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
        status=TransferStatus.PENDING,  # Começará no worker como MONITORING se continuous_watch
        # Week 5: Watch Mode fields
        watch_mode_enabled=1 if transfer.watch_mode_enabled else 0,
        settle_time_seconds=transfer.settle_time_seconds,
        # Week 5: Operation Mode
        operation_mode=transfer.operation_mode,
        # Week 6: Continuous Watch Mode
        is_continuous_watch=1 if transfer.is_continuous_watch else 0,
        watched_files_processed=[]
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
    # Week 6: Support for continuous watch mode
    # Week 5: Use watch_and_transfer_job if watch mode is enabled
    try:
        if transfer.is_continuous_watch:
            # Continuous watch mode: import and enqueue continuous_watch_job
            from app.worker_jobs import continuous_watch_job, CONTINUOUS_WATCH_JOB_CONFIG
            job = transfer_queue.enqueue(
                continuous_watch_job,
                db_transfer.id,
                job_timeout=CONTINUOUS_WATCH_JOB_CONFIG["timeout"],
                result_ttl=CONTINUOUS_WATCH_JOB_CONFIG["result_ttl"],
                failure_ttl=CONTINUOUS_WATCH_JOB_CONFIG["failure_ttl"]
            )

            # Log job enqueued
            job_log = AuditLog(
                transfer_id=db_transfer.id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Continuous watch job enqueued: {job.id} - Monitorando pasta {transfer.source_path}",
                event_metadata={
                    "job_id": job.id,
                    "queue": "default",
                    "continuous_watch": True,
                    "operation_mode": transfer.operation_mode
                }
            )
            db.add(job_log)
            db.commit()
        elif transfer.watch_mode_enabled:
            # Watch mode: enqueue watch_and_transfer_job
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

    **Week 6: Improved UX**
    - Permite deletar transferências em qualquer status
    - Cancela jobs RQ se necessário
    - Marca como CANCELLED antes de deletar

    Args:
        transfer_id: ID da transferência

    Returns:
        204 No Content: Transferência deletada com sucesso

    Raises:
        HTTPException 404: Se transferência não existe
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail=f"Transfer with ID {transfer_id} not found"
        )

    # Se transferência está em progresso, cancelar o job RQ primeiro
    if transfer.status in [TransferStatus.PENDING, TransferStatus.COPYING, TransferStatus.VERIFYING]:
        try:
            from rq.job import Job
            from redis import Redis
            import os

            redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

            # Try to find and stop the job
            jobs = transfer_queue.get_job_ids()
            for job_id in jobs:
                try:
                    job = Job.fetch(job_id, connection=redis_conn)
                    if job and (
                        (job.func_name == "app.worker_jobs.transfer_file_job" and len(job.args) > 0 and job.args[0] == transfer_id) or
                        (job.func_name == "app.worker_jobs.continuous_watch_job" and len(job.args) > 0 and job.args[0] == transfer_id) or
                        (job.func_name == "app.worker_jobs.watch_and_transfer_job" and len(job.args) > 0 and job.args[0] == transfer_id)
                    ):
                        job.cancel()
                        print(f"Cancelled RQ job {job_id} for transfer {transfer_id}")
                        break
                except Exception:
                    pass  # Skip if job not found
        except Exception as e:
            print(f"Warning: Could not cancel RQ job: {str(e)}")

        # Mark as cancelled before deleting
        transfer.status = TransferStatus.CANCELLED
        transfer.completed_at = datetime.utcnow()
        transfer.error_message = "Deleted by user"
        db.commit()

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


@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancela uma transferência em progresso

    **Week 6: Cancel Transfer in Progress**

    Cancela o job RQ de transferência e marca como CANCELLED.
    Funciona para:
    - Transferências regulares em PENDING, COPYING, VERIFYING
    - Continuous watch transfers
    - Watch mode transfers

    Args:
        transfer_id: ID da transferência para cancelar

    Returns:
        TransferResponse: Transferência atualizada com status CANCELLED
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail=f"Transfer {transfer_id} not found")

    # Validação: só permitir cancelar transferências em progresso
    CANCELLABLE_STATUSES = [
        TransferStatus.PENDING,
        TransferStatus.COPYING,
        TransferStatus.VERIFYING
    ]

    if transfer.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel transfer in status {transfer.status}. Only pending/copying/verifying transfers can be cancelled."
        )

    # Tentar cancelar job RQ se estiver rodando
    try:
        from rq.job import Job
        from redis import Redis
        import os

        redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

        # Search for the job in the queue
        jobs = transfer_queue.get_job_ids()
        for job_id in jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                # Check multiple job types
                if job and (
                    (job.func_name == "app.worker_jobs.transfer_file_job" and len(job.args) > 0 and job.args[0] == transfer_id) or
                    (job.func_name == "app.worker_jobs.continuous_watch_job" and len(job.args) > 0 and job.args[0] == transfer_id) or
                    (job.func_name == "app.worker_jobs.watch_and_transfer_job" and len(job.args) > 0 and job.args[0] == transfer_id)
                ):
                    job.cancel()
                    print(f"Cancelled RQ job {job_id} for transfer {transfer_id}")
                    break
            except Exception as e:
                print(f"Could not fetch job {job_id}: {str(e)}")
    except Exception as e:
        print(f"Warning: Error cancelling RQ job: {str(e)}")

    # Update transfer status to CANCELLED
    transfer.status = TransferStatus.CANCELLED
    transfer.completed_at = datetime.utcnow()
    transfer.error_message = "Cancelled by user"
    db.commit()

    # Log the cancellation
    audit_log = AuditLog(
        transfer_id=transfer_id,
        event_type=AuditEventType.TRANSFER_CANCELLED,
        message=f"Transferência cancelada manualmente pelo usuário",
        event_metadata={
            "previous_status": str(transfer.status),
            "cancelled_at": datetime.utcnow().isoformat(),
            "bytes_transferred": transfer.bytes_transferred
        }
    )
    db.add(audit_log)
    db.commit()

    return transfer


@router.post("/{transfer_id}/stop-watch", response_model=TransferResponse)
def stop_continuous_watch(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    """
    Para o monitoramento contínuo de uma transferência

    **Week 6: Stop Continuous Watch Mode**

    Cancela o job RQ de watch contínuo e marca a transferência como COMPLETED.
    As transferências individuais de arquivos realizadas já foram salvas no histórico.

    Args:
        transfer_id: ID da transferência com watch contínuo ativo

    Returns:
        TransferResponse: Transferência atualizada com status COMPLETED
    """
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail=f"Transfer {transfer_id} not found")

    if not transfer.is_continuous_watch:
        raise HTTPException(
            status_code=400,
            detail=f"Transfer {transfer_id} is not in continuous watch mode"
        )

    # Stop RQ job if it exists
    try:
        # Find the job in Redis
        from rq.job import Job
        from redis import Redis
        import os

        redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

        # Try to find and stop the job
        # Jobs in RQ are typically stored with key "rq:job:{job_id}"
        # We'll search for active jobs in the transfer queue
        queue_key = "rq:queue:default"
        try:
            jobs = transfer_queue.get_job_ids()
            for job_id in jobs:
                job = Job.fetch(job_id, connection=redis_conn)
                # Check if this job is for our transfer
                if job and job.func_name == "app.worker_jobs.continuous_watch_job":
                    if len(job.args) > 0 and job.args[0] == transfer_id:
                        job.cancel()
                        print(f"Cancelled RQ job {job_id} for transfer {transfer_id}")
                        break
        except Exception as e:
            print(f"Warning: Could not cancel RQ job: {str(e)}")

    except Exception as e:
        print(f"Warning: Error accessing RQ: {str(e)}")

    # Update transfer status
    transfer.status = TransferStatus.COMPLETED
    transfer.completed_at = datetime.utcnow()
    db.commit()

    # Log the stop action
    audit_log = AuditLog(
        transfer_id=transfer_id,
        event_type=AuditEventType.TRANSFER_PROGRESS,
        message=f"Monitoramento contínuo parado manualmente. Total de arquivos transferidos: {transfer.continuous_files_transferred}",
        event_metadata={
            "files_transferred": transfer.continuous_files_transferred,
            "watch_duration": int((transfer.completed_at - transfer.created_at).total_seconds()) if transfer.completed_at else 0
        }
    )
    db.add(audit_log)
    db.commit()

    return transfer


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

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    transfers = db.query(Transfer).filter(
        Transfer.created_at >= cutoff_date
    ).order_by(Transfer.created_at.desc()).all()

    return TransferListResponse(total=len(transfers), items=transfers)
