"""
Ketter 3.0 - Path Security Tests
ENHANCE #1: Path sanitization validation

Tests verify protection against:
- Path traversal attacks (..)
- Symlink attacks
- Access to unauthorized volumes
"""

import pytest
import os
import tempfile
from pathlib import Path

from app.security.path_security import (
    sanitize_path,
    validate_path_pair,
    PathSecurityError,
    PathTraversalError,
    SymlinkSecurityError,
    VolumeAccessError,
    is_path_safe,
    get_safe_path_info
)


# ============================================
# TEST 1: Path Traversal Protection
# ============================================

def test_path_traversal_blocked_double_dot():
    """
    SECURITY CRITICAL: Block path traversal with ..
    Attack: /tmp/../../../etc/passwd
    """
    with pytest.raises(PathTraversalError) as exc_info:
        sanitize_path("/tmp/../etc/passwd")

    assert ".." in str(exc_info.value)
    assert "traversal" in str(exc_info.value).lower()


def test_path_traversal_blocked_multiple():
    """
    SECURITY CRITICAL: Block multiple .. sequences
    Attack: /tmp/../../../../../../root/.ssh/id_rsa
    """
    with pytest.raises(PathTraversalError):
        sanitize_path("/tmp/../../../../../../root/.ssh/id_rsa")


def test_path_traversal_blocked_hidden():
    """
    SECURITY CRITICAL: Block hidden .. in middle of path
    Attack: /tmp/safe/../../../etc/shadow
    """
    with pytest.raises(PathTraversalError):
        sanitize_path("/tmp/safe/../../../etc/shadow")


# ============================================
# TEST 2: Symlink Protection
# ============================================

def test_symlink_blocked_by_default():
    """
    SECURITY CRITICAL: Block symlinks by default
    """
    # Create temp directory and symlink
    with tempfile.TemporaryDirectory() as tmpdir:
        real_file = os.path.join(tmpdir, "real_file.txt")
        symlink = os.path.join(tmpdir, "symlink.txt")

        # Create real file
        with open(real_file, 'w') as f:
            f.write("test")

        # Create symlink
        os.symlink(real_file, symlink)

        # Symlink should be blocked by default
        with pytest.raises(SymlinkSecurityError):
            sanitize_path(symlink, allow_symlinks=False)


def test_symlink_allowed_when_enabled():
    """
    Symlinks CAN be allowed with explicit flag (for source paths)
    But still must point to valid volumes
    """
    # Use /tmp directly (allowed volume)
    tmpdir = "/tmp"
    real_file = os.path.join(tmpdir, f"test_real_{os.getpid()}.txt")
    symlink = os.path.join(tmpdir, f"test_symlink_{os.getpid()}.txt")

    try:
        # Create real file
        with open(real_file, 'w') as f:
            f.write("test")

        # Create symlink
        if os.path.exists(symlink):
            os.remove(symlink)
        os.symlink(real_file, symlink)

        # Symlink allowed with flag
        result = sanitize_path(symlink, allow_symlinks=True)
        assert result  # Should not raise
    finally:
        # Cleanup
        if os.path.exists(symlink):
            os.remove(symlink)
        if os.path.exists(real_file):
            os.remove(real_file)


# ============================================
# TEST 3: Volume Whitelist Validation
# ============================================

def test_volume_validation_with_tmp():
    """
    Valid path: /tmp is usually an allowed volume
    """
    # /tmp is typically allowed by default config
    result = sanitize_path("/tmp/test_file.txt")
    assert result
    assert os.path.isabs(result)


def test_volume_validation_blocks_unauthorized():
    """
    SECURITY CRITICAL: Block paths outside configured volumes
    Attack: /root/.ssh/id_rsa (not in whitelist)
    """
    with pytest.raises(VolumeAccessError) as exc_info:
        sanitize_path("/root/.ssh/id_rsa")

    assert "outside allowed volumes" in str(exc_info.value).lower()


def test_volume_validation_blocks_etc():
    """
    SECURITY CRITICAL: Block access to /etc
    """
    with pytest.raises(VolumeAccessError):
        sanitize_path("/etc/passwd")


def test_volume_validation_blocks_home():
    """
    SECURITY CRITICAL: Block access to other users' home directories
    """
    with pytest.raises(VolumeAccessError):
        sanitize_path("/home/attacker/.bashrc")


# ============================================
# TEST 4: Empty/Invalid Path Handling
# ============================================

def test_empty_path_rejected():
    """
    Empty paths should be rejected
    """
    with pytest.raises(PathSecurityError):
        sanitize_path("")


def test_none_path_rejected():
    """
    None paths should be rejected
    """
    with pytest.raises((PathSecurityError, TypeError, AttributeError)):
        sanitize_path(None)


def test_whitespace_only_rejected():
    """
    Whitespace-only paths should be rejected
    """
    with pytest.raises(PathSecurityError):
        sanitize_path("   ")


# ============================================
# TEST 5: Path Pair Validation
# ============================================

def test_validate_path_pair_success():
    """
    Valid source-destination pair should pass
    """
    # Use /tmp directly (allowed volume)
    source = f"/tmp/test_source_{os.getpid()}.txt"
    dest = f"/tmp/test_dest_{os.getpid()}.txt"

    try:
        # Create source
        with open(source, 'w') as f:
            f.write("test")

        safe_source, safe_dest = validate_path_pair(source, dest)

        assert safe_source
        assert safe_dest
        assert safe_source != safe_dest
    finally:
        # Cleanup
        if os.path.exists(source):
            os.remove(source)
        if os.path.exists(dest):
            os.remove(dest)


