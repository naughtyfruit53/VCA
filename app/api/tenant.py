"""
Tenant management API endpoints.

Provides endpoints for creating, retrieving, and updating tenants.
All endpoints enforce proper validation and error handling.
All endpoints require authentication (Phase 8).
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantUpdate, TenantResponse
from app.services.auth import get_current_user, CurrentUser


router = APIRouter(tags=["tenants"])


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Annotated[Session, Depends(get_db)]
) -> TenantResponse:
    """
    Create a new tenant.
    
    Creates a new tenant with status=active by default.
    Note: This endpoint does not require authentication as it's used during initial signup.
    
    Args:
        tenant_data: Tenant creation data
        db: Database session
        
    Returns:
        TenantResponse: Created tenant details
    """
    # Create new tenant
    new_tenant = Tenant(
        status=tenant_data.status,
        plan=tenant_data.plan,
        primary_language=tenant_data.primary_language
    )
    
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    return TenantResponse.model_validate(new_tenant)


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> TenantResponse:
    """
    Get current user's tenant details.
    
    Returns tenant information for the authenticated user.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        TenantResponse: Current user's tenant details
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.model_validate(tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> TenantResponse:
    """
    Get tenant details by ID.
    
    User must belong to the tenant to access it.
    
    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        TenantResponse: Tenant details
        
    Raises:
        HTTPException: 403 if user doesn't have access to tenant
        HTTPException: 404 if tenant not found
    """
    # Verify user has access to this tenant
    if str(tenant_id) != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this tenant"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.model_validate(tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_update: TenantUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> TenantResponse:
    """
    Update tenant status or plan.
    
    Only allows updating status and plan fields.
    User must be an owner or admin of the tenant.
    
    Args:
        tenant_id: Tenant UUID
        tenant_update: Fields to update
        db: Database session
        current_user: Authenticated user
        
    Returns:
        TenantResponse: Updated tenant details
        
    Raises:
        HTTPException: 403 if user doesn't have permission
        HTTPException: 404 if tenant not found
    """
    # Verify user has access to this tenant
    if str(tenant_id) != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this tenant"
        )
    
    # Only owners and admins can update tenant
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only owners and admins can update tenant settings"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update only provided fields
    update_data = tenant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse.model_validate(tenant)


# TODO: Add tenant deletion endpoint (soft delete only)
# TODO: Add tenant metrics endpoint
