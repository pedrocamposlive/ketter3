#!/usr/bin/env python
"""
Ketter 3.0 — MVP Worker

Responsabilidades:
- Buscar jobs PENDING no Postgres.
- Marcar como RUNNING.
- Chamar o planner para decidir a estratégia (DIRECT vs ZIP_FIRST).
- Chamar o engine guardado (com overwrite safe).
- Atualizar status/metrics no DB.
- Registrar eventos em job_events.

Este worker é síncrono e simples de propósito para o MVP.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, asc

# DB e modelos do mvp_core
from mvp_core.db import SessionLocal, models

from mvp_core.transfer_engine.planner import (
    decide_strategy,
    TransferStrategy,
    TransferPlan,
)
from mvp_core.transfer_engine.guarded import (
    run_transfer_guarded,
    run_transfer_zip_first_guarded,
)
from mvp_core.transfer_engine.layout import DestinationExistsError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class JobRepository:
    """
    Repositório mínimo para lidar com jobs e job_events.

    Ajuste os nomes de campos caso seus modelos sejam diferentes.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_next_pending_job(self) -> Optional["models.Job"]:
        stmt = (
            select(models.Job)
            .where(models.Job.status == "pending")
            .order_by(asc(models.Job.created_at))
            .limit(1)
        )
        result = self.db.execute(stmt).scalars().first()
        return result

    def add_event(self, job_id: int, kind: str, message: str) -> None:
        event = models.JobEvent(
            job_id=job_id,
            event_type=kind,
            message=message,
        )
        self.db.add(event)
        self.db.flush()

    def save(self, job: "models.Job") -> None:
        self.db.add(job)
        self.db.flush()


def _to_transfer_job(job: "models.Job"):
    """
    Converte o modelo Job do ORM para o DTO esperado pelo engine.
    """
    from mvp_core.transfer_engine.models import TransferJob

    return TransferJob(
        id=job.id,
        source_path=job.source_path,
        destination_path=job.destination_path,
        mode=job.mode,
    )


def _process_job_with_engine(job: "models.Job", job_repo: JobRepository, db: Session) -> None:
    """
    Executa o engine com proteção de overwrite e tratamento de erros.
    """
    transfer_job = _to_transfer_job(job)

    # Planejamento da estratégia
    plan: TransferPlan = decide_strategy(transfer_job)
    job_repo.add_event(
        job.id,
        kind="strategy_decision",
        message=(
            f"strategy={plan.strategy.name}, "
            f"n_files={plan.n_files}, total_bytes={plan.total_bytes}, "
            f"avg_size={plan.avg_size_bytes}"
        ),
    )

    try:
        if plan.strategy is TransferStrategy.DIRECT:
            stats = run_transfer_guarded(transfer_job)
        else:
            stats = run_transfer_zip_first_guarded(plan)

        job.status = "success"
        job.files_copied = stats.files_copied
        job.bytes_copied = stats.bytes_copied

        job_repo.add_event(
            job.id,
            kind="finished",
            message=(
                f"transfer_success: {stats.files_copied} files, "
                f"{stats.bytes_copied} bytes (strategy={plan.strategy.name})"
            ),
        )
        job_repo.save(job)
        db.commit()

    except DestinationExistsError as exc:
        # Overwrite detectado → falha controlada e explicativa
        logger.warning("Job %s failed due to overwrite policy: %s", job.id, exc)
        job.status = "failed"
        job_repo.add_event(
            job.id,
            kind="error",
            message=str(exc),
        )
        job_repo.save(job)
        db.commit()
        # Não re-raise: overwrite é bug de chamada, não de infra.

    except Exception as exc:
        # Erro genérico de I/O ou infra
        logger.exception("Job %s failed due to engine_error", job.id)
        job.status = "failed"
        job_repo.add_event(
            job.id,
            kind="error",
            message=f"engine_error: {exc}",
        )
        job_repo.save(job)
        db.commit()
        # Para o MVP, apenas logamos. Retry estruturado entra depois.


def _take_job_and_mark_running(job_repo: JobRepository, db: Session) -> Optional["models.Job"]:
    job = job_repo.get_next_pending_job()
    if job is None:
        return None

    job.status = "running"
    job_repo.add_event(job.id, kind="started", message="Job started by worker")
    job_repo.save(job)
    db.commit()
    return job


def worker_loop(poll_interval_seconds: float = 1.0) -> None:
    """
    Loop principal do worker.

    - Poll em jobs PENDING.
    - Marca RUNNING.
    - Executa engine guardado.
    """
    logger.info("Ketter worker started (poll_interval=%ss)", poll_interval_seconds)

    while True:
        with get_db() as db:
            repo = JobRepository(db)

            job = _take_job_and_mark_running(repo, db)
            if job is None:
                # Nenhum job pendente, dorme e tenta de novo
                time.sleep(poll_interval_seconds)
                continue

            logger.info(
                "Processing job %s (%s) %s -> %s",
                job.id,
                job.mode,
                job.source_path,
                job.destination_path,
            )

            _process_job_with_engine(job, repo, db)

        # Pequena pausa entre jobs para não saturar logs
        time.sleep(0.1)


def main() -> None:
    worker_loop()


if __name__ == "__main__":
    main()