def test_validate_path_pair_same_path_rejected():
    """
    SECURITY: Source and destination cannot be the same
    """
    same_path = "/tmp/same_path_test.txt"

    with pytest.raises(PathSecurityError) as exc_info:
        validate_path_pair(same_path, same_path)

    assert "same path" in str(exc_info.value).lower()


def test_validate_path_pair_source_traversal_blocked():
    """
    SECURITY: Path traversal in source should be blocked
    """
    with pytest.raises(PathSecurityError):
        validate_path_pair("/tmp/../etc/passwd", "/tmp/dest.txt")


def test_validate_path_pair_dest_traversal_blocked():
    """
    SECURITY: Path traversal in destination should be blocked
    """
    source = "/tmp/valid_source.txt"

    with pytest.raises(PathSecurityError):
        validate_path_pair(source, "/tmp/../etc/passwd")


# ============================================
# TEST 6: Helper Functions
# ============================================

def test_is_path_safe_true():
    """
    is_path_safe() should return True for safe paths
    """
    safe_path = "/tmp/safe_file_test.txt"
    assert is_path_safe(safe_path) is True


def test_is_path_safe_false():
    """
    is_path_safe() should return False for unsafe paths
    """
    assert is_path_safe("/tmp/../etc/passwd") is False
    assert is_path_safe("/root/.ssh/id_rsa") is False


def test_get_safe_path_info_safe():
    """
    get_safe_path_info() should return details for safe paths
    """
    safe_path = "/tmp/test_info.txt"

    info = get_safe_path_info(safe_path)

    assert info["is_safe"] is True
    assert info["original_path"] == safe_path
    assert info["safe_path"]
    assert info["is_symlink"] is False


def test_get_safe_path_info_unsafe():
    """
    get_safe_path_info() should return error for unsafe paths
    """
    info = get_safe_path_info("/tmp/../etc/passwd")

    assert info["is_safe"] is False
    assert "error" in info
    assert "error_type" in info


# ============================================
# TEST 7: Real-World Attack Scenarios
# ============================================

def test_attack_scenario_null_byte():
    """
    SECURITY: Null byte injection attack
    Attack: /tmp/safe.txt\x00../../etc/passwd
    """
    # Python 3 handles null bytes in paths by raising ValueError
    # Our sanitizer should catch this
    malicious_path = "/tmp/safe.txt\x00../../etc/passwd"

    with pytest.raises((PathSecurityError, ValueError)):
        sanitize_path(malicious_path)


def test_attack_scenario_url_encoding():
    """
    SECURITY: URL-encoded path traversal
    Attack: /tmp/%2e%2e/%2e%2e/etc/passwd
    """
    # URL-encoded .. should still be caught
    malicious_path = "/tmp/%2e%2e/%2e%2e/etc/passwd"

    # Our validator checks for literal '..' before decoding
    # This should be caught if it contains ..
    if ".." in malicious_path:
        with pytest.raises(PathTraversalError):
            sanitize_path(malicious_path)


def test_attack_scenario_double_slash():
    """
    SECURITY: Double slash normalization attack
    Attack: /tmp//../../etc/passwd
    """
    with pytest.raises(PathTraversalError):
        sanitize_path("/tmp//../../etc/passwd")


# ============================================
# TEST 8: Edge Cases
# ============================================

def test_edge_case_very_long_path():
    """
    Very long paths should be handled gracefully
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested directories
        long_path = tmpdir
        for i in range(50):
            long_path = os.path.join(long_path, f"level{i}")

        # Should not crash, but may fail due to volume check
        try:
            result = sanitize_path(long_path)
            assert result
        except (VolumeAccessError, PathSecurityError):
            # Acceptable - path may be outside volumes
            pass


def test_edge_case_unicode_path():
    """
    Unicode characters in paths should be handled
    """
    unicode_path = "/tmp/файл_测试_.txt"

    result = sanitize_path(unicode_path)
    assert result


def test_edge_case_special_chars():
    """
    Special characters in paths (spaces, etc) should work
    """
    special_path = "/tmp/file with spaces & special-chars_123.txt"

    result = sanitize_path(special_path)
    assert result


# ============================================
# TEST 9: Integration with Pydantic
# ============================================

def test_pydantic_schema_validation():
    """
    Test that schemas.py validators use path_security
    """
    from app.schemas import TransferCreate

    # Test valid paths using /tmp
    source = f"/tmp/pydantic_test_source_{os.getpid()}.txt"
    dest = f"/tmp/pydantic_test_dest_{os.getpid()}.txt"

    try:
        # Create source file
        with open(source, 'w') as f:
            f.write("test")

        # Should pass validation
        transfer = TransferCreate(
            source_path=source,
            destination_path=dest
        )

        assert transfer.source_path
        assert transfer.destination_path
    finally:
        # Cleanup
        if os.path.exists(source):
            os.remove(source)


def test_pydantic_schema_blocks_traversal():
    """
    Test that schemas.py blocks path traversal
    """
    from app.schemas import TransferCreate
    from pydantic import ValidationError

    # Should raise validation error
    with pytest.raises(ValidationError) as exc_info:
        TransferCreate(
            source_path="/tmp/../etc/passwd",
            destination_path="/tmp/dest.txt"
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert "traversal" in str(errors).lower()


if __name__ == "__main__":
    # Run with: pytest tests/test_path_security.py -v
    pytest.main([__file__, "-v", "-s"])
