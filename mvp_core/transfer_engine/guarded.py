from pathlib import Path

from .layout import (
    resolve_destination_layout,
    assert_overwrite_safe,
    DestinationExistsError,
)

# Importa o engine "cru" que já foi validado nos Labs 02–06.
from .engine import (
    run_transfer as engine_run_transfer,
    run_transfer_zip_first as engine_run_transfer_zip_first,
)


def run_transfer_guarded(job):
    """
    Wrapper para o engine DIRECT (sem ZIP).

    - Resolve layout canônico (dest/<basename(source)> para diretórios).
    - Aplica política de overwrite segura (falha se destino já existir).
    - Atualiza job.source_path e job.destination_path.
    - Chama o engine.run_transfer original.
    """
    layout = resolve_destination_layout(
        Path(job.source_path),
        Path(job.destination_path),
    )
    assert_overwrite_safe(layout)

    # Atualiza o job para o layout final
    job.source_path = str(layout.source_path)
    job.destination_path = str(layout.final_root)

    return engine_run_transfer(job)


def run_transfer_zip_first_guarded(plan):
    """
    Wrapper para o engine ZIP_FIRST.

    - Usa o mesmo layout/overwrite do DIRECT.
    - Atualiza o job dentro do plano antes de chamar o engine ZIP_FIRST.
    """
    job = plan.job

    layout = resolve_destination_layout(
        Path(job.source_path),
        Path(job.destination_path),
    )
    assert_overwrite_safe(layout)

    job.source_path = str(layout.source_path)
    job.destination_path = str(layout.final_root)

    return engine_run_transfer_zip_first(plan)
