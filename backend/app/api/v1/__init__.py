"""
API v1 package.

This package contains all v1 API routes and router configuration.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .devices import router as devices_router
# from .templates import router as templates_router
# from .jobs import router as jobs_router
# from .users import router as users_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(devices_router, prefix="/devices", tags=["Devices"])
# api_router.include_router(templates_router, prefix="/templates", tags=["Templates"])
# api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
# api_router.include_router(users_router, prefix="/users", tags=["Users"])

__all__ = ["api_router"]