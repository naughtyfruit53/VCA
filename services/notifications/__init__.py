"""
Notification services package for Phase 6.

This package contains notification adapters for sending call summaries
to tenants via WhatsApp and email.

PHASE 6 IMPLEMENTATION:
- Strictly isolated notification logic
- One-way summary delivery only (no interactions)
- Maximum one notification per call
- Notification failures must not interrupt call flow

All adapters MUST:
- Enforce tenant_id scoping
- Handle failures gracefully
- Log all attempts
- Never block call processing
"""

from .whatsapp_adapter import WhatsAppAdapter
from .email_adapter import EmailAdapter
from .notification_service import NotificationService

__all__ = ['WhatsAppAdapter', 'EmailAdapter', 'NotificationService']
