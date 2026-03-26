"""
User Pydantic schemas for request/response validation.

This module provides schemas for user-related API operations.
"""

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams


class UserBase(BaseSchema):
    """
    Base user schema with common fields.
    """
    
    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"]
    )


class UserCreate(UserBase):
    """
    Schema for user creation requests.
    """
    
    password: str = Field(
        min_length=8,
        max_length=255,
        description="User password (min 8 characters)"
    )
    
    role_id: UUID = Field(
        description="Role ID to assign to user"
    )
    
    is_active: Optional[bool] = Field(
        default=True,
        description="Whether user account is active"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Basic password strength validation
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and digit characters")
        
        return v


class UserUpdate(BaseSchema):
    """
    Schema for user update requests.
    """
    
    email: Optional[EmailStr] = Field(
        default=None,
        description="User email address"
    )
    
    role_id: Optional[UUID] = Field(
        default=None,
        description="Role ID to assign to user"
    )
    
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether user account is active"
    )


class UserPasswordUpdate(BaseSchema):
    """
    Schema for user password update requests.
    """
    
    current_password: str = Field(
        description="Current password for verification"
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password (min 8 characters)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Basic password strength validation
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and digit characters")
        
        return v


class RoleResponse(UUIDSchema, TimestampSchema):
    """
    Schema for role responses.
    """
    
    name: str = Field(
        description="Role name"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Role description"
    )


class UserResponse(UserBase, UUIDSchema, TimestampSchema):
    """
    Schema for user responses.
    """
    
    tenant_id: UUID = Field(
        description="Tenant this user belongs to"
    )
    
    role_id: UUID = Field(
        description="Role assigned to this user"
    )
    
    is_active: bool = Field(
        description="Whether user account is active"
    )
    
    role: Optional[RoleResponse] = Field(
        default=None,
        description="Role information"
    )


class UserDetailResponse(UserResponse):
    """
    Schema for detailed user responses.
    """
    
    # Could include additional fields like last login, permissions, etc.
    pass


class UserFilterParams(FilterParams):
    """
    Schema for user filtering parameters.
    """
    
    role_id: Optional[UUID] = Field(
        default=None,
        description="Filter by role ID"
    )
    
    is_active: Optional[bool] = Field(
        default=None,
        description="Filter by active status"
    )


class UserRoleAssignRequest(BaseSchema):
    """
    Schema for user role assignment requests.
    """
    
    role_id: UUID = Field(
        description="Role ID to assign to user"
    )


class UserRoleAssignResponse(BaseSchema):
    """
    Schema for user role assignment responses.
    """
    
    user_id: UUID = Field(
        description="User ID"
    )
    
    role_id: UUID = Field(
        description="Assigned role ID"
    )
    
    role: RoleResponse = Field(
        description="Role information"
    )


class LoginRequest(BaseSchema):
    """
    Schema for login requests.
    """
    
    email: EmailStr = Field(
        description="User email address"
    )
    
    password: str = Field(
        description="User password"
    )


class LoginResponse(BaseSchema):
    """
    Schema for login responses.
    """
    
    access_token: str = Field(
        description="JWT access token"
    )
    
    refresh_token: str = Field(
        description="JWT refresh token"
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    
    expires_in: int = Field(
        description="Token expiration time in seconds"
    )
    
    user: UserResponse = Field(
        description="User information"
    )


class RefreshTokenRequest(BaseSchema):
    """
    Schema for token refresh requests.
    """
    
    refresh_token: str = Field(
        description="JWT refresh token"
    )


class RefreshTokenResponse(BaseSchema):
    """
    Schema for token refresh responses.
    """
    
    access_token: str = Field(
        description="New JWT access token"
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    
    expires_in: int = Field(
        description="Token expiration time in seconds"
    )