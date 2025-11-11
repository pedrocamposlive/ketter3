"""
Ketter 3.0 - Pytest Configuration
Fixtures compartilhados entre testes
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Transfer, Checksum, AuditLog

# Database URL para testes (usa banco em memória SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine():
    """
    Cria engine SQLAlchemy para testes
    Usa SQLite in-memory para velocidade
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Cria sessão de banco de dados para testes
    Cada teste roda em transação isolada
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_transfer(db_session):
    """
    Cria uma transferência de exemplo para testes
    """
    transfer = Transfer(
        source_path="/source/test.mp4",
        destination_path="/dest/test.mp4",
        file_size=1024 * 1024 * 100,  # 100 MB
        file_name="test.mp4"
    )
    db_session.add(transfer)
    db_session.commit()
    db_session.refresh(transfer)
    return transfer
