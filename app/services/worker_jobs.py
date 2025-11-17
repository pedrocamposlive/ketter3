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
import time
from datetime import datetime, timezone
from rq import get_current_job, Queue
from app.database import SessionLocal
from app.core.copy_engine import transfer_file_with_verification, CopyEngineError
from app.core.watch_folder import watch_folder_until_stable, WatchFolderError
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

        # Check if transfer was cancelled before processing
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {
                "success": False,
                "transfer_id": transfer_id,
                "message": "Transfer not found",
                "error": "Transfer does not exist"
            }

        # FIXED: Only skip if transfer has user_cancelled flag set
        # This prevents skipping jobs from previous failed transfers with same error message
        if hasattr(transfer, 'user_cancelled') and transfer.user_cancelled:
            print(f"[RQ Job {job.id}] Transfer {transfer_id} was cancelled by user, skipping")
            return {
                "success": False,
                "transfer_id": transfer_id,
                "message": "Transfer was cancelled by user",
                "error": "Cancelled"
            }

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

        print(f"[RQ Job {job.id}] Transfer {transfer_id} completed ")
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
            transfer.watch_started_at = datetime.now(timezone.utc)
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
            # IMPORTANT: Keep callback simple - no DB access in callback
            # watch_folder calls: callback(elapsed, settle_time, state_info_dict)
            checks_log = []  # Store check info locally, log after watch completes

            def watch_progress(elapsed, settle_time, state_info):
                # state_info = {'file_count': int, 'checks_done': int}
                checks_done = state_info.get('checks_done', 0)
                file_count = state_info.get('file_count', 0)

                # Just log to console, don't access DB in callback
                print(f"[RQ Job {job.id}] Watch progress: elapsed={elapsed}s, checks={checks_done}, files={file_count}")
                checks_log.append({"elapsed": elapsed, "checks": checks_done, "file_count": file_count})

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
            transfer.watch_triggered_at = datetime.now(timezone.utc)
            db.commit()

            watch_duration = int((transfer.watch_triggered_at - transfer.watch_started_at).total_seconds())

            # Log watch completion with check history
            log = AuditLog(
                transfer_id=transfer_id,
                event_type=AuditEventType.TRANSFER_PROGRESS,
                message=f"Watch mode: Folder is stable after {watch_duration}s. Starting transfer...",
                event_metadata={
                    "watch_duration": watch_duration,
                    "checks_performed": len(checks_log),
                    "check_history": checks_log  # Log all checks that were performed
                }
            )
            db.add(log)
            db.commit()

            print(f"[RQ Job {job.id}] Folder stable after {watch_duration}s ({len(checks_log)} checks), starting transfer")

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

        print(f"[RQ Job {job.id}] Transfer {transfer_id} completed ")
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


