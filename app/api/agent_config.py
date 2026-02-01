"""
Agent Configuration API endpoints for Agent Brain v1.

Provides endpoints for managing agent configuration including:
- Primary language settings
- Business profile configuration

All endpoints enforce strict tenant isolation.
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models import Tenant, BusinessProfile
from app.services.auth import CurrentUser, get_current_user
from app.schemas import (
    AgentConfigResponse,
    AgentConfigUpdate,
    BusinessProfileResponse,
    BusinessProfileCreate,
    BusinessProfileUpdate,
)


router = APIRouter(tags=["agent-config"])


@router.get("/tenants/{tenant_id}/agent-config", response_model=AgentConfigResponse)
async def get_agent_config(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> AgentConfigResponse:
    """
    Get agent configuration for a tenant.
    
    Returns the tenant's primary language and business profile (if configured).
    
    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        AgentConfigResponse: Agent configuration including primary_language and business_profile
        
    Raises:
        HTTPException: 403 if tenant_id doesn't match user's tenant
        HTTPException: 404 if tenant not found
    """
    # Verify tenant access
    if str(tenant_id) != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: tenant_id mismatch"
        )
    
    # Fetch tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Fetch business profile if exists
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.tenant_id == tenant_id
    ).first()
    
    return AgentConfigResponse(
        tenant_id=tenant.id,
        primary_language=tenant.primary_language,
        business_profile=BusinessProfileResponse.model_validate(business_profile) if business_profile else None
    )


@router.patch("/tenants/{tenant_id}/agent-config", response_model=AgentConfigResponse)
async def update_agent_config(
    tenant_id: UUID,
    config_update: AgentConfigUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> AgentConfigResponse:
    """
    Update agent configuration for a tenant.
    
    Updates the tenant's primary language and/or business profile.
    Creates business profile if it doesn't exist and business_profile data is provided.
    
    Args:
        tenant_id: Tenant UUID
        config_update: Configuration updates
        db: Database session
        current_user: Authenticated user
        
    Returns:
        AgentConfigResponse: Updated agent configuration
        
    Raises:
        HTTPException: 403 if tenant_id doesn't match user's tenant or insufficient permissions
        HTTPException: 404 if tenant not found
    """
    # Verify tenant access
    if str(tenant_id) != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: tenant_id mismatch"
        )
    
    # Verify user has permission to update
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: owner or admin role required"
        )
    
    # Fetch tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update primary language if provided
    if config_update.primary_language is not None:
        tenant.primary_language = config_update.primary_language
    
    # Update or create business profile if provided
    business_profile = None
    if config_update.business_profile is not None:
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.tenant_id == tenant_id
        ).first()
        
        profile_data = config_update.business_profile.model_dump(exclude_unset=True)
        
        if business_profile:
            # Update existing business profile
            for field, value in profile_data.items():
                setattr(business_profile, field, value)
        else:
            # Create new business profile
            # Need to provide required fields
            if "business_name" not in profile_data or "business_type" not in profile_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="business_name and business_type are required when creating business profile"
                )
            
            business_profile = BusinessProfile(
                tenant_id=tenant_id,
                **profile_data
            )
            db.add(business_profile)
    else:
        # Fetch existing business profile if not updating it
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.tenant_id == tenant_id
        ).first()
    
    db.commit()
    db.refresh(tenant)
    if business_profile:
        db.refresh(business_profile)
    
    return AgentConfigResponse(
        tenant_id=tenant.id,
        primary_language=tenant.primary_language,
        business_profile=BusinessProfileResponse.model_validate(business_profile) if business_profile else None
    )
