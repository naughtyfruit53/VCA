"""
Sandbox Simulation API endpoints for Agent Brain v1.

IMPORTANT: This endpoint provides SIMULATED/MOCK responses.
No real LLM calls are made. All responses are clearly marked as simulated.

The sandbox endpoint:
- Simulates language detection (session-based, once per session)
- Simulates language switching detection
- Assembles runtime context from configuration (no LLM call)
- Returns mock responses with session management
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models import Tenant, BusinessProfile
from app.schemas import SandboxSimulateRequest, SandboxSimulateResponse
from app.services import (
    LanguageDetectionService,
    LanguageSwitchDetector,
    RuntimeContextBuilder
)


router = APIRouter(tags=["sandbox"])


# Service instances (in production, these might be dependency-injected)
language_detector = LanguageDetectionService()
language_switcher = LanguageSwitchDetector()
context_builder = RuntimeContextBuilder()


@router.post("/sandbox/simulate", response_model=SandboxSimulateResponse)
async def simulate_agent_response(
    request: SandboxSimulateRequest,
    db: Annotated[Session, Depends(get_db)]
) -> SandboxSimulateResponse:
    """
    Simulate agent response (MOCK - NO REAL AI).
    
    This endpoint simulates an agent response based on configuration but
    DOES NOT call any real LLM or perform actual AI inference.
    
    Session-based behavior:
    - Generates session_id if not provided
    - Detects language once per session (cached)
    - Handles language switch requests
    - Locks speaking_language after explicit switch
    
    Args:
        request: Simulation request with tenant_id, user_text, optional session_id
        db: Database session
        
    Returns:
        SandboxSimulateResponse: SIMULATED response with session info and mock output
        
    Raises:
        HTTPException: 404 if tenant not found
        
    Note:
        This is a SIMULATION endpoint. The simulated_response field always contains:
        "This is a mock response based on assembled prompt. No AI inference performed."
    """
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Fetch tenant
    tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Fetch business profile (optional)
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.tenant_id == request.tenant_id
    ).first()
    
    # Convert business profile to dict for context builder
    business_profile_dict = None
    if business_profile:
        business_profile_dict = {
            "business_name": business_profile.business_name,
            "business_type": business_profile.business_type,
            "services": business_profile.services,
            "service_areas": business_profile.service_areas,
            "business_hours": business_profile.business_hours,
            "booking_enabled": business_profile.booking_enabled,
            "escalation_rules": business_profile.escalation_rules,
            "forbidden_statements": business_profile.forbidden_statements,
        }
    
    # Step 1: Detect language (session-based, cached after first detection)
    detection_result = language_detector.detect_language(
        text=request.user_text,
        session_id=session_id,
        primary_language=tenant.primary_language.value
    )
    detected_language = detection_result["detected_language"]
    
    # Step 2: Check for language switch request
    # Get current speaking language (initially same as detected language)
    current_speaking_language = language_switcher.get_speaking_language(
        session_id=session_id,
        default=detected_language
    )
    
    switch_result = language_switcher.detect_language_switch_request(
        text=request.user_text,
        session_id=session_id,
        current_language=current_speaking_language
    )
    speaking_language = switch_result["speaking_language"]
    
    # Step 3: Build runtime context (NO LLM CALL)
    assembled_context = context_builder.build_context(
        business_profile=business_profile_dict,
        speaking_language=speaking_language,
        user_text=request.user_text
    )
    
    # Step 4: Return SIMULATED response
    # IMPORTANT: This is a MOCK response, not from a real LLM
    simulated_response = "This is a mock response based on assembled prompt. No AI inference performed."
    
    return SandboxSimulateResponse(
        session_id=session_id,
        detected_language=detected_language,
        speaking_language=speaking_language,
        simulated_response=simulated_response
    )
