import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Ordem de resolução:
# 1) DB_URL (Docker / infra)
# 2) DATABASE_URL (legado)
# 3) Fallback: serviço "postgres" do docker-compose, DB "ketter_mvp"
DB_URL = (
    os.getenv("DB_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg2://ketter_user:ketter_pass@postgres:5432/ketter_mvp"
)

print(f"[DB] Using DB_URL={DB_URL}", flush=True)

engine = create_engine(DB_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
