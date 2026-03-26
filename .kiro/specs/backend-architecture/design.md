    # Backend Architecture Design Document

## Overview

The Backend Architecture provides the foundational infrastructure for a multi-tenant SaaS platform that enables centralized management of MikroTik router fleets. This design document specifies the technical implementation of a horizontally scalable system supporting 500 to 10,000+ routers with comprehensive device management, configuration automation, backup operations, alerting, and audit logging capabilities.

### System Context

The backend serves as the core orchestration layer between the frontend UI and MikroTik devices. It exposes RESTful APIs for client interactions, processes long-running operations asynchronously through a job queue system, maintains multi-tenant data isolation, and provides real-time updates via WebSocket connections.

### Key Design Goals

- **Multi-tenancy**: Strict data isolation between customer organizations with row-level security
- **Scalability**: Horizontal scaling from 500 to 10,000+ devices through stateless API design and distributed job processing
- **Reliability**: Asynchronous job processing with retry logic, graceful degradation, and comprehensive error handling
- **Security**: JWT authentication, RBAC authorization, encrypted credential storage, and complete audit logging
- **Observability**: Structured logging, Prometheus metrics, distributed tracing, and health check endpoints
- **Developer Experience**: Clear project structure, comprehensive API documentation, dependency injection, and testing infrastructure

## Architecture

### High-Level Component Architecture

```mermaid
graph TB
    Client[Frontend Client]
    LB[Load Balancer]
    API1[API Instance 1]
    API2[API Instance 2]
    API3[API Instance N]
    Worker1[Worker Instance 1]
    Worker2[Worker Instance 2]
    Worker3[Worker Instance N]
    DB[(PostgreSQL)]
    Redis[(Redis)]
    Devices[MikroTik Devices]
    
    Client -->|HTTPS| LB
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 -->|SQL| DB
    API2 -->|SQL| DB
    API3 -->|SQL| DB
    
    API1 -->|Pub/Sub| Redis
    API2 -->|Pub/Sub| Redis
    API3 -->|Pub/Sub| Redis
    
    API1 -->|Enqueue Jobs| Redis
    API2 -->|Enqueue Jobs| Redis
    API3 -->|Enqueue Jobs| Redis
    
    Worker1 -->|Consume Jobs| Redis
    Worker2 -->|Consume Jobs| Redis
    Worker3 -->|Consume Jobs| Redis
    
    Worker1 -->|SQL| DB
    Worker2 -->|SQL| DB
    Worker3 -->|SQL| DB
    
    Worker1 -->|RouterOS API| Devices
    Worker2 -->|RouterOS API| Devices
    Worker3 -->|RouterOS API| Devices
```

### Component Responsibilities

**API Backend (FastAPI)**
- Exposes RESTful endpoints for all client operations
- Handles authentication and authorization
- Validates request/response data using Pydantic schemas
- Enforces multi-tenant isolation
- Enqueues asynchronous jobs to Redis
- Provides WebSocket connections for real-time updates
- Serves health check and metrics endpoints

**Worker Engine (Celery)**
- Processes asynchronous jobs from Redis queues
- Executes device operations (connectivity checks, backups, template application, command execution)
- Communicates with MikroTik devices via RouterOS API
- Updates job status and results in database
- Implements retry logic with exponential backoff
- Generates alerts based on job outcomes

**Database (PostgreSQL + SQLAlchemy)**
- Stores all persistent data with multi-tenant isolation
- Enforces referential integrity through foreign key constraints
- Provides ACID transactions for data consistency
- Supports connection pooling for efficient resource usage
- Enables query optimization through strategic indexing

**Redis**
- Message broker for Celery job queue
- Result backend for job status and output
- Pub/sub for cross-instance WebSocket message distribution
- Distributed rate limiting state
- API response caching layer
- Session storage for stateless API instances

**MikroTik Connector**
- Abstracts RouterOS API communication
- Manages device connections with timeout handling
- Retrieves credentials from encrypted storage
- Executes commands and retrieves configurations
- Handles connection errors and retries

**Template Engine (Jinja2)**
- Parses and validates configuration templates
- Renders templates with device-specific variables
- Supports conditional logic and loops
- Validates rendered output against RouterOS syntax

**Secret Vault**
- Encrypts device credentials using AES-256
- Derives encryption keys from master secret using PBKDF2
- Provides secure credential storage and retrieval
- Supports key rotation
- Never logs or exposes decrypted credentials

**Backup Storage**
- Stores device configuration backups with compression
- Calculates and verifies SHA-256 checksums
- Implements retention policies
- Provides backup retrieval and restore capabilities

**Alerting Engine**
- Creates alerts for device issues and job failures
- Tracks alert status (Active, Acknowledged, Resolved)
- Prevents duplicate alerts within time windows
- Enqueues notification jobs for critical alerts

**Audit System**
- Logs all API requests with user context
- Logs all database mutations
- Logs all device operations
- Logs authentication attempts and permission failures
- Provides queryable audit trail for compliance

### Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "API Containers"
            API1[api-1]
            API2[api-2]
        end
        
        subgraph "Worker Containers"
            Worker1[worker-1]
            Worker2[worker-2]
        end
        
        subgraph "Infrastructure"
            DB[PostgreSQL]
            Redis[Redis]
        end
        
        Nginx[Nginx Load Balancer]
    end
    
    Internet[Internet] --> Nginx
    Nginx --> API1
    Nginx --> API2
    API1 --> DB
    API2 --> DB
    API1 --> Redis
    API2 --> Redis
    Worker1 --> Redis
    Worker2 --> Redis
    Worker1 --> DB
    Worker2 --> DB
```

## Components and Interfaces

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # FastAPI dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── devices.py      # Device endpoints
│   │   │   ├── templates.py    # Template endpoints
│   │   │   ├── jobs.py         # Job endpoints
│   │   │   ├── backups.py      # Backup endpoints
│   │   │   ├── alerts.py       # Alert endpoints
│   │   │   ├── users.py        # User endpoints
│   │   │   ├── audit.py        # Audit log endpoints
│   │   │   └── auth.py         # Authentication endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy base
│   │   ├── tenant.py           # Tenant model
│   │   ├── site.py             # Site model
│   │   ├── device.py           # Device model
│   │   ├── template.py         # Template model
│   │   ├── job.py              # Job model
│   │   ├── backup.py           # Backup model
│   │   ├── alert.py            # Alert model
│   │   ├── user.py             # User model
│   │   ├── role.py             # Role model
│   │   └── audit.py            # AuditLog model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── device.py           # Device Pydantic schemas
│   │   ├── template.py         # Template Pydantic schemas
│   │   ├── job.py              # Job Pydantic schemas
│   │   ├── backup.py           # Backup Pydantic schemas
│   │   ├── alert.py            # Alert Pydantic schemas
│   │   ├── user.py             # User Pydantic schemas
│   │   └── common.py           # Common schemas (pagination, etc.)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── device_service.py   # Device business logic
│   │   ├── template_service.py # Template business logic
│   │   ├── job_service.py      # Job business logic
│   │   ├── backup_service.py   # Backup business logic
│   │   ├── alert_service.py    # Alert business logic
│   │   ├── user_service.py     # User business logic
│   │   └── audit_service.py    # Audit business logic
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery configuration
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── device_tasks.py # Device operation tasks
│   │   │   ├── backup_tasks.py # Backup tasks
│   │   │   ├── template_tasks.py # Template application tasks
│   │   │   └── alert_tasks.py  # Alert notification tasks
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py         # Database session management
│   │   ├── security.py         # Authentication/authorization
│   │   ├── middleware.py       # Custom middleware
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── logging.py          # Logging configuration
│   │   └── metrics.py          # Prometheus metrics
│   │
│   ├── connectors/
│   │   ├── __init__.py
│   │   └── mikrotik.py         # MikroTik RouterOS API connector
│   │
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── template_engine.py  # Jinja2 template rendering
│   │   ├── backup_engine.py    # Backup operations
│   │   └── alert_engine.py     # Alert generation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── crypto.py           # Encryption utilities
│       ├── validators.py       # Custom validators
│       └── helpers.py          # Helper functions
│
├── alembic/
│   ├── versions/               # Migration scripts
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_api/               # API endpoint tests
│   ├── test_services/          # Service layer tests
│   ├── test_workers/           # Worker task tests
│   └── test_integration/       # Integration tests
│
├── docker/
│   ├── Dockerfile.api          # API container
│   ├── Dockerfile.worker       # Worker container
│   └── docker-compose.yml      # Development environment
│
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── alembic.ini                 # Alembic configuration
├── pytest.ini                  # Pytest configuration
└── README.md                   # Setup instructions
```

