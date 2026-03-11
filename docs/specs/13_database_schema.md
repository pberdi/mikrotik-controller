# Database Schema Specification

## Purpose

This document defines the relational database schema used by the MikroTik Controller Platform.

The database must support multi-tenant isolation, job processing, configuration management and device inventory.

Primary database: PostgreSQL

---

# Core Tables

## tenants

tenant_id (UUID, PK)  
name (text)  
status (active, suspended)  
created_at (timestamp)  
updated_at (timestamp)

---

## sites

site_id (UUID, PK)  
tenant_id (FK → tenants)  
name (text)  
address (text)  
metadata (jsonb)  
created_at (timestamp)

---

## devices

device_id (UUID, PK)  
tenant_id (FK → tenants)  
site_id (FK → sites)  
hostname (text)  
ip_address (inet)  
ros_version (text)  
ros_major (integer)  
architecture (text)  
model (text)  
serial_number (text)  
status (enum)  
last_seen (timestamp)  
created_at (timestamp)

Indexes:

index_devices_tenant  
index_devices_status

---

## device_credentials

credential_id (UUID, PK)  
device_id (FK → devices)  
username (text)  
password_encrypted (text)  
private_key (text)  
created_at (timestamp)

Secrets must be encrypted.

---

## templates

template_id (UUID, PK)  
tenant_id (FK → tenants)  
name (text)  
type (declarative | script)  
created_at (timestamp)

---

## template_versions

version_id (UUID, PK)  
template_id (FK → templates)  
version (integer)  
content (text)  
created_by (user_id)  
created_at (timestamp)

---

## jobs

job_id (UUID, PK)  
tenant_id (FK → tenants)  
device_id (FK → devices)  
type (inventory | backup | template_apply | command)  
status (pending | running | success | failed)  
created_at (timestamp)  
started_at (timestamp)  
finished_at (timestamp)

---

## job_results

result_id (UUID, PK)  
job_id (FK → jobs)  
output (text)  
status (success | failed)  
timestamp (timestamp)

---

## backups

backup_id (UUID, PK)  
device_id (FK → devices)  
type (export | binary)  
storage_path (text)  
size (integer)  
hash (text)  
created_at (timestamp)

---

## alerts

alert_id (UUID, PK)  
device_id (FK → devices)  
severity (info | warning | critical)  
message (text)  
created_at (timestamp)

---

## audit_events

event_id (UUID, PK)  
user_id (FK → users)  
tenant_id (FK → tenants)  
device_id (FK → devices)  
action (text)  
result (text)  
timestamp (timestamp)

---

## users

user_id (UUID, PK)  
tenant_id (FK → tenants)  
email (text)  
password_hash (text)  
role_id (FK → roles)  
created_at (timestamp)

---

## roles

role_id (UUID, PK)  
name (text)

Example roles:

SuperAdmin  
Operator  
TenantAdmin  
Technician  
ReadOnly
