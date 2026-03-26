# Implementation Plan: Backend Architecture

## Overview

This implementation plan breaks down the backend architecture for the MikroTik Controller Platform into discrete, manageable coding tasks. The plan follows a natural dependency order: foundation (project structure, database, configuration) → core features (API endpoints, authentication, services) → advanced features (workers, templates, backups, alerts) → testing and deployment.

The implementation creates a production-ready, horizontally scalable multi-tenant SaaS backend supporting 500 to 10,000+ MikroTik routers with comprehensive device management, configuration automation, backup operations, alerting, and audit logging.

## Tasks

- [x] 1. Project structure and foundation setup
  - [x] 1.1 Create project directory structure and Python package organization
    - Create directory structure: app/, app/api/, app/models/, app/schemas/, app/services/, app/workers/, app/core/, app/connectors/, app/engines/, app/utils/
    - Create __init__.py files in all packages
    - Create docker/, tests/, alembic/ directories
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 Implement configuration management system
    - Create app/config.py with Pydantic BaseSettings for environment variable loading
    - Define configuration classes: DatabaseConfig, RedisConfig, SecurityConfig, ApplicationConfig
    - Implement validation for required configuration values
    - Support environment-specific profiles (development, staging, production)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 49.1, 49.2, 49.3, 49.4, 49.5, 49.7_

  - [x] 1.3 Write property test for configuration loading
    - **Property 1: Configuration Loading from Environment**
    - **Validates: Requirements 1.2, 7.1, 7.2**

  - [x] 1.4 Create requirements.txt and requirements-dev.txt files
    - Add production dependencies: fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, celery, redis, pydantic, python-jose, passlib, bcrypt, jinja2, routeros-api, cryptography, prometheus-client
    - Add development dependencies: pytest, pytest-cov, pytest-mock, hypothesis, locust, black, flake8, mypy
    - _Requirements: 34.2, 34.3_


- [x] 2. Database models and schema
  - [x] 2.1 Create SQLAlchemy base models and mixins
    - Create app/models/base.py with declarative base
    - Implement TimestampMixin with created_at and updated_at fields
    - Implement UUIDMixin with UUID primary key
    - _Requirements: 3.4, 3.7_

  - [x] 2.2 Implement core database models
    - Create Tenant model (app/models/tenant.py) with status enum
    - Create Site model (app/models/site.py) with tenant relationship
    - Create Device model (app/models/device.py) with status enum and relationships
    - Create DeviceCredential model for encrypted credential storage
    - Create Template model (app/models/template.py) with type enum
    - Create Job model (app/models/job.py) with status and type enums
    - Create Backup model (app/models/backup.py) with checksum field
    - Create Alert model (app/models/alert.py) with severity and status enums
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6_

  - [x] 2.3 Implement user and RBAC models
    - Create Role model (app/models/role.py) with predefined roles
    - Create Permission model with resource and action fields
    - Create User model (app/models/user.py) with role relationship
    - Create AuditLog model (app/models/audit.py) with comprehensive fields
    - _Requirements: 3.1, 8.4_

  - [x] 2.4 Define database indexes for query optimization
    - Add indexes on tenant_id for all tenant-scoped tables
    - Add indexes on status fields for devices, jobs, alerts
    - Add indexes on timestamp fields for audit logs and backups
    - Add indexes on foreign keys
    - _Requirements: 3.5, 38.2_

  - [x] 2.5 Create database connection and session management
    - Create app/core/database.py with SQLAlchemy engine and session factory
    - Implement connection pooling with configurable pool size
    - Create get_db() dependency for FastAPI with automatic session lifecycle
    - Implement transaction management (commit on success, rollback on error)
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8_

- [x] 3. Database migrations with Alembic
  - [x] 3.1 Initialize Alembic migration system
    - Run alembic init alembic
    - Configure alembic.ini with database URL from environment
    - Update alembic/env.py to import models and use async if needed
    - _Requirements: 4.1_

  - [x] 3.2 Create initial migration for all core tables
    - Generate migration: alembic revision --autogenerate -m "Initial schema"
    - Review and adjust migration script
    - Include all tables: tenants, sites, devices, device_credentials, templates, jobs, backups, alerts, users, roles, permissions, audit_logs
    - _Requirements: 4.2, 4.4_

  - [ ] 3.3 Write property tests for migration round-trip
    - **Property 5: Migration Round-Trip**
    - **Validates: Requirements 4.3**

  - [ ] 3.4 Write property test for migration version recording
    - **Property 6: Migration Version Recording**
    - **Validates: Requirements 4.5**

