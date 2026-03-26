"""
FastAPI dependency injection functions.

This module provides dependency functions for authentication, authorization,
database sessions, and other common requirements across API endpoints.
"""

import logging
from functools import wraps
from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose.exceptions import JWTError
from sqlalchemy.orm import Session

from .core.database import get_db
from .core.security import verify_token
from .core.middleware import inject_tenant_context, get_tenant_context
from .models import User

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    This dependency validates the JWT token and returns the authenticated user.
    It handles token extraction, validation, and user lookup.
    
    Args:
        credentials: HTTP Bearer credentials from request header.
        db: Database session.
        
    Returns:
        User: Authenticated user object.
        
    Raises:
        HTTPException: 401 if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if credentials are provided
    if not credentials:
        logger.warning("No authentication credentials provided")
        raise credentials_exception
    
    try:
        # Verify JWT token
        payload = verify_token(credentials.credentials, token_type="access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token missing subject claim")
            raise credentials_exception
        
        # Validate UUID format
        try:
            UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid UUID format in token: {user_id}")
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise credentials_exception
    
    # Look up user in database
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise credentials_exception
        
        # Inject tenant context into request state
        inject_tenant_context(request, user)
        
        logger.debug(f"Successfully authenticated user: {user.email}")
        return user
        
    except Exception as e:
        logger.error(f"Database error during user lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (must be authenticated and active).
    
    This dependency ensures the user is not only authenticated but also
    has an active account status.
    
    Args:
        current_user: Authenticated user from get_current_user dependency.
        
    Returns:
        User: Active authenticated user.
        
    Raises:
        HTTPException: 401 if user account is inactive.
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account"
        )
    
    return current_user