### API Endpoints Specification

#### Authentication Endpoints

**POST /api/v1/auth/login**
- Request: `{ "email": "user@example.com", "password": "secret" }`
- Response: `{ "access_token": "jwt_token", "refresh_token": "refresh_token", "token_type": "bearer" }`
- Status: 200 OK, 401 Unauthorized

**POST /api/v1/auth/refresh**
- Request: `{ "refresh_token": "refresh_token" }`
- Response: `{ "access_token": "new_jwt_token", "token_type": "bearer" }`
- Status: 200 OK, 401 Unauthorized

**POST /api/v1/auth/logout**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "message": "Logged out successfully" }`
- Status: 200 OK

#### Device Management Endpoints

**POST /api/v1/devices**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "hostname": "router1", "ip_address": "192.168.1.1", "site_id": "uuid", "username": "admin", "password": "secret" }`
- Response: `{ "device_id": "uuid", "hostname": "router1", "status": "pending_adoption", "created_at": "timestamp" }`
- Status: 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden

**GET /api/v1/devices**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&status=managed&site_id=uuid&sort=hostname:asc`
- Response: `{ "items": [...], "total_count": 100, "page": 1, "page_size": 50, "total_pages": 2 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/devices/{device_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "device_id": "uuid", "hostname": "router1", "ip_address": "192.168.1.1", "status": "managed", "ros_version": "7.10", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**PATCH /api/v1/devices/{device_id}**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "hostname": "new-router1", "site_id": "new-uuid" }`
- Response: `{ "device_id": "uuid", "hostname": "new-router1", ... }`
- Status: 200 OK, 400 Bad Request, 404 Not Found, 401 Unauthorized

**DELETE /api/v1/devices/{device_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "message": "Device deleted successfully" }`
- Status: 204 No Content, 404 Not Found, 401 Unauthorized

**POST /api/v1/devices/{device_id}/command**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "command": "/system resource print" }`
- Response: `{ "job_id": "uuid", "status": "pending" }`
- Status: 202 Accepted, 404 Not Found, 401 Unauthorized

#### Template Management Endpoints

**POST /api/v1/templates**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "name": "Basic Config", "type": "declarative", "content": "template content" }`
- Response: `{ "template_id": "uuid", "name": "Basic Config", "created_at": "timestamp" }`
- Status: 201 Created, 400 Bad Request, 401 Unauthorized

**GET /api/v1/templates**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&type=declarative`
- Response: `{ "items": [...], "total_count": 20, "page": 1, "page_size": 50, "total_pages": 1 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/templates/{template_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "template_id": "uuid", "name": "Basic Config", "content": "...", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**PATCH /api/v1/templates/{template_id}**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "name": "Updated Config", "content": "new content" }`
- Response: `{ "template_id": "uuid", "name": "Updated Config", ... }`
- Status: 200 OK, 400 Bad Request, 404 Not Found, 401 Unauthorized

**DELETE /api/v1/templates/{template_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "message": "Template deleted successfully" }`
- Status: 204 No Content, 404 Not Found, 401 Unauthorized

**POST /api/v1/templates/{template_id}/apply**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "device_ids": ["uuid1", "uuid2"], "variables": { "key": "value" } }`
- Response: `{ "job_id": "uuid", "status": "pending" }`
- Status: 202 Accepted, 404 Not Found, 401 Unauthorized

#### Job Management Endpoints

**GET /api/v1/jobs**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&status=running&device_id=uuid`
- Response: `{ "items": [...], "total_count": 50, "page": 1, "page_size": 50, "total_pages": 1 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/jobs/{job_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "job_id": "uuid", "type": "backup", "status": "completed", "result": "...", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**POST /api/v1/jobs/{job_id}/cancel**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "job_id": "uuid", "status": "cancelled" }`
- Status: 200 OK, 404 Not Found, 409 Conflict, 401 Unauthorized

**GET /api/v1/jobs/{job_id}/logs**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "job_id": "uuid", "logs": ["log line 1", "log line 2", ...] }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

#### Backup Management Endpoints

**POST /api/v1/backups**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "device_ids": ["uuid1", "uuid2"], "type": "export" }`
- Response: `{ "job_id": "uuid", "status": "pending" }`
- Status: 202 Accepted, 400 Bad Request, 401 Unauthorized

**GET /api/v1/backups**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&device_id=uuid&start_date=2024-01-01&end_date=2024-12-31`
- Response: `{ "items": [...], "total_count": 100, "page": 1, "page_size": 50, "total_pages": 2 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/backups/{backup_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "backup_id": "uuid", "device_id": "uuid", "type": "export", "size": 12345, "created_at": "timestamp", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**GET /api/v1/backups/{backup_id}/download**
- Headers: `Authorization: Bearer <token>`
- Response: Binary backup file content
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**POST /api/v1/backups/{backup_id}/restore**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "job_id": "uuid", "status": "pending" }`
- Status: 202 Accepted, 404 Not Found, 401 Unauthorized

**DELETE /api/v1/backups/{backup_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "message": "Backup deleted successfully" }`
- Status: 204 No Content, 404 Not Found, 401 Unauthorized

#### Alert Management Endpoints

**GET /api/v1/alerts**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&severity=critical&status=active&device_id=uuid`
- Response: `{ "items": [...], "total_count": 25, "page": 1, "page_size": 50, "total_pages": 1 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/alerts/{alert_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "alert_id": "uuid", "device_id": "uuid", "severity": "critical", "message": "...", "status": "active", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**PATCH /api/v1/alerts/{alert_id}**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "status": "acknowledged" }`
- Response: `{ "alert_id": "uuid", "status": "acknowledged", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**GET /api/v1/alerts/stats**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "active": 10, "acknowledged": 5, "resolved": 100, "by_severity": { "critical": 3, "warning": 7, "info": 0 } }`
- Status: 200 OK, 401 Unauthorized

#### User Management Endpoints

**POST /api/v1/users**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "email": "user@example.com", "password": "secret", "role_id": "uuid" }`
- Response: `{ "user_id": "uuid", "email": "user@example.com", "created_at": "timestamp" }`
- Status: 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden

**GET /api/v1/users**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50`
- Response: `{ "items": [...], "total_count": 15, "page": 1, "page_size": 50, "total_pages": 1 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/users/{user_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "user_id": "uuid", "email": "user@example.com", "role": {...}, ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

**PATCH /api/v1/users/{user_id}**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "email": "newemail@example.com" }`
- Response: `{ "user_id": "uuid", "email": "newemail@example.com", ... }`
- Status: 200 OK, 400 Bad Request, 404 Not Found, 401 Unauthorized

