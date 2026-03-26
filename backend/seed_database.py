#!/usr/bin/env python3
"""
Database seeding script for development and testing.

This script creates initial data including:
- Roles and permissions
- Test tenant
- Test users with different roles
- Sample devices
"""

import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import db_manager, init_db
from app.models.base import Base
from app.models.tenant import Tenant, TenantStatus
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.site import Site
from app.models.device import Device, DeviceStatus
from app.models.device_credential import DeviceCredential
from app.core.security import hash_password
from app.utils.crypto import encrypt_credential


def create_roles_and_permissions(db: Session):
    """Create default roles and permissions."""
    print("Creating roles and permissions...")
    
    # Define roles
    roles_data = [
        {
            "name": "SuperAdmin",
            "description": "Full system access across all tenants"
        },
        {
            "name": "TenantAdmin",
            "description": "Full access within tenant"
        },
        {
            "name": "SiteManager",
            "description": "Manage devices within assigned sites"
        },
        {
            "name": "Operator",
            "description": "Execute operations on devices"
        },
        {
            "name": "Viewer",
            "description": "Read-only access"
        }
    ]
    
    roles = {}
    for role_data in roles_data:
        # Check if role already exists
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing_role:
            roles[role_data["name"]] = existing_role
            print(f"  ✓ Role '{role_data['name']}' already exists")
        else:
            role = Role(**role_data)
            db.add(role)
            db.flush()
            roles[role_data["name"]] = role
            print(f"  ✓ Created role: {role_data['name']}")
    
    # Define permissions for each role
    permissions_data = {
        "SuperAdmin": [
            # All permissions
            ("device", "read"), ("device", "write"), ("device", "delete"),
            ("template", "read"), ("template", "write"), ("template", "delete"),
            ("job", "read"), ("job", "write"),
            ("backup", "read"), ("backup", "write"), ("backup", "delete"),
            ("alert", "read"), ("alert", "write"),
            ("user", "read"), ("user", "write"), ("user", "delete"),
            ("audit", "read"),
        ],
        "TenantAdmin": [
            ("device", "read"), ("device", "write"), ("device", "delete"),
            ("template", "read"), ("template", "write"), ("template", "delete"),
            ("job", "read"), ("job", "write"),
            ("backup", "read"), ("backup", "write"), ("backup", "delete"),
            ("alert", "read"), ("alert", "write"),
            ("user", "read"), ("user", "write"),
            ("audit", "read"),
        ],
        "SiteManager": [
            ("device", "read"), ("device", "write"),
            ("template", "read"), ("template", "write"),
            ("job", "read"), ("job", "write"),
            ("backup", "read"), ("backup", "write"),
            ("alert", "read"), ("alert", "write"),
        ],
        "Operator": [
            ("device", "read"),
            ("template", "read"),
            ("job", "read"), ("job", "write"),
            ("backup", "read"),
            ("alert", "read"),
        ],
        "Viewer": [
            ("device", "read"),
            ("template", "read"),
            ("job", "read"),
            ("backup", "read"),
            ("alert", "read"),
        ]
    }
    
    for role_name, perms in permissions_data.items():
        role = roles[role_name]
        
        # Check if permissions already exist
        existing_perms = db.query(Permission).filter(Permission.role_id == role.id).count()
        if existing_perms > 0:
            print(f"  ✓ Permissions for '{role_name}' already exist")
            continue
        
        for resource, action in perms:
            permission = Permission(
                role_id=role.id,
                resource=resource,
                action=action
            )
            db.add(permission)
        
        print(f"  ✓ Created {len(perms)} permissions for {role_name}")
    
    db.commit()
    return roles


def create_test_tenant(db: Session):
    """Create test tenant."""
    print("\nCreating test tenant...")
    
    # Check if tenant already exists
    existing_tenant = db.query(Tenant).filter(Tenant.name == "Test Company").first()
    if existing_tenant:
        print("  ✓ Test tenant already exists")
        return existing_tenant
    
    tenant = Tenant(
        name="Test Company",
        status=TenantStatus.ACTIVE
    )
    db.add(tenant)
    db.commit()
    
    print(f"  ✓ Created tenant: {tenant.name} (ID: {tenant.id})")
    return tenant


