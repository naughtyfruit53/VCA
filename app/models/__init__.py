"""
Database models for VCA platform.

IMPORTANT: All future features MUST be added behind tenant_id boundaries.
No global data access is permitted.

All models implement strict multi-tenancy through tenant_id foreign keys.
Every resource must be scoped to a specific tenant.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Integer,
    Enum, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


# Enums
class TenantStatus(str, PyEnum):
    """Tenant account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TenantPlan(str, PyEnum):
    """Tenant subscription plan."""
    STARTER = "starter"
    GROWTH = "growth"
    CUSTOM = "custom"


class PrimaryLanguage(str, PyEnum):
    """Primary language for tenant."""
    EN = "en"
    HI = "hi"
    MR = "mr"
    GU = "gu"


class UserRole(str, PyEnum):
    """User role within a tenant."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class CallDirection(str, PyEnum):
    """Call direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(str, PyEnum):
    """Call status."""
    COMPLETED = "completed"
    FAILED = "failed"
    TRANSFERRED = "transferred"


class AIRole(str, PyEnum):
    """AI profile role types."""
    RECEPTIONIST = "receptionist"
    SALES = "sales"
    SUPPORT = "support"
    DISPATCHER = "dispatcher"
    CUSTOM = "custom"


# Models
class User(Base):
    """
    User model - represents authenticated users.
    
    STRICT TENANT ISOLATION: Each user belongs to exactly one tenant.
    Users authenticate via Supabase and are mapped to tenants.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_supabase_user_id", "supabase_user_id"),
        Index("idx_user_email", "email"),
        Index("idx_user_tenant_id", "tenant_id"),
    )


class Tenant(Base):
    """
    Tenant model - represents a customer organization.
    
    Each tenant is isolated and has its own set of resources.
    All other models must reference tenant_id.
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE)
    plan = Column(Enum(TenantPlan), nullable=False, default=TenantPlan.STARTER)
    primary_language = Column(Enum(PrimaryLanguage), nullable=False, default=PrimaryLanguage.EN)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    phone_numbers = relationship("PhoneNumber", back_populates="tenant", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="tenant", cascade="all, delete-orphan")
    ai_profiles = relationship("AIProfile", back_populates="tenant", cascade="all, delete-orphan")
    business_profile = relationship("BusinessProfile", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_plan", "plan"),
    )


class PhoneNumber(Base):
    """
    PhoneNumber model - DID numbers assigned to tenants.
    
    STRICT TENANT ISOLATION: Each phone number belongs to exactly one tenant.
    """
    __tablename__ = "phone_numbers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    did_number = Column(String(20), nullable=False, unique=True)
    provider_type = Column(String(50), nullable=False)  # Generic string, not vendor-specific
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="phone_numbers")
    calls = relationship("Call", back_populates="phone_number", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_phone_tenant_id", "tenant_id"),
        Index("idx_phone_did_number", "did_number"),
        Index("idx_phone_is_active", "is_active"),
    )


class Call(Base):
    """
    Call model - represents individual phone calls.
    
    STRICT TENANT ISOLATION: Each call belongs to exactly one tenant.
    """
    __tablename__ = "calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    phone_number_id = Column(UUID(as_uuid=True), ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False)
    direction = Column(Enum(CallDirection), nullable=False)
    status = Column(Enum(CallStatus), nullable=False)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="calls")
    phone_number = relationship("PhoneNumber", back_populates="calls")
    
    # Indexes
    __table_args__ = (
        Index("idx_call_tenant_id", "tenant_id"),
        Index("idx_call_phone_number_id", "phone_number_id"),
        Index("idx_call_direction", "direction"),
        Index("idx_call_status", "status"),
        Index("idx_call_started_at", "started_at"),
    )


class AIProfile(Base):
    """
    AIProfile model - AI agent configuration per tenant.
    
    STRICT TENANT ISOLATION: Each AI profile belongs to exactly one tenant.
    Tenants can have multiple AI profiles for different purposes.
    """
    __tablename__ = "ai_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(AIRole), nullable=False, default=AIRole.RECEPTIONIST)
    system_prompt = Column(Text, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="ai_profiles")
    
    # Indexes
    __table_args__ = (
        Index("idx_ai_profile_tenant_id", "tenant_id"),
        Index("idx_ai_profile_role", "role"),
        Index("idx_ai_profile_is_default", "is_default"),
    )


