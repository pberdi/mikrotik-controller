"""
Device management API endpoints.

This module provides endpoints for device CRUD operations, command execution,
and device management functionality.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...dependencies import get_current_active_user, get_tenant_context
from ...models.user import User
from ...schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceDetailResponse,
    DeviceFilterParams,
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceStatsResponse
)
from ...schemas.common import PaginatedResponse, SuccessResponse
from ...services.device_service import DeviceService
from ...services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Devices"])


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Create a new device (device adoption).
    
    This endpoint creates a new device record with encrypted credentials
    and enqueues a connectivity check job.
    
    Args:
        device_data: Device creation data including credentials.
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        DeviceResponse: Created device information.
        
    Raises:
        HTTPException: 400 if validation fails, 403 if unauthorized.
    """
    # Initialize services
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    audit_service = AuditService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        request=request
    )
    
    try:
        # Validate device data
        if not device_data.name or not device_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device name is required"
            )
        
        if not device_data.host or not device_data.host.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device host is required"
            )
        
        # Create device
        device = device_service.create_device(device_data)
        
        # TODO: Enqueue connectivity check job (Task 11.2)
        # job_service.enqueue_connectivity_check(device.id)
        
        # Commit transaction
        db.commit()
        
        logger.info(f"Device created: {device.id} by user {current_user.email}")
        
        return device
        
    except ValueError as e:
        db.rollback()
        logger.warning(f"Device creation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Device creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device"
        )


@router.get("", response_model=PaginatedResponse[DeviceResponse])
async def list_devices(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by device status"),
    site_id: Optional[UUID] = Query(None, description="Filter by site ID"),
    online_only: Optional[bool] = Query(None, description="Show only online devices"),
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    List devices with pagination and filtering.
    
    Args:
        request: FastAPI request object.
        page: Page number (1-based).
        page_size: Number of items per page.
        status: Optional status filter.
        site_id: Optional site ID filter.
        online_only: Optional filter for online devices only.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        PaginatedResponse: Paginated list of devices.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Build filters
        filters = DeviceFilterParams(
            status=status,
            site_id=site_id,
            online_only=online_only
        )
        
        # List devices
        result = device_service.list_devices(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        # Commit transaction (for audit logs)
        db.commit()
        
        return PaginatedResponse(
            items=result["items"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Device listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list devices"
        )


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    device_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Get device by ID.
    
    Args:
        device_id: Device ID.
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        DeviceDetailResponse: Device details.
        
    Raises:
        HTTPException: 404 if device not found.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Get device
        device = device_service.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        # Commit transaction (for audit logs)
        db.commit()
        
        return device
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Device retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Update device.
    
    Args:
        device_id: Device ID.
        device_data: Updated device data.
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        DeviceResponse: Updated device.
        
    Raises:
        HTTPException: 404 if device not found, 400 if validation fails.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Update device
        device = device_service.update_device(device_id, device_data)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        # Commit transaction
        db.commit()
        
        logger.info(f"Device updated: {device_id} by user {current_user.email}")
        
        return device
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        logger.warning(f"Device update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Device update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Delete device.
    
    Args:
        device_id: Device ID.
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Raises:
        HTTPException: 404 if device not found.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Delete device
        deleted = device_service.delete_device(device_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        # Commit transaction
        db.commit()
        
        logger.info(f"Device deleted: {device_id} by user {current_user.email}")
        
        return None
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Device deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device"
        )


@router.post("/{device_id}/command", response_model=DeviceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_device_command(
    device_id: UUID,
    command_data: DeviceCommandRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Execute command on device.
    
    This endpoint enqueues a command execution job and returns the job ID
    for tracking. The actual command execution happens asynchronously.
    
    Args:
        device_id: Device ID.
        command_data: Command to execute.
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        DeviceCommandResponse: Job ID for tracking command execution.
        
    Raises:
        HTTPException: 404 if device not found.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Verify device exists and is accessible
        device = device_service.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        # TODO: Enqueue command execution job
        # job = job_service.enqueue_command_execution(device_id, command_data.command)
        # For now, return a placeholder response
        
        # Commit transaction
        db.commit()
        
        logger.info(f"Command execution enqueued for device {device_id} by user {current_user.email}")
        
        # Placeholder response
        return DeviceCommandResponse(
            job_id="00000000-0000-0000-0000-000000000000",  # Placeholder
            status="pending",
            message="Command execution job enqueued (placeholder - job system not yet implemented)"
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Command execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute command"
        )


@router.get("/stats/summary", response_model=DeviceStatsResponse)
async def get_device_stats(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Get device statistics for the current tenant.
    
    Args:
        request: FastAPI request object.
        current_user: Current authenticated user.
        tenant_id: Current tenant ID.
        db: Database session.
        
    Returns:
        DeviceStatsResponse: Device statistics.
    """
    # Initialize device service
    device_service = DeviceService(
        db=db,
        tenant_id=tenant_id,
        user_id=str(current_user.id),
        is_superadmin=(current_user.role.name == "SuperAdmin")
    )
    
    try:
        # Get device stats
        stats = device_service.get_device_stats()
        
        # Commit transaction (for audit logs)
        db.commit()
        
        return DeviceStatsResponse(**stats)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Device stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device statistics"
        )
