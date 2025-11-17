import os
import tempfile
import zipfile
from datetime import datetime

from app.core.zip_engine import zip_folder_smart, unzip_folder_smart


def test_zip_metadata_scrub():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        os.makedirs(source)
        file_path = os.path.join(source, "file.txt")
        with open(file_path, "w") as f:
            f.write("data")

        zip_path = os.path.join(tmpdir, "audit.zip")
        zip_folder_smart(source, zip_path)

        dest = os.path.join(tmpdir, "dest")
        os.makedirs(dest, exist_ok=True)
        unzip_folder_smart(zip_path, dest)

        extracted = os.path.join(dest, "file.txt")
        stat = os.stat(extracted)
        assert stat.st_mtime == 0 and stat.st_atime == 0
