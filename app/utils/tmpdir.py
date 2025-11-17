"""Secure temporary directory helpers"""

import os
import tempfile
import secrets

from typing import Optional


def create_secure_tmpdir(base_dir: Optional[str] = None) -> str:
    """Create a randomized tmpdir guarded by Ketter-specific prefix"""
    base_dir = base_dir or os.getenv("KETTER_TMP_BASE", "/tmp")
    prefix = f"ketter-{secrets.token_hex(8)}-"
    return tempfile.mkdtemp(prefix=prefix, dir=base_dir)