class BusinessProfile(Base):
    """
    BusinessProfile model - Business information and configuration per tenant.
    
    STRICT TENANT ISOLATION: Each business profile belongs to exactly one tenant.
    One-to-one relationship with Tenant.
    
    This model stores business-specific information used for Agent Brain v1 APIs:
    - Business identity (name, type)
    - Service catalog (services offered, service areas)
    - Operating parameters (business hours, booking settings)
    - Agent behavior rules (escalation rules, forbidden statements)
    """
    __tablename__ = "business_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Business identity
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100), nullable=False)
    
    # Service catalog - stored as JSON arrays
    services = Column(JSON, nullable=False, default=lambda: [])  # List of service names
    service_areas = Column(JSON, nullable=False, default=lambda: [])  # List of geographic areas
    
    # Operating parameters - stored as JSON
    business_hours = Column(JSON, nullable=False, default=lambda: {})  # e.g., {"monday": "9-5", "tuesday": "9-5"}
    booking_enabled = Column(Boolean, nullable=False, default=False)
    
    # Agent behavior rules - stored as JSON
    escalation_rules = Column(JSON, nullable=False, default=lambda: {})  # Rules for escalating conversations
    forbidden_statements = Column(JSON, nullable=False, default=lambda: [])  # Statements the agent should never make
    
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="business_profile")
    
    # Indexes
    __table_args__ = (
        Index("idx_business_profile_tenant_id", "tenant_id"),
    )


class CallSummary(Base):
    """
    CallSummary model - Structured call summary generated after call ends.
    
    STRICT TENANT ISOLATION: Each call summary belongs to exactly one tenant.
    
    Phase 6 Implementation:
    - Generated after call ends
    - Always tenant_id scoped
    - Stores structured summary data (not raw transcripts)
    - Used for notifications and dashboard display
    """
    __tablename__ = "call_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Summary content
    summary_text = Column(Text, nullable=False)
    caller_intent = Column(String(255), nullable=True)
    resolution_status = Column(String(100), nullable=True)  # e.g., "resolved", "needs_callback", "transferred"
    
    # Metadata
    call_duration_seconds = Column(Integer, nullable=True)
    ai_turns_count = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("idx_call_summary_tenant_id", "tenant_id"),
        Index("idx_call_summary_call_id", "call_id"),
        Index("idx_call_summary_created_at", "created_at"),
    )




class NotificationLog(Base):
    """
    NotificationLog model - Log of notifications sent for Phase 6.
    
    STRICT TENANT ISOLATION: Each notification log belongs to exactly one tenant.
    
    Phase 6 Implementation:
    - Tracks notification attempts (WhatsApp, Email)
    - Records success/failure status
    - Maximum one notification per call
    - Notification failures must not interrupt call flow
    """
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    call_summary_id = Column(UUID(as_uuid=True), ForeignKey("call_summaries.id", ondelete="SET NULL"), nullable=True)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # "whatsapp", "email"
    recipient = Column(String(255), nullable=False)  # Phone number or email
    status = Column(String(50), nullable=False)  # "sent", "failed", "pending"
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("idx_notification_log_tenant_id", "tenant_id"),
        Index("idx_notification_log_call_id", "call_id"),
        Index("idx_notification_log_status", "status"),
    )


# TODO: Future models to be added (all must have tenant_id):
# TODO: - CallRecording (tenant_id, call_id, recording_url, duration)
# TODO: - CallTranscript (tenant_id, call_id, transcript_text, language)
# TODO: - TenantBilling (tenant_id, period_start, period_end, amount, status)
# TODO: - TenantUsage (tenant_id, metric_type, value, recorded_at)
# TODO: - WebhookEndpoint (tenant_id, url, event_types, is_active)
# TODO: - TenantSettings (tenant_id, setting_key, setting_value)
