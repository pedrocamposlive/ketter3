"""
Ketter 3.0 - Path Security Module
ENHANCE #1: Path sanitization and validation

Protects against:
- Path traversal attacks (../)
- Symlink attacks
- Access to paths outside allowed volumes

MRC Principles:
- Simple: Clear validation logic
- Reliable: Multiple layers of defense
- Transparent: Explicit error messages
"""

import os
import re
import unicodedata
from typing import Tuple
from pathlib import Path
from app.config import get_config

TRANSFER_NODE_MODE = os.getenv("TRANSFER_NODE_MODE", "0") == "1"
CURRENT_VLAN_ID = os.getenv("KETTER_VLAN_ID")

_INVALID_PATH_CHARS = re.compile(r'[\x00-\x1f\x7f<>:"|?*]')
_INVISIBLE_WHITESPACE = re.compile(r'[\u2000-\u200F\u2028-\u202F\u205F\uFEFF]')
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]"
)
_ENCODED_TRAVERSAL = re.compile(r'%2[0-9a-fA-F]')


def canonicalize_path(path: str) -> str:
    """
    Return normalized/casefolded form for inter-VLAN comparison.
    """
    normalized = unicodedata.normalize("NFC", os.path.normpath(path))
    return normalized.casefold()


class PathSecurityError(Exception):
    """Base exception for path security violations"""
    pass


class PathTraversalError(PathSecurityError):
    """Raised when path traversal attempt detected"""
    pass


class SymlinkSecurityError(PathSecurityError):
    """Raised when symlink points outside allowed volumes"""
    pass


class VolumeAccessError(PathSecurityError):
    """Raised when path is outside configured volumes"""
    pass


def sanitize_path(path: str, allow_symlinks: bool = False) -> str:
    """
    Sanitize and validate a file path for security

    **SECURITY CRITICAL FUNCTION**

    Protections:
    1. Resolves absolute path (eliminates ..)
    2. Validates against configured volumes whitelist
    3. Blocks symlinks pointing outside volumes (optional)
    4. Prevents path traversal attacks

    Args:
        path: User-provided file path
        allow_symlinks: If True, allows symlinks (still validates target)

    Returns:
        str: Sanitized absolute path (safe to use)

    Raises:
        PathTraversalError: If path contains traversal attempts
        SymlinkSecurityError: If symlink points outside volumes
        VolumeAccessError: If path is outside configured volumes
        PathSecurityError: For other security violations

    Example:
        >>> sanitize_path("/tmp/../etc/passwd")
        PathTraversalError: Path traversal detected

        >>> sanitize_path("/tmp/safe_file.txt")
        "/tmp/safe_file.txt"
    """
    if not path:
        raise PathSecurityError("Empty path provided")

    path = unicodedata.normalize("NFC", path)

    if _INVALID_PATH_CHARS.search(path) or _INVISIBLE_WHITESPACE.search(path):
        raise PathSecurityError(
            f"Path contains forbidden characters: {path}"
        )

    lowered_path = path.lower()
    if "%2e%2e" in lowered_path or "%2e%2f" in lowered_path or "%2f%2e" in lowered_path:
        raise PathTraversalError(
            f"Encoded traversal detected: {path}"
        )
    # Step 1: Check for obvious traversal patterns BEFORE resolving
    # This catches attempts like "../../etc/passwd"
    if ".." in path:
        raise PathTraversalError(
            f"Path traversal detected: '..' found in path: {path}"
        )

    # Step 2: Resolve to absolute path
    # This eliminates symbolic links and relative paths
    try:
        # Use realpath to resolve symlinks and normalize
        absolute_path = unicodedata.normalize("NFC", os.path.realpath(path))
        canonical_path = canonicalize_path(absolute_path)
    except (OSError, ValueError) as e:
        raise PathSecurityError(f"Invalid path: {path} - Error: {e}")

    # Step 3: Check if symlink and validate
    if Path(path).is_symlink() and not allow_symlinks:
        raise SymlinkSecurityError(
            f"Symlinks not allowed: {path} -> {absolute_path}"
        )

        # If symlinks allowed, verify target is within volumes
        # (checked in Step 4 below)

    # Step 4: Validate against configured volumes whitelist
    config = get_config()

    # IMPORTANT: Resolve volume paths too (for macOS /tmp -> /private/tmp)
    # Check if absolute_path starts with any configured volume (resolved)
    is_valid = False
    for volume in config.volumes:
        resolved_volume = os.path.realpath(volume.path)
        canonical_volume = canonicalize_path(resolved_volume)

        if canonical_path.startswith(canonical_volume):
            if volume.check_mounted and not volume.is_available():
                raise VolumeAccessError(
                    f"Volume '{volume.alias}' is not mounted or accessible"
                )
            if volume.vlan_id and not TRANSFER_NODE_MODE:
                if CURRENT_VLAN_ID is None or str(volume.vlan_id) != CURRENT_VLAN_ID:
                    continue
            is_valid = True
            break

        canonical_original = canonicalize_path(volume.path)
        if canonical_path.startswith(canonical_original):
            if volume.check_mounted and not volume.is_available():
                raise VolumeAccessError(
                    f"Volume '{volume.alias}' is not mounted or accessible"
                )
            if volume.vlan_id and not TRANSFER_NODE_MODE:
                if CURRENT_VLAN_ID is None or str(volume.vlan_id) != CURRENT_VLAN_ID:
                    continue
            is_valid = True
            break

    if not is_valid:
        volume_paths = [v.path for v in config.volumes]
        raise VolumeAccessError(
            f"Path outside allowed volumes: {absolute_path} - "
            f"Path must start with a configured volume: {', '.join(volume_paths)}"
        )

    # Step 5: Additional check - ensure resolved path still matches original intent
    # This catches cases where realpath resolved to unexpected location
    original_normalized = os.path.normpath(path)
    resolved_normalized = os.path.normpath(absolute_path)

    # If paths differ significantly, it might be a symlink attack
    if not allow_symlinks and original_normalized != resolved_normalized:
        # Check if the difference is just absolute vs relative
        if not os.path.isabs(original_normalized):
            # Original was relative, now absolute - this is OK
            pass
        elif os.path.islink(path):
            # Symlink detected (already handled above, but double-check)
            raise SymlinkSecurityError(
                f"Symlink detected: {path} -> {absolute_path}"
            )

    # Path is safe!
    return absolute_path


