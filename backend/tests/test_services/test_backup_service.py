"""
Unit tests for BackupService.

This module tests the backup service functionality including
listing, retrieving, and deleting backups with tenant isolation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.backup import Backup, BackupType
from app.models.device import Device, DeviceStatus
from app.models.tenant import Tenant
from app.schemas.backup import BackupFilterParams
from app.services.backup_service import BackupService


class TestBackupService:
    """Test cases for BackupService."""
    
    def test_list_backups_empty(self, db_session, sample_tenant):
        """Test listing backups when none exist."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.list_backups()
        
        assert result["total_count"] == 0
        assert result["items"] == []
        assert result["page"] == 1
        assert result["total_pages"] == 0
    
    def test_list_backups_with_data(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test listing backups with existing data."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.list_backups()
        
        assert result["total_count"] == len(sample_backups)
        assert len(result["items"]) == len(sample_backups)
        assert result["page"] == 1
        
        # Verify backups are ordered by creation date (newest first)
        items = result["items"]
        for i in range(len(items) - 1):
            assert items[i].created_at >= items[i + 1].created_at
    
    def test_list_backups_with_device_filter(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test listing backups filtered by device ID."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        # Filter by specific device
        filters = BackupFilterParams(device_id=sample_device.id)
        result = service.list_backups(filters=filters)
        
        assert result["total_count"] > 0
        for backup in result["items"]:
            assert backup.device_id == sample_device.id
    
    def test_list_backups_with_type_filter(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test listing backups filtered by type."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        # Filter by export type
        filters = BackupFilterParams(type=BackupType.EXPORT)
        result = service.list_backups(filters=filters)
        
        for backup in result["items"]:
            assert backup.type == BackupType.EXPORT
    
    def test_list_backups_with_date_filter(self, db_session, sample_tenant, sample_device):
        """Test listing backups filtered by date range."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        # Create backups with specific dates
        old_date = datetime.utcnow() - timedelta(days=7)
        recent_date = datetime.utcnow() - timedelta(hours=1)
        
        old_backup = Backup(
            device_id=sample_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/old/backup",
            size=1000,
            checksum="old_checksum",
            created_at=old_date
        )
        
        recent_backup = Backup(
            device_id=sample_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/recent/backup",
            size=2000,
            checksum="recent_checksum",
            created_at=recent_date
        )
        
        db_session.add_all([old_backup, recent_backup])
        db_session.commit()
        
        # Filter by date range (last 2 days)
        start_date = datetime.utcnow() - timedelta(days=2)
        filters = BackupFilterParams(start_date=start_date)
        result = service.list_backups(filters=filters)
        
        # Should only return recent backup
        assert result["total_count"] == 1
        assert result["items"][0].id == recent_backup.id
    
    def test_list_backups_pagination(self, db_session, sample_tenant, sample_device):
        """Test backup listing pagination."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        # Create multiple backups
        backups = []
        for i in range(5):
            backup = Backup(
                device_id=sample_device.id,
                type=BackupType.EXPORT,
                storage_path=f"/path/to/backup_{i}",
                size=1000 + i,
                checksum=f"checksum_{i}"
            )
            backups.append(backup)
        
        db_session.add_all(backups)
        db_session.commit()
        
        # Test pagination
        result = service.list_backups(page=1, page_size=2)
        
        assert result["total_count"] == 5
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["total_pages"] == 3
        assert result["has_next"] is True
        assert result["has_prev"] is False
    
    def test_list_backups_tenant_isolation(self, db_session, sample_tenant):
        """Test that backups are properly isolated by tenant."""
        # Create another tenant and device
        other_tenant = Tenant(name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.flush()
        
        other_device = Device(
            tenant_id=other_tenant.id,
            hostname="other-device",
            ip_address="192.168.2.1",
            status=DeviceStatus.MANAGED
        )
        db_session.add(other_device)
        db_session.flush()
        
        # Create backup for other tenant
        other_backup = Backup(
            device_id=other_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/other/backup",
            size=1000,
            checksum="other_checksum"
        )
        db_session.add(other_backup)
        db_session.commit()
        
        # Service for original tenant should not see other tenant's backups
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        result = service.list_backups()
        
        for backup in result["items"]:
            assert backup.device.tenant_id == sample_tenant.id
    
    def test_get_backup_success(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test getting a backup by ID."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        backup = sample_backups[0]
        
        result = service.get_backup(backup.id)
        
        assert result is not None
        assert result.id == backup.id
        assert result.device_id == backup.device_id
    
    def test_get_backup_not_found(self, db_session, sample_tenant):
        """Test getting a non-existent backup."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.get_backup(uuid4())
        
        assert result is None
    
    def test_get_backup_tenant_isolation(self, db_session, sample_tenant):
        """Test that get_backup respects tenant isolation."""
        # Create another tenant and backup
        other_tenant = Tenant(name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.flush()
        
        other_device = Device(
            tenant_id=other_tenant.id,
            hostname="other-device",
            ip_address="192.168.2.1",
            status=DeviceStatus.MANAGED
        )
        db_session.add(other_device)
        db_session.flush()
        
        other_backup = Backup(
            device_id=other_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/other/backup",
            size=1000,
            checksum="other_checksum"
        )
        db_session.add(other_backup)
        db_session.commit()
        
        # Service for original tenant should not access other tenant's backup
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        result = service.get_backup(other_backup.id)
        
        assert result is None
    
    def test_delete_backup_success(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test deleting a backup."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        backup = sample_backups[0]
        backup_id = backup.id
        
        result = service.delete_backup(backup_id)
        
        assert result is True
        
        # Verify backup is deleted
        deleted_backup = db_session.query(Backup).filter(Backup.id == backup_id).first()
        assert deleted_backup is None
    
    def test_delete_backup_not_found(self, db_session, sample_tenant):
        """Test deleting a non-existent backup."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.delete_backup(uuid4())
        
        assert result is False
    
    def test_delete_backup_tenant_isolation(self, db_session, sample_tenant):
        """Test that delete_backup respects tenant isolation."""
        # Create another tenant and backup
        other_tenant = Tenant(name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.flush()
        
        other_device = Device(
            tenant_id=other_tenant.id,
            hostname="other-device",
            ip_address="192.168.2.1",
            status=DeviceStatus.MANAGED
        )
        db_session.add(other_device)
        db_session.flush()
        
        other_backup = Backup(
            device_id=other_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/other/backup",
            size=1000,
            checksum="other_checksum"
        )
        db_session.add(other_backup)
        db_session.commit()
        
        # Service for original tenant should not delete other tenant's backup
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        result = service.delete_backup(other_backup.id)
        
        assert result is False
        
        # Verify backup still exists
        existing_backup = db_session.query(Backup).filter(Backup.id == other_backup.id).first()
        assert existing_backup is not None
    
    def test_get_backup_stats(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test getting backup statistics."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.get_backup_stats()
        
        assert "total_backups" in result
        assert "by_type" in result
        assert "total_size" in result
        assert "compressed_backups" in result
        assert "recent_backups" in result
        
        assert result["total_backups"] == len(sample_backups)
        assert isinstance(result["by_type"], dict)
        assert result["total_size"] > 0
    
    def test_get_device_backups(self, db_session, sample_tenant, sample_device, sample_backups):
        """Test getting backups for a specific device."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        result = service.get_device_backups(sample_device.id)
        
        assert len(result) > 0
        for backup in result:
            assert backup.device_id == sample_device.id
        
        # Verify ordering (newest first)
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at
    
    def test_get_device_backups_with_limit(self, db_session, sample_tenant, sample_device):
        """Test getting device backups with limit."""
        service = BackupService(db_session, tenant_id=str(sample_tenant.id))
        
        # Create multiple backups
        backups = []
        for i in range(5):
            backup = Backup(
                device_id=sample_device.id,
                type=BackupType.EXPORT,
                storage_path=f"/path/to/backup_{i}",
                size=1000 + i,
                checksum=f"checksum_{i}"
            )
            backups.append(backup)
        
        db_session.add_all(backups)
        db_session.commit()
        
        # Get limited results
        result = service.get_device_backups(sample_device.id, limit=2)
        
        assert len(result) == 2
    
    def test_superadmin_cross_tenant_access(self, db_session, sample_tenant):
        """Test that superadmin can access backups across tenants."""
        # Create another tenant and backup
        other_tenant = Tenant(name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.flush()
        
        other_device = Device(
            tenant_id=other_tenant.id,
            hostname="other-device",
            ip_address="192.168.2.1",
            status=DeviceStatus.MANAGED
        )
        db_session.add(other_device)
        db_session.flush()
        
        other_backup = Backup(
            device_id=other_device.id,
            type=BackupType.EXPORT,
            storage_path="/path/to/other/backup",
            size=1000,
            checksum="other_checksum"
        )
        db_session.add(other_backup)
        db_session.commit()
        
        # Superadmin service should access all backups
        service = BackupService(
            db_session, 
            tenant_id=str(sample_tenant.id),
            is_superadmin=True
        )
        
        # List all backups
        result = service.list_backups(allow_cross_tenant=True)
        backup_tenant_ids = {backup.device.tenant_id for backup in result["items"]}
        assert len(backup_tenant_ids) > 1  # Should see backups from multiple tenants
        
        # Get specific backup from other tenant
        result = service.get_backup(other_backup.id, allow_cross_tenant=True)
        assert result is not None
        assert result.id == other_backup.id