- [ ] 4. Security and authentication foundation
  - [x] 4.1 Implement credential encryption with Secret Vault
    - Create app/utils/crypto.py with SecretVault class
    - Implement AES-256 encryption using cryptography.fernet
    - Implement PBKDF2 key derivation from master secret
    - Create encrypt() and decrypt() methods
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.6, 30.7, 30.8_

  - [ ] 4.2 Write property test for credential encryption
    - **Property 43: Credential Encryption**
    - **Validates: Requirements 30.1**

  - [x] 4.3 Implement JWT authentication
    - Create app/core/security.py with JWT token functions
    - Implement create_access_token() and create_refresh_token()
    - Implement verify_token() with JWT decoding and validation
    - Implement password hashing with bcrypt (hash_password, verify_password)
    - _Requirements: 8.1, 8.2, 8.3, 15.7_

  - [x] 4.4 Implement authentication dependencies
    - Create get_current_user() dependency that validates JWT and returns User
    - Create get_current_active_user() dependency that checks user is_active
    - Handle token validation errors with 401 responses
    - _Requirements: 8.3, 8.6, 8.7_

  - [ ] 4.5 Write property tests for JWT authentication
    - **Property 10: Invalid JWT Token Rejection**
    - **Property 12: Authenticated User Context**
    - **Validates: Requirements 8.3, 8.6, 8.7, 9.1**

  - [x] 4.6 Implement RBAC authorization
    - Create require_permission() decorator for endpoint protection
    - Implement permission checking against user role
    - Handle permission failures with 403 responses
    - Allow SuperAdmin to bypass permission checks
    - _Requirements: 8.4, 8.5, 8.8_

  - [-] 4.7 Write property test for permission enforcement
    - **Property 11: Insufficient Permission Rejection**
    - **Validates: Requirements 8.8**


- [ ] 5. Multi-tenant isolation middleware
  - [x] 5.1 Implement tenant isolation middleware
    - Create app/core/middleware.py with tenant_isolation_middleware
    - Extract tenant_id from authenticated user context
    - Inject tenant_id into request.state for downstream use
    - _Requirements: 9.1, 9.2_

  - [x] 5.2 Create tenant context dependency
    - Create get_tenant_context() dependency that returns tenant_id from request.state
    - Handle missing tenant context with 401 error
    - _Requirements: 9.1, 36.3_

  - [x] 5.3 Implement tenant filtering in service layer
    - Update service methods to automatically filter by tenant_id
    - Implement SuperAdmin bypass for cross-tenant access
    - Log cross-tenant access attempts to audit system
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ] 5.4 Write property tests for multi-tenant isolation
    - **Property 2: Multi-Tenant Query Isolation**
    - **Property 3: SuperAdmin Cross-Tenant Access**
    - **Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6, 44.1, 44.2, 44.3, 44.5, 44.6**

- [ ] 6. Pydantic schemas for request/response validation
  - [x] 6.1 Create common schemas
    - Create app/schemas/common.py with PaginatedResponse generic schema
    - Create error response schemas
    - _Requirements: 24.2, 29.3_

  - [x] 6.2 Create device schemas
    - Create app/schemas/device.py with DeviceCreate, DeviceUpdate, DeviceResponse
    - Add field validation (min_length, max_length, IP address validation)
    - _Requirements: 10.6, 24.1, 24.5, 24.7_

  - [x] 6.3 Create template, job, backup, alert, and user schemas
    - Create app/schemas/template.py with template CRUD schemas
    - Create app/schemas/job.py with job response schemas
    - Create app/schemas/backup.py with backup CRUD schemas
    - Create app/schemas/alert.py with alert schemas
    - Create app/schemas/user.py with user CRUD schemas
    - _Requirements: 24.1, 24.2, 24.5_

  - [ ] 6.4 Write property test for request validation
    - **Property 35: Request Validation Error Response**
    - **Validates: Requirements 24.4, 24.8**

- [ ] 7. FastAPI application bootstrap
  - [x] 7.1 Create FastAPI application factory
    - Create app/main.py with create_app() factory function
    - Initialize FastAPI with title, version, and OpenAPI configuration
    - Configure CORS middleware with allowed origins from config
    - Add request ID middleware for request tracing
    - _Requirements: 2.1, 2.4, 25.4_

  - [x] 7.2 Register exception handlers
    - Create app/core/exceptions.py with custom exception classes
    - Register exception handlers for APIException, RequestValidationError, IntegrityError
    - Implement consistent error response format
    - _Requirements: 2.3, 25.2, 25.3, 25.8, 25.9_

  - [ ] 7.3 Write property tests for error handling
    - **Property 36: Exception to HTTP Status Mapping**
    - **Property 38: Database Constraint Violation Handling**
    - **Validates: Requirements 25.2, 25.3, 25.9**

  - [x] 7.3 Configure structured logging
    - Create app/core/logging.py with JSONFormatter for production
    - Configure log levels and handlers
    - Implement sensitive data masking in logs
    - _Requirements: 25.1, 25.5, 25.6, 25.7_

  - [ ] 7.4 Write property test for sensitive data masking
    - **Property 37: Sensitive Data Masking in Logs**
    - **Validates: Requirements 25.7, 30.6**

  - [x] 7.5 Create health check endpoints
    - Create GET /health endpoint returning status and version
    - Create GET /health/ready endpoint checking database and Redis connectivity
    - Create GET /health/live endpoint for liveness probes
    - Return 503 if dependencies unavailable
    - _Requirements: 2.4, 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7_

  - [ ] 7.6 Write property test for health check dependency verification
    - **Property 39: Health Check Dependency Verification**
    - **Validates: Requirements 26.2, 26.5, 26.6**

  - [x] 7.7 Register API routers
    - Create app/api/v1/__init__.py with router registration
    - Register routers with /api/v1 prefix
    - Include version in response headers
    - _Requirements: 2.2, 27.1, 27.2_

