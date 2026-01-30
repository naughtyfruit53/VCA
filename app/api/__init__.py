"""API routes package."""

from app.api.health import router as health_router
from app.api.tenant import router as tenant_router
from app.api.phone_number import router as phone_number_router
from app.api.ai_profile import router as ai_profile_router
from app.api.telephony import router as telephony_router
from app.api.agent_config import router as agent_config_router
from app.api.sandbox import router as sandbox_router

__all__ = [
    "health_router",
    "tenant_router",
    "phone_number_router",
    "ai_profile_router",
    "telephony_router",
    "agent_config_router",
    "sandbox_router",
]
