"""
Abstract telephony adapter interface.

This module defines the contract for telephony provider integrations.
All concrete implementations MUST follow this interface.

IMPORTANT: This is an INTERFACE-ONLY module. No real telephony logic is implemented here.
All TODOs must be implemented by actual provider integrations (Twilio, Asterisk, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID

from backend.telephony.types import CallMetadata, CallEvent


class TelephonyAdapter(ABC):
    """
    Abstract base class for telephony provider adapters.
    
    All telephony integrations MUST implement this interface.
    Every method MUST enforce tenant isolation.
    
    ⚠️ WARNING: This is an interface-only class with NO implementation.
    Real telephony logic must be added by concrete implementations.
    """
    
    @abstractmethod
    async def register_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Register a phone number with the telephony provider.
        
        This method should configure the telephony system to route incoming calls
        for the specified DID number to this platform for the given tenant.
        
        Args:
            tenant_id: UUID of the tenant owning this number
            phone_number_id: UUID of the phone number record in database
            did_number: The actual phone number (DID) to register
            
        Returns:
            Dict containing registration details (provider-specific)
            
        Raises:
            TelephonyException: If registration fails
            
        TODO: Implement actual telephony provider registration logic
        TODO: Configure SIP trunk, webhook endpoints, or API callbacks
        TODO: Handle provider-specific authentication and authorization
        TODO: Implement error handling for provider failures
        TODO: Add retry logic for transient failures
        """
        pass
    
    @abstractmethod
    async def unregister_number(
        self,
        tenant_id: UUID,
        phone_number_id: UUID,
        did_number: str
    ) -> Dict[str, Any]:
        """
        Unregister a phone number from the telephony provider.
        
        This method should remove call routing configuration for the specified
        DID number from the telephony system.
        
        Args:
            tenant_id: UUID of the tenant owning this number
            phone_number_id: UUID of the phone number record in database
            did_number: The actual phone number (DID) to unregister
            
        Returns:
            Dict containing unregistration details (provider-specific)
            
        Raises:
            TelephonyException: If unregistration fails
            
        TODO: Implement actual telephony provider unregistration logic
        TODO: Remove SIP trunk configuration or API callbacks
        TODO: Handle provider-specific cleanup
        TODO: Implement error handling for provider failures
        TODO: Ensure idempotent behavior (safe to call multiple times)
        """
        pass
    
    @abstractmethod
    async def on_inbound_call(
        self,
        call_metadata: CallMetadata
    ) -> CallEvent:
        """
        Handle an incoming call event from the telephony provider.
        
        This method is called when a new inbound call is received.
        It should initialize call handling and return a CallEvent.
        
        Args:
            call_metadata: Metadata about the incoming call
            
        Returns:
            CallEvent representing the call state
            
        Raises:
            TelephonyException: If call handling fails
            
        TODO: Implement actual inbound call handling logic
        TODO: Validate tenant_id and phone_number_id
        TODO: Initialize call session in Redis
        TODO: Trigger AI conversation flow
        TODO: Handle call routing to AI agent
        TODO: Implement call recording if required
        TODO: Log call start event
        TODO: Handle failures gracefully (busy signal, etc.)
        """
        pass


# TODO: Implement concrete adapters for specific providers:
# TODO: - AsteriskAdapter (for SIP-based telephony)
# TODO: - TwilioAdapter (for Twilio API)
# TODO: - TelnyxAdapter (for Telnyx API)
# TODO: Each adapter must implement all abstract methods above
# TODO: Each adapter must enforce tenant_id isolation
# TODO: Each adapter must handle provider-specific authentication
