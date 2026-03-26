"""
Job database model.

This module defines the Job model for asynchronous task tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant
    from .device import Device


class JobType(str, Enum):
    """Job type enumeration."""
    INVENTORY = "inventory"
    BACKUP = "backup"
    TEMPLATE_APPLY = "template_apply"
    COMMAND = "command"
    CONNECTIVITY_CHECK = "connectivity_check"


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """
    Job model for tracking asynchronous tasks.
    
    Jobs belong to tenants and optionally to specific devices.
    """
    
    __tablename__ = "jobs"
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this job"
    )
    
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Device this job operates on"
    )
    
    type: Mapped[JobType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Job type"
    )
    
    status: Mapped[JobStatus] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
        doc="Job status"
    )
    
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Celery task ID for tracking"
    )
    
    result: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Job result data"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if job failed"
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When job execution started"
    )
    
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When job execution finished"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="jobs",
        doc="Tenant that owns this job"
    )
    
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="jobs",
        doc="Device this job operates on"
    )
    
    def __repr__(self) -> str:
        """Return string representation of the job."""
        return f"<Job(id={self.id}, type='{self.type}', status='{self.status}', tenant_id={self.tenant_id})>"