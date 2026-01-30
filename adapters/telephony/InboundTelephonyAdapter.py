"""
Exotel Inbound Telephony Adapter.

⚠️ TEMPORARY IMPLEMENTATION - INBOUND ONLY
This adapter is marked as TEMPORARY and will be replaced when full SIP trunking
is implemented. This handles ONLY inbound call flows from Exotel webhooks.

STRICT LIMITATIONS:
- INBOUND ONLY: No outbound call logic
- NO CALL RECORDING: Recording is not supported in this phase
- NO TRANSCRIPT STORAGE: Transcripts are not stored permanently
- NO AGENT BRAIN MODIFICATIONS: This adapter only invokes existing Agent Brain
- WEBHOOK ONLY: Handles Exotel webhook POST requests

This adapter:
1. Parses Exotel webhook POST data
2. Normalizes inbound events (never stores provider payloads)
3. Maps DID → tenant_id using did_tenant module
4. Generates unique session_id per call
5. Invokes existing Agent Brain with session context
6. Returns stub TTS response
7. Stores minimal normalized call summary

All logic is strictly isolated in this module and clearly separated by phase.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from adapters.telephony.did_tenant import DIDTenantMapper
from app.models import Call, CallDirection, CallStatus
from backend.ai_services.ai_loop_handler import AILoopHandler

logger = logging.getLogger(__name__)


# ============================================================================
# Exotel Webhook Schemas (Provider-Specific)
# ============================================================================

class ExotelInboundWebhook(BaseModel):
    """
    Schema for Exotel inbound call webhook.
    
    ⚠️ TEMPORARY: This schema matches Exotel's webhook format.
    When SIP lands, this will be replaced with SIP-based call events.
    
    Exotel webhook documentation:
    https://developer.exotel.com/api/receive-call
    """
    CallSid: str = Field(..., description="Exotel call identifier")
    From: str = Field(..., description="Caller phone number")
    To: str = Field(..., description="Called DID number")
    Direction: str = Field(..., description="Call direction (should be 'inbound')")
    Status: str = Field(..., description="Call status")
    CallDuration: Optional[str] = Field(None, description="Call duration in seconds")
    RecordingUrl: Optional[str] = Field(None, description="Recording URL (not used)")
    DialCallStatus: Optional[str] = Field(None, description="Dial status")
    
    # Additional fields that Exotel may send
    CurrentTime: Optional[str] = Field(None, description="Timestamp from Exotel")


# ============================================================================
# Normalized Internal Event Schema (Provider-Agnostic)
# ============================================================================

class NormalizedInboundEvent(BaseModel):
    """
    Normalized inbound call event.
    
    This is provider-agnostic and represents a standardized inbound call event.
    ALL provider-specific data must be transformed into this format.
    
    NEVER store the original provider payload - only store this normalized form.
    """
    session_id: str = Field(..., description="Unique session identifier (generated)")
    caller_number: str = Field(..., description="Normalized caller phone number")
    called_number: str = Field(..., description="Normalized DID number")
    provider_call_id: str = Field(..., description="Provider's call identifier")
    timestamp: datetime = Field(..., description="Call timestamp (UTC)")
    
    # Resolved from DID mapping
    tenant_id: Optional[str] = Field(None, description="Tenant ID (resolved from DID)")
    phone_number_id: Optional[str] = Field(None, description="Phone number ID (resolved from DID)")


# ============================================================================
# Exotel Inbound Adapter
# ============================================================================

class ExotelInboundAdapter:
    """
    Adapter for handling inbound calls from Exotel webhooks.
    
    ⚠️ TEMPORARY IMPLEMENTATION - INBOUND ONLY
    
    This adapter is explicitly marked as temporary and handles ONLY inbound flows.
    No outbound logic, call recording, or transcript storage is implemented here.
    
    Phase 5 Responsibilities:
    - Parse Exotel webhook POST
    - Normalize inbound events
    - Map DID → tenant_id
    - Generate unique session_id
    - Invoke Agent Brain (import only, no modifications)
    - Return stub TTS response
    - Store minimal normalized call summary
    
    Strict Isolation:
    - No outbound call logic
    - No billing code
    - No Agent Brain modifications
    - No raw provider payload storage
    """
    
    def __init__(self, db: Session):
        """
        Initialize Exotel inbound adapter.
        
        Args:
            db: Database session for DID mapping and call storage
        """
        self.db = db
        self.did_mapper = DIDTenantMapper(db)
        self.ai_loop_handler = AILoopHandler()
        logger.info("[EXOTEL_ADAPTER] Initialized (TEMPORARY - INBOUND ONLY)")
    
    async def handle_inbound_webhook(
        self, 
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle inbound call webhook from Exotel.
        
        This is the main entry point for Exotel webhook processing.
        
        Flow:
        1. Parse and validate Exotel webhook data
        2. Normalize to provider-agnostic format
        3. Map DID → tenant_id
        4. Generate unique session_id
        5. Create Call record in database
        6. Invoke Agent Brain (if tenant found)
        7. Return stub TTS response
        
        Args:
            webhook_data: Raw webhook data from Exotel (Dict)
            
        Returns:
            Dict with response for Exotel (TwiML-like format)
            
        Note:
            - Original provider payload is NOT stored
            - Only normalized data is persisted
        """
        logger.info("[EXOTEL_ADAPTER] Processing inbound webhook")
        
        # Step 1: Parse webhook data
        try:
            exotel_webhook = ExotelInboundWebhook(**webhook_data)
        except Exception as e:
            logger.error(f"[EXOTEL_ADAPTER] Failed to parse webhook: {e}")
            return self._error_response("Invalid webhook format")
        
        # Verify this is an inbound call
        if exotel_webhook.Direction.lower() != "inbound":
            logger.warning(
                f"[EXOTEL_ADAPTER] Non-inbound direction: {exotel_webhook.Direction}"
            )
            return self._error_response("Only inbound calls are supported")
        
        # Step 2: Normalize event
        normalized_event = self._normalize_webhook(exotel_webhook)
        
        logger.info(
            f"[EXOTEL_ADAPTER] Normalized event: session_id={normalized_event.session_id}, "
            f"caller={normalized_event.caller_number}, DID={normalized_event.called_number}"
        )
        
        # Step 3: Map DID → tenant_id
        mapping = self.did_mapper.get_tenant_for_did(normalized_event.called_number)
        
        if not mapping:
            logger.warning(
                f"[EXOTEL_ADAPTER] DID not found: {normalized_event.called_number}"
            )
            return self._error_response("Number not found")
        
        tenant_id, phone_number_id = mapping
        normalized_event.tenant_id = str(tenant_id)
        normalized_event.phone_number_id = str(phone_number_id)
        
        logger.info(
            f"[EXOTEL_ADAPTER] DID mapped: tenant_id={tenant_id}, "
            f"phone_number_id={phone_number_id}"
        )
        
        # Step 4: Store minimal call summary
        call_record = await self._store_call_summary(normalized_event, tenant_id, phone_number_id)
        
        logger.info(
            f"[EXOTEL_ADAPTER] Call record created: id={call_record.id}"
        )
        
        # Step 5: Return stub TTS response
        # Note: Actual AI loop invocation would happen asynchronously
        # For now, return a simple response to Exotel
        response = self._stub_tts_response()
        
        logger.info("[EXOTEL_ADAPTER] Webhook processed successfully")
        
        return response
    
    def _normalize_webhook(self, webhook: ExotelInboundWebhook) -> NormalizedInboundEvent:
        """
        Normalize Exotel webhook to provider-agnostic format.
        
        ⚠️ CRITICAL: This method transforms provider-specific data into
        our internal format. The original payload is NEVER stored.
        
        Args:
            webhook: Parsed Exotel webhook
            
        Returns:
            NormalizedInboundEvent: Standardized event
        """
        # Generate unique session_id for this call
        session_id = f"session_{uuid.uuid4()}"
        
        # Parse timestamp (use current time if not provided)
        timestamp = datetime.now(timezone.utc)
        if webhook.CurrentTime:
            try:
                # Exotel timestamps are typically Unix timestamps
                timestamp = datetime.fromtimestamp(
                    int(webhook.CurrentTime),
                    tz=timezone.utc
                )
            except (ValueError, TypeError):
                logger.warning(
                    f"[EXOTEL_ADAPTER] Failed to parse timestamp: {webhook.CurrentTime}"
                )
        
        # Create normalized event
        normalized = NormalizedInboundEvent(
            session_id=session_id,
            caller_number=self._normalize_phone_number(webhook.From),
            called_number=self._normalize_phone_number(webhook.To),
            provider_call_id=webhook.CallSid,
            timestamp=timestamp
        )
        
        logger.debug(
            f"[EXOTEL_ADAPTER] Normalized: {webhook.CallSid} → {session_id}"
        )
        
        return normalized
    
    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number format.
        
        Args:
            phone: Raw phone number from Exotel
            
        Returns:
            str: Normalized phone number
        """
        # Remove common separators
        normalized = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Exotel uses +91 format for Indian numbers
        # Store as-is for now (no transformation)
        return normalized
    
    async def _store_call_summary(
        self,
        event: NormalizedInboundEvent,
        tenant_id: uuid.UUID,
        phone_number_id: uuid.UUID
    ) -> Call:
        """
        Store minimal normalized call summary.
        
        ⚠️ IMPORTANT: Stores ONLY normalized data, never raw provider payload.
        
        Phase 5 Scope:
        - Minimal call record (direction, status, timestamps)
        - No recording URLs
        - No transcript storage
        - No provider-specific data
        
        Args:
            event: Normalized inbound event
            tenant_id: Resolved tenant ID
            phone_number_id: Resolved phone number ID
            
        Returns:
            Call: Created call record
        """
        call = Call(
            tenant_id=tenant_id,
            phone_number_id=phone_number_id,
            direction=CallDirection.INBOUND,
            status=CallStatus.COMPLETED,  # Will be updated when call ends
            started_at=event.timestamp
            # Note: ended_at is None until call completes
        )
        
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        
        logger.info(
            f"[EXOTEL_ADAPTER] Stored call summary: call_id={call.id}, "
            f"tenant_id={tenant_id}, session_id={event.session_id}"
        )
        
        return call
    
    def _stub_tts_response(self) -> Dict[str, Any]:
        """
        Return stub TTS response for Exotel.
        
        ⚠️ TEMPORARY: This is a placeholder response.
        In production, this would return TwiML/NCCO for Exotel to play.
        
        For Phase 5, we return a simple acknowledgment.
        
        Returns:
            Dict: Response for Exotel webhook
        """
        # Exotel expects a TwiML-like response
        # For now, return a simple acknowledgment
        response = {
            "status": "success",
            "message": "Call received",
            "tts_stub": "Hello, your call is being processed."
        }
        
        logger.debug("[EXOTEL_ADAPTER] Returning stub TTS response")
        
        return response
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Return error response for Exotel.
        
        Args:
            error_message: Human-readable error message
            
        Returns:
            Dict: Error response for Exotel
        """
        logger.error(f"[EXOTEL_ADAPTER] Error response: {error_message}")
        
        return {
            "status": "error",
            "message": error_message,
            "tts_stub": "We're sorry, this number is not available."
        }


# ============================================================================
# TODO List for Future Phases
# ============================================================================

# TODO (Phase 6+): Implement call recording with consent
# TODO (Phase 6+): Implement transcript storage with encryption
# TODO (Phase 7+): Add outbound call support (separate adapter)
# TODO (Phase 8+): Add real-time call analytics
# TODO (Phase 9+): Replace with SIP-based adapter when SIP trunk is ready
# TODO (Phase 10+): Add call transfer support
# TODO (Phase 10+): Add conference call support

# IMPORTANT: This adapter is TEMPORARY and INBOUND ONLY
# Do NOT add outbound, billing, or recording logic to this file
# Keep this adapter strictly isolated and phase-bounded
