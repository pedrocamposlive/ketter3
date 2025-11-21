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
    run_transfer,
)


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

    result = run_transfer(engine_job)

    if result.status.value == "success":
        job.status = JobStatus.SUCCESS.value
        job.files_copied = result.stats.files_copied
        job.bytes_copied = result.stats.bytes_copied
        event_type = "finished"
        message = (
            f"Job finished successfully: "
            f"{result.stats.files_copied} files, {result.stats.bytes_copied} bytes"
        )
    else:
        job.status = JobStatus.FAILED.value
        job.files_copied = None
        job.bytes_copied = None
        event_type = "error"
        message = f"Job failed: {result.error}"

    event = db_models.JobEvent(
        job_id=job.id,
        event_type=event_type,
        message=message,
    )
    db.add(event)
    db.commit()

    log(f"Job {job.id} -> {job.status}")
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
