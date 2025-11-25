from __future__ import annotations

from pathlib import Path
from typing import Optional

from mvp_core.transfer_engine.models import TransferJob, TransferStats
from mvp_core.transfer_engine.layout import (
    resolve_destination_layout,
    assert_overwrite_safe,
    DestinationLayout,
    DestinationExistsError,
)

def run_transfer(job: TransferJob) -> TransferStats:
    """
    Engine DIRECT (sem ZIP).

    Agora:
      - Resolve o layout canônico via layout.resolve_destination_layout().
      - Aplica a política de overwrite segura via assert_overwrite_safe().
      - Usa sempre layout.final_root como raiz de destino.

    IMPORTANTE:
      - Dentro do corpo, substitua qualquer uso antigo de Path(job.source_path)
        por layout.source_path.
      - Substitua Path(job.destination_path) por layout.final_root.
    """
    layout = resolve_destination_layout(
        Path(job.source_path),
        Path(job.destination_path),
    )
    # Política de overwrite do MVP – falha rápido se o destino já existe.
    assert_overwrite_safe(layout)

    source_root = layout.source_path
    dest_root = layout.final_root

    # A partir daqui, mantenha sua lógica atual, apenas usando
    # 'source_root' e 'dest_root' como base.
    #
    # Exemplo típico (adapte para o que você já tem):
    #
    # if layout.is_source_dir:
    #     files_copied, bytes_copied = _copy_tree(source_root, dest_root, job.mode)
    # else:
    #     files_copied, bytes_copied = _copy_single_file(source_root, dest_root, job.mode)
    #
    # return TransferStats(
    #     files_copied=files_copied,
    #     bytes_copied=bytes_copied,
    # )
    ...

def run_transfer_zip_first(plan: TransferPlan) -> TransferStats:
    """
    Engine ZIP_FIRST.

    - Aplica a mesma política de layout/overwrite do DIRECT.
    - Cria um zip temporário a partir de layout.source_path.
    - Transfere esse zip para layout.final_root (ou temp próximo dele).
    - Extrai o zip em layout.final_root.
    - Limpa temporários.

    IMPORTANTE:
      - Nunca ignore layout.final_root.
      - Nunca use job.destination_path cru.
    """
    job = plan.job

    layout = resolve_destination_layout(
        Path(job.source_path),
        Path(job.destination_path),
    )
    # Garante semântica de overwrite antes de criar zip/dirs.
    assert_overwrite_safe(layout)

    source_root = layout.source_path
    dest_root = layout.final_root

    # Abaixo, substitua sua lógica existente de ZIP_FIRST
    # para usar sempre 'source_root' e 'dest_root':
    #
    # 1) zip_path = criar_zip_sem_compressao(source_root, temp_dir)
    # 2) transferir zip_path -> dest_root (pode usar run_transfer() interno,
    #    mas apontando o destino para um subpath temp sob dest_root, se preferir)
    # 3) extrair zip em dest_root
    # 4) remover zip temporário
    # 5) retornar TransferStats correto
    ...