def get_tenant_context_dependency(request: Request) -> str:
    """
    Get tenant ID from request state.
    
    This dependency extracts the tenant ID that was injected by the
    authentication middleware. It ensures that the user is authenticated
    and has a valid tenant context.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        str: Tenant ID for the authenticated user.
        
    Raises:
        HTTPException: 401 if tenant context is missing (user not authenticated).
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    
    if not tenant_id:
        logger.warning("Tenant context missing - user not authenticated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return tenant_id


def get_user_context(request: Request) -> dict:
    """
    Get complete user context from request state.
    
    This dependency returns all available user context information
    including tenant ID, user ID, and role information.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        dict: Complete user context information.
        
    Raises:
        HTTPException: 401 if user context is missing.
    """
    context = get_tenant_context(request)
    
    if not context.get("tenant_id") or not context.get("user_id"):
        logger.warning("User context missing - authentication required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return context


def get_optional_tenant_context(request: Request) -> Optional[str]:
    """
    Get tenant ID from request state if available.
    
    This dependency is useful for endpoints that work for both authenticated
    and anonymous users but need tenant context when available.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        str: Tenant ID if user is authenticated, None otherwise.
    """
    return getattr(request.state, "tenant_id", None)


def require_cross_tenant_access(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require SuperAdmin role for cross-tenant access.
    
    This dependency is used for endpoints that need to access data
    across multiple tenants, which is only allowed for SuperAdmin users.
    
    Args:
        current_user: Active authenticated user.
        
    Returns:
        User: SuperAdmin user with cross-tenant access.
        
    Raises:
        HTTPException: 403 if user is not SuperAdmin.
    """
    if current_user.role.name != "SuperAdmin":
        logger.warning(
            f"Non-SuperAdmin user attempted cross-tenant access: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access requires SuperAdmin role"
        )
    
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    This dependency is useful for endpoints that work for both authenticated
    and anonymous users but provide different functionality based on auth status.
    
    Args:
        credentials: HTTP Bearer credentials from request header.
        db: Database session.
        
    Returns:
        User: Authenticated user if valid token provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        # Verify JWT token
        payload = verify_token(credentials.credentials, token_type="access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Look up user in database
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None or not user.is_active:
            return None
        
        # Inject tenant context for authenticated users
        inject_tenant_context(request, user)
        
        return user
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


def get_superadmin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require SuperAdmin role for access.
    
    This dependency ensures only users with SuperAdmin role can access
    the protected endpoint.
    
    Args:
        current_user: Active authenticated user.
        
    Returns:
        User: SuperAdmin user.
        
    Raises:
        HTTPException: 403 if user is not SuperAdmin.
    """
    if current_user.role.name != "SuperAdmin":
        logger.warning(
            f"Non-SuperAdmin user attempted SuperAdmin access: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin access required"
        )
    
    return current_user


def get_tenant_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require TenantAdmin or SuperAdmin role for access.
    
    Args:
        current_user: Active authenticated user.
        
    Returns:
        User: TenantAdmin or SuperAdmin user.
        
    Raises:
        HTTPException: 403 if user lacks required role.
    """
    allowed_roles = ["SuperAdmin", "TenantAdmin"]
    
    if current_user.role.name not in allowed_roles:
        logger.warning(
            f"User without admin role attempted admin access: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


class PermissionChecker:
    """
    Permission checker for role-based access control.
    
    This class creates dependency functions that check if the current user
    has specific permissions for resources and actions.
    """
    
    def __init__(self, resource: str, action: str):
        """
        Initialize permission checker.
        
        Args:
            resource: Resource type (e.g., "device", "template").
            action: Action type (e.g., "create", "read", "update", "delete").
        """
        self.resource = resource
        self.action = action
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if current user has required permission.
        
        Args:
            current_user: Active authenticated user.
            
        Returns:
            User: User with required permission.
            
        Raises:
            HTTPException: 403 if user lacks required permission.
        """
        # SuperAdmin bypasses all permission checks
        if current_user.role.name == "SuperAdmin":
            return current_user
        
        # Check if user's role has the required permission
        has_permission = any(
            perm.resource == self.resource and perm.action == self.action
            for perm in current_user.role.permissions
        )
        
        if not has_permission:
            logger.warning(
                f"User {current_user.email} lacks permission {self.resource}:{self.action}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.resource}:{self.action}"
            )
        
        return current_user


def require_permission(resource: str, action: str):
    """
    Create permission requirement dependency.
    
    Args:
        resource: Resource type to check.
        action: Action type to check.
        
    Returns:
        Callable: Dependency function that checks permission.
        
    Example:
        @app.get("/devices/")
        def list_devices(
            user: User = Depends(require_permission("device", "read"))
        ):
            return get_devices_for_user(user)
    """
    return PermissionChecker(resource, action)


def get_api_key_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate user via API key token.
    
    This dependency is similar to get_current_user but specifically
    validates API key tokens for programmatic access.
    
    Args:
        credentials: HTTP Bearer credentials from request header.
        db: Database session.
        
    Returns:
        User: Authenticated user via API key.
        
    Raises:
        HTTPException: 401 if API key authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    try:
        # Verify API key token
        payload = verify_token(credentials.credentials, token_type="access")
        
        # Verify it's an API key token
        if payload.get("type") != "api_key":
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Look up user in database
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None or not user.is_active:
            raise credentials_exception
        
        logger.debug(f"Successfully authenticated API key for user: {user.email}")
        return user
        
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"API key authentication error: {e}")
        raise credentials_exception


# Common permission dependencies for convenience
require_device_read = require_permission("device", "read")
require_device_write = require_permission("device", "write")
require_device_delete = require_permission("device", "delete")

require_template_read = require_permission("template", "read")
require_template_write = require_permission("template", "write")
require_template_delete = require_permission("template", "delete")

require_user_read = require_permission("user", "read")
require_user_write = require_permission("user", "write")
require_user_delete = require_permission("user", "delete")

require_job_read = require_permission("job", "read")
require_job_write = require_permission("job", "write")

require_backup_read = require_permission("backup", "read")
require_backup_write = require_permission("backup", "write")
require_backup_delete = require_permission("backup", "delete")

require_alert_read = require_permission("alert", "read")
require_alert_write = require_permission("alert", "write")


def require_permissions(*permissions: tuple[str, str]):
    """
    Decorator to require multiple permissions for endpoint access.
    
    Args:
        permissions: Tuples of (resource, action) permissions required.
        
    Returns:
        Callable: Decorator function.
        
    Example:
        @require_permissions(("device", "read"), ("template", "read"))
        def get_device_templates(user: User = Depends(get_current_active_user)):
            return templates
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (assumes user parameter exists)
            user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    user = value
                    break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User context not found"
                )
            
            # SuperAdmin bypasses all permission checks
            if user.role.name == "SuperAdmin":
                return await func(*args, **kwargs)
            
            # Check all required permissions
            user_permissions = {
                (perm.resource, perm.action) 
                for perm in user.role.permissions
            }
            
            missing_permissions = []
            for resource, action in permissions:
                if (resource, action) not in user_permissions:
                    missing_permissions.append(f"{resource}:{action}")
            
            if missing_permissions:
                logger.warning(
                    f"User {user.email} lacks permissions: {missing_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator