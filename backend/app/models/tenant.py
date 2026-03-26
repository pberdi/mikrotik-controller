"""
Tenant database model.

This module defines the Tenant model for multi-tenant isolation.
"""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .site import Site
    from .device import Device
    from .template import Template
    from .job import Job
    from .alert import Alert
    from .user import User


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Tenant(BaseModel):
    """
    Tenant model for multi-tenant isolation.
    
    Each tenant represents a separate customer organization with isolated data.
    """
    
    __tablename__ = "tenants"
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Tenant organization name"
    )
    
    status: Mapped[TenantStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TenantStatus.ACTIVE,
        index=True,
        doc="Tenant status (active, suspended)"
    )
    
    # Relationships
    sites: Mapped[list["Site"]] = relationship(
        "Site",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Sites belonging to this tenant"
    )
    
    devices: Mapped[list["Device"]] = relationship(
        "Device",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Devices belonging to this tenant"
    )
    
    templates: Mapped[list["Template"]] = relationship(
        "Template",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Templates belonging to this tenant"
    )
    
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Jobs belonging to this tenant"
    )
    
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Alerts belonging to this tenant"
    )
    
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Users belonging to this tenant"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the tenant."""
        return f"<Tenant(id={self.id}, name='{self.name}', status='{self.status}')>"