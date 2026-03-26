"""
Template Pydantic schemas for request/response validation.

This module provides schemas for template-related API operations.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema, UUIDSchema, FilterParams
from ..models.template import TemplateType


class TemplateBase(BaseSchema):
    """
    Base template schema with common fields.
    """
    
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Template name",
        examples=["Basic Router Config", "VLAN Setup"]
    )
    
    type: TemplateType = Field(
        description="Template type (declarative or script)"
    )
    
    content: str = Field(
        min_length=1,
        description="Template content in Jinja2 format"
    )


class TemplateCreate(TemplateBase):
    """
    Schema for template creation requests.
    """
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name."""
        if not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate template content."""
        if not v.strip():
            raise ValueError("Template content cannot be empty")
        return v.strip()


class TemplateUpdate(BaseSchema):
    """
    Schema for template update requests.
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Template name"
    )
    
    type: Optional[TemplateType] = Field(
        default=None,
        description="Template type"
    )
    
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Template content"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate template name if provided."""
        if v is not None and not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip() if v else v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate template content if provided."""
        if v is not None and not v.strip():
            raise ValueError("Template content cannot be empty")
        return v.strip() if v else v


class TemplateResponse(TemplateBase, UUIDSchema, TimestampSchema):
    """
    Schema for template responses.
    """
    
    tenant_id: UUID = Field(
        description="Tenant that owns this template"
    )


class TemplateFilterParams(FilterParams):
    """
    Schema for template filtering parameters.
    """
    
    type: Optional[TemplateType] = Field(
        default=None,
        description="Filter by template type"
    )


class TemplateApplyRequest(BaseSchema):
    """
    Schema for template application requests.
    """
    
    device_ids: List[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of device IDs to apply template to (max 100)"
    )
    
    variables: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Variables for template rendering"
    )
    
    dry_run: Optional[bool] = Field(
        default=False,
        description="Whether to perform a dry run (validation only)"
    )


class TemplateApplyResponse(BaseSchema):
    """
    Schema for template application responses.
    """
    
    job_id: UUID = Field(
        description="Job ID for tracking template application"
    )
    
    template_id: UUID = Field(
        description="Template ID being applied"
    )
    
    device_count: int = Field(
        description="Number of devices the template will be applied to"
    )
    
    status: str = Field(
        description="Initial job status"
    )