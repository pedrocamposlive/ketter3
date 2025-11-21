from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from mvp_core.db import Base, engine, get_session
from mvp_core.db import models as db_models
from mvp_core.app.schemas import (
    JobCreate,
    JobDetail,
    JobEventRead,
    JobRead,
    JobStatus,
)


app = FastAPI(title="Ketter 3.0 MVP Core")


@app.on_event("startup")
def on_startup() -> None:
    # Para o MVP, criamos as tabelas automaticamente.
    # Em produção, depois migramos para Alembic.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "component": "api"}


# ---------------------------------------------------------------------------
# JOBS
# ---------------------------------------------------------------------------


@app.post(
    "/jobs",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_session),
) -> JobRead:
    job = db_models.Job(
        source_path=payload.source_path,
        destination_path=payload.destination_path,
        mode=payload.mode.value,
        status=JobStatus.PENDING.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    event = db_models.JobEvent(
        job_id=job.id,
        event_type="created",
        message="Job created via API",
    )
    db.add(event)
    db.commit()

    return job


@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_session),
) -> JobRead:
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job


@app.get("/jobs", response_model=List[JobRead])
def list_jobs(
    db: Session = Depends(get_session),
    status_filter: JobStatus | None = Query(
        default=None,
        description="Filtrar por status (pending, running, success, failed).",
    ),
) -> List[JobRead]:
    query = db.query(db_models.Job)
    if status_filter is not None:
        query = query.filter(db_models.Job.status == status_filter.value)
    return query.order_by(db_models.Job.created_at.desc()).all()


# ---------------------------------------------------------------------------
# JOB EVENTS / DETAIL
# ---------------------------------------------------------------------------


@app.get(
    "/jobs/{job_id}/events",
    response_model=List[JobEventRead],
)
def list_job_events(
    job_id: int,
    db: Session = Depends(get_session),
) -> List[JobEventRead]:
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job.events


@app.get(
    "/jobs/{job_id}/detail",
    response_model=JobDetail,
)
def get_job_detail(
    job_id: int,
    db: Session = Depends(get_session),
) -> JobDetail:
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    # Pydantic vai montar JobDetail com base no Job + relação events
    return job  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# STATS / OBSERVABILITY BÁSICA
# ---------------------------------------------------------------------------


@app.get("/stats/jobs-summary")
def jobs_summary(
    db: Session = Depends(get_session),
) -> dict:
    total = db.query(db_models.Job).count()
    pending = db.query(db_models.Job).filter(db_models.Job.status == JobStatus.PENDING.value).count()
    running = db.query(db_models.Job).filter(db_models.Job.status == JobStatus.RUNNING.value).count()
    success = db.query(db_models.Job).filter(db_models.Job.status == JobStatus.SUCCESS.value).count()
    failed = db.query(db_models.Job).filter(db_models.Job.status == JobStatus.FAILED.value).count()

    last_job = (
        db.query(db_models.Job)
        .order_by(db_models.Job.created_at.desc())
        .first()
    )
    last_success = (
        db.query(db_models.Job)
        .filter(db_models.Job.status == JobStatus.SUCCESS.value)
        .order_by(db_models.Job.created_at.desc())
        .first()
    )
    last_failed = (
        db.query(db_models.Job)
        .filter(db_models.Job.status == JobStatus.FAILED.value)
        .order_by(db_models.Job.created_at.desc())
        .first()
    )

    def job_snapshot(job: db_models.Job | None) -> dict | None:
        if job is None:
            return None
        return {
            "id": job.id,
            "status": job.status,
            "created_at": job.created_at,
            "files_copied": job.files_copied,
            "bytes_copied": job.bytes_copied,
        }

    return {
        "total": total,
        "by_status": {
            "pending": pending,
            "running": running,
            "success": success,
            "failed": failed,
        },
        "last_job": job_snapshot(last_job),
        "last_success": job_snapshot(last_success),
        "last_failed": job_snapshot(last_failed),
    }
