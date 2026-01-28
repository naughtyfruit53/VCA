"""
Health check API endpoint.

Provides system health status and configuration validation.
"""

from fastapi import APIRouter, Response
from app.schemas import HealthCheckResponse
from app.config import is_config_valid

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthCheckResponse)
async def health_check(response: Response) -> HealthCheckResponse:
    """
    Health check endpoint.
    
    Returns the health status of the application and validates
    that all required configuration is present.
    
    Returns 503 Service Unavailable if configuration is invalid.
    
    Returns:
        HealthCheckResponse: Health status information
    """
    config_valid = is_config_valid()
    
    if config_valid:
        return HealthCheckResponse(
            status="healthy",
            config_valid=True,
            message="All systems operational"
        )
    else:
        response.status_code = 503
        return HealthCheckResponse(
            status="unhealthy",
            config_valid=False,
            message="Configuration validation failed - required environment variables are missing"
        )
