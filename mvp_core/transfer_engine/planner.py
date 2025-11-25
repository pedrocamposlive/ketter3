from __future__ import annotations
from mvp_core.transfer_engine.models import TransferStats  # noqa

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Iterable

from .models import TransferJob


class TransferStrategy(str, Enum):
    DIRECT = "DIRECT"
    ZIP_FIRST = "ZIP_FIRST"


@dataclass
class TransferPlan:
    job: TransferJob
    strategy: TransferStrategy
    n_files: int
    total_bytes: int

    @property
    def avg_size_bytes(self) -> Optional[float]:
        if self.n_files == 0:
            return None
        return self.total_bytes / self.n_files


def _walk_files(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        dirpath_path = Path(dirpath)
        for name in filenames:
            yield dirpath_path / name


def analyze_source(job: TransferJob) -> tuple[int, int]:
    """
    Calcula número de arquivos e total de bytes do source.
    Para arquivos únicos, n_files=1 e total_bytes = size.
    Para diretórios, faz walk recursivo.
    """
    source = job.source

    if source.is_file():
        return 1, source.stat().st_size

    if source.is_dir():
        n_files = 0
        total_bytes = 0
        for f in _walk_files(source):
            try:
                st = f.stat()
            except FileNotFoundError:
                # Arquivo removido durante o scan – ignora.
                continue
            n_files += 1
            total_bytes += st.st_size
        return n_files, total_bytes

    # Se não for arquivo nem diretório, tratamos como nenhum arquivo.
    return 0, 0


def _get_thresholds() -> tuple[int, int]:
    """
    Lê thresholds das env vars (se existirem) ou usa defaults.
    - N_FILES_ZIP_THRESHOLD (default 1000)
    - AVG_FILE_SIZE_MAX_BYTES (default 4 MiB)
    """
    default_n_files = 1000
    default_avg_size = 4 * 1024 * 1024  # 4 MiB

    n_files_str = os.getenv("KETTER_ZIP_THRESHOLD_FILES")
    avg_size_str = os.getenv("KETTER_ZIP_THRESHOLD_AVG_SIZE_BYTES")

    try:
        n_files_threshold = int(n_files_str) if n_files_str else default_n_files
    except ValueError:
        n_files_threshold = default_n_files

    try:
        avg_size_threshold = int(avg_size_str) if avg_size_str else default_avg_size
    except ValueError:
        avg_size_threshold = default_avg_size

    return n_files_threshold, avg_size_threshold


def decide_strategy(job: TransferJob) -> TransferPlan:
    """
    Decide se usamos DIRECT ou ZIP_FIRST para este job.

    Política v1:
    - Se source não for diretório → DIRECT.
    - Se source for diretório:
        - calcula n_files e total_bytes
        - se n_files > N_FILES_ZIP_THRESHOLD e avg_size < AVG_FILE_SIZE_MAX_BYTES → ZIP_FIRST
        - caso contrário → DIRECT
    """
    source = job.source

    # Arquivo único: sempre DIRECT.
    if source.is_file():
        n_files, total_bytes = 1, source.stat().st_size
        return TransferPlan(
            job=job,
            strategy=TransferStrategy.DIRECT,
            n_files=n_files,
            total_bytes=total_bytes,
        )

    # Diretório ou outro tipo: analisamos.
    n_files, total_bytes = analyze_source(job)
    n_files_threshold, avg_size_threshold = _get_thresholds()

    if n_files == 0:
        # Nada para copiar – mantém DIRECT.
        strategy = TransferStrategy.DIRECT
    else:
        avg_size = total_bytes / n_files
        if n_files > n_files_threshold and avg_size < avg_size_threshold:
            strategy = TransferStrategy.ZIP_FIRST
        else:
            strategy = TransferStrategy.DIRECT

    return TransferPlan(
        job=job,
        strategy=strategy,
        n_files=n_files,
        total_bytes=total_bytes,
    )
