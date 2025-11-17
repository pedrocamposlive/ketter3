"""
Ketter 3.0 - Volume Configuration Manager

Loads and validates ketter.config.yml
Provides volume information to API and frontend
"""

import os
import platform
import yaml
from typing import List, Dict, Optional
from pathlib import Path


class VolumeConfig:
    """Single volume configuration"""

    def __init__(self, data: dict):
        self.path = data.get('path', '')
        self.alias = data.get('alias', self.path)
        self.type = data.get('type', 'local')
        self.description = data.get('description', '')
        self.check_mounted = data.get('check_mounted', False)
        self.vlan_id = data.get('vlan_id')

    def is_available(self) -> bool:
        """Check if volume path exists and is accessible"""
        if not self.check_mounted:
            return True  # Don't validate if check_mounted=false

        return os.path.exists(self.path) and os.path.isdir(self.path)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            'path': self.path,
            'alias': self.alias,
            'type': self.type,
            'description': self.description,
            'available': self.is_available()
        }


class KetterConfig:
    """Main configuration manager"""

    def __init__(self, config_path: str = 'ketter.config.yml'):
        self.config_path = config_path
        self.server_name = "Unknown"
        self.server_location = ""
        self.volumes: List[VolumeConfig] = []

        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            print(f"Warning: Config file not found: {self.config_path}")
            print("Using default configuration (only /tmp)")
            self._load_defaults()
            return

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Load server info
            server = config.get('server', {})
            self.server_name = server.get('name', 'Unknown')
            self.server_location = server.get('location', '')

            # Load volumes
            volumes_data = config.get('volumes', [])
            self.volumes = [VolumeConfig(vol) for vol in volumes_data]
            self._attach_local_user_paths()

            print(f" Loaded config: {self.server_name} ({len(self.volumes)} volumes)")

        except Exception as e:
            print(f"Error loading config: {e}")
            self._load_defaults()

    def _load_defaults(self):
        """Load default configuration if file not found"""
        self.server_name = "Default"
        self.volumes = [
            VolumeConfig({
                'path': '/tmp',
                'alias': 'Temporary',
                'type': 'local',
                'description': 'Default temporary folder',
                'check_mounted': False
            })
        ]
        self._attach_local_user_paths()

    def _volume_exists(self, target_path: Path) -> bool:
        """Check if a path is already present in configured volumes (case-insensitive)"""
        target_real = os.path.realpath(target_path)
        for volume in self.volumes:
            if os.path.realpath(volume.path) == target_real:
                return True
        return False

    def _attach_local_user_paths(self):
        """
        Allow Desktop/Desktop transfers in development by dynamically adding the current user's workspace.

        Controlled via ALLOW_USER_DESKTOP (default: enabled). Only attaches if the folder exists locally.
        """
        allow_local = os.getenv("ALLOW_USER_DESKTOP", "1")
        if allow_local not in ("1", "true", "TRUE", "yes", "YES"):
            return

        # Only auto attach on developer workstations (macOS/Windows) – servers should configure explicitly
        system_name = platform.system().lower()
        if system_name not in ("darwin", "windows"):
            return

        home = Path.home()
        candidate_paths = [
            ("Desktop", home / "Desktop"),
            ("Documents", home / "Documents"),
            ("Downloads", home / "Downloads"),
        ]

        for alias_suffix, candidate in candidate_paths:
            if not candidate.exists():
                continue
            if self._volume_exists(candidate):
                continue

            volume_alias = f"Local {alias_suffix}"
            self.volumes.append(
                VolumeConfig({
                    "path": str(candidate),
                    "alias": volume_alias,
                    "type": "local",
                    "description": f"Auto-added {alias_suffix} workspace for development transfers",
                    "check_mounted": False
                })
            )

    def get_volumes(self) -> List[Dict]:
        """Get all volumes as dictionaries"""
        return [vol.to_dict() for vol in self.volumes]

    def get_available_volumes(self) -> List[Dict]:
        """Get only available volumes"""
        return [vol.to_dict() for vol in self.volumes if vol.is_available()]

    def validate_path(self, path: str) -> tuple[bool, str]:
        """
        Validate if a path belongs to a configured volume

        Returns:
            (is_valid, error_message)
        """
        # Check if path starts with any configured volume
        for volume in self.volumes:
            if path.startswith(volume.path):
                # Check if volume is available
                if volume.check_mounted and not volume.is_available():
                    return (False, f"Volume '{volume.alias}' is not mounted or accessible")
                return (True, "")

        # Path doesn't match any configured volume
        volume_paths = [v.path for v in self.volumes]
        return (False, f"Path must start with a configured volume: {', '.join(volume_paths)}")

    def get_server_info(self) -> dict:
        """Get server information"""
        return {
            'name': self.server_name,
            'location': self.server_location,
            'volumes_count': len(self.volumes),
            'available_volumes': len([v for v in self.volumes if v.is_available()])
        }


# Global config instance
_config_instance: Optional[KetterConfig] = None


def get_config() -> KetterConfig:
    """Get global configuration instance (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = KetterConfig()
    return _config_instance


def reload_config():
    """Reload configuration from file"""
    global _config_instance
    _config_instance = KetterConfig()
    return _config_instance
