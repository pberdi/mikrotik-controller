"""
Pydantic schemas package.

This package contains all Pydantic schemas for request/response validation
across the API endpoints.
"""

from .common import (
    BaseSchema,
    TimestampSchema,
    UUIDSchema,
    PaginationParams,
    PaginationMetadata,
    PaginatedResponse,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    SuccessResponse,
    HealthCheckResponse,
    FilterParams,
    DateRangeFilter,
    BulkOperationRequest,
    BulkOperationResponse,
    JobReference,
)

from .device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceCredentialUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceDetailResponse,
    DeviceFilterParams,
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceStatsResponse,
)

from .template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateFilterParams,
    TemplateApplyRequest,
    TemplateApplyResponse,
)

from .job import (
    JobResponse,
    JobDetailResponse,
    JobFilterParams,
    JobCancelRequest,
    JobCancelResponse,
    JobLogsResponse,
    JobStatsResponse,
)

from .backup import (
    BackupCreateRequest,
    BackupCreateResponse,
    BackupResponse,
    BackupDetailResponse,
    BackupFilterParams,
    BackupRestoreRequest,
    BackupRestoreResponse,
    BackupStatsResponse,
)

from .alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertDetailResponse,
    AlertFilterParams,
    AlertAcknowledgeRequest,
    AlertAcknowledgeResponse,
    AlertStatsResponse,
)

from .user import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserDetailResponse,
    UserFilterParams,
    UserRoleAssignRequest,
    UserRoleAssignResponse,
    RoleResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)

__all__ = [
    # Common schemas
    "BaseSchema",
    "TimestampSchema",
    "UUIDSchema",
    "PaginationParams",
    "PaginationMetadata",
    "PaginatedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
    "FilterParams",
    "DateRangeFilter",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "JobReference",
    
    # Device schemas
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceCredentialUpdate",
    "DeviceResponse",
    "DeviceListResponse",
    "DeviceDetailResponse",
    "DeviceFilterParams",
    "DeviceCommandRequest",
    "DeviceCommandResponse",
    "DeviceStatsResponse",
    
    # Template schemas
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateFilterParams",
    "TemplateApplyRequest",
    "TemplateApplyResponse",
    
    # Job schemas
    "JobResponse",
    "JobDetailResponse",
    "JobFilterParams",
    "JobCancelRequest",
    "JobCancelResponse",
    "JobLogsResponse",
    "JobStatsResponse",
    
    # Backup schemas
    "BackupCreateRequest",
    "BackupCreateResponse",
    "BackupResponse",
    "BackupDetailResponse",
    "BackupFilterParams",
    "BackupRestoreRequest",
    "BackupRestoreResponse",
    "BackupStatsResponse",
    
    # Alert schemas
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "AlertDetailResponse",
    "AlertFilterParams",
    "AlertAcknowledgeRequest",
    "AlertAcknowledgeResponse",
    "AlertStatsResponse",
    
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserDetailResponse",
    "UserFilterParams",
    "UserRoleAssignRequest",
    "UserRoleAssignResponse",
    "RoleResponse",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
]