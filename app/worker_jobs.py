"""
Ketter 3.0 - RQ Worker Jobs
Background jobs for async file transfer processing

MRC Principles:
- Simple job definitions
- Clear error handling
- Complete logging

Week 5: Watch Folder Intelligence support
"""

import os
from datetime import datetime
from rq import get_current_job
from app.database import SessionLocal
from app.copy_engine import transfer_file_with_verification, CopyEngineError
from app.watch_folder import watch_folder_until_stable, WatchFolderError
from app.models import Transfer, AuditLog, AuditEventType, TransferStatus


def transfer_file_job(transfer_id: int) -> dict:
    """
    RQ Job: Executa transferência de arquivo com verificação SHA-256

    **MRC: Main worker job - processes file transfers asynchronously**

    Este job:
    1. Recebe transfer_id
    2. Obtém sessão do database
    3. Executa transfer_file_with_verification()
    4. Retorna resultado

    Args:
        transfer_id: ID da transferência a processar

    Returns:
        dict: Resultado da transferência
            - success: bool
            - transfer_id: int
            - message: str
            - checksum: str (se sucesso)
            - error: str (se falha)

    Raises:
        Exception: Propaga exceções para RQ retry mechanism
    """
    job = get_current_job()
    db = SessionLocal()

    try:
        # Log job start
        print(f"[RQ Job {job.id}] Starting transfer {transfer_id}")

        # Execute transfer with verification
        transfer = transfer_file_with_verification(
            transfer_id=transfer_id,
            db=db,
            progress_callback=None  # TODO: Implementar progress via Redis/RQ meta
        )

        # Get final checksum
        from app.models import Checksum, ChecksumType
        final_checksum = db.query(Checksum).filter(
            Checksum.transfer_id == transfer_id,
            Checksum.checksum_type == ChecksumType.FINAL
        ).first()

        result = {
            "success": True,
            "transfer_id": transfer_id,
            "message": f"Transfer completed successfully: {transfer.file_name}",
            "checksum": final_checksum.checksum_value if final_checksum else None,
            "file_size": transfer.file_size,
            "bytes_transferred": transfer.bytes_transferred
        }

        print(f"[RQ Job {job.id}] Transfer {transfer_id} completed ✓")
        return result

    except CopyEngineError as e:
        error_msg = f"Copy engine error: {str(e)}"
        print(f"[RQ Job {job.id}] Transfer {transfer_id} failed: {error_msg}")

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Transfer failed",
            "error": error_msg
        }
        return result

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[RQ Job {job.id}] Transfer {transfer_id} error: {error_msg}")

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Transfer failed with unexpected error",
            "error": error_msg
        }

        # Re-raise for RQ retry mechanism
        raise

    finally:
        db.close()


