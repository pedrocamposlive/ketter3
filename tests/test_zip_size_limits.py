import os
import tempfile
import zipfile

import pytest

from app.core import zip_engine
from app.core.zip_engine import ZipEngineError, zip_folder_smart

MAX_ENTRY_BYTES = 10 * 1024 * 1024


def test_zip_entry_size_limit():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "src")
        os.makedirs(source)
        large_path = os.path.join(source, "large.bin")
        with open(large_path, "wb") as f:
            f.write(b"\x00" * (MAX_ENTRY_BYTES + 1))

        zip_path = os.path.join(tmpdir, "out.zip")
        with pytest.raises(ZipEngineError):
            zip_folder_smart(source, zip_path)


def test_zip_total_size_limit():
    zip_engine.MAX_ZIP_TOTAL_BYTES = 1024 * 1024  # 1 MB for test
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "src")
        os.makedirs(source)
        for i in range(2):
            with open(os.path.join(source, f"part{i}.bin"), "wb") as f:
                f.write(b"\x00" * (MAX_ENTRY_BYTES // 2))

        zip_path = os.path.join(tmpdir, "out.zip")
        with pytest.raises(ZipEngineError):
            zip_folder_smart(source, zip_path)
