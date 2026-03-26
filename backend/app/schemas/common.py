"""
Common Pydantic schemas for request/response validation.

This module provides common schemas used across multiple API endpoints
including pagination, error responses, and base schemas.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

# Type variable for generic schemas
T = TypeVar('T')


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.
    
    All other schemas should inherit from this base class to ensure
    consistent configuration across the application.
    """
    
    model_config = ConfigDict(
        # Allow population by field name or alias
        populate_by_name=True,
        # Validate assignment to fields
        validate_assignment=True,
        # Use enum values instead of names
        use_enum_values=True,
        # Allow extra fields to be ignored
        extra='ignore'
    )


class TimestampSchema(BaseSchema):
    """
    Schema mixin for timestamp fields.
    
    Provides created_at and updated_at fields for resources that track timestamps.
    """
    
    created_at: datetime = Field(
        description="Timestamp when the resource was created"
    )
    updated_at: datetime = Field(
        description="Timestamp when the resource was last updated"
    )


class UUIDSchema(BaseSchema):
    """
    Schema mixin for UUID primary key.
    
    Provides id field for resources that use UUID primary keys.
    """
    
    id: UUID = Field(
        description="Unique identifier for the resource"
    )


class PaginationParams(BaseSchema):
    """
    Schema for pagination query parameters.
    
    Used to validate pagination parameters in list endpoints.
    """
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )


class PaginationMetadata(BaseSchema):
    """
    Schema for pagination metadata in responses.
    
    Provides information about the current page and total results.
    """
    
    total_count: int = Field(
        description="Total number of items across all pages"
    )
    page: int = Field(
        description="Current page number"
    )
    page_size: int = Field(
        description="Number of items per page"
    )
    total_pages: int = Field(
        description="Total number of pages"
    )
    has_next: bool = Field(
        description="Whether there is a next page"
    )
    has_prev: bool = Field(
        description="Whether there is a previous page"
    )


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Generic schema for paginated responses.
    
    Wraps a list of items with pagination metadata.
    """
    
    items: List[T] = Field(
        description="List of items for the current page"
    )
    pagination: PaginationMetadata = Field(
        description="Pagination metadata"
    )


class ErrorDetail(BaseSchema):
    """
    Schema for error detail information.
    
    Provides structured error information for API responses.
    """
    
    type: str = Field(
        description="Error type or category"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    field: Optional[str] = Field(
        default=None,
        description="Field name if error is field-specific"
    )
    code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code"
    )


class ErrorResponse(BaseSchema):
    """
    Schema for error responses.
    
    Provides consistent error response format across all endpoints.
    """
    
    detail: str = Field(
        description="Main error message"
    )
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Detailed error information"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )


class ValidationErrorResponse(ErrorResponse):
    """
    Schema for validation error responses.
    
    Extends ErrorResponse with validation-specific information.
    """
    
    detail: str = Field(
        default="Validation error",
        description="Main error message"
    )


class SuccessResponse(BaseSchema):
    """
    Schema for simple success responses.
    
    Used for operations that don't return specific data.
    """
    
    message: str = Field(
        description="Success message"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )


class HealthCheckResponse(BaseSchema):
    """
    Schema for health check responses.
    
    Provides system health status information.
    """
    
    status: str = Field(
        description="Overall health status"
    )
    version: Optional[str] = Field(
        default=None,
        description="Application version"
    )
    timestamp: datetime = Field(
        description="Health check timestamp"
    )
    dependencies: Optional[Dict[str, str]] = Field(
        default=None,
        description="Status of external dependencies"
    )


class FilterParams(BaseSchema):
    """
    Base schema for filtering parameters.
    
    Provides common filtering options for list endpoints.
    """
    
    q: Optional[str] = Field(
        default=None,
        description="Search query string"
    )
    sort: Optional[str] = Field(
        default=None,
        description="Sort field and direction (e.g., 'name:asc', 'created_at:desc')"
    )


class DateRangeFilter(BaseSchema):
    """
    Schema for date range filtering.
    
    Provides start and end date filters for time-based queries.
    """
    
    start_date: Optional[datetime] = Field(
        default=None,
        description="Start date for filtering (inclusive)"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="End date for filtering (inclusive)"
    )


class BulkOperationRequest(BaseSchema):
    """
    Schema for bulk operation requests.
    
    Provides structure for operations that affect multiple resources.
    """
    
    resource_ids: List[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of resource IDs to operate on (max 100)"
    )
    operation: str = Field(
        description="Operation to perform"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for the operation"
    )


class BulkOperationResponse(BaseSchema):
    """
    Schema for bulk operation responses.
    
    Provides results and status for bulk operations.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking the bulk operation"
    )
    total_count: int = Field(
        description="Total number of resources to process"
    )
    status: str = Field(
        description="Initial status of the bulk operation"
    )


class JobReference(BaseSchema):
    """
    Schema for job references in async operations.
    
    Provides job information for tracking asynchronous operations.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking"
    )
    status: str = Field(
        description="Current job status"
    )
    message: Optional[str] = Field(
        default=None,
        description="Status message or description"
    )