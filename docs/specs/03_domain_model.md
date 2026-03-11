# Domain Model Specification

## Core Entities

Tenant  
Site  
Device  
DeviceCredential  
DeviceCapabilities  
Template  
TemplateVersion  
AdoptionRequest  
Job  
JobResult  
BackupArtifact  
Alert  
AuditEvent  
User  
Role  
Policy  

## Tenant

Represents an organization.

Fields:

tenant_id  
name  
status  
created_at  
updated_at  

Relationships:

Tenant → Sites  
Tenant → Devices  
Tenant → Users  
Tenant → Templates  

## Site

Represents a physical location.

Fields:

site_id  
tenant_id  
name  
address  
metadata  
created_at  

Relationships:

Site → Devices

## Device

Represents a MikroTik router.

Fields:

device_id  
tenant_id  
site_id  
hostname  
ip_address  
ros_version  
ros_major  
architecture  
model  
serial_number  
status  
last_seen  
created_at  

Device lifecycle states:

unregistered  
discovered  
pending_adoption  
adopted  
managed  
offline  
error  
retired