**DELETE /api/v1/users/{user_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "message": "User deactivated successfully" }`
- Status: 204 No Content, 404 Not Found, 401 Unauthorized

**POST /api/v1/users/{user_id}/roles**
- Headers: `Authorization: Bearer <token>`
- Request: `{ "role_id": "uuid" }`
- Response: `{ "user_id": "uuid", "role": {...} }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized, 403 Forbidden

#### Audit Log Endpoints

**GET /api/v1/audit-logs**
- Headers: `Authorization: Bearer <token>`
- Query: `?page=1&page_size=50&user_id=uuid&action=device_update&start_date=2024-01-01`
- Response: `{ "items": [...], "total_count": 500, "page": 1, "page_size": 50, "total_pages": 10 }`
- Status: 200 OK, 401 Unauthorized

**GET /api/v1/audit-logs/{log_id}**
- Headers: `Authorization: Bearer <token>`
- Response: `{ "event_id": "uuid", "user_id": "uuid", "action": "device_update", "result": "success", "timestamp": "...", ... }`
- Status: 200 OK, 404 Not Found, 401 Unauthorized

#### Health Check Endpoints

**GET /health**
- Response: `{ "status": "healthy", "version": "1.0.0" }`
- Status: 200 OK

**GET /health/ready**
- Response: `{ "status": "ready", "dependencies": { "database": "healthy", "redis": "healthy" } }`
- Status: 200 OK, 503 Service Unavailable

**GET /health/live**
- Response: `{ "status": "alive" }`
- Status: 200 OK

#### Metrics Endpoint

**GET /metrics**
- Response: Prometheus metrics in text format
- Status: 200 OK

### Authentication and Authorization Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant DB
    participant Redis
    
    Client->>API: POST /auth/login (email, password)
    API->>DB: Query user by email
    DB-->>API: User record
    API->>Auth: Verify password hash
    Auth-->>API: Password valid
    API->>Auth: Generate JWT tokens
    Auth-->>API: access_token, refresh_token
    API->>Redis: Store refresh_token
    API-->>Client: tokens
    
    Client->>API: GET /devices (Authorization: Bearer token)
    API->>Auth: Validate JWT token
    Auth-->>API: User context (user_id, tenant_id, role)
    API->>Auth: Check permissions
    Auth-->>API: Permission granted
    API->>DB: Query devices (filtered by tenant_id)
    DB-->>API: Device list
    API-->>Client: Device list
```

### Multi-Tenant Isolation Implementation

**Row-Level Security Strategy**

All tenant-scoped tables include a `tenant_id` foreign key. The system enforces isolation through:

1. **Middleware Injection**: Extract `tenant_id` from authenticated user context
2. **Query Filtering**: Automatically inject `tenant_id` filter in all database queries
3. **Validation**: Verify `tenant_id` matches authenticated user before mutations
4. **Audit Logging**: Log all cross-tenant access attempts

**Implementation Pattern**

```python
# Middleware extracts tenant context
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    if request.user:
        request.state.tenant_id = request.user.tenant_id
    response = await call_next(request)
    return response

# Dependency provides tenant-filtered queries
def get_tenant_context(request: Request) -> str:
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401)
    return request.state.tenant_id

# Service layer applies filtering
class DeviceService:
    def list_devices(self, tenant_id: str, filters: dict):
        query = db.query(Device).filter(Device.tenant_id == tenant_id)
        # Apply additional filters
        return query.all()
```

**Super Admin Bypass**

Super Admin role can access cross-tenant data when explicitly requested:

```python
def get_devices_cross_tenant(
    user: User = Depends(get_current_user),
    cross_tenant: bool = False
):
    if cross_tenant and user.role != "SuperAdmin":
        raise HTTPException(status_code=403)
    
    if cross_tenant:
        audit_log("cross_tenant_access", user_id=user.id)
        return db.query(Device).all()
    else:
        return db.query(Device).filter(Device.tenant_id == user.tenant_id).all()
