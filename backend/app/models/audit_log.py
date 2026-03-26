"""
Audit log database model.

This module defines the AuditLog model for tracking user and system actions.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin

if TYPE_CHECKING:
    from .tenant import Tenant
    from .user import User
    from .device import Device


class AuditLog(Base, UUIDMixin):
    """
    Audit log model for tracking user and system actions.
    
    Audit logs provide a complete trail of all actions performed in the system
    for compliance, security, and troubleshooting purposes.
    """
    
    __tablename__ = "audit_logs"
    
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Tenant this audit log belongs to"
    )
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User who performed the action"
    )
    
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Device the action was performed on"
    )
    
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Action performed (e.g., device_create, user_login)"
    )
    
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Type of resource affected (e.g., device, user, template)"
    )
    
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the resource affected"
    )
    
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Result of the action (success, failure, error)"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        doc="IP address of the client"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string of the client"
    )
    
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Request ID for correlating related log entries"
    )
    
    before_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Value before the change (for updates)"
    )
    
    after_value: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Value after the change (for updates)"
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
        doc="When the action occurred"
    )
    
    # Relationships
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant",
        doc="Tenant this audit log belongs to"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        doc="User who performed the action"
    )
    
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        doc="Device the action was performed on"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the audit log."""
        return f"<AuditLog(id={self.id}, action='{self.action}', result='{self.result}', timestamp={self.timestamp})>"