# mvp_core/transfer_engine/models.py
from __future__ import annotations


import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class TransferMode(str, Enum):
    COPY = "copy"
    MOVE = "move"


class TransferStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TransferJob:
    """
    Representa um job de transferência entre dois caminhos de filesystem.

    Este nível NÃO sabe nada de DB, HTTP, Redis etc.
    É intencionalmente simples para ser usado tanto pelo worker quanto por um CLI.
    """
    source: Path
    destination: Path
    mode: TransferMode = TransferMode.COPY
    created_at: dt.datetime = field(default_factory=dt.datetime.utcnow)


@dataclass
class TransferStats:
    """
    Estatísticas simples de transferência.
    No futuro podemos adicionar tempo por arquivo, taxa média, etc.
    """
    files_copied: int = 0
    bytes_copied: int = 0


@dataclass
class TransferResult:
    """
    Resultado de um job de transferência.
    """
    job: TransferJob
    status: TransferStatus
    stats: TransferStats
    error: Optional[str] = None
    started_at: dt.datetime = field(default_factory=dt.datetime.utcnow)
    finished_at: Optional[dt.datetime] = None
