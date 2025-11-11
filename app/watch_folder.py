"""
Ketter 3.0 - Watch Folder Intelligence
Smart folder monitoring with "settle time" detection

MRC Principles:
- Simple: Basic file comparison (no inotify/fsevents complexity)
- Reliable: Multiple checks ensure folder is truly stable
- Transparent: Progress callbacks show what's happening
- Fast: Minimal overhead, configurable settle time

Use Case:
- Client transfers Pro Tools session → origem (30-60s via network)
- Watch mode waits for files to stop changing
- After settle_time seconds stable → auto-starts transfer
- Operator doesn't need to watch - system handles it

Algorithm:
1. Get folder state snapshot: {file_path: (size, mtime)}
2. Wait settle_time seconds
3. Get new snapshot
4. Compare: anything changed?
   - YES: Go back to step 2
   - NO: Folder is stable! Trigger transfer
"""

import os
import time
from datetime import datetime
from typing import Dict, Tuple, Optional, Callable


class WatchFolderError(Exception):
    """Base exception for Watch Folder errors"""
    pass


class FolderNotFoundError(WatchFolderError):
    """Raised when folder doesn't exist"""
    pass


def get_folder_state(folder_path: str) -> Dict[str, Tuple[int, float]]:
    """
    Get current state of all files in folder

    **MRC: Simple file snapshot**

    Creates a dictionary mapping each file path to its (size, mtime).
    This allows us to detect any changes by comparing snapshots.

    Args:
        folder_path: Path to folder to monitor

    Returns:
        dict: {file_path: (size_bytes, mtime_timestamp)}

    Raises:
        FolderNotFoundError: If folder doesn't exist

    Example:
        {
            '/path/to/file1.txt': (1024, 1699123456.789),
            '/path/to/file2.wav': (50000, 1699123460.123),
            ...
        }
    """
    if not os.path.exists(folder_path):
        raise FolderNotFoundError(f"Folder does not exist: {folder_path}")

    if not os.path.isdir(folder_path):
        raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

    folder_state = {}

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    size = stat.st_size
                    mtime = stat.st_mtime

                    folder_state[file_path] = (size, mtime)
                except (OSError, IOError):
                    # Skip files we can't read
                    continue

        return folder_state

    except Exception as e:
        raise WatchFolderError(f"Failed to get folder state: {e}") from e


def compare_folder_states(
    state1: Dict[str, Tuple[int, float]],
    state2: Dict[str, Tuple[int, float]]
) -> bool:
    """
    Compare two folder states to detect changes

    **MRC: Simple dictionary comparison**

    Returns True if folder is stable (no changes), False if changed.

    Changes detected:
    - Files added (in state2 but not state1)
    - Files removed (in state1 but not state2)
    - Files modified (different size or mtime)

    Args:
        state1: Previous folder state
        state2: Current folder state

    Returns:
        bool: True if NO changes (stable), False if changed
    """
    # Check for added or removed files
    files1 = set(state1.keys())
    files2 = set(state2.keys())

    if files1 != files2:
        # Files were added or removed
        return False

    # Check for modified files (same path but different size/mtime)
    for file_path in files1:
        size1, mtime1 = state1[file_path]
        size2, mtime2 = state2[file_path]

        if size1 != size2 or mtime1 != mtime2:
            # File was modified
            return False

    # No changes detected - folder is stable
    return True


def watch_folder_until_stable(
    folder_path: str,
    settle_time_seconds: int = 30,
    max_wait_seconds: int = 3600,
    progress_callback: Optional[Callable[[int, int, Dict], None]] = None
) -> bool:
    """
    Watch folder until stable for settle_time seconds

    **MRC: Core watch function - simple polling loop**

    Algorithm:
    1. Get initial folder state
    2. Wait settle_time seconds
    3. Get new folder state
    4. Compare states
       - If changed: Go back to step 1 (reset timer)
       - If stable: Return True (folder ready)
    5. If max_wait exceeded: Return False (timeout)

    Args:
        folder_path: Path to folder to watch
        settle_time_seconds: Seconds without changes = stable (default: 30)
        max_wait_seconds: Maximum total wait time (default: 3600 = 1 hour)
        progress_callback: Optional callback(elapsed, settle_time, state_dict)

    Returns:
        bool: True if folder became stable, False if timeout

    Raises:
        FolderNotFoundError: If folder doesn't exist
        WatchFolderError: If watching fails
    """
    if not os.path.exists(folder_path):
        raise FolderNotFoundError(f"Folder does not exist: {folder_path}")

    start_time = time.time()
    checks_done = 0

    try:
        # Get initial state
        previous_state = get_folder_state(folder_path)
        last_change_time = start_time

        while True:
            # Check if we would exceed max_wait BEFORE sleeping
            elapsed = int(time.time() - start_time)
            if elapsed + settle_time_seconds > max_wait_seconds:
                # Would timeout after this sleep - return False now
                return False

            # Wait settle_time seconds
            time.sleep(settle_time_seconds)

            # Update elapsed time after sleep
            elapsed = int(time.time() - start_time)
            checks_done += 1

            # Progress callback BEFORE getting state (allows callback to modify folder)
            if progress_callback:
                state_info = {
                    'file_count': len(previous_state),
                    'checks_done': checks_done
                }
                progress_callback(elapsed, settle_time_seconds, state_info)

            # Get current state AFTER callback
            current_state = get_folder_state(folder_path)

            # Compare states
            is_stable = compare_folder_states(previous_state, current_state)

            if is_stable:
                # Folder is stable! No changes in last settle_time seconds
                return True
            else:
                # Folder changed - reset timer
                previous_state = current_state
                last_change_time = time.time()

    except FolderNotFoundError:
        raise
    except Exception as e:
        raise WatchFolderError(f"Watch folder failed: {e}") from e


def get_folder_info(folder_path: str) -> dict:
    """
    Get information about folder being watched

    Args:
        folder_path: Path to folder

    Returns:
        dict: {
            'file_count': int,
            'total_size': int,
            'folder_path': str
        }
    """
    if not os.path.exists(folder_path):
        return {
            'file_count': 0,
            'total_size': 0,
            'folder_path': folder_path
        }

    state = get_folder_state(folder_path)

    file_count = len(state)
    total_size = sum(size for size, mtime in state.values())

    return {
        'file_count': file_count,
        'total_size': total_size,
        'path': folder_path
    }


def format_settle_time(seconds: int) -> str:
    """
    Format settle time in human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "30 seconds", "1 minute", "1.5 minutes")
    """
    if seconds < 60:
        return f"{seconds} seconds"

    minutes = seconds / 60.0
    if minutes == int(minutes):
        minute_word = "minute" if int(minutes) == 1 else "minutes"
        return f"{int(minutes)} {minute_word}"
    else:
        return f"{minutes} minutes"


def estimate_watch_duration(
    current_activity: bool,
    settle_time_seconds: int,
    typical_transfer_time_seconds: int = 60
) -> int:
    """
    Estimate how long watch will take

    Args:
        current_activity: Is folder currently changing?
        settle_time_seconds: Settle time setting
        typical_transfer_time_seconds: Typical time for client transfer

    Returns:
        int: Estimated seconds until stable
    """
    if current_activity:
        # Folder is changing - estimate transfer time + settle time
        return typical_transfer_time_seconds + settle_time_seconds
    else:
        # Folder appears stable - just settle time
        return settle_time_seconds
