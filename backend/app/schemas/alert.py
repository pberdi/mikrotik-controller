"""
Alert Pydantic schemas for request/response validation.

This module provides schemas for alert-related API operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams, DateRangeFilter
from ..models.alert import AlertSeverity, AlertStatus


class AlertBase(BaseSchema):
    """
    Base alert schema with common fields.
    """
    
    severity: AlertSeverity = Field(
        description="Alert severity (info, warning, critical)"
    )
    
    message: str = Field(
        min_length=1,
        max_length=1000,
        description="Alert message"
    )


class AlertCreate(AlertBase):
    """
    Schema for alert creation requests.
    """
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Device this alert relates to"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate alert message."""
        if not v.strip():
            raise ValueError("Alert message cannot be empty")
        return v.strip()


class AlertUpdate(BaseSchema):
    """
    Schema for alert update requests.
    """
    
    status: Optional[AlertStatus] = Field(
        default=None,
        description="Alert status (active, acknowledged, resolved)"
    )
    
    message: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Updated alert message"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        """Validate alert message if provided."""
        if v is not None and not v.strip():
            raise ValueError("Alert message cannot be empty")
        return v.strip() if v else v


class AlertResponse(AlertBase, UUIDSchema, TimestampSchema):
    """
    Schema for alert responses.
    """
    
    tenant_id: UUID = Field(
        description="Tenant that owns this alert"
    )
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Device this alert relates to"
    )
    
    status: AlertStatus = Field(
        description="Alert status"
    )
    
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        description="When alert was acknowledged"
    )
    
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When alert was resolved"
    )


class AlertDetailResponse(AlertResponse):
    """
    Schema for detailed alert responses.
    """
    
    # Could include additional fields like related events, etc.
    pass


class AlertFilterParams(FilterParams, DateRangeFilter):
    """
    Schema for alert filtering parameters.
    """
    
    severity: Optional[AlertSeverity] = Field(
        default=None,
        description="Filter by alert severity"
    )
    
    status: Optional[AlertStatus] = Field(
        default=None,
        description="Filter by alert status"
    )
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Filter by device ID"
    )


class AlertAcknowledgeRequest(BaseSchema):
    """
    Schema for alert acknowledgment requests.
    """
    
    note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Acknowledgment note"
    )


class AlertAcknowledgeResponse(BaseSchema):
    """
    Schema for alert acknowledgment responses.
    """
    
    alert_id: UUID = Field(
        description="Alert ID that was acknowledged"
    )
    
    status: AlertStatus = Field(
        description="Updated alert status"
    )
    
    acknowledged_at: datetime = Field(
        description="When alert was acknowledged"
    )


class AlertStatsResponse(BaseSchema):
    """
    Schema for alert statistics responses.
    """
    
    total_alerts: int = Field(
        description="Total number of alerts"
    )
    
    active: int = Field(
        description="Number of active alerts"
    )
    
    acknowledged: int = Field(
        description="Number of acknowledged alerts"
    )
    
    resolved: int = Field(
        description="Number of resolved alerts"
    )
    
    by_severity: dict[str, int] = Field(
        description="Alert count by severity"
    )
    
    critical_alerts: int = Field(
        description="Number of critical alerts"
    )
    
    recent_alerts: int = Field(
        description="Number of alerts created in last 24 hours"
    )