```


## Data Models

### Database Schema

The database schema implements multi-tenant isolation with UUID primary keys and timestamp tracking on all entities.

#### Core Tables

**tenants**
```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(status);
```

**sites**
```sql
CREATE TABLE sites (
    site_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sites_tenant ON sites(tenant_id);
```

**devices**
```sql
CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    site_id UUID REFERENCES sites(site_id) ON DELETE SET NULL,
    hostname TEXT NOT NULL,
    ip_address INET NOT NULL,
    ros_version TEXT,
    ros_major INTEGER,
    architecture TEXT,
    model TEXT,
    serial_number TEXT,
    status TEXT NOT NULL CHECK (status IN ('unregistered', 'discovered', 'pending_adoption', 'adopted', 'managed', 'offline', 'error', 'retired')),
    last_seen TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_tenant ON devices(tenant_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_site ON devices(site_id);
CREATE INDEX idx_devices_ip ON devices(ip_address);
```

**device_credentials**
```sql
CREATE TABLE device_credentials (
    credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    private_key TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_device_credentials_device ON device_credentials(device_id);
```


**templates**
```sql
CREATE TABLE templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('declarative', 'script')),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_tenant ON templates(tenant_id);
CREATE INDEX idx_templates_type ON templates(type);
```

**jobs**
```sql
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(device_id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('inventory', 'backup', 'template_apply', 'command', 'connectivity_check')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    celery_task_id TEXT,
    result TEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX idx_jobs_device ON jobs(device_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_type ON jobs(type);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);
```

**backups**
```sql
CREATE TABLE backups (
    backup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('export', 'binary')),
    storage_path TEXT NOT NULL,
    size INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    compressed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_backups_device ON backups(device_id);
CREATE INDEX idx_backups_created ON backups(created_at DESC);
```

**alerts**
```sql
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(device_id) ON DELETE SET NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'acknowledged', 'resolved')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_alerts_tenant ON alerts(tenant_id);
CREATE INDEX idx_alerts_device ON alerts(device_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
```

**users**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id UUID NOT NULL REFERENCES roles(role_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
```

**roles**
```sql
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO roles (name, description) VALUES
    ('SuperAdmin', 'Full system access across all tenants'),
    ('TenantAdmin', 'Full access within tenant'),
    ('SiteManager', 'Manage devices within assigned sites'),
    ('Operator', 'Execute operations on devices'),
    ('Viewer', 'Read-only access');
```

**permissions**
```sql
CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_permissions_role ON permissions(role_id);
CREATE UNIQUE INDEX idx_permissions_role_resource_action ON permissions(role_id, resource, action);
```

**audit_logs**
```sql
CREATE TABLE audit_logs (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    device_id UUID REFERENCES devices(device_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    result TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    request_id TEXT,
    before_value JSONB,
    after_value JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_device ON audit_logs(device_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_request ON audit_logs(request_id);
```

### SQLAlchemy Models

**Base Model**
```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Tenant Model**
```python
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
import enum

class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"

class Tenant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenants"
    
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE)
    
    # Relationships
    sites = relationship("Site", back_populates="tenant", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="tenant", cascade="all, delete-orphan")
```

**Device Model**
```python
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
import enum

class DeviceStatus(str, enum.Enum):
    UNREGISTERED = "unregistered"
    DISCOVERED = "discovered"
    PENDING_ADOPTION = "pending_adoption"
    ADOPTED = "adopted"
    MANAGED = "managed"
    OFFLINE = "offline"
    ERROR = "error"
    RETIRED = "retired"

class Device(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "devices"
    
    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"))
    hostname = Column(String, nullable=False)
    ip_address = Column(INET, nullable=False)
    ros_version = Column(String)
    ros_major = Column(Integer)
    architecture = Column(String)
    model = Column(String)
    serial_number = Column(String)
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.UNREGISTERED)
    last_seen = Column(DateTime)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="devices")
    site = relationship("Site", back_populates="devices")
    credentials = relationship("DeviceCredential", back_populates="device", uselist=False, cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="device")
    backups = relationship("Backup", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device")
```

### Pydantic Schemas

**Device Schemas**
```python
from pydantic import BaseModel, Field, IPvAnyAddress
from datetime import datetime
from uuid import UUID
from typing import Optional

class DeviceCreate(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: IPvAnyAddress
    site_id: Optional[UUID] = None
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class DeviceUpdate(BaseModel):
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    site_id: Optional[UUID] = None

class DeviceResponse(BaseModel):
    device_id: UUID
    tenant_id: UUID
    site_id: Optional[UUID]
    hostname: str
    ip_address: str
    ros_version: Optional[str]
    ros_major: Optional[int]
    architecture: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    status: str
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

**Pagination Schema**
```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
```


### Job Queue Architecture

**Celery Configuration**
```python
from celery import Celery
from kombu import Queue, Exchange

celery_app = Celery(
    "mikrotik_controller",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues=(
        Queue("high", Exchange("high"), routing_key="high"),
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("low", Exchange("low"), routing_key="low"),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

# Task retry configuration
celery_app.conf.task_autoretry_for = (Exception,)
celery_app.conf.task_retry_kwargs = {"max_retries": 3}
celery_app.conf.task_retry_backoff = True
celery_app.conf.task_retry_backoff_max = 600  # 10 minutes
celery_app.conf.task_retry_jitter = True
```

**Worker Task Example**
```python
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.connectors.mikrotik import MikroTikConnector
from app.services.audit_service import AuditService

class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()

@celery_app.task(bind=True, base=DatabaseTask, queue="default")
def execute_device_backup(self, job_id: str, device_id: str):
    """Execute backup operation on a device"""
    db = self.db
    
    # Update job status to running
    job = db.query(Job).filter(Job.job_id == job_id).first()
    job.status = JobStatus.RUNNING
    job.started_at = datetime.utcnow()
    db.commit()
    
    try:
        # Get device and credentials
        device = db.query(Device).filter(Device.device_id == device_id).first()
        credentials = device.credentials
        
        # Connect to device
        connector = MikroTikConnector(
            host=str(device.ip_address),
            username=credentials.username,
            password=decrypt_password(credentials.password_encrypted)
        )
        
        # Execute backup
        backup_content = connector.export_configuration()
        
        # Store backup
        backup_path = f"backups/{device.tenant_id}/{device_id}/{datetime.utcnow().isoformat()}.rsc"
        storage.save(backup_path, backup_content)
        
        # Calculate checksum
        checksum = hashlib.sha256(backup_content.encode()).hexdigest()
        
        # Create backup record
        backup = Backup(
            device_id=device_id,
            type="export",
            storage_path=backup_path,
            size=len(backup_content),
            checksum=checksum
        )
        db.add(backup)
        
        # Update job status
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.utcnow()
        job.result = f"Backup created: {backup.backup_id}"
        db.commit()
        
        # Audit log
        AuditService.log(
            tenant_id=device.tenant_id,
            action="device_backup",
            resource_type="device",
            resource_id=device_id,
            result="success"
        )
        
        return {"backup_id": str(backup.backup_id)}
        
    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.FAILED
        job.finished_at = datetime.utcnow()
        job.error_message = str(e)
        db.commit()
        
        # Create alert
        alert = Alert(
            tenant_id=device.tenant_id,
            device_id=device_id,
            severity="critical",
            message=f"Backup failed: {str(e)}",
            status="active"
        )
        db.add(alert)
        db.commit()
        
        # Audit log
        AuditService.log(
            tenant_id=device.tenant_id,
            action="device_backup",
            resource_type="device",
            resource_id=device_id,
            result="failed"
        )
        
        raise
```

### MikroTik Connector Implementation

**Connector Interface**
```python
from typing import Optional, Dict, List
import routeros_api
from app.utils.crypto import decrypt_credential

class MikroTikConnector:
    """Interface for communicating with MikroTik devices via RouterOS API"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 8728, timeout: int = 30):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.connection = None
    
    def connect(self) -> bool:
        """Establish connection to device"""
        try:
            self.connection = routeros_api.RouterOsApiPool(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                plaintext_login=True
            )
            api = self.connection.get_api()
            # Test connection
            api.get_resource('/system/identity').get()
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}: {str(e)}")
    
    def disconnect(self):
        """Close connection to device"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
    
    def execute_command(self, command: str) -> List[Dict]:
        """Execute RouterOS command and return results"""
        if not self.connection:
            self.connect()
        
        try:
            api = self.connection.get_api()
            resource = api.get_resource(command)
            return resource.get()
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {str(e)}")
    
    def export_configuration(self) -> str:
        """Export device configuration"""
        if not self.connection:
            self.connect()
        
        try:
            api = self.connection.get_api()
            # Execute export command
            result = api.get_resource('/export').call('export')
            return result
        except Exception as e:
            raise RuntimeError(f"Configuration export failed: {str(e)}")
    
    def apply_configuration(self, commands: List[str]) -> Dict:
        """Apply configuration commands to device"""
        if not self.connection:
            self.connect()
        
        results = []
        errors = []
        
        for command in commands:
            try:
                result = self.execute_command(command)
                results.append({"command": command, "status": "success", "result": result})
            except Exception as e:
                errors.append({"command": command, "status": "failed", "error": str(e)})
        
        return {
            "total": len(commands),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    def get_system_resource(self) -> Dict:
        """Get system resource information"""
        return self.execute_command('/system/resource')[0]
    
    def get_interfaces(self) -> List[Dict]:
        """Get interface list"""
        return self.execute_command('/interface')
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
```

### Template Engine Design

**Template Engine Implementation**
```python
from jinja2 import Environment, BaseLoader, TemplateError, meta
from typing import Dict, List, Optional

class TemplateEngine:
    """Jinja2-based template engine for RouterOS configurations"""
    
    def __init__(self):
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters['ip_network'] = self._filter_ip_network
        self.env.filters['subnet_mask'] = self._filter_subnet_mask
    
    def validate_syntax(self, template_content: str) -> tuple[bool, Optional[str]]:
        """Validate Jinja2 template syntax"""
        try:
            self.env.parse(template_content)
            return True, None
        except TemplateError as e:
            return False, str(e)
    
    def get_variables(self, template_content: str) -> List[str]:
        """Extract all variables from template"""
        try:
            ast = self.env.parse(template_content)
            return list(meta.find_undeclared_variables(ast))
        except TemplateError as e:
            raise ValueError(f"Template parsing failed: {str(e)}")
    
    def render(self, template_content: str, variables: Dict) -> str:
        """Render template with provided variables"""
        try:
            template = self.env.from_string(template_content)
            return template.render(**variables)
        except TemplateError as e:
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    def validate_rendered_output(self, output: str) -> tuple[bool, Optional[str]]:
        """Validate rendered output is valid RouterOS configuration"""
        # Basic validation - check for common syntax errors
        lines = output.split('\n')
        errors = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for basic RouterOS command structure
            if not line.startswith('/'):
                errors.append(f"Line {i}: Commands must start with '/'")
        
        if errors:
            return False, '; '.join(errors)
        return True, None
    
    def dry_run(self, template_content: str, variables: Dict) -> Dict:
        """Render template and validate without applying"""
        # Validate syntax
        valid, error = self.validate_syntax(template_content)
        if not valid:
            return {"valid": False, "error": error, "stage": "syntax"}
        
        # Check variables
        required_vars = self.get_variables(template_content)
        missing_vars = [v for v in required_vars if v not in variables]
        if missing_vars:
            return {
                "valid": False,
                "error": f"Missing variables: {', '.join(missing_vars)}",
                "stage": "variables"
            }
        
        # Render
        try:
            output = self.render(template_content, variables)
        except Exception as e:
            return {"valid": False, "error": str(e), "stage": "rendering"}
        
        # Validate output
        valid, error = self.validate_rendered_output(output)
        if not valid:
            return {"valid": False, "error": error, "stage": "validation"}
        
        return {"valid": True, "output": output}
    
    @staticmethod
    def _filter_ip_network(cidr: str) -> str:
        """Extract network address from CIDR"""
        from ipaddress import ip_network
        return str(ip_network(cidr, strict=False).network_address)
    
    @staticmethod
    def _filter_subnet_mask(cidr: str) -> str:
        """Extract subnet mask from CIDR"""
        from ipaddress import ip_network
        return str(ip_network(cidr, strict=False).netmask)
```

**Template Example**
```jinja2
# Basic Router Configuration
# Generated: {{ timestamp }}

/system identity
set name={{ hostname }}

/ip address
{% for interface in interfaces %}
add address={{ interface.ip_address }} interface={{ interface.name }}
{% endfor %}

/ip route
add dst-address=0.0.0.0/0 gateway={{ default_gateway }}

/ip dns
set servers={{ dns_servers|join(',') }}

{% if enable_ntp %}
/system ntp client
set enabled=yes primary-ntp={{ ntp_server }}
{% endif %}

/user
add name={{ admin_user }} password={{ admin_password }} group=full
```


### Backup System Architecture

**Backup Storage Implementation**
```python
import gzip
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

class BackupStorage:
    """Manages device configuration backups with compression and integrity verification"""
    
    def __init__(self, base_path: str = "/var/lib/backups"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def store_backup(
        self,
        tenant_id: str,
        device_id: str,
        content: str,
        backup_type: str = "export"
    ) -> Dict:
        """Store backup with compression and checksum"""
        # Create directory structure
        backup_dir = self.base_path / tenant_id / device_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().isoformat()
        filename = f"{timestamp}_{backup_type}.rsc.gz"
        filepath = backup_dir / filename
        
        # Compress content
        compressed_content = gzip.compress(content.encode('utf-8'))
        
        # Calculate checksum
        checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Write to disk
        filepath.write_bytes(compressed_content)
        
        return {
            "storage_path": str(filepath.relative_to(self.base_path)),
            "size": len(compressed_content),
            "checksum": checksum,
            "compressed": True
        }
    
    def retrieve_backup(self, storage_path: str) -> str:
        """Retrieve and decompress backup"""
        filepath = self.base_path / storage_path
        
        if not filepath.exists():
            raise FileNotFoundError(f"Backup not found: {storage_path}")
        
        # Read and decompress
        compressed_content = filepath.read_bytes()
        content = gzip.decompress(compressed_content).decode('utf-8')
        
        return content
    
    def verify_backup(self, storage_path: str, expected_checksum: str) -> bool:
        """Verify backup integrity using checksum"""
        content = self.retrieve_backup(storage_path)
        actual_checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return actual_checksum == expected_checksum
    
    def delete_backup(self, storage_path: str):
        """Delete backup file"""
        filepath = self.base_path / storage_path
        if filepath.exists():
            filepath.unlink()
    
    def apply_retention_policy(
        self,
        tenant_id: str,
        device_id: str,
        retention_days: int = 30
    ) -> List[str]:
        """Delete backups older than retention period"""
        backup_dir = self.base_path / tenant_id / device_id
        
        if not backup_dir.exists():
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted = []
        
        for backup_file in backup_dir.glob("*.rsc.gz"):
            # Extract timestamp from filename
            timestamp_str = backup_file.stem.split('_')[0]
            try:
                backup_date = datetime.fromisoformat(timestamp_str)
                if backup_date < cutoff_date:
                    backup_file.unlink()
                    deleted.append(str(backup_file.relative_to(self.base_path)))
            except ValueError:
                continue
        
        return deleted
```

### Alerting and Audit Logging Design

**Alert Engine Implementation**
```python
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.core.database import SessionLocal

class AlertEngine:
    """Manages alert creation, deduplication, and lifecycle"""
    
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal()
        self.dedup_window_minutes = 15
    
    def create_alert(
        self,
        tenant_id: str,
        device_id: Optional[str],
        severity: AlertSeverity,
        message: str,
        metadata: Optional[Dict] = None
    ) -> Optional[Alert]:
        """Create alert with deduplication"""
        # Check for duplicate alerts within time window
        if self._is_duplicate(tenant_id, device_id, message):
            return None
        
        alert = Alert(
            tenant_id=tenant_id,
            device_id=device_id,
            severity=severity,
            message=message,
            status=AlertStatus.ACTIVE,
            metadata=metadata
        )
        
        self.db.add(alert)
        self.db.commit()
        
        # Enqueue notification for critical alerts
        if severity == AlertSeverity.CRITICAL:
            from app.workers.tasks.alert_tasks import send_alert_notification
            send_alert_notification.apply_async(
                args=[str(alert.alert_id)],
                queue="high"
            )
        
        return alert
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> Alert:
        """Mark alert as acknowledged"""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        
        self.db.commit()
        return alert
    
    def resolve_alert(self, alert_id: str) -> Alert:
        """Mark alert as resolved"""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
        return alert
    
    def auto_resolve_alerts(self, tenant_id: str, device_id: str, alert_type: str):
        """Automatically resolve alerts when condition is cleared"""
        alerts = self.db.query(Alert).filter(
            Alert.tenant_id == tenant_id,
            Alert.device_id == device_id,
            Alert.status == AlertStatus.ACTIVE,
            Alert.message.like(f"%{alert_type}%")
        ).all()
        
        for alert in alerts:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
    
    def _is_duplicate(
        self,
        tenant_id: str,
        device_id: Optional[str],
        message: str
    ) -> bool:
        """Check if similar alert exists within deduplication window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.dedup_window_minutes)
        
        query = self.db.query(Alert).filter(
            Alert.tenant_id == tenant_id,
            Alert.message == message,
            Alert.status == AlertStatus.ACTIVE,
            Alert.created_at >= cutoff_time
        )
        
        if device_id:
            query = query.filter(Alert.device_id == device_id)
        
        return query.first() is not None
```

**Audit Service Implementation**
```python
from typing import Optional, Dict, Any
from app.models.audit import AuditLog
from app.core.database import SessionLocal
from datetime import datetime
import json

class AuditService:
    """Comprehensive audit logging for compliance and troubleshooting"""
    
    @staticmethod
    def log(
        tenant_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        result: str = "success",
        before_value: Optional[Dict] = None,
        after_value: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Create audit log entry"""
        db = SessionLocal()
        
        try:
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                device_id=device_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                before_value=before_value,
                after_value=after_value,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def log_api_request(
        request,
        user_id: Optional[str],
        tenant_id: Optional[str],
        response_status: int
    ):
        """Log API request"""
        AuditService.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"{request.method} {request.url.path}",
            resource_type="api_request",
            result="success" if response_status < 400 else "failed",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    
    @staticmethod
    def log_authentication(
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        AuditService.log(
            tenant_id=None,
            action="authentication",
            resource_type="user",
            result="success" if success else "failed",
            ip_address=ip_address,
            user_agent=user_agent,
            after_value={"email": email, "reason": reason} if reason else {"email": email}
        )
    
    @staticmethod
    def log_device_operation(
        tenant_id: str,
        device_id: str,
        user_id: str,
        operation: str,
        result: str,
        details: Optional[Dict] = None
    ):
        """Log device operation"""
        AuditService.log(
            tenant_id=tenant_id,
            user_id=user_id,
            device_id=device_id,
            action=f"device_{operation}",
            resource_type="device",
            resource_id=device_id,
            result=result,
            after_value=details
        )
```

### Docker and Deployment Configuration

**API Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Worker Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run Celery worker
CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
```

**Docker Compose Configuration**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mikrotik_controller
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/mikrotik_controller
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-here
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
      - backup_storage:/var/lib/backups

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/mikrotik_controller
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-here
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
      - backup_storage:/var/lib/backups
    deploy:
      replicas: 2

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/mikrotik_controller
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-here
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
  backup_storage:
```

### Security Considerations

**Credential Encryption**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class SecretVault:
    """Secure credential storage with AES-256 encryption"""
    
    def __init__(self, master_secret: str):
        self.master_secret = master_secret
        self._cipher = None
    
    @property
    def cipher(self):
        """Lazy initialization of cipher"""
        if self._cipher is None:
            # Derive encryption key from master secret
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'mikrotik_controller_salt',  # Should be unique per deployment
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_secret.encode()))
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt credential"""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt credential"""
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
```

**JWT Authentication**
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**RBAC Implementation**
```python
from functools import wraps
from fastapi import HTTPException, Depends
from app.models.user import User
from app.models.role import Role, Permission

def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            # Check if user has required permission
            has_permission = db.query(Permission).join(Role).filter(
                Role.role_id == current_user.role_id,
                Permission.resource == resource,
                Permission.action == action
            ).first()
            
            if not has_permission and current_user.role.name != "SuperAdmin":
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage example
@router.delete("/devices/{device_id}")
@require_permission("device", "delete")
async def delete_device(device_id: str, current_user: User = Depends(get_current_user)):
    # Implementation
    pass
```

### Scalability Patterns

**Horizontal Scaling Architecture**

1. **Stateless API Instances**: All session state stored in Redis, enabling any API instance to handle any request
2. **Database Connection Pooling**: SQLAlchemy connection pool with configurable size per instance
3. **Read Replicas**: Route read-heavy queries to PostgreSQL read replicas
4. **Distributed Caching**: Redis cache shared across all API instances
5. **Job Distribution**: Celery automatically distributes jobs across worker instances
6. **WebSocket Scaling**: Redis pub/sub for cross-instance WebSocket message distribution

**Load Balancing Configuration (Nginx)**
```nginx
upstream api_backend {
    least_conn;
    server api-1:8000 max_fails=3 fail_timeout=30s;
    server api-2:8000 max_fails=3 fail_timeout=30s;
    server api-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /health {
        proxy_pass http://api_backend/health;
        access_log off;
    }
}
```

**Database Scaling Strategy**
```python
# Read/Write splitting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Write database (primary)
write_engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Read database (replica)
read_engine = create_engine(
    READ_REPLICA_URL,
    pool_size=30,
    max_overflow=60,
    pool_pre_ping=True
)

WriteSession = sessionmaker(bind=write_engine)
ReadSession = sessionmaker(bind=read_engine)

def get_write_db():
    """Get write database session"""
    db = WriteSession()
    try:
        yield db
    finally:
        db.close()

def get_read_db():
    """Get read database session"""
    db = ReadSession()
    try:
        yield db
    finally:
        db.close()
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration Loading from Environment

*For any* configuration key defined in the system, loading configuration from environment variables should either return the environment variable value if set, or the default value if defined, or raise an error if required and missing.

**Validates: Requirements 1.2, 7.1, 7.2**

### Property 2: Multi-Tenant Query Isolation

*For any* database query on tenant-scoped tables, when executed with a tenant context, the query should only return records matching that tenant_id and should never return records from other tenants.

**Validates: Requirements 9.2, 9.3, 9.5, 44.1, 44.2, 44.3, 44.6**

### Property 3: SuperAdmin Cross-Tenant Access

*For any* SuperAdmin user, when explicitly requesting cross-tenant access, the system should allow access to data from all tenants and log the access attempt to the audit system.

**Validates: Requirements 9.4, 9.6, 44.5**

### Property 4: Foreign Key Constraint Enforcement

*For any* database operation that violates a foreign key constraint, the database should reject the operation and raise an appropriate error.

**Validates: Requirements 3.6**

### Property 5: Migration Round-Trip

*For any* database migration, applying the upgrade followed by the downgrade should return the database to its original state.

**Validates: Requirements 4.3**

### Property 6: Migration Version Recording

*For any* migration that is successfully applied, the migration system should record the migration version in the database.

**Validates: Requirements 4.5**

### Property 7: Task Retry with Exponential Backoff

*For any* Celery task that fails, the worker engine should retry the task with exponentially increasing delays between attempts, up to the configured maximum retries.

**Validates: Requirements 5.4**

### Property 8: Task Time Limit Enforcement

*For any* Celery task that exceeds the configured time limit, the worker engine should terminate the task and mark it as failed.

**Validates: Requirements 5.6**

### Property 9: Failed Task Audit Logging

*For any* Celery task that fails after all retries, the worker engine should create an audit log entry recording the failure.

**Validates: Requirements 5.7**

### Property 10: Invalid JWT Token Rejection

*For any* protected API endpoint, when provided with an invalid or expired JWT token, the system should return a 401 Unauthorized response.

**Validates: Requirements 8.3, 8.7**

### Property 11: Insufficient Permission Rejection

*For any* API endpoint requiring specific permissions, when accessed by a user lacking those permissions, the system should return a 403 Forbidden response.

**Validates: Requirements 8.8**

### Property 12: Authenticated User Context

*For any* authenticated API request, the system should extract and include user information (user_id, tenant_id, role) in the request context.

**Validates: Requirements 8.6, 9.1**

### Property 13: Template Variable Substitution

*For any* valid template with defined variables, rendering the template with those variables should produce output containing the substituted values.

**Validates: Requirements 18.2**

### Property 14: Template Syntax Validation

*For any* template with invalid Jinja2 syntax, the template engine should reject the template and return a descriptive error message.

**Validates: Requirements 18.4, 42.1**

### Property 15: Template Rendering Error Reporting

*For any* template that fails to render, the template engine should return an error message including the line number where the error occurred.

**Validates: Requirements 18.6**

### Property 16: Template Round-Trip Validation

*For any* valid template, rendering with valid input data should produce syntactically correct RouterOS configuration that can be parsed and validated.

**Validates: Requirements 18.7, 42.6**

### Property 17: Backup Compression

*For any* backup created by the backup storage system, the stored backup should be compressed and the compressed size should be less than or equal to the original size.

**Validates: Requirements 19.2**

### Property 18: Backup Retention Policy Enforcement

*For any* device with backups older than the configured retention period, the backup storage system should automatically delete those old backups.

**Validates: Requirements 19.4, 19.8**

### Property 19: Backup Checksum Calculation

*For any* backup created, the backup storage system should calculate and store a SHA-256 checksum of the backup content.

**Validates: Requirements 19.6, 43.1**

### Property 20: Backup Checksum Verification

*For any* backup retrieved, the backup storage system should verify the checksum matches the stored checksum, and if verification fails, mark the backup as corrupted and create an alert.

**Validates: Requirements 43.3, 43.5**

### Property 21: Backup Round-Trip Integrity

*For any* backup, storing the backup content and then retrieving it should produce identical content to the original.

**Validates: Requirements 43.6**

### Property 22: Backup Content Validation

*For any* backup created, the backup storage system should validate that the content is parseable as valid RouterOS configuration.

**Validates: Requirements 19.7, 43.4**

### Property 23: Alert Deduplication

*For any* alert condition, if an active alert with the same message already exists within the configured time window, the alerting engine should not create a duplicate alert.

**Validates: Requirements 20.5**

### Property 24: Critical Alert Notification

*For any* alert created with critical severity, the alerting engine should enqueue a notification job to the high-priority queue.

**Validates: Requirements 20.7**

### Property 25: Alert Auto-Resolution

*For any* alert condition that is resolved, the alerting engine should automatically update the alert status to resolved.

**Validates: Requirements 20.8**

### Property 26: API Request Audit Logging

*For any* API request, the audit system should create a log entry containing user_id, endpoint, method, timestamp, IP address, and user agent.

**Validates: Requirements 21.1, 21.9**

### Property 27: Database Mutation Audit Logging

*For any* database mutation operation, the audit system should create a log entry containing the before and after values of the modified data.

**Validates: Requirements 21.2**

### Property 28: Device Operation Audit Logging

*For any* device operation (command execution, backup, template application), the audit system should create a log entry containing the operation details and result.

**Validates: Requirements 21.3**

### Property 29: Authentication Attempt Audit Logging

*For any* authentication attempt (successful or failed), the audit system should create a log entry containing the email, result, IP address, and user agent.

**Validates: Requirements 21.4**

### Property 30: Permission Failure Audit Logging

*For any* permission check that fails, the audit system should create a log entry containing the user, resource, action, and result.

**Validates: Requirements 21.5**

### Property 31: Audit Log Request Correlation

*For any* audit log entry, the system should include a request_id that can be used to correlate related log entries from the same request.

**Validates: Requirements 21.6**

### Property 32: Audit Log Tenant Isolation

*For any* audit log entry for a tenant-scoped operation, the system should include the tenant_id in the log entry.

**Validates: Requirements 21.8**

### Property 33: Job Status Lifecycle

*For any* job, the job status should transition through valid states (pending → running → completed/failed/cancelled) and never transition to invalid states.

**Validates: Requirements 22.3, 22.4, 31.9, 31.10, 31.11**

### Property 34: Job Result Storage

*For any* job that completes (successfully or with failure), the system should store the job result or error message in the database.

**Validates: Requirements 22.4, 31.7**

### Property 35: Request Validation Error Response

*For any* API request with invalid data that fails Pydantic validation, the system should return a 422 Unprocessable Entity response with detailed error messages indicating which fields are invalid.

**Validates: Requirements 24.4, 24.8**

### Property 36: Exception to HTTP Status Mapping

*For any* exception raised during request processing, the system should map the exception to an appropriate HTTP status code and return a consistent error response format.

**Validates: Requirements 25.2, 25.3**

### Property 37: Sensitive Data Masking in Logs

*For any* log entry, the system should mask sensitive data (passwords, tokens, API keys) and never log them in plain text.

**Validates: Requirements 25.7, 30.6**

### Property 38: Database Constraint Violation Handling

*For any* database operation that violates a constraint (unique, foreign key, check), the system should return a 409 Conflict response with a descriptive message.

**Validates: Requirements 25.9**

### Property 39: Health Check Dependency Verification

*For any* health check request to /health/ready, the system should verify connectivity to all dependencies (database, Redis) and return 503 Service Unavailable if any dependency is unavailable.

**Validates: Requirements 26.2, 26.5, 26.6**

### Property 40: Rate Limit Enforcement

*For any* user or tenant, when the number of requests exceeds the configured rate limit within the time window, the system should return 429 Too Many Requests with rate limit headers.

**Validates: Requirements 28.2, 28.3, 28.4**

### Property 41: Pagination Metadata

*For any* paginated list endpoint, the response should include pagination metadata (total_count, page, page_size, total_pages) that accurately reflects the result set.

**Validates: Requirements 29.3**

### Property 42: Pagination Bounds Enforcement

*For any* paginated request, the system should enforce the maximum page_size limit and default to the configured default page_size if not specified.

**Validates: Requirements 29.2**

### Property 43: Credential Encryption

*For any* device credential stored in the database, the password should be encrypted using the secret vault before storage.

**Validates: Requirements 30.1**

### Property 44: MikroTik Connection Timeout

*For any* MikroTik device connection attempt, if the connection does not succeed within the configured timeout, the connector should raise a timeout error.

**Validates: Requirements 17.5**

### Property 45: MikroTik Connection Error Reporting

*For any* MikroTik device connection that fails, the connector should return a descriptive error message indicating the failure reason.

**Validates: Requirements 17.7**

### Property 46: MikroTik Command Failure Logging

*For any* MikroTik command execution that fails, the connector should log the error to the audit system.

**Validates: Requirements 17.8**

### Property 47: WebSocket Tenant Isolation

*For any* WebSocket message broadcast, the system should only send messages to clients belonging to the relevant tenant.

**Validates: Requirements 39.5**

### Property 48: WebSocket Job Status Updates

*For any* job status change, the system should broadcast the update to all connected WebSocket clients belonging to the job's tenant.

**Validates: Requirements 39.8**

### Property 49: WebSocket Alert Notifications

*For any* new alert created, the system should broadcast the alert to all connected WebSocket clients belonging to the alert's tenant.

**Validates: Requirements 39.9**

### Property 50: Graceful Shutdown Request Completion

*For any* in-flight API request when a shutdown signal is received, the system should complete the request before terminating.

**Validates: Requirements 40.3**

### Property 51: Graceful Shutdown Worker Task Completion

*For any* worker task in progress when a shutdown signal is received, the worker should complete the current task before terminating.

**Validates: Requirements 40.6**

### Property 52: Cache Tenant Isolation

*For any* cached API response, the cache key should include the tenant_id to ensure cache isolation between tenants.

**Validates: Requirements 45.2**

### Property 53: Cache Invalidation on Mutation

*For any* data mutation operation, the system should invalidate relevant cache entries to ensure cache consistency.

**Validates: Requirements 45.4**


## Error Handling

### Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "request_id": "uuid"
  }
}
```

### Exception Hierarchy

```python
class APIException(Exception):
    """Base exception for all API errors"""
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An internal error occurred"

