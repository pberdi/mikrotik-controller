# MikroTik Controller - Backend

Backend API and worker services for the MikroTik Controller Platform.

## Overview

This backend provides a multi-tenant SaaS platform for centralized management of MikroTik router fleets. It supports device adoption, configuration management, remote command execution, backup operations, alerting, and audit logging with horizontal scalability from 500 to 10,000+ routers.

## Architecture

- **FastAPI**: RESTful API server with automatic OpenAPI documentation
- **Celery**: Asynchronous task processing for device operations
- **PostgreSQL**: Primary database with SQLAlchemy ORM
- **Redis**: Message broker, result backend, and caching layer
- **Alembic**: Database migration management

## Project Structure

```
backend/
├── app/
│   ├── api/          # API route handlers
│   ├── models/       # SQLAlchemy database models
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Business logic layer
│   ├── workers/      # Celery task definitions
│   ├── core/         # Core functionality (auth, database, middleware)
│   ├── connectors/   # External system connectors (MikroTik API)
│   ├── engines/      # Processing engines (templates, backups, alerts)
│   ├── utils/        # Utility functions
│   └── config.py     # Configuration management
├── alembic/          # Database migrations
├── docker/           # Docker configurations
├── tests/            # Test suite
├── requirements.txt  # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

1. Clone the repository and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Set up the database:
   ```bash
   # Create database
   createdb mikrotik_controller
   
   # Run migrations (once implemented)
   alembic upgrade head
   ```

### Running the Application

**Development Mode:**

```bash
# Start API server with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

**Production Mode:**

```bash
# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

# Start Celery beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

### API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Configuration is managed through environment variables using Pydantic Settings. See `.env.example` for all available options.

### Configuration Sections

- **Database**: PostgreSQL connection and pool settings
- **Redis**: Redis connection and pool settings
- **Security**: JWT tokens, encryption keys, password policies
- **Application**: General app settings, CORS, rate limiting, pagination
- **Workers**: Celery task processing configuration

### Environment Profiles

- `development`: Debug mode, verbose logging, relaxed security
- `staging`: Production-like environment for testing
- `production`: Strict security, optimized performance

## Development

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_devices.py

# Run with verbose output
pytest -v
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Security

- All passwords are hashed using bcrypt
- Device credentials are encrypted using AES-256
- JWT tokens for API authentication
- Role-based access control (RBAC)
- Multi-tenant data isolation
- Rate limiting on API endpoints
- Comprehensive audit logging

## Monitoring

- Health check endpoints: `/health`, `/health/ready`, `/health/live`
- Prometheus metrics: `/metrics`
- Structured JSON logging
- Distributed tracing support

## License

Proprietary - All rights reserved
