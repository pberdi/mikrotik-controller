Read all specification files located in /docs/specs.

Using those specifications, generate the initial backend architecture and project skeleton.

Create the following modules:

- tenants
- sites
- devices
- templates
- jobs
- backups
- alerts
- audit
- mikrotik_connector
- security

Generate:

- project directory structure
- database schema
- SQLAlchemy models
- FastAPI routers
- Celery workers
- MikroTik connector module
- job scheduler
- example API endpoints
- Docker setup

Ensure the system supports RouterOS 6 and RouterOS 7.
Ensure all remote device operations run as asynchronous jobs.
Focus on maintainability and scalability.
