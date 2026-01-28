"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data exchanged via the API.
All schemas respect tenant isolation boundaries.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models import TenantStatus, TenantPlan, CallDirection, CallStatus, AIRole


# Tenant Schemas
class TenantBase(BaseModel):
    """Base tenant schema."""
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)
    plan: TenantPlan = Field(default=TenantPlan.STARTER)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    status: Optional[TenantStatus] = None
    plan: Optional[TenantPlan] = None


class TenantResponse(TenantBase):
    """Schema for tenant response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# PhoneNumber Schemas
class PhoneNumberBase(BaseModel):
    """Base phone number schema."""
    did_number: str = Field(..., min_length=10, max_length=20)
    provider_type: str = Field(..., min_length=1, max_length=50)
    is_active: bool = Field(default=True)


class PhoneNumberCreate(PhoneNumberBase):
    """Schema for creating a new phone number."""
    pass


class PhoneNumberUpdate(BaseModel):
    """Schema for updating a phone number."""
    provider_type: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class PhoneNumberResponse(PhoneNumberBase):
    """Schema for phone number response."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Call Schemas
class CallBase(BaseModel):
    """Base call schema."""
    direction: CallDirection
    status: CallStatus


class CallCreate(CallBase):
    """Schema for creating a new call."""
    tenant_id: UUID
    phone_number_id: UUID


class CallUpdate(BaseModel):
    """Schema for updating a call."""
    status: Optional[CallStatus] = None
    ended_at: Optional[datetime] = None


class CallResponse(CallBase):
    """Schema for call response."""
    id: UUID
    tenant_id: UUID
    phone_number_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# AIProfile Schemas
class AIProfileBase(BaseModel):
    """Base AI profile schema."""
    role: AIRole = Field(default=AIRole.RECEPTIONIST)
    system_prompt: str = Field(..., min_length=1)
    is_default: bool = Field(default=False)


class AIProfileCreate(AIProfileBase):
    """Schema for creating a new AI profile."""
    pass


class AIProfileUpdate(BaseModel):
    """Schema for updating an AI profile."""
    role: Optional[AIRole] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    is_default: Optional[bool] = None


class AIProfileResponse(AIProfileBase):
    """Schema for AI profile response."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Overall health status")
    config_valid: bool = Field(..., description="Whether configuration is valid")
    message: Optional[str] = Field(None, description="Additional information")


# TODO: Future schemas to be added (all must respect tenant_id boundaries):
# TODO: - CallRecordingResponse (tenant_id, call_id, recording_url)
# TODO: - CallTranscriptResponse (tenant_id, call_id, transcript_text)
# TODO: - CallSummaryResponse (tenant_id, call_id, summary_text, sentiment)
# TODO: - BillingResponse (tenant_id, period, amount, usage_details)
# TODO: - UsageMetricsResponse (tenant_id, metric_type, value, period)
# TODO: - WebhookConfigResponse (tenant_id, url, event_types)
