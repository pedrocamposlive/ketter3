from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Portal(Base):
    __tablename__ = "portals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    root_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    jobs = relationship("Job", back_populates="portal")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    portal_id = Column(Integer, ForeignKey("portals.id"), nullable=True)

    source_path = Column(String(2048), nullable=False)
    destination_path = Column(String(2048), nullable=False)

    mode = Column(String(20), nullable=False)   # copy / move
    status = Column(String(20), nullable=False, default="pending")

    # Stats básicos da última execução da engine
    files_copied = Column(Integer, nullable=True)
    bytes_copied = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
        nullable=False,
    )

    portal = relationship("Portal", back_populates="jobs")
    events = relationship(
        "JobEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobEvent.created_at.asc()",
    )


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    event_type = Column(String(50), nullable=False)  # created / started / finished / error
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="events")