- [ ] 8. Checkpoint - Verify foundation
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 9. Service layer implementation
  - [x] 9.1 Create device service
    - Create app/services/device_service.py with DeviceService class
    - Implement list_devices() with pagination and filtering
    - Implement get_device() with tenant isolation
    - Implement create_device() with credential encryption
    - Implement update_device() and delete_device()
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 37.1, 37.2, 37.6_

  - [x] 9.2 Create template service
    - Create app/services/template_service.py with TemplateService class
    - Implement CRUD operations for templates
    - Integrate template syntax validation
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.7, 37.1, 37.2_

  - [x] 9.3 Create job service
    - Create app/services/job_service.py with JobService class
    - Implement list_jobs() with status filtering
    - Implement get_job() with results
    - Implement cancel_job() for pending jobs
    - _Requirements: 12.1, 12.2, 12.3, 12.5, 37.1, 37.2_

  - [-] 9.4 Create backup service
    - Create app/services/backup_service.py with BackupService class
    - Implement list_backups() with filtering
    - Implement get_backup() and delete_backup()
    - _Requirements: 13.2, 13.3, 13.6, 37.1, 37.2_

  - [x] 9.5 Create alert service
    - Create app/services/alert_service.py with AlertService class
    - Implement list_alerts() with filtering
    - Implement get_alert() and update_alert()
    - Implement get_alert_stats()
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 37.1, 37.2_

  - [x] 9.6 Create user service
    - Create app/services/user_service.py with UserService class
    - Implement CRUD operations for users
    - Implement role assignment
    - Hash passwords before storage
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 37.1, 37.2_

  - [x] 9.7 Create audit service
    - Create app/services/audit_service.py with AuditService class
    - Implement log() method for creating audit entries
    - Implement specialized logging methods (log_api_request, log_authentication, log_device_operation)
    - Implement list_audit_logs() with filtering
    - _Requirements: 16.1, 16.2, 16.3, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.8, 21.9, 37.1, 37.2_

  - [ ] 9.8 Write property tests for audit logging
    - **Property 26: API Request Audit Logging**
    - **Property 27: Database Mutation Audit Logging**
    - **Property 28: Device Operation Audit Logging**
    - **Property 29: Authentication Attempt Audit Logging**
    - **Property 30: Permission Failure Audit Logging**
    - **Property 31: Audit Log Request Correlation**
    - **Property 32: Audit Log Tenant Isolation**
    - **Validates: Requirements 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.8, 21.9**

- [ ] 10. Authentication API endpoints
  - [x] 10.1 Create authentication router
    - Create app/api/v1/auth.py with authentication endpoints
    - Implement POST /api/v1/auth/login with email/password validation
    - Implement POST /api/v1/auth/refresh for token refresh
    - Implement POST /api/v1/auth/logout
    - Return access_token and refresh_token on successful login
    - _Requirements: 8.1, 8.2_

  - [ ] 10.2 Write unit tests for authentication endpoints
    - Test successful login with valid credentials
    - Test login failure with invalid credentials
    - Test token refresh with valid refresh token
    - Test token refresh with invalid refresh token
    - _Requirements: 8.1, 8.2_

- [ ] 11. Device management API endpoints
  - [x] 11.1 Create device router
    - Create app/api/v1/devices.py with device endpoints
    - Implement POST /api/v1/devices for device adoption
    - Implement GET /api/v1/devices with pagination and filtering
    - Implement GET /api/v1/devices/{device_id}
    - Implement PATCH /api/v1/devices/{device_id}
    - Implement DELETE /api/v1/devices/{device_id}
    - Implement POST /api/v1/devices/{device_id}/command
    - Enforce tenant isolation and authentication on all endpoints
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.7_

  - [ ] 11.2 Enqueue connectivity check job on device creation
    - When device is created, enqueue job to verify connectivity
    - _Requirements: 10.8_

  - [ ] 11.3 Write unit tests for device endpoints
    - Test device creation with valid data
    - Test device creation with invalid IP address
    - Test device listing with pagination
    - Test cross-tenant access denial
    - Test device update and deletion
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 12. Template management API endpoints
  - [ ] 12.1 Create template router
    - Create app/api/v1/templates.py with template endpoints
    - Implement POST /api/v1/templates with syntax validation
    - Implement GET /api/v1/templates with pagination
    - Implement GET /api/v1/templates/{template_id}
    - Implement PATCH /api/v1/templates/{template_id}
    - Implement DELETE /api/v1/templates/{template_id}
    - Implement POST /api/v1/templates/{template_id}/apply
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.8_

  - [ ] 12.2 Write unit tests for template endpoints
    - Test template creation with valid syntax
    - Test template creation with invalid syntax
    - Test template application enqueues job
    - _Requirements: 11.1, 11.7, 11.8_


- [ ] 13. Job management API endpoints
  - [ ] 13.1 Create job router
    - Create app/api/v1/jobs.py with job endpoints
    - Implement GET /api/v1/jobs with status filtering
    - Implement GET /api/v1/jobs/{job_id}
    - Implement POST /api/v1/jobs/{job_id}/cancel
    - Implement GET /api/v1/jobs/{job_id}/logs
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.6_

  - [ ] 13.2 Write property test for job status lifecycle
    - **Property 33: Job Status Lifecycle**
    - **Validates: Requirements 22.3, 22.4, 31.9, 31.10, 31.11**

  - [ ] 13.3 Write property test for job result storage
    - **Property 34: Job Result Storage**
    - **Validates: Requirements 22.4, 31.7**

  - [ ] 13.4 Write unit tests for job endpoints
    - Test job listing with filtering
    - Test job cancellation
    - Test job log retrieval
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 14. Backup management API endpoints
  - [ ] 14.1 Create backup router
    - Create app/api/v1/backups.py with backup endpoints
    - Implement POST /api/v1/backups to trigger manual backups
    - Implement GET /api/v1/backups with filtering
    - Implement GET /api/v1/backups/{backup_id}
    - Implement GET /api/v1/backups/{backup_id}/download
    - Implement POST /api/v1/backups/{backup_id}/restore
    - Implement DELETE /api/v1/backups/{backup_id}
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ] 14.2 Write unit tests for backup endpoints
    - Test backup creation enqueues job
    - Test backup download returns file content
    - Test backup restore enqueues job
    - _Requirements: 13.1, 13.4, 13.5_

