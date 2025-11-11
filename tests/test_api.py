"""
Ketter 3.0 - API Tests
Testes dos endpoints REST

MRC: TDD desde Day 1
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Transfer, TransferStatus

# Test database (PostgreSQL test database)
# MRC: Usar mesmo PostgreSQL do projeto para testes mais realistas
TEST_DATABASE_URL = "postgresql://ketter:ketter123@postgres:5432/ketter"


@pytest.fixture(scope="function")
def test_db():
    """Usa database de teste (mesmo PostgreSQL)"""
    from app.database import engine, SessionLocal

    # Limpa dados de teste antes de cada teste
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("TRUNCATE TABLE audit_logs, checksums, transfers RESTART IDENTITY CASCADE"))
        conn.commit()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield engine
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Cliente de teste FastAPI"""
    return TestClient(app)


@pytest.fixture
def temp_file():
    """Cria arquivo temporário para testes"""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Test content for file transfer")
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestHealthEndpoints:
    """Testes dos endpoints de health"""

    def test_health_endpoint(self, client):
        """Testa endpoint /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ketter-api"
        assert data["version"] == "3.0.0"

    def test_root_endpoint(self, client):
        """Testa endpoint /"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Ketter 3.0 API"
        assert "docs" in data

    def test_status_endpoint(self, client):
        """Testa endpoint /status"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "operational"
        assert data["version"] == "3.0.0"


class TestTransferCRUD:
    """Testes de CRUD para transfers"""

    def test_create_transfer(self, client, temp_file):
        """Testa POST /transfers"""
        response = client.post(
            "/transfers",
            json={
                "source_path": temp_file,
                "destination_path": "/tmp/dest.txt"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["source_path"] == temp_file
        assert data["destination_path"] == "/tmp/dest.txt"
        assert data["status"] == "pending"
        assert data["file_size"] > 0
        assert data["file_name"] == os.path.basename(temp_file)

    def test_create_transfer_invalid_source(self, client):
        """Testa POST /transfers com source inexistente"""
        response = client.post(
            "/transfers",
            json={
                "source_path": "/nonexistent/file.txt",
                "destination_path": "/tmp/dest.txt"
            }
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_get_transfers_empty(self, client):
        """Testa GET /transfers quando vazio"""
        response = client.get("/transfers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_transfers(self, client, temp_file):
        """Testa GET /transfers com transfers"""
        # Cria 2 transfers
        client.post("/transfers", json={"source_path": temp_file, "destination_path": "/tmp/dest1.txt"})
        client.post("/transfers", json={"source_path": temp_file, "destination_path": "/tmp/dest2.txt"})

        response = client.get("/transfers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_transfer_by_id(self, client, temp_file):
        """Testa GET /transfers/{id}"""
        # Cria transfer
        create_response = client.post(
            "/transfers",
            json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"}
        )
        transfer_id = create_response.json()["id"]

        # Busca por ID
        response = client.get(f"/transfers/{transfer_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transfer_id
        assert data["source_path"] == temp_file

    def test_get_transfer_not_found(self, client):
        """Testa GET /transfers/{id} com ID inexistente"""
        response = client.get("/transfers/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_transfer(self, client, temp_file):
        """Testa DELETE /transfers/{id}"""
        # Cria transfer
        create_response = client.post(
            "/transfers",
            json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"}
        )
        transfer_id = create_response.json()["id"]

        # Deleta
        response = client.delete(f"/transfers/{transfer_id}")
        assert response.status_code == 204

        # Verifica que não existe mais
        get_response = client.get(f"/transfers/{transfer_id}")
        assert get_response.status_code == 404


class TestTransferFilters:
    """Testes de filtros e paginação"""

    def test_filter_by_status(self, client, temp_file):
        """Testa filtro por status"""
        # Cria transfer
        client.post("/transfers", json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"})

        # Busca por status PENDING
        response = client.get("/transfers?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    def test_pagination(self, client, temp_file):
        """Testa paginação"""
        # Cria 5 transfers
        for i in range(5):
            client.post("/transfers", json={"source_path": temp_file, "destination_path": f"/tmp/dest{i}.txt"})

        # Busca com limit=2
        response = client.get("/transfers?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

        # Busca próxima página
        response = client.get("/transfers?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestTransferChecksums:
    """Testes de checksums"""

    def test_get_transfer_checksums_empty(self, client, temp_file):
        """Testa GET /transfers/{id}/checksums quando vazio"""
        # Cria transfer
        create_response = client.post(
            "/transfers",
            json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"}
        )
        transfer_id = create_response.json()["id"]

        # Busca checksums
        response = client.get(f"/transfers/{transfer_id}/checksums")
        assert response.status_code == 200
        data = response.json()
        assert data["transfer_id"] == transfer_id
        assert data["items"] == []


class TestTransferAuditLogs:
    """Testes de audit logs"""

    def test_get_transfer_logs(self, client, temp_file):
        """Testa GET /transfers/{id}/logs"""
        # Cria transfer
        create_response = client.post(
            "/transfers",
            json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"}
        )
        transfer_id = create_response.json()["id"]

        # Busca logs
        response = client.get(f"/transfers/{transfer_id}/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["transfer_id"] == transfer_id
        assert data["total"] >= 2  # transfer_created + job_enqueued
        assert len(data["items"]) >= 2
        assert data["items"][0]["event_type"] == "transfer_created"
        assert "event_metadata" in data["items"][0]

    def test_get_logs_not_found(self, client):
        """Testa GET /transfers/{id}/logs com transfer inexistente"""
        response = client.get("/transfers/999/logs")
        assert response.status_code == 404


class TestTransferHistory:
    """Testes de histórico"""

    def test_get_recent_transfers(self, client, temp_file):
        """Testa GET /history/recent"""
        # Cria transfer
        client.post("/transfers", json={"source_path": temp_file, "destination_path": "/tmp/dest.txt"})

        # Busca histórico
        response = client.get("/transfers/history/recent?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
