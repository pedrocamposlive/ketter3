import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError


# ----------------------------------------
# Ambiente e resolução da DATABASE_URL
# ----------------------------------------

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Estratégia "dev chato":
# - development/dev:
#     usa DATABASE_URL se existir, senão cai em sqlite:///./dev_state.db
# - test/testing:
#     usa DATABASE_URL se existir, senão cai em sqlite:///./test_state.db
# - qualquer outro ambiente (staging, production, homolog, etc.):
#     DATABASE_URL é OBRIGATÓRIA. Sem ela, falha no startup.

_env_db_url = os.getenv("DATABASE_URL")

if ENVIRONMENT in ("development", "dev"):
    DATABASE_URL = _env_db_url or "sqlite:///./dev_state.db"
elif ENVIRONMENT in ("test", "testing"):
    DATABASE_URL = _env_db_url or "sqlite:///./test_state.db"
else:
    if not _env_db_url:
        raise RuntimeError(
            "DATABASE_URL is required when ENVIRONMENT is not 'development' or 'test'. "
            "Defina ENVIRONMENT=development para usar SQLite local ou configure DATABASE_URL "
            "explicitamente (Postgres, etc.) para staging/produção."
        )
    DATABASE_URL = _env_db_url

print(f"[DB] Using DATABASE_URL={DATABASE_URL}", flush=True)

# Garante que o Alembic (alembic/env.py) veja o mesmo valor.
os.environ.setdefault("DATABASE_URL", DATABASE_URL)


# ----------------------------------------
# Engine / Session / Base
# ----------------------------------------

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # Necessário para SQLite + SQLAlchemy em modo multi-thread
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


# ----------------------------------------
# Dependency do FastAPI
# ----------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------
# Health-check de conexão
# ----------------------------------------

def check_db_connection() -> None:
    """
    Usado no startup da API para falhar cedo se o DB estiver quebrado.
    Levanta exceção em caso de erro.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB] Connection OK", flush=True)
    except SQLAlchemyError as exc:
        print(f"[DB] Connection error: {exc}", flush=True)
        # Mantém o comportamento esperado pelo FastAPI: falhar o startup.
        raise


# ----------------------------------------
# Locks de transferência (best-effort)
# ----------------------------------------

def _is_postgres() -> bool:
    return str(engine.url).startswith("postgresql")


def acquire_transfer_lock(db, transfer_id: int, timeout_seconds: int = 30) -> bool:
    """
    Best-effort lock por transferência.

    Compatível com o contrato usado em copy_engine:

        lock_acquired = acquire_transfer_lock(db, transfer_id, timeout_seconds=30)

    - Em Postgres: usa pg_advisory_lock(transfer_id) de forma bloqueante.
    - Em SQLite (dev/test): no-op; retorna sempre True.

    Não implementamos timeout real ainda — timeout_seconds é aceito para manter
    a assinatura (e permitir futura evolução), mas atualmente é ignorado.
    """
    if not _is_postgres():
        # Em dev/test (SQLite) não fazemos nada, e seguimos como se o lock
        # tivesse sido obtido. Risco de concorrência real aqui é irrelevante.
        return True

    conn = db.connection()
    conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": int(transfer_id)})
    return True


def release_transfer_lock(db, transfer_id: int) -> None:
    """
    Libera o lock criado em acquire_transfer_lock.

    - Em Postgres: pg_advisory_unlock(transfer_id).
    - Em SQLite: no-op.
    """
    if not _is_postgres():
        return

    conn = db.connection()
    conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": int(transfer_id)})