- [ ] 15. Alert management API endpoints
  - [ ] 15.1 Create alert router
    - Create app/api/v1/alerts.py with alert endpoints
    - Implement GET /api/v1/alerts with filtering
    - Implement GET /api/v1/alerts/{alert_id}
    - Implement PATCH /api/v1/alerts/{alert_id} for acknowledgment
    - Implement GET /api/v1/alerts/stats
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ] 15.2 Write unit tests for alert endpoints
    - Test alert listing with severity filtering
    - Test alert acknowledgment
    - Test alert statistics
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ] 16. User management API endpoints
  - [ ] 16.1 Create user router
    - Create app/api/v1/users.py with user endpoints
    - Implement POST /api/v1/users
    - Implement GET /api/v1/users
    - Implement GET /api/v1/users/{user_id}
    - Implement PATCH /api/v1/users/{user_id}
    - Implement DELETE /api/v1/users/{user_id}
    - Implement POST /api/v1/users/{user_id}/roles
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ] 16.2 Write unit tests for user endpoints
    - Test user creation with role assignment
    - Test cross-tenant user access denial
    - Test password hashing
    - _Requirements: 15.1, 15.7, 15.8_

- [ ] 17. Audit log API endpoints
  - [ ] 17.1 Create audit log router
    - Create app/api/v1/audit.py with audit endpoints
    - Implement GET /api/v1/audit-logs with filtering
    - Implement GET /api/v1/audit-logs/{log_id}
    - Support filtering by user, action, resource type, date range
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 17.2 Write unit tests for audit log endpoints
    - Test audit log listing with filters
    - Test SuperAdmin cross-tenant access
    - _Requirements: 16.1, 16.3, 16.5_

- [ ] 18. Pagination and filtering implementation
  - [ ] 18.1 Implement pagination helper
    - Create pagination utility in app/utils/helpers.py
    - Support page and page_size query parameters
    - Return PaginatedResponse with metadata
    - Enforce maximum page_size of 100, default to 50
    - _Requirements: 29.1, 29.2, 29.3_

  - [ ] 18.2 Write property tests for pagination
    - **Property 41: Pagination Metadata**
    - **Property 42: Pagination Bounds Enforcement**
    - **Validates: Requirements 29.2, 29.3**

  - [ ] 18.3 Implement filtering and sorting
    - Support filtering using query parameters
    - Support sorting with sort parameter
    - Support search with q parameter
    - _Requirements: 29.4, 29.5, 29.6, 29.7_

- [ ] 19. Checkpoint - Verify API layer
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 20. MikroTik connector implementation
  - [ ] 20.1 Create MikroTik connector
    - Create app/connectors/mikrotik.py with MikroTikConnector class
    - Implement connect() method with timeout handling
    - Implement disconnect() method
    - Implement execute_command() for RouterOS commands
    - Implement export_configuration() for backup
    - Implement apply_configuration() for template application
    - Implement get_system_resource() and get_interfaces()
    - Use context manager protocol (__enter__, __exit__)
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ] 20.2 Implement error handling and logging
    - Return descriptive error messages on connection failure
    - Log command execution failures to audit system
    - Retrieve credentials from Secret Vault
    - _Requirements: 17.6, 17.7, 17.8_

  - [ ] 20.3 Write property tests for MikroTik connector
    - **Property 44: MikroTik Connection Timeout**
    - **Property 45: MikroTik Connection Error Reporting**
    - **Property 46: MikroTik Command Failure Logging**
    - **Validates: Requirements 17.5, 17.7, 17.8**

  - [ ] 20.4 Write unit tests for MikroTik connector
    - Test successful connection and command execution
    - Test connection timeout
    - Test command execution failure
    - Use mocking for RouterOS API
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 21. Template engine implementation
  - [ ] 21.1 Create template engine
    - Create app/engines/template_engine.py with TemplateEngine class
    - Initialize Jinja2 environment with custom filters
    - Implement validate_syntax() for Jinja2 syntax validation
    - Implement get_variables() to extract template variables
    - Implement render() for template rendering
    - Implement validate_rendered_output() for RouterOS syntax validation
    - Implement dry_run() for template testing
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 42.1, 42.2, 42.3, 42.4_

  - [ ] 21.2 Implement custom Jinja2 filters
    - Create ip_network filter for CIDR network extraction
    - Create subnet_mask filter for CIDR mask extraction
    - _Requirements: 18.5_

  - [ ] 21.3 Write property tests for template engine
    - **Property 13: Template Variable Substitution**
    - **Property 14: Template Syntax Validation**
    - **Property 15: Template Rendering Error Reporting**
    - **Property 16: Template Round-Trip Validation**
    - **Validates: Requirements 18.2, 18.4, 18.6, 18.7, 42.1, 42.6**

  - [ ] 21.4 Write unit tests for template engine
    - Test template rendering with variables
    - Test syntax validation with invalid templates
    - Test dry-run mode
    - Test custom filters
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [ ] 22. Backup storage implementation
  - [ ] 22.1 Create backup storage engine
    - Create app/engines/backup_engine.py with BackupStorage class
    - Implement store_backup() with compression and checksum
    - Implement retrieve_backup() with decompression
    - Implement verify_backup() with checksum verification
    - Implement delete_backup()
    - Implement apply_retention_policy() for automatic cleanup
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.8_

  - [ ] 22.2 Implement backup validation
    - Validate backup content is valid RouterOS configuration
    - Mark corrupted backups and create alerts
    - _Requirements: 19.7, 43.4, 43.5_

  - [ ] 22.3 Write property tests for backup storage
    - **Property 17: Backup Compression**
    - **Property 18: Backup Retention Policy Enforcement**
    - **Property 19: Backup Checksum Calculation**
    - **Property 20: Backup Checksum Verification**
    - **Property 21: Backup Round-Trip Integrity**
    - **Property 22: Backup Content Validation**
    - **Validates: Requirements 19.2, 19.4, 19.6, 19.7, 19.8, 43.1, 43.3, 43.4, 43.5, 43.6**

  - [ ] 22.4 Write unit tests for backup storage
    - Test backup creation with compression
    - Test backup retrieval and decompression
    - Test checksum verification
    - Test retention policy cleanup
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_

