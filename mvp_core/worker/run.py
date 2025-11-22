from __future__ import annotations

import os
import time
from pathlib import Path

from sqlalchemy.orm import Session

from mvp_core.db.database import SessionLocal
from mvp_core.db import models as db_models
from mvp_core.app.schemas import JobStatus
from mvp_core.transfer_engine import (
    TransferJob as EngineJob,
    TransferMode,
)
from mvp_core.transfer_engine.planner import (
    decide_strategy,
)
from mvp_core.transfer_engine.strategy_runner import run_plan


POLL_INTERVAL_SECONDS = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))


def log(msg: str) -> None:
    print(f"[WORKER] {msg}", flush=True)


def process_next_job(db: Session) -> bool:
    """
    Processa o próximo job pendente, se existir.
    Retorna True se processou algum job, False se não havia nada a fazer.
    """
    job: db_models.Job | None = (
        db.query(db_models.Job)
        .filter(db_models.Job.status == JobStatus.PENDING.value)
        .order_by(db_models.Job.created_at.asc())
        .first()
    )

    if job is None:
        return False

    log(f"Pegando job {job.id}: {job.source_path} -> {job.destination_path} ({job.mode})")

    # Marca como RUNNING
    job.status = JobStatus.RUNNING.value
    event = db_models.JobEvent(
        job_id=job.id,
        event_type="started",
        message="Job started by worker",
    )
    db.add(event)
    db.commit()
    db.refresh(job)

    # Mapeia o job do DB para o TransferJob da engine
    engine_job = EngineJob(
        source=Path(job.source_path),
        destination=Path(job.destination_path),
        mode=TransferMode(job.mode),
    )

    # Decisão de estratégia (DIRECT vs ZIP_FIRST)
    plan = decide_strategy(engine_job)

    log(
        "Strategy decision for job "
        f"{job.id}: strategy={plan.strategy.value}, "
        f"n_files={plan.n_files}, total_bytes={plan.total_bytes}, "
        f"avg_size={plan.avg_size_bytes}",
    )

    strategy_event = db_models.JobEvent(
        job_id=job.id,
        event_type="strategy_decision",
        message=(
            f"strategy={plan.strategy.value}, "
            f"n_files={plan.n_files}, total_bytes={plan.total_bytes}, "
            f"avg_size={plan.avg_size_bytes}"
        ),
    )
    db.add(strategy_event)
    db.commit()

    # Executa o plano (DIRECT ou ZIP_FIRST)
    result = run_plan(plan)

    if result.status == "success":
        job.status = JobStatus.SUCCESS.value
        job.files_copied = result.files_copied
        job.bytes_copied = result.bytes_copied

        extra_zip = (
            f", zip_size_bytes={result.zip_size_bytes}"
            if result.zip_size_bytes is not None
            else ""
        )

        event_type = "finished"
        message = (
            f"Job finished successfully: "
            f"{result.files_copied} files, {result.bytes_copied} bytes "
            f"(strategy={plan.strategy.value}{extra_zip})"
        )
    else:
        job.status = JobStatus.FAILED.value
        job.files_copied = None
        job.bytes_copied = None

        event_type = "error"
        message = (
            f"Job failed: {result.error} "
            f"(strategy={plan.strategy.value})"
        )

    event = db_models.JobEvent(
        job_id=job.id,
        event_type=event_type,
        message=message,
    )
    db.add(event)
    db.commit()

    log(f"Job {job.id} -> {job.status} (strategy={plan.strategy.value})")
    return True


def main() -> None:
    log("Worker iniciado.")
    while True:
        try:
            with SessionLocal() as db:
                processed = process_next_job(db)
        except Exception as exc:  # noqa: BLE001
            log(f"Erro inesperado no loop do worker: {exc}")
            processed = False

        if not processed:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
