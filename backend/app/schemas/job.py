"""
Job Pydantic schemas for request/response validation.

This module provides schemas for job-related API operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams, DateRangeFilter
from ..models.job import JobStatus, JobType


class JobBase(BaseSchema):
    """
    Base job schema with common fields.
    """
    
    type: JobType = Field(
        description="Job type"
    )
    
    status: JobStatus = Field(
        description="Job status"
    )


class JobResponse(JobBase, UUIDSchema, TimestampSchema):
    """
    Schema for job responses.
    """
    
    tenant_id: UUID = Field(
        description="Tenant that owns this job"
    )
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Device this job operates on"
    )
    
    celery_task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID for tracking"
    )
    
    result: Optional[str] = Field(
        default=None,
        description="Job result data"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    
    started_at: Optional[datetime] = Field(
        default=None,
        description="When job execution started"
    )
    
    finished_at: Optional[datetime] = Field(
        default=None,
        description="When job execution finished"
    )


class JobDetailResponse(JobResponse):
    """
    Schema for detailed job responses.
    """
    
    # Could include additional fields like logs, progress, etc.
    pass


class JobFilterParams(FilterParams, DateRangeFilter):
    """
    Schema for job filtering parameters.
    """
    
    status: Optional[JobStatus] = Field(
        default=None,
        description="Filter by job status"
    )
    
    type: Optional[JobType] = Field(
        default=None,
        description="Filter by job type"
    )
    
    device_id: Optional[UUID] = Field(
        default=None,
        description="Filter by device ID"
    )


class JobCancelRequest(BaseSchema):
    """
    Schema for job cancellation requests.
    """
    
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for cancellation"
    )


class JobCancelResponse(BaseSchema):
    """
    Schema for job cancellation responses.
    """
    
    job_id: UUID = Field(
        description="Job ID that was cancelled"
    )
    
    status: JobStatus = Field(
        description="Updated job status"
    )
    
    message: str = Field(
        description="Cancellation result message"
    )


class JobLogsResponse(BaseSchema):
    """
    Schema for job logs responses.
    """
    
    job_id: UUID = Field(
        description="Job ID"
    )
    
    logs: list[str] = Field(
        description="Job execution logs"
    )
    
    last_updated: datetime = Field(
        description="When logs were last updated"
    )


class JobStatsResponse(BaseSchema):
    """
    Schema for job statistics responses.
    """
    
    total_jobs: int = Field(
        description="Total number of jobs"
    )
    
    by_status: dict[str, int] = Field(
        description="Job count by status"
    )
    
    by_type: dict[str, int] = Field(
        description="Job count by type"
    )
    
    running_jobs: int = Field(
        description="Number of currently running jobs"
    )
    
    failed_jobs: int = Field(
        description="Number of failed jobs"
    )