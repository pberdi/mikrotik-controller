"""
Device database model.

This module defines the Device model for MikroTik routers.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant
    from .site import Site
    from .job import Job
    from .backup import Backup
    from .alert import Alert
    from .device_credential import DeviceCredential


class DeviceStatus(str, Enum):
    """Device status enumeration."""
    UNREGISTERED = "unregistered"
    DISCOVERED = "discovered"
    PENDING_ADOPTION = "pending_adoption"
    ADOPTED = "adopted"
    MANAGED = "managed"
    OFFLINE = "offline"
    ERROR = "error"
    RETIRED = "retired"


class Device(BaseModel):
    """
    Device model for MikroTik routers.
    
    Devices belong to tenants and optionally to sites.
    """
    
    __tablename__ = "devices"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this device"
    )
    
    site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Site where this device is located"
    )
    
    hostname: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Device hostname"
    )
    
    ip_address: Mapped[str] = mapped_column(
        INET,
        nullable=False,
        index=True,
        doc="Device IP address"
    )
    
    ros_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="RouterOS version"
    )
    
    ros_major: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="RouterOS major version number"
    )
    
    architecture: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Device architecture (e.g., arm, x86)"
    )
    
    model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Device model"
    )
    
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Device serial number"
    )
    
    status: Mapped[DeviceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeviceStatus.UNREGISTERED,
        index=True,
        doc="Device status"
    )
    
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time device was seen online"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="devices",
        doc="Tenant that owns this device"
    )
    
    site: Mapped[Optional["Site"]] = relationship(
        "Site",
        back_populates="devices",
        doc="Site where this device is located"
    )
    
    credentials: Mapped[Optional["DeviceCredential"]] = relationship(
        "DeviceCredential",
        back_populates="device",
        cascade="all, delete-orphan",
        uselist=False,
        doc="Device credentials"
    )
    
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="device",
        cascade="all, delete-orphan",
        doc="Jobs executed on this device"
    )
    
    backups: Mapped[list["Backup"]] = relationship(
        "Backup",
        back_populates="device",
        cascade="all, delete-orphan",
        doc="Backups of this device"
    )
    
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="device",
        cascade="all, delete-orphan",
        doc="Alerts for this device"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the device."""
        return f"<Device(id={self.id}, hostname='{self.hostname}', ip='{self.ip_address}', status='{self.status}')>"