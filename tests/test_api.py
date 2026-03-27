"""Tests for health check and general API endpoints."""

from fastapi import status


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK


def test_protected_endpoint_without_token(client):
    """Test that protected endpoints require authentication."""
    response = client.get("/api/v1/accounts")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_with_invalid_token(client):
    """Test that invalid token is rejected."""
    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_with_bearer_missing(client):
    """Test that missing Bearer prefix is rejected."""
    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": "invalid_token_here"},
    )
    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_401_UNAUTHORIZED,
    ]
