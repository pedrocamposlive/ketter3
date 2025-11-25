from __future__ import annotations

import os
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import TransferJob, TransferMode
from .planner import TransferPlan, TransferStrategy
from .core import run_transfer, resolve_destination_root


@dataclass
class ExecutionResult:
    status: str                 # "success" | "failed"
    files_copied: int
    bytes_copied: int
    error: Optional[str] = None
    zip_size_bytes: Optional[int] = None


def run_plan(plan: TransferPlan) -> ExecutionResult:
    """
    Executa um plano de transferência (DIRECT ou ZIP_FIRST).
    """
    if plan.strategy == TransferStrategy.DIRECT:
        return _run_direct(plan)

    return _run_zip_first(plan)


def _run_direct(plan: TransferPlan) -> ExecutionResult:
    """
    Execução simples usando a engine padrão (DIRECT).
    """
    result = run_transfer(plan.job)
    return ExecutionResult(
        status=result.status.value,
        files_copied=result.stats.files_copied,
        bytes_copied=result.stats.bytes_copied,
        error=result.error,
        zip_size_bytes=None,
    )


def _run_zip_first(plan: TransferPlan) -> ExecutionResult:
    """
    Estratégia ZIP_FIRST:

    1. Cria um .zip sem compressão a partir do diretório source.
    2. Transfere o .zip usando run_transfer().
    3. Descompacta o .zip no destino.
    4. Remove o .zip no destino.
    5. Se modo MOVE, remove o diretório source original.
    6. Limpa o .zip temporário local.

    Stats (files_copied / bytes_copied) são sempre dos ARQUIVOS ORIGINAIS
    (plan.n_files / plan.total_bytes), não do .zip.
    """
    job: TransferJob = plan.job
    source: Path = job.source
    dest_root: Path = job.destination
    mode: TransferMode = job.mode

    # Degradação de segurança:
    # se o source não for diretório, cai para DIRECT.
    if not source.is_dir():
        return _run_direct(plan)

    # Semântica de overwrite (modo seguro) para diretórios:
    # usamos a mesma lógica de destino da engine (dest/<basename(source)>).
    dest_dir = resolve_destination_root(source, dest_root)
    if dest_dir.exists():
        return ExecutionResult(
            status="failed",
            files_copied=0,
            bytes_copied=0,
            error=f"Destination already exists: {dest_dir}",
            zip_size_bytes=None,
        )

    # Proteção: relações perigosas entre source e destination
    try:
        source_resolved = source.resolve()
        dest_resolved = dest_root.resolve()
    except FileNotFoundError:
        return ExecutionResult(
            status="failed",
            files_copied=0,
            bytes_copied=0,
            error="ZIP_FIRST: source or destination path does not exist",
            zip_size_bytes=None,
        )

    # 1) destination == source
    if dest_resolved == source_resolved:
        return ExecutionResult(
            status="failed",
            files_copied=0,
            bytes_copied=0,
            error="ZIP_FIRST: unsafe configuration (destination == source)",
            zip_size_bytes=None,
        )

    # 2) destination dentro de source (ou vice-versa)
    if dest_resolved.is_relative_to(source_resolved) or source_resolved.is_relative_to(dest_resolved):
        return ExecutionResult(
            status="failed",
            files_copied=0,
            bytes_copied=0,
            error="ZIP_FIRST: unsafe configuration (one path contains the other)",
            zip_size_bytes=None,
        )

    tmp_root = Path(os.getenv("KETTER_TMP_DIR", "/tmp/ketter_tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)

    base_name = f"{source.name}.zip"
    tmp_zip_path = tmp_root / base_name
    if tmp_zip_path.exists():
        tmp_zip_path = tmp_root / f"{source.name}_{uuid.uuid4().hex}.zip"

    dest_root.mkdir(parents=True, exist_ok=True)
    dest_zip_path = dest_root / tmp_zip_path.name

    try:
        # 1) Criar ZIP sem compressão (usando nome base do diretório)
        with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
            for dirpath, _, filenames in os.walk(source):
                dirpath_path = Path(dirpath)
                for name in filenames:
                    file_path = dirpath_path / name
                    rel = file_path.relative_to(source)
                    arcname = Path(source.name) / rel
                    zf.write(file_path, arcname.as_posix())

        zip_size_bytes = tmp_zip_path.stat().st_size

        # 2) Transferir o ZIP usando o engine normal
        zip_job = TransferJob(
            source=tmp_zip_path,
            destination=dest_zip_path,
            mode=mode,
        )
        zip_result = run_transfer(zip_job)
        if zip_result.status.value != "success":
            return ExecutionResult(
                status="failed",
                files_copied=0,
                bytes_copied=0,
                error=f"ZIP_FIRST: zip transfer failed: {zip_result.error}",
                zip_size_bytes=zip_size_bytes,
            )

        # 3) Descompactar no destino
        with zipfile.ZipFile(dest_zip_path, "r") as zf:
            zf.extractall(dest_root)

        # 4) Limpar zip no destino
        try:
            dest_zip_path.unlink()
        except FileNotFoundError:
            pass

        # 5) Se MOVE, remover o diretório original
        if mode == TransferMode.MOVE and source.exists():
            shutil.rmtree(source)

        # 6) Limpar zip temporário local
        try:
            tmp_zip_path.unlink()
        except FileNotFoundError:
            pass

        return ExecutionResult(
            status="success",
            files_copied=plan.n_files,
            bytes_copied=plan.total_bytes,
            error=None,
            zip_size_bytes=zip_size_bytes,
        )

    except Exception as exc:  # noqa: BLE001
        # Tenta limpar temporários, mas não deixa isso quebrar o erro principal.
        try:
            if dest_zip_path.exists():
                dest_zip_path.unlink()
        except Exception:
            pass
        try:
            if tmp_zip_path.exists():
                tmp_zip_path.unlink()
        except Exception:
            pass

        return ExecutionResult(
            status="failed",
            files_copied=0,
            bytes_copied=0,
            error=f"ZIP_FIRST: unexpected error: {exc}",
            zip_size_bytes=None,
        )
