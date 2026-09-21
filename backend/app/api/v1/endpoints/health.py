"""Health Check Endpoint."""

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.core.database import check_database_health
from app.core.logging import get_correlation_id
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health and Dependency Status",
    description="Returns service runtime health, environment details, and database connectivity status.",
)
async def get_health(response: Response) -> HealthResponse:
    db_healthy = await check_database_health()

    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "degraded"
        db_status = "unhealthy"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "healthy"
        db_status = "healthy"

    return HealthResponse(
        status=overall_status,
        service=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        database=db_status,
        version=settings.VERSION,
        correlation_id=get_correlation_id(),
    )
