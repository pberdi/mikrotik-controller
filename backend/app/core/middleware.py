"""
Custom middleware for the FastAPI application.

This module provides middleware for tenant isolation, request tracking,
and other cross-cutting concerns.
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from jose.exceptions import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from .security import verify_token
from ..models import User

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for multi-tenant isolation.
    
    This middleware extracts tenant information from authenticated users
    and injects it into the request state for downstream use by services
    and database queries.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject tenant context.
        
        Args:
            request: FastAPI request object.
            call_next: Next middleware/endpoint in chain.
            
        Returns:
            Response: HTTP response.
        """
        # Initialize tenant context
        request.state.tenant_id = None
        request.state.user_id = None
        request.state.is_superadmin = False
        
        # Extract tenant information from JWT token if present
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            
            if scheme.lower() == "bearer" and token:
                try:
                    # Verify token and extract user information
                    payload = verify_token(token, token_type="access")
                    user_id = payload.get("sub")
                    
                    if user_id:
                        # Store user ID for potential database lookup
                        request.state.user_id = user_id
                        
                        # Extract tenant_id from token claims if available
                        tenant_id = payload.get("tenant_id")
                        if tenant_id:
                            request.state.tenant_id = tenant_id
                        
                        # Note: We don't do database lookup here to avoid
                        # database dependency in middleware. The actual user
                        # and tenant lookup happens in the authentication
                        # dependencies where we have database access.
                        
                        logger.debug(f"Extracted user ID from token: {user_id}")
                
                except JWTError:
                    # Invalid token - let authentication dependencies handle this
                    logger.debug("Invalid token in middleware - will be handled by auth dependencies")
                except Exception as e:
                    logger.error(f"Error processing token in middleware: {e}")
        
        # Process request
        response = await call_next(request)
        
        return response


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracking and logging.
    
    This middleware adds request IDs, tracks request duration,
    and logs request information for debugging and monitoring.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with tracking and logging.
        
        Args:
            request: FastAPI request object.
            call_next: Next middleware/endpoint in chain.
            
        Returns:
            Response: HTTP response with tracking headers.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}] from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{request_id}] {response.status_code} in {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration = time.time() - start_time
            
            # Log request error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{request_id}] error: {e} in {duration:.3f}s"
            )
            
            # Re-raise exception to be handled by FastAPI
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    
    This middleware adds common security headers to protect against
    various web vulnerabilities.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: FastAPI request object.
            call_next: Next middleware/endpoint in chain.
            
        Returns:
            Response: HTTP response with security headers.
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add HSTS header for HTTPS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def inject_tenant_context(request: Request, user: User) -> None:
    """
    Inject tenant context into request state.
    
    This function is called by authentication dependencies to inject
    tenant information after user lookup.
    
    Args:
        request: FastAPI request object.
        user: Authenticated user object.
    """
    request.state.tenant_id = str(user.tenant_id)
    request.state.user_id = str(user.id)
    request.state.is_superadmin = user.role.name == "SuperAdmin"
    
    logger.debug(
        f"Injected tenant context: tenant_id={user.tenant_id}, "
        f"user_id={user.id}, is_superadmin={request.state.is_superadmin}"
    )


def get_tenant_context(request: Request) -> dict:
    """
    Get tenant context from request state.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        dict: Tenant context information.
    """
    return {
        "tenant_id": getattr(request.state, "tenant_id", None),
        "user_id": getattr(request.state, "user_id", None),
        "is_superadmin": getattr(request.state, "is_superadmin", False),
        "request_id": getattr(request.state, "request_id", None),
    }