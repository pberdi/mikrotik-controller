"""
SQLAlchemy base models and mixins.

This module provides the declarative base and common mixins used by all
database models in the application.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class.
    
    All database models inherit from this base class.
    """
    pass


class UUIDMixin:
    """
    Mixin that provides UUID primary key.
    
    This mixin adds a UUID primary key field to any model that includes it.
    The UUID is automatically generated using uuid4().
    """
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Primary key UUID"
    )


class TimestampMixin:
    """
    Mixin that provides created_at and updated_at timestamp fields.
    
    This mixin adds automatic timestamp tracking to any model that includes it.
    - created_at: Set when the record is first created
    - updated_at: Updated automatically whenever the record is modified
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class that combines Base, UUIDMixin, and TimestampMixin.
    
    This is the recommended base class for most database models as it provides:
    - UUID primary key
    - Automatic timestamp tracking
    - SQLAlchemy declarative base functionality
    """
    
    __abstract__ = True
    
    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model with all column values.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Legacy declarative_base for backward compatibility
# New models should inherit from BaseModel instead
DeclarativeBase = declarative_base()