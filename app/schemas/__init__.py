"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data exchanged via the API.
All schemas respect tenant isolation boundaries.
"""

from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel, Field

from app.models import TenantStatus, TenantPlan, CallDirection, CallStatus, AIRole, PrimaryLanguage


# Tenant Schemas
class TenantBase(BaseModel):
    """Base tenant schema."""
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)
    plan: TenantPlan = Field(default=TenantPlan.STARTER)
    primary_language: PrimaryLanguage = Field(default=PrimaryLanguage.EN)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    status: Optional[TenantStatus] = None
    plan: Optional[TenantPlan] = None
    primary_language: Optional[PrimaryLanguage] = None


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


# BusinessProfile Schemas
class BusinessProfileBase(BaseModel):
    """Base business profile schema."""
    business_name: str = Field(..., min_length=1, max_length=255)
    business_type: str = Field(..., min_length=1, max_length=100)
    services: List[str] = Field(default_factory=list)
    service_areas: List[str] = Field(default_factory=list)
    business_hours: Dict[str, str] = Field(default_factory=dict)
    booking_enabled: bool = Field(default=False)
    escalation_rules: Dict[str, str] = Field(default_factory=dict)
    forbidden_statements: List[str] = Field(default_factory=list)


class BusinessProfileCreate(BusinessProfileBase):
    """Schema for creating a business profile."""
    pass


class BusinessProfileUpdate(BaseModel):
    """Schema for updating a business profile."""
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[str] = Field(None, min_length=1, max_length=100)
    services: Optional[List[str]] = None
    service_areas: Optional[List[str]] = None
    business_hours: Optional[Dict[str, str]] = None
    booking_enabled: Optional[bool] = None
    escalation_rules: Optional[Dict[str, str]] = None
    forbidden_statements: Optional[List[str]] = None


class BusinessProfileResponse(BusinessProfileBase):
    """Schema for business profile response."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Agent Config Schemas (combines primary_language and business profile)
class AgentConfigResponse(BaseModel):
    """Schema for agent configuration response."""
    tenant_id: UUID
    primary_language: PrimaryLanguage
    business_profile: Optional[BusinessProfileResponse] = None


class AgentConfigUpdate(BaseModel):
    """Schema for updating agent configuration."""
    primary_language: Optional[PrimaryLanguage] = None
    business_profile: Optional[BusinessProfileUpdate] = None


# Sandbox Simulation Schemas
class SandboxSimulateRequest(BaseModel):
    """
    Schema for sandbox simulation request.
    
    This endpoint simulates agent responses without real LLM calls.
    All responses are clearly marked as MOCK/SIMULATED.
    """
    tenant_id: UUID = Field(..., description="Tenant ID for configuration lookup")
    user_text: str = Field(..., min_length=1, description="User input text")
    session_id: Optional[str] = Field(None, description="Optional session ID (auto-generated if not provided)")


class SandboxSimulateResponse(BaseModel):
    """
    Schema for sandbox simulation response.
    
    IMPORTANT: This response is SIMULATED/MOCK. No real AI inference is performed.
    """
    session_id: str = Field(..., description="Session ID for this conversation")
    detected_language: str = Field(..., description="Detected language code (SIMULATED)")
    speaking_language: str = Field(..., description="Agent speaking language for this session")
    simulated_response: str = Field(
        ...,
        description="MOCK response - This is a simulated response based on assembled prompt. No AI inference performed."
    )


# TODO: Future schemas to be added (all must respect tenant_id boundaries):
# TODO: - CallRecordingResponse (tenant_id, call_id, recording_url)
# TODO: - CallTranscriptResponse (tenant_id, call_id, transcript_text)
# TODO: - CallSummaryResponse (tenant_id, call_id, summary_text, sentiment)
# TODO: - BillingResponse (tenant_id, period, amount, usage_details)
# TODO: - UsageMetricsResponse (tenant_id, metric_type, value, period)
# TODO: - WebhookConfigResponse (tenant_id, url, event_types)
