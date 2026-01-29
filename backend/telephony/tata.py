"""
Tata SIP Telephony Adapter for VCA Platform.

This module implements the TelephonyAdapter interface for Tata SIP + Asterisk
integration, handling inbound calls with strict tenant isolation.

ARCHITECTURE:
    Tata SIP --> Asterisk --> This Adapter --> VCA Backend --> Database

SECURITY:
    - All operations are tenant-scoped
    - No credentials stored in code
    - Production-safe error handling (no stack traces in responses)
    - Extensive logging at each step for debugging

SCOPE:
    - ✅ Inbound call handling (on_inbound_call)
    - ⚠️ register_number: TODO placeholder only
    - ⚠️ unregister_number: TODO placeholder only
    - ❌ No AI/STT/TTS implementation (future phase)
    - ❌ No outbound calls (future phase)
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.telephony.adapter import TelephonyAdapter
from backend.telephony.types import CallMetadata, CallEvent, CallEventType, CallDirection
from app.models import PhoneNumber, Call, CallStatus as DBCallStatus, CallDirection as DBCallDirection


logger = logging.getLogger(__name__)


class TataTelephonyAdapter(TelephonyAdapter):
    """
    Tata SIP + Asterisk telephony adapter implementation.
    
    This adapter handles inbound calls from Tata SIP trunk via Asterisk,
    implementing strict tenant isolation and production-safe error handling.
    
    IMPORTANT:
    - All calls MUST be associated with a tenant_id
    - DID number resolution is strict (no fallback or guessing)
    - Errors are logged but NEVER expose stack traces to callers
    - All database operations are safe and atomic
    
    Configuration:
        Asterisk must be configured with:
        - pjsip.conf: Tata SIP trunk connection
        - extensions.conf: Dialplan posting to /internal/telephony/inbound
    
    Usage:
        adapter = TataTelephonyAdapter(db_session)
        call_event = await adapter.on_inbound_call(call_metadata)
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the Tata telephony adapter.
        
        Args:
            db_session: SQLAlchemy database session for tenant data access
        """
        self.db = db_session
        logger.info("TataTelephonyAdapter initialized")
    
    async def register_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Register a phone number with Tata SIP service.
        
        ⚠️  TODO: This is a placeholder implementation only.
        Real Tata SIP registration requires:
        1. API credentials from Tata Communications
        2. DID provisioning workflow
        3. SIP trunk configuration updates
        4. Webhook/endpoint registration
        
        For production implementation:
        - Integrate with Tata SIP provisioning API
        - Configure Asterisk pjsip.conf dynamically
        - Update dialplan routing for new DID
        - Store provider-specific metadata in database
        - Implement retry logic for API failures
        - Add rollback on partial failures
        
        Args:
            tenant_id: UUID of the tenant owning this number
            phone_number_id: UUID of the phone number record in database
            did_number: The actual phone number (DID) to register
            
        Returns:
            Dict containing registration status (placeholder)
            
        Raises:
            NotImplementedError: This method is not yet implemented
        """
        logger.warning(
            f"register_number called but NOT IMPLEMENTED: "
            f"tenant_id={tenant_id}, phone_number_id={phone_number_id}, "
            f"did_number={did_number}"
        )
        
        # TODO: Implement actual Tata SIP registration
        # TODO: Call Tata provisioning API
        # TODO: Update Asterisk configuration
        # TODO: Validate trunk connectivity
        # TODO: Store provider metadata
        
        raise NotImplementedError(
            "register_number is not yet implemented for Tata SIP adapter. "
            "Manual DID configuration in Asterisk pjsip.conf is required. "
            "See backend/telephony/asterisk/pjsip.conf for configuration."
        )
    
    async def unregister_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Unregister a phone number from Tata SIP service.
        
        ⚠️  TODO: This is a placeholder implementation only.
        Real Tata SIP unregistration requires:
        1. API credentials from Tata Communications
        2. DID deprovisioning workflow
        3. SIP trunk configuration cleanup
        4. Graceful call termination handling
        
        For production implementation:
        - Integrate with Tata SIP provisioning API
        - Remove DID from Asterisk configuration
        - Clean up dialplan routing
        - Handle active calls gracefully
        - Implement idempotent behavior (safe to call multiple times)
        - Add audit logging for compliance
        
        Args:
            tenant_id: UUID of the tenant owning this number
            phone_number_id: UUID of the phone number record in database
            did_number: The actual phone number (DID) to unregister
            
        Returns:
            Dict containing unregistration status (placeholder)
            
        Raises:
            NotImplementedError: This method is not yet implemented
        """
        logger.warning(
            f"unregister_number called but NOT IMPLEMENTED: "
            f"tenant_id={tenant_id}, phone_number_id={phone_number_id}, "
            f"did_number={did_number}"
        )
        
        # TODO: Implement actual Tata SIP unregistration
        # TODO: Call Tata deprovisioning API
        # TODO: Update Asterisk configuration
        # TODO: Handle active calls on this DID
        # TODO: Clean up provider metadata
        
        raise NotImplementedError(
            "unregister_number is not yet implemented for Tata SIP adapter. "
            "Manual DID removal from Asterisk pjsip.conf is required. "
            "See backend/telephony/asterisk/pjsip.conf for configuration."
        )
    
    async def on_inbound_call(
        self,
        call_metadata: CallMetadata
    ) -> CallEvent:
        """
        Handle an incoming call from Tata SIP via Asterisk.
        
        This is the main entry point for inbound call processing. It:
        1. Validates the call metadata
        2. Resolves the DID to a PhoneNumber record
        3. Extracts the tenant_id from the PhoneNumber
        4. Creates a Call record in the database
        5. Returns a CallEvent for further processing
        
        CRITICAL TENANT ISOLATION:
        - DID resolution is strict: must map to exactly one PhoneNumber
        - No fallback or default tenant
        - No guessing or approximation of tenant_id
        - Fails safely if tenant cannot be determined
        
        PRODUCTION-SAFE ERROR HANDLING:
        - All database errors are caught and logged
        - No stack traces exposed to caller
        - Clear logging at each step for debugging
        - Atomic database operations (auto-rollback on error)
        
        Args:
            call_metadata: Metadata about the incoming call
                - caller_number: Caller's phone number
                - called_number: DID that was called
                - call_id: Asterisk unique call ID
                - timestamp: When call was received
                - tenant_id: IGNORED (will be resolved from DID)
                - phone_number_id: IGNORED (will be resolved from DID)
            
        Returns:
            CallEvent: Event representing the call state (INITIATED, FAILED, etc.)
            
        Raises:
            Exception: Never raises to caller - all errors logged and returned as FAILED events
        
        TODO: Future phases (not in this implementation):
        - Initialize AI conversation loop
        - Start STT/TTS audio streaming
        - Track call state in Redis
        - Trigger webhooks for call events
        """
        logger.info(
            f"[INBOUND CALL] Received call: {call_metadata.caller_number} -> "
            f"{call_metadata.called_number} (call_id: {call_metadata.call_id})"
        )
        
        # Step 1: Resolve DID to PhoneNumber record
        # This is CRITICAL for tenant isolation
        logger.info(f"[INBOUND CALL] Step 1: Resolving DID {call_metadata.called_number}")
        phone_number = await self._resolve_did_to_phone_number(call_metadata.called_number)
        
        if phone_number is None:
            # DID not found in database - this is a configuration error
            logger.error(
                f"[INBOUND CALL] ERROR: DID {call_metadata.called_number} not found in database. "
                f"Call cannot be routed. Caller: {call_metadata.caller_number}, "
                f"Call ID: {call_metadata.call_id}"
            )
            return CallEvent(
                event_type=CallEventType.FAILED,
                call_metadata=call_metadata,
                timestamp=datetime.now(timezone.utc),
                details=f"DID {call_metadata.called_number} not configured in system"
            )
        
        if not phone_number.is_active:
            # DID is inactive - should not receive calls
            logger.warning(
                f"[INBOUND CALL] WARNING: DID {call_metadata.called_number} is inactive. "
                f"Tenant: {phone_number.tenant_id}, Caller: {call_metadata.caller_number}"
            )
            return CallEvent(
                event_type=CallEventType.FAILED,
                call_metadata=call_metadata,
                timestamp=datetime.now(timezone.utc),
                details=f"DID {call_metadata.called_number} is not active"
            )
        
        # Step 2: Extract tenant_id from PhoneNumber
        # This is the tenant isolation boundary
        tenant_id = phone_number.tenant_id
        phone_number_id = phone_number.id
        logger.info(
            f"[INBOUND CALL] Step 2: DID resolved to tenant_id={tenant_id}, "
            f"phone_number_id={phone_number_id}"
        )
        
        # Step 3: Create Call record in database
        # This persists the call for tracking and analytics
        logger.info(f"[INBOUND CALL] Step 3: Creating Call record in database")
        call_record = await self._create_call_record(
            tenant_id=tenant_id,
            phone_number_id=phone_number_id,
            caller_number=call_metadata.caller_number,
            called_number=call_metadata.called_number,
            call_id=call_metadata.call_id
        )
        
        if call_record is None:
            # Database error - call cannot be tracked
            logger.error(
                f"[INBOUND CALL] ERROR: Failed to create Call record. "
                f"Tenant: {tenant_id}, DID: {call_metadata.called_number}, "
                f"Caller: {call_metadata.caller_number}"
            )
            return CallEvent(
                event_type=CallEventType.FAILED,
                call_metadata=call_metadata,
                timestamp=datetime.now(timezone.utc),
                details="Failed to create call record in database"
            )
        
        logger.info(
            f"[INBOUND CALL] Step 4: Call record created with ID={call_record.id}"
        )
        
        # Step 4: Return successful INITIATED event
        # Update call_metadata with resolved tenant and phone number IDs
        resolved_metadata = CallMetadata(
            caller_number=call_metadata.caller_number,
            called_number=call_metadata.called_number,
            direction=CallDirection.INBOUND,
            timestamp=call_metadata.timestamp,
            tenant_id=tenant_id,
            phone_number_id=phone_number_id,
            call_id=call_metadata.call_id
        )
        
        logger.info(
            f"[INBOUND CALL] SUCCESS: Call initiated. "
            f"Call record ID: {call_record.id}, Tenant: {tenant_id}"
        )
        
        # TODO: Next phase - Initialize AI conversation loop
        # TODO: This is where STT/TTS and LLM integration would begin
        # TODO: For now, we just return INITIATED - Asterisk will handle media
        
        return CallEvent(
            event_type=CallEventType.INITIATED,
            call_metadata=resolved_metadata,
            timestamp=datetime.now(timezone.utc),
            details=f"Call initiated successfully. Call record ID: {call_record.id}"
        )
    
    async def _resolve_did_to_phone_number(
        self,
        did_number: str
    ) -> Optional[PhoneNumber]:
        """
        Resolve a DID number to a PhoneNumber database record.
        
        This is a critical tenant isolation function. It MUST:
        - Return exactly one PhoneNumber or None
        - Never fallback to a default tenant
        - Never guess or approximate the tenant
        
        Args:
            did_number: The DID number to resolve (e.g., "+15551234567")
            
        Returns:
            PhoneNumber record if found and unique, None otherwise
        """
        try:
            logger.debug(f"Querying database for DID: {did_number}")
            
            # Query for exact DID match
            stmt = select(PhoneNumber).where(PhoneNumber.did_number == did_number)
            result = self.db.execute(stmt)
            phone_number = result.scalar_one_or_none()
            
            if phone_number:
                logger.debug(
                    f"DID {did_number} resolved to phone_number_id={phone_number.id}, "
                    f"tenant_id={phone_number.tenant_id}"
                )
            else:
                logger.warning(f"DID {did_number} not found in database")
            
            return phone_number
            
        except Exception as e:
            # Database query error - never expose details to caller
            logger.error(
                f"Database error while resolving DID {did_number}: {type(e).__name__}",
                exc_info=True  # Logs full stack trace to logs only
            )
            return None
    
    async def _create_call_record(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        caller_number: str,
        called_number: str,
        call_id: Optional[str]
    ) -> Optional[Call]:
        """
        Create a Call record in the database.
        
        This function safely persists the call to the database with
        proper tenant isolation and error handling.
        
        Args:
            tenant_id: UUID of the tenant
            phone_number_id: UUID of the PhoneNumber record
            caller_number: Caller's phone number
            called_number: Called DID number
            call_id: Optional external call ID from Asterisk
            
        Returns:
            Call record if created successfully, None otherwise
        """
        try:
            logger.debug(
                f"Creating Call record: tenant={tenant_id}, "
                f"phone_number={phone_number_id}, caller={caller_number}"
            )
            
            # Create Call record with proper tenant isolation
            call = Call(
                tenant_id=tenant_id,
                phone_number_id=phone_number_id,
                direction=DBCallDirection.INBOUND,
                status=DBCallStatus.COMPLETED,  # Initial status
                started_at=datetime.now(timezone.utc),
                ended_at=None  # Will be updated when call ends
            )
            
            self.db.add(call)
            self.db.commit()
            self.db.refresh(call)
            
            logger.debug(f"Call record created with ID: {call.id}")
            return call
            
        except Exception as e:
            # Database error - rollback and log
            self.db.rollback()
            logger.error(
                f"Database error while creating Call record for tenant {tenant_id}: "
                f"{type(e).__name__}",
                exc_info=True  # Logs full stack trace to logs only
            )
            return None


# Production deployment notes:
# ============================
# 1. Ensure database session is properly managed (use dependency injection)
# 2. Configure logging to appropriate level (INFO for production, DEBUG for troubleshooting)
# 3. Monitor call failure rates - high failure indicates configuration issues
# 4. Set up alerts for:
#    - Unknown DIDs (configuration drift)
#    - Inactive DIDs receiving calls (routing issue)
#    - Database errors (system health)
# 5. Implement call cleanup job for ended_at updates
# 6. Add metrics collection for call volume per tenant
#
# TODO: Next phase implementation:
# ================================
# 1. Initialize AI conversation loop in on_inbound_call
# 2. Implement call state tracking (Redis)
# 3. Add call recording integration
# 4. Implement call transfer logic
# 5. Add DTMF input handling
# 6. Implement call disposition (completed/failed/transferred)
# 7. Add webhook notifications for call events
# 8. Implement register_number with Tata API
# 9. Implement unregister_number with Tata API
