"""
Alert database model.

This module defines the Alert model for system alerts and notifications.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant
    from .device import Device


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(BaseModel):
    """
    Alert model for system alerts and notifications.
    
    Alerts belong to tenants and optionally to specific devices.
    """
    
    __tablename__ = "alerts"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this alert"
    )
    
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Device this alert relates to"
    )
    
    severity: Mapped[AlertSeverity] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Alert severity (info, warning, critical)"
    )
    
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Alert message"
    )
    
    status: Mapped[AlertStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AlertStatus.ACTIVE,
        index=True,
        doc="Alert status (active, acknowledged, resolved)"
    )
    
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When alert was acknowledged"
    )
    
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When alert was resolved"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="alerts",
        doc="Tenant that owns this alert"
    )
    
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="alerts",
        doc="Device this alert relates to"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the alert."""
        return f"<Alert(id={self.id}, severity='{self.severity}', status='{self.status}', tenant_id={self.tenant_id})>"