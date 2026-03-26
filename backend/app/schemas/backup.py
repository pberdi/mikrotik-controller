"""
Backup Pydantic schemas for request/response validation.

This module provides schemas for backup-related API operations.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import Field

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams, DateRangeFilter
from ..models.backup import BackupType


class BackupBase(BaseSchema):
    """
    Base backup schema with common fields.
    """
    
    type: BackupType = Field(
        description="Backup type (export or binary)"
    )


class BackupCreateRequest(BaseSchema):
    """
    Schema for backup creation requests.
    """
    
    device_ids: List[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of device IDs to backup (max 100)"
    )
    
    type: BackupType = Field(
        description="Type of backup to create"
    )
    
    compress: Optional[bool] = Field(
        default=True,
        description="Whether to compress the backup"
    )


class BackupCreateResponse(BaseSchema):
    """
    Schema for backup creation responses.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking backup creation"
    )
    
    device_count: int = Field(
        description="Number of devices to backup"
    )
    
    type: BackupType = Field(
        description="Type of backup being created"
    )
    
    status: str = Field(
        description="Initial job status"
    )


class BackupResponse(BackupBase, UUIDSchema, TimestampSchema):
    """
    Schema for backup responses.
    """
    
    device_id: UUID = Field(
        description="Device this backup belongs to"
    )
    
    storage_path: str = Field(
        description="Path to backup file in storage"
    )
    
    size: int = Field(
        description="Backup file size in bytes"
    )
    
    checksum: str = Field(
        description="SHA-256 checksum of backup file"
    )
    
    compressed: bool = Field(
        description="Whether backup is compressed"
    )


class BackupDetailResponse(BackupResponse):
    """
    Schema for detailed backup responses.
    """
    
    # Could include additional fields like validation status, etc.
    pass


class BackupFilterParams(FilterParams, DateRangeFilter):
    """
    Schema for backup filtering parameters.
    """
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Filter by device ID"
    )
    
    type: Optional[BackupType] = Field(
        default=None,
        description="Filter by backup type"
    )
    
    compressed: Optional[bool] = Field(
        default=None,
        description="Filter by compression status"
    )


class BackupRestoreRequest(BaseSchema):
    """
    Schema for backup restore requests.
    """
    
    target_device_id: Optional[UUID] = Field(
        default=None,
        description="Target device ID (defaults to original device)"
    )
    
    force: Optional[bool] = Field(
        default=False,
        description="Force restore even if device is online"
    )


class BackupRestoreResponse(BaseSchema):
    """
    Schema for backup restore responses.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking backup restore"
    )
    
    backup_id: UUID = Field(
        description="Backup ID being restored"
    )
    
    target_device_id: UUID = Field(
        description="Device where backup will be restored"
    )
    
    status: str = Field(
        description="Initial job status"
    )


class BackupStatsResponse(BaseSchema):
    """
    Schema for backup statistics responses.
    """
    
    total_backups: int = Field(
        description="Total number of backups"
    )
    
    by_type: dict[str, int] = Field(
        description="Backup count by type"
    )
    
    total_size: int = Field(
        description="Total size of all backups in bytes"
    )
    
    compressed_backups: int = Field(
        description="Number of compressed backups"
    )
    
    recent_backups: int = Field(
        description="Number of backups created in last 24 hours"
    )