def watcher_continuous_job(transfer_id: int, stop_after_cycles: int | None = None) -> dict:
    """
    RQ Job: Continuous file monitoring and transfer (Week 6 - NEW)

    **Week 6: Watch Mode Contínuo - Infinite loop monitoring**

    Este job:
    1. Loop infinito a cada 5 segundos
    2. Scaneia pasta de origem
    3. Detecta arquivos novos (delta from last_files_processed)
    4. Aplica settle_time para confirmar estabilidade
    5. Enfileira transfer_file_job para cada arquivo novo
    6. Atualiza last_files_processed JSON
    7. Incrementa watch_cycle_count
    8. Continua até transfer.watch_continuous=False (pause signal)

        Args:
            transfer_id: ID da transferência com watch_continuous=True
            stop_after_cycles: Optional cycle limit used in tests to escape the infinite loop

    Returns:
        dict: Status final do monitoramento
            - success: bool
            - transfer_id: int
            - message: str
            - total_files_detected: int
            - watch_cycles: int
            - reason_stopped: str

    Raises:
        Exception: Propaga exceções para RQ retry mechanism
    """
    import time
    import json
    from redis import Redis

    job = get_current_job()
    db = SessionLocal()

    try:
        print(f"[RQ Job {job.id}] Starting continuous watch job for transfer {transfer_id}")

        # Load transfer
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise ValueError(f"Transfer {transfer_id} not found")

        # Verify watch mode is configured
        if not transfer.watch_mode_enabled:
            raise ValueError(f"Transfer {transfer_id} does not have watch mode enabled")

        # Initialize tracking
        try:
            last_processed = json.loads(transfer.last_files_processed or "[]")
        except (json.JSONDecodeError, TypeError):
            last_processed = []

        # Set watch start time
        transfer.watch_started_at = datetime.now(timezone.utc)
        transfer.watch_continuous = 1
        db.commit()

        # Log watch start
        log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message=f"Continuous watch mode started (settle time: {transfer.settle_time_seconds}s)",
            event_metadata={
                "action": "watch_start",
                "settle_time": transfer.settle_time_seconds,
                "job_id": job.id
            }
        )
        db.add(log)
        db.commit()

        total_detected = 0
        watch_cycles = 0

        # ENHANCE #6: Circuit breaker configuration
        MAX_CYCLES = int(os.getenv("WATCH_MAX_CYCLES", "10000"))  # Default: 10k cycles (~14h at 5s/cycle)
        MAX_DURATION_SECONDS = int(os.getenv("WATCH_MAX_DURATION", "86400"))  # Default: 24 hours
        ERROR_THRESHOLD_PERCENT = int(os.getenv("WATCH_ERROR_THRESHOLD", "50"))  # Default: 50%
        ERROR_WINDOW_SIZE = 10  # Track last 10 cycles for error rate

        # Circuit breaker tracking
        error_history = []  # Track errors in recent cycles: True = error, False = success
        watch_start_time = datetime.now(timezone.utc)

        # Main loop - continue while watch_continuous=True AND circuit breaker allows
        while True:
            # ENHANCE #6: Circuit breaker checks BEFORE processing

            # Check 1: Max cycles reached
            if watch_cycles >= MAX_CYCLES:
                reason_stopped = f"Circuit breaker: Max cycles reached ({MAX_CYCLES})"
                print(f"[RQ Job {job.id}] {reason_stopped}")

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.TRANSFER_PROGRESS,
                    message=reason_stopped,
                    event_metadata={
                        "circuit_breaker": "max_cycles",
                        "cycles_completed": watch_cycles,
                        "limit": MAX_CYCLES
                    }
                )
                db.add(log)
                db.commit()
                break

            # Check 2: Max duration exceeded
            elapsed_seconds = (datetime.now(timezone.utc) - watch_start_time).total_seconds()
            if elapsed_seconds > MAX_DURATION_SECONDS:
                reason_stopped = f"Circuit breaker: Max duration exceeded ({MAX_DURATION_SECONDS}s = {MAX_DURATION_SECONDS/3600:.1f}h)"
                print(f"[RQ Job {job.id}] {reason_stopped}")

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.TRANSFER_PROGRESS,
                    message=reason_stopped,
                    event_metadata={
                        "circuit_breaker": "max_duration",
                        "elapsed_seconds": int(elapsed_seconds),
                        "limit_seconds": MAX_DURATION_SECONDS
                    }
                )
                db.add(log)
                db.commit()
                break

            # Check 3: Error rate threshold exceeded
            if len(error_history) >= ERROR_WINDOW_SIZE:
                error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
                error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

                if error_rate_percent >= ERROR_THRESHOLD_PERCENT:
                    reason_stopped = f"Circuit breaker: High error rate ({error_rate_percent:.0f}% >= {ERROR_THRESHOLD_PERCENT}%)"
                    print(f"[RQ Job {job.id}] {reason_stopped}")

                    log = AuditLog(
                        transfer_id=transfer_id,
                        event_type=AuditEventType.ERROR,
                        message=reason_stopped,
                        event_metadata={
                            "circuit_breaker": "error_threshold",
                            "error_rate_percent": error_rate_percent,
                            "threshold_percent": ERROR_THRESHOLD_PERCENT,
                            "window_size": ERROR_WINDOW_SIZE,
                            "recent_errors": error_history[-ERROR_WINDOW_SIZE:]
                        }
                    )
                    db.add(log)
                    db.commit()
                    break

            # Refresh transfer to check for pause signal
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            if not transfer or not transfer.watch_continuous:
                reason_stopped = "User paused" if transfer else "Transfer deleted"
                print(f"[RQ Job {job.id}] Watch stopped: {reason_stopped}")
                break

            watch_cycles += 1
            print(f"[RQ Job {job.id}] Watch cycle {watch_cycles}: scanning folder...")

            # ENHANCE #6: Track cycle success/failure for circuit breaker
            cycle_had_error = False

            try:
                # Scan source folder
                if not os.path.exists(transfer.source_path):
                    print(f"[RQ Job {job.id}] Source path does not exist, waiting...")
                    log = AuditLog(
                        transfer_id=transfer_id,
                        event_type=AuditEventType.TRANSFER_PROGRESS,
                        message=f"Watch cycle {watch_cycles}: Source path not yet available",
                        event_metadata={"cycle": watch_cycles}
                    )
                    db.add(log)
                    db.commit()
                    time.sleep(5)
                    continue

                # Get current files
                current_files = []
                try:
                    if os.path.isdir(transfer.source_path):
                        current_files = [
                            os.path.join(transfer.source_path, f)
                            for f in os.listdir(transfer.source_path)
                            if os.path.isfile(os.path.join(transfer.source_path, f)) and not f.startswith('.')
                        ]
                except OSError as e:
                    print(f"[RQ Job {job.id}] Error scanning folder: {str(e)}")
                    time.sleep(5)
                    continue

                # Calculate delta
                current_set = set(current_files)
                previous_set = set(last_processed)
                new_files = current_set - previous_set

                if new_files:
                    print(f"[RQ Job {job.id}] Found {len(new_files)} new files in cycle {watch_cycles}")

                    # Process each new file
                    for file_path in sorted(new_files):
                        file_name = os.path.basename(file_path)

                        try:
                            # Wait for file to stabilize
                            file_stable = _wait_for_file_settle(
                                file_path,
                                settle_time_seconds=transfer.settle_time_seconds
                            )

                            if not file_stable:
                                print(f"[RQ Job {job.id}] File {file_name} timeout, skipping")
                                continue

                            # FIXED: Create a NEW Transfer record for each file (not reuse watch session)
                            # This allows transfer_file_job to process each file independently
                            from app.models import WatchFile, TransferStatus

                            # Create new Transfer record for this individual file
                            file_transfer = Transfer(
                                source_path=file_path,
                                destination_path=transfer.destination_path,
                                file_name=file_name,
                                file_size=os.path.getsize(file_path),
                                status=TransferStatus.PENDING,
                                watch_mode_enabled=0,  # Already watched by parent, no need to re-watch
                                operation_mode=transfer.operation_mode  # Inherit COPY/MOVE from parent
                            )
                            db.add(file_transfer)
                            db.commit()
                            db.refresh(file_transfer)

                            # Create WatchFile record to track this detection
                            watch_file = WatchFile(
                                transfer_id=transfer_id,  # Link to watch session
                                file_name=file_name,
                                file_path=file_path,
                                file_size=os.path.getsize(file_path),
                                status=TransferStatus.PENDING,
                                detected_at=datetime.now(timezone.utc)
                            )
                            db.add(watch_file)
                            db.commit()

                            # Enqueue transfer job for this file (using new transfer_id, not parent)
                            try:
                                redis_conn = Redis.from_url(
                                    os.getenv("REDIS_URL", "redis://redis:6379/0")
                                )
                                transfer_queue = Queue("default", connection=redis_conn)

                                transfer_job = transfer_queue.enqueue(
                                    transfer_file_job,
                                    file_transfer.id,  # Use NEW transfer_id, not parent
                                    job_timeout=TRANSFER_JOB_CONFIG["timeout"],
                                    result_ttl=TRANSFER_JOB_CONFIG["result_ttl"],
                                    failure_ttl=TRANSFER_JOB_CONFIG["failure_ttl"]
                                )

                                # Update WatchFile with job ID
                                watch_file.transfer_job_id = transfer_job.id
                                db.commit()

                                total_detected += 1

                                print(f"[RQ Job {job.id}] Enqueued transfer job {transfer_job.id} for {file_name}")

                                # Log file detection
                                log = AuditLog(
                                    transfer_id=transfer_id,
                                    event_type=AuditEventType.TRANSFER_PROGRESS,
                                    message=f"File detected and transfer enqueued: {file_name} ({watch_file.file_size} bytes)",
                                    event_metadata={
                                        "watch_file_id": watch_file.id,
                                        "file_name": file_name,
                                        "file_size": watch_file.file_size,
                                        "job_id": transfer_job.id,
                                        "cycle": watch_cycles
                                    }
                                )
                                db.add(log)
                                db.commit()

                            except Exception as e:
                                error_msg = f"Failed to enqueue transfer: {str(e)}"
                                print(f"[RQ Job {job.id}] {error_msg}")
                                watch_file.error_message = error_msg
                                db.commit()

                        except Exception as e:
                            error_msg = f"Error processing file {file_name}: {str(e)}"
                            print(f"[RQ Job {job.id}] {error_msg}")

                # Update tracking
                last_processed = list(current_set)
                transfer.last_files_processed = json.dumps(last_processed)
                transfer.watch_cycle_count = watch_cycles
                db.commit()

                # Log cycle complete
                if new_files:
                    log = AuditLog(
                        transfer_id=transfer_id,
                        event_type=AuditEventType.TRANSFER_PROGRESS,
                        message=f"Watch cycle {watch_cycles} complete: detected {len(new_files)} new files",
                        event_metadata={
                            "cycle": watch_cycles,
                            "files_detected_this_cycle": len(new_files),
                            "total_detected": total_detected
                        }
                    )
                    db.add(log)
                    db.commit()

            except Exception as e:
                # ENHANCE #6: Mark cycle as error
                cycle_had_error = True

                error_msg = f"Watch cycle {watch_cycles} error: {str(e)}"
                print(f"[RQ Job {job.id}] {error_msg}")

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.ERROR,
                    message=error_msg,
                    event_metadata={"cycle": watch_cycles, "error": str(e)}
                )
                db.add(log)
                db.commit()

                # Continue watching despite errors
                time.sleep(10)

            # ENHANCE #6: Record cycle result for circuit breaker
            error_history.append(cycle_had_error)

            # Keep only last ERROR_WINDOW_SIZE * 2 entries to prevent unbounded growth
            if len(error_history) > ERROR_WINDOW_SIZE * 2:
                error_history = error_history[-ERROR_WINDOW_SIZE * 2:]

            # ENHANCE #6: Log circuit breaker status periodically (every 100 cycles)
            if watch_cycles % 100 == 0:
                recent_errors = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err) if len(error_history) >= ERROR_WINDOW_SIZE else 0
                error_rate = (recent_errors / min(len(error_history), ERROR_WINDOW_SIZE)) * 100 if error_history else 0

                log = AuditLog(
                    transfer_id=transfer_id,
                    event_type=AuditEventType.TRANSFER_PROGRESS,
                    message=f"Circuit breaker status: {watch_cycles} cycles, {error_rate:.0f}% error rate, {int(elapsed_seconds)}s elapsed",
                    event_metadata={
                        "cycles": watch_cycles,
                        "error_rate_percent": error_rate,
                        "elapsed_seconds": int(elapsed_seconds),
                        "total_detected": total_detected
                    }
                )
                db.add(log)
                db.commit()

            # Sleep before next scan (if no error, 5s; if error, already slept 10s)
            if not cycle_had_error:
                time.sleep(5)

            if stop_after_cycles is not None and watch_cycles >= stop_after_cycles:
                raise StopIteration(f"Test stop hook reached after {watch_cycles} cycles")

        # Loop ended - log final status
        # FIXED: Check if transfer still exists before accessing attributes
        reason_stopped = "Transfer deleted"
        if transfer:
            reason_stopped = "User paused" if not transfer.watch_continuous else "Watch stopped by user"

        log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.TRANSFER_PROGRESS,
            message=f"Continuous watch mode stopped after {watch_cycles} cycles, {total_detected} files detected",
            event_metadata={
                "cycles": watch_cycles,
                "total_detected": total_detected,
                "reason": reason_stopped
            }
        )
        db.add(log)
        db.commit()

        result = {
            "success": True,
            "transfer_id": transfer_id,
            "message": f"Watch mode completed: {total_detected} files detected in {watch_cycles} cycles",
            "total_files_detected": total_detected,
            "watch_cycles": watch_cycles,
            "reason_stopped": reason_stopped
        }

        print(f"[RQ Job {job.id}] Watch job completed successfully ")
        return result

    except Exception as e:
        error_msg = f"Watch job failed: {str(e)}"
        print(f"[RQ Job {job.id}] {error_msg}")

        log = AuditLog(
            transfer_id=transfer_id,
            event_type=AuditEventType.ERROR,
            message=error_msg,
            event_metadata={"error": str(e)}
        )
        try:
            db.add(log)
            db.commit()
        except:
            pass

        result = {
            "success": False,
            "transfer_id": transfer_id,
            "message": "Watch job failed",
            "error": error_msg
        }

        # Re-raise for RQ retry mechanism
        raise

    finally:
        db.close()


