import io
import zipfile
import tempfile
import os
import pytest

from app.core.zip_engine import zip_folder_smart, ZipEngineError


def test_zip_traversal_guard():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        os.makedirs(source)
        safe_file = os.path.join(source, "safe.txt")
        with open(safe_file, "w") as f:
            f.write("ok")

        zip_path = os.path.join(tmpdir, "archive.zip")
        zip_folder_smart(source, zip_path)

        # Inject a malicious entry
        with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_STORED) as zf:
            zf.writestr("../evil.txt", "bad")

        with pytest.raises(ZipEngineError):
            from app.core.zip_engine import unzip_folder_smart
            unzip_folder_smart(zip_path, os.path.join(tmpdir, "dest"))