- [ ] 23. Alert engine implementation
  - [ ] 23.1 Create alert engine
    - Create app/engines/alert_engine.py with AlertEngine class
    - Implement create_alert() with deduplication
    - Implement acknowledge_alert() and resolve_alert()
    - Implement auto_resolve_alerts() for condition clearing
    - Implement _is_duplicate() for deduplication window checking
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.8_

  - [ ] 23.2 Enqueue notification jobs for critical alerts
    - When critical alert is created, enqueue notification job to high-priority queue
    - _Requirements: 20.7_

  - [ ] 23.3 Write property tests for alert engine
    - **Property 23: Alert Deduplication**
    - **Property 24: Critical Alert Notification**
    - **Property 25: Alert Auto-Resolution**
    - **Validates: Requirements 20.5, 20.7, 20.8**

  - [ ] 23.4 Write unit tests for alert engine
    - Test alert creation with deduplication
    - Test alert acknowledgment and resolution
    - Test critical alert notification enqueuing
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.7_

- [ ] 24. Checkpoint - Verify engines and connectors
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 25. Celery worker configuration
  - [ ] 25.1 Create Celery application
    - Create app/workers/celery_app.py with Celery configuration
    - Configure Redis as broker and result backend
    - Define task queues (high, default, low)
    - Configure task retry logic with exponential backoff
    - Configure task time limits (hard and soft)
    - Enable task tracking and late acknowledgment
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 25.2 Write property tests for Celery configuration
    - **Property 7: Task Retry with Exponential Backoff**
    - **Property 8: Task Time Limit Enforcement**
    - **Property 9: Failed Task Audit Logging**
    - **Validates: Requirements 5.4, 5.6, 5.7**

  - [ ] 25.2 Create base task class with database session
    - Create DatabaseTask base class with session management
    - Implement session cleanup in after_return()
    - _Requirements: 23.2, 23.3, 23.6_

- [ ] 26. Worker tasks implementation
  - [ ] 26.1 Create device operation tasks
    - Create app/workers/tasks/device_tasks.py
    - Implement execute_device_backup task
    - Implement execute_connectivity_check task
    - Implement execute_command task
    - Update job status throughout task execution (pending → running → completed/failed)
    - Store task results in job records
    - _Requirements: 31.1, 31.6, 31.7, 31.9, 31.10, 31.11_

  - [ ] 26.2 Create template application tasks
    - Create app/workers/tasks/template_tasks.py
    - Implement apply_template_to_device task
    - Render template with device variables
    - Apply configuration using MikroTik connector
    - _Requirements: 31.3_

  - [ ] 26.3 Create backup tasks
    - Create app/workers/tasks/backup_tasks.py
    - Implement scheduled_backup task for automatic backups
    - Implement backup_retention_cleanup task
    - _Requirements: 31.2_

  - [ ] 26.4 Create alert notification tasks
    - Create app/workers/tasks/alert_tasks.py
    - Implement send_alert_notification task
    - _Requirements: 31.5_

  - [ ] 26.5 Implement error handling in tasks
    - Handle task failures gracefully with retry logic
    - Create alerts on job failures
    - Log all device operations to audit system
    - _Requirements: 31.8_

  - [ ] 26.6 Write unit tests for worker tasks
    - Test device backup task execution
    - Test connectivity check task
    - Test template application task
    - Test job status updates
    - Test error handling and retry
    - Use mocking for MikroTik connector
    - _Requirements: 31.1, 31.2, 31.3, 31.6, 31.7, 31.8, 31.9, 31.10, 31.11_

- [ ] 27. Job scheduler with Celery Beat
  - [ ] 27.1 Configure Celery Beat for scheduled jobs
    - Configure Celery Beat in celery_app.py
    - Define schedule for automatic device backups
    - Define schedule for periodic connectivity checks
    - Define schedule for cleanup of old audit logs and backups
    - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5_

  - [ ] 27.2 Implement dynamic schedule management
    - Store schedule configuration in database
    - Allow schedule updates without restart
    - _Requirements: 32.6, 32.7, 32.8_

  - [ ] 27.3 Write unit tests for scheduled jobs
    - Test schedule configuration
    - Test job enqueuing on schedule
    - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.8_

