from dataclasses import dataclass
from pathlib import Path


class DestinationExistsError(Exception):
    """Erro levantado quando a política 'modo seguro' de overwrite é violada."""
    pass


@dataclass
class DestinationLayout:
    """
    Representa o layout lógico de destino para um job de transferência.

    - source_path: caminho real da origem (resolvido).
    - destination_root: path que veio no job (destination_path).
    - final_root: raiz lógica onde o conteúdo será escrito.
      * Se source é diretório: destination_root / basename(source).
      * Se source é arquivo: destination_root.
    - is_source_dir: flag útil para o engine.
    """
    source_path: Path
    destination_root: Path
    final_root: Path
    is_source_dir: bool


def resolve_destination_layout(source_path: Path, destination_path: Path) -> DestinationLayout:
    """
    Aplica a regra canônica de layout para o MVP:

    - Diretório:
        final_root = destination_path / basename(source_path)
    - Arquivo único:
        final_root = destination_path
    """
    source_path = source_path.resolve()
    destination_root = destination_path.resolve()

    is_dir = source_path.is_dir()
    if is_dir:
        final_root = destination_root / source_path.name
    else:
        final_root = destination_root

    return DestinationLayout(
        source_path=source_path,
        destination_root=destination_root,
        final_root=final_root,
        is_source_dir=is_dir,
    )


def assert_overwrite_safe(layout: DestinationLayout) -> None:
    """
    Política de overwrite 'modo seguro' do MVP 3.0:

    - Se source é diretório:
        - Se layout.final_root já existe → ERRO (não toca em nada).
    - Se source é arquivo:
        - Se já existe um arquivo com o mesmo nome em layout.final_root → ERRO.

    A ideia é:
      - Jobs repetidos com o mesmo destino falham rápido.
      - Nenhum comportamento 'mágico' de overwrite silencioso.
    """
    if layout.is_source_dir:
        if layout.final_root.exists():
            raise DestinationExistsError(
                f"Destination already exists for directory job: {layout.final_root}"
            )
    else:
        # Arquivo único: layout.final_root é a pasta onde o arquivo será escrito.
        target_file = layout.final_root / layout.source_path.name
        if target_file.exists():
            raise DestinationExistsError(
                f"Destination file already exists: {target_file}"
            )
