"""
Tenant management API endpoints.

Provides endpoints for creating, retrieving, and updating tenants.
All endpoints enforce proper validation and error handling.
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantUpdate, TenantResponse


router = APIRouter(tags=["tenants"])


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Annotated[Session, Depends(get_db)]
) -> TenantResponse:
    """
    Create a new tenant.
    
    Creates a new tenant with status=active by default.
    
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


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> TenantResponse:
    """
    Get tenant details by ID.
    
    Args:
        tenant_id: Tenant UUID
        db: Database session
        
    Returns:
        TenantResponse: Tenant details
        
    Raises:
        HTTPException: 404 if tenant not found
    """
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
    db: Annotated[Session, Depends(get_db)]
) -> TenantResponse:
    """
    Update tenant status or plan.
    
    Only allows updating status and plan fields.
    
    Args:
        tenant_id: Tenant UUID
        tenant_update: Fields to update
        db: Database session
        
    Returns:
        TenantResponse: Updated tenant details
        
    Raises:
        HTTPException: 404 if tenant not found
    """
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


# TODO: Add authentication middleware to validate tenant ownership
# TODO: Add rate limiting per tenant
# TODO: Add tenant deletion endpoint (soft delete only)
# TODO: Add tenant metrics endpoint
