"""
Permission database model.

This module defines the Permission model for role-based access control (RBAC).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .role import Role


class Permission(BaseModel):
    """
    Permission model for role-based access control.
    
    Permissions define what actions a role can perform on what resources.
    """
    
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "resource", "action", name="uq_role_resource_action"),
    )
    
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Role this permission belongs to"
    )
    
    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Resource type (e.g., device, template, user)"
    )
    
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Action allowed (e.g., create, read, update, delete)"
    )
    
    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="permissions",
        doc="Role this permission belongs to"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the permission."""
        return f"<Permission(id={self.id}, role_id={self.role_id}, resource='{self.resource}', action='{self.action}')>"