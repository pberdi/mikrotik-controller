"""
Audit service for managing audit logs and compliance tracking.

This module provides the AuditService class for audit log operations
including creation, querying, and specialized logging methods.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload
from fastapi import Request

from .base_service import BaseService
from ..models.audit_log import AuditLog
from ..models.user import User
from ..models.device import Device

logger = logging.getLogger(__name__)


class AuditService(BaseService):
    """
    Service class for audit log management operations.
    
    Provides methods for creating and querying audit logs with
    specialized logging for different types of actions.
    """
    
    def __init__(
        self,
        db: Session,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_superadmin: bool = False,
        request: Optional[Request] = None
    ):
        """
        Initialize audit service.
        
        Args:
            db: Database session.
            tenant_id: Current tenant ID for isolation.
            user_id: Current user ID for audit logging.
            is_superadmin: Whether current user is SuperAdmin.
            request: Optional FastAPI request for extracting IP and user agent.
        """
        super().__init__(db, tenant_id, user_id, is_superadmin)
        self.request = request
    
    def log(
        self,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, UUID]] = None,
        result: str = "success",
        before_value: Optional[Dict[str, Any]] = None,
        after_value: Optional[Dict[str, Any]] = None,
        device_id: Optional[Union[str, UUID]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Create audit log entry.
        
        Args:
            action: Action performed (e.g., "device_create", "user_login").
            resource_type: Type of resource affected.
            resource_id: ID of the resource affected.
            result: Result of the action ("success", "failure", "error").
            before_value: Value before the change (for updates).
            after_value: Value after the change (for updates).
            device_id: Device ID if action is device-related.
            ip_address: IP address of the client.
            user_agent: User agent string of the client.
            request_id: Request ID for correlation.
            
        Returns:
            AuditLog: Created audit log entry.
        """
        try:
            # Validate input parameters
            if not action:
                raise ValueError("Action is required for audit logging")
            
            # Validate UUID format for IDs if provided
            if resource_id:
                try:
                    if isinstance(resource_id, str):
                        UUID(resource_id)
                except ValueError:
                    logger.warning(f"Invalid resource_id format: {resource_id}")
                    resource_id = str(resource_id)  # Convert to string for logging
            
            if device_id:
                try:
                    if isinstance(device_id, str):
                        UUID(device_id)
                except ValueError:
                    logger.warning(f"Invalid device_id format: {device_id}")
                    device_id = str(device_id)  # Convert to string for logging
            
            # Extract request information if request is available
            if self.request and not ip_address:
                ip_address = self.request.client.host if self.request.client else None
            
            if self.request and not user_agent:
                user_agent = self.request.headers.get("user-agent")
            
            if self.request and not request_id:
                request_id = getattr(self.request.state, "request_id", None)
            
            # Create audit log entry
            audit_log = AuditLog(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                device_id=device_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                before_value=before_value,
                after_value=after_value,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.db.add(audit_log)
            self.db.flush()
            
            logger.debug(
                f"Created audit log: action={action}, resource_type={resource_type}, "
                f"resource_id={resource_id}, result={result}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise exception - audit logging failure shouldn't break operations
            return None
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: Optional[float] = None
    ) -> Optional[AuditLog]:
        """
        Log API request for audit trail.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path.
            status_code: HTTP status code.
            duration_ms: Request duration in milliseconds.
            
        Returns:
            AuditLog: Created audit log entry.
        """
        action = f"api_request_{method.lower()}"
        result = "success" if 200 <= status_code < 400 else "failure"
        
        after_value = {
            "method": method,
            "path": path,
            "status_code": status_code
        }
        
        if duration_ms is not None:
            after_value["duration_ms"] = duration_ms
        
        return self.log(
            action=action,
            resource_type="api_request",
            result=result,
            after_value=after_value
        )
    
    def log_authentication(
        self,
        email: str,
        result: str,
        reason: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log authentication attempt.
        
        Args:
            email: Email address used for authentication.
            result: Result of authentication ("success", "failure").
            reason: Reason for failure (e.g., "incorrect_password", "user_not_found").
            
        Returns:
            AuditLog: Created audit log entry.
        """
        after_value = {
            "email": email
        }
        
        if reason:
            after_value["reason"] = reason
        
        return self.log(
            action="user_authenticate",
            resource_type="user",
            result=result,
            after_value=after_value
        )
    
    def log_device_operation(
        self,
        device_id: Union[str, UUID],
        operation: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """
        Log device operation (backup, template application, command execution).
        
        Args:
            device_id: ID of the device.
            operation: Operation performed (e.g., "backup", "template_apply", "command").
            result: Result of the operation.
            details: Additional operation details.
            
        Returns:
            AuditLog: Created audit log entry.
        """
        action = f"device_{operation}"
        
        return self.log(
            action=action,
            resource_type="device",
            resource_id=device_id,
            device_id=device_id,
            result=result,
            after_value=details
        )
    
    def log_permission_failure(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[Union[str, UUID]] = None,
        required_permission: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log permission failure for security monitoring.
        
        Args:
            action: Action that was attempted.
            resource_type: Type of resource.
            resource_id: ID of the resource.
            required_permission: Permission that was required.
            
        Returns:
            AuditLog: Created audit log entry.
        """
        after_value = {
            "attempted_action": action
        }
        
        if required_permission:
            after_value["required_permission"] = required_permission
        
        return self.log(
            action="permission_denied",
            resource_type=resource_type,
            resource_id=resource_id,
            result="failure",
            after_value=after_value
        )
    
    def list_audit_logs(
        self,
        user_id: Optional[Union[str, UUID]] = None,
        device_id: Optional[Union[str, UUID]] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List audit logs with filtering and pagination.
        
        Args:
            user_id: Filter by user ID.
            device_id: Filter by device ID.
            action: Filter by action.
            resource_type: Filter by resource type.
            result: Filter by result.
            start_date: Filter by start date.
            end_date: Filter by end date.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated audit log results with metadata.
        """
        # Start with base query including relationships
        query = self.db.query(AuditLog).options(
            joinedload(AuditLog.user),
            joinedload(AuditLog.device),
            joinedload(AuditLog.tenant)
        )
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, AuditLog, allow_cross_tenant)
        
        # Apply filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if device_id:
            query = query.filter(AuditLog.device_id == device_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if result:
            query = query.filter(AuditLog.result == result)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        audit_logs = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        result = {
            "items": audit_logs,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        logger.info(
            f"Listed {len(audit_logs)} audit logs "
            f"(page {page}/{total_pages}, total: {total_count})"
        )
        
        return result
    
    def get_audit_log(
        self,
        log_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[AuditLog]:
        """
        Get audit log by ID with tenant isolation.
        
        Args:
            log_id: ID of the audit log to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            AuditLog: Audit log if found and accessible, None otherwise.
        """
        query = self.db.query(AuditLog).options(
            joinedload(AuditLog.user),
            joinedload(AuditLog.device),
            joinedload(AuditLog.tenant)
        ).filter(AuditLog.id == log_id)
        
        query = self._apply_tenant_filter(query, AuditLog, allow_cross_tenant)
        audit_log = query.first()
        
        if audit_log:
            logger.debug(f"Retrieved audit log {log_id}")
        else:
            logger.debug(f"Audit log {log_id} not found or not accessible")
        
        return audit_log
    
    def get_user_activity(
        self,
        user_id: Union[str, UUID],
        days: int = 30,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        Get user activity summary for the specified period.
        
        Args:
            user_id: ID of the user.
            days: Number of days to look back.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: User activity summary.
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Query audit logs for user
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
            
            query = self._apply_tenant_filter(query, AuditLog, allow_cross_tenant)
            
            audit_logs = query.all()
            
            # Calculate statistics
            total_actions = len(audit_logs)
            
            # Count by action type
            by_action = {}
            for log in audit_logs:
                by_action[log.action] = by_action.get(log.action, 0) + 1
            
            # Count by result
            successful = sum(1 for log in audit_logs if log.result == "success")
            failed = sum(1 for log in audit_logs if log.result in ["failure", "error"])
            
            # Get most recent activity
            most_recent = audit_logs[0] if audit_logs else None
            
            activity = {
                "user_id": str(user_id),
                "period_days": days,
                "total_actions": total_actions,
                "successful_actions": successful,
                "failed_actions": failed,
                "by_action": by_action,
                "most_recent_activity": most_recent.timestamp if most_recent else None
            }
            
            logger.debug(f"Generated activity summary for user {user_id}: {total_actions} actions")
            
            return activity
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            raise
    
    def get_device_activity(
        self,
        device_id: Union[str, UUID],
        days: int = 30,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        Get device activity summary for the specified period.
        
        Args:
            device_id: ID of the device.
            days: Number of days to look back.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Device activity summary.
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Query audit logs for device
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.device_id == device_id,
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
            
            query = self._apply_tenant_filter(query, AuditLog, allow_cross_tenant)
            
            audit_logs = query.all()
            
            # Calculate statistics
            total_operations = len(audit_logs)
            
            # Count by operation type
            by_operation = {}
            for log in audit_logs:
                by_operation[log.action] = by_operation.get(log.action, 0) + 1
            
            # Count by result
            successful = sum(1 for log in audit_logs if log.result == "success")
            failed = sum(1 for log in audit_logs if log.result in ["failure", "error"])
            
            # Get most recent operation
            most_recent = audit_logs[0] if audit_logs else None
            
            activity = {
                "device_id": str(device_id),
                "period_days": days,
                "total_operations": total_operations,
                "successful_operations": successful,
                "failed_operations": failed,
                "by_operation": by_operation,
                "most_recent_operation": most_recent.timestamp if most_recent else None
            }
            
            logger.debug(f"Generated activity summary for device {device_id}: {total_operations} operations")
            
            return activity
            
        except Exception as e:
            logger.error(f"Failed to get device activity: {e}")
            raise
    
    def get_security_events(
        self,
        days: int = 7,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        Get security-related events for monitoring.
        
        Args:
            days: Number of days to look back.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Security events summary.
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Query security-related audit logs
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    or_(
                        AuditLog.action.like("%authenticate%"),
                        AuditLog.action.like("%permission%"),
                        AuditLog.action == "cross_tenant_access",
                        AuditLog.result.in_(["failure", "error", "denied"])
                    )
                )
            )
            
            query = self._apply_tenant_filter(query, AuditLog, allow_cross_tenant)
            
            security_logs = query.all()
            
            # Calculate statistics
            total_events = len(security_logs)
            
            # Count failed authentication attempts
            failed_auth = sum(
                1 for log in security_logs 
                if "authenticate" in log.action and log.result == "failure"
            )
            
            # Count permission denials
            permission_denials = sum(
                1 for log in security_logs 
                if "permission" in log.action or log.result == "denied"
            )
            
            # Count cross-tenant access attempts
            cross_tenant_access = sum(
                1 for log in security_logs 
                if log.action == "cross_tenant_access"
            )
            
            # Get recent security events
            recent_events = security_logs[:10]  # Last 10 events
            
            events = {
                "period_days": days,
                "total_security_events": total_events,
                "failed_authentication_attempts": failed_auth,
                "permission_denials": permission_denials,
                "cross_tenant_access_attempts": cross_tenant_access,
                "recent_events": [
                    {
                        "timestamp": log.timestamp,
                        "action": log.action,
                        "result": log.result,
                        "user_id": str(log.user_id) if log.user_id else None,
                        "ip_address": log.ip_address
                    }
                    for log in recent_events
                ]
            }
            
            logger.debug(f"Generated security events summary: {total_events} events")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            raise
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Clean up audit logs older than specified days.
        
        Args:
            days: Delete logs older than this many days.
            
        Returns:
            int: Number of logs deleted.
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Query old logs
            query = self.db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            )
            
            # Apply tenant filtering
            query = self._apply_tenant_filter(query, AuditLog)
            
            # Count logs to delete
            count = query.count()
            
            # Delete logs
            query.delete(synchronize_session=False)
            self.db.flush()
            
            logger.info(f"Cleaned up {count} audit logs older than {days} days")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            raise
