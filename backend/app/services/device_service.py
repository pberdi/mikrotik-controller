"""
Device service for managing MikroTik devices.

This module provides the DeviceService class for device management operations
including CRUD operations, credential encryption, and tenant isolation.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from .base_service import BaseService
from ..models.device import Device, DeviceStatus
from ..models.device_credential import DeviceCredential
from ..models.site import Site
from ..utils.crypto import encrypt_credential, decrypt_credential
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceFilterParams

logger = logging.getLogger(__name__)


class DeviceService(BaseService):
    """
    Service class for device management operations.
    
    Provides CRUD operations for devices with tenant isolation,
    credential encryption, and comprehensive audit logging.
    """
    
    def list_devices(
        self,
        filters: Optional[DeviceFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List devices with pagination and filtering.
        
        Args:
            filters: Filter parameters for device listing.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated device results with metadata.
        """
        # Start with base query including relationships for efficient loading
        query = self.db.query(Device).options(
            joinedload(Device.site),
            joinedload(Device.tenant)
        )
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, Device, allow_cross_tenant)
        
        # Apply filters if provided
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            
            # Handle special filters
            if 'online_only' in filter_dict:
                online_only = filter_dict.pop('online_only')
                if online_only:
                    # Consider devices online if they're managed and last_seen within 5 minutes
                    from datetime import datetime, timedelta
                    cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                    query = query.filter(
                        and_(
                            Device.status == DeviceStatus.MANAGED,
                            Device.last_seen >= cutoff_time
                        )
                    )
            
            # Apply remaining filters using base service method
            for field, value in filter_dict.items():
                if hasattr(Device, field) and value is not None:
                    if isinstance(value, list):
                        query = query.filter(getattr(Device, field).in_(value))
                    else:
                        query = query.filter(getattr(Device, field) == value)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        devices = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        result = {
            "items": devices,
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
            resource_type="device",
            result="success"
        )
        
        logger.info(
            f"Listed {len(devices)} devices "
            f"(page {page}/{total_pages}, total: {total_count})"
        )
        
        return result
    
    def get_device(
        self,
        device_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[Device]:
        """
        Get device by ID with tenant isolation.
        
        Args:
            device_id: ID of the device to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            Device: Device if found and accessible, None otherwise.
        """
        # Use base service method with eager loading
        query = self.db.query(Device).options(
            joinedload(Device.site),
            joinedload(Device.tenant),
            joinedload(Device.credentials)
        ).filter(Device.id == device_id)
        
        query = self._apply_tenant_filter(query, Device, allow_cross_tenant)
        device = query.first()
        
        if device:
            # Log audit event
            self._log_audit_event(
                action="get",
                resource_type="device",
                resource_id=device.id,
                device_id=device.id,
                result="success"
            )
            
            logger.debug(f"Retrieved device {device_id}")
        else:
            # Log failed access attempt
            self._log_audit_event(
                action="get",
                resource_type="device",
                resource_id=device_id,
                result="not_found"
            )
            
            logger.debug(f"Device {device_id} not found or not accessible")
        
        return device
    
    def create_device(self, device_data: DeviceCreate) -> Device:
        """
        Create new device with credential encryption.
        
        Args:
            device_data: Device creation data including credentials.
            
        Returns:
            Device: Created device.
            
        Raises:
            ValueError: If site_id is provided but site doesn't exist or belong to tenant.
            Exception: If device creation fails.
        """
        try:
            # Validate site_id if provided
            if device_data.site_id:
                site_query = self.db.query(Site).filter(Site.id == device_data.site_id)
                site_query = self._apply_tenant_filter(site_query, Site)
                site = site_query.first()
                
                if not site:
                    raise ValueError(f"Site {device_data.site_id} not found or not accessible")
            
            # Extract credentials from device data
            username = device_data.username
            password = device_data.password
            private_key = device_data.private_key
            
            # Create device data without credentials
            device_dict = device_data.model_dump(exclude={'username', 'password', 'private_key'})
            
            # Convert IP address to string for database storage
            device_dict['ip_address'] = str(device_data.ip_address)
            
            # Set initial status
            device_dict['status'] = DeviceStatus.PENDING_ADOPTION
            
            # Create device using base service method
            device = self.create_resource(Device, device_dict)
            
            # Encrypt and store credentials
            encrypted_password = encrypt_credential(password)
            
            credential_data = {
                'device_id': device.id,
                'username': username,
                'password_encrypted': encrypted_password,
                'private_key': private_key
            }
            
            credential = DeviceCredential(**credential_data)
            self.db.add(credential)
            self.db.flush()
            
            # Log credential creation (without sensitive data)
            self._log_audit_event(
                action="create_credentials",
                resource_type="device_credential",
                resource_id=credential.id,
                device_id=device.id,
                result="success"
            )
            
            logger.info(f"Created device {device.id} with encrypted credentials")
            
            return device
            
        except Exception as e:
            logger.error(f"Failed to create device: {e}")
            # Log failure
            self._log_audit_event(
                action="create",
                resource_type="device",
                result="error"
            )
            raise
    
    def update_device(
        self,
        device_id: Union[str, UUID],
        device_data: DeviceUpdate
    ) -> Optional[Device]:
        """
        Update existing device.
        
        Args:
            device_id: ID of the device to update.
            device_data: Updated device data.
            
        Returns:
            Device: Updated device if found and accessible, None otherwise.
            
        Raises:
            ValueError: If site_id is provided but site doesn't exist or belong to tenant.
        """
        # Get existing device
        device = self.get_device(device_id)
        if not device:
            return None
        
        try:
            # Validate site_id if provided
            if device_data.site_id is not None:
                if device_data.site_id:  # Not None and not empty
                    site_query = self.db.query(Site).filter(Site.id == device_data.site_id)
                    site_query = self._apply_tenant_filter(site_query, Site)
                    site = site_query.first()
                    
                    if not site:
                        raise ValueError(f"Site {device_data.site_id} not found or not accessible")
            
            # Prepare update data
            update_dict = device_data.model_dump(exclude_none=True)
            
            # Convert IP address to string if provided
            if 'ip_address' in update_dict:
                update_dict['ip_address'] = str(device_data.ip_address)
            
            # Update device using base service method
            updated_device = self.update_resource(device, update_dict)
            
            logger.info(f"Updated device {device_id}")
            
            return updated_device
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="update",
                resource_type="device",
                resource_id=device_id,
                device_id=device_id,
                result="error"
            )
            raise
    
    def delete_device(self, device_id: Union[str, UUID]) -> bool:
        """
        Delete existing device and its credentials.
        
        Args:
            device_id: ID of the device to delete.
            
        Returns:
            bool: True if device was deleted, False if not found.
        """
        # Get existing device
        device = self.get_device(device_id)
        if not device:
            return False
        
        try:
            # Delete device using base service method (credentials will cascade)
            self.delete_resource(device)
            
            logger.info(f"Deleted device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device {device_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="delete",
                resource_type="device",
                resource_id=device_id,
                device_id=device_id,
                result="error"
            )
            raise
    
    def get_device_credentials(
        self,
        device_id: Union[str, UUID]
    ) -> Optional[Dict[str, str]]:
        """
        Get decrypted device credentials.
        
        Args:
            device_id: ID of the device.
            
        Returns:
            dict: Decrypted credentials if found, None otherwise.
            
        Note:
            This method returns decrypted credentials and should be used carefully.
            Credentials are never logged or exposed in audit logs.
        """
        # Get device to ensure tenant access
        device = self.get_device(device_id)
        if not device:
            return None
        
        try:
            # Get credentials
            credential = self.db.query(DeviceCredential).filter(
                DeviceCredential.device_id == device_id
            ).first()
            
            if not credential:
                logger.debug(f"No credentials found for device {device_id}")
                return None
            
            # Decrypt password
            decrypted_password = decrypt_credential(credential.password_encrypted)
            
            # Log credential access (without sensitive data)
            self._log_audit_event(
                action="get_credentials",
                resource_type="device_credential",
                resource_id=credential.id,
                device_id=device_id,
                result="success"
            )
            
            logger.debug(f"Retrieved credentials for device {device_id}")
            
            return {
                'username': credential.username,
                'password': decrypted_password,
                'private_key': credential.private_key
            }
            
        except Exception as e:
            logger.error(f"Failed to get credentials for device {device_id}: {e}")
            # Log failure (without sensitive data)
            self._log_audit_event(
                action="get_credentials",
                resource_type="device_credential",
                device_id=device_id,
                result="error"
            )
            return None
    
    def update_device_credentials(
        self,
        device_id: Union[str, UUID],
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> bool:
        """
        Update device credentials with encryption.
        
        Args:
            device_id: ID of the device.
            username: New username (optional).
            password: New password (optional).
            private_key: New private key (optional).
            
        Returns:
            bool: True if credentials were updated, False if device not found.
        """
        # Get device to ensure tenant access
        device = self.get_device(device_id)
        if not device:
            return False
        
        try:
            # Get existing credentials
            credential = self.db.query(DeviceCredential).filter(
                DeviceCredential.device_id == device_id
            ).first()
            
            if not credential:
                logger.error(f"No credentials found for device {device_id}")
                return False
            
            # Capture before state (without sensitive data)
            before_value = {
                'username': credential.username,
                'has_private_key': bool(credential.private_key)
            }
            
            # Update fields
            if username is not None:
                credential.username = username
            
            if password is not None:
                credential.password_encrypted = encrypt_credential(password)
            
            if private_key is not None:
                credential.private_key = private_key
            
            self.db.flush()
            
            # Capture after state (without sensitive data)
            after_value = {
                'username': credential.username,
                'has_private_key': bool(credential.private_key)
            }
            
            # Log credential update (without sensitive data)
            self._log_audit_event(
                action="update_credentials",
                resource_type="device_credential",
                resource_id=credential.id,
                device_id=device_id,
                before_value=before_value,
                after_value=after_value,
                result="success"
            )
            
            logger.info(f"Updated credentials for device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update credentials for device {device_id}: {e}")
            # Log failure (without sensitive data)
            self._log_audit_event(
                action="update_credentials",
                resource_type="device_credential",
                device_id=device_id,
                result="error"
            )
            return False
    
    def get_device_stats(self, allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        Get device statistics for the current tenant.
        
        Args:
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Device statistics including counts by status, model, etc.
        """
        try:
            # Base query with tenant filtering
            query = self.db.query(Device)
            query = self._apply_tenant_filter(query, Device, allow_cross_tenant)
            
            # Get all devices for statistics
            devices = query.all()
            
            # Calculate statistics
            total_devices = len(devices)
            
            # Count by status
            by_status = {}
            for status in DeviceStatus:
                by_status[status.value] = sum(1 for d in devices if d.status == status)
            
            # Count by model
            by_model = {}
            for device in devices:
                model = device.model or "Unknown"
                by_model[model] = by_model.get(model, 0) + 1
            
            # Count online/offline devices
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            online_devices = sum(
                1 for d in devices 
                if d.status == DeviceStatus.MANAGED and d.last_seen and d.last_seen >= cutoff_time
            )
            offline_devices = total_devices - online_devices
            
            stats = {
                "total_devices": total_devices,
                "by_status": by_status,
                "by_model": by_model,
                "online_devices": online_devices,
                "offline_devices": offline_devices
            }
            
            # Log audit event
            self._log_audit_event(
                action="get_stats",
                resource_type="device",
                result="success"
            )
            
            logger.debug(f"Generated device statistics: {total_devices} total devices")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get device statistics: {e}")
            # Log failure
            self._log_audit_event(
                action="get_stats",
                resource_type="device",
                result="error"
            )
            raise