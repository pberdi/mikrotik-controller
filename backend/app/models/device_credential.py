"""
Device credential database model.

This module defines the DeviceCredential model for storing encrypted device credentials.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .device import Device


class DeviceCredential(BaseModel):
    """
    Device credential model for storing encrypted device credentials.
    
    Credentials are encrypted using the Secret Vault before storage.
    """
    
    __tablename__ = "device_credentials"
    
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="Device these credentials belong to"
    )
    
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Username for device access"
    )
    
    password_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Encrypted password for device access"
    )
    
    private_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="SSH private key for key-based authentication"
    )
    
    # Relationships
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="credentials",
        doc="Device these credentials belong to"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the device credential."""
        return f"<DeviceCredential(id={self.id}, device_id={self.device_id}, username='{self.username}')>"