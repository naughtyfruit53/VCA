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
    Column, String, Boolean, DateTime, Text, ForeignKey, 
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
    services = Column(JSON, nullable=False, default=list)  # List of service names
    service_areas = Column(JSON, nullable=False, default=list)  # List of geographic areas
    
    # Operating parameters - stored as JSON
    business_hours = Column(JSON, nullable=False, default=dict)  # e.g., {"monday": "9-5", "tuesday": "9-5"}
    booking_enabled = Column(Boolean, nullable=False, default=False)
    
    # Agent behavior rules - stored as JSON
    escalation_rules = Column(JSON, nullable=False, default=dict)  # Rules for escalating conversations
    forbidden_statements = Column(JSON, nullable=False, default=list)  # Statements the agent should never make
    
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="business_profile")
    
    # Indexes
    __table_args__ = (
        Index("idx_business_profile_tenant_id", "tenant_id"),
    )


# TODO: Future models to be added (all must have tenant_id):
# TODO: - CallRecording (tenant_id, call_id, recording_url, duration)
# TODO: - CallTranscript (tenant_id, call_id, transcript_text, language)
# TODO: - CallSummary (tenant_id, call_id, summary_text, sentiment)
# TODO: - TenantBilling (tenant_id, period_start, period_end, amount, status)
# TODO: - TenantUsage (tenant_id, metric_type, value, recorded_at)
# TODO: - WebhookEndpoint (tenant_id, url, event_types, is_active)
# TODO: - TenantSettings (tenant_id, setting_key, setting_value)
