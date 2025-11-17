"""
Ketter 3.0 - ZIP Smart Engine
Smart folder packaging with STORE mode (no compression) for Pro Tools sessions

MRC Principles:
- Simple: Uses Python stdlib zipfile (no external deps)
- Reliable: STORE mode = bit-perfect copy inside container
- Transparent: Progress callbacks for every operation
- Fast: No compression = 100-200 MB/s vs 20-50 MB/s

Use Case:
- Pro Tools sessions with 1000+ audio files (WAV, MP3, AAC)
- Audio is already compressed - additional compression is wasteful
- STORE mode = instant "packaging" without CPU overhead
"""

import hashlib
import os
import zipfile
import time
from datetime import datetime
from typing import Optional, Callable, Tuple
from pathlib import Path

MAX_ZIP_ENTRY_BYTES = int(os.getenv("KETTER_ZIP_MAX_ENTRY_BYTES", 10 * 1024 * 1024))
MAX_ZIP_TOTAL_BYTES = int(os.getenv("KETTER_ZIP_MAX_TOTAL_BYTES", 500 * 1024 * 1024))


class ZipEngineError(Exception):
    """Base exception for ZIP Smart Engine errors"""
    pass


class InvalidPathError(ZipEngineError):
    """Raised when path is invalid or doesn't exist"""
    pass


def is_directory(path: str) -> bool:
    """
    Check if path is a directory (not a file)

    MRC: Simple boolean check

    Args:
        path: Path to check

    Returns:
        bool: True if directory, False if file or doesn't exist
    """
    return os.path.isdir(path)