- [ ] 28. Job queue integration
  - [ ] 28.1 Implement job enqueuing in services
    - Update device service to enqueue connectivity check on device creation
    - Update template service to enqueue template application
    - Update backup service to enqueue backup jobs
    - Create Job records before enqueuing
    - Return job_id for tracking
    - _Requirements: 22.1, 22.2, 22.8_

  - [ ] 28.2 Implement job status updates
    - Update job status as workers process tasks
    - Store job results upon completion
    - _Requirements: 22.3, 22.4_

  - [ ] 28.3 Write integration tests for job queue
    - Test job enqueuing and execution
    - Test job status updates
    - Test job result storage
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.8_

- [ ] 29. Rate limiting implementation
  - [ ] 29.1 Implement rate limiting middleware
    - Create rate limiting middleware using Redis
    - Configure rate limits per user and per tenant
    - Configure different limits for different endpoint categories
    - Return 429 with rate limit headers when exceeded
    - Allow SuperAdmin to bypass rate limits
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_

  - [ ] 29.2 Write property test for rate limit enforcement
    - **Property 40: Rate Limit Enforcement**
    - **Validates: Requirements 28.2, 28.3, 28.4**

  - [ ] 29.3 Write unit tests for rate limiting
    - Test rate limit enforcement
    - Test rate limit headers
    - Test SuperAdmin bypass
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.6_

- [ ] 30. Checkpoint - Verify workers and job processing
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 31. WebSocket support for real-time updates
  - [ ] 31.1 Implement WebSocket endpoint
    - Create WebSocket endpoint at /ws
    - Implement JWT authentication for WebSocket connections
    - Handle connection lifecycle (connect, disconnect, error)
    - _Requirements: 39.1, 39.2, 39.6_

  - [ ] 31.2 Implement tenant-isolated message broadcasting
    - Use Redis pub/sub for cross-instance message distribution
    - Implement tenant isolation for WebSocket messages
    - _Requirements: 39.5, 39.7_

  - [ ] 31.3 Broadcast job status updates
    - When job status changes, publish update to relevant WebSocket clients
    - _Requirements: 39.3, 39.8_

  - [ ] 31.4 Broadcast alert notifications
    - When new alert is created, publish alert to relevant WebSocket clients
    - _Requirements: 39.4, 39.9_

  - [ ] 31.5 Write property tests for WebSocket
    - **Property 47: WebSocket Tenant Isolation**
    - **Property 48: WebSocket Job Status Updates**
    - **Property 49: WebSocket Alert Notifications**
    - **Validates: Requirements 39.5, 39.8, 39.9**

  - [ ] 31.6 Write unit tests for WebSocket
    - Test WebSocket authentication
    - Test message broadcasting
    - Test tenant isolation
    - _Requirements: 39.1, 39.2, 39.3, 39.4, 39.5_

- [ ] 32. API response caching
  - [ ] 32.1 Implement caching middleware
    - Create caching middleware using Redis
    - Cache GET endpoint responses
    - Use cache keys that include tenant_id
    - Set appropriate cache TTL based on data volatility
    - Include cache status in response headers (X-Cache: HIT/MISS)
    - Support cache bypass using query parameter
    - _Requirements: 45.1, 45.2, 45.3, 45.5, 45.6, 45.7_

  - [ ] 32.2 Implement cache invalidation
    - Invalidate cache entries when underlying data changes
    - _Requirements: 45.4_

  - [ ] 32.3 Write property tests for caching
    - **Property 52: Cache Tenant Isolation**
    - **Property 53: Cache Invalidation on Mutation**
    - **Validates: Requirements 45.2, 45.4**

  - [ ] 32.4 Write unit tests for caching
    - Test cache hit and miss
    - Test cache invalidation
    - Test tenant isolation in cache keys
    - _Requirements: 45.1, 45.2, 45.3, 45.4, 45.5_

- [ ] 33. Bulk operations support
  - [ ] 33.1 Implement bulk operation endpoints
    - Create POST /api/v1/devices/bulk-update endpoint
    - Create POST /api/v1/backups/bulk-create endpoint
    - Create POST /api/v1/templates/bulk-apply endpoint
    - Validate batch size (maximum 100)
    - Process asynchronously using Worker_Engine
    - Return job_id for tracking
    - _Requirements: 46.1, 46.2, 46.3, 46.4, 46.5, 46.6, 46.7_

  - [ ] 33.2 Write unit tests for bulk operations
    - Test bulk update with valid batch
    - Test batch size validation
    - Test job creation for bulk operations
    - _Requirements: 46.1, 46.2, 46.3, 46.4, 46.5, 46.6_

- [ ] 34. Metrics and observability
  - [ ] 34.1 Implement Prometheus metrics
    - Create app/core/metrics.py with Prometheus instrumentation
    - Expose /metrics endpoint
    - Track request count, duration, and error rate
    - Track database connection pool usage
    - Track Celery queue lengths and task execution times
    - Track custom business metrics (devices online, jobs pending, alerts active)
    - _Requirements: 41.1, 41.2, 41.3, 41.4, 41.5_

  - [ ] 34.2 Implement distributed tracing
    - Add trace_id propagation across services
    - Integrate with OpenTelemetry
    - _Requirements: 41.6, 41.7_

  - [ ] 34.3 Write unit tests for metrics
    - Test metric collection
    - Test metric endpoint
    - _Requirements: 41.1, 41.2, 41.3, 41.4, 41.5_

