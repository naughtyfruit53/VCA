"""
Authentication service for Supabase JWT verification.

Implements JWT token verification with JWK caching and user lookup.
"""

import jwt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.config.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# JWK cache (simple in-memory cache for production should use Redis)
_jwk_cache: Optional[Dict[str, Any]] = None
_jwk_cache_time: Optional[datetime] = None
_jwk_cache_ttl = timedelta(hours=1)


def _fetch_jwks() -> Dict[str, Any]:
    """
    Fetch JWKs from Supabase.
    
    In production, this should be cached in Redis.
    For now, using simple in-memory cache.
    """
    global _jwk_cache, _jwk_cache_time
    
    # Check if cache is valid
    if _jwk_cache and _jwk_cache_time:
        if datetime.now() - _jwk_cache_time < _jwk_cache_ttl:
            return _jwk_cache
    
    # For Phase 8, we'll use the JWT secret directly (HS256)
    # In production with Supabase, you'd fetch from /.well-known/jwks.json
    # For now, return a simple marker that we're using HS256
    _jwk_cache = {"alg": "HS256"}
    _jwk_cache_time = datetime.now()
    
    return _jwk_cache


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict containing decoded token payload
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        # Fetch JWKs (cached)
        _fetch_jwks()
        
        # Decode and verify token using Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": False}  # Supabase may use different audience
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error verifying JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


class CurrentUser:
    """
    Current authenticated user information.
    
    Contains user_id, tenant_id, and role from database lookup.
    """
    def __init__(self, user_id: str, tenant_id: str, role: str, email: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.
    
    Verifies JWT token, looks up user in database, and returns user info.
    Supports DEV_AUTH_BYPASS for development environments.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        CurrentUser: Current user information
        
    Raises:
        HTTPException: 401 if not authenticated or user not found
    """
    # DEV_AUTH_BYPASS mode (ONLY if explicitly enabled)
    if settings.dev_auth_bypass:
        logger.warning("DEV_AUTH_BYPASS is enabled - bypassing authentication")
        # Return a mock user for development
        # In real usage, you'd query for the first user or use a specific test user
        test_user = db.query(User).first()
        if test_user:
            return CurrentUser(
                user_id=str(test_user.id),
                tenant_id=str(test_user.tenant_id),
                role=test_user.role.value,
                email=test_user.email
            )
        # If no users exist, raise error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DEV_AUTH_BYPASS enabled but no users found in database",
        )
    
    # Extract token from Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify JWT token
    payload = verify_jwt_token(token)
    
    # Extract supabase_user_id from payload
    supabase_user_id = payload.get("sub")
    email = payload.get("email")
    
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Look up user in database
    user = db.query(User).filter(User.supabase_user_id == supabase_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please complete registration.",
        )
    
    # Return current user info
    return CurrentUser(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
        email=user.email
    )