def create_test_users(db: Session, tenant: Tenant, roles: dict):
    """Create test users with different roles."""
    print("\nCreating test users...")
    
    users_data = [
        {
            "email": "admin@test.com",
            "password": "admin123",
            "role": "TenantAdmin"
        },
        {
            "email": "manager@test.com",
            "password": "manager123",
            "role": "SiteManager"
        },
        {
            "email": "operator@test.com",
            "password": "operator123",
            "role": "Operator"
        },
        {
            "email": "viewer@test.com",
            "password": "viewer123",
            "role": "Viewer"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"  ✓ User '{user_data['email']}' already exists")
            created_users.append(existing_user)
            continue
        
        user = User(
            tenant_id=tenant.id,
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            role_id=roles[user_data["role"]].id,
            is_active=True
        )
        db.add(user)
        db.flush()
        created_users.append(user)
        
        print(f"  ✓ Created user: {user_data['email']} (Role: {user_data['role']}, Password: {user_data['password']})")
    
    db.commit()
    return created_users


def create_test_site(db: Session, tenant: Tenant):
    """Create test site."""
    print("\nCreating test site...")
    
    # Check if site already exists
    existing_site = db.query(Site).filter(
        Site.tenant_id == tenant.id,
        Site.name == "Main Office"
    ).first()
    if existing_site:
        print("  ✓ Test site already exists")
        return existing_site
    
    site = Site(
        tenant_id=tenant.id,
        name="Main Office",
        address="123 Main St, City, Country",
        metadata={"timezone": "UTC", "contact": "admin@test.com"}
    )
    db.add(site)
    db.commit()
    
    print(f"  ✓ Created site: {site.name} (ID: {site.id})")
    return site


def create_test_devices(db: Session, tenant: Tenant, site: Site):
    """Create test devices."""
    print("\nCreating test devices...")
    
    devices_data = [
        {
            "hostname": "router-01",
            "ip_address": "192.168.1.1",
            "model": "RB4011iGS+",
            "username": "admin",
            "password": "admin123"
        },
        {
            "hostname": "router-02",
            "ip_address": "192.168.1.2",
            "model": "hEX S",
            "username": "admin",
            "password": "admin123"
        },
        {
            "hostname": "router-03",
            "ip_address": "192.168.1.3",
            "model": "CCR1009",
            "username": "admin",
            "password": "admin123"
        }
    ]
    
    created_devices = []
    for device_data in devices_data:
        # Check if device already exists
        existing_device = db.query(Device).filter(
            Device.tenant_id == tenant.id,
            Device.hostname == device_data["hostname"]
        ).first()
        if existing_device:
            print(f"  ✓ Device '{device_data['hostname']}' already exists")
            created_devices.append(existing_device)
            continue
        
        # Create device
        device = Device(
            tenant_id=tenant.id,
            site_id=site.id,
            hostname=device_data["hostname"],
            ip_address=device_data["ip_address"],
            model=device_data["model"],
            status=DeviceStatus.PENDING_ADOPTION,
            ros_version="7.10",
            ros_major=7,
            architecture="arm64"
        )
        db.add(device)
        db.flush()
        
        # Create encrypted credentials
        credential = DeviceCredential(
            device_id=device.id,
            username=device_data["username"],
            password_encrypted=encrypt_credential(device_data["password"])
        )
        db.add(credential)
        
        created_devices.append(device)
        print(f"  ✓ Created device: {device_data['hostname']} ({device_data['ip_address']})")
    
    db.commit()
    return created_devices


def main():
    """Main seeding function."""
    print("🌱 Seeding database with test data...\n")
    
    # Initialize database manager
    init_db()
    
    # Create database session using context manager
    try:
        with db_manager.get_session() as db:
            # Create roles and permissions
            roles = create_roles_and_permissions(db)
            
            # Create test tenant
            tenant = create_test_tenant(db)
            
            # Create test users
            users = create_test_users(db, tenant, roles)
            
            # Create test site
            site = create_test_site(db, tenant)
            
            # Create test devices
            devices = create_test_devices(db, tenant, site)
            
            print("\n✅ Database seeding complete!")
            print("\n📝 Test Credentials:")
            print("  Admin:    admin@test.com / admin123")
            print("  Manager:  manager@test.com / manager123")
            print("  Operator: operator@test.com / operator123")
            print("  Viewer:   viewer@test.com / viewer123")
            print("\n🚀 You can now test the API with these credentials!")
            
            return 0
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
