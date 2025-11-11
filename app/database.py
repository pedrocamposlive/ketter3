"""
Ketter 3.0 - Database Connection
SQLAlchemy setup with PostgreSQL
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ketter:ketter123@localhost:5432/ketter"
)

# SQLAlchemy engine with connection pooling
# MRC: Simple, reliable configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # Conexões simultâneas (simples para MVP)
    max_overflow=10,      # Conexões extras sob carga
    pool_timeout=30,      # Timeout de 30s
    pool_recycle=3600,    # Recicla conexões a cada hora
    echo=False,           # Disable SQL logging (use only for debug)
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# Dependency para FastAPI
def get_db():
    """
    Dependency para obter sessão do banco
    Usado em endpoints FastAPI

    Usage:
        @app.get("/transfers")
        def get_transfers(db: Session = Depends(get_db)):
            return db.query(Transfer).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database initialization
def init_db():
    """
    Inicializa o banco de dados
    Cria todas as tabelas definidas nos models

    IMPORTANTE: Em produção, use Alembic migrations
    Este método é apenas para desenvolvimento/testes
    """
    Base.metadata.create_all(bind=engine)


# Database reset (apenas para testes)
def reset_db():
    """
    ATENÇÃO: Dropa todas as tabelas e recria
    Use APENAS em ambiente de testes
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# Health check do database
def check_db_connection() -> bool:
    """
    Verifica se a conexão com o database está funcionando

    Returns:
        bool: True se conectado, False caso contrário
    """
    try:
        # Tenta executar query simples
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
