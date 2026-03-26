"""
Role database model.

This module defines the Role model for role-based access control (RBAC).
"""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .permission import Permission


class Role(BaseModel):
    """
    Role model for role-based access control.
    
    Roles define sets of permissions that can be assigned to users.
    """
    
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Role name (e.g., SuperAdmin, TenantAdmin)"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Role description"
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
        doc="Users assigned to this role"
    )
    
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        back_populates="role",
        cascade="all, delete-orphan",
        doc="Permissions granted by this role"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the role."""
        return f"<Role(id={self.id}, name='{self.name}')>"