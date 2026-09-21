"""Health Check API Response Schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Structured health check response."""

    status: str = Field(..., description="Overall service status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service identifier name")
    environment: str = Field(..., description="Runtime environment")
    database: str = Field(..., description="Database connectivity status")
    version: str = Field(..., description="Semantic version of the application")
    correlation_id: str = Field(..., description="Request correlation identifier")
