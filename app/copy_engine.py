"""
Ketter 3.0 - Copy Engine
Core file transfer with triple SHA-256 verification

MRC Principles:
- Simple, reliable file copying
- Triple checksum verification (source, destination, final)
- Complete audit trail
- Explicit error handling

Week 5: ZIP Smart support for folder transfers
"""

import os
import shutil
import hashlib
import tempfile
from datetime import datetime
from typing import Callable, Optional
from sqlalchemy.orm import Session

from app.models import Transfer, Checksum, AuditLog, TransferStatus, ChecksumType, AuditEventType
from app.zip_engine import (
    is_directory,
    count_files_recursive,
    zip_folder_smart,
    unzip_folder_smart,
    validate_zip_integrity,
    cleanup_zip_file,
    format_file_count
)


class CopyEngineError(Exception):
    """Base exception for Copy Engine errors"""
    pass


class InsufficientSpaceError(CopyEngineError):
    """Raised when there's not enough disk space"""
    pass


class ChecksumMismatchError(CopyEngineError):
    """Raised when checksums don't match"""
    pass


def calculate_sha256(file_path: str, chunk_size: int = 8192, progress_callback: Optional[Callable] = None) -> str:
    """
    Calcula SHA-256 de um arquivo

    MRC: Simple, reliable hash calculation
    - Lê arquivo em chunks para suportar arquivos grandes (500GB+)
    - Progress callback opcional para feedback

    Args:
        file_path: Caminho do arquivo
        chunk_size: Tamanho do chunk em bytes (default: 8KB)
        progress_callback: Função callback(bytes_read) para progresso

    Returns:
        str: SHA-256 hash em hexadecimal (64 caracteres)

    Raises:
        FileNotFoundError: Se arquivo não existe
        PermissionError: Se sem permissão de leitura
    """
    sha256_hash = hashlib.sha256()
    file_size = os.path.getsize(file_path)
    bytes_read = 0

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256_hash.update(chunk)
            bytes_read += len(chunk)

            # Progress callback
            if progress_callback:
                progress_callback(bytes_read, file_size)

    return sha256_hash.hexdigest()


def check_disk_space(destination_path: str, required_bytes: int, min_free_percent: int = 10) -> bool:
    """
    Verifica se há espaço suficiente no disco de destino

    MRC: Pre-flight validation - fail fast

    Args:
        destination_path: Caminho de destino
        required_bytes: Bytes necessários para o arquivo
        min_free_percent: Percentual mínimo de espaço livre após cópia (default: 10%)

    Returns:
        bool: True se há espaço suficiente

    Raises:
        InsufficientSpaceError: Se espaço insuficiente
    """
    # Get destination directory
    dest_dir = os.path.dirname(destination_path)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    # Check available space
    stat = shutil.disk_usage(dest_dir)
    available_bytes = stat.free
    total_bytes = stat.total

    # Calculate space after copy
    space_after_copy = available_bytes - required_bytes
    percent_free_after = (space_after_copy / total_bytes) * 100

    if percent_free_after < min_free_percent:
        raise InsufficientSpaceError(
            f"Insufficient disk space. "
            f"Required: {required_bytes / (1024**3):.2f} GB, "
            f"Available: {available_bytes / (1024**3):.2f} GB, "
            f"Free after copy: {percent_free_after:.1f}% (minimum: {min_free_percent}%)"
        )

    return True


def copy_file_with_progress(
    source_path: str,
    destination_path: str,
    chunk_size: int = 1024 * 1024,  # 1MB chunks
    progress_callback: Optional[Callable] = None
) -> int:
    """
    Copia arquivo com progress tracking

    MRC: Reliable file copy with progress feedback

    Args:
        source_path: Caminho do arquivo original
        destination_path: Caminho de destino
        chunk_size: Tamanho do chunk (default: 1MB)
        progress_callback: Função callback(bytes_copied, total_bytes)

    Returns:
        int: Total de bytes copiados

    Raises:
        FileNotFoundError: Se source não existe
        PermissionError: Se sem permissão
        IOError: Erros de I/O
    """
    file_size = os.path.getsize(source_path)
    bytes_copied = 0

    # Create destination directory if needed
    dest_dir = os.path.dirname(destination_path)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    with open(source_path, 'rb') as source_file:
        with open(destination_path, 'wb') as dest_file:
            while True:
                chunk = source_file.read(chunk_size)
                if not chunk:
                    break

                dest_file.write(chunk)
                bytes_copied += len(chunk)

                # Progress callback
                if progress_callback:
                    progress_callback(bytes_copied, file_size)

    return bytes_copied


