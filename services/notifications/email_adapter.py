"""
Email Adapter - Phase 6

Fallback email adapter for sending call summaries when WhatsApp fails.

PHASE 6 SCOPE:
- Fallback notification channel
- Simple text email
- No HTML templates (optional in future)
- Fail gracefully

STRICT RULES:
- Only used when WhatsApp fails
- Never interrupt call flow
- Log all attempts
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailAdapter:
    """
    Email adapter for sending call summaries as fallback.
    
    Phase 6 Implementation:
    - Fallback when WhatsApp fails
    - Simple text emails
    - Fails gracefully
    
    Configuration:
    - Requires SMTP_HOST, SMTP_PORT environment variables
    - Requires SMTP_USERNAME, SMTP_PASSWORD for authentication
    - Requires SMTP_FROM_EMAIL for sender address
    """
    
    def __init__(self):
        """Initialize email adapter."""
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@vca.example.com")
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning(
                "[EMAIL_ADAPTER] SMTP credentials not configured. "
                "Set SMTP_USERNAME and SMTP_PASSWORD environment variables."
            )
        
        logger.info("[EMAIL_ADAPTER] Initialized (FALLBACK)")
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Send email.
        
        Args:
            recipient_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
            
        Returns:
            bool: True if sent successfully, False otherwise
            
        Note:
            - Fails gracefully (returns False on error)
            - Never raises exceptions
            - Logs all attempts
        """
        logger.info(
            f"[EMAIL_ADAPTER] Sending email to {recipient_email}"
        )
        
        # Check if credentials are configured
        if not self.smtp_username or not self.smtp_password:
            logger.error(
                "[EMAIL_ADAPTER] Cannot send: SMTP credentials not configured"
            )
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient_email
            
            # Attach text part
            text_part = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Attach HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(
                f"[EMAIL_ADAPTER] Email sent successfully to {recipient_email}"
            )
            return True
            
        except smtplib.SMTPException as e:
            logger.error(
                f"[EMAIL_ADAPTER] SMTP error: {type(e).__name__}: {e}"
            )
            return False
            
        except Exception as e:
            logger.error(
                f"[EMAIL_ADAPTER] Exception while sending: {type(e).__name__}: {e}"
            )
            return False


# TODO (Future Phases):
# =====================
# TODO: Add HTML email templates
# TODO: Add email queueing for high volume
# TODO: Add retry logic with exponential backoff
# TODO: Add bounce handling
# TODO: Add unsubscribe support
# TODO: Consider using a transactional email service (SendGrid, AWS SES)

# IMPORTANT: This adapter is FALLBACK ONLY
# Only used when WhatsApp notification fails
# Keep this adapter simple and phase-bounded for Phase 6
