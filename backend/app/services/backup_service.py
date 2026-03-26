"""
Backup service for device configuration backup management.

This module provides the BackupService class for managing device configuration
backups with tenant isolation, filtering capabilities, and comprehensive audit logging.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from ..models.backup import Backup, BackupType
from ..models.device import Device
from ..schemas.backup import BackupFilterParams
from .base_service import BaseService

logger = logging.getLogger(__name__)


class BackupService(BaseService):
    """
    Service class for backup management operations.
    
    Provides operations for listing, retrieving, and deleting backups
    with tenant isolation and comprehensive audit logging.
    """
    
    def list_backups(
        self,
        filters: Optional[BackupFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List backups with pagination and filtering.
        
        Args:
            filters: Filter parameters for backup listing.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated backup results with metadata.
        """
        try:
            # Start with base query including relationships for efficient loading
            query = self.db.query(Backup).options(
                joinedload(Backup.device).joinedload(Device.site),
                joinedload(Backup.device).joinedload(Device.tenant)
            )
            
            # Apply tenant filtering through device relationship
            if not allow_cross_tenant or not self.is_superadmin:
                if self.tenant_id:
                    query = query.join(Device).filter(Device.tenant_id == self.tenant_id)
                else:
                    # If no tenant_id, return empty results
                    query = query.filter(False)
            
            # Apply filters if provided
            if filters:
                filter_dict = filters.model_dump(exclude_none=True)
                
                # Handle device_id filter
                if 'device_id' in filter_dict:
                    query = query.filter(Backup.device_id == filter_dict['device_id'])
                
                # Handle type filter
                if 'type' in filter_dict:
                    query = query.filter(Backup.type == filter_dict['type'])
                
                # Handle compressed filter
                if 'compressed' in filter_dict:
                    query = query.filter(Backup.compressed == filter_dict['compressed'])
                
                # Handle date range filters
                if 'start_date' in filter_dict and filter_dict['start_date']:
                    query = query.filter(Backup.created_at >= filter_dict['start_date'])
                
                if 'end_date' in filter_dict and filter_dict['end_date']:
                    # Add one day to end_date to include the entire day
                    end_date = filter_dict['end_date']
                    if isinstance(end_date, datetime):
                        end_date = end_date.replace(hour=23, minute=59, second=59)
                    query = query.filter(Backup.created_at <= end_date)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Backup.created_at))
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            backups = query.offset(offset).limit(page_size).all()
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            
            result = {
                "items": backups,
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
                resource_type="backup",
                result="success"
            )
            
            logger.info(
                f"Listed {len(backups)} backups "
                f"(page {page}/{total_pages}, total: {total_count})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            # Log failure
            self._log_audit_event(
                action="list",
                resource_type="backup",
                result="error"
            )
            raise
    
    def get_backup(
        self,
        backup_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[Backup]:
        """
        Get backup by ID with tenant isolation.
        
        Args:
            backup_id: ID of the backup to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            Backup: Backup if found and accessible, None otherwise.
        """
        try:
            # Query with eager loading
            query = self.db.query(Backup).options(
                joinedload(Backup.device).joinedload(Device.site),
                joinedload(Backup.device).joinedload(Device.tenant)
            ).filter(Backup.id == backup_id)
            
            # Apply tenant filtering through device relationship
            if not allow_cross_tenant or not self.is_superadmin:
                if self.tenant_id:
                    query = query.join(Device).filter(Device.tenant_id == self.tenant_id)
                else:
                    # If no tenant_id, return None
                    return None
            
            backup = query.first()
            
            if backup:
                # Log audit event
                self._log_audit_event(
                    action="get",
                    resource_type="backup",
                    resource_id=backup.id,
                    device_id=backup.device_id,
                    result="success"
                )
                
                logger.debug(f"Retrieved backup {backup_id}")
            else:
                # Log failed access attempt
                self._log_audit_event(
                    action="get",
                    resource_type="backup",
                    resource_id=backup_id,
                    result="not_found"
                )
                
                logger.debug(f"Backup {backup_id} not found or not accessible")
            
            return backup
            
        except Exception as e:
            logger.error(f"Failed to get backup {backup_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="get",
                resource_type="backup",
                resource_id=backup_id,
                result="error"
            )
            raise
    
    def delete_backup(self, backup_id: Union[str, UUID]) -> bool:
        """
        Delete existing backup.
        
        Args:
            backup_id: ID of the backup to delete.
            
        Returns:
            bool: True if backup was deleted, False if not found.
        """
        try:
            # Get existing backup to ensure tenant access
            backup = self.get_backup(backup_id)
            if not backup:
                return False
            
            # Capture backup info for audit log
            backup_info = {
                'device_id': str(backup.device_id),
                'type': backup.type.value,
                'size': backup.size,
                'storage_path': backup.storage_path
            }
            
            # Delete backup using base service method
            self.delete_resource(backup)
            
            # Log successful deletion
            self._log_audit_event(
                action="delete",
                resource_type="backup",
                resource_id=backup_id,
                device_id=backup.device_id,
                before_value=backup_info,
                result="success"
            )
            
            logger.info(f"Deleted backup {backup_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="delete",
                resource_type="backup",
                resource_id=backup_id,
                result="error"
            )
            raise
    
    def get_backup_stats(self, allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        Get backup statistics for the current tenant.
        
        Args:
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Backup statistics including counts by type, total size, etc.
        """
        try:
            # Base query with tenant filtering
            query = self.db.query(Backup)
            
            # Apply tenant filtering through device relationship
            if not allow_cross_tenant or not self.is_superadmin:
                if self.tenant_id:
                    query = query.join(Device).filter(Device.tenant_id == self.tenant_id)
                else:
                    # If no tenant_id, return empty stats
                    return {
                        "total_backups": 0,
                        "by_type": {t.value: 0 for t in BackupType},
                        "total_size": 0,
                        "compressed_backups": 0,
                        "recent_backups": 0
                    }
            
            # Get all backups for statistics
            backups = query.all()
            
            # Calculate statistics
            total_backups = len(backups)
            
            # Count by type
            by_type = {t.value: 0 for t in BackupType}
            for backup in backups:
                by_type[backup.type.value] += 1
            
            # Calculate total size
            total_size = sum(backup.size for backup in backups)
            
            # Count compressed backups
            compressed_backups = sum(1 for backup in backups if backup.compressed)
            
            # Count recent backups (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_backups = sum(
                1 for backup in backups 
                if backup.created_at >= cutoff_time
            )
            
            stats = {
                "total_backups": total_backups,
                "by_type": by_type,
                "total_size": total_size,
                "compressed_backups": compressed_backups,
                "recent_backups": recent_backups
            }
            
            # Log audit event
            self._log_audit_event(
                action="get_stats",
                resource_type="backup",
                result="success"
            )
            
            logger.debug(f"Generated backup statistics: {total_backups} total backups")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {e}")
            # Log failure
            self._log_audit_event(
                action="get_stats",
                resource_type="backup",
                result="error"
            )
            raise
    
    def get_device_backups(
        self,
        device_id: Union[str, UUID],
        limit: Optional[int] = None
    ) -> List[Backup]:
        """
        Get backups for a specific device.
        
        Args:
            device_id: ID of the device.
            limit: Maximum number of backups to return (optional).
            
        Returns:
            list: List of backups for the device, ordered by creation date (newest first).
        """
        try:
            # Verify device access through tenant isolation
            device_query = self.db.query(Device).filter(Device.id == device_id)
            if not self.is_superadmin and self.tenant_id:
                device_query = device_query.filter(Device.tenant_id == self.tenant_id)
            
            device = device_query.first()
            if not device:
                logger.debug(f"Device {device_id} not found or not accessible")
                return []
            
            # Query backups for the device
            query = self.db.query(Backup).filter(
                Backup.device_id == device_id
            ).order_by(desc(Backup.created_at))
            
            if limit:
                query = query.limit(limit)
            
            backups = query.all()
            
            # Log audit event
            self._log_audit_event(
                action="get_device_backups",
                resource_type="backup",
                device_id=device_id,
                result="success"
            )
            
            logger.debug(f"Retrieved {len(backups)} backups for device {device_id}")
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to get backups for device {device_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="get_device_backups",
                resource_type="backup",
                device_id=device_id,
                result="error"
            )
            raise