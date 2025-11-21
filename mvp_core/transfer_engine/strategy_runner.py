from __future__ import annotations

import os
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Tuple, Optional

from mvp_core.transfer_engine import TransferJob, TransferMode, run_transfer
from mvp_core.transfer_engine.planner import TransferPlan, TransferStrategy


def run_plan(plan: TransferPlan) -> Tuple[str, int, int, Optional[str]]:
    """
    Executa um plano de transferência e normaliza o resultado em:
    (status, files_copied, bytes_copied, error)

    status: "success" | "failed"
    """
    if plan.strategy == TransferStrategy.DIRECT:
        result = run_transfer(plan.job)
        return (
            result.status.value,
            result.stats.files_copied,
            result.stats.bytes_copied,
            result.error,
        )

    # Estratégia ZIP_FIRST
    return _run_zip_first(plan)


def _run_zip_first(plan: TransferPlan) -> Tuple[str, int, int, Optional[str]]:
    """
    Implementação da estratégia ZIP_FIRST:

    1. Cria um .zip sem compressão a partir do diretório source.
    2. Transfere o .zip usando o engine normal (run_transfer).
    3. Descompacta o .zip no destino.
    4. Limpa temporários (zip local e remoto).
    5. Para MOVE, remove o diretório source original.

    Retorna (status, files_copied, bytes_copied, error).
    files_copied / bytes_copied são referentes aos ARQUIVOS ORIGINAIS
    (plan.n_files / plan.total_bytes), não ao .zip.
    """
    job: TransferJob = plan.job
    source: Path = job.source
    dest_root: Path = job.destination
    mode: TransferMode = job.mode

    # Se por algum motivo o source não for diretório, degradamos para DIRECT.
    if not source.is_dir():
        result = run_transfer(job)
        return (
            result.status.value,
            result.stats.files_copied,
            result.stats.bytes_copied,
            result.error,
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
        # 1) Criar ZIP sem compressão
        with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
            for dirpath, _, filenames in os.walk(source):
                dirpath_path = Path(dirpath)
                for name in filenames:
                    file_path = dirpath_path / name
                    # Ex: source=/data/src → arcname="src/subdir/file2.txt"
                    rel = file_path.relative_to(source)
                    arcname = Path(source.name) / rel
                    zf.write(file_path, arcname.as_posix())

        # 2) Transferir o ZIP usando o engine normal
        zip_job = TransferJob(
            source=tmp_zip_path,
            destination=dest_zip_path,
            mode=mode,
        )
        zip_result = run_transfer(zip_job)
        if zip_result.status.value != "success":
            return (
                "failed",
                0,
                0,
                f"ZIP_FIRST: zip transfer failed: {zip_result.error}",
            )

        # 3) Descompactar no destino (cria dest_root/source.name/...)
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

        # Limpar zip temporário
        try:
            tmp_zip_path.unlink()
        except FileNotFoundError:
            pass

        # Stats correspondem aos arquivos ORIGINAIS
        return (
            "success",
            plan.n_files,
            plan.total_bytes,
            None,
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

        return (
            "failed",
            0,
            0,
            f"ZIP_FIRST: unexpected error: {exc}",
        )