def _wait_for_file_settle(file_path: str, settle_time_seconds: int = 30, max_wait: int = 300) -> bool:
    """
    Helper: Aguarda arquivo estabilizar (tamanho não muda por settle_time segundos)

    Args:
        file_path: Caminho do arquivo
        settle_time_seconds: Segundos sem mudanças para considerar estável
        max_wait: Máximo de segundos para aguardar

    Returns:
        bool: True se arquivo estabilizou, False se timeout
    """
    import time

    start_time = time.time()
    last_size = -1
    stable_time = 0

    while time.time() - start_time < max_wait:
        try:
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)

                if current_size == last_size:
                    stable_time += 1
                    # FIXED: Only return True after settle_time consecutive stable checks
                    # Each check is separated by 1 second sleep, so stable_time in seconds
                    if stable_time >= settle_time_seconds:
                        return True
                else:
                    last_size = current_size
                    stable_time = 0

        except OSError:
            # File was deleted or access denied
            return False

        # Always sleep before next check to ensure proper timing
        time.sleep(1)

    return False  # Timeout - file never stabilized within max_wait


# Job configuration
# FIXED: Timeout must be in seconds (integer), not strings like "2h"
TRANSFER_JOB_CONFIG = {
    "timeout": 7200,  # 2 hours = 7200 seconds for large files (500GB)
    "result_ttl": 86400,  # Keep result for 24h
    "failure_ttl": 86400,  # Keep failures for 24h
    "ttl": None,  # Job doesn't expire until processed
}

# Watch job configuration (longer timeout for watching)
# FIXED: 3 hours = 10800 seconds (1h watch + 2h transfer)
WATCH_TRANSFER_JOB_CONFIG = {
    "timeout": 10800,  # 3 hours = 10800 seconds
    "result_ttl": 86400,  # Keep result for 24h
    "failure_ttl": 86400,  # Keep failures for 24h
    "ttl": None,  # Job doesn't expire until processed
}

# Continuous watch job configuration (NEW - Week 6)
# FIXED: 24 hours = 86400 seconds
WATCH_CONTINUOUS_JOB_CONFIG = {
    "timeout": 86400,  # 24 hours = 86400 seconds - continuous job should not timeout
    "result_ttl": 500,  # Keep result 500 seconds
    "failure_ttl": 86400,  # Keep failures 24 hours
}
