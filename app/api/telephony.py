"""
Internal telephony API endpoints.

⚠️  SECURITY WARNING: These are INTERNAL endpoints only.
Do NOT expose these endpoints to the public internet.
These should only be accessible from:
- localhost (Asterisk on same server)
- Internal network (if Asterisk on separate server)
- VPN/private network only

Production deployment MUST:
1. Restrict access via firewall rules
2. Use authentication headers (TODO)
3. Enable HTTPS for inter-service communication
4. Log all access attempts
5. Rate limit to prevent abuse

This module handles inbound call webhooks from Asterisk, routing
calls to the appropriate tenant based on DID number.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.database import get_db
from backend.telephony.tata import TataTelephonyAdapter
from backend.telephony.types import CallMetadata, CallDirection


logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Schemas
# ============================================================================

class InboundCallRequest(BaseModel):
    """
    Request schema for inbound call webhook from Asterisk.
    
    This matches the JSON payload sent by Asterisk extensions.conf
    via the CURL dialplan function.
    """
    caller_number: str = Field(
        ...,
        description="Caller's phone number (ANI)",
        min_length=1,
        max_length=20,
        examples=["+15551234567", "15551234567"]
    )
    called_number: str = Field(
        ...,
        description="Called DID number (DNIS)",
        min_length=1,
        max_length=20,
        examples=["+15559876543", "15559876543"]
    )
    call_id: str = Field(
        ...,
        description="Unique call identifier from Asterisk (UNIQUEID)",
        min_length=1,
        max_length=100,
        examples=["1706556789.123"]
    )
    timestamp: str = Field(
        ...,
        description="Unix epoch timestamp when call started",
        examples=["1706556789"]
    )


class InboundCallResponse(BaseModel):
    """
    Response schema for inbound call webhook.
    
    This is returned to Asterisk after processing the call.
    """
    status: str = Field(
        ...,
        description="Status of call processing",
        examples=["success", "error"]
    )
    call_record_id: Optional[str] = Field(
        None,
        description="UUID of created Call record (if successful)"
    )
    tenant_id: Optional[str] = Field(
        None,
        description="UUID of tenant owning this call (if successful)"
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Call initiated successfully", "DID not found in system"]
    )


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    prefix="/internal/telephony",
    tags=["internal-telephony"],
    # TODO: Add authentication dependency here in production
    # dependencies=[Depends(verify_internal_auth)]
)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/inbound",
    response_model=InboundCallResponse,
    status_code=status.HTTP_200_OK,
    summary="Inbound Call Webhook",
    description="""
    Internal endpoint for receiving inbound call notifications from Asterisk.
    
    ⚠️  INTERNAL ONLY - Do not expose to public internet.
    
    This endpoint is called by Asterisk extensions.conf when a call arrives
    on the Tata SIP trunk. It resolves the DID to a tenant and creates a
    Call record in the database.
    
    Flow:
    1. Asterisk receives call on Tata SIP trunk
    2. Asterisk dialplan POSTs call metadata to this endpoint
    3. Endpoint resolves DID -> PhoneNumber -> tenant_id
    4. Creates Call record in database
    5. Returns success/error to Asterisk
    6. TODO: Future - initiate AI conversation loop
    
    Security:
    - TODO: Implement authentication header validation
    - TODO: Rate limiting to prevent abuse
    - TODO: IP whitelist for Asterisk server(s)
    """,
)
async def handle_inbound_call(
    request: Request,
    call_data: InboundCallRequest,
    db: Session = Depends(get_db)
) -> InboundCallResponse:
    """
    Handle inbound call webhook from Asterisk.
    
    This is the main entry point for inbound telephony integration.
    
    Args:
        request: FastAPI request object (for logging/auth)
        call_data: Inbound call metadata from Asterisk
        db: Database session dependency
        
    Returns:
        InboundCallResponse: Status and call record details
        
    Raises:
        HTTPException: On unrecoverable errors (400, 500)
    """
    # Log the incoming request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"[INBOUND WEBHOOK] Received call from Asterisk: "
        f"caller={call_data.caller_number}, DID={call_data.called_number}, "
        f"call_id={call_data.call_id}, source_ip={client_ip}"
    )
    
    # TODO: Validate authentication
    # TODO: Check that request is from authorized source (localhost/internal IP)
    # For now, we log a warning
    if client_ip not in ["127.0.0.1", "localhost", "::1"]:
        logger.warning(
            f"[INBOUND WEBHOOK] Call received from non-localhost IP: {client_ip}. "
            f"TODO: Implement authentication/IP whitelist."
        )
    
    # Step 1: Parse and validate timestamp
    logger.info("[INBOUND WEBHOOK] Step 1: Validating call metadata")
    try:
        call_timestamp = datetime.fromtimestamp(
            int(call_data.timestamp),
            tz=timezone.utc
        )
    except (ValueError, OverflowError) as e:
        logger.error(
            f"[INBOUND WEBHOOK] Invalid timestamp: {call_data.timestamp}, "
            f"error: {type(e).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp format"
        )
    
    # Step 2: Create CallMetadata object
    # Note: tenant_id and phone_number_id are not known yet - will be resolved by adapter
    logger.info("[INBOUND WEBHOOK] Step 2: Creating CallMetadata")
    try:
        call_metadata = CallMetadata(
            caller_number=call_data.caller_number,
            called_number=call_data.called_number,
            direction=CallDirection.INBOUND,
            timestamp=call_timestamp,
            call_id=call_data.call_id,
            tenant_id=None,  # Will be resolved by adapter from DID
            phone_number_id=None  # Will be resolved by adapter from DID
        )
    except ValueError as e:
        # CallMetadata validation error
        logger.error(
            f"[INBOUND WEBHOOK] CallMetadata validation error: {type(e).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid call metadata"
        )
    
    # Step 3: Initialize TataTelephonyAdapter
    logger.info("[INBOUND WEBHOOK] Step 3: Initializing TataTelephonyAdapter")
    try:
        adapter = TataTelephonyAdapter(db)
    except Exception as e:
        # Adapter initialization error - should never happen
        logger.error(
            f"[INBOUND WEBHOOK] Failed to initialize adapter: {type(e).__name__}",
            exc_info=True
        )
        # Production-safe error response (no stack trace)
        return InboundCallResponse(
            status="error",
            message="Internal server error during adapter initialization"
        )
    
    # Step 4: Process the inbound call
    logger.info("[INBOUND WEBHOOK] Step 4: Processing inbound call via adapter")
    try:
        call_event = await adapter.on_inbound_call(call_metadata)
    except Exception as e:
        # Unexpected error in adapter - should be caught by adapter itself
        logger.error(
            f"[INBOUND WEBHOOK] Unexpected error in adapter.on_inbound_call: "
            f"{type(e).__name__}",
            exc_info=True
        )
        # Production-safe error response
        return InboundCallResponse(
            status="error",
            message="Internal server error during call processing"
        )
    
    # Step 5: Handle the result from adapter
    logger.info(
        f"[INBOUND WEBHOOK] Step 5: Adapter returned event_type={call_event.event_type}"
    )
    
    if call_event.event_type == "failed":
        # Call processing failed (DID not found, inactive, or DB error)
        logger.warning(
            f"[INBOUND WEBHOOK] Call processing failed: {call_event.details}"
        )
        return InboundCallResponse(
            status="error",
            message=call_event.details or "Call processing failed"
        )
    
    # Success case - call was initiated
    logger.info(
        f"[INBOUND WEBHOOK] SUCCESS: Call initiated. "
        f"Tenant: {call_event.call_metadata.tenant_id}, "
        f"Details: {call_event.details}"
    )
    
    # Extract call_record_id from details if present
    # Details format: "Call initiated successfully. Call record ID: <uuid>"
    call_record_id = None
    if call_event.details and "Call record ID:" in call_event.details:
        try:
            call_record_id = call_event.details.split("Call record ID:")[1].strip()
        except (IndexError, AttributeError):
            pass
    
    return InboundCallResponse(
        status="success",
        call_record_id=call_record_id,
        tenant_id=str(call_event.call_metadata.tenant_id) if call_event.call_metadata.tenant_id else None,
        message="Call initiated successfully"
    )


# TODO: Add authentication dependency
# ====================================
# async def verify_internal_auth(
#     request: Request,
#     authorization: str = Header(None)
# ) -> bool:
#     """
#     Verify that request is from authorized internal service.
#     
#     Production implementation options:
#     1. Shared secret in Authorization header
#     2. mTLS certificate validation
#     3. IP whitelist (basic, not recommended alone)
#     4. Service mesh authentication (Istio, Linkerd)
#     
#     Raises:
#         HTTPException: 401 if authentication fails
#     """
#     # TODO: Implement actual authentication
#     # For now, placeholder that always passes
#     return True


# TODO: Add additional internal endpoints as needed
# ==================================================
# - POST /internal/telephony/call-status - Update call status
# - POST /internal/telephony/call-ended - Mark call as ended
# - POST /internal/telephony/dtmf - Handle DTMF input from caller


# Production deployment checklist:
# =================================
# [ ] Implement verify_internal_auth dependency
# [ ] Configure IP whitelist or firewall rules
# [ ] Enable HTTPS for inter-service communication
# [ ] Set up monitoring/alerts for endpoint failures
# [ ] Configure rate limiting
# [ ] Add request/response logging (excluding sensitive data)
# [ ] Test with actual Asterisk integration
# [ ] Document authentication mechanism for ops team
# [ ] Add health check endpoint for monitoring
