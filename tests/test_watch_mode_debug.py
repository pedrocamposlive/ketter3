"""
Debug test for watch mode - trace every function call
"""

import os
import tempfile
from pathlib import Path
from app.core.watch_folder import watch_folder_until_stable, get_folder_state, compare_folder_states
from app.core.copy_engine import transfer_file_with_verification
from app.database import SessionLocal
from app.models import Transfer, TransferStatus, AuditLog
from datetime import datetime


def test_watch_mode_complete_flow():
    """Trace complete flow: watch -> transfer -> MOVE delete"""

    # Create temp directories
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        dest = os.path.join(tmpdir, "dest")
        os.makedirs(source)
        os.makedirs(dest)

        # Create test file
        test_file = os.path.join(source, "test.txt")
        Path(test_file).write_text("test content")

        print(f"\n=== SETUP ===")
        print(f"Source folder: {source}")
        print(f"Dest folder: {dest}")
        print(f"Test file: {test_file}")
        assert os.path.exists(test_file), "Test file not created"

        # STEP 1: Test watch_folder_until_stable
        print(f"\n=== STEP 1: Watch folder ===")
        try:
            became_stable = watch_folder_until_stable(
                source,
                settle_time_seconds=2,  # Short timeout for testing
                max_wait_seconds=10
            )
            print(f"Watch result: became_stable={became_stable}")
            assert became_stable, "Watch should detect stable folder"
        except Exception as e:
            print(f"WATCH ERROR: {e}")
            raise

        # STEP 2: Create transfer in DB
        print(f"\n=== STEP 2: Create transfer ===")
        db = SessionLocal()
        try:
            transfer = Transfer(
                source_path=source,
                destination_path=dest,
                file_size=0,  # Will be updated
                file_name=os.path.basename(test_file),
                status=TransferStatus.PENDING,
                watch_mode_enabled=1,
                settle_time_seconds=2,
                operation_mode="move"  # MOVE mode - delete after
            )
            db.add(transfer)
            db.commit()
            transfer_id = transfer.id
            print(f"Transfer created: id={transfer_id}, status={transfer.status}, mode={transfer.operation_mode}")

            # STEP 3: Execute transfer
            print(f"\n=== STEP 3: Execute transfer ===")
            result = transfer_file_with_verification(transfer_id, db)

            # Reload transfer to check status
            transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
            print(f"Transfer after execution:")
            print(f"  - status: {transfer.status}")
            print(f"  - completed_at: {transfer.completed_at}")
            print(f"  - bytes_transferred: {transfer.bytes_transferred}")
            print(f"  - operation_mode: {transfer.operation_mode}")

            # STEP 4: Check if file was deleted (MOVE mode)
            print(f"\n=== STEP 4: Verify MOVE mode ===")
            print(f"Source folder exists: {os.path.exists(source)}")
            print(f"Dest folder contents: {os.listdir(dest)}")

            if os.path.exists(test_file):
                print(f"ERROR: Test file still exists in source! MOVE mode didn't delete!")
                assert False, "MOVE mode should delete source"
            else:
                print(f"SUCCESS: Test file deleted from source (MOVE mode working)")

            # Check destination
            if os.path.exists(dest) and len(os.listdir(dest)) > 0:
                print(f"SUCCESS: File found in destination")
            else:
                print(f"ERROR: File not found in destination!")
                assert False, "File should be in destination"

            # STEP 5: Check audit trail
            print(f"\n=== STEP 5: Audit trail ===")
            logs = db.query(AuditLog).filter(AuditLog.transfer_id == transfer_id).all()
            for log in logs:
                print(f"  [{log.event_type}] {log.message}")

        finally:
            db.close()

        print(f"\n=== TEST PASSED ===")


if __name__ == "__main__":
    test_watch_mode_complete_flow()