- [ ] 35. Graceful shutdown implementation
  - [ ] 35.1 Implement graceful shutdown for API
    - Handle SIGTERM signal
    - Stop accepting new requests
    - Complete in-flight requests
    - Close database and Redis connections
    - Complete shutdown within 30 seconds
    - _Requirements: 40.1, 40.2, 40.3, 40.4, 40.5, 40.8_

  - [ ] 35.2 Implement graceful shutdown for workers
    - Complete current tasks before terminating
    - Requeue incomplete tasks
    - _Requirements: 40.6, 40.7_

  - [ ] 35.3 Write property tests for graceful shutdown
    - **Property 50: Graceful Shutdown Request Completion**
    - **Property 51: Graceful Shutdown Worker Task Completion**
    - **Validates: Requirements 40.3, 40.6**

  - [ ] 35.4 Write unit tests for graceful shutdown
    - Test SIGTERM handling
    - Test in-flight request completion
    - Test connection cleanup
    - _Requirements: 40.1, 40.2, 40.3, 40.4, 40.5_

- [ ] 36. Checkpoint - Verify advanced features
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 37. Docker configuration
  - [ ] 37.1 Create API Dockerfile
    - Create docker/Dockerfile.api with Python 3.11 base image
    - Install system dependencies (gcc, postgresql-client)
    - Copy requirements and install dependencies
    - Copy application code
    - Create non-root user
    - Configure health check
    - Set CMD to run uvicorn
    - _Requirements: 6.1, 6.4_

  - [ ] 37.2 Create Worker Dockerfile
    - Create docker/Dockerfile.worker with Python 3.11 base image
    - Install system dependencies
    - Copy requirements and install dependencies
    - Copy application code
    - Create non-root user
    - Set CMD to run Celery worker
    - _Requirements: 6.2_

  - [ ] 37.3 Create docker-compose.yml for development
    - Create docker/docker-compose.yml with services: postgres, redis, api, worker, celery-beat
    - Configure environment variables
    - Configure health checks
    - Configure volumes for persistent data
    - Configure dependency ordering
    - Configure container networking
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 34.1_

  - [ ] 37.4 Write integration tests for Docker deployment
    - Test docker-compose startup
    - Test service health checks
    - Test inter-service communication
    - _Requirements: 6.3, 6.4, 6.8_

- [ ] 38. Database query optimization
  - [ ] 38.1 Implement eager loading for relationships
    - Use joinedload for commonly accessed relationships
    - Prevent N+1 queries
    - _Requirements: 38.1, 38.5_

  - [ ] 38.2 Implement query result caching
    - Cache frequently accessed data
    - _Requirements: 38.4_

  - [ ] 38.3 Implement slow query logging
    - Log queries exceeding 1 second
    - _Requirements: 38.6_

  - [ ] 38.4 Verify pagination for large result sets
    - Use database-level pagination
    - _Requirements: 38.3, 38.7_

  - [ ] 38.5 Write performance tests for database queries
    - Test query performance with large datasets
    - Test N+1 query prevention
    - _Requirements: 38.1, 38.2, 38.3, 38.5_

- [ ] 39. API documentation
  - [ ] 39.1 Configure OpenAPI specification
    - Generate OpenAPI 3.0 specification automatically
    - Include request and response schemas
    - Include authentication requirements
    - Include example requests and responses
    - Document all error codes
    - Group endpoints by domain entity
    - Include description text for all endpoints and parameters
    - _Requirements: 2.5, 33.1, 33.2, 33.3, 33.4, 33.5, 33.6, 33.7_

  - [ ] 39.2 Verify OpenAPI spec for SDK generation
    - Ensure OpenAPI spec is compatible with code generators
    - Version the OpenAPI specification
    - _Requirements: 47.1, 47.2, 47.3, 47.4, 47.5_

  - [ ] 39.3 Write tests for API documentation
    - Test OpenAPI spec generation
    - Test documentation completeness
    - _Requirements: 33.1, 33.2, 33.3, 33.4, 33.5_

- [ ] 40. Testing infrastructure
  - [ ] 40.1 Configure pytest
    - Create pytest.ini with test configuration
    - Configure test coverage reporting
    - _Requirements: 35.1, 35.6_

  - [ ] 40.2 Create test fixtures
    - Create tests/conftest.py with pytest fixtures
    - Implement database session fixture with isolation
    - Implement test client fixture
    - Implement authenticated user fixtures for different roles
    - _Requirements: 35.2, 35.3, 35.4_

  - [ ] 40.3 Create example tests
    - Create example tests for API endpoints
    - Create example tests for services
    - Create example tests for workers
    - _Requirements: 35.5_

  - [ ] 40.4 Configure test database
    - Support test database isolation
    - Support running tests in Docker containers
    - _Requirements: 35.4, 35.7_

  - [ ] 40.5 Write integration tests
    - Test device adoption flow end-to-end
    - Test backup flow end-to-end
    - Test template application flow end-to-end
    - _Requirements: 35.1, 35.2, 35.3, 35.4, 35.5_

