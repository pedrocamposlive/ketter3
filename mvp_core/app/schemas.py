from __future__ import annotations

import datetime as dt
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class JobMode(str, Enum):
    COPY = "copy"
    MOVE = "move"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class JobCreate(BaseModel):
    source_path: str = Field(..., description="Caminho de origem (arquivo ou pasta).")
    destination_path: str = Field(..., description="Caminho de destino (arquivo ou pasta).")
    mode: JobMode = Field(default=JobMode.COPY)

    @validator("source_path", "destination_path")
    def normalize_paths(cls, v: str) -> str:
        return str(Path(v).expanduser())


class JobRead(BaseModel):
    id: int
    source_path: str
    destination_path: str
    mode: JobMode
    status: JobStatus
    files_copied: Optional[int] = None
    bytes_copied: Optional[int] = None
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        orm_mode = True


class JobEventRead(BaseModel):
    id: int
    job_id: int
    event_type: str
    message: Optional[str]
    created_at: dt.datetime

    class Config:
        orm_mode = True


class JobDetail(JobRead):
    events: List[JobEventRead] = []
