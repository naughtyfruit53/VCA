"""
Mock telephony adapter for local development and testing.

⚠️ WARNING: This is a FAKE adapter for development only.
It does NOT interact with any real telephony systems.
DO NOT use this in production environments.

This adapter:
- Logs all operations to console
- Returns dummy/placeholder results
- Has NO real side effects
- Is useful for local testing without telephony infrastructure
"""

import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from backend.telephony.adapter import TelephonyAdapter
from backend.telephony.types import CallMetadata, CallEvent, CallEventType


logger = logging.getLogger(__name__)


class FakeTelephonyAdapter(TelephonyAdapter):
    """
    Fake telephony adapter for testing and local development.
    
    ⚠️ WARNING: This adapter does NOT connect to real telephony systems.
    All operations are simulated and logged only.
    
    Use this adapter for:
    - Local development without telephony infrastructure
    - Unit testing
    - Integration testing
    
    DO NOT use this adapter in production.
    """
    
    def __init__(self):
        """Initialize the fake adapter."""
        logger.warning(
            "⚠️  FakeTelephonyAdapter initialized - This is a MOCK adapter with NO real telephony functionality!"
        )
        self._registered_numbers: Dict[str, UUID] = {}
    
    async def register_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Fake registration of a phone number.
        
        Logs the operation and stores in-memory only.
        NO real telephony registration occurs.
        """
        logger.info(
            f"[FAKE] Registering number {did_number} for tenant {tenant_id} "
            f"(phone_number_id: {phone_number_id})"
        )
        
        # Store in-memory mapping (ephemeral, lost on restart)
        self._registered_numbers[did_number] = tenant_id
        
        # Return dummy result
        return {
            "status": "success",
            "did_number": did_number,
            "tenant_id": str(tenant_id),
            "phone_number_id": str(phone_number_id),
            "provider": "fake",
            "registered_at": datetime.now().isoformat(),
            "warning": "This is a FAKE registration with no real side effects"
        }
    
    async def unregister_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Fake unregistration of a phone number.
        
        Logs the operation and removes from in-memory storage only.
        NO real telephony unregistration occurs.
        """
        logger.info(
            f"[FAKE] Unregistering number {did_number} for tenant {tenant_id} "
            f"(phone_number_id: {phone_number_id})"
        )
        
        # Remove from in-memory mapping if exists
        if did_number in self._registered_numbers:
            del self._registered_numbers[did_number]
        
        # Return dummy result
        return {
            "status": "success",
            "did_number": did_number,
            "tenant_id": str(tenant_id),
            "phone_number_id": str(phone_number_id),
            "provider": "fake",
            "unregistered_at": datetime.now().isoformat(),
            "warning": "This is a FAKE unregistration with no real side effects"
        }
    
    async def on_inbound_call(
        self,
        call_metadata: CallMetadata
    ) -> CallEvent:
        """
        Fake handling of an inbound call.
        
        Logs the call and returns a dummy CallEvent.
        NO real call handling occurs.
        """
        logger.info(
            f"[FAKE] Inbound call received: {call_metadata.caller_number} -> "
            f"{call_metadata.called_number} (tenant: {call_metadata.tenant_id})"
        )
        
        # Return dummy call event
        return CallEvent(
            event_type=CallEventType.ANSWERED,
            call_metadata=call_metadata,
            timestamp=datetime.now(),
            details="FAKE call answered - no real telephony interaction occurred"
        )


# TODO: Remove FakeTelephonyAdapter when real adapters are implemented
# TODO: Ensure production deployments use real adapter implementations
