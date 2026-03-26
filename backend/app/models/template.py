"""
Template database model.

This module defines the Template model for configuration templates.
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant


class TemplateType(str, Enum):
    """Template type enumeration."""
    DECLARATIVE = "declarative"
    SCRIPT = "script"


class Template(BaseModel):
    """
    Template model for configuration templates.
    
    Templates belong to tenants and contain Jinja2 configuration templates.
    """
    
    __tablename__ = "templates"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this template"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Template name"
    )
    
    type: Mapped[TemplateType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Template type (declarative, script)"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Template content (Jinja2 syntax)"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="templates",
        doc="Tenant that owns this template"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the template."""
        return f"<Template(id={self.id}, name='{self.name}', type='{self.type}', tenant_id={self.tenant_id})>"