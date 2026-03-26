"""
Site database model.

This module defines the Site model for organizing devices by location.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant
    from .device import Device


class Site(BaseModel):
    """
    Site model for organizing devices by physical location.
    
    Sites belong to tenants and contain devices.
    """
    
    __tablename__ = "sites"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this site"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Site name"
    )
    
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Physical address of the site"
    )
    
    site_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional site metadata as JSON"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="sites",
        doc="Tenant that owns this site"
    )
    
    devices: Mapped[list["Device"]] = relationship(
        "Device",
        back_populates="site",
        cascade="all, delete-orphan",
        doc="Devices at this site"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the site."""
        return f"<Site(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"