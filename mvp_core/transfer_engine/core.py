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

# 8 MiB por chunk – baseline razoável.
_DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024


def run_transfer(job: TransferJob, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> TransferResult:
    """
    Executa a transferência descrita em `job`.

    - Se source for arquivo:
        - destination pode ser arquivo ou diretório.
    - Se source for diretório:
        - faz copy/move recursivo de todo o conteúdo.

    Engine síncrona, single-threaded, usada como baseline.
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
    destination_root = job.destination

    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    # Podemos endurecer isso depois (whitelist de volumes, etc.)
    if source.resolve() == destination_root.resolve():
        raise ValueError("Source and destination must be different paths.")


def _copy(job: TransferJob, stats: TransferStats, chunk_size: int) -> None:
    source = job.source
    raw_destination_root = job.destination

    # Layout unificado: diretórios vão sempre para dest/<basename(source)>
    destination_root = resolve_destination_root(source, raw_destination_root)

    # Semântica de overwrite (modo seguro):
    # - Para diretórios: se dest/<basename(source)> já existir → falha imediata.
    if source.is_dir() and destination_root.exists():
        raise FileExistsError(f"Destination already exists: {destination_root}")

    if source.is_file():
        # Se destino for diretório, copiar mantendo o nome; senão, trata como arquivo.
        if destination_root.is_dir():
            destination_file = destination_root / source.name
        else:
            destination_file = destination_root

        _copy_file(source, destination_file, stats, chunk_size)

    elif source.is_dir():
        # Para diretórios, já usamos destination_root ajustado:
        # dest/<basename(source)>/rel_path
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

    Podemos evoluir para:
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


def resolve_destination_root(source: Path, destination_root: Path) -> Path:
    """
    Define a raiz de destino *lógica* para uma transferência.

    Regras:
    - Se `source` for diretório: sempre usamos dest/<basename(source)>.
    - Se `source` for arquivo: mantemos `dest` como está.

    Essa função existe justamente para unificar o layout de destino
    entre DIRECT (run_transfer) e ZIP_FIRST (que já guarda o basename
    do diretório no arcname do .zip).
    """
    if source.is_dir():
        return destination_root / source.name
    return destination_root
