import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base

TESTING = (
    "PYTEST_CURRENT_TEST" in os.environ
    or os.getenv("PYTEST_FORCE_SQLITE") == "1"
)

if TESTING:
    DATABASE_URL = "sqlite:///./test_state.db"
else:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ketter"
    )

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if TESTING else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency that yields a database session and ensures it closes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    """
    Lightweight database health check used by the /status endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def acquire_transfer_lock(db, transfer_id: int, timeout_seconds: int = 30) -> bool:
    """
    Acquire an exclusive MOVEs transfer lock with a PostgreSQL lock timeout.
    """
    if TESTING:
        # SQLite doesn't support row-level locking; assume success for tests.
        return True

    from app.models import Transfer

    try:
        db.execute(text(f"SET lock_timeout = '{timeout_seconds}s'"))
        transfer = (
            db.query(Transfer)
            .with_for_update()
            .filter(Transfer.id == transfer_id)
            .first()
        )

        if not transfer:
            return False

        return True
    except OperationalError:
        return False
    except Exception:
        return False


def release_transfer_lock(db, transfer_id: int) -> None:
    """
    Release logic is noop since Postgres releases row locks at commit/rollback,
    but this helper keeps the API consistent.
    """
    return None


def reset_db():
    """
    Reset the database schema during tests to guarantee a clean slate.
    """
    # Import models to ensure metadata is populated (avoids circular import at module load)
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
