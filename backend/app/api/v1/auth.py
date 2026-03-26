"""
Authentication API endpoints.

This module provides authentication endpoints for login, logout, and token refresh.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import create_access_token, create_refresh_token, verify_token
from ...dependencies import get_current_user, get_current_active_user
from ...models.user import User
from ...schemas.user import LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from ...schemas.common import SuccessResponse
from ...services.user_service import UserService
from ...services.audit_service import AuditService
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access tokens.
    
    This endpoint validates user credentials and returns JWT access and refresh tokens.
    It also logs the authentication attempt for audit purposes.
    
    Args:
        login_data: Login credentials (email and password).
        request: FastAPI request object for audit logging.
        db: Database session.
        
    Returns:
        LoginResponse: Access and refresh tokens with user information.
        
    Raises:
        HTTPException: 401 if credentials are invalid or account is inactive.
    """
    # Initialize services
    user_service = UserService(db=db)
    audit_service = AuditService(db=db, request=request)
    
    try:
        # Authenticate user
        user = user_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            # Log failed authentication
            audit_service.log_authentication(
                email=login_data.email,
                result="failure",
                reason="invalid_credentials"
            )
            
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create tokens with user context
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "tenant_id": str(user.tenant_id),
                "role": user.role.name,
                "email": user.email
            }
        )
        
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Log successful authentication
        audit_service.log_authentication(
            email=user.email,
            result="success"
        )
        
        # Commit audit logs
        db.commit()
        
        logger.info(f"Successful login for user: {user.email}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
            user={
                "id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role_id": user.role_id,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "role": {
                    "id": user.role.id,
                    "name": user.role.name,
                    "description": user.role.description,
                    "created_at": user.role.created_at
                } if user.role else None
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Login error for {login_data.email}: {e}")
        audit_service.log_authentication(
            email=login_data.email,
            result="error",
            reason="system_error"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    This endpoint validates a refresh token and issues a new access token.
    The refresh token itself is not rotated.
    
    Args:
        refresh_data: Refresh token data.
        request: FastAPI request object for audit logging.
        db: Database session.
        
    Returns:
        RefreshTokenResponse: New access token.
        
    Raises:
        HTTPException: 401 if refresh token is invalid or user is inactive.
    """
    # Initialize services
    audit_service = AuditService(db=db, request=request)
    
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            audit_service.log(
                action="token_refresh",
                result="failure",
                after_value={"reason": "invalid_token"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Look up user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            audit_service.log(
                action="token_refresh",
                result="failure",
                after_value={"reason": "user_not_found_or_inactive", "user_id": user_id}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "tenant_id": str(user.tenant_id),
                "role": user.role.name,
                "email": user.email
            }
        )
        
        # Log successful token refresh
        audit_service.log(
            action="token_refresh",
            resource_type="user",
            resource_id=user.id,
            result="success"
        )
        
        # Commit audit logs
        db.commit()
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Token refresh error: {e}")
        audit_service.log(
            action="token_refresh",
            result="error",
            after_value={"error": str(e)}
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.
    
    Note: In a stateless JWT implementation, logout is primarily client-side
    (the client should discard the tokens). This endpoint serves as a confirmation
    and for audit logging purposes.
    
    In a production system, you might want to implement token blacklisting
    using Redis to immediately invalidate tokens.
    
    Args:
        request: FastAPI request object for audit logging.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        SuccessResponse: Logout confirmation.
    """
    # Initialize audit service
    audit_service = AuditService(
        db=db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        request=request
    )
    
    try:
        # Log logout event
        audit_service.log(
            action="user_logout",
            resource_type="user",
            resource_id=current_user.id,
            result="success"
        )
        
        # Commit audit log
        db.commit()
        
        logger.info(f"User logged out: {current_user.email}")
        
        return SuccessResponse(
            message="Successfully logged out"
        )
        
    except Exception as e:
        logger.error(f"Logout error for user {current_user.email}: {e}")
        db.rollback()
        # Still return success to client even if audit logging fails
        return SuccessResponse(
            message="Successfully logged out"
        )
