"""
Ketter 3.0 - CORS Security Tests
ENHANCE #5: CORS restrito validation

Tests verify that CORS is properly configured with whitelist-only origins
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_cors_authorized_origin_localhost_3000():
    """
    Test CORS with authorized origin (localhost:3000)
    Should return access-control-allow-origin header with the origin
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_authorized_origin_localhost_8000():
    """
    Test CORS with authorized origin (localhost:8000)
    Should return access-control-allow-origin header with the origin
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_cors_unauthorized_origin_blocked():
    """
    Test CORS with UNAUTHORIZED origin (malicious-site.com)
    Should return 400 Bad Request with "Disallowed CORS origin"
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"
    # Should NOT have access-control-allow-origin for unauthorized origin
    assert "access-control-allow-origin" not in response.headers or \
           response.headers.get("access-control-allow-origin") != "http://malicious-site.com"


def test_cors_unauthorized_origin_random_domain():
    """
    Test CORS with random unauthorized domain
    Should block any non-whitelisted origin
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"


def test_cors_methods_restricted():
    """
    Test that only specific HTTP methods are allowed
    Should only allow: GET, POST, PUT, DELETE, PATCH
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-methods" in response.headers

    allowed_methods = response.headers["access-control-allow-methods"]
    # Should contain our explicit methods
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods
    assert "PUT" in allowed_methods
    assert "DELETE" in allowed_methods
    assert "PATCH" in allowed_methods


def test_cors_headers_restricted():
    """
    Test that only specific headers are allowed
    Should allow: Content-Type, Authorization
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-headers" in response.headers

    allowed_headers = response.headers["access-control-allow-headers"].lower()
    # Should contain our explicit headers
    assert "content-type" in allowed_headers
    assert "authorization" in allowed_headers


def test_cors_credentials_enabled():
    """
    Test that credentials (cookies, auth) are allowed
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_no_wildcard():
    """
    SECURITY TEST: Ensure wildcard (*) is NOT in allowed origins
    This would be a critical security vulnerability
    """
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    # Should never return * as allowed origin
    assert response.headers.get("access-control-allow-origin") != "*"


if __name__ == "__main__":
    # Run with: pytest tests/test_cors_security.py -v
    pytest.main([__file__, "-v", "-s"])
