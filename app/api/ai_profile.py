"""
AI Profile management API endpoints.

Provides endpoints for creating, listing, and managing AI profiles for tenants.
All endpoints enforce tenant isolation and the one default profile per tenant rule.
"""

from uuid import UUID
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models import Tenant, AIProfile
from app.schemas import AIProfileCreate, AIProfileUpdate, AIProfileResponse
from app.services.auth import CurrentUser, get_current_user


router = APIRouter(tags=["ai-profiles"])


@router.post(
    "/tenants/{tenant_id}/ai-profiles",
    response_model=AIProfileResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_ai_profile(
    tenant_id: UUID,
    profile_data: AIProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> AIProfileResponse:
    """
    Create an AI profile for a tenant.
    
    Enforces that only one profile can be set as default per tenant.
    If this profile is marked as default, all other profiles for the tenant
    will be set to non-default.
    
    Args:
        tenant_id: Tenant UUID
        profile_data: AI profile data
        db: Database session
        
    Returns:
        AIProfileResponse: Created AI profile details
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check user has owner or admin role
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can create AI profiles"
        )
    
    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # If this profile is marked as default, unset all other defaults for this tenant
    if profile_data.is_default:
        db.query(AIProfile).filter(
            AIProfile.tenant_id == tenant_id,
            AIProfile.is_default.is_(True)
        ).update({"is_default": False})
    
    # Create AI profile
    new_profile = AIProfile(
        tenant_id=tenant_id,
        role=profile_data.role,
        system_prompt=profile_data.system_prompt,
        is_default=profile_data.is_default
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return AIProfileResponse.model_validate(new_profile)


@router.get("/tenants/{tenant_id}/ai-profiles", response_model=List[AIProfileResponse])
async def list_ai_profiles(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> List[AIProfileResponse]:
    """
    List all AI profiles for a tenant.
    
    Args:
        tenant_id: Tenant UUID
        db: Database session
        
    Returns:
        List[AIProfileResponse]: List of AI profiles
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Get all AI profiles for tenant
    profiles = db.query(AIProfile).filter(
        AIProfile.tenant_id == tenant_id
    ).all()
    
    return [AIProfileResponse.model_validate(profile) for profile in profiles]


@router.patch(
    "/tenants/{tenant_id}/ai-profiles/{ai_profile_id}",
    response_model=AIProfileResponse
)
async def update_ai_profile(
    tenant_id: UUID,
    ai_profile_id: UUID,
    profile_update: AIProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> AIProfileResponse:
    """
    Update an AI profile.
    
    Can update system_prompt, role, or is_default.
    Enforces that only one profile can be default per tenant.
    
    Args:
        tenant_id: Tenant UUID
        ai_profile_id: AI profile UUID
        profile_update: Fields to update
        db: Database session
        
    Returns:
        AIProfileResponse: Updated AI profile details
        
    Raises:
        HTTPException: 404 if profile not found or doesn't belong to tenant
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check user has owner or admin role
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can update AI profiles"
        )
    
    # Get AI profile and enforce tenant ownership
    profile = db.query(AIProfile).filter(
        AIProfile.id == ai_profile_id,
        AIProfile.tenant_id == tenant_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI profile not found or does not belong to tenant"
        )
    
    # Get update data
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # If setting this as default, unset all other defaults for this tenant
    if update_data.get("is_default") is True:
        db.query(AIProfile).filter(
            AIProfile.tenant_id == tenant_id,
            AIProfile.id != ai_profile_id,
            AIProfile.is_default.is_(True)
        ).update({"is_default": False})
    
    # Update fields
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return AIProfileResponse.model_validate(profile)


# TODO: Add LLM provider integration (OpenAI, Anthropic, etc.)
# TODO: Add profile testing endpoint (dry run with sample input)
# TODO: Add profile versioning for rollback capability
# TODO: Add profile templates/presets
# TODO: Add profile performance metrics
# TODO: Add profile deletion endpoint
