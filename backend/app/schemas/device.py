"""
Device Pydantic schemas for request/response validation.

This module provides schemas for device-related API operations including
device creation, updates, and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator, IPvAnyAddress

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams
from ..models.device import DeviceStatus


class DeviceBase(BaseSchema):
    """
    Base device schema with common fields.
    
    Contains fields that are common across device creation and update operations.
    """
    
    hostname: str = Field(
        min_length=1,
        max_length=255,
        description="Device hostname",
        examples=["router-01", "mikrotik-main"]
    )
    
    ip_address: IPvAnyAddress = Field(
        description="Device IP address",
        examples=["192.168.1.1", "10.0.0.1"]
    )
    
    site_id: Optional[UUID] = Field(
        default=None,
        description="Site where device is located"
    )


class DeviceCreate(DeviceBase):
    """
    Schema for device creation requests.
    
    Includes credentials and other fields needed for device adoption.
    """
    
    username: str = Field(
        min_length=1,
        max_length=255,
        description="Username for device access",
        examples=["admin"]
    )
    
    password: str = Field(
        min_length=1,
        max_length=255,
        description="Password for device access"
    )
    
    private_key: Optional[str] = Field(
        default=None,
        description="SSH private key for key-based authentication"
    )
    
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """Validate hostname format."""
        if not v.strip():
            raise ValueError("Hostname cannot be empty")
        
        # Basic hostname validation (alphanumeric, hyphens, dots)
        import re
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Hostname contains invalid characters")
        
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty."""
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class DeviceUpdate(BaseSchema):
    """
    Schema for device update requests.
    
    All fields are optional for partial updates.
    """
    
    hostname: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Device hostname"
    )
    
    ip_address: Optional[IPvAnyAddress] = Field(
        default=None,
        description="Device IP address"
    )
    
    site_id: Optional[UUID] = Field(
        default=None,
        description="Site where device is located"
    )
    
    status: Optional[DeviceStatus] = Field(
        default=None,
        description="Device status"
    )
    
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v: Optional[str]) -> Optional[str]:
        """Validate hostname format if provided."""
        if v is None:
            return v
        
        if not v.strip():
            raise ValueError("Hostname cannot be empty")
        
        # Basic hostname validation
        import re
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Hostname contains invalid characters")
        
        return v.strip()


class DeviceCredentialUpdate(BaseSchema):
    """
    Schema for updating device credentials.
    
    Separate schema for credential updates to handle sensitive data properly.
    """
    
    username: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Username for device access"
    )
    
    password: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Password for device access"
    )
    
    private_key: Optional[str] = Field(
        default=None,
        description="SSH private key for key-based authentication"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class DeviceResponse(DeviceBase, UUIDSchema, TimestampSchema):
    """
    Schema for device responses.
    
    Includes all device information except sensitive credentials.
    """
    
    tenant_id: UUID = Field(
        description="Tenant that owns this device"
    )
    
    ros_version: Optional[str] = Field(
        default=None,
        description="RouterOS version"
    )
    
    ros_major: Optional[int] = Field(
        default=None,
        description="RouterOS major version number"
    )
    
    architecture: Optional[str] = Field(
        default=None,
        description="Device architecture"
    )
    
    model: Optional[str] = Field(
        default=None,
        description="Device model"
    )
    
    serial_number: Optional[str] = Field(
        default=None,
        description="Device serial number"
    )
    
    status: DeviceStatus = Field(
        description="Device status"
    )
    
    last_seen: Optional[datetime] = Field(
        default=None,
        description="Last time device was seen online"
    )


class DeviceListResponse(DeviceResponse):
    """
    Schema for device list responses.
    
    Optimized version of DeviceResponse for list operations.
    """
    pass


class DeviceDetailResponse(DeviceResponse):
    """
    Schema for detailed device responses.
    
    Includes additional information for single device queries.
    """
    
    # Could include additional fields like recent jobs, alerts, etc.
    pass


class DeviceFilterParams(FilterParams):
    """
    Schema for device filtering parameters.
    
    Extends base FilterParams with device-specific filters.
    """
    
    status: Optional[DeviceStatus] = Field(
        default=None,
        description="Filter by device status"
    )
    
    site_id: Optional[UUID] = Field(
        default=None,
        description="Filter by site ID"
    )
    
    ros_version: Optional[str] = Field(
        default=None,
        description="Filter by RouterOS version"
    )
    
    model: Optional[str] = Field(
        default=None,
        description="Filter by device model"
    )
    
    online_only: Optional[bool] = Field(
        default=None,
        description="Filter to show only online devices"
    )


class DeviceCommandRequest(BaseSchema):
    """
    Schema for device command execution requests.
    
    Used for executing RouterOS commands on devices.
    """
    
    command: str = Field(
        min_length=1,
        max_length=1000,
        description="RouterOS command to execute",
        examples=["/system resource print", "/interface print"]
    )
    
    timeout: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Command timeout in seconds (max 300)"
    )
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate command format."""
        if not v.strip():
            raise ValueError("Command cannot be empty")
        
        # Basic validation - RouterOS commands typically start with /
        command = v.strip()
        if not command.startswith('/'):
            raise ValueError("RouterOS commands should start with '/'")
        
        return command


class DeviceCommandResponse(BaseSchema):
    """
    Schema for device command execution responses.
    
    Returns job information for tracking command execution.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking command execution"
    )
    
    device_id: UUID = Field(
        description="Device ID where command will be executed"
    )
    
    command: str = Field(
        description="Command that will be executed"
    )
    
    status: str = Field(
        description="Initial job status"
    )


class DeviceStatsResponse(BaseSchema):
    """
    Schema for device statistics responses.
    
    Provides aggregate statistics about devices.
    """
    
    total_devices: int = Field(
        description="Total number of devices"
    )
    
    by_status: dict[str, int] = Field(
        description="Device count by status"
    )
    
    by_model: dict[str, int] = Field(
        description="Device count by model"
    )
    
    online_devices: int = Field(
        description="Number of online devices"
    )
    
    offline_devices: int = Field(
        description="Number of offline devices"
    )