class ValidationError(APIException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"

class AuthenticationError(APIException):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"

class AuthorizationError(APIException):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    message = "Insufficient permissions"

class NotFoundError(APIException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"

class ConflictError(APIException):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"

class RateLimitError(APIException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded"

class ServiceUnavailableError(APIException):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
    message = "Service temporarily unavailable"
```

### Exception Handler

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    logger.error(
        f"API Exception: {exc.error_code}",
        extra={
            "request_id": request.state.request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        errors[field] = error["msg"]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(
        f"Database integrity error: {str(exc)}",
        extra={"request_id": request.state.request_id}
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "CONFLICT",
                "message": "Database constraint violation",
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": request.state.request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request.state.request_id
            }
        }
    )
```

### Logging Strategy

**Log Levels**
- DEBUG: Detailed diagnostic information for development
- INFO: General informational messages (request/response, job completion)
- WARNING: Warning messages for recoverable issues
- ERROR: Error messages for failures that don't crash the application
- CRITICAL: Critical errors that may cause system instability

**Structured Logging**
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

# Apply JSON formatter in production
if os.getenv("ENVIRONMENT") == "production":
    for handler in logging.root.handlers:
        handler.setFormatter(JSONFormatter())
```

### Retry Logic

**Celery Task Retry Configuration**
```python
@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def resilient_task(self, *args, **kwargs):
    """Task with automatic retry logic"""
    try:
        # Task implementation
        pass
    except Exception as exc:
        # Log retry attempt
        logger.warning(
            f"Task {self.request.id} failed, retrying",
            extra={
                "task_id": self.request.id,
                "retry_count": self.request.retries,
                "error": str(exc)
            }
        )
        raise
```

## Testing Strategy

### Testing Approach

The backend architecture requires a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage and correctness.

**Unit Tests**: Verify specific examples, edge cases, error conditions, and integration points between components. Unit tests are essential for testing concrete scenarios and ensuring components work correctly in isolation.

**Property-Based Tests**: Verify universal properties across all inputs using randomized test data generation. Property-based tests ensure that correctness properties hold for a wide range of inputs, catching edge cases that might be missed by example-based tests.

Together, these approaches provide comprehensive coverage: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Testing Framework

**Primary Framework**: pytest
**Property-Based Testing Library**: Hypothesis (Python)
**Test Database**: PostgreSQL (isolated test database)
**Mocking**: pytest-mock, unittest.mock
**Coverage**: pytest-cov

### Property-Based Testing Configuration

Each property-based test must:
- Run a minimum of 100 iterations to ensure adequate input coverage
- Reference the corresponding design document property in a comment
- Use the tag format: `# Feature: backend-architecture, Property {number}: {property_text}`
- Generate randomized test data using Hypothesis strategies

**Example Property Test**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: backend-architecture, Property 2: Multi-Tenant Query Isolation
@given(
    tenant_id=st.uuids(),
    other_tenant_id=st.uuids(),
    device_data=st.lists(st.builds(Device))
)
@pytest.mark.property_test
def test_multi_tenant_query_isolation(tenant_id, other_tenant_id, device_data, db_session):
    """
    Property: For any database query on tenant-scoped tables, when executed with a tenant context,
    the query should only return records matching that tenant_id and should never return records
    from other tenants.
    """
    # Assume tenant_id != other_tenant_id
    if tenant_id == other_tenant_id:
        return
    
    # Setup: Create devices for both tenants
    for device in device_data:
        device.tenant_id = tenant_id
        db_session.add(device)
    
    other_device = Device(tenant_id=other_tenant_id, hostname="other", ip_address="10.0.0.1")
    db_session.add(other_device)
    db_session.commit()
    
    # Execute: Query devices with tenant context
    results = db_session.query(Device).filter(Device.tenant_id == tenant_id).all()
    
    # Verify: All results belong to the correct tenant
    assert all(device.tenant_id == tenant_id for device in results)
    assert other_device not in results
```

### Unit Testing Strategy

**Test Organization**
```
tests/
├── unit/
│   ├── test_api/
│   │   ├── test_devices.py
│   │   ├── test_templates.py
│   │   └── test_auth.py
│   ├── test_services/
│   │   ├── test_device_service.py
│   │   └── test_template_service.py
│   ├── test_workers/
│   │   ├── test_device_tasks.py
│   │   └── test_backup_tasks.py
│   ├── test_connectors/
│   │   └── test_mikrotik.py
│   └── test_engines/
│       ├── test_template_engine.py
│       └── test_backup_engine.py
├── integration/
│   ├── test_device_adoption_flow.py
│   ├── test_backup_flow.py
│   └── test_template_application_flow.py
└── property/
    ├── test_tenant_isolation_properties.py
    ├── test_backup_properties.py
    ├── test_template_properties.py
    └── test_audit_properties.py
```

**Test Fixtures**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import create_access_token

# Test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create isolated database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create test client with database override"""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def superadmin_user(db_session):
    """Create SuperAdmin user for testing"""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("password"),
        role_id=get_role_id("SuperAdmin"),
        tenant_id=None
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def superadmin_token(superadmin_user):
    """Create JWT token for SuperAdmin"""
    return create_access_token({"sub": str(superadmin_user.user_id), "role": "SuperAdmin"})

@pytest.fixture
def tenant_admin_user(db_session, test_tenant):
    """Create TenantAdmin user for testing"""
    user = User(
        email="tenant@example.com",
        password_hash=hash_password("password"),
        role_id=get_role_id("TenantAdmin"),
        tenant_id=test_tenant.tenant_id
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def tenant_admin_token(tenant_admin_user):
    """Create JWT token for TenantAdmin"""
    return create_access_token({
        "sub": str(tenant_admin_user.user_id),
        "tenant_id": str(tenant_admin_user.tenant_id),
        "role": "TenantAdmin"
    })
```

**Example Unit Tests**
```python
def test_create_device_success(client, tenant_admin_token, test_tenant):
    """Test successful device creation"""
    response = client.post(
        "/api/v1/devices",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={
            "hostname": "router1",
            "ip_address": "192.168.1.1",
            "username": "admin",
            "password": "secret"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == "router1"
    assert data["tenant_id"] == str(test_tenant.tenant_id)
    assert "password" not in data  # Ensure password not in response

def test_create_device_invalid_ip(client, tenant_admin_token):
    """Test device creation with invalid IP address"""
    response = client.post(
        "/api/v1/devices",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={
            "hostname": "router1",
            "ip_address": "invalid-ip",
            "username": "admin",
            "password": "secret"
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "ip_address" in data["error"]["details"]

def test_get_device_cross_tenant_access_denied(client, tenant_admin_token, other_tenant_device):
    """Test that users cannot access devices from other tenants"""
    response = client.get(
        f"/api/v1/devices/{other_tenant_device.device_id}",
        headers={"Authorization": f"Bearer {tenant_admin_token}"}
    )
    
    assert response.status_code == 404  # Returns 404 to prevent tenant enumeration
```

### Integration Testing

Integration tests verify end-to-end workflows across multiple components:

```python
def test_device_adoption_flow(client, tenant_admin_token, mock_mikrotik):
    """Test complete device adoption workflow"""
    # 1. Create device
    response = client.post(
        "/api/v1/devices",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={
            "hostname": "router1",
            "ip_address": "192.168.1.1",
            "username": "admin",
            "password": "secret"
        }
    )
    assert response.status_code == 201
    device_id = response.json()["device_id"]
    
    # 2. Verify connectivity job was enqueued
    # (In real test, would check Celery queue or job database)
    
    # 3. Simulate job completion
    # (In real test, would execute worker task)
    
    # 4. Verify device status updated
    response = client.get(
        f"/api/v1/devices/{device_id}",
        headers={"Authorization": f"Bearer {tenant_admin_token}"}
    )
    assert response.json()["status"] == "managed"
    
    # 5. Verify audit log created
    response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        params={"device_id": device_id}
    )
    assert len(response.json()["items"]) > 0
```

### Test Coverage Requirements

- Minimum 80% code coverage for all modules
- 100% coverage for security-critical code (authentication, authorization, encryption)
- All correctness properties must have corresponding property-based tests
- All API endpoints must have unit tests for success and error cases
- All service layer methods must have unit tests
- All worker tasks must have unit tests

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Performance Testing

Performance tests ensure the system meets scalability requirements:

```python
import pytest
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def list_devices(self):
        """Test device listing performance"""
        self.client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def get_device(self):
        """Test device retrieval performance"""
        self.client.get(
            f"/api/v1/devices/{self.device_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )

# Run with: locust -f tests/performance/test_api_load.py --host=http://localhost:8000
```

---

## Summary

This design document specifies a comprehensive backend architecture for a multi-tenant MikroTik controller platform. The architecture emphasizes:

- **Scalability**: Horizontal scaling through stateless API design, distributed job processing, and database read replicas
- **Security**: Multi-tenant isolation, JWT authentication, RBAC authorization, encrypted credential storage, and comprehensive audit logging
- **Reliability**: Asynchronous job processing with retry logic, graceful error handling, and health monitoring
- **Maintainability**: Clear project structure, dependency injection, service layer architecture, and comprehensive testing
- **Observability**: Structured logging, Prometheus metrics, distributed tracing, and health check endpoints

The design provides 53 correctness properties that serve as formal specifications for property-based testing, ensuring the system behaves correctly across all valid inputs. Combined with unit tests for specific scenarios and integration tests for end-to-end workflows, this testing strategy provides comprehensive coverage and confidence in system correctness.

