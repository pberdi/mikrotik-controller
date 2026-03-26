"""
Template service for managing configuration templates.

This module provides the TemplateService class for CRUD operations on templates
with integrated Jinja2 template syntax validation.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

import jinja2
import jinja2.meta
from sqlalchemy.orm import Session

from ..models.template import Template, TemplateType
from ..schemas.template import TemplateCreate, TemplateUpdate, TemplateFilterParams
from .base_service import BaseService

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""
    pass


class TemplateService(BaseService[Template]):
    """
    Service for managing configuration templates.
    
    Provides CRUD operations with tenant isolation and Jinja2 template
    syntax validation.
    """
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None, 
                 user_id: Optional[str] = None, is_superadmin: bool = False):
        """Initialize template service."""
        super().__init__(db, tenant_id, user_id, is_superadmin)
        self._jinja_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            undefined=jinja2.StrictUndefined,
            autoescape=False
        )
    
    def validate_template_syntax(self, content: str) -> None:
        """
        Validate Jinja2 template syntax.
        
        Args:
            content: Template content to validate
            
        Raises:
            TemplateValidationError: If template syntax is invalid
        """
        try:
            self._jinja_env.parse(content)
        except jinja2.TemplateSyntaxError as e:
            raise TemplateValidationError(
                f"Template syntax error at line {e.lineno}: {e.message}"
            ) from e
        except jinja2.TemplateError as e:
            raise TemplateValidationError(f"Template error: {str(e)}") from e
    
    def create_template(self, template_data: TemplateCreate) -> Template:
        """
        Create a new template with syntax validation.
        
        Args:
            template_data: Template creation data
            
        Returns:
            Created template
            
        Raises:
            TemplateValidationError: If template syntax is invalid
        """
        # Validate template syntax
        self.validate_template_syntax(template_data.content)
        
        # Create template
        template = Template(
            tenant_id=self.tenant_id,
            name=template_data.name,
            type=template_data.type,
            content=template_data.content
        )
        
        created_template = self.create_resource(template)
        
        self._log_audit_event(
            action="template_create",
            resource_type="template",
            resource_id=created_template.id,
            after_value={
                "name": created_template.name,
                "type": created_template.type.value,
                "content_length": len(created_template.content)
            }
        )
        
        return created_template
    
    def get_template(self, template_id: UUID, allow_cross_tenant: bool = False) -> Optional[Template]:
        """
        Get template by ID.
        
        Args:
            template_id: Template ID
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Template if found, None otherwise
        """
        return self.get_by_id(Template, template_id, allow_cross_tenant)
    
    def list_templates(self, filters: Optional[TemplateFilterParams] = None, 
                      page: int = 1, page_size: int = 50,
                      allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        List templates with filtering and pagination.
        
        Args:
            filters: Filter parameters
            page: Page number (1-based)
            page_size: Number of items per page
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Dictionary with templates and pagination metadata
        """
        query_filters = {}
        if filters:
            if filters.type:
                query_filters["type"] = filters.type
        
        return self.list_resources(
            Template,
            filters=query_filters,
            page=page,
            page_size=page_size,
            allow_cross_tenant=allow_cross_tenant
        )
    
    def update_template(self, template_id: UUID, template_data: TemplateUpdate,
                       allow_cross_tenant: bool = False) -> Optional[Template]:
        """
        Update template with syntax validation.
        
        Args:
            template_id: Template ID
            template_data: Template update data
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Updated template if found, None otherwise
            
        Raises:
            TemplateValidationError: If template syntax is invalid
        """
        template = self.get_template(template_id, allow_cross_tenant)
        if not template:
            return None
        
        # Store original values for audit
        before_value = {
            "name": template.name,
            "type": template.type.value,
            "content_length": len(template.content)
        }
        
        # Validate new content if provided
        if template_data.content is not None:
            self.validate_template_syntax(template_data.content)
        
        # Update fields
        update_data = template_data.model_dump(exclude_unset=True)
        updated_template = self.update_resource(template, update_data)
        
        # Log audit event
        after_value = {
            "name": updated_template.name,
            "type": updated_template.type.value,
            "content_length": len(updated_template.content)
        }
        
        self._log_audit_event(
            action="template_update",
            resource_type="template",
            resource_id=updated_template.id,
            before_value=before_value,
            after_value=after_value
        )
        
        return updated_template
    
    def delete_template(self, template_id: UUID, allow_cross_tenant: bool = False) -> bool:
        """
        Delete template.
        
        Args:
            template_id: Template ID
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            True if template was deleted, False if not found
        """
        template = self.get_template(template_id, allow_cross_tenant)
        if not template:
            return False
        
        # Store values for audit
        before_value = {
            "name": template.name,
            "type": template.type.value,
            "content_length": len(template.content)
        }
        
        self.delete_resource(template)
        
        self._log_audit_event(
            action="template_delete",
            resource_type="template",
            resource_id=template_id,
            before_value=before_value
        )
        
        return True
    
    def render_template(self, template_id: UUID, variables: Optional[Dict[str, Any]] = None,
                       allow_cross_tenant: bool = False) -> Optional[str]:
        """
        Render template with provided variables.
        
        Args:
            template_id: Template ID
            variables: Variables for template rendering
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Rendered template content if successful, None if template not found
            
        Raises:
            TemplateValidationError: If template rendering fails
        """
        template = self.get_template(template_id, allow_cross_tenant)
        if not template:
            return None
        
        try:
            jinja_template = self._jinja_env.from_string(template.content)
            rendered = jinja_template.render(variables or {})
            
            self._log_audit_event(
                action="template_render",
                resource_type="template",
                resource_id=template_id,
                after_value={
                    "variables_count": len(variables) if variables else 0,
                    "rendered_length": len(rendered)
                }
            )
            
            return rendered
            
        except jinja2.UndefinedError as e:
            raise TemplateValidationError(
                f"Template rendering failed - undefined variable: {str(e)}"
            ) from e
        except jinja2.TemplateError as e:
            raise TemplateValidationError(
                f"Template rendering failed: {str(e)}"
            ) from e
    
    def get_template_variables(self, template_id: UUID, 
                              allow_cross_tenant: bool = False) -> Optional[List[str]]:
        """
        Extract variable names from template.
        
        Args:
            template_id: Template ID
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            List of variable names if template found, None otherwise
        """
        template = self.get_template(template_id, allow_cross_tenant)
        if not template:
            return None
        
        try:
            ast = self._jinja_env.parse(template.content)
            variables = jinja2.meta.find_undeclared_variables(ast)
            return sorted(list(variables))
        except jinja2.TemplateError:
            # If parsing fails, return empty list
            return []
    
    def dry_run_template(self, template_id: UUID, variables: Optional[Dict[str, Any]] = None,
                        allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        Perform dry run of template rendering for validation.
        
        Args:
            template_id: Template ID
            variables: Variables for template rendering
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Dictionary with dry run results
        """
        template = self.get_template(template_id, allow_cross_tenant)
        if not template:
            return {"success": False, "error": "Template not found"}
        
        try:
            # Get required variables
            required_vars = self.get_template_variables(template_id, allow_cross_tenant)
            provided_vars = set(variables.keys()) if variables else set()
            missing_vars = set(required_vars or []) - provided_vars
            
            # Try to render
            rendered = self.render_template(template_id, variables, allow_cross_tenant)
            
            return {
                "success": True,
                "required_variables": required_vars,
                "missing_variables": list(missing_vars),
                "rendered_length": len(rendered) if rendered else 0,
                "preview": rendered[:500] if rendered else None  # First 500 chars
            }
            
        except TemplateValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "required_variables": self.get_template_variables(template_id, allow_cross_tenant),
                "missing_variables": []
            }