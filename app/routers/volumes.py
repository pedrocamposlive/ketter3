"""
Ketter 3.0 - Volumes API Router

Endpoints for volume management and discovery
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.config import get_config, reload_config

router = APIRouter(prefix="/volumes", tags=["volumes"])


@router.get("")
async def list_volumes():
    """
    Get all configured volumes

    Returns list of volumes with availability status
    """
    config = get_config()
    volumes = config.get_volumes()

    return {
        "server": config.get_server_info(),
        "volumes": volumes
    }


@router.get("/available")
async def list_available_volumes():
    """
    Get only available (mounted) volumes

    Useful for frontend dropdowns - only show usable volumes
    """
    config = get_config()
    volumes = config.get_available_volumes()

    return {
        "server": config.get_server_info(),
        "volumes": volumes
    }


@router.post("/reload")
async def reload_configuration():
    """
    Reload ketter.config.yml

    Useful after editing config file without restarting container
    """
    try:
        config = reload_config()
        return {
            "message": "Configuration reloaded successfully",
            "server": config.get_server_info(),
            "volumes_count": len(config.volumes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")


@router.get("/validate")
async def validate_path(path: str):
    """
    Validate if a path is within configured volumes

    Args:
        path: Full path to validate (e.g., /nexis/ProjectX)

    Returns:
        Validation result with error message if invalid
    """
    config = get_config()
    is_valid, error_message = config.validate_path(path)

    if not is_valid:
        return {
            "valid": False,
            "error": error_message,
            "path": path
        }

    return {
        "valid": True,
        "path": path
    }
