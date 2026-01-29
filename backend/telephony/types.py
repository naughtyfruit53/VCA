"""
Data structures for telephony events and metadata.

These types represent call-related data without any vendor-specific logic.
All data structures are tenant-scoped.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from dataclasses import dataclass
from enum import Enum


class CallDirection(str, Enum):
    """Direction of the call."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallEventType(str, Enum):
    """Type of call event."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    ENDED = "ended"
    FAILED = "failed"


@dataclass
class CallMetadata:
    """
    Metadata about a phone call.
    
    This structure contains essential call information without vendor-specific details.
    All calls must be associated with a tenant.
    """
    caller_number: str
    called_number: str
    direction: CallDirection
    timestamp: datetime
    tenant_id: Optional[UUID] = None  # May be None initially, resolved from DID
    phone_number_id: Optional[UUID] = None  # May be None initially, resolved from DID
    call_id: Optional[str] = None  # External telephony system call ID
    
    def __post_init__(self):
        """Validate required fields are set."""
        if not self.caller_number:
            raise ValueError("caller_number is required for all calls")
        if not self.called_number:
            raise ValueError("called_number is required for all calls")


@dataclass
class CallEvent:
    """
    Event representing a change in call state.
    
    This structure represents state transitions in a call lifecycle.
    """
    event_type: CallEventType
    call_metadata: CallMetadata
    timestamp: datetime
    details: Optional[str] = None
