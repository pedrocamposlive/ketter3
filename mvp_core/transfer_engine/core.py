# mvp_core/transfer_engine/core.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable
import datetime as dt

from .models import (
    TransferJob,
    TransferResult,
    TransferStatus,
    TransferStats,
    TransferMode,
)

# 8 MiB por chunk – razoável pra começar.
_DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024


def run_transfer(job: TransferJob, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> TransferResult:
    """
    Executa a transferência descrita em `job`.

    - Se source for arquivo:
        - destination pode ser arquivo ou diretório.
    - Se source for diretório:
        - faz copy/move recursivo de todo o conteúdo.

    Por enquanto é uma engine síncrona, single-threaded, pensada como baseline.
    Depois podemos plugar trio/async e heurística de zip em cima desta interface.
    """
    started_at = dt.datetime.utcnow()
    stats = TransferStats()

    try:
        _validate_paths(job)
        _copy(job, stats, chunk_size=chunk_size)

        if job.mode is TransferMode.MOVE:
            _remove_source(job.source)

        status = TransferStatus.SUCCESS
        error = None
    except Exception as exc:  # noqa: BLE001 – aqui queremos capturar tudo
        status = TransferStatus.FAILED
        error = str(exc)

    finished_at = dt.datetime.utcnow()

    return TransferResult(
        job=job,
        status=status,
        stats=stats,
        error=error,
        started_at=started_at,
        finished_at=finished_at,
    )


def _validate_paths(job: TransferJob) -> None:
    source = job.source
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    # Podemos endurecer isso depois (por ex.: bloquear cópia para dentro do próprio source)
    # ou adicionar whitelist de volumes / roots.
    if source.resolve() == job.destination.resolve():
        raise ValueError("Source and destination must be different paths.")


def _copy(job: TransferJob, stats: TransferStats, chunk_size: int) -> None:
    source = job.source
    destination_root = job.destination

    if source.is_file():
        # Se destino for diretório, copiar mantendo o nome.
        if destination_root.is_dir():
            destination_file = destination_root / source.name
        else:
            destination_file = destination_root

        _copy_file(source, destination_file, stats, chunk_size)
    elif source.is_dir():
        for file_path in _walk_files(source):
            relative = file_path.relative_to(source)
            destination_file = destination_root / relative
            _copy_file(file_path, destination_file, stats, chunk_size)
    else:
        raise ValueError(f"Unsupported source type: {source}")


def _walk_files(root: Path) -> Iterable[Path]:
    """
    Itera sobre todos os arquivos sob `root` de forma recursiva.
    """
    for dirpath, _, filenames in os.walk(root):
        dirpath_path = Path(dirpath)
        for name in filenames:
            yield dirpath_path / name


def _copy_file(
    source: Path,
    destination: Path,
    stats: TransferStats,
    chunk_size: int,
) -> None:
    """
    Cópia de arquivo por streaming, sem usar shutil.

    É intencionalmente simples e síncrono. Podemos evoluir depois para:
    - async com trio/aiofiles,
    - paralelismo por arquivo,
    - checagem de hash, etc.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    size = source.stat().st_size

    with source.open("rb") as fsrc, destination.open("wb") as fdst:
        while True:
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)

    stats.files_copied += 1
    stats.bytes_copied += size


def _remove_source(path: Path) -> None:
    """
    Remove o source após um MOVE, sem usar shutil.rmtree.

    - Para arquivo: unlink.
    - Para diretório: remove recursivamente (pós-ordem).
    """
    if path.is_file() or path.is_symlink():
        try:
            path.unlink(missing_ok=True)
        except TypeError:
            # Python < 3.8 não tem missing_ok, mas estamos em 3.11.
            if path.exists():
                path.unlink()
        return

    if path.is_dir():
        for child in path.iterdir():
            _remove_source(child)
        path.rmdir()

