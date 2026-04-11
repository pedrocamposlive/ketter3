import os
import tempfile
import pytest
from app.core.zip_engine import zip_folder_smart, unzip_folder_smart
from app.core.watch_folder import watch_folder_until_stable

class TestProToolsScenario:
    def test_protools_session_transfer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock Pro Tools session
            session_dir = os.path.join(tmpdir, "My Session")
            os.makedirs(session_dir)
            
            # Create Audio Files folder
            audio_dir = os.path.join(session_dir, "Audio Files")
            os.makedirs(audio_dir)
            
            # Create some mock audio files
            for i in range(5):
                with open(os.path.join(audio_dir, f"audio_{i}.wav"), "w") as f:
                    f.write("mock audio data" * 100)
                    
            # Create session file
            with open(os.path.join(session_dir, "My Session.ptx"), "w") as f:
                f.write("mock session data")
                
            # 1. Watch folder until stable
            is_stable = watch_folder_until_stable(
                session_dir,
                settle_time_seconds=1,
                max_wait_seconds=5
            )
            assert is_stable is True
            
            # 2. Zip the session
            zip_path = os.path.join(tmpdir, "session.zip")
            zip_folder_smart(session_dir, zip_path)
            assert os.path.exists(zip_path)
            
            # 3. Unzip the session
            dest_dir = os.path.join(tmpdir, "Destination")
            os.makedirs(dest_dir)
            unzip_folder_smart(zip_path, dest_dir)
            
            # Verify contents
            print(f"Extracted contents: {os.listdir(dest_dir)}")
            if os.path.exists(os.path.join(dest_dir, "My Session")):
                print(f"My Session contents: {os.listdir(os.path.join(dest_dir, 'My Session'))}")
            
            # The zip_folder_smart zips the CONTENTS of the folder, not the folder itself
            # So we should check for the contents directly in dest_dir
            assert os.path.exists(os.path.join(dest_dir, "My Session.ptx"))
            assert os.path.exists(os.path.join(dest_dir, "Audio Files", "audio_0.wav"))
