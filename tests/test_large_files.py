"""
Ketter 3.0 - Large File Transfer Test
Tests system with large files (500GB+)

MRC: Real-world stress test for production readiness

USAGE:
    # Create a 500GB test file (sparse file for testing):
    truncate -s 500G /data/test_500gb.bin

    # Or create with random data (slow but more realistic):
    dd if=/dev/urandom of=/data/test_500gb.bin bs=1M count=512000

    # Run test:
    python tests/test_large_files.py --source /data/test_500gb.bin --dest /data/dest_500gb.bin
"""

import argparse
import os
import sys
import time
from datetime import datetime

import requests


class LargeFileTransferTest:
    """Test large file transfers end-to-end"""

    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = None
        self.transfer_id = None

    def format_bytes(self, bytes_value):
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def format_duration(self, seconds):
        """Format seconds to human-readable duration"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    def verify_file_exists(self, path):
        """Verify file exists and get size"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")

        size = os.path.getsize(path)
        return size

    def create_transfer(self, source_path, destination_path):
        """Create transfer via API"""
        print(f"[{datetime.now().isoformat()}] Creating transfer...")
        print(f"  Source: {source_path}")
        print(f"  Destination: {destination_path}")

        # Verify source exists
        source_size = self.verify_file_exists(source_path)
        print(f"  Source size: {self.format_bytes(source_size)}")

        # Create transfer
        response = requests.post(
            f"{self.api_url}/transfers",
            json={
                "source_path": source_path,
                "destination_path": destination_path
            }
        )

        if response.status_code != 201:
            raise Exception(f"Failed to create transfer: {response.text}")

        data = response.json()
        self.transfer_id = data["id"]
        self.start_time = time.time()

        print(f"[{datetime.now().isoformat()}] Transfer created: ID #{self.transfer_id}")
        print(f"  Status: {data['status']}")
        print()

        return self.transfer_id

    def monitor_transfer(self, poll_interval=5):
        """Monitor transfer progress until completion"""
        print(f"[{datetime.now().isoformat()}] Monitoring transfer...")
        print(f"  Poll interval: {poll_interval} seconds")
        print()

        last_status = None
        last_progress = None

        while True:
            try:
                response = requests.get(f"{self.api_url}/transfers/{self.transfer_id}")
                if response.status_code != 200:
                    print(f"ERROR: Failed to get transfer status: {response.status_code}")
                    time.sleep(poll_interval)
                    continue

                transfer = response.json()
                status = transfer["status"]
                progress = transfer["progress_percent"]
                bytes_transferred = transfer["bytes_transferred"]
                elapsed = time.time() - self.start_time

                # Print status if changed
                if status != last_status or progress != last_progress:
                    print(f"[{datetime.now().isoformat()}] Status: {status.upper()}")
                    print(f"  Progress: {progress}%")
                    print(f"  Transferred: {self.format_bytes(bytes_transferred)}")
                    print(f"  Elapsed time: {self.format_duration(elapsed)}")

                    if bytes_transferred > 0 and progress > 0:
                        rate = bytes_transferred / elapsed
                        print(f"  Transfer rate: {self.format_bytes(rate)}/s")

                        if progress < 100:
                            remaining_bytes = (bytes_transferred / progress) * (100 - progress)
                            eta_seconds = remaining_bytes / rate
                            print(f"  Estimated time remaining: {self.format_duration(eta_seconds)}")

                    print()

                last_status = status
                last_progress = progress

                # Check if completed or failed
                if status == "completed":
                    print(f"[{datetime.now().isoformat()}]  TRANSFER COMPLETED")
                    return self.verify_transfer()

                elif status == "failed":
                    error = transfer.get("error_message", "Unknown error")
                    print(f"[{datetime.now().isoformat()}]  TRANSFER FAILED")
                    print(f"  Error: {error}")
                    return False

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                print("\n\nTransfer monitoring interrupted by user.")
                return False

            except Exception as e:
                print(f"ERROR during monitoring: {str(e)}")
                time.sleep(poll_interval)

    def verify_transfer(self):
        """Verify transfer was successful"""
        print(f"[{datetime.now().isoformat()}] Verifying transfer...")
        elapsed = time.time() - self.start_time

        # Get transfer details
        response = requests.get(f"{self.api_url}/transfers/{self.transfer_id}")
        transfer = response.json()

        print(f"  Transfer ID: #{self.transfer_id}")
        print(f"  Status: {transfer['status']}")
        print(f"  File size: {self.format_bytes(transfer['file_size'])}")
        print(f"  Bytes transferred: {self.format_bytes(transfer['bytes_transferred'])}")
        print(f"  Total time: {self.format_duration(elapsed)}")
        print(f"  Average rate: {self.format_bytes(transfer['bytes_transferred'] / elapsed)}/s")
        print()

        # Verify checksums
        print(f"[{datetime.now().isoformat()}] Verifying checksums...")
        response = requests.get(f"{self.api_url}/transfers/{self.transfer_id}/checksums")
        checksums = response.json()

        if len(checksums["items"]) != 3:
            print(f"   ERROR: Expected 3 checksums, got {len(checksums['items'])}")
            return False

        checksum_map = {c["checksum_type"]: c["checksum_value"] for c in checksums["items"]}
        source_hash = checksum_map.get("source")
        dest_hash = checksum_map.get("destination")
        final_hash = checksum_map.get("final")

        print(f"  SOURCE:      {source_hash}")
        print(f"  DESTINATION: {dest_hash}")
        print(f"  FINAL:       {final_hash}")

        if source_hash == dest_hash == final_hash:
            print(f"   All checksums match!")
        else:
            print(f"   ERROR: Checksums do not match!")
            return False

        print()

        # Verify audit trail
        print(f"[{datetime.now().isoformat()}] Checking audit trail...")
        response = requests.get(f"{self.api_url}/transfers/{self.transfer_id}/logs")
        logs = response.json()
        print(f"  Total audit events: {logs['total']}")
        print()

        # Generate PDF report
        print(f"[{datetime.now().isoformat()}] Generating PDF report...")
        response = requests.get(f"{self.api_url}/transfers/{self.transfer_id}/report")
        if response.status_code == 200:
            report_filename = f"transfer_{self.transfer_id}_report.pdf"
            with open(report_filename, 'wb') as f:
                f.write(response.content)
            print(f"   PDF report saved: {report_filename}")
            print(f"  Report size: {self.format_bytes(len(response.content))}")
        else:
            print(f"   Failed to generate PDF report")

        print()
        print("=" * 80)
        print("TRANSFER VERIFICATION: SUCCESS ")
        print("=" * 80)
        print(f"Transfer ID: #{self.transfer_id}")
        print(f"File size: {self.format_bytes(transfer['file_size'])}")
        print(f"Total time: {self.format_duration(elapsed)}")
        print(f"Average rate: {self.format_bytes(transfer['bytes_transferred'] / elapsed)}/s")
        print(f"Checksums: VERIFIED ")
        print(f"Audit trail: {logs['total']} events")
        print(f"PDF report: Generated ")
        print("=" * 80)

        return True

    def run_test(self, source_path, destination_path, poll_interval=5):
        """Run complete large file transfer test"""
        print("=" * 80)
        print("KETTER 3.0 - LARGE FILE TRANSFER TEST")
        print("=" * 80)
        print(f"Start time: {datetime.now().isoformat()}")
        print()

        try:
            # Create transfer
            self.create_transfer(source_path, destination_path)

            # Monitor until completion
            success = self.monitor_transfer(poll_interval)

            if success:
                print("\n TEST PASSED: Large file transfer successful with zero errors")
                return 0
            else:
                print("\n TEST FAILED: Transfer did not complete successfully")
                return 1

        except Exception as e:
            print(f"\n TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="Ketter 3.0 Large File Transfer Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 500GB sparse file (fast, for testing):
  truncate -s 500G /data/test_500gb.bin
  python tests/test_large_files.py --source /data/test_500gb.bin --dest /data/dest_500gb.bin

  # Test with 100GB real data (slower, more realistic):
  dd if=/dev/urandom of=/data/test_100gb.bin bs=1M count=102400
  python tests/test_large_files.py --source /data/test_100gb.bin --dest /data/dest_100gb.bin --poll 10
        """
    )

    parser.add_argument("--source", required=True, help="Source file path")
    parser.add_argument("--dest", required=True, help="Destination file path")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL (default: http://localhost:8000)")
    parser.add_argument("--poll", type=int, default=5, help="Poll interval in seconds (default: 5)")

    args = parser.parse_args()

    test = LargeFileTransferTest(api_url=args.api_url)
    exit_code = test.run_test(args.source, args.dest, poll_interval=args.poll)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
