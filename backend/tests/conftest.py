"""
Test configuration and fixtures.

This module provides common test fixtures for the backend tests.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.models.base import BaseModel
from app.models.tenant import Tenant
from app.models.device import Device, DeviceStatus
from app.models.backup import Backup, BackupType


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_tenant(db_session):
    """Create a sample tenant for testing."""
    tenant = Tenant(
        name="Test Tenant",
        status="active"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def sample_device(db_session, sample_tenant):
    """Create a sample device for testing."""
    device = Device(
        tenant_id=sample_tenant.id,
        hostname="test-device",
        ip_address="192.168.1.1",
        status=DeviceStatus.MANAGED,
        ros_version="7.10",
        model="RB4011iGS+",
        last_seen=datetime.utcnow()
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def other_tenant(db_session):
    """Create another tenant for testing tenant isolation."""
    tenant = Tenant(
        name="Other Tenant",
        status="active"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def sample_backups(db_session, sample_device):
    """Create sample backups for testing."""
    backups = []
    
    # Create different types of backups
    backup1 = Backup(
        device_id=sample_device.id,
        type=BackupType.EXPORT,
        storage_path="/path/to/export/backup1",
        size=1024,
        checksum="checksum1",
        compressed=True
    )
    
    backup2 = Backup(
        device_id=sample_device.id,
        type=BackupType.BINARY,
        storage_path="/path/to/binary/backup2",
        size=2048,
        checksum="checksum2",
        compressed=False
    )
    
    backup3 = Backup(
        device_id=sample_device.id,
        type=BackupType.EXPORT,
        storage_path="/path/to/export/backup3",
        size=1536,
        checksum="checksum3",
        compressed=True
    )
    
    backups.extend([backup1, backup2, backup3])
    
    db_session.add_all(backups)
    db_session.commit()
    
    for backup in backups:
        db_session.refresh(backup)
    
    return backups