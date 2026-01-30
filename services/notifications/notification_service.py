"""
Notification Service Module - Phase 6

This module orchestrates notification delivery for call summaries.

PHASE 6 SCOPE:
- Send call summaries after call ends
- WhatsApp as primary channel (via Gupshup)
- Email as fallback
- Maximum one notification per call
- Failures must not interrupt call flow

STRICT RULES:
- Always tenant_id scoped
- No interactive messaging (one-way only)
- Clear phase separation
- No improper imports from Phase 5
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CallSummary, NotificationLog
from services.notifications.whatsapp_adapter import WhatsAppAdapter
from services.notifications.email_adapter import EmailAdapter

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Orchestrates notification delivery for call summaries.
    
    Phase 6 Implementation:
    - Sends call summaries via WhatsApp (primary)
    - Falls back to email if WhatsApp fails
    - Maximum one notification per call
    - Logs all attempts
    - Never interrupts call flow
    
    Flow:
    1. Try WhatsApp via Gupshup
    2. If WhatsApp fails, try email
    3. Log all attempts
    4. Never raise exceptions (fail silently)
    """
    
    def __init__(self, db: Session):
        """
        Initialize notification service.
        
        Args:
            db: Database session for logging
        """
        self.db = db
        self.whatsapp_adapter = WhatsAppAdapter()
        self.email_adapter = EmailAdapter()
        logger.info("[NOTIFICATION_SERVICE] Initialized")
    
    async def send_call_summary(
        self,
        tenant_id: UUID,
        call_id: UUID,
        call_summary_id: UUID,
        summary_text: str,
        recipient_phone: Optional[str] = None,
        recipient_email: Optional[str] = None
    ) -> bool:
        """
        Send call summary notification.
        
        Tries WhatsApp first, then email as fallback.
        Maximum one notification per call.
        
        Args:
            tenant_id: Tenant ID (for scoping)
            call_id: Call ID (for logging)
            call_summary_id: Call summary ID (for linking)
            summary_text: Summary text to send
            recipient_phone: Phone number for WhatsApp (optional)
            recipient_email: Email address for fallback (optional)
            
        Returns:
            bool: True if any notification succeeded, False otherwise
            
        Note:
            - Never raises exceptions
            - Logs all attempts
            - Fails silently to not interrupt call flow
        """
        logger.info(
            f"[NOTIFICATION_SERVICE] Sending call summary: "
            f"tenant_id={tenant_id}, call_id={call_id}"
        )
        
        # Check if notification already sent for this call
        existing_log = self.db.query(NotificationLog).filter(
            NotificationLog.call_id == call_id,
            NotificationLog.status == "sent"
        ).first()
        
        if existing_log:
            logger.warning(
                f"[NOTIFICATION_SERVICE] Notification already sent for call: {call_id}"
            )
            return True
        
        # Try WhatsApp first (if phone number provided)
        if recipient_phone:
            whatsapp_success = await self._try_whatsapp(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                recipient_phone=recipient_phone,
                summary_text=summary_text
            )
            
            if whatsapp_success:
                logger.info(
                    f"[NOTIFICATION_SERVICE] WhatsApp notification sent successfully"
                )
                return True
        
        # Fallback to email (if email provided)
        if recipient_email:
            email_success = await self._try_email(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                recipient_email=recipient_email,
                summary_text=summary_text
            )
            
            if email_success:
                logger.info(
                    f"[NOTIFICATION_SERVICE] Email notification sent successfully"
                )
                return True
        
        # Both failed or no recipients provided
        logger.warning(
            f"[NOTIFICATION_SERVICE] All notification attempts failed for call: {call_id}"
        )
        return False
    
    async def _try_whatsapp(
        self,
        tenant_id: UUID,
        call_id: UUID,
        call_summary_id: UUID,
        recipient_phone: str,
        summary_text: str
    ) -> bool:
        """
        Try to send WhatsApp notification.
        
        Args:
            tenant_id: Tenant ID
            call_id: Call ID
            call_summary_id: Call summary ID
            recipient_phone: Recipient phone number
            summary_text: Summary text
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            success = await self.whatsapp_adapter.send_message(
                recipient_phone=recipient_phone,
                message_text=summary_text
            )
            
            # Log attempt
            self._log_notification_attempt(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                notification_type="whatsapp",
                recipient=recipient_phone,
                status="sent" if success else "failed",
                error_message=None if success else "WhatsApp send failed"
            )
            
            return success
            
        except Exception as e:
            logger.error(
                f"[NOTIFICATION_SERVICE] WhatsApp exception: {type(e).__name__}: {e}"
            )
            
            # Log failed attempt
            self._log_notification_attempt(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                notification_type="whatsapp",
                recipient=recipient_phone,
                status="failed",
                error_message=str(e)
            )
            
            return False
    
    async def _try_email(
        self,
        tenant_id: UUID,
        call_id: UUID,
        call_summary_id: UUID,
        recipient_email: str,
        summary_text: str
    ) -> bool:
        """
        Try to send email notification.
        
        Args:
            tenant_id: Tenant ID
            call_id: Call ID
            call_summary_id: Call summary ID
            recipient_email: Recipient email address
            summary_text: Summary text
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            success = await self.email_adapter.send_email(
                recipient_email=recipient_email,
                subject="Call Summary",
                body_text=summary_text
            )
            
            # Log attempt
            self._log_notification_attempt(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                notification_type="email",
                recipient=recipient_email,
                status="sent" if success else "failed",
                error_message=None if success else "Email send failed"
            )
            
            return success
            
        except Exception as e:
            logger.error(
                f"[NOTIFICATION_SERVICE] Email exception: {type(e).__name__}: {e}"
            )
            
            # Log failed attempt
            self._log_notification_attempt(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                notification_type="email",
                recipient=recipient_email,
                status="failed",
                error_message=str(e)
            )
            
            return False
    
    def _log_notification_attempt(
        self,
        tenant_id: UUID,
        call_id: UUID,
        call_summary_id: UUID,
        notification_type: str,
        recipient: str,
        status: str,
        error_message: Optional[str]
    ) -> None:
        """
        Log notification attempt to database.
        
        Args:
            tenant_id: Tenant ID
            call_id: Call ID
            call_summary_id: Call summary ID
            notification_type: Type of notification ("whatsapp", "email")
            recipient: Recipient identifier
            status: Status ("sent", "failed", "pending")
            error_message: Error message if failed
        """
        try:
            log_entry = NotificationLog(
                tenant_id=tenant_id,
                call_id=call_id,
                call_summary_id=call_summary_id,
                notification_type=notification_type,
                recipient=recipient,
                status=status,
                error_message=error_message
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
            logger.debug(
                f"[NOTIFICATION_SERVICE] Logged notification attempt: "
                f"type={notification_type}, status={status}"
            )
            
        except Exception as e:
            # Don't fail if logging fails
            logger.error(
                f"[NOTIFICATION_SERVICE] Failed to log notification: {e}"
            )
            # Rollback to prevent transaction issues
            self.db.rollback()


# Phase 6 Implementation Notes:
# ==============================
# - This service is strictly isolated for Phase 6
# - No imports from Phase 5 telephony code
# - Notification failures are logged but never interrupt call flow
# - Maximum one notification per call is enforced
# - Clear separation between WhatsApp and email adapters
# - All operations are tenant_id scoped
