"""
Alert service for managing system alerts and notifications.

This module provides the AlertService class for alert management operations
including CRUD operations, status updates, and statistics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from .base_service import BaseService
from ..models.alert import Alert, AlertSeverity, AlertStatus
from ..models.device import Device
from ..schemas.alert import AlertCreate, AlertUpdate, AlertFilterParams

logger = logging.getLogger(__name__)


class AlertService(BaseService):
    """
    Service class for alert management operations.
    
    Provides CRUD operations for alerts with tenant isolation,
    status management, and comprehensive statistics.
    """
    
    def list_alerts(
        self,
        filters: Optional[AlertFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List alerts with pagination and filtering.
        
        Args:
            filters: Filter parameters for alert listing.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated alert results with metadata.
        """
        # Start with base query including relationships for efficient loading
        query = self.db.query(Alert).options(
            joinedload(Alert.device),
            joinedload(Alert.tenant)
        )
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, Alert, allow_cross_tenant)
        
        # Apply filters if provided
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            
            # Handle date range filters
            if 'start_date' in filter_dict:
                start_date = filter_dict.pop('start_date')
                query = query.filter(Alert.created_at >= start_date)
            
            if 'end_date' in filter_dict:
                end_date = filter_dict.pop('end_date')
                query = query.filter(Alert.created_at <= end_date)
            
            # Apply remaining filters
            for field, value in filter_dict.items():
                if hasattr(Alert, field) and value is not None:
                    if isinstance(value, list):
                        query = query.filter(getattr(Alert, field).in_(value))
                    else:
                        query = query.filter(getattr(Alert, field) == value)
        
        # Order by created_at descending (newest first)
        query = query.order_by(Alert.created_at.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        alerts = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        result = {
            "items": alerts,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        # Log audit event
        self._log_audit_event(
            action="list",
            resource_type="alert",
            result="success"
        )
        
        logger.info(
            f"Listed {len(alerts)} alerts "
            f"(page {page}/{total_pages}, total: {total_count})"
        )
        
        return result
    
    def get_alert(
        self,
        alert_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[Alert]:
        """
        Get alert by ID with tenant isolation.
        
        Args:
            alert_id: ID of the alert to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            Alert: Alert if found and accessible, None otherwise.
        """
        # Use base service method with eager loading
        query = self.db.query(Alert).options(
            joinedload(Alert.device),
            joinedload(Alert.tenant)
        ).filter(Alert.id == alert_id)
        
        query = self._apply_tenant_filter(query, Alert, allow_cross_tenant)
        alert = query.first()
        
        if alert:
            # Log audit event
            self._log_audit_event(
                action="get",
                resource_type="alert",
                resource_id=alert.id,
                device_id=alert.device_id,
                result="success"
            )
            
            logger.debug(f"Retrieved alert {alert_id}")
        else:
            # Log failed access attempt
            self._log_audit_event(
                action="get",
                resource_type="alert",
                resource_id=alert_id,
                result="not_found"
            )
            
            logger.debug(f"Alert {alert_id} not found or not accessible")
        
        return alert
    
    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """
        Create new alert.
        
        Args:
            alert_data: Alert creation data.
            
        Returns:
            Alert: Created alert.
            
        Raises:
            ValueError: If device_id is provided but device doesn't exist or belong to tenant.
            Exception: If alert creation fails.
        """
        try:
            # Validate device_id if provided
            if alert_data.device_id:
                device_query = self.db.query(Device).filter(Device.id == alert_data.device_id)
                device_query = self._apply_tenant_filter(device_query, Device)
                device = device_query.first()
                
                if not device:
                    raise ValueError(f"Device {alert_data.device_id} not found or not accessible")
            
            # Create alert data
            alert_dict = alert_data.model_dump()
            
            # Set initial status
            alert_dict['status'] = AlertStatus.ACTIVE
            
            # Create alert using base service method
            alert = self.create_resource(Alert, alert_dict)
            
            logger.info(
                f"Created alert {alert.id} "
                f"(severity: {alert.severity}, device: {alert.device_id})"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            # Log failure
            self._log_audit_event(
                action="create",
                resource_type="alert",
                result="error"
            )
            raise
    
    def update_alert(
        self,
        alert_id: Union[str, UUID],
        alert_data: AlertUpdate
    ) -> Optional[Alert]:
        """
        Update existing alert.
        
        Args:
            alert_id: ID of the alert to update.
            alert_data: Updated alert data.
            
        Returns:
            Alert: Updated alert if found and accessible, None otherwise.
        """
        # Get existing alert
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        try:
            # Prepare update data
            update_dict = alert_data.model_dump(exclude_none=True)
            
            # Handle status transitions
            if 'status' in update_dict:
                new_status = update_dict['status']
                
                # Set acknowledged_at when status changes to acknowledged
                if new_status == AlertStatus.ACKNOWLEDGED and alert.status != AlertStatus.ACKNOWLEDGED:
                    update_dict['acknowledged_at'] = datetime.now(timezone.utc)
                
                # Set resolved_at when status changes to resolved
                if new_status == AlertStatus.RESOLVED and alert.status != AlertStatus.RESOLVED:
                    update_dict['resolved_at'] = datetime.now(timezone.utc)
            
            # Update alert using base service method
            updated_alert = self.update_resource(alert, update_dict)
            
            logger.info(f"Updated alert {alert_id}")
            
            return updated_alert
            
        except Exception as e:
            logger.error(f"Failed to update alert {alert_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="update",
                resource_type="alert",
                resource_id=alert_id,
                device_id=alert.device_id,
                result="error"
            )
            raise
    
    def acknowledge_alert(
        self,
        alert_id: Union[str, UUID]
    ) -> Optional[Alert]:
        """
        Acknowledge an alert (shortcut for updating status to acknowledged).
        
        Args:
            alert_id: ID of the alert to acknowledge.
            
        Returns:
            Alert: Acknowledged alert if found and accessible, None otherwise.
        """
        # Get existing alert
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        try:
            # Update status to acknowledged
            update_dict = {
                'status': AlertStatus.ACKNOWLEDGED,
                'acknowledged_at': datetime.now(timezone.utc)
            }
            
            # Update alert using base service method
            updated_alert = self.update_resource(alert, update_dict)
            
            logger.info(f"Acknowledged alert {alert_id}")
            
            return updated_alert
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="acknowledge",
                resource_type="alert",
                resource_id=alert_id,
                device_id=alert.device_id,
                result="error"
            )
            raise
    
    def resolve_alert(
        self,
        alert_id: Union[str, UUID]
    ) -> Optional[Alert]:
        """
        Resolve an alert (shortcut for updating status to resolved).
        
        Args:
            alert_id: ID of the alert to resolve.
            
        Returns:
            Alert: Resolved alert if found and accessible, None otherwise.
        """
        # Get existing alert
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        try:
            # Update status to resolved
            update_dict = {
                'status': AlertStatus.RESOLVED,
                'resolved_at': datetime.now(timezone.utc)
            }
            
            # Update alert using base service method
            updated_alert = self.update_resource(alert, update_dict)
            
            logger.info(f"Resolved alert {alert_id}")
            
            return updated_alert
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="resolve",
                resource_type="alert",
                resource_id=alert_id,
                device_id=alert.device_id,
                result="error"
            )
            raise
    
    def get_alert_stats(self, allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        Get alert statistics for the current tenant.
        
        Args:
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Alert statistics including counts by status, severity, etc.
        """
        try:
            # Base query with tenant filtering
            query = self.db.query(Alert)
            query = self._apply_tenant_filter(query, Alert, allow_cross_tenant)
            
            # Get all alerts for statistics
            alerts = query.all()
            
            # Calculate statistics
            total_alerts = len(alerts)
            
            # Count by status
            active = sum(1 for a in alerts if a.status == AlertStatus.ACTIVE)
            acknowledged = sum(1 for a in alerts if a.status == AlertStatus.ACKNOWLEDGED)
            resolved = sum(1 for a in alerts if a.status == AlertStatus.RESOLVED)
            
            # Count by severity
            by_severity = {
                AlertSeverity.INFO.value: sum(1 for a in alerts if a.severity == AlertSeverity.INFO),
                AlertSeverity.WARNING.value: sum(1 for a in alerts if a.severity == AlertSeverity.WARNING),
                AlertSeverity.CRITICAL.value: sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
            }
            
            # Count critical alerts
            critical_alerts = by_severity[AlertSeverity.CRITICAL.value]
            
            # Count recent alerts (last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_alerts = sum(1 for a in alerts if a.created_at >= cutoff_time)
            
            stats = {
                "total_alerts": total_alerts,
                "active": active,
                "acknowledged": acknowledged,
                "resolved": resolved,
                "by_severity": by_severity,
                "critical_alerts": critical_alerts,
                "recent_alerts": recent_alerts
            }
            
            # Log audit event
            self._log_audit_event(
                action="get_stats",
                resource_type="alert",
                result="success"
            )
            
            logger.debug(f"Generated alert statistics: {total_alerts} total alerts")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            # Log failure
            self._log_audit_event(
                action="get_stats",
                resource_type="alert",
                result="error"
            )
            raise
    
    def delete_alert(self, alert_id: Union[str, UUID]) -> bool:
        """
        Delete existing alert.
        
        Args:
            alert_id: ID of the alert to delete.
            
        Returns:
            bool: True if alert was deleted, False if not found.
        """
        # Get existing alert
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        try:
            # Delete alert using base service method
            self.delete_resource(alert)
            
            logger.info(f"Deleted alert {alert_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete alert {alert_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="delete",
                resource_type="alert",
                resource_id=alert_id,
                device_id=alert.device_id,
                result="error"
            )
            raise
    
    def get_device_alerts(
        self,
        device_id: Union[str, UUID],
        status: Optional[AlertStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get alerts for a specific device.
        
        Args:
            device_id: ID of the device.
            status: Optional status filter.
            page: Page number (1-based).
            page_size: Number of items per page.
            
        Returns:
            dict: Paginated alert results for the device.
        """
        # Build filters
        filters = AlertFilterParams(device_id=device_id, status=status)
        
        # Use list_alerts with filters
        return self.list_alerts(filters=filters, page=page, page_size=page_size)
    
    def auto_resolve_alerts(
        self,
        device_id: Optional[Union[str, UUID]] = None,
        older_than_days: int = 30
    ) -> int:
        """
        Auto-resolve old acknowledged alerts.
        
        Args:
            device_id: Optional device ID to filter alerts.
            older_than_days: Resolve alerts acknowledged more than this many days ago.
            
        Returns:
            int: Number of alerts auto-resolved.
        """
        try:
            # Build query for old acknowledged alerts
            query = self.db.query(Alert).filter(
                Alert.status == AlertStatus.ACKNOWLEDGED
            )
            
            # Apply tenant filtering
            query = self._apply_tenant_filter(query, Alert)
            
            # Filter by device if provided
            if device_id:
                query = query.filter(Alert.device_id == device_id)
            
            # Filter by age
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            query = query.filter(Alert.acknowledged_at <= cutoff_time)
            
            # Get alerts to resolve
            alerts_to_resolve = query.all()
            
            # Resolve each alert
            resolved_count = 0
            for alert in alerts_to_resolve:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)
                resolved_count += 1
            
            self.db.flush()
            
            # Log audit event
            self._log_audit_event(
                action="auto_resolve",
                resource_type="alert",
                result="success"
            )
            
            logger.info(f"Auto-resolved {resolved_count} old acknowledged alerts")
            
            return resolved_count
            
        except Exception as e:
            logger.error(f"Failed to auto-resolve alerts: {e}")
            # Log failure
            self._log_audit_event(
                action="auto_resolve",
                resource_type="alert",
                result="error"
            )
            raise
