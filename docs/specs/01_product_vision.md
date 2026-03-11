# MikroTik Controller Platform
## Product Vision Specification

### Purpose

The MikroTik Controller Platform is a SaaS multi-tenant system designed to centrally manage fleets of MikroTik routers.

The system enables Managed Service Providers (MSPs), WISPs and enterprise network operators to manage distributed RouterOS infrastructures from a single control plane.

The platform provides functionality conceptually similar to UniFi Controller or Aruba Central but specifically optimized for RouterOS environments.

### Core Goals

Centralized device management  
Automated configuration deployment  
Secure remote operations  
Inventory and monitoring  
Configuration backups  
Multi-tenant isolation  

### Target Users

MSP Administrator  
Global platform administrator.

MSP Operator  
Operations engineer managing devices.

Tenant Administrator  
Customer administrator with limited scope.

Field Technician  
Responsible for installing and bootstrapping routers.

### Core Capabilities

Device discovery  
Device adoption  
Configuration templates  
Remote command execution  
Configuration backup  
Alerting  
Audit logging  

### Design Principles

API-first architecture  
Multi-tenant isolation  
Horizontal scalability  
Secure secret handling  
Asynchronous operations
