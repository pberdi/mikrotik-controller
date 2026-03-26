"""
User database model.

This module defines the User model for authentication and authorization.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant
    from .role import Role
    from .audit_log import AuditLog


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Users belong to tenants and have roles that define their permissions.
    """
    
    __tablename__ = "users"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this user belongs to"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="User email address (used for login)"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )
    
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
        index=True,
        doc="Role assigned to this user"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether user account is active"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
        doc="Tenant this user belongs to"
    )
    
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        doc="Role assigned to this user"
    )
    
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        doc="Audit logs for this user's actions"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the user."""
        return f"<User(id={self.id}, email='{self.email}', tenant_id={self.tenant_id}, active={self.is_active})>"