def watch_and_transfer_job(transfer_id: int) -> dict:
    """
    RQ Job: Watch folder until stable, then execute transfer

    **Week 5: Watch Folder Intelligence**

    Este job:
    1. Verifica se watch_mode está habilitado
    2. Se SIM: aguarda pasta estabilizar (settle time detection)
    3. Marca watch_triggered_at quando estável
    4. Executa transfer_file_job() normal

    Args:
        transfer_id: ID da transferência a processar

    Returns:
        dict: Resultado da transferência
            - success: bool
            - transfer_id: int
            - message: str
            - watch_duration: int (seconds waited)
            - checksum: str (se sucesso)
            - error: str (se falha)

    Raises:
        Exception: Propaga exceções para RQ retry mechanism
    """
    job = get_current_job()
    db = SessionLocal()

    try:
        # Load transfer
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise ValueError(f"Transfer {transfer_id} not found")

        # Check if watch mode is enabled
        if transfer.watch_mode_enabled:
            print(f"[RQ Job {job.id}] Watch mode enabled for transfer {transfer_id}")

            # Log watch start
            transfer.watch_started_at = datetime.utcnow()
            db.commit()

            log = AuditLog(
                transfer_id=transfer_id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Watch mode: Monitoring folder for stability (settle time: {transfer.settle_time_seconds}s)",
                event_metadata={"settle_time": transfer.settle_time_seconds}
            )
            db.add(log)
            db.commit()

            # Progress callback for watch
            def watch_progress(elapsed, max_wait, checks_done):
                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.TRANSFER_PROGRESS,
                    message=f"Watch mode: Checking folder stability... (elapsed: {elapsed}s, checks: {checks_done})",
                    event_metadata={"elapsed": elapsed, "checks": checks_done}
                )
                db.add(log)
                db.commit()

            # Watch folder until stable
            became_stable = watch_folder_until_stable(
                folder_path=transfer.source_path,
                settle_time_seconds=transfer.settle_time_seconds,
                max_wait_seconds=3600,  # Max 1 hour
                progress_callback=watch_progress
            )

            if not became_stable:
                # Timeout - folder never stabilized
                error_msg = f"Watch timeout: Folder did not stabilize within 1 hour"
                print(f"[RQ Job {job.id}] {error_msg}")

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.ERROR,
                    message=error_msg
                )
                db.add(log)
                db.commit()

                return {
                    "success": False,
                    "transfer_id": transfer_id,
                    "message": "Watch mode timeout",
                    "error": error_msg
                }

            # Folder is stable!
            transfer.watch_triggered_at = datetime.utcnow()
            db.commit()

            watch_duration = int((transfer.watch_triggered_at - transfer.watch_started_at).total_seconds())

            log = AuditLog(
                transfer_id=transfer_id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Watch mode: Folder is stable after {watch_duration}s. Starting transfer...",
                event_metadata={"watch_duration": watch_duration}
            )
            db.add(log)
            db.commit()

            print(f"[RQ Job {job.id}] Folder stable after {watch_duration}s, starting transfer")

        # Execute normal transfer
        print(f"[RQ Job {job.id}] Starting transfer {transfer_id}")

        transfer_result = transfer_file_with_verification(
            transfer_id=transfer_id,
            db=db,
            progress_callback=None
        )

        # Get final checksum
        from app.models import Checksum, ChecksumType
        final_checksum = db.query(Checksum).filter(
            Checksum.transfer_id == transfer_id,
            Checksum.checksum_type == ChecksumType.FINAL
        ).first()

        result = {
            "success": True,
            "transfer_id": transfer_id,
            "message": f"Transfer completed successfully: {transfer_result.file_name}",
            "checksum": final_checksum.checksum_value if final_checksum else None,
            "file_size": transfer_result.file_size,
            "bytes_transferred": transfer_result.bytes_transferred
        }

        if transfer.watch_mode_enabled and transfer.watch_triggered_at:
            watch_duration = int((transfer.watch_triggered_at - transfer.watch_started_at).total_seconds())
            result["watch_duration"] = watch_duration

        print(f"[RQ Job {job.id}] Transfer {transfer_id} completed ✓")
        return result

    except WatchFolderError as e:
        error_msg = f"Watch folder error: {str(e)}"
        print(f"[RQ Job {job.id}] Transfer {transfer_id} failed: {error_msg}")

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Watch mode failed",
            "error": error_msg
        }
        return result

    except CopyEngineError as e:
        error_msg = f"Copy engine error: {str(e)}"
        print(f"[RQ Job {job.id}] Transfer {transfer_id} failed: {error_msg}")

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Transfer failed",
            "error": error_msg
        }
        return result

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[RQ Job {job.id}] Transfer {transfer_id} error: {error_msg}")

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Transfer failed with unexpected error",
            "error": error_msg
        }

        # Re-raise for RQ retry mechanism
        raise

    finally:
        db.close()


