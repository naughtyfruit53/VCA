"""
DID to Tenant ID mapping module.

⚠️ IMPORTANT: Single source of truth for inbound routing — replaceable when SIP lands.

This module provides the mapping logic from DID (Direct Inward Dialing) numbers
to tenant IDs for routing inbound calls. This is a centralized routing table
that will be replaced when full SIP trunking is implemented.

TEMPORARY IMPLEMENTATION:
- Currently uses database queries to map DIDs to tenants
- When SIP trunking is implemented, this will be replaced with SIP-based routing
- All inbound routing logic should reference this module

STRICT RULES:
- All mappings must be tenant_id scoped
- No outbound routing logic belongs here
- Database is source of truth for DID ownership
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.models import PhoneNumber

logger = logging.getLogger(__name__)


class DIDTenantMapper:
    """
    Maps DID numbers to tenant IDs for inbound call routing.
    
    ⚠️ Single source of truth for inbound routing — replaceable when SIP lands.
    
    This class is the ONLY place where DID→tenant_id resolution should occur
    for inbound calls. All telephony adapters must use this mapper.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the DID tenant mapper.
        
        Args:
            db: Database session for querying phone numbers
        """
        self.db = db
        logger.debug("[DID_MAPPER] Initialized DID tenant mapper")
    
    def get_tenant_for_did(self, did_number: str) -> Optional[tuple[UUID, UUID]]:
        """
        Get tenant_id and phone_number_id for a given DID number.
        
        This is the primary routing method for inbound calls.
        Queries the phone_numbers table to find the tenant owning this DID.
        
        Args:
            did_number: The DID number to look up (e.g., "+15551234567")
            
        Returns:
            Optional[tuple[UUID, UUID]]: (tenant_id, phone_number_id) if found, None otherwise
            
        Note:
            - Only returns active phone numbers (is_active=True)
            - Returns None if DID is not found or is inactive
        """
        logger.info(f"[DID_MAPPER] Looking up tenant for DID: {did_number}")
        
        # Normalize DID number (remove spaces, standardize format)
        normalized_did = self._normalize_did(did_number)
        
        # Query database for phone number
        phone_number = self.db.query(PhoneNumber).filter(
            PhoneNumber.did_number == normalized_did,
            PhoneNumber.is_active == True
        ).first()
        
        if not phone_number:
            logger.warning(f"[DID_MAPPER] DID not found or inactive: {normalized_did}")
            return None
        
        logger.info(
            f"[DID_MAPPER] DID mapped successfully: {normalized_did} → "
            f"tenant_id={phone_number.tenant_id}, phone_number_id={phone_number.id}"
        )
        
        return (phone_number.tenant_id, phone_number.id)
    
    def _normalize_did(self, did_number: str) -> str:
        """
        Normalize DID number format for consistent lookups.
        
        Args:
            did_number: Raw DID number from provider
            
        Returns:
            str: Normalized DID number
            
        Note:
            - Removes spaces and dashes
            - Ensures consistent format for database lookups
            - Does NOT add/remove country codes (stored as-is in DB)
        """
        # Remove common separators
        normalized = did_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        logger.debug(f"[DID_MAPPER] Normalized DID: {did_number} → {normalized}")
        
        return normalized
    
    def validate_tenant_owns_did(self, tenant_id: UUID, did_number: str) -> bool:
        """
        Validate that a tenant owns a specific DID number.
        
        Useful for authorization checks in API endpoints.
        
        Args:
            tenant_id: Tenant ID to validate
            did_number: DID number to check
            
        Returns:
            bool: True if tenant owns this DID, False otherwise
        """
        logger.debug(f"[DID_MAPPER] Validating tenant {tenant_id} owns DID {did_number}")
        
        normalized_did = self._normalize_did(did_number)
        
        phone_number = self.db.query(PhoneNumber).filter(
            PhoneNumber.did_number == normalized_did,
            PhoneNumber.tenant_id == tenant_id,
            PhoneNumber.is_active == True
        ).first()
        
        result = phone_number is not None
        logger.debug(f"[DID_MAPPER] Validation result: {result}")
        
        return result


# TODO: When SIP trunking is implemented:
# TODO: - Replace database lookups with SIP-based routing
# TODO: - Integrate with Asterisk dialplan for real-time routing
# TODO: - Add caching layer for high-volume routing
# TODO: - Add monitoring/metrics for routing performance
# TODO: - Consider Redis cache for hot DIDs
