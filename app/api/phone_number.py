"""
Phone number management API endpoints.

Provides endpoints for attaching, listing, and managing phone numbers for tenants.
All endpoints enforce tenant isolation and validation.
"""

from uuid import UUID
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config.database import get_db
from app.models import Tenant, PhoneNumber
from app.schemas import PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberResponse
from app.services.auth import CurrentUser, get_current_user


router = APIRouter(tags=["phone-numbers"])


@router.post(
    "/tenants/{tenant_id}/phone-numbers",
    response_model=PhoneNumberResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_phone_number(
    tenant_id: UUID,
    phone_data: PhoneNumberCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> PhoneNumberResponse:
    """
    Attach a phone number to a tenant.
    
    Phone number must be globally unique. Tenant must exist.
    
    Args:
        tenant_id: Tenant UUID
        phone_data: Phone number data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PhoneNumberResponse: Created phone number details
        
    Raises:
        HTTPException: 403 if tenant_id doesn't match user's tenant or user lacks permissions
        HTTPException: 404 if tenant not found
        HTTPException: 409 if phone number already exists
        HTTPException: 400 if provider_type is not "generic"
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    # Verify user has owner or admin role
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can create phone numbers"
        )
    
    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Validate provider_type is generic
    if phone_data.provider_type != "generic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provider_type must be 'generic'"
        )
    
    # Create phone number
    new_phone = PhoneNumber(
        tenant_id=tenant_id,
        did_number=phone_data.did_number,
        provider_type=phone_data.provider_type,
        is_active=phone_data.is_active
    )
    
    try:
        db.add(new_phone)
        db.commit()
        db.refresh(new_phone)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already exists"
        )
    
    return PhoneNumberResponse.model_validate(new_phone)


@router.get("/tenants/{tenant_id}/phone-numbers", response_model=List[PhoneNumberResponse])
async def list_phone_numbers(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> List[PhoneNumberResponse]:
    """
    List all phone numbers for a tenant.
    
    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[PhoneNumberResponse]: List of phone numbers
        
    Raises:
        HTTPException: 403 if tenant_id doesn't match user's tenant
        HTTPException: 404 if tenant not found
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Get all phone numbers for tenant
    phone_numbers = db.query(PhoneNumber).filter(
        PhoneNumber.tenant_id == tenant_id
    ).all()
    
    return [PhoneNumberResponse.model_validate(phone) for phone in phone_numbers]


@router.patch(
    "/tenants/{tenant_id}/phone-numbers/{phone_number_id}",
    response_model=PhoneNumberResponse
)
async def update_phone_number(
    tenant_id: UUID,
    phone_number_id: UUID,
    phone_update: PhoneNumberUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> PhoneNumberResponse:
    """
    Update phone number (activate/deactivate).
    
    Enforces tenant ownership - can only update phone numbers belonging to the tenant.
    
    Args:
        tenant_id: Tenant UUID
        phone_number_id: Phone number UUID
        phone_update: Fields to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PhoneNumberResponse: Updated phone number details
        
    Raises:
        HTTPException: 403 if tenant_id doesn't match user's tenant or user lacks permissions
        HTTPException: 404 if phone number not found or doesn't belong to tenant
        HTTPException: 400 if provider_type is not "generic"
    """
    # Verify tenant_id matches current user's tenant
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    # Verify user has owner or admin role
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can update phone numbers"
        )
    
    # Get phone number and enforce tenant ownership
    phone_number = db.query(PhoneNumber).filter(
        PhoneNumber.id == phone_number_id,
        PhoneNumber.tenant_id == tenant_id
    ).first()
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found or does not belong to tenant"
        )
    
    # Get update data
    update_data = phone_update.model_dump(exclude_unset=True)
    
    # Validate provider_type if being updated
    if "provider_type" in update_data and update_data["provider_type"] != "generic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provider_type must be 'generic'"
        )
    
    # Update fields
    for field, value in update_data.items():
        setattr(phone_number, field, value)
    
    db.commit()
    db.refresh(phone_number)
    
    return PhoneNumberResponse.model_validate(phone_number)


# TODO: Add telephony provider integration (Twilio, Telnyx, etc.)
# TODO: Add phone number verification endpoint
# TODO: Add phone number deletion endpoint
# TODO: Add webhook endpoint for incoming calls
# TODO: Add call routing configuration per phone number
