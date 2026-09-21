"""Integration Tests for Health Check API."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient):
    """Verify health endpoint returns 200 with complete system metadata when healthy."""
    with patch("app.api.v1.endpoints.health.check_database_health", return_value=True):
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert data["service"] == "SE IntelliPlatform"
    assert data["environment"] == "testing"
    assert "version" in data
    assert "correlation_id" in data
    assert response.headers.get("X-Correlation-ID") == data["correlation_id"]


@pytest.mark.asyncio
async def test_health_check_echoes_incoming_correlation_id(client: AsyncClient):
    """Verify that an incoming X-Correlation-ID header is propagated through the response."""
    custom_cid = "custom-test-cid-999"
    with patch("app.api.v1.endpoints.health.check_database_health", return_value=True):
        response = await client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": custom_cid},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["correlation_id"] == custom_cid
    assert response.headers.get("X-Correlation-ID") == custom_cid


@pytest.mark.asyncio
async def test_health_check_degraded_when_database_down(client: AsyncClient):
    """Verify health endpoint returns 503 Service Unavailable when database fails."""
    with patch("app.api.v1.endpoints.health.check_database_health", return_value=False):
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unhealthy"
