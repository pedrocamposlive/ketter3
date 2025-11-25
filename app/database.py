import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError


# ----------------------------------------
# Ambiente e resolução da DB_URL
# ----------------------------------------

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Aceita tanto DATABASE_URL quanto DB_URL.
# Prioridade:
#   1) DATABASE_URL
#   2) DB_URL
_raw_env_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

# Estratégia "dev chato":
# - development/dev:
#     usa DB_URL se existir, senão cai em sqlite:///./dev_state.db
# - test/testing:
#     usa DB_URL se existir, senão cai em sqlite:///./test_state.db
# - qualquer outro ambiente (staging, production, homolog, etc.):
#     DB_URL é OBRIGATÓRIA. Sem ela, falha no startup.
if ENVIRONMENT in ("development", "dev"):
    DB_URL = _raw_env_url or "sqlite:///./dev_state.db"
elif ENVIRONMENT in ("test", "testing"):
    DB_URL = _raw_env_url or "sqlite:///./test_state.db"
else:
    if not _raw_env_url:
        raise RuntimeError(
            "DB_URL/DATABASE_URL é obrigatório quando ENVIRONMENT não é "
            "'development' ou 'test'. Defina ENVIRONMENT=development para usar "
            "SQLite local ou configure DB_URL/DATABASE_URL explicitamente para "
            "staging/produção."
        )
    DB_URL = _raw_env_url

print(f"[DB] Using DB_URL={DB_URL}", flush=True)

# Compatibilidade com código existente (ex.: alembic/env.py importa DATABASE_URL)
DATABASE_URL = DB_URL

# Garante que o Alembic (alembic/env.py) veja o mesmo valor via env var.
os.environ.setdefault("DATABASE_URL", DB_URL)


# ----------------------------------------
# Engine / Session / Base
# ----------------------------------------

connect_args = {}
if DB_URL.startswith("sqlite"):
    # Necessário para SQLite + SQLAlchemy em modo multi-thread
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DB_URL,
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


def acquire_transfer_lock(
    db,
    transfer_id: int,
    timeout_seconds: int | None = None,
) -> bool:
    """
    Best-effort lock por transferência.

    Retorno:
        True  -> lock adquirido (ou ignorado com segurança em SQLite)
        False -> lock não adquirido (apenas em Postgres, se implementarmos timeout real)

    Comportamento:
    - Em SQLite (dev/test):
        - No-op, mas retorna sempre True para não quebrar fluxo de MOVE.
    - Em Postgres:
        - Usa pg_advisory_lock(transfer_id).
        - timeout_seconds está na assinatura para futura evolução; hoje
          usamos lock bloqueante simples e retornamos True, deixando o
          controle de erro para exceptions do driver.
    """
    if not _is_postgres():
        # Em dev/test (SQLite) não fazemos nada, mas consideramos lock adquirido.
        return True

    conn = db.connection()

    # Por enquanto, timeout_seconds é ignorado e usamos lock bloqueante.
    # Se quisermos implementar timeout real depois, trocamos por pg_try_advisory_lock
    # em loop com sleep, retornando False em caso de timeout.
    conn.execute(
        text("SELECT pg_advisory_lock(:k)"),
        {"k": int(transfer_id)},
    )
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


# ----------------------------------------
# Test helper: reset_db (para pytest)
# ----------------------------------------

def reset_db() -> None:
    """
    Helper para testes: derruba e recria todas as tabelas
    no banco apontado pelo engine atual.

    Uso:
        - Exclusivo para ambiente de teste (ENVIRONMENT=test/testing).
        - Chamado por fixtures em tests/test_pdf_report_api.py, etc.

    Proteções:
        - Só roda em ENVIRONMENT=test/testing.
        - Só roda se o engine for SQLite.

    NÃO use em produção ou staging.
    """
    from sqlalchemy import inspect

    if ENVIRONMENT not in ("test", "testing"):
        raise RuntimeError(
            f"reset_db() só pode ser utilizado em ambiente de teste. "
            f"ENVIRONMENT atual: {ENVIRONMENT!r}"
        )

    if not str(engine.url).startswith("sqlite"):
        raise RuntimeError("reset_db() só é permitido com SQLite (ambiente de teste).")

    inspector = inspect(engine)

    # Drop all tables se existirem
    if inspector.get_table_names():
        Base.metadata.drop_all(bind=engine)

    # Recria todas as tabelas com base nos models atuais
    Base.metadata.create_all(bind=engine)