def validate_path_pair(source: str, destination: str) -> Tuple[str, str]:
    """
    Validate and sanitize a source-destination path pair

    **SECURITY CRITICAL FUNCTION**

    Validates both paths and ensures they are safe for transfer operations.

    Args:
        source: Source file/folder path
        destination: Destination file/folder path

    Returns:
        Tuple[str, str]: (sanitized_source, sanitized_destination)

    Raises:
        PathSecurityError: If either path is invalid

    Example:
        >>> validate_path_pair("/tmp/file.txt", "/backup/file.txt")
        ("/tmp/file.txt", "/backup/file.txt")
    """
    # Sanitize source (allow symlinks for source - we'll read the target)
    try:
        safe_source = sanitize_path(source, allow_symlinks=True)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid source path: {e}")

    # Sanitize destination (no symlinks for destination)
    try:
        # For destination, we need to handle non-existent paths
        # (destination might not exist yet)
        dest_parent = os.path.dirname(destination)

        if dest_parent and os.path.exists(dest_parent):
            # Validate parent directory
            # Allow symlinks for parent (e.g., /tmp -> /private/tmp on macOS)
            # We just need parent to be within volumes
            safe_dest_parent = sanitize_path(dest_parent, allow_symlinks=True)
            # Reconstruct destination path
            dest_filename = os.path.basename(destination)
            safe_destination = os.path.join(safe_dest_parent, dest_filename)
        else:
            # Parent doesn't exist - validate the path structure only
            safe_destination = sanitize_path(destination, allow_symlinks=False)
    except PathSecurityError as e:
        raise PathSecurityError(f"Invalid destination path: {e}")

    # Additional validation: source and destination should be different
    if safe_source == safe_destination:
        raise PathSecurityError(
            "Source and destination cannot be the same path"
        )

    return safe_source, safe_destination


def is_path_safe(path: str) -> bool:
    """
    Quick check if path is safe (does not raise exception)

    Args:
        path: Path to check

    Returns:
        bool: True if path is safe, False otherwise
    """
    try:
        sanitize_path(path)
        return True
    except PathSecurityError:
        return False


def get_safe_path_info(path: str) -> dict:
    """
    Get information about a path with security validation

    Args:
        path: Path to analyze

    Returns:
        dict: Path information or error details
    """
    try:
        safe_path = sanitize_path(path)

        return {
            "is_safe": True,
            "original_path": path,
            "safe_path": safe_path,
            "is_symlink": os.path.islink(path),
            "exists": os.path.exists(safe_path),
            "is_file": os.path.isfile(safe_path) if os.path.exists(safe_path) else None,
            "is_dir": os.path.isdir(safe_path) if os.path.exists(safe_path) else None
        }
    except PathSecurityError as e:
        return {
            "is_safe": False,
            "original_path": path,
            "error": str(e),
            "error_type": type(e).__name__
        }


# Security audit log helper
def log_security_violation(path: str, error: PathSecurityError, user_context: dict = None):
    """
    Log security violations for audit trail

    Args:
        path: Attempted path
        error: Security error raised
        user_context: Optional context (IP, user, etc.)
    """
    # TODO: Integrate with proper logging system (PHASE 2)
    print(f" SECURITY VIOLATION: {type(error).__name__}")
    print(f"   Path: {path}")
    print(f"   Error: {error}")
    if user_context:
        print(f"   Context: {user_context}")
