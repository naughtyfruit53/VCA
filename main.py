"""
Main FastAPI application entry point.

IMPORTANT MULTI-TENANT NOTICE:
================================================================================
All future features MUST be added behind tenant_id boundaries.
No global data access is permitted.
================================================================================

This application implements strict SaaS multi-tenancy where every resource
is scoped to a specific tenant. All database queries, API endpoints, and
business logic must enforce tenant isolation.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys

from app.config import settings, is_config_valid
from app.api import health_router, tenant_router, phone_number_router, ai_profile_router, telephony_router


# Validate configuration on startup
if not is_config_valid():
    print("FATAL: Required configuration is missing. Application cannot start.", file=sys.stderr)
    sys.exit(1)


# Create FastAPI application
app = FastAPI(
    title="VCA - Voice AI Agent Platform",
    description=(
        "Multi-tenant Voice AI platform for small and medium businesses. "
        "All resources are strictly isolated by tenant_id."
    ),
    version="0.1.0",
    debug=settings.debug,
)


# Register routers
app.include_router(health_router)
app.include_router(tenant_router, prefix="/api")
app.include_router(phone_number_router, prefix="/api")
app.include_router(ai_profile_router, prefix="/api")
app.include_router(telephony_router)


@app.get("/")
async def root():
    """
    Root endpoint - API information.
    
    Returns:
        dict: API metadata
    """
    return {
        "name": "VCA API",
        "version": "0.1.0",
        "status": "operational",
        "multi_tenant": True,
        "message": "Voice AI Agent Platform - All resources are tenant-scoped"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
        
    Returns:
        JSONResponse: Error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred"
        }
    )


# TODO: Add tenant management endpoints (MUST enforce tenant_id isolation)
# TODO: - POST /api/tenants - Create new tenant
# TODO: - GET /api/tenants/{tenant_id} - Get tenant details
# TODO: - PATCH /api/tenants/{tenant_id} - Update tenant
# TODO: - DELETE /api/tenants/{tenant_id} - Soft delete tenant

# TODO: Add phone number management endpoints (MUST enforce tenant_id isolation)
# TODO: - POST /api/tenants/{tenant_id}/phone-numbers - Add phone number to tenant
# TODO: - GET /api/tenants/{tenant_id}/phone-numbers - List tenant's phone numbers
# TODO: - GET /api/phone-numbers/{id} - Get phone number (validate tenant_id)
# TODO: - PATCH /api/phone-numbers/{id} - Update phone number (validate tenant_id)
# TODO: - DELETE /api/phone-numbers/{id} - Remove phone number (validate tenant_id)

# TODO: Add call management endpoints (MUST enforce tenant_id isolation)
# TODO: - GET /api/tenants/{tenant_id}/calls - List tenant's calls
# TODO: - GET /api/calls/{id} - Get call details (validate tenant_id)
# TODO: - POST /api/calls/{id}/status - Update call status (validate tenant_id)

# TODO: Add AI profile management endpoints (MUST enforce tenant_id isolation)
# TODO: - POST /api/tenants/{tenant_id}/ai-profiles - Create AI profile
# TODO: - GET /api/tenants/{tenant_id}/ai-profiles - List tenant's AI profiles
# TODO: - GET /api/ai-profiles/{id} - Get AI profile (validate tenant_id)
# TODO: - PATCH /api/ai-profiles/{id} - Update AI profile (validate tenant_id)
# TODO: - DELETE /api/ai-profiles/{id} - Delete AI profile (validate tenant_id)

# TODO: Add telephony integration (NO implementation yet - just placeholders)
# TODO: - Webhook endpoint for incoming SIP calls (MUST map DID -> tenant_id)
# TODO: - Call control API (MUST enforce tenant_id)
# TODO: - Real-time call status updates (MUST enforce tenant_id)

# TODO: Add AI/LLM integration (NO implementation yet - just placeholders)
# TODO: - STT service integration (tenant-scoped)
# TODO: - LLM service integration (tenant-scoped, use tenant's AI profile)
# TODO: - TTS service integration (tenant-scoped)

# TODO: Add analytics endpoints (MUST enforce tenant_id isolation)
# TODO: - GET /api/tenants/{tenant_id}/analytics/calls - Call analytics
# TODO: - GET /api/tenants/{tenant_id}/analytics/usage - Usage metrics
# TODO: - GET /api/tenants/{tenant_id}/analytics/performance - Performance metrics

# TODO: Add billing endpoints (MUST enforce tenant_id isolation)
# TODO: - GET /api/tenants/{tenant_id}/billing/current - Current billing period
# TODO: - GET /api/tenants/{tenant_id}/billing/history - Billing history
# TODO: - POST /api/tenants/{tenant_id}/billing/update-plan - Update subscription plan

# TODO: Add webhook configuration (MUST enforce tenant_id isolation)
# TODO: - POST /api/tenants/{tenant_id}/webhooks - Register webhook
# TODO: - GET /api/tenants/{tenant_id}/webhooks - List webhooks
# TODO: - DELETE /api/webhooks/{id} - Remove webhook (validate tenant_id)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
