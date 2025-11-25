import shutil
from datetime import datetime
from pathlib import Path

import pytest

from mvp_core.transfer_engine.planner import decide_strategy, TransferStrategy
from mvp_core.transfer_engine.layout import (
    resolve_destination_layout,
    assert_overwrite_safe,
    DestinationExistsError,
)

DEV_DATA_ROOT = Path("dev_data")


class SimpleJob:
    """
    Job mínimo só para testar planner + layout.

    Requisitos atendidos:
    - .source: Path
    - .destination: Path
    - .mode: "copy" | "move"
    - .created_at: datetime
    """

    def __init__(self, source: Path, destination: Path, mode: str = "copy"):
        self.source = source if isinstance(source, Path) else Path(source)
        self.destination = destination if isinstance(destination, Path) else Path(destination)
        self.mode = mode
        self.created_at = datetime.utcnow()


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file())


def _make_simple_job(src: Path, dst: Path, mode: str = "copy") -> SimpleJob:
    return SimpleJob(source=src, destination=dst, mode=mode)


# --------------------------------------------------------------------------------------
# ZIP_FIRST — equivalente aos jobs 26 / 27 (2000 arquivos pequenos)
# --------------------------------------------------------------------------------------


def test_overwrite_zip_first_many_small_files_layout_semantics():
    """
    Cenário equivalente aos jobs 26/27, mas testando a SEMÂNTICA de overwrite
    no nível de layout/assert_overwrite_safe:

    - src_overwrite_zip_01 com 2000 arquivos pequenos → strategy=ZIP_FIRST
    - 1ª "execução": final_root ainda não existe → assert_overwrite_safe OK
    - Simulamos criação do destino (copy bem-sucedido)
    - 2ª "execução": final_root já existe → DestinationExistsError
    """
    src = DEV_DATA_ROOT / "src_overwrite_zip_01"
    dst = DEV_DATA_ROOT / "dst_overwrite_zip_01"

    # Reset dataset
    _reset_dir(src)
    if dst.exists():
        shutil.rmtree(dst)

    # Cria 2000 arquivos pequenos (~1 KiB), como no lab
    for i in range(2000):
        p = src / f"file_{i:04d}.txt"
        p.write_text(f"arquivo {i}\n" + "x" * 1024)

    job = _make_simple_job(src, dst, mode="copy")

    # Planner deve escolher ZIP_FIRST para esse perfil
    plan = decide_strategy(job)
    assert plan.strategy == TransferStrategy.ZIP_FIRST

    # 1) Antes da "primeira execução": destino ainda não existe → OK
    layout1 = resolve_destination_layout(src, dst)
    assert not layout1.final_root.exists()
    assert_overwrite_safe(layout1)  # não deve levantar

    # Simula que a engine realmente copiou os arquivos para final_root
    shutil.copytree(src, layout1.final_root)
    assert layout1.final_root.exists()
    assert _count_files(layout1.final_root) == 2000

    # 2) Segunda "execução": mesmo source/dest → deve falhar na checagem de overwrite
    layout2 = resolve_destination_layout(src, dst)
    assert layout2.final_root == layout1.final_root
    assert layout2.final_root.exists()

    with pytest.raises(DestinationExistsError):
        assert_overwrite_safe(layout2)


# --------------------------------------------------------------------------------------
# DIRECT — equivalente aos jobs 31 / 32 (10 arquivos pequenos)
# --------------------------------------------------------------------------------------


def test_overwrite_direct_small_dir_layout_semantics():
    """
    Cenário equivalente aos jobs 31/32, focando na mesma regra de overwrite:

    - src_overwrite_direct_01 com 10 arquivos pequenos → strategy=DIRECT
    - 1ª "execução": final_root ainda não existe → assert_overwrite_safe OK
    - Simulamos criação do destino
    - 2ª "execução": final_root já existe → DestinationExistsError
    """
    src = DEV_DATA_ROOT / "src_overwrite_direct_01"
    dst = DEV_DATA_ROOT / "dst_overwrite_direct_01"

    # Reset dataset
    _reset_dir(src)
    if dst.exists():
        shutil.rmtree(dst)

    # Cria 10 arquivos pequenos (~1 KiB) para forçar DIRECT (< threshold de ZIP_FIRST)
    for i in range(10):
        p = src / f"file_{i:04d}.txt"
        p.write_text(f"arquivo {i}\n" + "x" * 1024)

    job = _make_simple_job(src, dst, mode="copy")

    # Planner deve escolher DIRECT aqui
    plan = decide_strategy(job)
    assert plan.strategy == TransferStrategy.DIRECT

    # 1) Antes da "primeira execução": destino ainda não existe → OK
    layout1 = resolve_destination_layout(src, dst)
    assert not layout1.final_root.exists()
    assert_overwrite_safe(layout1)

    # Simula que a engine copiou arquivos para final_root
    shutil.copytree(src, layout1.final_root)
    assert layout1.final_root.exists()
    assert _count_files(layout1.final_root) == 10

    # 2) Segunda "execução": mesmo source/dest → deve falhar
    layout2 = resolve_destination_layout(src, dst)
    assert layout2.final_root == layout1.final_root
    assert layout2.final_root.exists()

    with pytest.raises(DestinationExistsError):
        assert_overwrite_safe(layout2)
