import os
import pytest
from fastapi.testclient import TestClient
import requests
from urllib.parse import urlparse

# Ensure the test suite always uses SQLite
os.environ["DATABASE_URL"] = "sqlite:///./test_state.db"
os.environ["PYTEST_FORCE_SQLITE"] = "1"

from app.main import app


class _TestClientSession:
    def __init__(self, *args, **kwargs):
        self._client = TestClient(app)

    def _path(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return path

    def get(self, url: str, timeout=None, **kwargs):
        return self._client.get(self._path(url), **kwargs)

    def post(self, url: str, json=None, timeout=None, **kwargs):
        return self._client.post(self._path(url), json=json, **kwargs)

    def patch(self, url: str, json=None, timeout=None, **kwargs):
        return self._client.patch(self._path(url), json=json, **kwargs)


requests.Session = _TestClientSession


@pytest.fixture
def client():
    """
    FastAPI test client fixture required by integration suites.
    """
    class _TupleClient:
        def __init__(self):
            self._client = TestClient(app)

        def _wrap(self, response):
            try:
                body = response.json()
            except ValueError:
                body = response
            return response.status_code, body

        def get(self, endpoint, **kwargs):
            return self._wrap(self._client.get(endpoint, **kwargs))

        def post(self, endpoint, json=None, **kwargs):
            return self._wrap(self._client.post(endpoint, json=json, **kwargs))

        def patch(self, endpoint, json=None, **kwargs):
            return self._wrap(self._client.patch(endpoint, json=json, **kwargs))

    return _TupleClient()
