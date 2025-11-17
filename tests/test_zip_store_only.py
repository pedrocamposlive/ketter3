import os
import tempfile
import zipfile

from app.core.zip_engine import zip_folder_smart


def test_zip_folder_store_only():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        os.makedirs(source)
        file_path = os.path.join(source, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello")

        zip_path = os.path.join(tmpdir, "output.zip")
        zip_folder_smart(source, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_STORED