def count_files_recursive(path: str) -> Tuple[int, int]:
    """
    Count files and total size in a directory recursively

    MRC: Pre-flight validation - know what we're dealing with

    Args:
        path: Directory path

    Returns:
        tuple: (file_count, total_bytes)

    Raises:
        InvalidPathError: If path doesn't exist or is not a directory
    """
    if not os.path.exists(path):
        raise InvalidPathError(f"Path does not exist: {path}")

    if not os.path.isdir(path):
        raise InvalidPathError(f"Path is not a directory: {path}")

    file_count = 0
    total_bytes = 0

    for root, dirs, files in os.walk(path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue

            file_path = os.path.join(root, file)
            try:
                total_bytes += os.path.getsize(file_path)
                file_count += 1
            except (OSError, IOError):
                # Skip files we can't read
                continue

    return file_count, total_bytes


def zip_folder_smart(
    source_folder: str,
    zip_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> str:
    """
    Package folder into ZIP using STORE mode (no compression)

    **MRC: Core ZIP Smart function**

    STORE mode advantages:
    - No CPU overhead (audio already compressed)
    - Faster: 100-200 MB/s vs 20-50 MB/s (compressed)
    - Bit-perfect: No compression artifacts
    - Still provides container benefits (single file, metadata)

    Args:
        source_folder: Path to folder to zip
        zip_path: Destination ZIP file path
        progress_callback: Optional callback(files_done, total_files, current_file)

    Returns:
        str: Path to created ZIP file

    Raises:
        InvalidPathError: If source doesn't exist
        ZipEngineError: If ZIP creation fails
    """
    if not os.path.exists(source_folder):
        raise InvalidPathError(f"Source folder does not exist: {source_folder}")

    if not os.path.isdir(source_folder):
        raise InvalidPathError(f"Source is not a directory: {source_folder}")

    # Count files for progress tracking
    try:
        file_count, total_bytes = count_files_recursive(source_folder)
    except Exception as e:
        raise ZipEngineError(f"Failed to count files: {e}") from e

    # Create ZIP with STORE mode (no compression)
    files_processed = 0

    try:
        # Get absolute path of zip file to exclude it from being zipped
        zip_abs_path = os.path.abspath(zip_path)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
            # Walk through directory
            source_path = Path(source_folder)
            total_bytes = 0

            for root, dirs, files in os.walk(source_folder):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]

                    # Add empty directories (excluding hidden ones)
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        arcname = os.path.relpath(dir_path, source_folder) + '/'
                        # Check if directory is empty
                        if not os.listdir(dir_path):
                            # Add empty directory to ZIP
                            zipf.write(dir_path, arcname)

                    # Add files (excluding hidden files)
                    for file in files:
                        # Skip hidden files (starting with .)
                        if file.startswith('.'):
                            continue

                        file_path = os.path.join(root, file)
                        file_abs_path = os.path.abspath(file_path)

                        # Skip the ZIP file itself if it's inside the source folder
                        if file_abs_path == zip_abs_path:
                            continue

                        # Calculate relative path to maintain folder structure
                        arcname = os.path.relpath(file_path, source_folder)

                        file_size = os.path.getsize(file_path)
                        if file_size > MAX_ZIP_ENTRY_BYTES:
                            raise ZipEngineError(
                                f"ZIP entry exceeds max size ({file_size} bytes): {file_path}"
                            )
                        total_bytes += file_size
                        if total_bytes > MAX_ZIP_TOTAL_BYTES:
                            raise ZipEngineError(
                                f"ZIP total exceeds limit ({total_bytes} bytes) at {file_path}"
                            )

                        try:
                            # Add file to ZIP
                            zipf.write(file_path, arcname)
                            files_processed += 1

                            # Progress callback
                            if progress_callback:
                                progress_callback(files_processed, file_count, arcname)

                        except (OSError, IOError) as e:
                            # Skip files we can't read but continue
                            print(f"Warning: Skipping file {file_path}: {e}")
                        continue

        # Verify ZIP was created
        if not os.path.exists(zip_path):
            raise ZipEngineError(f"ZIP file was not created: {zip_path}")

        # Validate store-only header for all entries
        with zipfile.ZipFile(zip_path, 'r') as verify_zip:
            for info in verify_zip.infolist():
                if info.compress_type != zipfile.ZIP_STORED:
                    raise ZipEngineError(
                        f"ZIP entry '{info.filename}' not stored (compress_type={info.compress_type})"
                    )

        return zip_path

        # Store SHA256 for verification
        sha256_path = f"{zip_path}.sha256"
        digest = _compute_sha256(zip_path)
        with open(sha256_path, "w") as digest_file:
            digest_file.write(digest)

    except zipfile.BadZipFile as e:
        raise ZipEngineError(f"Failed to create ZIP: {e}") from e
    except Exception as e:
        raise ZipEngineError(f"Unexpected error during ZIP creation: {e}") from e


def _ensure_zip_entry_safe(entry_name: str) -> None:
    norm = os.path.normpath(entry_name)
    if os.path.isabs(entry_name):
        raise ZipEngineError(f"ZIP entry uses absolute path: {entry_name}")
    if norm.startswith("..") or ".." in norm.split(os.path.sep):
        raise ZipEngineError(f"ZIP entry attempts traversal: {entry_name}")


def unzip_folder_smart(
    zip_path: str,
    dest_folder: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> str:
    """
    Extract ZIP maintaining original folder structure

    **MRC: Reliable extraction with progress tracking**

    Args:
        zip_path: Path to ZIP file
        dest_folder: Destination folder path
        progress_callback: Optional callback(files_done, total_files, current_file)

    Returns:
        str: Path to extracted folder

    Raises:
        InvalidPathError: If ZIP doesn't exist
        ZipEngineError: If extraction fails
    """
    if not os.path.exists(zip_path):
        raise InvalidPathError(f"ZIP file does not exist: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise InvalidPathError(f"File is not a valid ZIP: {zip_path}")

    try:
        sha256_path = f"{zip_path}.sha256"
        if os.path.exists(sha256_path):
            expected = open(sha256_path).read().strip()
            actual = _compute_sha256(zip_path)
            if actual != expected:
                raise ZipEngineError(
                    f"ZIP integrity failed: expected {expected}, got {actual}"
                )
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            total_files = len(file_list)
            files_extracted = 0

            for file_name in file_list:
                _ensure_zip_entry_safe(file_name)
                try:
                    extracted_path = zipf.extract(file_name, dest_folder)
                    os.utime(extracted_path, (0, 0))
                    files_extracted += 1

                    if progress_callback:
                        progress_callback(files_extracted, total_files, file_name)

                except Exception as e:
                    print(f"Warning: Failed to extract {file_name}: {e}")
                    continue

        return dest_folder

    except zipfile.BadZipFile as e:
        raise ZipEngineError(f"Invalid or corrupted ZIP file: {e}") from e
    except Exception as e:
        raise ZipEngineError(f"Unexpected error during extraction: {e}") from e


def validate_zip_integrity(zip_path: str) -> Tuple[bool, str]:
    """
    Validate ZIP file integrity

    MRC: Simple validation - can we open it?

    Args:
        zip_path: Path to ZIP file

    Returns:
        Tuple[bool, str]: (is_valid, message)
            - (True, "ZIP is valid") if file exists and is readable
            - (False, "Error message") otherwise
    """
    if not os.path.exists(zip_path):
        return (False, f"ZIP file not found: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Test ZIP integrity
            bad_file = zipf.testzip()
            if bad_file:
                return (False, f"ZIP corrupted at file: {bad_file}")
            return (True, "ZIP is valid")
    except zipfile.BadZipFile:
        return (False, "Invalid ZIP file or corrupted archive")
    except Exception as e:
        return (False, f"Error validating ZIP: {str(e)}")


def get_zip_info(zip_path: str) -> dict:
    """
    Get information about a ZIP file

    Args:
        zip_path: Path to ZIP file

    Returns:
        dict: {
            'file_count': int,
            'compressed_size': int,
            'uncompressed_size': int,
            'compression_ratio': float,
            'files': list[str]
        }

    Raises:
        InvalidPathError: If ZIP doesn't exist or is invalid
    """
    if not os.path.exists(zip_path):
        raise InvalidPathError(f"ZIP file does not exist: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise InvalidPathError(f"File is not a valid ZIP: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            info_list = zipf.infolist()

            file_count = len(info_list)
            compressed_size = sum(info.compress_size for info in info_list)
            uncompressed_size = sum(info.file_size for info in info_list)

            compression_ratio = 0.0
            if uncompressed_size > 0:
                compression_ratio = (1 - compressed_size / uncompressed_size) * 100

            files = [info.filename for info in info_list]

            return {
                'file_count': file_count,
                'compressed_size': compressed_size,
                'uncompressed_size': uncompressed_size,
                'compression_ratio': compression_ratio,
                'files': files
            }
    except Exception as e:
        raise ZipEngineError(f"Failed to read ZIP info: {e}") from e


def cleanup_zip_file(zip_path: str) -> bool:
    """
    Delete ZIP file after successful transfer

    MRC: Simple cleanup helper

    Args:
        zip_path: Path to ZIP file to delete

    Returns:
        bool: True if deleted successfully
    """
    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            return True
        return False
    except Exception:
        return False


# Helper functions for formatting

def _compute_sha256(path: str) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def format_file_count(count: int) -> str:
    """Format file count for display"""
    if count == 1:
        return "1 file"
    return f"{count:,} files"


def format_bytes(bytes_value: int) -> str:
    """Format bytes for human-readable display"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def estimate_zip_time(folder_size_bytes: int, file_count: int) -> float:
    """
    Estimate time to ZIP folder (STORE mode)

    STORE mode is very fast: ~100-200 MB/s
    Time = disk I/O + overhead per file

    Args:
        folder_size_bytes: Total size in bytes
        file_count: Number of files

    Returns:
        float: Estimated seconds
    """
    # Assume 150 MB/s for STORE mode
    io_time = folder_size_bytes / (150 * 1024 * 1024)

    # Add ~0.001s overhead per file
    overhead = file_count * 0.001

    return io_time + overhead


def estimate_unzip_time(zip_size_bytes: int, file_count: int) -> float:
    """
    Estimate time to unzip (STORE mode)

    Similar to ZIP time for STORE mode

    Args:
        zip_size_bytes: ZIP file size in bytes
        file_count: Number of files in ZIP

    Returns:
        float: Estimated seconds
    """
    # Assume 150 MB/s extraction
    io_time = zip_size_bytes / (150 * 1024 * 1024)

    # Add ~0.001s overhead per file
    overhead = file_count * 0.001

    return io_time + overhead