- [ ] 41. Development environment setup
  - [ ] 41.1 Create README with setup instructions
    - Document prerequisites
    - Document installation steps
    - Document running the application
    - Document running tests
    - Document Docker usage
    - _Requirements: 34.4_

  - [ ] 41.2 Create docker-compose.dev.yml for local development
    - Configure hot-reload for code changes
    - Configure development logging (DEBUG level to stdout)
    - _Requirements: 34.1, 34.5, 34.7_

  - [ ] 41.3 Create database seeding script
    - Seed database with sample data for development
    - Create sample tenants, users, devices
    - _Requirements: 34.6_

  - [ ] 41.4 Test development environment setup
    - Test docker-compose.dev.yml startup
    - Test hot-reload functionality
    - Test database seeding
    - _Requirements: 34.1, 34.5, 34.6_

- [ ] 42. Horizontal scalability configuration
  - [ ] 42.1 Configure stateless API instances
    - Ensure all session state stored in Redis
    - Use Redis for shared state across instances
    - Use Redis pub/sub for cross-instance communication
    - Include instance_id in logs
    - _Requirements: 50.1, 50.2, 50.3, 50.7_

  - [ ] 42.2 Configure worker distribution
    - Support multiple worker instances
    - Ensure jobs distributed across workers automatically
    - _Requirements: 50.4, 50.5_

  - [ ] 42.3 Configure database read replicas
    - Support read replicas for query scaling
    - _Requirements: 50.6_

  - [ ] 42.4 Write load tests for horizontal scaling
    - Test load distribution across multiple API instances
    - Test job distribution across multiple workers
    - _Requirements: 50.1, 50.2, 50.4, 50.5, 50.8_

- [ ] 43. Final checkpoint - Complete system verification
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 44. Database backup and recovery
  - [ ] 44.1 Implement PostgreSQL backup automation
    - Create backup script using pg_dump
    - Schedule daily backups via Job_Scheduler
    - Store backups in external storage (S3-compatible)
    - Retain backups for 30 days
    - _Requirements: 48.1, 48.2, 48.3, 48.4_

  - [ ] 44.2 Implement backup verification
    - Verify backup integrity after creation
    - Test backup restoration
    - _Requirements: 48.5, 48.7_

  - [ ] 44.3 Document restore procedures
    - Create documentation for backup restoration
    - _Requirements: 48.6_

  - [ ] 44.4 Write tests for database backup
    - Test backup creation
    - Test backup verification
    - Test backup restoration
    - _Requirements: 48.1, 48.2, 48.5, 48.7_

- [ ] 45. Security hardening
  - [ ] 45.1 Implement input sanitization
    - Sanitize string inputs to prevent injection attacks
    - _Requirements: 24.6_

  - [ ] 45.2 Verify SQL injection prevention
    - Ensure all queries use parameterized statements
    - Prevent SQL injection of tenant_id values
    - _Requirements: 44.4_

  - [ ] 45.3 Implement security headers
    - Add security headers to API responses
    - Configure CORS properly
    - _Requirements: 2.1_

  - [ ] 45.4 Write security tests
    - Test SQL injection prevention
    - Test XSS prevention
    - Test CSRF protection
    - _Requirements: 24.6, 44.4_

- [ ] 46. Production deployment preparation
  - [ ] 46.1 Create production environment configuration
    - Create .env.production template
    - Document all required environment variables
    - Require explicit configuration for production
    - Prevent startup with development settings in production
    - _Requirements: 49.2, 49.5, 49.6, 49.7_

  - [ ] 46.2 Create Nginx load balancer configuration
    - Create nginx.conf with upstream configuration
    - Configure load balancing (least_conn)
    - Configure health checks
    - Configure WebSocket support
    - _Requirements: 50.1_

  - [ ] 46.3 Create deployment documentation
    - Document deployment process
    - Document scaling procedures
    - Document monitoring setup
    - Document backup and recovery procedures
    - _Requirements: 34.4, 48.6_

  - [ ] 46.4 Write deployment verification tests
    - Test production configuration validation
    - Test environment variable requirements
    - _Requirements: 49.2, 49.3, 49.5, 49.7_

- [ ] 47. Final integration and wiring
  - [ ] 47.1 Wire all components together
    - Ensure all routers registered in main.py
    - Ensure all middleware configured
    - Ensure all exception handlers registered
    - Ensure all dependencies properly injected
    - Verify database migrations applied
    - Verify Celery workers can process all task types
    - _Requirements: 2.2, 2.3, 36.1, 36.2, 36.3, 36.4_

  - [ ] 47.2 Verify end-to-end workflows
    - Test complete device adoption workflow
    - Test complete backup workflow
    - Test complete template application workflow
    - Test complete alert workflow
    - Test complete audit logging workflow
    - _Requirements: All requirements_

  - [ ] 47.3 Run comprehensive test suite
    - Run all unit tests
    - Run all property-based tests
    - Run all integration tests
    - Verify test coverage meets 80% minimum
    - Verify 100% coverage for security-critical code
    - _Requirements: 35.1, 35.2, 35.3, 35.4, 35.5, 35.6_

  - [ ] 47.4 Run performance tests
    - Run load tests with Locust
    - Verify system handles 500-10,000+ devices
    - Verify API response times
    - Verify job processing throughput
    - _Requirements: 50.1, 50.2, 50.4, 50.5, 50.8_

- [ ] 48. Final checkpoint - Production readiness verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation follows a natural dependency order: foundation → core → advanced → testing → deployment
- All code should be production-ready with proper error handling, logging, and security
- The system is designed for horizontal scalability from 500 to 10,000+ devices

