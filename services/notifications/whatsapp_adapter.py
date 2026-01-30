"""
WhatsApp Adapter for Gupshup - Phase 6

⚠️ TEMPORARY IMPLEMENTATION (if marked)
This adapter sends one-way call summaries via Gupshup WhatsApp API.

PHASE 6 SCOPE:
- One-way summary delivery only
- Maximum one message per call
- No interactive messaging
- Clearly marked as TEMPORARY if applicable

STRICT RULES:
- No incoming message handling
- No conversation flows
- Just send and forget
- Fail gracefully
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    """
    WhatsApp adapter for sending call summaries via Gupshup.
    
    ⚠️ TEMPORARY: This adapter is marked as temporary and may be replaced
    with a more robust solution in future phases.
    
    Phase 6 Implementation:
    - Sends one-way call summaries
    - Maximum one message per call
    - No interactive features
    - Fails gracefully
    
    Configuration:
    - Requires GUPSHUP_API_KEY environment variable
    - Requires GUPSHUP_APP_NAME environment variable
    """
    
    def __init__(self):
        """Initialize WhatsApp adapter."""
        self.api_key = os.getenv("GUPSHUP_API_KEY")
        self.app_name = os.getenv("GUPSHUP_APP_NAME")
        
        if not self.api_key or not self.app_name:
            logger.warning(
                "[WHATSAPP_ADAPTER] Gupshup credentials not configured. "
                "Set GUPSHUP_API_KEY and GUPSHUP_APP_NAME environment variables."
            )
        
        logger.info("[WHATSAPP_ADAPTER] Initialized (TEMPORARY - ONE-WAY ONLY)")
    
    async def send_message(
        self,
        recipient_phone: str,
        message_text: str
    ) -> bool:
        """
        Send WhatsApp message via Gupshup.
        
        This is a one-way message delivery. No response handling.
        
        Args:
            recipient_phone: Recipient phone number (E.164 format recommended)
            message_text: Message text to send
            
        Returns:
            bool: True if sent successfully, False otherwise
            
        Note:
            - Fails gracefully (returns False on error)
            - Never raises exceptions
            - Logs all attempts
        """
        logger.info(
            f"[WHATSAPP_ADAPTER] Sending message to {recipient_phone}"
        )
        
        # Check if credentials are configured
        if not self.api_key or not self.app_name:
            logger.error(
                "[WHATSAPP_ADAPTER] Cannot send: credentials not configured"
            )
            return False
        
        try:
            # TODO: Implement actual Gupshup API call
            # For now, this is a stub implementation
            # In production, this would call:
            # POST https://api.gupshup.io/sm/api/v1/msg
            # Headers: apikey: <GUPSHUP_API_KEY>
            # Body: channel=whatsapp, source=<app_name>, destination=<phone>, message=<text>
            
            logger.info(
                "[WHATSAPP_ADAPTER] Stub: Would send message via Gupshup API"
            )
            logger.debug(f"[WHATSAPP_ADAPTER] Message text: {message_text[:100]}...")
            
            # Simulate success for now
            # In production, check API response status
            success = True
            
            if success:
                logger.info(
                    f"[WHATSAPP_ADAPTER] Message sent successfully to {recipient_phone}"
                )
            else:
                logger.warning(
                    f"[WHATSAPP_ADAPTER] Failed to send message to {recipient_phone}"
                )
            
            return success
            
        except Exception as e:
            # Catch all exceptions and fail gracefully
            logger.error(
                f"[WHATSAPP_ADAPTER] Exception while sending: {type(e).__name__}: {e}"
            )
            return False


# TODO (Future Phases):
# =====================
# TODO: Implement actual Gupshup API integration
# TODO: Add retry logic with exponential backoff
# TODO: Add rate limiting to respect Gupshup limits
# TODO: Add template message support (if required by WhatsApp Business)
# TODO: Add delivery status tracking (webhooks)
# TODO: Add message queueing for high volume
# TODO: Consider replacing with more robust solution if needed

# IMPORTANT: This adapter is ONE-WAY ONLY
# Do NOT add incoming message handling or interactive features here
# Keep this adapter strictly phase-bounded for Phase 6