def continuous_watch_job(transfer_id: int) -> dict:
    """
    RQ Job: Monitor source folder continuously and transfer new files

    **Week 6: Continuous Watch Mode**

    Este job:
    1. Monitora pasta de origem continuamente (a cada 30 segundos)
    2. Detecta NOVOS arquivos (que não foram processados antes)
    3. Para cada novo arquivo:
       - Aplica operação COPY ou MOVE conforme configurado
       - Cria registro de transferência individual
       - Atualiza lista de arquivos processados
    4. Continua monitorando indefinidamente até ser cancelado

    Args:
        transfer_id: ID da transferência monitor (contém paths e config)

    Returns:
        dict: Status do monitoramento

    Raises:
        Exception: Propaga exceções para RQ retry mechanism
    """
    import time
    import json
    from pathlib import Path

    job = get_current_job()
    db = SessionLocal()

    try:
        # Load transfer config
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise ValueError(f"Transfer {transfer_id} not found")

        if not transfer.is_continuous_watch:
            raise ValueError(f"Transfer {transfer_id} is not configured for continuous watch")

        source_path = transfer.source_path
        dest_path = transfer.destination_path
        operation_mode = transfer.operation_mode  # 'copy' or 'move'

        print(f"[RQ Job {job.id}] Starting continuous watch for transfer {transfer_id}")
        print(f"  Source: {source_path}")
        print(f"  Destination: {dest_path}")
        print(f"  Operation Mode: {operation_mode}")

        # Log watch start
        transfer.status = TransferStatus.COPYING  # Use COPYING as "in progress" state
        db.commit()

        log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message=f"Continuous watch mode started - Monitorando {source_path} para novos arquivos",
            event_metadata={"operation_mode": operation_mode, "check_interval": 30}
        )
        db.add(log)
        db.commit()

        processed_files = transfer.watched_files_processed if transfer.watched_files_processed else []
        check_count = 0

        # Continuous monitoring loop
        while True:
            try:
                check_count += 1
                transfer.last_watch_check_at = datetime.utcnow()
                db.commit()

                # Get current files in source
                if os.path.isfile(source_path):
                    # Single file - don't monitor single files continuously
                    print(f"[RQ Job {job.id}] Source is a file, not a folder. Continuous watch not applicable.")
                    break
                elif os.path.isdir(source_path):
                    # Get all items (files AND folders) at top level ONLY
                    current_items = []
                    try:
                        for item in os.listdir(source_path):
                            item_path = os.path.join(source_path, item)
                            # Add all items (files and folders) - use just the name as identifier
                            current_items.append(item)
                    except Exception as list_error:
                        print(f"[RQ Job {job.id}] Error listing source: {str(list_error)}")
                        current_items = []

                    # Find new items (files or folders)
                    new_items = [i for i in current_items if i not in processed_files]

                    if new_items:
                        print(f"[RQ Job {job.id}] Found {len(new_items)} new items to transfer")

                        for new_item_name in new_items:
                            source_item = os.path.join(source_path, new_item_name)
                            dest_item = os.path.join(dest_path, new_item_name)

                            print(f"[RQ Job {job.id}] Processing: {new_item_name}")

                            try:
                                import shutil
                                from app.copy_engine import transfer_file_with_verification, CopyEngineError

                                # PASTA (DIRECTORY)
                                if os.path.isdir(source_item):
                                    print(f"[RQ Job {job.id}] Processing folder: {new_item_name}")

                                    # Ensure destination folder structure exists
                                    os.makedirs(dest_item, exist_ok=True)

                                    # Copy entire folder recursively maintaining structure
                                    try:
                                        # Use shutil to copy entire directory tree
                                        if os.path.exists(dest_item):
                                            shutil.rmtree(dest_item)  # Remove dest if exists to avoid conflicts
                                        shutil.copytree(source_item, dest_item)

                                        log_msg = f"Pasta copiada: {new_item_name} → {dest_item}"
                                        print(f"[RQ Job {job.id}] ✓ Copied folder: {new_item_name}")

                                        # If MOVE mode, delete the source folder after successful copy
                                        if operation_mode == 'move':
                                            try:
                                                shutil.rmtree(source_item)
                                                log_msg = f"Pasta copiada e DELETADA: {new_item_name} (MOVE mode)"
                                                print(f"[RQ Job {job.id}] ✓ Moved folder: {new_item_name}")
                                            except Exception as delete_error:
                                                log_msg = f"Pasta copiada mas FALHA ao deletar: {new_item_name} - {str(delete_error)}"
                                                print(f"[RQ Job {job.id}] ⚠ Copied folder but failed to delete: {new_item_name}")

                                        # Mark item as processed
                                        processed_files.append(new_item_name)
                                        transfer.watched_files_processed = processed_files
                                        transfer.continuous_files_transferred += 1
                                        db.commit()

                                        # Log success
                                        log = AuditLog(
                                            transfer_id=transfer_id,
                                            event_type=AuditEventType.TRANSFER_PROGRESS,
                                            message=log_msg,
                                            event_metadata={"item": new_item_name, "type": "folder", "operation": operation_mode}
                                        )
                                        db.add(log)
                                        db.commit()

                                    except Exception as folder_error:
                                        error_msg = f"Failed to process folder {new_item_name}: {str(folder_error)}"
                                        print(f"[RQ Job {job.id}] ✗ {error_msg}")
                                        log = AuditLog(
                                            transfer_id=transfer_id,
                                            event_type=AuditEventType.ERROR,
                                            message=error_msg
                                        )
                                        db.add(log)
                                        db.commit()

                                # ARQUIVO (FILE)
                                elif os.path.isfile(source_item):
                                    print(f"[RQ Job {job.id}] Processing file: {new_item_name}")

                                    # Ensure destination directory exists
                                    os.makedirs(os.path.dirname(dest_item), exist_ok=True)

                                    # Create a temporary transfer record for this file
                                    temp_transfer = Transfer(
                                        source_path=source_item,
                                        destination_path=dest_item,
                                        file_size=os.path.getsize(source_item),
                                        file_name=new_item_name,
                                        status=TransferStatus.PENDING,
                                        operation_mode=operation_mode,
                                        parent_transfer_id=transfer_id
                                    )
                                    db.add(temp_transfer)
                                    db.commit()

                                    # Execute transfer
                                    result_transfer = transfer_file_with_verification(
                                        transfer_id=temp_transfer.id,
                                        db=db,
                                        progress_callback=None
                                    )

                                    # If MOVE mode, delete the source file after successful transfer
                                    if operation_mode == 'move':
                                        try:
                                            os.remove(source_item)
                                            log_msg = f"Arquivo transferido e DELETADO: {new_item_name} (MOVE mode)"
                                            print(f"[RQ Job {job.id}] ✓ Moved: {new_item_name}")
                                        except Exception as delete_error:
                                            log_msg = f"Arquivo transferido mas FALHA ao deletar: {new_item_name} - {str(delete_error)}"
                                            print(f"[RQ Job {job.id}] ⚠ Transferred but failed to delete: {new_item_name}")
                                    else:
                                        log_msg = f"Arquivo transferido: {new_item_name} (COPY mode)"
                                        print(f"[RQ Job {job.id}] ✓ Copied: {new_item_name}")

                                    # Mark file as processed
                                    processed_files.append(new_item_name)
                                    transfer.watched_files_processed = processed_files
                                    transfer.continuous_files_transferred += 1
                                    db.commit()

                                    # Log success or partial success
                                    log = AuditLog(
                                        transfer_id=transfer_id,
                                        event_type=AuditEventType.TRANSFER_PROGRESS,
                                        message=log_msg,
                                        event_metadata={"item": new_item_name, "type": "file", "sub_transfer_id": temp_transfer.id, "operation": operation_mode}
                                    )
                                    db.add(log)
                                    db.commit()

                            except CopyEngineError as e:
                                # Log error but continue monitoring
                                error_msg = f"Failed to transfer {new_item_name}: {str(e)}"
                                print(f"[RQ Job {job.id}] ✗ {error_msg}")

                                log = AuditLog(
                                    transfer_id=transfer_id,
                                    event_type=AuditEventType.ERROR,
                                    message=error_msg
                                )
                                db.add(log)
                                db.commit()
                            except Exception as e:
                                # Catch all other errors
                                error_msg = f"Unexpected error processing {new_item_name}: {str(e)}"
                                print(f"[RQ Job {job.id}] ✗ {error_msg}")

                                log = AuditLog(
                                    transfer_id=transfer_id,
                                    event_type=AuditEventType.ERROR,
                                    message=error_msg
                                )
                                db.add(log)
                                db.commit()

                    else:
                        # No new items, log checkpoint
                        if check_count % 6 == 0:  # Log every 3 minutes (6 checks * 30 sec)
                            log = AuditLog(
                                transfer_id=transfer_id,
                                event_type=AuditEventType.TRANSFER_PROGRESS,
                                message=f"Verificação contínua #{check_count}: {len(processed_files)} itens processados, aguardando novos...",
                                event_metadata={"check": check_count, "total_processed": len(processed_files)}
                            )
                            db.add(log)
                            db.commit()

                        print(f"[RQ Job {job.id}] No new items. Processed: {len(processed_files)}, checked {check_count} times")

                # Wait before next check (30 seconds)
                time.sleep(30)

            except Exception as e:
                error_msg = f"Error during continuous watch check: {str(e)}"
                print(f"[RQ Job {job.id}] {error_msg}")

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.ERROR,
                    message=error_msg
                )
                db.add(log)
                db.commit()

                # Continue monitoring despite error
                time.sleep(30)

    except Exception as e:
        error_msg = f"Continuous watch job failed: {str(e)}"
        print(f"[RQ Job {job.id}] {error_msg}")

        transfer.status = TransferStatus.FAILED
        db.commit()

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Continuous watch failed",
            "error": error_msg
        }
        return result

    finally:
        db.close()


# Job configuration
TRANSFER_JOB_CONFIG = {
    "timeout": "2h",  # 2 hours para arquivos grandes (500GB)
    "result_ttl": 86400,  # Manter resultado por 24h
    "failure_ttl": 86400,  # Manter falhas por 24h
    "ttl": None,  # Job não expira até ser processado
}

# Watch job configuration (longer timeout for watching)
WATCH_TRANSFER_JOB_CONFIG = {
    "timeout": "3h",  # 3 hours (1h watch + 2h transfer)
    "result_ttl": 86400,  # Manter resultado por 24h
    "failure_ttl": 86400,  # Manter falhas por 24h
    "ttl": None,  # Job não expira até ser processado
}

# Continuous watch job configuration (very long timeout - runs indefinitely)
CONTINUOUS_WATCH_JOB_CONFIG = {
    "timeout": "72h",  # 72 hours - can be manually stopped via API
    "result_ttl": 86400,  # Manter resultado por 24h
    "failure_ttl": 86400,  # Manter falhas por 24h
    "ttl": None,  # Job não expira até ser processado
}
