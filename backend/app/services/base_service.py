"""
Base service class with tenant isolation and common functionality.

This module provides the base service class that all other services inherit from,
ensuring consistent tenant isolation and audit logging across the application.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from ..models.base import BaseModel
from ..models import AuditLog

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService:
    """
    Base service class with tenant isolation and audit logging.
    
    This class provides common functionality for all services including:
    - Automatic tenant filtering for multi-tenant isolation
    - Audit logging for all operations
    - SuperAdmin bypass for cross-tenant access
    - Common CRUD operations with tenant awareness
    """
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None, user_id: Optional[str] = None, is_superadmin: bool = False):
        """
        Initialize base service.
        
        Args:
            db: Database session.
            tenant_id: Current tenant ID for isolation.
            user_id: Current user ID for audit logging.
            is_superadmin: Whether current user is SuperAdmin.
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.is_superadmin = is_superadmin
    
    def _apply_tenant_filter(self, query: Query, model: Type[ModelType], allow_cross_tenant: bool = False) -> Query:
        """
        Apply tenant filtering to query.
        
        Args:
            query: SQLAlchemy query to filter.
            model: Model class being queried.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            Query: Filtered query with tenant isolation.
        """
        # Check if model has tenant_id field
        if not hasattr(model, 'tenant_id'):
            return query
        
        # SuperAdmin can bypass tenant filtering if explicitly allowed
        if self.is_superadmin and allow_cross_tenant:
            logger.debug("SuperAdmin cross-tenant access granted")
            return query
        
        # Apply tenant filtering
        if self.tenant_id:
            filtered_query = query.filter(model.tenant_id == self.tenant_id)
            logger.debug(f"Applied tenant filter: tenant_id={self.tenant_id}")
            return filtered_query
        else:
            # No tenant context - this should not happen in normal operation
            logger.warning("No tenant context available for filtering")
            # Return empty result set for security
            return query.filter(False)
    
    def _log_audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[Union[str, UUID]] = None,
        result: str = "success",
        before_value: Optional[Dict[str, Any]] = None,
        after_value: Optional[Dict[str, Any]] = None,
        device_id: Optional[Union[str, UUID]] = None
    ) -> None:
        """
        Log audit event for the operation.
        
        Args:
            action: Action performed (e.g., "create", "update", "delete").
            resource_type: Type of resource (e.g., "device", "template").
            resource_id: ID of the resource affected.
            result: Result of the operation ("success", "failure", "error").
            before_value: Value before the change (for updates).
            after_value: Value after the change (for updates).
            device_id: Device ID if operation is device-related.
        """
        try:
            audit_log = AuditLog(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                device_id=device_id,
                action=f"{resource_type}_{action}",
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                before_value=before_value,
                after_value=after_value
            )
            
            self.db.add(audit_log)
            # Note: Don't commit here - let the calling code handle transaction
            
            logger.debug(f"Audit log created: {action} on {resource_type} {resource_id}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise exception - audit logging failure shouldn't break operations
    
    def get_by_id(
        self, 
        model: Type[ModelType], 
        resource_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[ModelType]:
        """
        Get resource by ID with tenant filtering.
        
        Args:
            model: Model class to query.
            resource_id: ID of the resource to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            ModelType: Resource if found and accessible, None otherwise.
        """
        query = self.db.query(model).filter(model.id == resource_id)
        query = self._apply_tenant_filter(query, model, allow_cross_tenant)
        
        result = query.first()
        
        if result:
            logger.debug(f"Retrieved {model.__name__} {resource_id}")
        else:
            logger.debug(f"{model.__name__} {resource_id} not found or not accessible")
        
        return result
    
    def list_resources(
        self,
        model: Type[ModelType],
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List resources with pagination and filtering.
        
        Args:
            model: Model class to query.
            filters: Additional filters to apply.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated results with metadata.
        """
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        elif page_size > 1000:  # Prevent excessive page sizes
            page_size = 1000
        
        query = self.db.query(model)
        query = self._apply_tenant_filter(query, model, allow_cross_tenant)
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(model, field) and value is not None:
                    # Handle different filter types
                    if isinstance(value, list):
                        # IN filter for lists
                        if value:  # Only apply if list is not empty
                            query = query.filter(getattr(model, field).in_(value))
                    elif isinstance(value, str) and value.strip():
                        # String filter (only if not empty)
                        query = query.filter(getattr(model, field) == value)
                    elif not isinstance(value, str):
                        # Non-string values (numbers, booleans, etc.)
                        query = query.filter(getattr(model, field) == value)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        result = {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        logger.debug(
            f"Listed {len(items)} {model.__name__} items "
            f"(page {page}/{total_pages}, total: {total_count})"
        )
        
        return result
    
    def create_resource(
        self,
        model: Type[ModelType],
        data: Dict[str, Any],
        **kwargs
    ) -> ModelType:
        """
        Create new resource with tenant isolation.
        
        Args:
            model: Model class to create.
            data: Data for the new resource.
            **kwargs: Additional arguments for model creation.
            
        Returns:
            ModelType: Created resource.
        """
        # Inject tenant_id if model supports it and not already provided
        if hasattr(model, 'tenant_id') and 'tenant_id' not in data and self.tenant_id:
            data['tenant_id'] = self.tenant_id
        
        # Create resource
        resource = model(**data, **kwargs)
        self.db.add(resource)
        self.db.flush()  # Get ID without committing
        
        # Log audit event
        self._log_audit_event(
            action="create",
            resource_type=model.__name__.lower(),
            resource_id=resource.id,
            after_value=resource.to_dict() if hasattr(resource, 'to_dict') else None
        )
        
        logger.info(f"Created {model.__name__} {resource.id}")
        return resource
    
    def update_resource(
        self,
        resource: ModelType,
        data: Dict[str, Any]
    ) -> ModelType:
        """
        Update existing resource.
        
        Args:
            resource: Resource to update.
            data: Updated data.
            
        Returns:
            ModelType: Updated resource.
        """
        # Capture before state for audit
        before_value = resource.to_dict() if hasattr(resource, 'to_dict') else None
        
        # Update resource
        for field, value in data.items():
            if hasattr(resource, field):
                setattr(resource, field, value)
        
        self.db.flush()  # Ensure changes are reflected
        
        # Capture after state for audit
        after_value = resource.to_dict() if hasattr(resource, 'to_dict') else None
        
        # Log audit event
        self._log_audit_event(
            action="update",
            resource_type=resource.__class__.__name__.lower(),
            resource_id=resource.id,
            before_value=before_value,
            after_value=after_value
        )
        
        logger.info(f"Updated {resource.__class__.__name__} {resource.id}")
        return resource
    
    def delete_resource(self, resource: ModelType) -> None:
        """
        Delete existing resource.
        
        Args:
            resource: Resource to delete.
        """
        # Capture before state for audit
        before_value = resource.to_dict() if hasattr(resource, 'to_dict') else None
        resource_id = resource.id
        resource_type = resource.__class__.__name__.lower()
        
        # Delete resource
        self.db.delete(resource)
        self.db.flush()
        
        # Log audit event
        self._log_audit_event(
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            before_value=before_value
        )
        
        logger.info(f"Deleted {resource_type} {resource_id}")
    
    def check_tenant_access(self, resource: BaseModel) -> bool:
        """
        Check if current user has access to resource based on tenant.
        
        Args:
            resource: Resource to check access for.
            
        Returns:
            bool: True if access is allowed, False otherwise.
        """
        # SuperAdmin has access to all resources
        if self.is_superadmin:
            return True
        
        # Check tenant access for tenant-scoped resources
        if hasattr(resource, 'tenant_id'):
            return str(resource.tenant_id) == self.tenant_id
        
        # Non-tenant-scoped resources are accessible
        return True
    
    def log_cross_tenant_access(self, resource_type: str, resource_id: Union[str, UUID]) -> None:
        """
        Log cross-tenant access attempt for security monitoring.
        
        Args:
            resource_type: Type of resource accessed.
            resource_id: ID of resource accessed.
        """
        self._log_audit_event(
            action="cross_tenant_access",
            resource_type=resource_type,
            resource_id=resource_id,
            result="success" if self.is_superadmin else "denied"
        )
        
        logger.warning(
            f"Cross-tenant access attempt: {resource_type} {resource_id} "
            f"by user {self.user_id} (SuperAdmin: {self.is_superadmin})"
        )