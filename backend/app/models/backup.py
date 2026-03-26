"""
Backup database model.

This module defines the Backup model for device configuration backups.
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .device import Device


class BackupType(str, Enum):
    """Backup type enumeration."""
    EXPORT = "export"
    BINARY = "binary"


class Backup(BaseModel):
    """
    Backup model for device configuration backups.
    
    Backups belong to devices and store configuration data.
    """
    
    __tablename__ = "backups"
    
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Device this backup belongs to"
    )
    
    type: Mapped[BackupType] = mapped_column(
        String(20),
        nullable=False,
        doc="Backup type (export, binary)"
    )
    
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Path to backup file in storage"
    )
    
    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Backup file size in bytes"
    )
    
    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA-256 checksum of backup file"
    )
    
    compressed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether backup is compressed"
    )
    
    # Relationships
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="backups",
        doc="Device this backup belongs to"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the backup."""
        return f"<Backup(id={self.id}, device_id={self.device_id}, type='{self.type}', size={self.size})>"