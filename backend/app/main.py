"""
FastAPI application factory and main entry point.

This module creates and configures the FastAPI application with all
necessary middleware, routers, and dependencies.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.database import init_db, close_db
from .core.middleware import (
    TenantIsolationMiddleware,
    RequestTrackingMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting MikroTik Controller API")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MikroTik Controller API")
    
    # Close database connections
    close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance.
    """
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=settings.app.app_name,
        version=settings.app.app_version,
        description="MikroTik Controller Platform - Backend API",
        docs_url="/docs" if settings.app.environment != "production" else None,
        redoc_url="/redoc" if settings.app.environment != "production" else None,
        openapi_url="/openapi.json" if settings.app.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=settings.app.cors_credentials,
        allow_methods=settings.app.cors_methods,
        allow_headers=settings.app.cors_headers,
    )
    
    # Add custom middleware (order matters - last added runs first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TenantIsolationMiddleware)
    app.add_middleware(RequestTrackingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register API routers
    register_routers(app)
    
    logger.info(f"FastAPI application created for environment: {settings.app.environment}")
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers.
    
    Args:
        app: FastAPI application instance.
    """
    from fastapi import HTTPException, status
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import IntegrityError
    from pydantic import ValidationError
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "type": error["type"],
                "message": error["msg"],
                "field": ".".join(str(x) for x in error["loc"]),
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "type": error["type"],
                "message": error["msg"],
                "field": ".".join(str(x) for x in error["loc"]),
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity constraint violations."""
        logger.error(f"Database integrity error: {exc}")
        
        # Parse common constraint violations
        error_msg = str(exc.orig) if exc.orig else str(exc)
        
        if "unique constraint" in error_msg.lower():
            detail = "A record with this information already exists"
        elif "foreign key constraint" in error_msg.lower():
            detail = "Referenced record does not exist"
        elif "not null constraint" in error_msg.lower():
            detail = "Required field is missing"
        else:
            detail = "Database constraint violation"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            },
        )


def register_routers(app: FastAPI) -> None:
    """
    Register API routers with the application.
    
    Args:
        app: FastAPI application instance.
    """
    # Import routers
    from .api.v1 import api_router
    
    # Register API v1 router
    app.include_router(api_router, prefix=settings.app.api_prefix)
    
    # Add health check endpoints
    register_health_endpoints(app)
    
    logger.info("API routers registered")


def register_health_endpoints(app: FastAPI) -> None:
    """
    Register health check endpoints.
    
    Args:
        app: FastAPI application instance.
    """
    from datetime import datetime
    from fastapi import status
    from .core.database import check_db_health
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app.app_version,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check with dependency verification."""
        # Check database connectivity
        db_health = check_db_health()
        
        # TODO: Add Redis health check when Redis is implemented
        redis_health = {"status": "healthy", "redis": "not_implemented"}
        
        dependencies = {
            "database": db_health["database"],
            "redis": redis_health["redis"],
        }
        
        # Determine overall status
        all_healthy = all(
            dep_status in ["healthy", "connected", "not_implemented"] 
            for dep_status in dependencies.values()
        )
        
        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_healthy else "not_ready",
                "dependencies": dependencies,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Liveness check for container orchestration."""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Create application instance
app = create_app()


# Add version header middleware
@app.middleware("http")
async def add_version_header(request: Request, call_next):
    """Add API version to response headers."""
    response = await call_next(request)
    response.headers["X-API-Version"] = settings.app.app_version
    return response


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )