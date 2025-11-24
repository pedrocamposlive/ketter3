from datetime import datetime
from typing import List, Optional, Dict

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from mvp_core.db import Base, engine, get_session
from mvp_core.db.models import Job, JobEvent


# Garante que as tabelas existam (MVP, sem migrações Alembic aqui)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ketter 3.0 - MVP Core API")


# ---------------------------------------------------------------------------
# Schemas (Pydantic)
# ---------------------------------------------------------------------------

class JobEventSchema(BaseModel):
    id: int
    job_id: int
    event_type: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True


class JobCreateRequest(BaseModel):
    source_path: str
    destination_path: str
    mode: str  # "copy" ou "move"


class JobSchema(BaseModel):
    id: int
    source_path: str
    destination_path: str
    mode: str
    status: str
    files_copied: Optional[int]
    bytes_copied: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class JobDetailResponse(BaseModel):
    id: int
    source_path: str
    destination_path: str
    mode: str
    status: str
    files_copied: Optional[int]
    bytes_copied: Optional[int]
    created_at: datetime
    updated_at: datetime
    # Observabilidade leve
    duration_seconds: Optional[float] = None
    strategy: Optional[str] = None
    events: List[JobEventSchema]

    class Config:
        orm_mode = True


class JobSummaryItem(BaseModel):
    id: int
    status: str
    created_at: datetime
    files_copied: Optional[int]
    bytes_copied: Optional[int]


class JobsSummaryResponse(BaseModel):
    total: int
    by_status: Dict[str, int]
    last_job: Optional[JobSummaryItem]
    last_success: Optional[JobSummaryItem]
    last_failed: Optional[JobSummaryItem]


class JobHistoryItem(BaseModel):
    id: int
    mode: str
    status: str
    strategy: Optional[str]
    duration_seconds: Optional[float]
    created_at: datetime
    files_copied: Optional[int]
    bytes_copied: Optional[int]


class JobsHistoryResponse(BaseModel):
    jobs: List[JobHistoryItem]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_duration_seconds(job: Job) -> Optional[float]:
    if job.created_at and job.updated_at:
        return (job.updated_at - job.created_at).total_seconds()
    return None


def _extract_strategy_from_events(events: List[JobEvent]) -> Optional[str]:
    """
    Extrai a estratégia a partir do último evento de tipo 'strategy_decision'.

    Mensagens atuais têm formato:
      "strategy=ZIP_FIRST, n_files=2000, total_bytes=..., avg_size=..."

    Se em algum momento o formato mudar, ainda assim tentamos algo razoável.
    """
    strategy_event = None
    for ev in events:
        if ev.event_type == "strategy_decision":
            strategy_event = ev

    if not strategy_event:
        return None

    msg = strategy_event.message or ""
    marker = "strategy="
    if marker in msg:
        part = msg.split(marker, 1)[1]
        return part.split(",", 1)[0].strip()

    # Fallback tosco, mas melhor que nada
    return msg.strip() or None


def _job_to_summary_item(job: Job) -> JobSummaryItem:
    return JobSummaryItem(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        files_copied=job.files_copied,
        bytes_copied=job.bytes_copied,
    )


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "component": "api"}


@app.post("/jobs", response_model=JobSchema)
def create_job(payload: JobCreateRequest, db: Session = Depends(get_session)) -> JobSchema:
    job = Job(
        source_path=payload.source_path,
        destination_path=payload.destination_path,
        mode=payload.mode,
        status="pending",
        files_copied=None,
        bytes_copied=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()  # garante ID para o JobEvent

    event = JobEvent(
        job_id=job.id,
        event_type="created",
        message="Job created via API",
        created_at=datetime.utcnow(),
    )
    db.add(event)

    db.commit()
    db.refresh(job)

    return JobSchema.from_orm(job)


@app.get("/jobs/{job_id}/detail", response_model=JobDetailResponse)
def get_job_detail(job_id: int, db: Session = Depends(get_session)) -> JobDetailResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    events = (
        db.query(JobEvent)
        .filter(JobEvent.job_id == job.id)
        .order_by(JobEvent.created_at.asc())
        .all()
    )

    duration_seconds = _compute_duration_seconds(job)
    strategy = _extract_strategy_from_events(events)

    return JobDetailResponse(
        id=job.id,
        source_path=job.source_path,
        destination_path=job.destination_path,
        mode=job.mode,
        status=job.status,
        files_copied=job.files_copied,
        bytes_copied=job.bytes_copied,
        created_at=job.created_at,
        updated_at=job.updated_at,
        duration_seconds=duration_seconds,
        strategy=strategy,
        events=[JobEventSchema.from_orm(e) for e in events],
    )


@app.get("/stats/jobs-summary", response_model=JobsSummaryResponse)
def jobs_summary(db: Session = Depends(get_session)) -> JobsSummaryResponse:
    total = db.query(func.count(Job.id)).scalar() or 0

    by_status_rows = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )
    by_status: Dict[str, int] = {status: count for status, count in by_status_rows}

    last_job = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .limit(1)
        .one_or_none()
    )

    last_success = (
        db.query(Job)
        .filter(Job.status == "success")
        .order_by(Job.created_at.desc())
        .limit(1)
        .one_or_none()
    )

    last_failed = (
        db.query(Job)
        .filter(Job.status == "failed")
        .order_by(Job.created_at.desc())
        .limit(1)
        .one_or_none()
    )

    return JobsSummaryResponse(
        total=total,
        by_status=by_status,
        last_job=_job_to_summary_item(last_job) if last_job else None,
        last_success=_job_to_summary_item(last_success) if last_success else None,
        last_failed=_job_to_summary_item(last_failed) if last_failed else None,
    )


@app.get("/stats/jobs-history", response_model=JobsHistoryResponse)
def jobs_history(
    limit: int = 20,
    db: Session = Depends(get_session),
) -> JobsHistoryResponse:
    """
    Retorna histórico dos últimos N jobs com:
      - id, mode, status
      - duration_seconds (calculado)
      - strategy (derivada dos eventos)
      - created_at
      - files_copied / bytes_copied

    Útil para calibração de thresholds e observabilidade básica.
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be > 0")

    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .all()
    )

    if not jobs:
        return JobsHistoryResponse(jobs=[])

    job_ids = [j.id for j in jobs]

    events = (
        db.query(JobEvent)
        .filter(JobEvent.job_id.in_(job_ids))
        .order_by(JobEvent.created_at.asc())
        .all()
    )

    events_by_job: Dict[int, List[JobEvent]] = {jid: [] for jid in job_ids}
    for ev in events:
        events_by_job.setdefault(ev.job_id, []).append(ev)

    history_items: List[JobHistoryItem] = []
    for job in jobs:
        evs = events_by_job.get(job.id, [])
        duration_seconds = _compute_duration_seconds(job)
        strategy = _extract_strategy_from_events(evs)

        history_items.append(
            JobHistoryItem(
                id=job.id,
                mode=job.mode,
                status=job.status,
                strategy=strategy,
                duration_seconds=duration_seconds,
                created_at=job.created_at,
                files_copied=job.files_copied,
                bytes_copied=job.bytes_copied,
            )
        )

    return JobsHistoryResponse(jobs=history_items)