def transfer_file_with_verification(
    transfer_id: int,
    db: Session,
    progress_callback: Optional[Callable] = None
) -> Transfer:
    """
    Transfere arquivo com verificação tripla SHA-256

    **MRC: Core function - Triple verification for reliability**

    Fluxo:
    1. Valida que transfer existe e está PENDING
    2. Valida espaço em disco
    3. Calcula checksum SOURCE
    4. Copia arquivo com progress tracking
    5. Calcula checksum DESTINATION
    6. Verifica checksums (FINAL)
    7. Se operation_mode=MOVE: delete source após verificação
    8. Atualiza status para COMPLETED

    Args:
        transfer_id: ID da transferência
        db: Database session
        progress_callback: Callback(bytes_done, total_bytes) opcional

    Returns:
        Transfer: Transfer object atualizado

    Raises:
        ValueError: Se transfer não existe ou status inválido
        InsufficientSpaceError: Se espaço insuficiente
        ChecksumMismatchError: Se checksums não batem
        CopyEngineError: Outros erros de cópia
    """
    # 1. Load transfer
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise ValueError(f"Transfer {transfer_id} not found")

    if transfer.status != TransferStatus.PENDING:
        raise ValueError(f"Transfer {transfer_id} is not pending (status: {transfer.status})")

    try:
        # Week 5: Check if source is a folder (ZIP Smart)
        is_folder = is_directory(transfer.source_path)
        actual_source_path = transfer.source_path  # Will be updated if folder
        zip_created = False

        if is_folder:
            # Mark as folder transfer
            transfer.is_folder_transfer = 1
            transfer.original_folder_path = transfer.source_path
            db.commit()

            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Folder detected: {transfer.source_path}")

            # Count files in folder
            file_count, folder_size = count_files_recursive(transfer.source_path)
            transfer.file_count = file_count
            transfer.file_size = folder_size  # Update with actual folder size
            db.commit()

            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Folder contains {format_file_count(file_count)} ({folder_size / (1024**3):.2f} GB)")

            # Create temporary ZIP file (STORE mode - no compression)
            zip_dir = tempfile.gettempdir()
            folder_name = os.path.basename(transfer.source_path.rstrip('/'))
            zip_filename = f"ketter_temp_{transfer_id}_{folder_name}.zip"
            zip_path = os.path.join(zip_dir, zip_filename)

            transfer.zip_file_path = zip_path
            db.commit()

            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Zipping folder (STORE mode - no compression)...")

            # ZIP folder with progress tracking
            def zip_progress(files_done, total_files, current_file):
                percent = int((files_done / total_files) * 100) if total_files > 0 else 0
                transfer.progress_percent = percent // 2  # First half of progress
                db.commit()

            zip_folder_smart(transfer.source_path, zip_path, progress_callback=zip_progress)
            zip_created = True

            # Validate ZIP integrity
            if not validate_zip_integrity(zip_path):
                raise CopyEngineError("ZIP file validation failed")

            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Folder zipped successfully: {format_file_count(file_count)}")

            # Update source to ZIP file for transfer
            actual_source_path = zip_path
            transfer.file_size = os.path.getsize(zip_path)
            db.commit()

        # Update status to VALIDATING
        transfer.status = TransferStatus.VALIDATING
        db.commit()

        # Log: validation started
        log_event(db, transfer_id, AuditEventType.TRANSFER_STARTED, "Starting validation")

        # 2. Check disk space (use actual size - ZIP if folder, file if file)
        check_disk_space(transfer.destination_path, transfer.file_size)

        # Log: space validated
        log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                 f"Disk space validated ({transfer.file_size / (1024**3):.2f} GB required)")

        # 3. Calculate SOURCE checksum
        transfer.status = TransferStatus.VERIFYING
        transfer.started_at = datetime.utcnow()
        db.commit()

        log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS, "Calculating source checksum...")

        start_time = datetime.utcnow()
        # Use actual_source_path (ZIP if folder, original file if file)
        source_hash = calculate_sha256(actual_source_path)
        calc_duration = int((datetime.utcnow() - start_time).total_seconds())

        # Save SOURCE checksum
        source_checksum = Checksum(
            transfer_id=transfer_id,
            checksum_type=ChecksumType.SOURCE,
            checksum_value=source_hash,
            calculation_duration_seconds=calc_duration
        )
        db.add(source_checksum)
        db.commit()

        log_event(db, transfer_id, AuditEventType.CHECKSUM_CALCULATED,
                 f"Source checksum: {source_hash[:16]}... ({calc_duration}s)",
                 {"checksum": source_hash, "duration": calc_duration})

        # 4. Copy file
        transfer.status = TransferStatus.COPYING
        db.commit()

        log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                 f"Copying {transfer.file_name} ({transfer.file_size / (1024**3):.2f} GB)...")

        def update_progress(bytes_done, total_bytes):
            percent = int((bytes_done / total_bytes) * 100)
            transfer.bytes_transferred = bytes_done
            transfer.progress_percent = percent
            db.commit()
            if progress_callback:
                progress_callback(bytes_done, total_bytes)

        # Copy file (ZIP if folder, file if file)
        # For folder: destination will be the ZIP, we'll unzip after verification
        dest_for_copy = transfer.destination_path
        if is_folder:
            # If folder transfer, destination should be ZIP first
            dest_folder_name = os.path.basename(transfer.original_folder_path.rstrip('/'))
            dest_zip_filename = f"{dest_folder_name}.zip"
            dest_parent = os.path.dirname(transfer.destination_path)
            dest_for_copy = os.path.join(dest_parent, dest_zip_filename)

        bytes_copied = copy_file_with_progress(
            actual_source_path,
            dest_for_copy,
            progress_callback=update_progress
        )

        log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                 f"File copied: {bytes_copied} bytes")

        # 5. Calculate DESTINATION checksum
        transfer.status = TransferStatus.VERIFYING
        db.commit()

        log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS, "Calculating destination checksum...")

        start_time = datetime.utcnow()
        # Calculate checksum of copied file (ZIP if folder)
        dest_hash = calculate_sha256(dest_for_copy)
        calc_duration = int((datetime.utcnow() - start_time).total_seconds())

        # Save DESTINATION checksum
        dest_checksum = Checksum(
            transfer_id=transfer_id,
            checksum_type=ChecksumType.DESTINATION,
            checksum_value=dest_hash,
            calculation_duration_seconds=calc_duration
        )
        db.add(dest_checksum)
        db.commit()

        log_event(db, transfer_id, AuditEventType.CHECKSUM_CALCULATED,
                 f"Destination checksum: {dest_hash[:16]}... ({calc_duration}s)",
                 {"checksum": dest_hash, "duration": calc_duration})

        # 6. FINAL verification - Compare checksums
        if source_hash != dest_hash:
            transfer.status = TransferStatus.FAILED
            transfer.error_message = f"Checksum mismatch! Source: {source_hash[:16]}..., Dest: {dest_hash[:16]}..."
            db.commit()

            log_event(db, transfer_id, AuditEventType.ERROR,
                     f"CHECKSUM MISMATCH! Transfer failed.",
                     {"source_checksum": source_hash, "dest_checksum": dest_hash})

            raise ChecksumMismatchError(
                f"Checksum verification failed! "
                f"Source: {source_hash}, "
                f"Destination: {dest_hash}"
            )

        # Save FINAL checksum (same as others, confirming match)
        final_checksum = Checksum(
            transfer_id=transfer_id,
            checksum_type=ChecksumType.FINAL,
            checksum_value=source_hash,  # Same as source/dest
            calculation_duration_seconds=0  # No calculation, just verification
        )
        db.add(final_checksum)
        db.commit()

        log_event(db, transfer_id, AuditEventType.CHECKSUM_VERIFIED,
                 "Triple SHA-256 verification PASSED ",
                 {"checksum": source_hash})

        # Week 5: If folder transfer, unzip at destination
        if is_folder:
            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Unzipping folder at destination...")

            # Unzip with progress tracking
            def unzip_progress(files_done, total_files, current_file):
                # Progress is 50-100% (second half)
                percent = 50 + int((files_done / total_files) * 50) if total_files > 0 else 50
                transfer.progress_percent = percent
                db.commit()

            # Unzip to original destination path
            unzip_folder_smart(dest_for_copy, transfer.destination_path, progress_callback=unzip_progress)
            transfer.unzip_completed = 1
            db.commit()

            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     f"Folder unzipped successfully: {format_file_count(transfer.file_count)}")

            # Cleanup temporary ZIP files
            if zip_created and transfer.zip_file_path:
                cleanup_zip_file(transfer.zip_file_path)  # Source ZIP
                log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                         "Cleaned up temporary ZIP files")

            if dest_for_copy and os.path.exists(dest_for_copy):
                cleanup_zip_file(dest_for_copy)  # Destination ZIP

        # 7. Handle MOVE operation if enabled
        if transfer.operation_mode == 'move':
            log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                     "MOVE mode: Deleting source files after verification...")

            try:
                if is_folder:
                    # For folder MOVE: Delete only the CONTENTS, keep the folder structure
                    source_folder = transfer.original_folder_path
                    deleted_count = 0
                    deleted_size = 0

                    # Walk through all files in the folder recursively
                    for root, dirs, files in os.walk(source_folder, topdown=False):
                        # Delete all files first
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                deleted_size += os.path.getsize(file_path)
                                os.remove(file_path)
                                deleted_count += 1
                            except Exception as e:
                                log_event(db, transfer_id, AuditEventType.ERROR,
                                         f"Failed to delete file: {file_path} - {str(e)}")

                        # Delete empty directories (bottom-up)
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            try:
                                if not os.listdir(dir_path):  # Only if empty
                                    os.rmdir(dir_path)
                            except Exception:
                                pass  # Skip if directory not empty or has issues

                    log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                             f"Source folder contents deleted: {deleted_count} files ({deleted_size / (1024**2):.2f} MB). Source folder '{os.path.basename(source_folder)}' preserved.")
                else:
                    # Delete source file (single file, not folder)
                    os.remove(transfer.source_path)
                    log_event(db, transfer_id, AuditEventType.TRANSFER_PROGRESS,
                             f"Source file deleted: {transfer.source_path}")
            except Exception as e:
                error_msg = f"Failed to delete source in MOVE operation: {str(e)}"
                log_event(db, transfer_id, AuditEventType.ERROR, error_msg)
                # Don't fail the transfer - just log the error
                # The file was already copied and verified, so this is a non-critical error

        # 8. Complete transfer
        transfer.status = TransferStatus.COMPLETED
        transfer.completed_at = datetime.utcnow()
        transfer.progress_percent = 100
        db.commit()

        duration = (transfer.completed_at - transfer.started_at).total_seconds()
        speed_mbps = (transfer.file_size / (1024**2)) / duration if duration > 0 else 0

        if is_folder:
            log_event(db, transfer_id, AuditEventType.TRANSFER_COMPLETED,
                     f"Folder transfer completed successfully in {duration:.1f}s ({speed_mbps:.2f} MB/s) - {format_file_count(transfer.file_count)}",
                     {
                         "duration_seconds": duration,
                         "speed_mbps": speed_mbps,
                         "file_size": transfer.file_size,
                         "file_count": transfer.file_count,
                         "is_folder_transfer": True
                     })
        else:
            log_event(db, transfer_id, AuditEventType.TRANSFER_COMPLETED,
                     f"Transfer completed successfully in {duration:.1f}s ({speed_mbps:.2f} MB/s)",
                     {
                         "duration_seconds": duration,
                         "speed_mbps": speed_mbps,
                         "file_size": transfer.file_size
                     })

        return transfer

    except Exception as e:
        # Handle any errors
        transfer.status = TransferStatus.FAILED
        transfer.error_message = str(e)
        transfer.retry_count += 1
        db.commit()

        log_event(db, transfer_id, AuditEventType.ERROR,
                 f"Transfer failed: {str(e)}",
                 {"error": str(e), "error_type": type(e).__name__})

        raise CopyEngineError(f"Transfer failed: {str(e)}") from e


def log_event(db: Session, transfer_id: int, event_type: AuditEventType, message: str, metadata: dict = None):
    """
    Helper para criar audit log

    Args:
        db: Database session
        transfer_id: ID da transferência
        event_type: Tipo do evento
        message: Mensagem do log
        metadata: Metadata adicional (opcional)
    """
    log = AuditLog(
        transfer_id=transfer_id,
        event_type=event_type,
        message=message,
        event_metadata=metadata
    )
    db.add(log)
    db.commit()
