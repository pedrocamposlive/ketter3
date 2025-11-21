# mvp_core/transfer_engine/cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import TransferMode, TransferJob
from .core import run_transfer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ketter 3.0 MVP – Transfer Engine CLI",
    )
    parser.add_argument(
        "source",
        type=str,
        help="Caminho de origem (arquivo ou diretório).",
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Caminho de destino (arquivo ou diretório).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=[m.value for m in TransferMode],
        default=TransferMode.COPY.value,
        help="Modo de transferência: copy (default) ou move.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=8 * 1024 * 1024,
        help="Tamanho do chunk de cópia em bytes (default: 8 MiB).",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    job = TransferJob(
        source=Path(args.source),
        destination=Path(args.destination),
        mode=TransferMode(args.mode),
    )

    result = run_transfer(job, chunk_size=args.chunk_size)

    if result.status.value == "success":
        print(
            f"[OK] {result.job.mode.value.upper()} "
            f"{result.stats.files_copied} arquivos / {result.stats.bytes_copied} bytes",
        )
        print(f"Source: {result.job.source}")
        print(f"Destination: {result.job.destination}")
        return 0

    print("[ERROR] Transfer failed")
    print(f"Job: {result.job}")
    print(f"Error: {result.error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

